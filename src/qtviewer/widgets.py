from typing import List, Optional
from PySide6.QtWidgets import QWidget, QSlider, QLabel, QGridLayout
from PySide6.QtCore import Qt

from qtviewer.state import State


class StatefulWidget(QWidget):

    states: List[State]
    key: str

    def __init__(self, key, init) -> None:
        self.key = key
        self.init = init
        self.states = []
        super().__init__()

    def attach(self, state: State):
        """
        Attach the stateful widget to a parent StatefulPane instance and
        immediately initialize the state. Flush is not called to avoid
        unneccessary extra renders at start up in the event many stateful
        widgets exist in the application. Hence the desire to be "detached".

        :param state: [TODO:description]
        """
        state[self.key] = self.init
        self.states.append(state)

    def on_change(self, *_):
        """
        A method which exists on this base class purely as a reminder to
        implement it on inheriting classes.
        """
        raise NotImplementedError

    def state_update(self, value):
        """
        will fail if not attached to a parent state
        i.e. self.state == None

        :param value: [TODO:description]
        """
        for x in self.states:
            x[self.key] = value

        for x in self.states:
            x.flush()


class LabeledTrackbar(StatefulWidget):
    label: str
    s: QSlider
    t: QLabel

    # instantiated with a detached state for future integration ergonomics
    def __init__(self, label: str, start: int, stop: int, step: int, init: int, key: Optional[str] = None) -> None:
        """
        Instantiate a new stateful trackbar widget in a detached state
        (relative to the parent pane). Due to the functional interface
        requirements of the Qt library, all *value* related parameters must be
        integers for the slider.

        :param label: the label to appear on the right side of the slider.
        :param start: minimum slider value
        :param stop: maximum slider value
        :param step: change in value (delta) for one tick of slider movement.
        :param init: initial slider value / position
        :param key: optional key for the state. if not specified, the label is the key.
        """
        assert init < stop + 1 and init > start - 1
        skey = key if key is not None else label
        super().__init__(skey, init)
        self.label = label
        self.s = QSlider(Qt.Horizontal)  # pyright: ignore
        self.s.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.t = QLabel()
        l, s, t = self.label, self.s, self.t
        s.setFocusPolicy(Qt.StrongFocus)  # pyright: ignore
        s.setMinimum(start)
        s.setMaximum(stop)
        s.setSingleStep(step)
        s.setValue(init)
        t.setText(f"{l}: {s.value()}")
        s.valueChanged.connect(self.on_change)

        layout = QGridLayout()
        self.setLayout(layout)
        layout.addWidget(s, 0, 0)  # left
        layout.addWidget(t, 0, 1)  # far-right (trackbar size pushes it luckily)

    def on_change(self, *_):
        """
        A call back provided to the QSlider instance which is execute on any
        change to the underlying slider state.
        """
        value = self.s.value()
        self.t.setText(f"{self.label}: {value}")
        self.state_update(value)
