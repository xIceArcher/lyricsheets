from collections.abc import Mapping
from typing import Optional
import string

from src.models import Song
from src.db import SongDB
from src.cache import Cache, with_cache

from .service import SongService, NotFoundError


class SongServiceByDB(SongService):
    def __init__(
        self,
        googleCredentials: Mapping[str, str],
        defaultSpreadsheetId: str = "",
        cache: Optional[Cache] = None,
    ) -> None:
        self.defaultSpreadsheetId = defaultSpreadsheetId
        self.service = SongDB(googleCredentials, cache=cache)
        self.cache = cache

    @with_cache("SongServiceByDB::get_song")
    def get_song(self, songName: str, spreadsheetId: str = "") -> Song:
        if spreadsheetId == "":
            spreadsheetId = self.defaultSpreadsheetId

        songKeyToFind = self._to_song_key(songName)

        for existingSongName in self.service.list_song_names(spreadsheetId):
            if self._to_song_key(existingSongName) == songKeyToFind:
                return self.service.get_song(
                    self.defaultSpreadsheetId if not spreadsheetId else spreadsheetId,
                    existingSongName,
                )

        raise NotFoundError(spreadsheetId, songName)

    def _to_song_key(self, songName: str):
        return "".join(
            "" if c in string.punctuation or c in string.whitespace else c
            for c in songName.encode("ascii", "ignore").decode().lower()
        )

    @with_cache("SongServiceByDB::get_format_tags")
    def get_format_tags(self, spreadsheetId: str = "") -> Mapping[str, str]:
        if spreadsheetId == "":
            spreadsheetId = self.defaultSpreadsheetId

        return self.service.songTemplateDB.get_format_tags(spreadsheetId)

    def save_song(self, song: Song, spreadsheetId: str = ""):
        if spreadsheetId == "":
            spreadsheetId = self.defaultSpreadsheetId

        self.service.save_song(spreadsheetId, song)
