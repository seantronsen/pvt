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
       routine's qualified name (`__qualname__`) as the primary label.

       **However**, if the decorated routine is an instance method and that
       same instance has an attribute named `identifier`, the value referenced
       by the attribute will override the original default. This situation
       typically applies only to widget's in this library whose names are
       prefixed with `Stateful`.

    2. **with arguments:**
       When used with configuration options (e.g., `@perflog(label="Custom
       Label", event="compute")`), the arguments provided will override any
       afformentioned default values.

    **Parameters:**
      - *dkwargs*: Optional configuration parameters:
          - `label` (Optional[str]): Custom label for the log output. Defaults
            to the function's `__qualname__`.
          - `event` (Optional[str]): Can be used to indicate in logs which
            event category the routine belongs to (e.g., render, compute, etc.).

    **Example:**

        @perflog(label="Subtraction Routine", event="compute")
        def subtract(a: int, b: int) -> int:
            return a - b

        class MyClass:

            @perflog
            def multiply(self, a: int, b: int) -> int:
                return a * b
    """

    epsilon = 1e-9
    flag_should_log = os.getenv("VIEWER_DEBUG") == "1"

    def decorator(func: T) -> T:

        label: str = dkwargs.get("label", func.__qualname__)
        event: str = dkwargs.get("event", "")

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
