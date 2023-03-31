from collections.abc import Mapping
from typing import Optional

from ..models import Song
from ..db import SongDB
from ..cache import Cache

class SongServer:
    def __init__(self, googleCredentials: Mapping[str, str], defaultSpreadsheetId: str = '', cache: Optional[Cache] = None) -> None:
        self.defaultSpreadsheetId = defaultSpreadsheetId
        self.service = SongDB(googleCredentials)

    def get_song(self, songName: str, spreadsheetId: str = '') -> Song:
        return self.service.scan_song(self.defaultSpreadsheetId if not spreadsheetId else spreadsheetId, songName)
