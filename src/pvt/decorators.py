import time
from functools import wraps
import os
from typing import Callable


# todo: improve this so it can be attached to any callable object, functions,
# or methods.
def perflog(event: str):
    """
    Attached to a defined function to wrap with a performance logging feature.
    Used only when the associated environment variable is true.

    IMPORTANT: Right now this is only intended to be used with display panes.

    IMPORTANT: The specified function must take a **kwargs argument. Nuisances
    aside, the requirement allows this decorator to remain compatible with
    instance methods and classic functions alike.

    :param func: routine to decorate
    """

    def decorate(func: Callable):

        epsilon = 1e-9

        if not os.getenv("VIEWER_DEBUG") == "1":
            return func

        @wraps(func)
        def wrapper(self, *args, **kwargs):
            identifier = self.identifier
            start = time.time()
            result = func(self, *args, **kwargs)
            elapsed = time.time() - start
            print(
                f"identifier: {identifier.ljust(30)} event: {event.ljust(10)} processing time (s): {elapsed:010.07f} max possible fps: {1 / (elapsed + epsilon): 015.07f}"
            )
            return result
        return wrapper
    return decorate
