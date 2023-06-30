from collections.abc import Sequence, Mapping
from datetime import timedelta
from functools import reduce
import itertools

import pyass

from src.fonts import FontScaler
from src.models import Song, SongLine, SongTitle

from .consts import *
from ..models.karaoke import *
from .kfx import to_default_event, to_shad_event, to_plain_event


def to_divider_event(song: Song, dividerText: str) -> pyass.Event:
    return pyass.Event(
        format=pyass.EventFormat.COMMENT,
        style=DIVIDER_STYLE.name,
        end=song.end,
        text=dividerText,
    )


def to_title_event(song: Song, shouldPrintTitle: bool) -> pyass.Event:
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
        style=TITLE_STYLE.name,
        end=TITLE_EVENT_DURATION,
        parts=[
            pyass.EventPart(tags=TITLE_CARD_TAGS, text=r"\N".join(s)),
        ],
    )


def to_events(
    song: Song,
    actorToStyle: Mapping[str, Sequence[pyass.Tag]],
    shouldPrintTitle: bool = True,
    switchDuration: timedelta = DEFAULT_SWITCH_DURATION,
    transitionDuration: timedelta = DEFAULT_TRANSITION_DURATION,
) -> Sequence[pyass.Event]:
    return [
        to_divider_event(song, song.title.romaji),
        to_title_event(song, shouldPrintTitle),
        to_divider_event(song, "Romaji"),
        *[
            to_plain_event(
                to_romaji_k_line(line, i + 1),
                actorToStyle,
                switchDuration,
                transitionDuration,
            )
            for i, line in enumerate(song.lyrics)
        ],
        to_divider_event(song, "English"),
        *[
            to_plain_event(
                to_en_k_line(line, i + 1),
                actorToStyle,
                switchDuration,
                transitionDuration,
            )
            for i, line in enumerate(song.lyrics)
        ],
    ]
