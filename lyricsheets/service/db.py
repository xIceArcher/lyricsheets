from collections.abc import Mapping
from typing import Optional
import string

from lyricsheets.models import Song
from lyricsheets.db import SongDB
from lyricsheets.cache import Cache, with_cache

from .service import SongService, NotFoundError


class SongServiceByDB(SongService):
    def __init__(
        self,
        googleCredentials: Mapping[str, str],
        groupToSpreadsheetIds: Mapping[str, str],
        defaultGroup: str = "",
        cache: Optional[Cache] = None,
    ) -> None:
        self.groupToSpreadsheetIds = groupToSpreadsheetIds
        self.defaultSpreadsheetId = groupToSpreadsheetIds[defaultGroup]
        self.service = SongDB(googleCredentials, cache=cache)
        self.cache = cache

        self._create_song_mappings()

    def _create_song_mappings(self):
        self.songMappings = {
            self._to_song_key(song): {"group": group, "name": song}
            for group, id in self.groupToSpreadsheetIds.items()
            for song in self.service.list_song_names(id)
        }

    @with_cache("SongServiceByDB::get_song")
    def get_song(self, songName: str) -> Song:
        songKeyToFind = self._to_song_key(songName)
        if songKeyToFind not in self.songMappings:
            raise NotFoundError(songName)

        group = self.songMappings[songKeyToFind]["group"]
        existingSongName = self.songMappings[songKeyToFind]["name"]
        spreadsheetId = self.groupToSpreadsheetIds.get(group, self.defaultSpreadsheetId)
        return self.service.get_song(spreadsheetId, existingSongName)

    def _to_song_key(self, songName: str):
        return "".join(
            "" if c in string.punctuation or c in string.whitespace else c
            for c in songName.encode("ascii", "ignore").decode().lower()
        )

    @with_cache("SongServiceByDB::get_format_tags")
    def get_format_tags(self, group: str = "") -> Mapping[str, str]:
        spreadsheetId = self.groupToSpreadsheetIds.get(group, self.defaultSpreadsheetId)

        return self.service.songTemplateDB.get_format_tags(spreadsheetId)

    @with_cache("SongServiceByDB::get_all_format_tags")
    def get_all_format_tags(self) -> Mapping[str, str]:
        return {
            actor: style
            for group in self.groupToSpreadsheetIds.keys()
            for actor, style in self.get_format_tags(group).items()
        }

    def create_song(self, song: Song, group: str = ""):
        spreadsheetId = self.groupToSpreadsheetIds.get(group, self.defaultSpreadsheetId)
        self.service.create_song(spreadsheetId, song)

    def update_song_karaoke(self, song: Song):
        songKey = self._to_song_key(song.title.romaji)
        group = self.songMappings[songKey]["group"]
        spreadsheetId = self.groupToSpreadsheetIds.get(group, self.defaultSpreadsheetId)
        self.service.update_song_karaoke(spreadsheetId, song)
