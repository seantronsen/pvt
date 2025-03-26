from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable
import functools


class Callback:
    """
    A wrapper for user-defined callbacks that adds extra features.

    Users should use the provided decorators rather than instantiating this
    class directly.
    """

    @dataclass
    class Config:
        """
        Configuration for Callback behavior.

        Attributes:
            cache_type: Determines the caching strategy.
            cached_parameters: Names of parameters to cache.
        """

        class CacheType(Enum):
            Fake = 0

        cache_type: CacheType | None = None
        cached_parameters: tuple[str, ...] = tuple()

    def __init__(self, func: Callable[..., Any], config: Config = Config()) -> None:
        self._func = func
        self._config = config
        self._parameter_cache: dict[str, object] = {p: None for p in self._config.cached_parameters}

        functools.update_wrapper(wrapper=self, wrapped=func)

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        return self._func(*args, **kwds)

    def should_run(self, *_, **kwds) -> bool:
        """
        Determines whether the callback should be executed.

        On the first call, this method overrides itself to avoid repeated conditional checks.
        If caching is enabled, it will use the _should_run method for subsequent calls.

        :return: True if the callback should run; otherwise, False.
        """

        ################################################################################
        # to avoid extra conditionals being executed on subsequent calls, the
        # original method is overwritten after the first execution call based
        # on whether caching should occur.
        ################################################################################

        # forbidden bullshit can be useful sometimes
        self.should_run = lambda *a, **k: True
        if self._config.cache_type == Callback.Config.CacheType.Fake:
            self.should_run = self._should_run

        # always compute and render the first frame
        # otherwise a blank display results on startup
        return True

    def _should_run(self, *_, **kwds) -> bool:
        """
        Checks if any cached parameter has changed. Compares the current
        keyword arguments with cached values and updates the cache.

        :return: True if at least one parameter value has changed; otherwise,
            False.
        """
        is_dirty = False
        for k in self._parameter_cache.keys():
            if self._parameter_cache[k] != kwds[k]:
                self._parameter_cache[k] = kwds[k]
                is_dirty = True

        return is_dirty
