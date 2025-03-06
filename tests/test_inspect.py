# valid as of commit: #79a129f
from functools import lru_cache
import pytest
import inspect
from pytest_benchmark.fixture import BenchmarkFixture


N_WARMUPS = 100
N_REPEAT = 1000


def func_empty() -> None:
    pass


def func_nameless_star_args(*_) -> None:
    pass


def func_named_star_args_a(*args) -> None:
    pass


def func_named_star_args_b(*args_args) -> None:
    pass


def func_nameless_kwargs(**_) -> None:
    pass


def func_named_kwargs_a(**kwargs) -> None:
    pass


def func_named_kwargs_b(**kwargs_kwargs) -> None:
    pass


def func_named_star_args_and_kwargs(*args, **kwargs) -> None:
    pass


def func_named_args_only(a: int, b: int, c: int):
    pass


def func_named_args_and_star_args(a: int, b: int, c: int, *args):
    pass


def func_named_args_and_kwargs(a: int, b: int, c: int, **kwargs):
    pass


def func_named_args_and_star_args_and_kwargs(a: int, b: int, c: int, **kwargs):
    pass


class Fake:
    def method_named_args_and_star_args_and_kwargs(self, a: int, b: int, c: int, **kwargs):
        pass


"""
if we implement this function args cache (not really a cache, just declines a
re-run if the tracked args are the same), what is the speed cost?

if the cost is on the scale of several microseconds, then it's okay. otherwise
reconsideration may be required.

there are two options for this:
    - package: inspect
    - the function (code) attribute) (likely terse and difficult to work with efficiently)


first, what are the args we care about?
- the library works using nameed parameters as keynames for particular state
  elements. so only those.


where should such a cache be implemented? should it be
- a decorator on the user callback function?
- under the hood, something held by state instances (or contexts) which applies
  in a manner somewhat hidden to the user. this could be something that's
  configured on a base data display config class passed to the widget instance.

need to define a function which takes some args and computes a result which
depends on the args (it's possible there's optimizations under the hood for
these None returning funcs).

need to define a decorator which caches the previous call args (only) and
checks if the current args are the same


"""

# benchmarks to do:
# - inspect speed check
# - speed to check cached named args (needs impl)
# - speed to check cached named args (needs impl)

import inspect


class TestBenchmark_InspectSignature:
    def test_func_empty(self, benchmark: BenchmarkFixture) -> None:
        benchmark(inspect.signature, func_empty)

    def test_func_nameless_star_args(self, benchmark: BenchmarkFixture) -> None:
        benchmark(inspect.signature, func_nameless_star_args)

    def test_func_named_star_args_a(self, benchmark: BenchmarkFixture) -> None:
        benchmark(inspect.signature, func_named_star_args_a)

    def test_func_named_star_args_b(self, benchmark: BenchmarkFixture) -> None:
        benchmark(inspect.signature, func_named_star_args_b)

    def test_func_nameless_kwargs(self, benchmark: BenchmarkFixture) -> None:
        benchmark(inspect.signature, func_nameless_kwargs)

    def test_func_named_kwargs_a(self, benchmark: BenchmarkFixture) -> None:
        benchmark(inspect.signature, func_named_kwargs_a)

    def test_func_named_kwargs_b(self, benchmark: BenchmarkFixture) -> None:
        benchmark(inspect.signature, func_named_kwargs_b)

    def test_func_named_star_args_and_kwargs(self, benchmark: BenchmarkFixture) -> None:
        benchmark(inspect.signature, func_named_star_args_and_kwargs)

    def test_func_named_args_only(self, benchmark: BenchmarkFixture):
        benchmark(inspect.signature, func_named_args_only)

    def test_func_named_args_and_star_args(self, benchmark: BenchmarkFixture):
        benchmark(inspect.signature, func_named_args_and_star_args)

    def test_func_named_args_and_kwargs(self, benchmark: BenchmarkFixture):
        benchmark(inspect.signature, func_named_args_and_kwargs)

    def test_func_named_args_and_star_args_and_kwargs(self, benchmark: BenchmarkFixture):
        benchmark(inspect.signature, func_named_args_and_star_args_and_kwargs)

    def test_fake_method_named_args_and_star_args_and_kwargs(self, benchmark: BenchmarkFixture):
        faker = Fake()
        benchmark(inspect.signature, faker.method_named_args_and_star_args_and_kwargs)


def find_named_args(func) -> tuple[str, ...]:
    sig = inspect.signature(func)
    return tuple(
        name
        for name, param in sig.parameters.items()
        if param.kind not in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)
    )


class TestBenchmark_FindNamedArgs:
    def test_func_empty(self, benchmark: BenchmarkFixture) -> None:
        benchmark(find_named_args, func_empty)

    def test_func_nameless_star_args(self, benchmark: BenchmarkFixture) -> None:
        benchmark(find_named_args, func_nameless_star_args)

    def test_func_named_star_args_a(self, benchmark: BenchmarkFixture) -> None:
        benchmark(find_named_args, func_named_star_args_a)

    def test_func_named_star_args_b(self, benchmark: BenchmarkFixture) -> None:
        benchmark(find_named_args, func_named_star_args_b)

    def test_func_nameless_kwargs(self, benchmark: BenchmarkFixture) -> None:
        benchmark(find_named_args, func_nameless_kwargs)

    def test_func_named_kwargs_a(self, benchmark: BenchmarkFixture) -> None:
        benchmark(find_named_args, func_named_kwargs_a)

    def test_func_named_kwargs_b(self, benchmark: BenchmarkFixture) -> None:
        benchmark(find_named_args, func_named_kwargs_b)

    def test_func_named_star_args_and_kwargs(self, benchmark: BenchmarkFixture) -> None:
        benchmark(find_named_args, func_named_star_args_and_kwargs)

    def test_func_named_args_only(self, benchmark: BenchmarkFixture):
        benchmark(find_named_args, func_named_args_only)

    def test_func_named_args_and_star_args(self, benchmark: BenchmarkFixture):
        benchmark(find_named_args, func_named_args_and_star_args)

    def test_func_named_args_and_kwargs(self, benchmark: BenchmarkFixture):
        benchmark(find_named_args, func_named_args_and_kwargs)

    def test_func_named_args_and_star_args_and_kwargs(self, benchmark: BenchmarkFixture):
        benchmark(find_named_args, func_named_args_and_star_args_and_kwargs)

    def test_fake_method_named_args_and_star_args_and_kwargs(self, benchmark: BenchmarkFixture):
        faker = Fake()
        benchmark(find_named_args, faker.method_named_args_and_star_args_and_kwargs)


class TestBenchmark_CachedFindNamedArgs:
    def test_func_empty(self, benchmark: BenchmarkFixture) -> None:
        benchmark(lru_cache(maxsize=None)(find_named_args), func_empty)

    def test_func_nameless_star_args(self, benchmark: BenchmarkFixture) -> None:
        benchmark(lru_cache(maxsize=None)(find_named_args), func_nameless_star_args)

    def test_func_named_star_args_a(self, benchmark: BenchmarkFixture) -> None:
        benchmark(lru_cache(maxsize=None)(find_named_args), func_named_star_args_a)

    def test_func_named_star_args_b(self, benchmark: BenchmarkFixture) -> None:
        benchmark(lru_cache(maxsize=None)(find_named_args), func_named_star_args_b)

    def test_func_nameless_kwargs(self, benchmark: BenchmarkFixture) -> None:
        benchmark(lru_cache(maxsize=None)(find_named_args), func_nameless_kwargs)

    def test_func_named_kwargs_a(self, benchmark: BenchmarkFixture) -> None:
        benchmark(lru_cache(maxsize=None)(find_named_args), func_named_kwargs_a)

    def test_func_named_kwargs_b(self, benchmark: BenchmarkFixture) -> None:
        benchmark(lru_cache(maxsize=None)(find_named_args), func_named_kwargs_b)

    def test_func_named_star_args_and_kwargs(self, benchmark: BenchmarkFixture) -> None:
        benchmark(lru_cache(maxsize=None)(find_named_args), func_named_star_args_and_kwargs)

    def test_func_named_args_only(self, benchmark: BenchmarkFixture):
        benchmark(lru_cache(maxsize=None)(find_named_args), func_named_args_only)

    def test_func_named_args_and_star_args(self, benchmark: BenchmarkFixture):
        benchmark(lru_cache(maxsize=None)(find_named_args), func_named_args_and_star_args)

    def test_func_named_args_and_kwargs(self, benchmark: BenchmarkFixture):
        benchmark(lru_cache(maxsize=None)(find_named_args), func_named_args_and_kwargs)

    def test_func_named_args_and_star_args_and_kwargs(self, benchmark: BenchmarkFixture):
        benchmark(lru_cache(maxsize=None)(find_named_args), func_named_args_and_star_args_and_kwargs)

    def test_fake_method_named_args_and_star_args_and_kwargs(self, benchmark: BenchmarkFixture):
        faker = Fake()
        benchmark(lru_cache(maxsize=None)(find_named_args), faker.method_named_args_and_star_args_and_kwargs)


#
# def test_callback_engine_experimental_single(qtbot: QtBot, benchmark: BenchmarkFixture):
#
#     display = MockExperimentalStatefulDisplay()
#     control = MockExperimentalStatefulControl()
#     context = MockExperimentalVisContext.create_viewer_with_vertical_layout([display, control])
#
#     for _ in range(N_WARMUPS):
#         control.complain()
#
#     assert display.render_call_counter != 0
#     n_total = display.render_call_counter
#     benchmark(control.complain)
#     assert display.render_call_counter > n_total
#
