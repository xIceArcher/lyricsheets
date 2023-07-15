from abc import abstractmethod
from collections.abc import Mapping

from src.models import Song


class NotFoundError(Exception):
    pass


class SongService:
    @abstractmethod
    def get_song(self, songName: str) -> Song:
        ...

    @abstractmethod
    def get_format_tags(self, group: str = "") -> Mapping[str, str]:
        ...

    @abstractmethod
    def get_all_format_tags(self) -> Mapping[str, str]:
        ...

    @abstractmethod
    def save_song(self, song: Song, group: str = ""):
        ...
