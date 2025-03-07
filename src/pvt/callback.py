from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable
import functools


class Callback:
    """
    Users should not be creating this class directly. Use one of the decorators
    provided by this library instead.
    """

    @dataclass
    class Config:
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
        The holder of the callback should use this method to determine whether
        the callback should be executed.

        :return: flag to indicate if the callback needs to run (is in dirty state)
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

        # always compute and render the first frame at the very least
        return True

    def _should_run(self, *_, **kwds) -> bool:
        is_dirty = False
        for k in self._parameter_cache.keys():
            if self._parameter_cache[k] != kwds[k]:
                self._parameter_cache[k] = kwds[k]
                is_dirty = True

        return is_dirty
