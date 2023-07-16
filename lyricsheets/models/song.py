from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Optional

from dataclass_wizard import JSONWizard

from .modifier import Modifier, Modifiers


@dataclass
class SongTitle:
    romaji: str = ""
    en: str = ""


@dataclass
class SongLineSyllable:
    length: timedelta = timedelta()
    text: str = ""


@dataclass
class SongLine:
    en: str = ""
    karaokeEffect: Optional[str] = None
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

    title: SongTitle = SongTitle()
    creators: SongCreators = SongCreators()
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
        for line, modifier in zip(self.lyrics, lineModifiers):
            if modifier.shouldForceSecondary:
                line.isSecondary = True

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

            if modifier.shouldOverwriteStyle:
                line.breakpoints = modifier.breakpoints
                line.actors = modifier.actors

            if modifier.shouldOverwriteTitle:
                self.title.romaji = modifier.titleRomaji
                self.title.en = modifier.titleEN

            if modifier.shouldOverwriteArtist:
                self.creators.artist = modifier.artist

            if modifier.shouldDiscard:
                continue

            outLyrics.append(line)

        if lineModifiers[0].newOrder is None:
            self.lyrics = outLyrics
            return self

        self.lyrics = []
        for lineNum in lineModifiers[0].newOrder:
            self.lyrics.append(outLyrics[lineNum])

        return self
