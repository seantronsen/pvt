from PySide6.QtCore import QObject, Signal, Slot
from dataclasses import dataclass


@dataclass
class VisualizerControlSignal:
    """
    A generic container class which encapsulates the state update information
    emit from a control widget (a producer). Instances of this class are sent
    to the visualizer state held by the nearest parent context in the
    hierarchy. The state instance decides whether it's necessary to notify any
    display widgets about the update.

    :param key: key name assigned to the control widget which emitted the
        signal. If the callback the user provides to a display widget has a
        parameter which shares the same name as this key, it will automatically
        receive the updated value when the control's state changes (a slider
        slides).
    :param value: the new state value
    """

    key: str
    value: object

    def __post_init__(self):
        if not self.key:
            raise ValueError("key cannot be empty")


class VisualizerState(QObject):
    """
    An collection of state implemented using python dictionaries. Subscribers
    are automatically notified of any changes in state. 

    Links the state of the control widgets to the data displays. 
    """

    state_changed = Signal(dict)

    def __init__(self) -> None:
        super().__init__()
        self._storage: dict[str, object] = dict()

    @Slot(VisualizerControlSignal)
    def modify_state(self, arg: VisualizerControlSignal):
        self._storage[arg.key] = arg.value
        self.state_changed.emit(self._storage)

    def flush(self):
        self.state_changed.emit(self._storage)
