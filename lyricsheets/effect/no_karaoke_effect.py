from collections.abc import Sequence, Mapping

from ..ass.to_ass import *


# WIP
class NoKaraokeEffect(LyricsEffect):
    def to_lyrics_events(
        self,
        songLines: Sequence[SongLine],
        actorToStyle: Mapping[str, Sequence[pyass.Tag]],
    ) -> Sequence[pyass.Event]:
        return []


register_effect("no_karaoke_effect", NoKaraokeEffect())
