from collections.abc import Sequence
from datetime import timedelta
import functools
import pyass

from lyricsheets.models import SongLine, SongLineSyllable


def read_karaoke(events: Sequence[pyass.Event]) -> list[SongLine]:
    events = [event for event in events if event.text != ""]

    ret = []
    for event in events:
        syllables: list[SongLineSyllable] = []

        for part in event.parts:
            karaokeTags = [
                tag for tag in part.tags if isinstance(tag, pyass.KaraokeTag)
            ]
            if len(karaokeTags) == 0:
                # This entire part is a syllable, which might happen when the entire line has one syllable
                syllables.append(SongLineSyllable(length=event.length, text=event.text))
            elif len(karaokeTags) == 1:
                syllables.append(
                    SongLineSyllable(length=karaokeTags[0].duration, text=part.text)
                )

        kTimeSum = functools.reduce(lambda a, b: a + b.length, syllables, timedelta())

        if len(syllables) > 0:
            syllables[-1].length -= kTimeSum - event.length

        ret.append(
            SongLine(
                syllables=syllables,
                start=event.start,
                end=event.end,
            )
        )

    return ret
