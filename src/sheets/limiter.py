from token_bucket import Limiter, MemoryStorage, StorageBase

from time import time


class BurstLimiter:
    def __init__(
        self, rate: float, capacity: float, initialCapacity: float, storage: StorageBase
    ) -> None:
        self._initialLimiter = Limiter(1e-999, initialCapacity, MemoryStorage())
        self._constantRateLimiter = Limiter(rate, capacity, storage)
        self._initTime = time()
        self._initialCoolTime = initialCapacity / rate

    def consume(self, key, num_tokens=1):
        if self._initialLimiter.consume(key, num_tokens):
            return True

        if time() - self._initTime < self._initialCoolTime:
            return False

        return self._constantRateLimiter.consume(key, num_tokens)
