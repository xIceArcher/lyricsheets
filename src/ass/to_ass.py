from collections.abc import Sequence, Mapping
from datetime import timedelta
from functools import reduce
import itertools

import pyass

from src.fonts import FontScaler
from src.models import Song, SongLine, SongTitle

from .consts import *
from ..models.karaoke import *
from .kfx import DefaultLiveKaraokeEffect


def to_events(
    song: Song,
    actorToStyle: Mapping[str, Sequence[pyass.Tag]],
    shouldPrintTitle: bool = True,
    switchDuration: timedelta = DEFAULT_SWITCH_DURATION,
    transitionDuration: timedelta = DEFAULT_TRANSITION_DURATION,
) -> Sequence[pyass.Event]:
    kfx = DefaultLiveKaraokeEffect(shouldPrintTitle)
    return kfx.to_events(song, actorToStyle)
