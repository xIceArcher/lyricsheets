from typing import Optional

from .models import Cache


class MemoryCache(Cache):
    def __init__(self) -> None:
        self.cache = {}

    def get(self, key: str) -> Optional[bytes]:
        try:
            return self.cache[key]
        except KeyError:
            return None

    def set(self, key: str, val: bytes):
        self.cache[key] = val

    def delete(self, key: str):
        del self.cache[key]
