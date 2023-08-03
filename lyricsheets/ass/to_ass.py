from collections.abc import Sequence, Mapping
from datetime import timedelta
from abc import ABC, abstractmethod

import pyass

from lyricsheets.models import Song, SongLine

from .consts import *
from ..models.karaoke import *


# Timings
TITLE_EVENT_DURATION = timedelta(seconds=5)


class Effect(ABC):
    @abstractmethod
    def to_events(
        self, song: Song, actorToStyle: Mapping[str, Sequence[pyass.Tag]]
    ) -> Sequence[pyass.Event]:
        ...


class LyricsEffect(Effect):
    def __init__(
        self,
        shouldPrintTitle: bool = True,
        dividerStyle: pyass.Style = DIVIDER_STYLE,
        titleStyle: pyass.Style = TITLE_STYLE,
        titleEventDuration: timedelta = TITLE_EVENT_DURATION,
        titleCardTags: pyass.Tags = TITLE_CARD_TAGS,
    ) -> None:
        self.shouldPrintTitle = shouldPrintTitle
        self.dividerStyle = dividerStyle
        self.titleStyle = titleStyle
        self.titleEventDuration = titleEventDuration
        self.titleCardTags = titleCardTags

    def to_events(
        self, song: Song, actorToStyle: Mapping[str, Sequence[pyass.Tag]]
    ) -> Sequence[pyass.Event]:
        return [
            self.to_divider_event(song, song.title.romaji),
            self.to_title_event(song, self.shouldPrintTitle),
            self.to_divider_event(song, "Romaji"),
            *self.to_romaji_events(song.lyrics, actorToStyle),
            self.to_divider_event(song, "English"),
            *self.to_en_events(song.lyrics, actorToStyle),
        ]

    def to_divider_event(self, song: Song, dividerText: str) -> pyass.Event:
        return pyass.Event(
            format=pyass.EventFormat.COMMENT,
            style=self.dividerStyle.name,
            end=song.end,
            text=dividerText,
        )

    def to_title_event(self, song: Song, shouldPrintTitle: bool) -> pyass.Event:
        s: list[str] = [song.title.romaji]

        if song.title.en:
            s.append(f"({song.title.en})")

        s.append(song.creators.artist)

        if song.creators.composers:
            s.append(f"Composed by: {', '.join(song.creators.composers)}")

        if song.creators.arrangers:
            s.append(f"Arranged by: {', '.join(song.creators.arrangers)}")

        if song.creators.writers:
            s.append(f"Written by: {', '.join(song.creators.writers)}")

        return pyass.Event(
            format=pyass.EventFormat.DIALOGUE
            if shouldPrintTitle
            else pyass.EventFormat.COMMENT,
            style=self.titleStyle.name,
            end=self.titleEventDuration,
            parts=[
                pyass.EventPart(tags=self.titleCardTags, text=r"\N".join(s)),
            ],
        )

    @abstractmethod
    def to_romaji_events(
        self,
        songLines: Sequence[SongLine],
        actorToStyle: Mapping[str, Sequence[pyass.Tag]],
    ) -> Sequence[pyass.Event]:
        ...

    @abstractmethod
    def to_en_events(
        self,
        songLines: Sequence[SongLine],
        actorToStyle: Mapping[str, Sequence[pyass.Tag]],
    ) -> Sequence[pyass.Event]:
        ...


class KaraokeEffect(LyricsEffect):
    def to_romaji_events(
        self,
        songLines: Sequence[SongLine],
        actorToStyle: Mapping[str, Sequence[pyass.Tag]],
    ) -> Sequence[pyass.Event]:
        romajiLines = [
            to_romaji_k_line(line, i + 1) for i, line in enumerate(songLines)
        ]
        return self.to_romaji_k_events(romajiLines, actorToStyle)

    def to_en_events(
        self,
        songLines: Sequence[SongLine],
        actorToStyle: Mapping[str, Sequence[pyass.Tag]],
    ) -> Sequence[pyass.Event]:
        enLines = [
            to_en_k_line(line, to_romaji_k_line(line, i + 1), i + 1)
            for i, line in enumerate(songLines)
        ]
        return self.to_en_k_events(enLines, actorToStyle)

    @abstractmethod
    def to_romaji_k_events(
        self,
        songLines: Sequence[KLine],
        actorToStyle: Mapping[str, Sequence[pyass.Tag]],
    ) -> Sequence[pyass.Event]:
        ...

    @abstractmethod
    def to_en_k_events(
        self,
        songLines: Sequence[KLine],
        actorToStyle: Mapping[str, Sequence[pyass.Tag]],
    ) -> Sequence[pyass.Event]:
        ...


def get_line_format(line: KLine) -> pyass.EventFormat:
    return (
        pyass.EventFormat.COMMENT
        if line.isAlone and line.isEN
        else pyass.EventFormat.DIALOGUE
    )


_effects: dict[str, Effect] = {}


def register_effect(name: str, effect: Effect):
    _effects[name] = effect


def retrieve_effect(name: str):
    return _effects[name]
