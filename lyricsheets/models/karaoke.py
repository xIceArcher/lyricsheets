from dataclasses import dataclass
from datetime import timedelta
from functools import reduce
from itertools import accumulate
from typing import Sequence

from src.models import SongLine

from src.fonts import FontScaler

import pyass
from pyass import Style


class KLine:
    pass


class KSyl:
    pass


@dataclass
class KChar:
    char: str
    i: int
    sylI: int
    fadeOffset: timedelta() = timedelta()
    karaStart: timedelta() = timedelta()
    karaEnd: timedelta() = timedelta()

    line: KLine = None
    syl: KSyl = None

    @property
    def karaDuration(self) -> timedelta:
        return self.karaEnd - self.karaStart


@dataclass
class KSyl:
    start: timedelta()
    end: timedelta()
    chars: Sequence[KChar]
    inlineFx: str
    i: int

    line: KLine = None

    @property
    def text(self) -> str:
        return ''.join(char.char for char in self.chars)

    @property
    def duration(self) -> timedelta:
        return self.end - self.start

    def calculate_char_kara_times(self, style: Style):
        fontScaler = FontScaler(style.fontName, style.fontSize)

        syllableCharLengths = [
            timedelta(milliseconds=c * 10)
            for c in fontScaler.split_by_rendered_width(
                pyass.timedelta(self.duration).total_centiseconds(), self.text
            )
        ]

        sylAccLength = self.start

        for char, syllableCharLength in zip(self.chars, syllableCharLengths):
            char.karaStart = sylAccLength
            char.karaEnd = sylAccLength + syllableCharLength

            sylAccLength += syllableCharLength


@dataclass
class KLine:
    start: timedelta()
    end: timedelta()
    kara: Sequence[KSyl]
    startActor: str
    actorSwitches: Sequence[tuple[int, str]]
    isSecondary: bool
    isAlone: bool
    isEN: bool
    lineNum: int

    @property
    def text(self) -> str:
        return ''.join(c.char for text in self.kara for c in text.chars)

    @property
    def duration(self) -> timedelta:
        return self.end - self.start

    @property
    def chars(self) -> Sequence[KChar]:
        return [char for k in self.kara for char in k.chars]

    def calculate_char_offsets(self, style: Style, transitionDuration: timedelta):
        self.calculate_char_fade_offsets(style, transitionDuration)
        for k in self.kara:
            k.calculate_char_kara_times(style)

    def calculate_char_fade_offsets(self, style: Style, transitionDuration: timedelta):
        fontScaler = FontScaler(style.fontName, style.fontSize)

        lineCharTimes = [
            timedelta(milliseconds=m)
            for m in fontScaler.split_by_rendered_width(
                pyass.timedelta(transitionDuration).total_milliseconds(), self.text
            )
        ]

        charAccTime = timedelta()
        for char, lineCharTime in zip(self.chars, lineCharTimes):
            char.fadeOffset = charAccTime
            charAccTime += lineCharTime


def to_romaji_k_line(line: SongLine, lineNum: int = 0) -> KLine:
    timedeltaUpToIdx = reduce(
        lambda a, b: a + [a[-1] + b.length], line.syllables, [timedelta(0)]
    )

    kLine = KLine(
        start=line.start,
        end=line.end,
        kara=[],
        startActor=line.actors[0],
        actorSwitches=[
            (timedeltaUpToIdx[breakpoint], actor)
            for breakpoint, actor in zip(line.breakpoints, line.actors)
            if breakpoint != 0
        ],
        isSecondary=line.isSecondary,
        isAlone=line.romaji == line.en,
        isEN=False,
        lineNum=lineNum,
    )

    accLength = timedelta()
    totalChars = 0
    counts = [a - b for a, b in zip(line.breakpoints[1:], line.breakpoints[:-1])] + [
        len(line.syllables) - line.breakpoints[-1]
    ]
    actors = [
        actor for (count, actor) in zip(counts, line.actors) for _ in range(count)
    ]

    for syl, actor in zip(line.syllables, actors):
        kSyl = KSyl(
            start=accLength,
            end=accLength + syl.length,
            inlineFx=actor,
            chars=[],
            i=len(kLine.kara),
            line=kLine,
        )

        for c in syl.text:
            kChar = KChar(
                char=c,
                i=totalChars,
                sylI=len(kSyl.chars),
                syl=kSyl,
                line=kLine,
            )

            kSyl.chars.append(kChar)
            totalChars += 1

        kLine.kara.append(kSyl)

        accLength += syl.length

    return kLine


def to_en_k_line(line: SongLine, lineNum: int = 0) -> KLine:
    timedeltaUpToIdx = reduce(
        lambda a, b: a + [a[-1] + b.length], line.syllables, [timedelta(0)]
    )
    kLineEN = KLine(
        start=line.start,
        end=line.end,
        kara=[],
        startActor=line.actors[0],
        actorSwitches=[
            (timedeltaUpToIdx[breakpoint], actor)
            for breakpoint, actor in zip(line.breakpoints, line.actors)
            if breakpoint != 0
        ],
        isSecondary=line.isSecondary,
        isAlone=line.romaji == line.en,
        isEN=True,
        lineNum=lineNum,
    )

    kSylEN = KSyl(
        start=line.start,
        end=line.start,
        chars=[],
        inlineFx=None,
        i=0,
        line=kLineEN,
    )

    kSylEN.chars = [
        KChar(
            char=char,
            i=i,
            karaStart=timedelta(),
            karaEnd=timedelta(),
            sylI=i,
            syl=kSylEN,
            line=kLineEN,
        )
        for i, char, in enumerate(line.en)
    ]

    kLineEN.kara.append(kSylEN)

    return kLineEN
