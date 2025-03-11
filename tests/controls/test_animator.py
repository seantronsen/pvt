from typing import cast
from PySide6.QtWidgets import QHBoxLayout, QWidget
from pvt.context import VisualizerContext
from pvt.controls import StatefulAnimator
from pvt.state import VisualizerControlSignal
import pytest
from pytest_benchmark.fixture import BenchmarkFixture
from pytestqt.qtbot import QtBot


class MockAnimator(StatefulAnimator):
    """Wrapper with convenience methods for testing."""

    def timer_is_active(self):
        return self._timer.isActive()

    def timer_timeout_signal(self):
        return self._timer.timeout

    def control_on_control_signal_changed(self):
        return self.on_control_signal_changed


class MockAnimatorContext(QWidget):
    """
    Defined as such in case for future testing, we want to add mock subscribers
    under this context.
    """

    def __init__(self, ups: int = 60):
        super().__init__()
        layout = QHBoxLayout()
        self.animator = MockAnimator(ups=ups, auto_start=False)
        self.ctxt = VisualizerContext.create_viewer_from_mosaic([[self.animator]])
        layout.addWidget(self.ctxt)
        self.setLayout(layout)


class TestAnimator:

    @pytest.fixture
    def mock_animator(self, qtbot: QtBot):
        mock = MockAnimatorContext()
        qtbot.addWidget(mock)
        return mock

    def test__init__(self, qtbot, benchmark):
        sa = StatefulAnimator(ups=60)
        qtbot.addWidget(sa)
        assert sa._time_of_previous_render == 0
        benchmark(StatefulAnimator, ups=60)

    def test_value(self, benchmark: BenchmarkFixture, mock_animator: MockAnimatorContext):
        animator = mock_animator.animator
        benchmark(animator.value)
        assert animator.value() == 0, "unexpected initial animation tick value"

    def test_forward(self, benchmark: BenchmarkFixture, mock_animator: MockAnimatorContext):
        animator = mock_animator.animator
        assert animator.value() == 0, "unexpected initial animation tick value"
        animator.forward()
        assert animator.value() == 1, "unexpected animation tick value after increment"
        animator.forward()
        assert animator.value() == 2, "unexpected animation tick value after increment"
        benchmark(animator.forward)

    def test_reverse(self, benchmark: BenchmarkFixture, mock_animator: MockAnimatorContext):
        animator = mock_animator.animator
        assert animator.value() == 0, "unexpected initial animation tick value"
        animator.forward()
        assert animator.value() == 1, "unexpected animation tick value after increment"
        animator.reverse()
        assert animator.value() == 0, "unexpected animation tick value after decrement"

        # ignore obvious uint underflow.... for now.
        benchmark(animator.forward)

    def test_reset(self, benchmark: BenchmarkFixture, mock_animator: MockAnimatorContext):
        animator = mock_animator.animator
        assert animator.value() == 0, "unexpected initial animation tick value"
        animator.forward()
        assert animator.value() != 0, "unexpected animation tick value after increment"
        animator.reset()
        assert animator.value() == 0, "unexpected animation tick value after reset"
        benchmark(animator.reset)

    def test_pause_play(self, qtbot: QtBot, benchmark: BenchmarkFixture, mock_animator: MockAnimatorContext):

        animator = mock_animator.animator

        # simulate play button
        assert not animator.timer_is_active()
        with qtbot.waitSignal(animator.timer_timeout_signal(), timeout=1000):
            animator.pause_play()

        # simulate pause button
        assert animator.timer_is_active()
        animator.pause_play()
        assert not animator.timer_is_active()

        # benchmark state toggle
        benchmark(animator.pause_play)

    def test_on_tick_event__animation_tick_incremented(
        self,
        qtbot: QtBot,
        mock_animator: MockAnimatorContext,
    ):
        animator = mock_animator.animator
        tick_init = cast(int, animator.value())

        # simulate play button press
        assert not animator.timer_is_active()
        with qtbot.waitSignal(animator.timer_timeout_signal(), timeout=1000):
            animator.pause_play()

        assert animator.timer_is_active()
        animator.pause_play()
        assert not animator.timer_is_active()
        tick_current = cast(int, animator.value())
        assert tick_current > tick_init, "the timer started ticking, but animation_tick did not increment"

    def test_on_tick_event_emit_on_changed(self, qtbot: QtBot, mock_animator: MockAnimatorContext):
        animator = mock_animator.animator
        tick_init = cast(int, animator.value())

        # simulate play button press
        assert not animator.timer_is_active()
        with qtbot.waitSignal(animator.on_control_signal_changed, timeout=1000) as blocker:
            animator.on_tick()

        # assert play and then pause immediately after
        assert isinstance(blocker.args[0], VisualizerControlSignal)
        control_signal = cast(VisualizerControlSignal, blocker.args[0])
        assert control_signal.key == "animation_tick"
        assert cast(int, control_signal.value) > tick_init

    # the disparity between this and the original benchmark is the time cost of
    # adding the label
    def test_on_tick_handler_benchmark(self, benchmark: BenchmarkFixture, mock_animator: MockAnimatorContext):
        animator = mock_animator.animator
        benchmark(animator.on_tick)

    def test_animator_fps_label_spec(self, qtbot: QtBot, mock_animator: MockAnimatorContext):
        # create two animators.
        # - one without labels
        sa = StatefulAnimator(ups=60, auto_start=False, show_ups_info=False)
        qtbot.addWidget(sa)
        with pytest.raises(AttributeError):
            sa._w_label_ups
        assert sa.on_tick == sa._on_tick

        # - one with labels
        sb = StatefulAnimator(ups=60, auto_start=False, show_ups_info=True)
        qtbot.addWidget(sb)
        sb._w_label_ups
        assert sb.on_tick == sb._on_tick_w_ups_diagnostics

    def test_animator_fps_label_change(self, qtbot: QtBot):
        sa = StatefulAnimator(ups=60, auto_start=False, show_ups_info=True)
        qtbot.addWidget(sa)
        current_text = sa._w_label_ups.text()
        sa.on_tick()
        assert current_text != sa._w_label_ups.text()

    # the disparity between this and the original benchmark is the time cost of
    # adding the label
    def test_on_tick_handler_w_label_benchmark(self, qtbot: QtBot, benchmark: BenchmarkFixture):
        sa = StatefulAnimator(ups=60, show_ups_info=True)
        qtbot.addWidget(sa)
        benchmark(sa.on_tick)
