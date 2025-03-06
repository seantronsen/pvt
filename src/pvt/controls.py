from PySide6.QtCore import QTimer, Signal, Slot
from PySide6.QtWidgets import QGridLayout, QPushButton, QVBoxLayout, QWidget
from abc import abstractmethod
from dataclasses import dataclass
from pvt.decorators import perflog
from pvt.identifier import IdManager
from pvt.qtmods import LabeledToggle, LabeledTrackbar, ToggleConfig, TrackbarConfig
from pvt.state import VisualizerControlSignal
from typing import cast
import numpy as np


class StatefulControl(QWidget):
    """
    The base class for this library's control type widgets which encapsulates
    logic common to all widgets of this type.

    "Stateful" controls are widgets the user can interact with to change the
    state of the application. Specifically, each control widget represents a
    set of values for some parameter and allows the user to explore changes
    through visualizations within data displays which subscribe to changes in
    that parameter (see `context.py` and the demo for more details).

    IMPORTANT: Stateful control widget are instantiated in a detached state,
    meaning they will not affect existing data displays until wired into a
    VisualizerContext.
    """

    on_control_signal_changed = Signal(VisualizerControlSignal)
    key: str
    _initial_value: object

    def __init__(self, key: str, initial_value: object) -> None:
        """
        :param key: key name for the state. must abide by python variable
            naming requirements.
        :param init: an initial value
        """
        super().__init__()
        self.key, self._initial_value = key, initial_value
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)
        self.identifier = f"{self.__class__.__name__}-{IdManager().generate_identifier()}".lower()

    def _add_widget(self, w: QWidget):
        self.layout().addWidget(w)

    @Slot()
    @perflog(event="full-interaction")
    def _on_change(self, *_, **__):
        self.on_control_signal_changed.emit(self.query_control_signal())

    def query_control_signal(self):
        return VisualizerControlSignal(key=self.key, value=self.value())

    @abstractmethod
    def value(self) -> object:
        raise NotImplementedError


@dataclass
class STP:
    """
    Class representation for `StatefulTrackbar` parameters. It exists to
    simplify the creation of a large group of sliders (see slider groups in the
    `layouts.py` module.
    """

    config: TrackbarConfig
    key: str
    label: str | None = None

    def __post_init__(self):
        if not self.key:
            raise ValueError("key cannot be empty")


class StatefulTrackbar(StatefulControl):
    """
    A stateful trackbar widget which can be used to explore results from a
    range of possible parameter inputs.

    IMPORTANT: Understand there is a limit on the number of events which can be
    emitting within a fixed time interval built-in to the Qt library. The
    developers assert that it exists to ensure the widget/interface remains
    response even when a large change of values has been detected. In other
    words, if you near-instantly move the slider from 0 to 1,000 when the step
    size is only one, only a fraction of the events will be processed and
    result in callbacks being triggered to change the UI.
    """

    def __init__(self, key: str, config: TrackbarConfig, label: str | None = None) -> None:
        """
        :param key: key name for the state
        :param config: trackbar range parameters
        :param label: optional label to appear on the right side of the slider
            defaults to `key` if not assigned.
        """
        super().__init__(key, config.initial_value)
        self._labeled_trackbar = LabeledTrackbar(config=config, label=label if label is not None else key)
        self._labeled_trackbar.signals_mediator.value_changed.connect(self._on_change)
        self._add_widget(self._labeled_trackbar)

    def value(self):
        return self._labeled_trackbar.value()

    @Slot()
    def set_orientation_horizontal(self):
        self._labeled_trackbar.set_orientation_horizontal()

    @Slot()
    def set_orientation_vertical(self):
        self._labeled_trackbar.set_orientation_vertical()


class StatefulToggle(StatefulControl):
    """
    A stateful checkbox / toggle widget which can be used to explore the results of "binary"
    parameter changes.

    The implementation is defined agnostically such that both the "on" and
    "off" states can be assigned arbitrary values. **However**, for the sake of
    performance it's recommended to use simple objects or primitives (not giant
    ndarray instances).
    """

    def __init__(self, key: str, config: ToggleConfig | None = None, label: str | None = None) -> None:
        """
        :param key: a name to associate with the state value
        :param config: control configuration
        :param label: optional label to appear on the right side of the toggle.
            defaults to `key` if not assigned.
        """

        _values = config if config is not None else ToggleConfig()
        super().__init__(key, _values.initial_value)
        self._labeled_toggle = LabeledToggle(label=label if label is not None else key, values=_values)
        self._labeled_toggle.signals_mediator.value_changed.connect(self._on_change)

    def value(self):
        return self._labeled_toggle.value()


class StatefulAnimator(StatefulControl):
    """
    Integrate a stateful animator into a visualizer context to enable timed
    updates. The animator supplies an extra parameter, animation_tick, to your
    custom callbacks. You can use animation_tick to drive behaviors that change
    over time—such as indexing into a series of frames to create a movie or
    advancing simulation time steps in dynamic visualizations.

    This feature is opt-in. Your callback must actively use the animation_tick
    parameter to benefit from time-based updates. Otherwise, the visualizer will
    simply continue displaying the previous frame’s data (unless your callback
    includes other dynamic behaviors).
    """

    def __init__(self, ups: float, auto_start: bool = False) -> None:
        """
        :param ups: desired maximum number of updates per second (animation
            ticks per second)
        :param auto_start: flag which indicates whether the animation should
            begin immediately upon start up (True) or wait for the user to
            press the "play" button (False)
        """
        assert ups > 0

        self._animation_tick = np.uint64(0)
        self._tick_time = int(round(1e3 / ups))

        self._timer = QTimer()
        self._timer.timeout.connect(self.on_tick)

        super().__init__(key="animation_tick", initial_value=self._animation_tick)

        # todo: link to comment
        # a janky way to get rid of a previous layout. there's a comment
        # about why this is like this somewhere in this library. I think it's
        # under the qtmods.py module.
        if self.layout() is not None:
            QWidget().setLayout(self.layout())  # pyright: ignore

        super().setLayout(QGridLayout())

        self.b_reset = QPushButton("RESET")
        self.b_one_forward = QPushButton(">")
        self.b_one_reverse = QPushButton("<")

        self.b_reset.clicked.connect(self.reset)
        self.b_one_forward.clicked.connect(self.forward)
        self.b_one_reverse.clicked.connect(self.reverse)

        self.b_toggle = QPushButton("PLAY")
        self.b_toggle.setCheckable(True)
        self.b_toggle.setChecked(auto_start)
        self.b_toggle.clicked.connect(self.pause_play)

        self.setLayout(QGridLayout())
        self._add_widget(self.b_reset)
        self._add_widget(self.b_one_reverse)
        self._add_widget(self.b_toggle)
        self._add_widget(self.b_one_forward)

        if auto_start:
            self._timer.start(self._tick_time)

    def value(self) -> object:
        return self._animation_tick

    def on_tick(self):
        self._animation_tick += np.uintp(1)
        self._on_change()

    def forward(self):
        self._animation_tick += 1
        self._on_change()

    def reverse(self):
        self._animation_tick -= 1
        self._on_change()

    def reset(self):
        self._animation_tick = np.uintp(0)
        self._on_change()

    def pause_play(self):
        if self._timer.isActive():
            self._timer.stop()
        else:
            self._timer.start(self._tick_time)

    def _add_widget(self, w: QWidget):
        layout = cast(QGridLayout, self.layout())
        layout.addWidget(w, 1, layout.columnCount() + 1, 1, 1)
