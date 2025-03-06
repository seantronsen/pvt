from pvt.callback import Callback, CallbackConfig
from typing import Callable, Literal, TypeVar, Any
import functools
import inspect
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


def add_callback_optimizations(
    func: Callable[..., Any] | None = None,
    /,
    *,
    track_parameters_include: list[str] = list(),
    track_parameters_exclude: list[str] | Literal["all"] = list(),
) -> Any:
    """

    :param func:
    :param track_parameters_include:
    :param track_parameters_exclude:
    :raises ValueError:
    :return: An optimized instance of the `Callback` class.
    """
    assert not track_parameters_exclude or not track_parameters_include, "choose one or the other, not both"
    _skip_tracking = True if track_parameters_include == track_parameters_exclude == None else False

    config = CallbackConfig()

    def decorator(func: Callable[..., Any]) -> Callback:

        def check_param_name(p: str, params_valid: tuple[str, ...]):
            if p not in params_valid:
                raise ValueError(f"`{func.__qualname__}` has no parameter `{p}`. {params_valid=}")

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

        if not _skip_tracking:
            param_kind_mask = (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)
            named_parameters = tuple(
                name for name, param in inspect.signature(func).parameters.items() if param.kind not in param_kind_mask
            )
            tracked_parameters: list[str] = []
            if track_parameters_include:
                assert isinstance(track_parameters_include, list)
                tracked_parameters.extend(track_parameters_include)
                for p in track_parameters_include:
                    check_param_name(p, params_valid=named_parameters)

            elif track_parameters_exclude and track_parameters_exclude != "all":
                assert isinstance(track_parameters_exclude, list)
                tracked_parameters.extend([p for p in named_parameters if p not in track_parameters_exclude])
                for p in track_parameters_exclude:
                    check_param_name(p, params_valid=named_parameters)

            if tracked_parameters:
                config.cache_type_for_parameters = CallbackConfig.CacheType.Fake
                config.cached_parameters = tuple(tracked_parameters)
            elif not tracked_parameters or track_parameters_exclude == "all":
                config.cache_type_for_parameters = CallbackConfig.CacheType.Fake
                config.cached_parameters = tuple()

        return Callback(func=func, config=config)

    if func is not None and callable(func):
        return decorator(func)
    else:
        return decorator
