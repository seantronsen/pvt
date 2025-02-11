from dataclasses import dataclass
from PySide6.QtCore import Signal, Slot
from PySide6.QtWidgets import QVBoxLayout, QWidget
from abc import abstractmethod
from .pvt_experimental.decorators import perflog
from .pvt_experimental.identifier import IdManager
from .pvt_experimental.qtmods import LabeledTrackbar, TrackbarRange
from .pvt_experimental.state import VisualizerControlSignal

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
    _key: str
    _initial_value: object

    def __init__(self, key: str, initial_value: object) -> None:
        """
        :param key: key name for the state. must abide by python variable
            naming requirements.
        :param init [Any]: an initial value
        """
        super().__init__()
        self._key, self._initial_value = key, initial_value
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)
        self.identifier = f"{self.__class__.__name__}-{IdManager().generate_identifier()}".lower()

    def _add_widget(self, w: QWidget):
        self.layout().addWidget(w)

    @Slot()
    @perflog(event="full-interaction")
    def _on_change(self, *_, **__):
        self.on_control_signal_changed.emit(self.query_control_signal())

    def query_control_signal(self):
        return VisualizerControlSignal(key=self._key, value=self.value())

    @abstractmethod
    def value(self) -> object:
        raise NotImplementedError


@dataclass
class STP:
    """Class representation for `StatefulTrackbar` parameters"""

    tb_range: TrackbarRange
    key: str
    label: str | None = None

    def __post_init__(self):
        if not self.key:
            raise ValueError("key cannot be empty")


class StatefulTrackbar(StatefulControl):

    def __init__(self, tb_range: TrackbarRange, key: str, label: str | None = None) -> None:
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

    @Slot()
    def set_orientation_horizontal(self):
        self._labeled_trackbar.set_orientation_horizontal()

    @Slot()
    def set_orientation_vertical(self):
        self._labeled_trackbar.set_orientation_vertical()

    def value(self):
        return self._labeled_trackbar.value()
