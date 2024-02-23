from typing import Optional
from PySide6.QtWidgets import QWidget, QSlider, QLabel, QGridLayout
from PySide6.QtCore import Qt
from qtviewer.state import State


class StatefulWidget(QWidget):

    state: Optional[State]
    key: str

    def __init__(self, key, init) -> None:
        self.key = key
        self.init = init
        self.state = None
        super().__init__()

    def attach(self, state: State):
        self.state = state
        self.state[self.key] = self.init

    def on_change(self, *_):
        """
        exists purely as a reminder to override this yourself.

        :raises [TODO:name]: [TODO:description]
        """
        raise NotImplementedError

    def state_update(self, value):
        """
        will fail if not attached to a parent state
        i.e. self.state == None

        :param value [TODO:type]: [TODO:description]
        """
        self.state[self.key] = value  # pyright: ignore
        self.state.flush()  # pyright: ignore


class LabeledTrackbar(StatefulWidget):
    label: str
    s: QSlider
    t: QLabel

    # instantiated with a detached state for future integration ergonomics
    def __init__(self, label: str, start: int, stop: int, step: int, init: int, key: Optional[str] = None) -> None:
        assert init < stop + 1 and init > start - 1
        skey = key if key is not None else label
        super().__init__(skey, init)
        self.label = label
        self.s = QSlider(Qt.Horizontal)  # pyright: ignore
        self.t = QLabel()
        l, s, t = self.label, self.s, self.t
        s.setMinimum(start)
        s.setMaximum(stop)
        s.setSingleStep(step)
        t.setText(f"{l}: {s.value()}")
        s.valueChanged.connect(self.on_change)

        layout = QGridLayout()
        self.setLayout(layout)
        layout.addWidget(s, 0, 0)  # left
        layout.addWidget(t, 0, 6)  # far-right

    def on_change(self, *_):
        value = self.s.value()
        self.t.setText(f"{self.label}: {value}")
        self.state_update(value)
