from typing import List, Optional
from PySide6.QtWidgets import QCheckBox, QWidget, QSlider, QLabel
from PySide6.QtCore import Qt
from qtviewer.state import State
from pyqtgraph import LayoutWidget


class StatefulWidget(LayoutWidget):
    """
    Instantiate a new stateful widget in a detached state (relative to the
    parent pane). Due to common functional interface requirements of the Qt
    library, overrides for the deriving class callback methods (`on_change` at
    the time of writing), are to return integer values for the sake of
    simplicity. If a different data type is needed, perform the translation in
    the top level user specified callbacks. For an example, the returned
    integer value could be used to index into a string array if a particular
    string value is needed.

    IMPORTANT: This is a base class for deriving widgets used in this library.

    NOTE FROM THE AUTHOR: I have no intention of supporting form components
    such as text input fields at this time. The purpose of this library is to
    simplify quick and dirty data visualization and algorithmic tuning. Text
    inputs have no place here in that regard.
    """

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


class ParameterToggle(StatefulWidget):
    cb: QCheckBox

    # instantiated with a detached state for future integration ergonomics
    def __init__(self, label: str, init: bool, key: Optional[str] = None) -> None:
        """
        Instantiate a new stateful checkbox / toggle widget in a detached state
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

        # fill in the optionals
        skey = key if key is not None else label
        super().__init__(skey, init)

        # set up the control
        self.s = QCheckBox(label)
        self.s.setFocusPolicy(Qt.StrongFocus)  # pyright: ignore
        self.s.setChecked(init)
        self.s.stateChanged.connect(self.on_change)
        self.addWidget(self.s)

    def on_change(self, *_):
        """
        A call back provided to the QSlider instance which is execute on any
        change to the underlying slider state.
        """
        value = int(self.s.isChecked())
        self.state_update(value)


class ParameterTrackbar(StatefulWidget):
    label: str
    s: QSlider
    t: QLabel

    # instantiated with a detached state for future integration ergonomics
    def __init__(
        self, label: str, start: int, stop: int, step: int, init: Optional[int] = None, key: Optional[str] = None
    ) -> None:
        """
        Instantiate a new stateful trackbar widget to visualize the results of
        a range of possible parameter inputs.

        IMPORTANT: Understand there is a limit on the number of events which
        can be emitting within a fixed time interval built-in to the Qt
        library. The developers assert that it exists to ensure the widget/interface
        remains response even when a large change of values has been detected.
        In other words, if you near-instantly move the slider from 0 to 1,000
        when the step size is only one, only a fraction of the events will be
        processed and result in callbacks being triggered to change the UI.

        :param label: the label to appear on the right side of the slider.
        :param start: minimum slider value
        :param stop: maximum slider value
        :param step: change in value (delta) for one tick of slider movement.
        :param init: initial slider value / position
        :param key: optional key for the state. if not specified, the label is the key.
        """

        # fill in the optionals
        init = init if init is not None else start
        skey = key if key is not None else label
        assert init <= stop and init >= start
        super().__init__(skey, init)

        # set up the control
        self.label = label
        self.s = QSlider(Qt.Horizontal)  # pyright: ignore
        self.s.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.t = QLabel()
        l, s, t = self.label, self.s, self.t
        s.setFocusPolicy(Qt.StrongFocus)  # pyright: ignore
        s.setRange(start, stop)
        s.setSingleStep(step)
        s.setValue(init)
        t.setText(f"{l}: {s.value()}")
        s.valueChanged.connect(self.on_change)

        self.addWidget(s, 0, 0)  # left
        self.addWidget(t, 0, 1)  # far-right (trackbar size pushes it luckily)

    def on_change(self, *_):
        """
        A call back provided to the QSlider instance which is execute on any
        change to the underlying slider state.
        """
        value = self.s.value()
        self.t.setText(f"{self.label}: {value}")
        self.state_update(value)
