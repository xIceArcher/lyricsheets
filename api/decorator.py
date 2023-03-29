import pickle
from typing import Optional

def with_cache(keyPrefix: str, expiry: Optional[float] = None):
    def _with_cache(f):
        def wrapper(self, *args, **kwargs):
            if kwargs:
                raise RuntimeError('kwargs not allowed when using with_cache decorator')

            key = ':'.join([keyPrefix, ':'.join(args)])

            val = self.cache.get(key)
            if val is not None:
                return pickle.loads(val)

            val = f(self, *args)
            if expiry:
                self.cache.set(key, pickle.dumps(val), ex=expiry)
            else:
                self.cache.set(key, pickle.dumps(val))

            return val

        return wrapper

    return _with_cache
