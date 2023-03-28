from collections.abc import Mapping
from typing import Optional
import pickle

from scan import scan_song

from ..models import models

from apiclient import discovery
from google.oauth2 import service_account
from redis import Redis


class UncachedSongAPI:
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

    def __init__(self, googleCredentials: Mapping[str, str], spreadsheetId: Optional[str]) -> None:
        self.defaultSpreadsheetId = spreadsheetId
        self.service = discovery.build(
            'sheets',
            'v4',
            credentials=service_account.Credentials.from_service_account_info(googleCredentials, scopes=UncachedSongAPI.SCOPES)
        ).spreadsheets()

    def get_song(self, songName: str, spreadsheetId: Optional[str]=None) -> models.Song:
        if not self.defaultSpreadsheetId and not spreadsheetId:
            raise RuntimeError('Spreadsheet ID not specified!')

        return scan_song(self.service, self.defaultSpreadsheetId if not spreadsheetId else spreadsheetId, songName)


class SongAPI(UncachedSongAPI):
    def __init__(self, googleCredentials: Mapping[str, str], spreadsheetId: Optional[str], host: str, port: int, db: int):
        super().__init__(googleCredentials, spreadsheetId)
        self.cache = Redis(host=host, port=port, db=db)

    def get_song(self, songName: str, spreadsheetId: Optional[str]=None) -> models.Song:
        spreadsheetId = self.defaultSpreadsheetId if not spreadsheetId else spreadsheetId
        return self.with_cache(f'lyricsheets:song:{spreadsheetId}:{songName}', lambda: super(SongAPI, self).get_song(songName, spreadsheetId))

    def with_cache(self, key, f, ex=None):
        val = self.cache.get(key)
        if val is not None:
            return pickle.loads(val)

        val = f()
        if ex:
            self.cache.set(key, pickle.dumps(val), ex=ex)
        else:
            self.cache.set(key, pickle.dumps(val))

        return val
