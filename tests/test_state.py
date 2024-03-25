from qtviewer import State
from pytest import fixture
from copy import deepcopy


class TestState:

    init_storage = dict(a=0, b=1, c=2)

    def callback(self, **kwargs):
        return kwargs

    @fixture
    def state(self):
        return State(callback=self.callback, init=deepcopy(self.init_storage))

    def test_init(self, benchmark):
        # test
        assert State(callback=self.callback).storage == {}
        assert State(callback=self.callback, init=self.init_storage).storage == self.init_storage

        # benchmark
        benchmark(State, callback=self.callback, init=self.init_storage)

    def test_get(self, state):
        assert state.storage == self.init_storage
        assert state["a"] == 0

    def test_set(self, state):
        state["a"] += 1
        self.init_storage["a"] += 1
        assert state["a"] == 1
        assert self.init_storage["a"] == 1
        assert self.init_storage == state.storage

    def test_flush(self, benchmark, mocker):

        # test
        mock = mocker.Mock()
        state = State(callback=mock, init=self.init_storage)
        state.flush()
        assert mock.call_args[1] == self.init_storage

        # benchmark
        state = State(callback=lambda **_: None, init=self.init_storage)
        benchmark(state.flush)
