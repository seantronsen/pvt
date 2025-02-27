import time
import os
import functools
from typing import Callable, TypeVar, Any


T = TypeVar("T", bound=Callable[..., Any])


def perflog(*dargs: Any, **dkwargs: Any) -> Any:

    epsilon = 1e-9
    flag_should_log = os.getenv("VIEWER_DEBUG") == "1"

    def decorator(func: T) -> T:

        label: str = dkwargs.get("label", func.__qualname__)
        event: str = dkwargs.get("extra_info", "")

        if not flag_should_log:
            return func

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:

            # explicitly annotate nonlocals to *appease* the static type checker... sigh.
            nonlocal label, event

            # check if args[0] is an instance parameter (self) and see if
            # instance has attr 'identifier'
            attr_label = "identifier"
            if args and not isinstance(args[0], type) and hasattr(args[0], attr_label):
                label = str(getattr(args[0], attr_label))

            start_time = time.perf_counter()
            result = func(*args, **kwargs)
            elapsed: float = time.perf_counter() - start_time

            print(
                f"identifier: {label.ljust(30)} "
                f"{f"event: {event.ljust(10)}" if event else ""} "
                f"processing time (s): {elapsed:010.07f} "
                f"updates per second: {1 / (elapsed + epsilon):015.07f}"
            )
            return result

        return wrapper  # type: ignore

    # used without parameters, dargs[0] is the function.
    if dargs and callable(dargs[0]):
        return decorator(dargs[0])
    else:
        return decorator


# note: the implementation above is cleaner, but not the best for python's static typing.
# the one below is an improvement that removes the errors, but is more
# complicated and contains more repeated codes.
#
# def perf_logger(*dargs: Any, **dkwargs: Any) -> Any:
#
#     epsilon = 1e-9
#     flag_should_log = os.getenv("VIEWER_DEBUG") == "1"
#
#     if dargs and callable(dargs[0]):
#         func = dargs[0]
#         if not flag_should_log:
#             return func
#
#         @functools.wraps(func)
#         def wrapper(*args: Any, **kwargs: Any) -> Any:
#
#             label = func.__qualname__
#             if args and not isinstance(args[0], type) and hasattr(args[0], 'identifier'):
#                 label = str(getattr(args[0], 'name'))
#
#             start_time: float = time.perf_counter()
#             result = func(*args, **kwargs)
#             elapsed: float = time.perf_counter() - start_time
#             message = (
#                 f"identifier: {label.ljust(30)} "
#                 f"processing time (s): {elapsed:010.07f} "
#                 f"updates per second: {1 / (elapsed + epsilon):015.07f}"
#             )
#
#             print(message)
#             return result
#
#         return wrapper
#     else:
#         label: str | None = dkwargs.get("label", None)
#
#         def decorator(func: T) -> T:
#             if not flag_should_log:
#                 return func
#
#             label: str = label if label is not None else func.__qualname__
#
#             @functools.wraps(func)
#             def wrapper(*args: Any, **kwargs: Any) -> Any:
#                 start_time: float = time.perf_counter()
#                 result = func(*args, **kwargs)
#                 elapsed: float = time.perf_counter() - start_time
#
#                 message = (
#                     f"identifier: {label.ljust(30)} "
#                     f"event: {event.ljust(10)} "
#                     f"processing time (s): {elapsed:010.07f} "
#                     f"updates per second: {1 / (elapsed + epsilon):015.07f}"
#                 )
#
#                 print(message)
#
#                 return result
#
#             return wrapper  # type: ignore
#
#         return decorator
