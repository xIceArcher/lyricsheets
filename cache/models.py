from abc import ABC, abstractmethod
from datetime import timedelta
from typing import Optional, Protocol

class Cache(ABC):
    @abstractmethod
    def get(self, key: str) -> Optional[bytes]: ...

    @abstractmethod
    def set(self, key: str, val: bytes, ex: Optional[float | timedelta] = None) -> Optional[bool]: ...

class Cacheable(Protocol):
    cache: Cache
