from collections.abc import Mapping
from typing import Optional

from .decorator import with_cache
from .scan import scan_song

from ..models import models

from apiclient import discovery
from google.oauth2 import service_account
from redis import Redis


class SongServer:
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

    def __init__(self, googleCredentials: Mapping[str, str], spreadsheetId: Optional[str]) -> None:
        self.defaultSpreadsheetId = spreadsheetId
        self.service = discovery.build(
            'sheets',
            'v4',
            credentials=service_account.Credentials.from_service_account_info(googleCredentials, scopes=SongServer.SCOPES)
        ).spreadsheets()

    def get_song(self, songName: str, spreadsheetId: Optional[str]=None) -> models.Song:
        if not self.defaultSpreadsheetId and not spreadsheetId:
            raise RuntimeError('Spreadsheet ID not specified!')

        return scan_song(self.service, self.defaultSpreadsheetId if not spreadsheetId else spreadsheetId, songName)


class CachedSongServer(SongServer):
    def __init__(self, googleCredentials: Mapping[str, str], spreadsheetId: Optional[str], host: str, port: int, db: int):
        super().__init__(googleCredentials, spreadsheetId)
        self.cache = Redis(host=host, port=port, db=db)

    def get_song(self, songName: str, spreadsheetId: Optional[str]=None) -> models.Song:
        return self._get_song(self.defaultSpreadsheetId if not spreadsheetId else spreadsheetId, songName)

    @with_cache(f'lyricsheets:song')
    def _get_song(self, spreadsheetId: Optional[str], songName: str) -> models.Song:
        return super().get_song(songName, spreadsheetId)
