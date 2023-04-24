from dataclasses import dataclass, field
from datetime import timedelta
import pyass
from typing import Optional, TypeVar

Modifier = TypeVar("Modifier", bound="Modifier")
Modifiers = TypeVar("Modifiers", bound="Modifiers")


@dataclass
class LineModifier:
    shouldForceSecondary: bool = False
    shouldDiscard: bool = False

    offset: timedelta = timedelta()
    trim: timedelta = timedelta()

    shouldOverwriteStyle: bool = False
    breakpoints: list[int] = field(default_factory=list)
    actors: list[str] = field(default_factory=list)

    shouldOverwriteKaraoke: bool = False
    start: timedelta = timedelta()
    end: timedelta = timedelta()
    syllableLengths: list[timedelta] = field(default_factory=list)

    shouldRunKaraTemplater: bool = False

    shouldOverwriteTitle: bool = False
    titleRomaji: str = ""
    titleEN: str = ""

    shouldOverwriteArtist: bool = False
    artist: str = ""

    newOrder: Optional[list[int]] = None


@dataclass
class Modifier:
    operation: str = ""
    start: int = 0
    end: Optional[int] = None
    rest: list[str] = field(default_factory=list)

    @staticmethod
    def parse(s: str) -> Modifier:
        m = Modifier()

        parts = s.split(",")
        m.operation = parts[0].lower()

        if parts[1] != "-":
            lineParts = parts[1].split("-")
            if len(lineParts) == 1:
                lineNum = int(lineParts[0])

                m.start = lineNum - 1
                m.end = lineNum
            elif len(lineParts) == 2:
                start, end = lineParts
                m.start = int(start) - 1
                if end:
                    m.end = int(end)

        m.rest = parts[2:]

        return m


class Modifiers(list[Modifier]):
    @staticmethod
    def parse(s: str) -> Modifiers:
        if s == "":
            return Modifiers()

        return Modifiers([Modifier.parse(match) for match in s.split(";")])

    def toLineModifiers(self, maxLines=100) -> list[LineModifier]:
        ret = [LineModifier() for _ in range(maxLines)]

        for modifier in self:
            if modifier.operation == "discard":
                for i in range(
                    modifier.start,
                    modifier.end if modifier.end is not None else maxLines,
                ):
                    ret[i].shouldDiscard = True
            elif modifier.operation == "offset":
                offsetStr = modifier.rest[0]
                offset = pyass.timedelta.parse(offsetStr)

                for i in range(
                    modifier.start,
                    modifier.end if modifier.end is not None else maxLines,
                ):
                    ret[i].offset += offset
            elif modifier.operation == "secondary":
                for i in range(
                    modifier.start,
                    modifier.end if modifier.end is not None else maxLines,
                ):
                    ret[i].shouldForceSecondary = True
            elif modifier.operation == "style":
                if len(modifier.rest) == 1 and not ":" in modifier.rest[0]:
                    # Simple case, entire line is the same actor
                    actor = modifier.rest[0]
                    for i in range(
                        modifier.start,
                        modifier.end if modifier.end is not None else maxLines,
                    ):
                        ret[i].shouldOverwriteStyle = True
                        ret[i].breakpoints = [0]
                        ret[i].actors = [actor]
                else:
                    breakpoints = []
                    actors = []

                    for breakpointToActorStr in modifier.rest:
                        breakpoint, actor = breakpointToActorStr.split(":")
                        breakpoints.append(int(breakpoint) - 1)
                        actors.append(actor)

                    for i in range(
                        modifier.start,
                        modifier.end if modifier.end is not None else maxLines,
                    ):
                        ret[i].shouldOverwriteStyle = True
                        ret[i].breakpoints = breakpoints
                        ret[i].actors = actors
            elif modifier.operation == "karaoke":
                ret[modifier.start].shouldOverwriteKaraoke = True
                ret[modifier.start].start = pyass.timedelta.parse(modifier.rest[0])
                ret[modifier.start].end = pyass.timedelta.parse(modifier.rest[1])
                ret[modifier.start].syllableLengths = list(
                    map(
                        lambda x: pyass.timedelta(centiseconds=int(x)),
                        modifier.rest[2:],
                    )
                )
            elif modifier.operation == "templater":
                ret[0].shouldRunKaraTemplater = True
            elif modifier.operation == "trim":
                trim = pyass.timedelta.parse(modifier.rest[0])

                for i in range(
                    modifier.start,
                    modifier.end if modifier.end is not None else maxLines,
                ):
                    ret[i].trim += trim
            elif modifier.operation == "title":
                ret[0].shouldOverwriteTitle = True
                ret[0].titleRomaji = modifier.rest[0]
                if len(modifier.rest) > 1:
                    ret[0].titleEN = modifier.rest[1]
            elif modifier.operation == "artist":
                ret[0].shouldOverwriteArtist = True
                ret[0].artist = ", ".join([s.strip() for s in modifier.rest])
            elif modifier.operation == "reorder":
                ret[0].newOrder = [int(s) - 1 for s in modifier.rest]

        return ret
