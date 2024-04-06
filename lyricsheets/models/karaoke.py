from dataclasses import dataclass
from datetime import timedelta
from functools import cached_property, reduce
from itertools import accumulate
import operator
from typing import Optional, Sequence, TypeVar

import pyass

from lyricsheets.models import SongLine
from lyricsheets.fonts import FontScaler


KChar = TypeVar("KChar", bound="KChar")
KSyl = TypeVar("KSyl", bound="KSyl")
KLine = TypeVar("KLine", bound="KLine")


@dataclass
class KChar:
    text: str
    idxInLine: int
    line: KLine
    idxInSyl: int
    syl: KSyl

    ### Property aliases to maintain compatibility with Aegisub variable namings
    @property
    def char(self) -> str:
        return self.text

    @char.setter
    def char(self, char: str):
        self.text = char

    @property
    def i(self) -> int:
        return self.idxInLine

    @i.setter
    def i(self, i: int):
        self.idxInLine = i

    @property
    def sylI(self) -> int:
        return self.idxInSyl

    @sylI.setter
    def sylI(self, sylI: int):
        self.idxInSyl = sylI

    @property
    def karaStart(self) -> timedelta:
        return self.start

    @property
    def karaEnd(self) -> timedelta:
        return self.end

    ### End Aegisub compatibility variables

    @property
    def start(self) -> timedelta:
        return self.syl._charKaraTimes[self.idxInSyl]

    @property
    def end(self) -> timedelta:
        return self.syl._charKaraTimes[self.idxInSyl + 1]

    @property
    def duration(self) -> timedelta:
        return self.end - self.start

    @property
    def style(self) -> pyass.Style:
        return self.line.style

    @cached_property
    def width(self) -> float:
        return FontScaler(self.style).get_length(self.text)

    @cached_property
    def left(self) -> float:
        if self.idxInLine == 1:
            return self.line.left

        prevChar = self.line.chars[self.idxInLine - 2]
        return prevChar.left + prevChar.width

    @property
    def height(self) -> float:
        return self.line.height

    @property
    def top(self) -> float:
        return self.line.top

    @property
    def y(self) -> float:
        return self.line.y

    @property
    def center(self) -> float:
        return self.left + self.width / 2

    @property
    def right(self) -> float:
        return self.left + self.width

    @property
    def middle(self) -> float:
        return self.top + self.height / 2

    @property
    def bottom(self) -> float:
        return self.top + self.height

    @property
    def fadeOffset(self) -> timedelta:
        return self.line._charFadeOffsets[self.idxInLine]


@dataclass
class KSyl:
    start: timedelta
    end: timedelta
    chars: list[KChar]
    inlineFx: str
    idxInLine: int
    line: KLine

    ### Property aliases to maintain compatibility with Aegisub variable namings
    @property
    def i(self) -> int:
        return self.idxInLine

    @i.setter
    def i(self, i: int):
        self.idxInLine = i

    ### End Aegisub compatibility variables

    @property
    def text(self) -> str:
        return "".join(char.text for char in self.chars)

    @property
    def duration(self) -> timedelta:
        return self.end - self.start

    @property
    def style(self) -> pyass.Style:
        return self.line.style

    @cached_property
    def width(self) -> float:
        return FontScaler(self.style).get_length(self.text.strip())

    @cached_property
    def preSpaceWidth(self) -> float:
        numPreSpaces = len(self.text) - len(self.text.lstrip())
        return (
            FontScaler(self.style).get_length(self.text[:numPreSpaces])
            if numPreSpaces
            else 0
        )

    @cached_property
    def postSpaceWidth(self) -> float:
        numPostSpaces = len(self.text) - len(self.text.rstrip())
        return (
            FontScaler(self.style).get_length(self.text[-(numPostSpaces):])
            if numPostSpaces
            else 0
        )

    @cached_property
    def left(self) -> float:
        if self.idxInLine == 1:
            return self.line.left + self.preSpaceWidth

        prevSyl = self.line.syls[self.idxInLine - 2]
        return (
            prevSyl.left + prevSyl.width + prevSyl.postSpaceWidth + self.preSpaceWidth
        )

    @property
    def height(self) -> float:
        return self.line.height

    @property
    def top(self) -> float:
        return self.line.top

    @property
    def y(self) -> float:
        return self.line.y

    @property
    def center(self) -> float:
        return self.left + self.width / 2

    @property
    def right(self) -> float:
        return self.left + self.width

    @property
    def middle(self) -> float:
        return self.top + self.height / 2

    @property
    def bottom(self) -> float:
        return self.top + self.height

    @cached_property
    def _charKaraTimes(self) -> list[timedelta]:
        syllableCharLengths = [
            timedelta(milliseconds=c * 10)
            for c in FontScaler(self.style).split_by_rendered_width(
                pyass.timedelta(self.duration).total_centiseconds(), self.text
            )
        ]

        return list(accumulate(syllableCharLengths, operator.add, initial=self.start))


@dataclass
class KLine:
    start: timedelta
    end: timedelta
    syls: list[KSyl]
    startActor: str
    actorSwitches: list[tuple[timedelta, str]]
    isSecondary: bool
    isAlone: bool
    idxInSong: int

    isEN: bool = False
    _style: Optional[pyass.Style] = None
    _resX: int = 1920
    resY: int = 1080
    _transitionDuration: timedelta = timedelta()

    ### Property aliases to maintain compatibility with Aegisub variable namings
    @property
    def kara(self) -> list[KSyl]:
        return self.syls

    @kara.setter
    def kara(self, kara: list[KSyl]):
        self.syls = kara

    ### End Aegisub compatibility variables

    @property
    def text(self) -> str:
        return "".join(c.text for text in self.syls for c in text.chars)

    @property
    def duration(self) -> timedelta:
        return self.end - self.start

    @property
    def chars(self) -> Sequence[KChar]:
        return [char for k in self.syls for char in k.chars]

    @property
    def style(self) -> pyass.Style:
        if not self._style:
            raise StyleNotBoundException()

        return self._style

    @style.setter
    def style(self, style: pyass.Style):
        if self._style == style:
            return

        # Invalidate cached properties
        self.__dict__.pop("width", None)
        self.__dict__.pop("_charFadeOffsets", None)

        for syl in self.syls:
            syl.__dict__.pop("width", None)
            syl.__dict__.pop("preSpaceWidth", None)
            syl.__dict__.pop("postSpaceWidth", None)
            syl.__dict__.pop("left", None)
            syl.__dict__.pop("_charKaraTimes", None)

        for char in self.chars:
            char.__dict__.pop("width", None)
            char.__dict__.pop("left", None)

        self._style = style

    @property
    def resX(self) -> int:
        return self._resX

    @resX.setter
    def resX(self, resX: int):
        if self._resX == resX:
            return

        # Invalidate cached properties
        for syl in self.syls:
            syl.__dict__.pop("left", None)

        for char in self.chars:
            char.__dict__.pop("left", None)

        self._resX = resX

    @property
    def transitionDuration(self) -> timedelta:
        return self._transitionDuration

    @transitionDuration.setter
    def transitionDuration(self, transitionDuration: timedelta):
        if self._transitionDuration == transitionDuration:
            return

        # Invalidate cached properties
        self.__dict__.pop("_charFadeOffsets", None)

        for syl in self.syls:
            syl.__dict__.pop("_charKaraTimes", None)

        self._transitionDuration = transitionDuration

    @cached_property
    def width(self) -> float:
        return FontScaler(self.style).get_length(self.text)

    @property
    def height(self) -> float:
        return self.style.fontSize

    @property
    def left(self) -> float:
        if self.style.alignment in {
            pyass.Alignment.BOTTOM_LEFT,
            pyass.Alignment.CENTER_LEFT,
            pyass.Alignment.TOP_LEFT,
        }:
            # Left aligned
            return self.style.marginL
        elif self.style.alignment in {
            pyass.Alignment.BOTTOM,
            pyass.Alignment.CENTER,
            pyass.Alignment.TOP,
        }:
            # Middle aligned
            return (
                self.resX + self.style.marginL - self.style.marginR - self.width
            ) / 2
        else:
            # Right aligned
            return self.resX - self.style.marginR - self.width

    @property
    def top(self) -> float:
        if self.style.alignment in {
            pyass.Alignment.BOTTOM_LEFT,
            pyass.Alignment.BOTTOM,
            pyass.Alignment.BOTTOM_RIGHT,
        }:
            # Bottom aligned
            return self.resY - self.style.marginV - self.height
        elif self.style.alignment in {
            pyass.Alignment.CENTER_LEFT,
            pyass.Alignment.CENTER,
            pyass.Alignment.CENTER_RIGHT,
        }:
            # Center aligned
            return (
                self.resY - self.style.marginV * 2 - self.height
            ) / 2 + self.style.marginV
        else:
            # Top aligned
            return self.style.marginV

    @property
    def x(self) -> float:
        if self.style.alignment in {
            pyass.Alignment.BOTTOM_LEFT,
            pyass.Alignment.CENTER_LEFT,
            pyass.Alignment.TOP_LEFT,
        }:
            return self.left
        elif self.style.alignment in {
            pyass.Alignment.BOTTOM,
            pyass.Alignment.CENTER,
            pyass.Alignment.TOP,
        }:
            return self.center
        else:
            return self.right

    @property
    def y(self) -> float:
        if self.style.alignment in {
            pyass.Alignment.BOTTOM_LEFT,
            pyass.Alignment.BOTTOM,
            pyass.Alignment.BOTTOM_RIGHT,
        }:
            return self.bottom
        elif self.style.alignment in {
            pyass.Alignment.CENTER_LEFT,
            pyass.Alignment.CENTER,
            pyass.Alignment.CENTER_RIGHT,
        }:
            return self.middle
        else:
            return self.top

    @property
    def center(self) -> float:
        return self.left + self.width / 2

    @property
    def right(self) -> float:
        return self.left + self.width

    @property
    def middle(self) -> float:
        return self.top + self.height / 2

    @property
    def bottom(self) -> float:
        return self.top + self.height

    @cached_property
    def _charFadeOffsets(self) -> list[timedelta]:
        lineCharTimes = [
            timedelta(milliseconds=m)
            for m in FontScaler(self.style).split_by_rendered_width(
                pyass.timedelta(self.transitionDuration).total_milliseconds(), self.text
            )
        ]

        return list(accumulate(lineCharTimes, operator.add, initial=timedelta()))


class StyleNotBoundException(Exception):
    pass


def to_romaji_k_line(line: SongLine) -> KLine:
    timedeltaUpToIdx = reduce(
        lambda a, b: a + [a[-1] + b.length], line.syllables, [timedelta(0)]
    )

    kLine = KLine(
        start=line.start,
        end=line.end,
        syls=[],
        startActor=line.actors[0],
        actorSwitches=[
            (timedeltaUpToIdx[breakpoint], actor)
            for breakpoint, actor in zip(line.breakpoints, line.actors)
            if breakpoint != 0
        ],
        isSecondary=line.isSecondary,
        isAlone=line.romaji == line.en,
        isEN=False,
        idxInSong=line.idxInSong,
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
            idxInLine=len(kLine.syls)+1,
            line=kLine,
        )

        for c in syl.text:
            kChar = KChar(
                text=c,
                idxInLine=totalChars,
                idxInSyl=len(kSyl.chars)+1,
                syl=kSyl,
                line=kLine,
            )

            kSyl.chars.append(kChar)
            totalChars += 1

        kLine.syls.append(kSyl)
        accLength += syl.length

    return kLine


def to_en_k_line(line: SongLine) -> KLine:
    timedeltaUpToIdx = reduce(
        lambda a, b: a + [a[-1] + b.length], line.syllables, [timedelta(0)]
    )
    kLineEN = KLine(
        start=line.start,
        end=line.end,
        syls=[],
        startActor=line.actors[0],
        actorSwitches=[
            (timedeltaUpToIdx[breakpoint], actor)
            for breakpoint, actor in zip(line.breakpoints, line.actors)
            if breakpoint != 0
        ],
        isSecondary=line.isSecondary,
        isAlone=line.romaji == line.en,
        isEN=True,
        idxInSong=line.idxInSong,
    )

    kSylEN = KSyl(
        start=line.start,
        end=line.start,
        chars=[],
        inlineFx="",
        idxInLine=1,
        line=kLineEN,
    )

    kSylEN.chars = [
        KChar(
            text=char,
            idxInLine=i+1,
            idxInSyl=i+1,
            syl=kSylEN,
            line=kLineEN,
        )
        for i, char, in enumerate(line.en)
    ]

    kLineEN.syls.append(kSylEN)
    return kLineEN
