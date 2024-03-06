import time
from functools import wraps
import os
from typing import Callable


def performance_log(func: Callable):
    """
    Attached to a defined function to wrap with a performance logging feature.
    Used only when the associated environment variable is true.

    IMPORTANT: The specified function must take a **kwargs argument. Nuisances
    aside, the requirement allows this decorator to remain compatible with
    instance methods and classic functions alike.

    :param func: routine to decorate
    """

    if os.getenv("VIEWER_PERF_LOG") == "1":
        return func

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        start = time.time()
        result = func(self, *args, **kwargs)
        elapsed = time.time() - start
        print(f"processing time: {elapsed:08.05f} max possible fps: {1 / elapsed: 08.03f}")
        return result

    return wrapper
