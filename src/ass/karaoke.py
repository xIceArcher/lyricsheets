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
    fadeOffset: timedelta()
    karaStart: timedelta()
    karaEnd: timedelta()
    karaDuration: timedelta()
    i: int
    sylI: int

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

    @property
    def chars(self) -> Sequence[KChar]:
        return [char for k in self.kara for char in k.chars]


def preproc_line_text(
    line: SongLine, style: Style, transitionDuration: timedelta
) -> KLine:
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
    )

    fontScaler = FontScaler(style.fontName, style.fontSize)

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

        syllableCharLengths = [
            timedelta(milliseconds=c * 10)
            for c in fontScaler.split_by_rendered_width(
                pyass.timedelta(syl.length).total_centiseconds(), kSyl.text
            )
        ]

        sylAccLength = accLength

        for c, syllableCharLength in zip(syl.text, syllableCharLengths):
            kChar = KChar(
                char=c,
                karaStart=sylAccLength,
                karaDuration=syllableCharLength,
                karaEnd=sylAccLength + syllableCharLength,
                i=totalChars,
                sylI=len(kSyl.chars),
                fadeOffset=timedelta(),
                syl=kSyl,
                line=kLine,
            )

            sylAccLength = kChar.karaEnd
            kSyl.chars.append(kChar)
            totalChars += 1

        kLine.kara.append(kSyl)

        accLength += syl.length

    lineCharTimes = [
        timedelta(milliseconds=m)
        for m in fontScaler.split_by_rendered_width(
            pyass.timedelta(transitionDuration).total_milliseconds(), kLine.text
        )
    ]

    charAccTime = timedelta()
    for char, lineCharTime in zip(kLine.chars, lineCharTimes):
        char.fadeOffset = charAccTime
        charAccTime += lineCharTime

    return kLine


def preproc_line_text_en(
    line: SongLine, style: Style, transitionDuration: timedelta
) -> KLine:
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
    )

    fontScaler = FontScaler(style.fontName, style.fontSize)
    lineCharTimes = [
        timedelta(milliseconds=m)
        for m in fontScaler.split_by_rendered_width(
            pyass.timedelta(transitionDuration).total_milliseconds(), line.en
        )
    ]

    lineCharTimes = [timedelta()] + list(accumulate(lineCharTimes))[:-1]

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
            fadeOffset=lineCharTime,
            i=i,
            karaStart=timedelta(),
            karaEnd=timedelta(),
            karaDuration=timedelta(),
            sylI=i,
            syl=kSylEN,
            line=kLineEN,
        )
        for i, (char, lineCharTime) in enumerate(zip(kLineEN.text, lineCharTimes))
    ]

    kLineEN.kara.append(kSylEN)

    return kLineEN
