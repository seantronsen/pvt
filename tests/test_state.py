from copy import deepcopy
from pvt.state import VisualizerState
from pytest import fixture


class MockVisualizerState(VisualizerState):

    @property
    def storage(self):
        return self._storage

    def set_storage(self, storage: dict[str, object]):
        self._storage = storage


class TestState:

    init_storage: dict[str, object] = dict(a=0, b=1, c=2)

    def callback(self, **kwargs):
        return kwargs

    @fixture
    def state(self):
        _state = MockVisualizerState()
        return _state

    @fixture
    def state_prepped(self, state):
        _state = MockVisualizerState()
        _state.set_storage(self.init_storage)
        return _state

    def test_init(self, benchmark):
        # test
        VisualizerState()
        mock_state = MockVisualizerState()
        assert mock_state.storage == {}
        mock_state.set_storage(storage=self.init_storage)
        assert mock_state.storage == self.init_storage

        # benchmark
        benchmark(VisualizerState)

    # def test_flush(self, benchmark, qtbot, state_prepped):

    #     # test
    #     mock = mocker.Mock()
    #     state = State(callback=mock, init=self.init_storage)
    #     state.flush()
    #     assert mock.call_args[1] == self.init_storage

    #     # benchmark
    #     state = State(callback=lambda **_: None, init=self.init_storage)
    #     benchmark(state.flush)
