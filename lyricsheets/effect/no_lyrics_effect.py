from collections.abc import Sequence, Mapping

from ..ass.to_ass import *


class NoLyricsEffect(Effect):
    def to_events(
        self,
        song: Song,
        actorToStyle: Mapping[str, Sequence[pyass.Tag]],
        shouldPrintTitle: bool = True,
    ) -> Sequence[pyass.Event]:
        return []


register_effect("no_lyrics_effect", NoLyricsEffect())
