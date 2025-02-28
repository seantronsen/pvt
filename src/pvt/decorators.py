from typing import Callable, TypeVar, Any
import functools
import os
import time

T = TypeVar("T", bound=Callable[..., Any])


def perflog(*dargs: Any, **dkwargs: Any) -> Any:
    """
    A decorator for logging the performance (execution time) of functions and
    methods. It supports two usage modes:

    1. **without arguments:**
       When used directly (e.g., `@perflog`), the decorator logs the execution time using the
       function's qualified name (`__qualname__`) as the label.

    2. **with arguments:**
       When used with configuration options (e.g., `@perflog(label="Custom Label", extra_info="Info")`),
       the provided `label` is used in the log message, and any additional information supplied via
       `extra_info` is appended.

    NOTE: There exists a priority order for which default labels are
    overridden. At the bottom is the __qualname__ of the routine. However, if
    the decorated routine is an instance method and said instance has an
    attribute `identifier`, the label then becomes the value of that attribute.
    At the top level, if `label` is provided as a kwarg to the decorator, it
    will **always** override any previous definitions.


    **Parameters:**
      - *dkwargs*: Optional configuration parameters:
          - `label` (Optional[str]): Custom label for the log output. Defaults
            to the function's `__qualname__`.
          - `event` (Optional[str]): Can be used to indicate in logs which
            event category the routine belongs to (e.g., render, compute, etc.).

    **Example:**

        @perflog
        def add(a: int, b: int) -> int:
            return a + b

        @perflog(label="Subtraction Routine", extra_info="Subtracting numbers")
        def subtract(a: int, b: int) -> int:
            return a - b

        class MyClass:
            def __init__(self, name: str) -> None:
                self.name = name

            @perflog
            def multiply(self, a: int, b: int) -> int:
                return a * b
    """

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
