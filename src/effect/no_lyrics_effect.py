from collections.abc import Sequence, Mapping

import pyass

from ..ass.consts import *
from ..ass.to_ass import *
from ..models.karaoke import *


class NoLyricsEffect(Effect):
    def to_events(
        self, song: Song, actorToStyle: Mapping[str, Sequence[pyass.Tag]]
    ) -> Sequence[pyass.Event]:
        return []


register_effect("no_lyrics_effect", NoLyricsEffect())
