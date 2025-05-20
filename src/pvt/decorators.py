from pvt.callback import Callback
from typing import Callable, Literal, TypeVar, Any
import functools
import inspect
import os
import time

T = TypeVar("T", bound=Callable[..., Any])


# todo: consider letting users decorate their callbacks with a perf logger
# such that regardless of whether the debug flag is set, it displays to them
# the max ups, they can possibly achieve on the compute side.
#
# of course, a mention of render costs must also be made so they aren't
# thinking a compute ups of 20K means an actual possible FPS of 20K.
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


def use_parameter_cache(
    func: Callable[..., Any] | None = None,
    /,
    *,
    whitelist: list[str] = list(),
    blacklist: list[str] | Literal["all"] = list(),
) -> Any:
    """
    cache masking cases:
        - no masking strategy is specified => whitelist all (useful for same
            context displays with different parameters)
        - whitelist not empty => watch only the mentioned variables
        - blacklist not empty => watch all variables, excluding members of the blacklist
        - blacklist = all => blacklist all (useful only for static content)

    :raises ValueError:
    :return: An optimized instance of the `Callback` class.
    """
    assert not (whitelist and blacklist), "multiple strategies were specified"
    assert isinstance(whitelist, list)
    assert isinstance(blacklist, list) or (blacklist == "all")

    def check_param_name(p: str, paramset: set[str]):
        if p not in paramset:
            raise ValueError(f"`{func.__qualname__}` has no parameter `{p}`. {paramset=}")

    def decorator(func: Callable[..., Any]) -> Callback:
        config = Callback.Config()

        if isinstance(func, Callback):
            raise ValueError(
                (
                    "Instances of the `Callback` must not use this decorator. **Under the hood, this"
                    "decorator converts the decorated function into an instance of this class.**"
                    "Either you've applied the decorator multiple times to the same function, or"
                    "you're decorating a manually defined instance of the `Callback` class.... why"
                    "are you doing this?"
                )
            )

        cached_parameters: list[str] = []
        callback_paramset = {
            name
            for name, param in inspect.signature(func).parameters.items()
            if param.kind not in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)
        }

        # implement the four cases described in the docstring
        if not (whitelist or blacklist):
            cached_parameters = list(callback_paramset)
        elif whitelist:
            for p in whitelist:
                check_param_name(p, callback_paramset)
            cached_parameters = list(whitelist)
        elif blacklist:
            if blacklist == "all":
                cached_parameters = list(callback_paramset)
            else:
                for p in blacklist:
                    check_param_name(p, callback_paramset)
                cached_parameters = [p for p in callback_paramset if p not in set(blacklist)]
        else:
            raise Exception

        config.cache_type = Callback.Config.CacheType.Fake
        config.cached_parameters = tuple(cached_parameters)
        return Callback(func=func, config=config)

    if func is not None and callable(func):
        return decorator(func)
    else:
        return decorator
