from typing import Dict
from qtviewer import State
from pytest import fixture
from copy import deepcopy


@fixture
def init_storage() -> Dict[str, int]:
    return dict(a=0, b=1, c=2)


@fixture
def callback():
    def c(**kwargs):
        return kwargs

    return c


@fixture
def state(callback, init_storage):
    return State(callback=callback, init=deepcopy(init_storage))


def test_state_init(benchmark, callback, init_storage):
    # test
    assert State(callback=callback).storage == {}
    assert State(callback=callback, init=init_storage).storage == init_storage

    # benchmark
    benchmark(State, callback=callback, init=init_storage)


def test_state_get(state, init_storage):
    assert state.storage == init_storage
    assert state["a"] == 0


def test_state_set(state, init_storage):
    state["a"] += 1
    init_storage["a"] += 1
    assert state["a"] == 1
    assert init_storage["a"] == 1
    assert init_storage == state.storage


def test_state_flush(benchmark, mocker, init_storage):

    # test
    mock = mocker.Mock()
    state = State(callback=mock, init=init_storage)
    state.flush()
    assert mock.call_args[1] == init_storage

    # benchmark
    state = State(callback=lambda **_: None, init=init_storage)
    benchmark(state.flush)
