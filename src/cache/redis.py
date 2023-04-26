from typing import Optional

from redis import Redis

from .models import Cache


class RedisCache(Cache):
    def __init__(self, host: str, port: int, db: int) -> None:
        self.cache = Redis(host=host, port=port, db=db)

    def get(self, key: str) -> Optional[bytes]:
        return self.cache.get(key)

    def set(self, key: str, val: bytes):
        self.cache.set(key, val)
