from collections.abc import Sequence, Mapping

from datetime import timedelta
from pyass import Color
from pyass import Alignment
import pyass.tag

from .consts import *
from .to_ass import KaraokeEffect
from ..models.karaoke import *


class DefaultLiveKaraokeEffect(KaraokeEffect):
    def to_romaji_k_events(self, songLines: Sequence[KLine], actorToStyle: Mapping[str, Sequence[pyass.Tag]]) -> Sequence[pyass.Event]:
        return [to_default_event(line, actorToStyle, DEFAULT_SWITCH_DURATION, DEFAULT_TRANSITION_DURATION) for line in songLines]

    def to_en_k_events(self, songLines: Sequence[KLine], actorToStyle: Mapping[str, Sequence[pyass.Tag]]) -> Sequence[pyass.Event]:
        return [to_default_event(line, actorToStyle, DEFAULT_SWITCH_DURATION, DEFAULT_TRANSITION_DURATION) for line in songLines]
    
class ShadowKaraokeEffect(KaraokeEffect):
    def to_romaji_k_events(self, songLines: Sequence[KLine], actorToStyle: Mapping[str, Sequence[pyass.Tag]]) -> Sequence[pyass.Event]:
        return [to_shad_event(line, actorToStyle, DEFAULT_SWITCH_DURATION, DEFAULT_TRANSITION_DURATION) for line in songLines]

    def to_en_k_events(self, songLines: Sequence[KLine], actorToStyle: Mapping[str, Sequence[pyass.Tag]]) -> Sequence[pyass.Event]:
        return [to_shad_event(line, actorToStyle, DEFAULT_SWITCH_DURATION, DEFAULT_TRANSITION_DURATION) for line in songLines]

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


def to_default_event(
    line: KLine,
    actorToStyle: Mapping[str, Sequence[pyass.Tag]],
    switchDuration: timedelta,
    transitionDuration: timedelta,
) -> pyass.Event:
    if line.isEN:
        line.calculate_char_offsets(EN_STYLE, transitionDuration)
    else:
        line.calculate_char_offsets(ROMAJI_STYLE, transitionDuration)

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
                    *get_char_transform_tags(char, switchDuration, transitionDuration),
                    *get_char_actor_tag(char, actorToStyle, switchDuration),
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


def get_char_syl_karaoke_tag(
    kChar: KChar, switchDuration: timedelta, resultTag: Sequence[pyass.Tag] = []
) -> Sequence[pyass.Tag]:
    if kChar.karaDuration == timedelta():
        return []
    # Karaoke timing
    if len(resultTag) == 0:
        return [pyass.KaraokeTag(kChar.karaDuration)]
    else:
        return [
            pyass.TransformTag(
                start=kChar.syl.start + switchDuration,
                end=kChar.syl.end + switchDuration,
                to=resultTag,
            )
        ]


def to_shad_event(
    line: KLine,
    actorToStyle: Mapping[str, Sequence[pyass.Tag]],
    switchDuration: timedelta,
    transitionDuration: timedelta,
) -> pyass.Event:
    line.calculate_char_offsets(ROMAJI_STYLE)
    firstColor = Color.parse("&HBBC9F8&")
    switchColor = Color.parse("&H8A78D7&")

    # Generate line style tags
    eventParts: list[pyass.EventPart] = [
        pyass.EventPart(
            tags=[
                pyass.BlurEdgesTag(1),
                pyass.AlignmentTag(Alignment.TOP_LEFT)
                if line.isSecondary
                else pyass.AlignmentTag(Alignment.TOP_RIGHT),
                pyass.PositionTag(30, 30)
                if line.isSecondary and not line.isEN
                else pyass.PositionTag(30, 100)
                if line.isSecondary and line.isEN
                else pyass.PositionTag(1890, 30)
                if not line.isSecondary and not line.isEN
                else pyass.PositionTag(1890, 100),
            ],
        )
    ]

    # Generate character style tags
    for char in line.chars:
        eventParts.append(
            pyass.EventPart(
                tags=[
                    *get_char_transform_tags(char, switchDuration, transitionDuration),
                    pyass.ShadowDepthTag(0),
                    pyass.ColorTag(firstColor)
                    if not line.isEN
                    else pyass.tag.UnknownTag(""),
                    *get_char_syl_karaoke_tag(
                        char,
                        switchDuration,
                        [pyass.ShadowDepthTag(9), pyass.ColorTag(switchColor)],
                    ),
                ],
                text=char.char,
            )
        )

    return pyass.Event(
        format=get_line_format(line),
        style=EN_STYLE.name if line.isEN else ROMAJI_STYLE.name,
        start=line.start - switchDuration,
        end=line.end + switchDuration,
        parts=eventParts,
    )
