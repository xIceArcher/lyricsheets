from collections.abc import Sequence, Mapping

from datetime import timedelta
from pyass import Color
from pyass import Alignment
import pyass.tag

from .consts import *
from .to_ass import effects, KaraokeEffect, get_line_format, get_char_transform_tags
from ..models.karaoke import *


class ShadowKaraokeEffect(KaraokeEffect):
    def to_romaji_k_events(
        self,
        songLines: Sequence[KLine],
        actorToStyle: Mapping[str, Sequence[pyass.Tag]],
    ) -> Sequence[pyass.Event]:
        return [
            to_shad_event(
                line, actorToStyle, DEFAULT_SWITCH_DURATION, DEFAULT_TRANSITION_DURATION
            )
            for line in songLines
        ]

    def to_en_k_events(
        self,
        songLines: Sequence[KLine],
        actorToStyle: Mapping[str, Sequence[pyass.Tag]],
    ) -> Sequence[pyass.Event]:
        return [
            to_shad_event(
                line, actorToStyle, DEFAULT_SWITCH_DURATION, DEFAULT_TRANSITION_DURATION
            )
            for line in songLines
        ]


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
    line.calculate_char_offsets(ROMAJI_STYLE, transitionDuration)
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


effects["shadow_karaoke_effect"] = ShadowKaraokeEffect()
