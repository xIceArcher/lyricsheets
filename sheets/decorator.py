from backoff import on_exception, expo

def token_bucket(key, num_tokens):
    def _token_bucket(f):
        class RateLimitException(Exception):
            pass

        @on_exception(expo, RateLimitException)
        def wrapper(self):
            if not self.bucket.consume(key=key, num_tokens=num_tokens):
                raise RateLimitException()

            return f(self)

        return wrapper

    return _token_bucket
