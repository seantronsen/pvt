from PySide6.QtCore import QObject, Signal, Slot
from dataclasses import dataclass


@dataclass
class VisualizerControlSignal:
    key: str
    value: object

    def __post_init__(self):
        if not self.key:
            raise ValueError("key cannot be empty")


class VisualizerState(QObject):
    """
    An abstract collection of state created using simple python dictionaries.
    Changes in state trigger the emission of a Qt signal which passes the
    current state to callbacks defined by subscribers. 

    Links the behaviors between control widgets and data display panes.
    """

    state_changed = Signal(dict)

    def __init__(self) -> None:
        super().__init__()
        self.__storage: dict[str, object] = dict()

    def __getitem__(self, key: str):
        return self.__storage.get(key)

    def __setitem__(self, key: str, value: object):
        self.__storage[key] = value

    @Slot(VisualizerControlSignal)
    def modify_state(self, arg: VisualizerControlSignal):
        self.__storage[arg.key] = arg.value
        self.state_changed.emit(self.__storage)

    def flush(self):
        self.state_changed.emit(self.__storage)
