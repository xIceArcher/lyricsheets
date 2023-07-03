from collections.abc import Sequence, Mapping
from datetime import timedelta

import pyass

from ass.consts import pyass
from models.karaoke import KLine, Sequence, pyass

from ..ass.consts import *
from ..ass.to_ass import *
from ..models.karaoke import *


def to_plain_event(line: KLine) -> pyass.Event:
    return pyass.Event(
        format=get_line_format(line),
        style=EN_STYLE.name if line.isEN else ROMAJI_STYLE.name,
        start=line.start,
        end=line.end,
        parts=[
            pyass.EventPart(
                tags=[
                    pyass.KaraokeTag(syl.duration, False),
                    pyass.IFXTag(syl.inlineFx)
                    if syl2 is None or syl.inlineFx != syl2.inlineFx
                    else pyass.tag.UnknownTag(""),
                ],
                text=syl.text,
            )
            for syl, syl2 in zip(line.kara, [None] + line.kara[:-1])
        ],
    )


class PlainEffect(KaraokeEffect):
    def to_romaji_k_events(
        self,
        songLines: Sequence[KLine],
        actorToStyle: Mapping[str, Sequence[pyass.Tag]],
    ) -> Sequence[pyass.Event]:
        return [to_plain_event(line) for line in songLines]

    def to_en_k_events(
        self,
        songLines: Sequence[KLine],
        actorToStyle: Mapping[str, Sequence[pyass.Tag]],
    ) -> Sequence[pyass.Event]:
        return [to_plain_event(line) for line in songLines]


register_effect("plain_effect", PlainEffect())
