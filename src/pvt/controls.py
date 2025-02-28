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

# todo: all stateful composition based controls should not have padding or margin spacing
# todo: consider a "widget base" since both controls and displays share some arbitrary bullshit
# and it could be useful for controls to be visually identifable too.


class StatefulControl(QWidget):
    """
    "Stateful" controls are widgets the user can interact with to change the
    state of the application. Specifically, each control widget represents a
    set of values for some parameter and allows the user to explore changes to
    data displays which relate to changes in that parameter.

    IMPORTANT: Stateful control widget are instantiated in a detached state,
    meaning they will not affect existing data displays until linked to a
    VisualizerContext.
    """

    on_control_signal_changed = Signal(VisualizerControlSignal)
    key: str
    _initial_value: object

    def __init__(self, key: str, initial_value: object) -> None:
        """
        :param key: key name for the state. must abide by python variable
            naming requirements.
        :param init [Any]: an initial value
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
    """Class representation for `StatefulTrackbar` parameters"""

    tb_range: TrackbarConfig
    key: str
    label: str | None = None

    def __post_init__(self):
        if not self.key:
            raise ValueError("key cannot be empty")


class StatefulTrackbar(StatefulControl):

    def __init__(self, tb_range: TrackbarConfig, key: str, label: str | None = None) -> None:
        """
        Instantiate a new stateful trackbar widget to visualize the results of
        a range of possible parameter inputs.

        IMPORTANT: Understand there is a limit on the number of events which
        can be emitting within a fixed time interval built-in to the Qt
        library. The developers assert that it exists to ensure the
        widget/interface remains responsive as the frequency of changes
        increases. In other words, if you near-instantly move the slider from 0
        to 1,000 when the step size is only one, only a fraction of the events
        will be processed and result in callbacks being triggered to change the
        UI.

        :param key: key name for the state
        :param tb_range: trackbar range parameters
        :param label: optional label to appear on the right side of the slider
            defaults to `key` if not assigned.
        """
        super().__init__(key, tb_range.initial_value)
        self._labeled_trackbar = LabeledTrackbar(tb_range=tb_range, label=label if label is not None else key)
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
    Instantiate a new stateful checkbox / toggle widget to visualize the
    result of a "binary" parameter input (two options only).
    """

    def __init__(self, key: str, values: ToggleConfig | None = None, label: str | None = None) -> None:
        """
        :param key: key name for the state
        :param values: toggle parameters and values associated with each state
        :param label: optional label to appear on the right side of the toggle,
            defaults to `key` if not assigned.
        """

        _values = values if values is not None else ToggleConfig()
        super().__init__(key, _values.initial_value)
        self._labeled_toggle = LabeledToggle(label=label if label is not None else key, values=_values)
        self._labeled_toggle.signals_mediator.value_changed.connect(self._on_change)

    def value(self):
        return self._labeled_toggle.value()


"""
the idea of the animator is one global to the closest visualizer context in the
hierarchy. meaning, if the user specifies an animator, all displays with
callbacks known to that visualizer context will have their callbacks triggered
for every time tick.

such is why it will be important to enable opt-in caching, especially if the
user has displays which aren't meant to be animated.

to have more than one animator where each modifies a unique set of displays, a
new visualizer context will need to own all displays and controls unique to
that animation.

note: things that need to be set up in the future
- parameter caching for callbacks. if the callback must execute with the same
  parameters and cache is specified, then don't update, for this, we can likely
  get away with caching the parameters yielded from state.

- implementing some sort of way to share state updates between contexts. what
  if the user wants a control to mutate multiple contexts? this should be as
  simple as just setting up a context's ability to subscribe to signal
  emissions for it's state.


"""


class StatefulAnimator(StatefulControl):
    """
    Integrate a stateful animator into your visualizer context to enable time-based
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
        """
        Exists to provide a timed update feature for animation / sequence data
        where new frames should be delivered at the specified interval.
        """
        self._animation_tick += np.uintp(1)
        self._on_change()

    def forward(self, *a, **k):
        self._animation_tick += 1
        self._on_change()

    def reverse(self, *a, **k):
        self._animation_tick -= 1
        self._on_change()

    def reset(self, *a, **k):
        self._animation_tick = np.uintp(0)
        self._on_change()

    def pause_play(self, *a, **k):
        if self._timer.isActive():
            self._timer.stop()
        else:
            self._timer.start(self._tick_time)

    # todo: if we ever extend the base class, this needs to change to
    # layout.addLayout relative to the original base class layout.
    def _add_widget(self, w: QWidget):
        layout = cast(QGridLayout, self.layout())
        layout.addWidget(w, 1, layout.columnCount() + 1, 1, 1)
