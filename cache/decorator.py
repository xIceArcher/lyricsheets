import pickle

from .models import Cacheable


def with_cache(keyPrefix: str):
    def _with_cache(f):
        def wrapper(self: Cacheable, *args: str, **kwargs):
            if self.cache is None or kwargs:
                return f(self, *args)

            key = ":".join([keyPrefix, ":".join(args)])

            val = self.cache.get(key)
            if val is not None:
                return pickle.loads(val)

            val = f(self, *args)
            self.cache.set(key, pickle.dumps(val))

            return val

        return wrapper

    return _with_cache
