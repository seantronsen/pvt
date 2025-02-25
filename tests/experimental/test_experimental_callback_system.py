import pytest
from pytest_benchmark.fixture import BenchmarkFixture
from pytestqt.qtbot import QtBot
from pvt.experimental.context import VisualizerContext as ExperimentalVisualizerContext
from pvt.experimental.controls import StatefulControl as ExperimentalStatefulControl
from pvt.experimental.displays import StatefulDisplay as ExperimentalStatefulDisplay
from pvt.panels import StatefulPane as OldStatefulDisplay
from pvt.widgets import StatefulWidget as OldStatefulControl

N_WARMUPS = 100
N_REPEAT = 1000


def nothing(**_) -> None:
    pass


class MockExperimentalVisContext(ExperimentalVisualizerContext):
    pass


class MockExperimentalStatefulDisplay(ExperimentalStatefulDisplay):

    render_call_counter = 0

    def __init__(self) -> None:
        super().__init__(callback=nothing, title="mock display")

    # do nothing. we're testing the callback system speed, not anything directly computational
    def _render_data(self, *_):
        self.render_call_counter += 1


class MockExperimentalStatefulControl(ExperimentalStatefulControl):

    def __init__(self) -> None:
        self.__dummy_ix = 0
        super().__init__(key="mock-test", initial_value=0)

    # identical follow-up events may result in Qt's event loop ignoring the
    # signal
    def value(self) -> object:
        self.__dummy_ix += 1
        return self.__dummy_ix

    def complain(self):
        self._on_change()


def test_nothing(benchmark: BenchmarkFixture):
    benchmark(nothing)


def test_callback_engine_experimental_single(qtbot: QtBot, benchmark: BenchmarkFixture):

    display = MockExperimentalStatefulDisplay()
    control = MockExperimentalStatefulControl()
    context = MockExperimentalVisContext.create_viewer_with_vertical_layout([display, control])

    for _ in range(N_WARMUPS):
        control.complain()

    assert display.render_call_counter != 0
    n_total = display.render_call_counter
    benchmark(control.complain)
    assert display.render_call_counter > n_total


def test_callback_engine_experimental_many(qtbot: QtBot, benchmark: BenchmarkFixture):

    display = MockExperimentalStatefulDisplay()
    control = MockExperimentalStatefulControl()
    context = MockExperimentalVisContext.create_viewer_with_vertical_layout([display, control])

    for _ in range(N_WARMUPS):
        control.complain()

    def foo():
        for _ in range(N_REPEAT):
            control.complain()

    benchmark(foo)


class MockOldStatefulControl(OldStatefulControl):

    dummy_ix = 0

    def __init__(self) -> None:
        super().__init__(key="mock-old", init=self.dummy_ix)

    def on_change(self, *_):
        self.dummy_ix += 1
        self.state_update(self.dummy_ix)

    def complain(self):
        self.on_change()


class MockOldStatefulDisplay(OldStatefulDisplay):

    render_call_counter = 0

    def __init__(self) -> None:
        super().__init__(callback=nothing)

    def render_data(self, *args):
        self.render_call_counter += 1


def test_callback_engine_original_single(qtbot: QtBot, benchmark: BenchmarkFixture):

    display = MockOldStatefulDisplay()
    control = MockOldStatefulControl()
    display.enchain(control)

    for _ in range(N_WARMUPS):
        control.complain()

    assert display.render_call_counter != 0
    n_total = display.render_call_counter
    benchmark(control.complain)
    assert display.render_call_counter > n_total


def test_callback_engine_original_many(qtbot: QtBot, benchmark: BenchmarkFixture):

    display = MockOldStatefulDisplay()
    control = MockOldStatefulControl()
    display.enchain(control)

    def foo():
        for _ in range(N_REPEAT):
            control.complain()

    for _ in range(N_WARMUPS):
        control.complain()

    benchmark(foo)
