from abc import abstractmethod
from collections.abc import Mapping

from src.models import Song


class NotFoundError(Exception):
    pass


class SongService:
    @abstractmethod
    def get_song(self, songName: str, spreadsheetId: str = "") -> Song:
        ...

    @abstractmethod
    def get_format_tags(self, spreadsheetId: str = "") -> Mapping[str, str]:
        ...
