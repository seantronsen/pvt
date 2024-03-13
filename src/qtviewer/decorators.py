import time
import inspect
from functools import wraps
import os
from typing import Callable


def performance_log(func: Callable):
    """
    Attached to a defined function to wrap with a performance logging feature.
    Used only when the associated environment variable is true.

    IMPORTANT: Right now this is only intended to be used with display panes.

    IMPORTANT: The specified function must take a **kwargs argument. Nuisances
    aside, the requirement allows this decorator to remain compatible with
    instance methods and classic functions alike.

    :param func: routine to decorate
    """

    if not os.getenv("VIEWER_PERF_LOG") == "1":
        return func

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        identifier = self.identifier
        start = time.time()
        result = func(self, *args, **kwargs)
        elapsed = time.time() - start
        print(
            f"identifier: {identifier.ljust(35)} processing time (s): {elapsed:010.07f} max possible fps: {1 / elapsed: 015.07f}"
        )
        return result

    return wrapper


def inherit_docstring(func: Callable):
    """
    DOESN'T WORK... CUE THE FAILURE TROMBONE
    """

    assoc_class = globals()[str.split(func.__qualname__, sep=".")[0]]
    parent = assoc_class.__bases__[0]
    parent_method = getattr(parent, func.__name__)
    parent_docstring = parent_method.__doc__
    holder = func.__doc__ if func.__doc__ is not None else ""
    if parent_docstring is not None:
        holder += "\n"
        holder += parent_docstring
        func.__doc__ = holder

    thunk = None
    if len(inspect.signature(func).parameters) != 1:

        @wraps(func)
        def a(self, *args, **kwargs):
            return func(self, *args, **kwargs)

        thunk = a

    else:

        @wraps(func)
        def b(self):
            return func(self)

        thunk = b

    return thunk
