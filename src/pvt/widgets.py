from typing import List, Optional, Union
from PySide6.QtWidgets import QCheckBox, QLabel
from PySide6.QtCore import Qt
from pvt.qtmods import Trackbar
from pvt.state import State
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

    NOTE FROM THE AUTHOR: I have no intention of supporting form components
    like text input fields at this time. The purpose of this library is to
    simplify quick and dirty data visualization and algorithmic tuning.
    """

    states: List[State]
    key: str

    def __init__(self, key, init, **kwargs) -> None:
        """
        :param key: key name for the state. must abide by python variable
        naming requirements.
        :param init [Any]: an initial value
        """
        self.key = key
        self.init = init
        self.states = []
        super().__init__(**kwargs)

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
        A callback method to be defined on deriving classes and passed to the
        `onChange` handler of the wrapped QWidget control. Members of user land
        do not need to be concerned with this details.

        Implementors must ensure to pass the resulting value to
        `self.state_update` in order for the callback chain to function
        properly.
        """
        raise NotImplementedError

    def state_update(self, value):
        """
        :param value: [TODO:description]
        :raises KeyError: fails when not attached to state
        """
        for x in self.states:
            x[self.key] = value

        for x in self.states:
            x.flush()


class ParameterToggle(StatefulWidget):
    s: QCheckBox

    def __init__(self, key: str, init: bool, label: Optional[str] = None) -> None:
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
        label = label if label is not None else key
        super().__init__(key, init)

        # set up the control
        self.s = QCheckBox(label)
        self.s.setFocusPolicy(Qt.StrongFocus)  # pyright: ignore
        self.s.setChecked(init)
        self.s.stateChanged.connect(self.on_change)
        self.addWidget(self.s)

    def on_change(self, *_):
        value = int(self.s.isChecked())
        self.state_update(value)


class ParameterTrackbar(StatefulWidget):
    label: str
    s: Trackbar
    t: QLabel

    def __init__(
        self,
        key: str,
        start: Union[int, float],
        stop: Union[int, float],
        step: Union[int, float] = 1,
        init: Optional[Union[int, float]] = None,
        label: Optional[str] = None,
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

        :param key: key name for the state
        :param start: minimum slider value
        :param stop: maximum slider value
        :param step: change in value (delta) for one tick of slider movement
        :param init: initial slider value / position
        :param label: optional label to appear on the right side of the slider
        defaults to `key` if not assigned.
        """

        # fill in the optionals
        init = init if init is not None else start
        label = label if label is not None else key
        # assert init <= stop and init >= start
        super().__init__(key, init)

        # set up the control
        self.label = label
        self.s = Trackbar(start, stop, step, init)
        self.t = QLabel()
        self.set_label_value()
        self.s.valueChanged.connect(self.on_change)

        self.addWidget(self.s, 0, 0)
        self.addWidget(self.t, 0, 1)

    def set_label_value(self, value: Optional[Union[float, int]] = None):
        v = value if value is not None else self.s.value()
        self.t.setText(f"{self.label}: {v: g}")

    def on_change(self, *_):
        value = self.s.value()
        self.set_label_value(value)
        self.state_update(value)
