from collections.abc import Sequence, Mapping
from datetime import timedelta
from functools import reduce
import itertools

import pyass

from ..fonts import FontScaler
from ..models import Song, SongLine, SongTitle

from .consts import *


def get_line_format(line: SongLine) -> pyass.EventFormat:
    return (
        pyass.EventFormat.COMMENT
        if line.romaji == line.en
        else pyass.EventFormat.DIALOGUE
    )


def get_romaji_pos_tag(line: SongLine) -> pyass.Tag:
    if line.isSecondary:
        return SECONDARY_ROMAJI_POS_TAG
    elif line.romaji == line.en:
        return NO_EN_ROMAJI_POS_TAG
    else:
        return ROMAJI_POS_TAG


def get_en_pos_tag(line: SongLine) -> pyass.Tag:
    return SECONDARY_EN_POS_TAG if line.isSecondary else EN_POS_TAG


def get_fade_transform_tags(
    lineLength: timedelta,
    offset: timedelta,
    switchDuration: timedelta,
    transitionDuration: timedelta,
) -> list[pyass.Tag]:
    return [
        pyass.AlphaTag(0xFF),
        pyass.TransformTag(
            start=offset,
            end=switchDuration + offset,
            to=[pyass.AlphaTag(0x00)],
        ),
        pyass.TransformTag(
            start=lineLength - transitionDuration + switchDuration + offset,
            end=lineLength - transitionDuration + 2 * switchDuration + offset,
            to=[pyass.AlphaTag(0xFF)],
        ),
    ]


def get_style_tag(
    switchTime: timedelta,
    style: list[pyass.Tag],
    switchDuration: timedelta,
) -> list[pyass.Tag]:
    return (
        [
            pyass.TransformTag(
                start=switchTime - switchDuration / 2,
                end=switchTime + switchDuration / 2,
                to=style,
            )
        ]
        if switchTime != timedelta()
        else style
    )


def get_style_tags(
    line: SongLine,
    actorToStyle: Mapping[str, list[pyass.Tag]],
    switchDuration: timedelta,
) -> list[pyass.Tag]:
    timedeltaUpToIdx = reduce(
        lambda a, b: a + [a[-1] + b.length], line.syllables, [timedelta(0)]
    )
    return list(
        itertools.chain.from_iterable(
            [
                get_style_tag(
                    timedeltaUpToIdx[breakpoint], actorToStyle[actor], switchDuration
                )
                for actor, breakpoint in zip(line.actors, line.breakpoints)
            ]
        )
    )


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


def to_karaoke_effect_romaji_event(
    line: SongLine,
    songTitle: SongTitle,
) -> pyass.Event:
    # Karaoke tag per syllable
    syllableEventParts = [
        pyass.EventPart(
            tags=[pyass.KaraokeTag(duration=syllable.length)],
            text=syllable.text,
        )
        for syllable in line.syllables
    ]

    # IFX tag per breakpoint
    for breakpoint, actor in zip(line.breakpoints, line.actors):
        syllableEventParts[breakpoint].tags.append(pyass.IFXTag(actor))

    return pyass.Event(
        style=f"Song - {songTitle.romaji} {line.karaokeEffect}",
        start=line.start,
        end=line.end,
        parts=[
            pyass.EventPart(
                tags=[get_romaji_pos_tag(line)],
            ),
            *syllableEventParts,
        ],
        effect=KARAOKE_EFFECT,
    )


def to_fade_effect_romaji_event(
    line: SongLine,
    actorToStyle: Mapping[str, list[pyass.Tag]],
    switchDuration: timedelta,
    transitionDuration: timedelta,
) -> pyass.Event:
    eventParts: list[pyass.EventPart] = [
        pyass.EventPart(
            tags=[
                *LYRICS_TAGS,
                get_romaji_pos_tag(line),
                *get_style_tags(line, actorToStyle, switchDuration),
            ],
        )
    ]

    # Make sure the syllable finishes before the line starts fading
    line.syllables[-1].length = max(
        line.syllables[-1].length - switchDuration, switchDuration / 2
    )

    fontScaler = FontScaler(ROMAJI_STYLE.fontName, ROMAJI_STYLE.fontSize)
    lineCharTimes = [
        timedelta(milliseconds=m)
        for m in fontScaler.split_by_rendered_width(
            pyass.timedelta(transitionDuration).total_milliseconds(), line.romaji
        )
    ]

    lineCharIdx = 0
    charOffsetFromLineStart = timedelta()

    # Leading switch duration
    eventParts.append(pyass.EventPart(tags=[pyass.KaraokeTag(switchDuration)]))

    for syllable in line.syllables:
        syllableCharLengths = [
            timedelta(milliseconds=c * 10)
            for c in fontScaler.split_by_rendered_width(
                pyass.timedelta(syllable.length).total_centiseconds(), syllable.text
            )
        ]

        for char, length in zip(syllable.text, syllableCharLengths):
            eventParts.append(
                pyass.EventPart(
                    tags=[
                        *get_fade_transform_tags(
                            line.length,
                            charOffsetFromLineStart,
                            switchDuration,
                            transitionDuration,
                        ),
                        pyass.KaraokeTag(length),
                    ],
                    text=char,
                )
            )

            charOffsetFromLineStart += lineCharTimes[lineCharIdx]
            lineCharIdx += 1

    # Trailing switch duration
    eventParts.append(pyass.EventPart(tags=[pyass.KaraokeTag(switchDuration)]))

    return pyass.Event(
        style=ROMAJI_STYLE.name,
        start=line.start - switchDuration,
        end=line.end + switchDuration,
        parts=eventParts,
    )


def to_romaji_event(
    line: SongLine,
    songTitle: SongTitle,
    actorToStyle: Mapping[str, list[pyass.Tag]],
    switchDuration: timedelta,
    transitionDuration: timedelta,
) -> pyass.Event:
    if line.karaokeEffect:
        return to_karaoke_effect_romaji_event(line, songTitle)

    return to_fade_effect_romaji_event(
        line, actorToStyle, switchDuration, transitionDuration
    )


def to_karaoke_effect_en_event(
    line: SongLine,
    actorToStyle: Mapping[str, list[pyass.Tag]],
    switchDuration: timedelta,
    transitionDuration: timedelta,
) -> pyass.Event:
    # TODO: Confirm requirements for EN lines with karaoke effect
    return to_fade_effect_en_event(
        line, actorToStyle, switchDuration, transitionDuration
    )


def to_fade_effect_en_event(
    line: SongLine,
    actorToStyle: Mapping[str, list[pyass.Tag]],
    switchDuration: timedelta,
    transitionDuration: timedelta,
) -> pyass.Event:
    # Determine how much time each character should take to transition, given its width in the rendered font
    lineCharTimes = FontScaler(
        EN_STYLE.fontName, EN_STYLE.fontSize
    ).split_by_rendered_width(
        pyass.timedelta(transitionDuration).total_milliseconds(), line.en
    )
    charOffsetsFromLineStart = itertools.accumulate([timedelta(milliseconds=m) for m in lineCharTimes], initial=timedelta(0))

    return pyass.Event(
        format=get_line_format(line),
        style=EN_STYLE.name,
        start=line.start - switchDuration,
        end=line.end + switchDuration,
        parts=[
            pyass.EventPart(
                tags=[
                    *LYRICS_TAGS,
                    get_en_pos_tag(line),
                ]
            ),
            pyass.EventPart(
                tags=get_style_tags(line, actorToStyle, switchDuration),
            ),
            *[
                pyass.EventPart(
                    tags=get_fade_transform_tags(
                        line.length, offset, switchDuration, transitionDuration
                    ),
                    text=char,
                )
                for offset, char in zip(charOffsetsFromLineStart, line.en)
            ],
        ],
    )


def to_en_event(
    line: SongLine,
    actorToStyle: Mapping[str, list[pyass.Tag]],
    switchDuration: timedelta,
    transitionDuration: timedelta,
) -> pyass.Event:
    if line.karaokeEffect:
        return to_karaoke_effect_en_event(
            line, actorToStyle, switchDuration, transitionDuration
        )

    return to_fade_effect_en_event(
        line, actorToStyle, switchDuration, transitionDuration
    )


def to_events(
    song: Song,
    actorToStyle: Mapping[str, list[pyass.Tag]],
    shouldPrintTitle: bool = True,
    switchDuration: timedelta = DEFAULT_SWITCH_DURATION,
    transitionDuration: timedelta = DEFAULT_TRANSITION_DURATION,
) -> Sequence[pyass.Event]:
    return [
        to_divider_event(song, song.title.romaji),
        to_title_event(song, shouldPrintTitle),
        to_divider_event(song, "Romaji"),
        *[
            to_romaji_event(
                line, song.title, actorToStyle, switchDuration, transitionDuration
            )
            for line in song.lyrics
        ],
        to_divider_event(song, "English"),
        *[
            to_en_event(line, actorToStyle, switchDuration, transitionDuration)
            for line in song.lyrics
        ],
    ]
