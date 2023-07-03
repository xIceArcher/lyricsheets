from collections.abc import Sequence, Mapping
from datetime import timedelta
from abc import ABC, abstractmethod

import pyass

from src.models import Song, SongLine

from .consts import *
from ..models.karaoke import *


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
        end: timedelta = TITLE_EVENT_DURATION,
        titleCardTags: pyass.Tags = TITLE_CARD_TAGS,
    ) -> None:
        self.shouldPrintTitle = shouldPrintTitle
        self.dividerStyle = dividerStyle
        self.titleStyle = titleStyle
        self.end = end
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
            end=self.end,
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
        enLines = [to_en_k_line(line, i + 1) for i, line in enumerate(songLines)]
        return self.to_romaji_k_events(enLines, actorToStyle)

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


def get_romaji_pos_tag(line: KLine) -> pyass.Tag:
    if line.isSecondary:
        return SECONDARY_ROMAJI_POS_TAG
    elif line.isAlone:
        return ALONE_ROMAJI_POS_TAG
    else:
        return ROMAJI_POS_TAG


def get_en_pos_tag(line: KLine) -> pyass.Tag:
    return SECONDARY_EN_POS_TAG if line.isSecondary else EN_POS_TAG


def get_char_transform_tags(
    kChar: KChar,
    switchDuration: timedelta,
    transitionDuration: timedelta,
    startTag: Sequence[pyass.Tag] = [pyass.AlphaTag(0xFF)],
    enterTag: Sequence[pyass.Tag] = [pyass.AlphaTag(0x00)],
    exitTag: Sequence[pyass.Tag] = [pyass.AlphaTag(0xFF)],
) -> Sequence[pyass.Tag]:
    return [
        *startTag,
        get_enter_transition_tag(kChar, switchDuration, transitionDuration, enterTag),
        get_exit_transition_tag(kChar, switchDuration, transitionDuration, exitTag),
    ]


def get_enter_transition_tag(
    kChar: KChar,
    switchDuration: timedelta,
    transitionDuration: timedelta,
    resultTag: Sequence[pyass.Tag] = [pyass.AlphaTag(0x00)],
) -> pyass.Tag:
    return pyass.TransformTag(
        start=kChar.fadeOffset, end=switchDuration + kChar.fadeOffset, to=resultTag
    )


def get_exit_transition_tag(
    kChar: KChar,
    switchDuration: timedelta,
    transitionDuration: timedelta,
    resultTag: Sequence[pyass.Tag] = [pyass.AlphaTag(0xFF)],
) -> pyass.Tag:
    return pyass.TransformTag(
        start=kChar.line.duration
        - transitionDuration
        + switchDuration
        + kChar.fadeOffset,
        end=kChar.line.duration
        - transitionDuration
        + 2 * switchDuration
        + kChar.fadeOffset,
        to=resultTag,
    )


def get_char_actor_tag(
    kChar: KChar,
    actorToStyle: Mapping[str, Sequence[pyass.Tag]],
    switchDuration: timedelta,
) -> Sequence[pyass.Tag]:
    if len(kChar.line.actorSwitches) == 0:
        return []
    return list(actorToStyle[kChar.line.startActor]) + [
        pyass.TransformTag(
            start=time + kChar.fadeOffset,
            end=time + kChar.fadeOffset,
            to=actorToStyle[actor],
        )
        for time, actor in kChar.line.actorSwitches
    ]


def get_char_karaoke_tag(
    kChar: KChar, resultTag: Sequence[pyass.Tag] = []
) -> Sequence[pyass.Tag]:
    if kChar.karaDuration == timedelta():
        return []
    # Karaoke timing
    if len(resultTag) == 0:
        return [pyass.KaraokeTag(kChar.karaDuration)]
    else:
        return [
            pyass.TransformTag(start=kChar.karaStart, end=kChar.karaEnd, to=resultTag)
        ]


_effects: dict[str, Effect] = {}


def register_effect(name: str, effect: Effect):
    _effects[name] = effect


def retrieve_effect(name: str):
    return _effects.get(name)
