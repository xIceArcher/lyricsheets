from collections.abc import Mapping, Sequence

from lyricsheets.models import Song, SongLine, SongLineSyllable

import pyass

from ..ass.to_ass import Effect


class KaraokeOnlyEffect(Effect):
    def to_events(
        self,
        song: Song,
        actorToStyle: Mapping[str, Sequence[pyass.Tag]],
        shouldPrintTitle: bool = True,
    ) -> Sequence[pyass.Event]:
        return [self.to_event(line) for line in song.lyrics]

    def to_event(self, line: SongLine) -> pyass.Event:
        return pyass.Event(
            start=line.start,
            end=line.end,
            parts=[self.to_event_part(syl) for syl in line.syllables],
        )

    def to_event_part(self, syl: SongLineSyllable) -> pyass.EventPart:
        return pyass.EventPart(
            tags=[pyass.KaraokeTag(syl.length, False)], text=syl.text
        )
