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
    karaDuration: timedelta() = timedelta()

    line: KLine = None
    syl: KSyl = None


@dataclass
class KSyl:
    start: timedelta()
    end: timedelta()
    duration: timedelta()
    chars: Sequence[KChar]
    text: str
    inlineFx: str
    i: int

    line: KLine = None

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
            char.karaDuration = syllableCharLength
            char.karaEnd = sylAccLength + syllableCharLength

            sylAccLength += syllableCharLength


@dataclass
class KLine:
    start: timedelta()
    end: timedelta()
    duration: timedelta()
    kara: Sequence[KSyl]
    text: str
    startActor: str
    actorSwitches: Sequence[tuple[int, str]]
    isSecondary: bool
    isAlone: bool
    isEN: bool
    lineNum: int

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


def preproc_line_text(line: SongLine, lineNum: int = 0) -> KLine:
    timedeltaUpToIdx = reduce(
        lambda a, b: a + [a[-1] + b.length], line.syllables, [timedelta(0)]
    )

    kLine = KLine(
        start=line.start,
        end=line.end,
        duration=line.end - line.start,
        kara=[],
        text=line.romaji,
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
            duration=syl.length,
            end=accLength + syl.length,
            text=syl.text,
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


def preproc_line_text_en(line: SongLine, lineNum: int = 0) -> KLine:
    timedeltaUpToIdx = reduce(
        lambda a, b: a + [a[-1] + b.length], line.syllables, [timedelta(0)]
    )
    kLineEN = KLine(
        start=line.start,
        end=line.end,
        duration=line.end - line.start,
        kara=[],
        text=line.en,
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
        duration=timedelta(),
        chars=[],
        text=line.en,
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
            karaDuration=timedelta(),
            sylI=i,
            syl=kSylEN,
            line=kLineEN,
        )
        for i, char, in enumerate(kLineEN.text)
    ]

    kLineEN.kara.append(kSylEN)

    return kLineEN
