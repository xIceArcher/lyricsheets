from collections.abc import Sequence, Mapping

from ..ass.to_ass import *


# WIP
class NoKaraokeEffect(LyricsEffect):
    def to_romaji_events(
        self,
        songLines: Sequence[SongLine],
        actorToStyle: Mapping[str, Sequence[pyass.Tag]],
    ) -> Sequence[pyass.Event]:
        return []

    def to_en_events(
        self,
        songLines: Sequence[SongLine],
        actorToStyle: Mapping[str, Sequence[pyass.Tag]],
    ) -> Sequence[pyass.Event]:
        return []


register_effect("no_karaoke_effect", NoKaraokeEffect())
