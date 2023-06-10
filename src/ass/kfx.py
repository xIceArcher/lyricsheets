from collections.abc import Sequence, Mapping

from datetime import timedelta
from pyass import Tag

from .consts import *
from .karaoke import *


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
        return NO_EN_ROMAJI_POS_TAG
    else:
        return ROMAJI_POS_TAG


def get_en_pos_tag(line: KLine) -> pyass.Tag:
    return SECONDARY_EN_POS_TAG if line.isSecondary else EN_POS_TAG


def get_char_transform_tags(
    kChar: KChar,
    kLine: KLine,
    switchDuration: timedelta,
    transitionDuration: timedelta,
    startTag: Sequence[pyass.Tag] = [pyass.AlphaTag(0xFF)],
    enterTag: Sequence[pyass.Tag] = [pyass.AlphaTag(0x00)],
    exitTag: Sequence[pyass.Tag] = [pyass.AlphaTag(0xFF)],
) -> Sequence[pyass.Tag]:
    return [
        *startTag,
        get_enter_transition_tag(
            kChar, kLine, switchDuration, transitionDuration, enterTag
        ),
        get_exit_transition_tag(
            kChar, kLine, switchDuration, transitionDuration, exitTag
        ),
    ]


def get_enter_transition_tag(
    kChar: KChar,
    kLine: KLine,
    switchDuration: timedelta,
    transitionDuration: timedelta,
    resultTag: Sequence[pyass.Tag] = [pyass.AlphaTag(0x00)],
) -> pyass.Tag:
    return pyass.TransformTag(
        start=kChar.fadeOffset, end=switchDuration + kChar.fadeOffset, to=resultTag
    )


def get_exit_transition_tag(
    kChar: KChar,
    kLine: KLine,
    switchDuration: timedelta,
    transitionDuration: timedelta,
    resultTag: Sequence[pyass.Tag] = [pyass.AlphaTag(0xFF)],
) -> pyass.Tag:
    return pyass.TransformTag(
        start=kLine.duration - transitionDuration + switchDuration + kChar.fadeOffset,
        end=kLine.duration - transitionDuration + 2 * switchDuration + kChar.fadeOffset,
        to=resultTag,
    )


def get_char_actor_tag(
    kChar: KChar,
    kLine: KLine,
    actorToStyle: Mapping[str, Sequence[pyass.Tag]],
    switchDuration: timedelta,
) -> Sequence[pyass.Tag]:
    if len(kLine.actorSwitches) == 0:
        return []
    return [*(actorToStyle[kLine.startActor])] + [
        pyass.TransformTag(
            start=time + kChar.fadeOffset,
            end=time + kChar.fadeOffset,
            to=actorToStyle[actor],
        )
        for time, actor in kLine.actorSwitches
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


def to_default_event(
    line: KLine,
    actorToStyle: Mapping[str, Sequence[pyass.Tag]],
    switchDuration: timedelta,
    transitionDuration: timedelta,
) -> pyass.Event:
    # Generate line style tags
    eventParts: list[pyass.EventPart] = [
        pyass.EventPart(
            tags=[
                *LYRICS_TAGS,
                get_en_pos_tag(line) if line.isEN else get_romaji_pos_tag(line),
            ],
        )
    ]

    # Set color if there's a constant actor
    if len(line.actorSwitches) == 0:
        eventParts.append(pyass.EventPart(tags=actorToStyle[line.startActor]))

    # Leading switch duration
    if not line.isEN:
        eventParts.append(pyass.EventPart(tags=[pyass.KaraokeTag(switchDuration)]))

    # Generate character style tags
    for char in line.chars:
        eventParts.append(
            pyass.EventPart(
                tags=[
                    *get_char_transform_tags(
                        char, line, switchDuration, transitionDuration
                    ),
                    *get_char_actor_tag(char, line, actorToStyle, switchDuration),
                    *get_char_karaoke_tag(char),
                ],
                text=char.char,
            )
        )

    # Trailing switch duration
    if not line.isEN:
        eventParts.append(pyass.EventPart(tags=[pyass.KaraokeTag(switchDuration)]))

    return pyass.Event(
        format=get_line_format(line),
        style=EN_STYLE.name if line.isEN else ROMAJI_STYLE.name,
        start=line.start - switchDuration,
        end=line.end + switchDuration,
        parts=eventParts,
    )
