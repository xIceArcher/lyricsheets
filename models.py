from dataclasses import dataclass, field
from datetime import timedelta

@dataclass
class SongTitle:
    romaji: str = ''
    en: str = ''

@dataclass
class SongLineSyllable:
    length: timedelta = timedelta()
    text: str = ''

@dataclass
class SongLine:
    en: str = ''
    karaokeEffect: str = ''
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
        return ''.join([syllable.text for syllable in self.syllables])

@dataclass
class SongCreators:
    artist: str = ''
    composers: list[str] = field(default_factory=list)
    arrangers: list[str] = field(default_factory=list)
    writers: list[str] = field(default_factory=list)

@dataclass
class Song:
    title: SongTitle = SongTitle()
    creators: SongCreators = SongCreators()
    lyrics: list[SongLine] = field(default_factory=list)

    shouldRunKaraokeTemplater: bool = False
