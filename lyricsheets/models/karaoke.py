from dataclasses import dataclass
from datetime import timedelta
from functools import reduce
from typing import Sequence, TypeVar

from lyricsheets.models import SongLine
from lyricsheets.fonts import FontScaler

import pyass
from pyass import Style

KChar = TypeVar("KChar", bound="KChar")
KSyl = TypeVar("KSyl", bound="KSyl")
KLine = TypeVar("KLine", bound="KLine")


def style_check(func):
    def style_wrapper(*args):
        if not args[0].style:
            raise StyleNotBoundException()
        return func(*args)

    return style_wrapper


def style_check(func):
    def style_wrapper(*args):
        if not args[0].style:
            raise StyleNotBoundException()
        return func(*args)

    return style_wrapper


def style_check(func):
    def style_wrapper(*args):
        if not args[0].style:
            raise StyleNotBoundException()
        return func(*args)

    return style_wrapper


def style_check(func):
    def style_wrapper(*args):
        if not args[0].style:
            raise StyleNotBoundException()
        return func(*args)

    return style_wrapper


@dataclass
class KChar:
    char: str
    i: int
    sylI: int
    line: KLine
    syl: KSyl
    fadeOffset: timedelta = timedelta()
    karaStart: timedelta = timedelta()
    karaEnd: timedelta = timedelta()

    _width: float = 0
    _left: float = 0

    @property
    def karaDuration(self) -> timedelta:
        return self.karaEnd - self.karaStart

    @property
    @style_check
    def width(self) -> float:
        return self._width

    @property
    @style_check
    def left(self) -> float:
        return self._left

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
        return self._left + self._width / 2

    @property
    def right(self) -> float:
        return self._left + self._width

    @property
    def middle(self) -> float:
        return self.top + self.height / 2

    @property
    def bottom(self) -> float:
        return self.top + self.height

    def _calculate_sizing(self):
        fontScaler = FontScaler(self.style)
        self._width = fontScaler.get_length(self.char)


@dataclass
class KSyl:
    start: timedelta
    end: timedelta
    chars: list[KChar]
    inlineFx: str
    i: int
    line: KLine

    _width: float = 0
    _preSpaceWidth: float = 0
    _postSpaceWidth: float = 0
    _left: float = 0

    @property
    def text(self) -> str:
        return "".join(char.char for char in self.chars)

    @property
    def duration(self) -> timedelta:
        return self.end - self.start

    @property
    @style_check
    def width(self) -> float:
        return self._width

    @property
    @style_check
    def preSpaceWidth(self) -> float:
        return self._preSpaceWidth

    @property
    @style_check
    def postSpaceWidth(self) -> float:
        return self._postSpaceWidth

    @property
    @style_check
    def left(self) -> float:
        return self._left

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

    def calculate_char_kara_times(self, style: Style):
        fontScaler = FontScaler(style)

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

    def _calculate_sizing(self):
        fontScaler = FontScaler(self.style)

        text = self.text
        stripped = text.strip()

        numPreSpaces = len(text) - len(text.lstrip())
        numPostSpaces = len(text) - len(text.rstrip())

        self._width = fontScaler.get_length(stripped)
        self._preSpaceWidth = (
            fontScaler.get_length(text[:numPreSpaces]) if numPreSpaces else 0
        )
        self._postSpaceWidth = (
            fontScaler.get_length(text[-(numPostSpaces):]) if numPostSpaces else 0
        )

        for char in self.chars:
            char._calculate_sizing()

    def _calculate_positions(self, curX: float):
        self._left = curX + self.preSpaceWidth

        curSylX = curX
        for char in self.chars:
            char._left = curSylX
            curSylX += char._width


@dataclass
class KLine:
    start: timedelta
    end: timedelta
    kara: list[KSyl]
    startActor: str
    actorSwitches: list[tuple[timedelta, str]]
    isSecondary: bool
    isAlone: bool
    isEN: bool
    lineNum: int

    _width: float = 0
    _height: float = 0
    _left: float = 0
    _top: float = 0
    _x: float = 0
    _y: float = 0

    @property
    def text(self) -> str:
        return "".join(c.char for text in self.kara for c in text.chars)

    @property
    def duration(self) -> timedelta:
        return self.end - self.start

    @property
    def chars(self) -> Sequence[KChar]:
        return [char for k in self.kara for char in k.chars]

    @property
    @style_check
    def width(self) -> float:
        return self._width

    @property
    @style_check
    def height(self) -> float:
        return self._height

    @property
    @style_check
    def left(self) -> float:
        return self._left

    @property
    @style_check
    def top(self) -> float:
        return self._top

    @property
    @style_check
    def x(self) -> float:
        return self._x

    @property
    @style_check
    def y(self) -> float:
        return self._y

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

    def calculate_char_offsets(self, style: Style, transitionDuration: timedelta):
        self.calculate_char_fade_offsets(style, transitionDuration)
        for k in self.kara:
            k.calculate_char_kara_times(style)

    def calculate_char_fade_offsets(self, style: Style, transitionDuration: timedelta):
        fontScaler = FontScaler(style)

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

    def bind_style(self, style: Style):
        self.style = style
        for kara in self.kara:
            kara.style = style
            for char in kara.chars:
                char.style = self.style

        self._calculate_sizing()
        self._calculate_positions()

    def _calculate_sizing(self):
        fontScaler = FontScaler(self.style)

        self._width = fontScaler.get_length(self.text)
        self._height = self.style.fontSize

        for syl in self.kara:
            syl._calculate_sizing()

    def _calculate_positions(self, resX: int = 1920, resY: int = 1080):
        # Horizontal positioning
        if self.style.alignment in {
            pyass.Alignment.BOTTOM_LEFT,
            pyass.Alignment.CENTER_LEFT,
            pyass.Alignment.TOP_LEFT,
        }:
            # Left aligned
            self._left = self.style.marginL
            self._x = self.left
        elif self.style.alignment in {
            pyass.Alignment.BOTTOM,
            pyass.Alignment.CENTER,
            pyass.Alignment.TOP,
        }:
            # Centered
            self._left = (
                resX + self.style.marginL - self.style.marginR - self.width
            ) / 2
            self._x = self.center
            # Left aligned
            self._left = self.style.marginL
            self._x = self.left
        elif self.style.alignment in {
            pyass.Alignment.BOTTOM,
            pyass.Alignment.CENTER,
            pyass.Alignment.TOP,
        }:
            # Centered
            self._left = (
                resX + self.style.marginL - self.style.marginR - self.width
            ) / 2
            self._x = self.center
        else:
            # Right aligned
            self._left = resX - self.style.marginR - self.width
            self._x = self.right

        # Vertical positioning
        if self.style.alignment in {
            pyass.Alignment.BOTTOM_LEFT,
            pyass.Alignment.BOTTOM,
            pyass.Alignment.BOTTOM_RIGHT,
        }:
            # Bottom aligned
            self._top = resY - self.style.marginV - self.height
            self._y = self.bottom
        elif self.style.alignment in {
            pyass.Alignment.CENTER_LEFT,
            pyass.Alignment.CENTER,
            pyass.Alignment.CENTER_RIGHT,
        }:
            # Middle aligned
            self._top = (
                resY - self.style.marginV * 2 - self.height
            ) / 2 + self.style.marginV
            self._y = self.middle
        else:
            # Top aligned
            self._top = self.style.marginV
            self._y = self.top

        curX = self.left
        for syl in self.kara:
            syl._calculate_positions(curX)
            curX += syl.preSpaceWidth + syl.width + syl.postSpaceWidth


class StyleNotBoundException(Exception):
    pass


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
        inlineFx="",
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
