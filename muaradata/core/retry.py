import time
import functools

class RetryConfig:
    def __init__(self, retries=5, delay=5, backoff=1.0, exceptions=(Exception,)):
        self.retries = retries
        self.delay = delay
        self.backoff = backoff
        self.exceptions = exceptions


def with_retry(config: RetryConfig):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 0
            wait = config.delay

            while True:
                try:
                    return func(*args, **kwargs)
                except config.exceptions as e:
                    attempt += 1
                    if attempt >= config.retries:
                        raise
                    print(f"[Retry {attempt}] {e} – retry in {wait}s")
                    time.sleep(wait)
                    wait *= config.backoff
        return wrapper
    return decorator
