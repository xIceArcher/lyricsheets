from collections.abc import Sequence, Mapping
from datetime import timedelta
import functools

from ..ass.to_ass import *

# Positions
ROMAJI_POS_TAG = pyass.PositionTag(960, 960)
ALONE_ROMAJI_POS_TAG = pyass.PositionTag(960, 1010)
SECONDARY_ROMAJI_POS_TAG = pyass.PositionTag(960, 65)

EN_POS_TAG = pyass.PositionTag(960, 1015)
SECONDARY_EN_POS_TAG = pyass.PositionTag(960, 120)

# Timings
DEFAULT_SWITCH_DURATION = timedelta(milliseconds=200)
DEFAULT_TRANSITION_DURATION = timedelta(milliseconds=500)


def get_romaji_pos_tag(line: KLine) -> pyass.Tag:
    if line.isSecondary:
        return SECONDARY_ROMAJI_POS_TAG
    elif line.isAlone:
        return ALONE_ROMAJI_POS_TAG
    else:
        return ROMAJI_POS_TAG


def get_en_pos_tag(line: KLine) -> pyass.Tag:
    return SECONDARY_EN_POS_TAG if line.isSecondary else EN_POS_TAG


def get_char_wrap_tags(
    kChar: KChar,
) -> tuple[Sequence[pyass.Tag], Sequence[pyass.Tag]]:
    if kChar.style.fontName not in STYLE_FONT_NAME_TO_CHAR_WRAP_TAGS:
        return ([], [])

    return STYLE_FONT_NAME_TO_CHAR_WRAP_TAGS[kChar.style.fontName].get(
        kChar.text, ([], [])
    )


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
        get_enter_transition_tag(kChar, switchDuration, enterTag),
        get_exit_transition_tag(kChar, switchDuration, transitionDuration, exitTag),
    ] if switchDuration != timedelta(0) else []


def get_enter_transition_tag(
    kChar: KChar,
    switchDuration: timedelta,
    resultTag: Sequence[pyass.Tag] = [pyass.AlphaTag(0x00)],
) -> pyass.Tag:
    return pyass.TransformTag(
        start=kChar.fadeOffset,
        end=switchDuration + kChar.fadeOffset,
        to=list(resultTag),
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
        to=list(resultTag),
    )


def get_char_actor_tag(
    kChar: KChar,
    actorToStyle: Mapping[str, Sequence[pyass.Tag]],
    switchSylFadeOffsets: Sequence[timedelta],
) -> Sequence[pyass.Tag]:
    if len(kChar.line.actorSwitches) == 0:
        return []

    ret = list(actorToStyle[kChar.line.startActor])

    for (time, actor), switchSylFadeOffset in zip(
        kChar.line.actorSwitches, switchSylFadeOffsets
    ):
        ret.append(
            pyass.TransformTag(
                start=time + kChar.fadeOffset - switchSylFadeOffset,
                end=time + kChar.fadeOffset - switchSylFadeOffset,
                to=list(actorToStyle[actor]),
            )
        )

    return ret


def get_char_karaoke_tag(
    kChar: KChar, resultTag: Sequence[pyass.Tag] = []
) -> Sequence[pyass.Tag]:
    if kChar.duration == timedelta():
        return []
    elif not resultTag:
        return [pyass.KaraokeTag(kChar.duration)]
    else:
        return [
            pyass.TransformTag(start=kChar.start, end=kChar.end, to=list(resultTag))
        ]


def get_char_event_parts(
    kChar: KChar,
    actorToStyle: Mapping[str, Sequence[pyass.Tag]],
    switchDuration: timedelta,
    transitionDuration: timedelta,
    switchSylFadeOffsets: Sequence[timedelta],
) -> Sequence[pyass.EventPart]:
    charWrapStartTags, charWrapEndTags = get_char_wrap_tags(kChar)

    ret = [
        pyass.EventPart(
            tags=[
                *get_char_transform_tags(kChar, switchDuration, transitionDuration),
                *get_char_actor_tag(kChar, actorToStyle, switchSylFadeOffsets),
                *get_char_karaoke_tag(kChar),
                *charWrapStartTags,
            ],
            text=kChar.text,
        )
    ]

    if charWrapEndTags:
        ret.append(pyass.EventPart(tags=charWrapEndTags))

    return ret


def get_syl_event_parts(
    kSyl: KSyl,
    actorToStyle: Mapping[str, Sequence[pyass.Tag]],
    switchDuration: timedelta,
    transitionDuration: timedelta,
    switchSylFadeOffsets: Sequence[timedelta],
) -> Sequence[pyass.EventPart]:
    return [
        eventPart
        for eventParts in [
            get_char_event_parts(
                char,
                actorToStyle,
                switchDuration,
                transitionDuration,
                switchSylFadeOffsets,
            )
            for char in kSyl.chars
        ]
        for eventPart in eventParts
    ]


def to_default_romaji_event(
    line: KLine,
    actorToStyle: Mapping[str, Sequence[pyass.Tag]],
    switchDuration: timedelta,
    transitionDuration: timedelta,
    switchSylFadeOffsets: Sequence[timedelta],
) -> pyass.Event:
    return pyass.Event(
        format=get_line_format(line),
        style=ROMAJI_STYLE.name,
        start=line.start - switchDuration,
        end=line.end + switchDuration,
        parts=[
            # Line style tag
            pyass.EventPart(
                tags=[
                    *LYRICS_TAGS,
                    get_romaji_pos_tag(line),
                ],
            ),
            # Set color if there's a constant actor
            *(
                [pyass.EventPart(tags=actorToStyle[line.startActor])]
                if not line.actorSwitches
                else []
            ),
            # Leading switch duration
            pyass.EventPart(tags=[pyass.KaraokeTag(switchDuration)]),
            # Per syllable tags
            *functools.reduce(
                operator.concat,
                [
                    get_syl_event_parts(
                        syl,
                        actorToStyle,
                        switchDuration,
                        transitionDuration,
                        switchSylFadeOffsets,
                    )
                    for syl in line.syls
                ],
            ),
            # Trailing switch duration
            pyass.EventPart(tags=[pyass.KaraokeTag(switchDuration)]),
        ],
    )


def to_default_en_event(
    line: KLine,
    actorToStyle: Mapping[str, Sequence[pyass.Tag]],
    switchDuration: timedelta,
    transitionDuration: timedelta,
    switchSylFadeOffsets: Sequence[timedelta],
) -> pyass.Event:
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
                ],
            ),
            # Set color if there's a constant actor
            *(
                [pyass.EventPart(tags=actorToStyle[line.startActor])]
                if not line.actorSwitches
                else []
            ),
            # Per syllable tags
            *functools.reduce(
                operator.concat,
                [
                    get_syl_event_parts(
                        syl,
                        actorToStyle,
                        switchDuration,
                        transitionDuration,
                        switchSylFadeOffsets,
                    )
                    for syl in line.syls
                ],
            ),
        ],
    )


def get_switch_syl_fade_offsets(
    actorSwitches: Sequence[tuple[timedelta, str]], syls: Sequence[KSyl]
) -> Sequence[timedelta]:
    switchSylFadeOffsets: list[timedelta] = []

    for time, _ in actorSwitches:
        # Find the KSyl at which this switch occurs
        for syl in syls:
            if syl.start == time:
                switchSylFadeOffsets.append(syl.chars[0].fadeOffset)
                break

    if len(switchSylFadeOffsets) != len(actorSwitches):
        raise ValueError("Could not find all switch syllables")

    return switchSylFadeOffsets


class DefaultLiveKaraokeEffect(DependentKaraokeEffect):
    def to_romaji_k_events(
        self,
        romajiLines: Sequence[KLine],
        enLines: Sequence[KLine],
        actorToStyle: Mapping[str, Sequence[pyass.Tag]],
    ) -> Sequence[pyass.Event]:
        return [
            self.to_romaji_k_event(romajiLine, enLine, actorToStyle)
            for romajiLine, enLine in zip(romajiLines, enLines)
        ]

    def to_romaji_k_event(
        self,
        romajiLine: KLine,
        enLine: KLine,
        actorToStyle: Mapping[str, Sequence[pyass.Tag]],
    ) -> pyass.Event:
        romajiLine.style = ROMAJI_STYLE
        romajiLine.transitionDuration = DEFAULT_TRANSITION_DURATION

        return to_default_romaji_event(
            romajiLine,
            actorToStyle,
            DEFAULT_SWITCH_DURATION,
            DEFAULT_TRANSITION_DURATION,
            get_switch_syl_fade_offsets(romajiLine.actorSwitches, romajiLine.syls),
        )

    def to_en_k_events(
        self,
        romajiLines: Sequence[KLine],
        enLines: Sequence[KLine],
        actorToStyle: Mapping[str, Sequence[pyass.Tag]],
    ) -> Sequence[pyass.Event]:
        return [
            self.to_en_k_event(romajiLine, enLine, actorToStyle)
            for romajiLine, enLine in zip(romajiLines, enLines)
        ]

    def to_en_k_event(
        self,
        romajiLine: KLine,
        enLine: KLine,
        actorToStyle: Mapping[str, Sequence[pyass.Tag]],
    ) -> pyass.Event:
        romajiLine.style = ROMAJI_STYLE
        romajiLine.transitionDuration = DEFAULT_TRANSITION_DURATION

        enLine.style = EN_STYLE
        enLine.transitionDuration = DEFAULT_TRANSITION_DURATION

        return to_default_en_event(
            enLine,
            actorToStyle,
            DEFAULT_SWITCH_DURATION,
            DEFAULT_TRANSITION_DURATION,
            get_switch_syl_fade_offsets(enLine.actorSwitches, romajiLine.syls),
        )


register_effect("default_live_karaoke_effect", DefaultLiveKaraokeEffect())
