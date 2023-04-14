from abc import abstractmethod

from ..models import Song


class NotFoundError(Exception):
    pass


class SongService:
    @abstractmethod
    def get_song(self, songName: str, spreadsheetId: str = "") -> Song:
        ...
