from dataclasses import dataclass
from PySide6.QtCore import Signal, Slot
from PySide6.QtWidgets import QVBoxLayout, QWidget
from abc import abstractmethod
from pvt.decorators import perflog
from pvt.identifier import IdManager
from pvt.qtmods import LabeledToggle, LabeledTrackbar, ToggleConfig, TrackbarConfig
from pvt.state import VisualizerControlSignal

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



from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QPushButton
from pyqtgraph import LayoutWidget
from pvt.displays import StatefulDisplay
import numpy as np


class Animator:
    animation_content: StatefulDisplay
    timer: QTimer
    animation_tick: np.uintp

    def __init__(self, contents: StatefulDisplay, fps: float) -> None:
        assert not fps <= 0
        super().__init__()
        self.animation_content = contents
        self.animation_content.pane_state.onUpdate = self.update
        self.animation_tick = np.uint64(0)
        self.timer = QTimer(parent=self.animation_content)
        self.timer.timeout.connect(self.on_tick)
        self.tick_time = int(round(1e3 / fps))
        self.timer.start(self.tick_time)

    def __getattr__(self, name):
        return getattr(self.animation_content, name)

    def content_flush(self):
        self.animation_content.force_flush()

    def on_tick(self):
        """
        Exists to provide a timed update feature for animation / sequence data
        where new frames should be delivered at the specified interval.
        """
        self.animation_tick += np.uintp(1)
        self.content_flush()

    def update(self, **kwargs):
        """
        This function is the callback provided to the State instance and is
        executed on each state change. The user specified callback is executed
        by this callback. If you wish to exist in user land, don't worry about
        anything other than the one callback you're required to define.
        """

        self.animation_content.update(animation_tick=int(self.animation_tick), **kwargs)

    def is_running(self):
        return self.timer.isActive()

    def pause_toggle(self, *a, **k):
        if self.is_running():
            self.timer.stop()
        else:
            self.timer.start(self.tick_time)

    def forward_one_step(self, *a, **k):
        self.animation_tick += 1
        self.content_flush()

    def reverse_one_step(self, *a, **k):
        self.animation_tick -= 1
        self.content_flush()

    def reset(self, *a, **k):
        self.animation_tick = np.uintp(0)
        self.content_flush()


class AnimatorControlBar(LayoutWidget):

    animator: Animator

    def __init__(self, animator: Animator):
        super().__init__()
        self.animator = animator

        self.b_reset = QPushButton("RESET")
        self.b_one_forward = QPushButton(">")
        self.b_one_reverse = QPushButton("<")

        self.b_reset.clicked.connect(self.animator.reset)
        self.b_one_forward.clicked.connect(self.animator.forward_one_step)
        self.b_one_reverse.clicked.connect(self.animator.reverse_one_step)

        self.b_toggle = QPushButton("PLAY")
        self.b_toggle.setCheckable(True)
        self.b_toggle.setChecked(self.animator.is_running())
        self.b_toggle.clicked.connect(self.animator.pause_toggle)

        self.addWidget(self.b_reset, row=0, col=0)
        self.addWidget(self.b_one_reverse, row=0, col=1)
        self.addWidget(self.b_toggle, row=0, col=2)
        self.addWidget(self.b_one_forward, row=0, col=3)

