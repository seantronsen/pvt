from pvt.state import VisualizerControlSignal, VisualizerState
from copy import deepcopy
from pytest import fixture
from pytest_benchmark.fixture import BenchmarkFixture
from pytestqt.qtbot import QtBot
from pytest_mock import MockerFixture


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
    def state_prepped(self):
        _state = MockVisualizerState()
        _state.set_storage(deepcopy(self.init_storage))
        return _state

    def test_init(self, benchmark: BenchmarkFixture):
        # test
        VisualizerState()
        mock_state = MockVisualizerState()
        assert mock_state.storage == {}
        mock_state.set_storage(storage=self.init_storage)
        assert mock_state.storage == self.init_storage

        # benchmark
        benchmark(VisualizerState)

    def test_modify_state(
        self,
        benchmark: BenchmarkFixture,
        qtbot: QtBot,
        mocker: MockerFixture,
        state_prepped: MockVisualizerState,
    ):
        # ensure initial state assumptions hold
        assert state_prepped.storage == self.init_storage

        # set up the mockery
        mock = mocker.Mock()
        state_prepped.state_changed.connect(mock)

        # define modifictions
        control_signal = VisualizerControlSignal(key="a_modification", value=0)
        expected_mod_state = deepcopy(self.init_storage)
        expected_mod_state[control_signal.key] = control_signal.value

        # do the modification
        with qtbot.waitSignal(state_prepped.state_changed, timeout=1000):
            state_prepped.modify_state(arg=control_signal)

        # assert changes
        mock.assert_called_once_with(expected_mod_state)

        # benchmark the routine
        state_prepped.state_changed.disconnect()
        benchmark(state_prepped.modify_state, control_signal)

    def test_flush(
        self,
        benchmark: BenchmarkFixture,
        qtbot: QtBot,
        mocker: MockerFixture,
        state_prepped: MockVisualizerState,
    ):

        # test
        mock = mocker.Mock()
        state_prepped.state_changed.connect(mock)

        with qtbot.waitSignal(state_prepped.state_changed, timeout=1000):
            state_prepped.flush()
        mock.assert_called_once_with(self.init_storage)

        # benchmark
        state_prepped.state_changed.disconnect()
        benchmark(state_prepped.flush)
