from dataclasses import dataclass, field
from datetime import timedelta
from typing import Any
from copy import deepcopy

from dataclass_wizard import JSONWizard

from .modifier import Modifiers


@dataclass
class SongTitle:
    romaji: str = ""
    en: str = ""


@dataclass
class SongLineSyllable:
    length: timedelta = timedelta()
    text: str = ""


@dataclass
class SongLine(JSONWizard):
    idxInSong: int = -1
    en: str = ""
    isSecondary: bool = False
    start: timedelta = timedelta()
    end: timedelta = timedelta()
    syllables: list[SongLineSyllable] = field(default_factory=list)
    actors: list[str] = field(default_factory=list)
    breakpoints: list[int] = field(default_factory=list)

    @property
    def length(self) -> timedelta:
        return self.end - self.start

    @property
    def romaji(self) -> str:
        return "".join([syllable.text for syllable in self.syllables])

    def merge(self, other: dict[str, Any]) -> None:
        # This method cannot directly take a SongLine
        # Since we would then be unable to determine whether the field doesn't exist (e.g. isSecondary: null)
        # vs the field is its default value (e.g. isSecondary: false)
        otherObj = SongLine().from_dict(other)
        for key in [
            "en",
            "isSecondary",
            "start",
            "end",
            "syllables",
            "actors",
            "breakpoints",
        ]:
            if key in other:
                setattr(self, key, getattr(otherObj, key))


@dataclass
class SongCreators:
    artist: str = ""
    composers: list[str] = field(default_factory=list)
    arrangers: list[str] = field(default_factory=list)
    writers: list[str] = field(default_factory=list)


@dataclass
class Song(JSONWizard):
    class _(JSONWizard.Meta):
        skip_defaults = True

    title: SongTitle = field(default_factory=SongTitle)
    creators: SongCreators = field(default_factory=SongCreators)
    lyrics: list[SongLine] = field(default_factory=list)

    @property
    def start(self) -> timedelta:
        if not self.lyrics:
            return timedelta()

        return self.lyrics[0].start

    @property
    def end(self) -> timedelta:
        if not self.lyrics:
            return timedelta()

        return self.lyrics[-1].end

    def modify(self, modifiers: Modifiers):
        lineModifiers = modifiers.toLineModifiers(maxLines=len(self.lyrics))
        outLyrics = []
        extraLyrics = []
        for line, modifier in zip(self.lyrics, lineModifiers):
            # Song-related modifiers
            if modifier.shouldOverwriteTitle:
                self.title.romaji = modifier.titleRomaji
                self.title.en = modifier.titleEN

            if modifier.shouldOverwriteArtist:
                self.creators.artist = modifier.artist

            # If discard, do nothing
            if modifier.shouldDiscard:
                continue

            # Line display-related modifiers
            if modifier.shouldForceSecondary:
                line.isSecondary = True

            if modifier.shouldOverwriteStyle:
                line.breakpoints = modifier.breakpoints
                line.actors = modifier.actors

            # Source line modifiers
            if modifier.shouldOverwriteSourceLine:
                line.merge(modifier.overwriteObj)

            # Timing modifiers
            if modifier.shouldOverwriteKaraoke:
                line.start = modifier.start + modifier.offset
                line.end = modifier.end + modifier.offset
                for syllable, newTime in zip(line.syllables, modifier.syllableLengths):
                    syllable.length = newTime
            else:
                line.start *= modifier.retimeScaleFactor
                line.end *= modifier.retimeScaleFactor
                for syllable in line.syllables:
                    syllable.length *= modifier.retimeScaleFactor

                line.start += modifier.offset
                line.end += modifier.offset - modifier.trim
                line.syllables[-1].length -= modifier.trim

            # Duplicate modifiers
            if modifier.dupes:
                for offset in modifier.dupes:
                    dupeLine = deepcopy(line)
                    dupeLine.idxInSong = len(self.lyrics) + len(extraLyrics)
                    dupeLine.start += offset
                    dupeLine.end += offset

                    extraLyrics.append(dupeLine)

            outLyrics.append(line)
        
        outLyrics.extend(extraLyrics)

        if len(lineModifiers) == 0 or lineModifiers[0].newOrder is None:
            self.lyrics = outLyrics
            return self

        self.lyrics = []
        for lineNum in lineModifiers[0].newOrder:
            self.lyrics.append(outLyrics[lineNum])

        return self
