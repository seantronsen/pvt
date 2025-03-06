from typing import Any
from PySide6.QtCore import QObject, Qt, Signal, Slot
from PySide6.QtWidgets import QCheckBox, QHBoxLayout, QLabel, QSizePolicy, QSlider, QVBoxLayout, QWidget
from decimal import Decimal
from numpy.typing import NDArray
import numpy as np

# work in progress replace as a base widget.
# idea is to override QWidget to implement some common things
# also will allow for env var which specifies layout boundary display for
# debugging (might need QFrame for that though)
#
# from pvt.identifier import IdManager
# import os
# class QWidgetMod(QWidget):
#
#     def __init__(self, remove_whitespace: bool = True) -> None:
#         super().__init__()
#
#         self.setLayout(QVBoxLayout())
#         if remove_whitespace:
#             self.layout().setContentsMargins(0, 0, 0, 0)
#             self.layout().setSpacing(0)
#
#         if os.getenv("VIEWER_DEBUG") == "1":
#             self.identifier = f"{self.__class__.__name__}-{IdManager().generate_identifier()}".lower()
#             self.identifier_label = QLabel(self.identifier)
#             self.identifier_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
#             self._add_widget(self.identifier_label)
#
#     def _add_widget(self, w: QWidget):
#         self.layout().addWidget(w)


class TrackbarConfig:

    init_index: int
    value_range: NDArray[Any]

    def __init__(
        self,
        start: int | float,
        stop: int | float,
        step: int | float = 1,
        init: int | float | None = None,
    ) -> None:

        # ensure values for optionals
        init_value = init if init is not None else start

        # set / check range
        nrange = stop - start
        assert step > 0, f"error: step must be a positive real or integer number, received {step}"
        assert step <= nrange, f"error: step value exceeds range ({step=} > {nrange=})"
        assert (
            init_value >= start <= stop
        ), f"error: {init_value=} does not exist in the specified range [{start}, {stop}]"

        # calculate number of steps with truncated integer divison
        # decimal types are used to bypass some floating point arithmetic issues
        # with standard python floats: 24.9 / 0.1 = 248.99999999999997 => 248
        # (after truncated integer division)
        nsteps = int(Decimal(str(nrange)) // Decimal(str(step))) + 1
        values = (np.arange(nsteps, dtype=np.intp) * step) + start

        self.value_range = values
        self.init_index = np.argmin(np.abs(values - init_value)).item()

    def value_at(self, index: int):
        return self.value_range[index].item()

    @property
    def initial_value(self):
        return self.value_at(self.init_index)


class TrackbarSignals(QObject):
    index_changed = Signal(int)
    value_changed = Signal(object)


class Trackbar(QSlider):
    """Derivation of QSlider class that allows both integer and float ranges."""

    def __init__(self, config: TrackbarConfig, signals_mediator: TrackbarSignals | None = None):
        """
        Constructor function for the class.

        IMPORTANT: Do note that it is possible to specify parameters that would
        otherwise yield a fractional number of total steps (total tick mark /
        slider settings). For example, a range where start=0.1, stop = 0.5, and
        step=0.3 yields nsteps=2.3 repeating. To ensure the range the user
        expects is not exceeded, truncated integer division is used to discard
        the fractional component of nsteps (i.e. nsteps=2). This ensures
        parameter values remain within the set of values the user expects
        without exceeding that range. The downside being that in these cases,
        the specified end boundary for the range will not be included.

        NOTE: The value range will be an integer type if the user specifies
        integer values for all configuration parameters. If any parameter
        (excluding `init`) is a floating point value, the range will be
        converted to floating point type (precision depends on user machine)
        due to standard numpy calculation type conversion.

        :param start: range start (inclusive)
        :param stop: range end (inclusive)
        :param step: step size (default is int(1))
        :param init: initial active value (important: instantiation fails if
        this value is not an element of the ndarray used to represent the
        range).
        """

        super().__init__()
        self.signals_mediator = signals_mediator if signals_mediator is not None else TrackbarSignals()
        self.revise_range(config)

        # IMPORTANT: No ticks is much faster for trackbar ranges of any size
        # where as trackbars with ticks become obnoxiously slow when more than
        # 100 ticks are involved. Perhaps in the future when can allow the user
        # to specify this or make a choose automatically based on the number of
        # steps, but I'm commenting this out for the sake of consistent
        # behavior and speed.
        # self.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        # setup signal slot connectsions
        self.valueChanged.connect(self._on_value_changed)

    @Slot()
    def set_orientation_horizontal(self):
        super().setOrientation(Qt.Orientation.Horizontal)

    @Slot()
    def set_orientation_vertical(self):
        super().setOrientation(Qt.Orientation.Vertical)

    @Slot(int)
    def _on_value_changed(self, arg: int) -> None:
        self.signals_mediator.index_changed.emit(arg)
        self.signals_mediator.value_changed.emit(self.value())

    @Slot(object)
    def set_index(self, idx: int):
        """
        overriden since the base method doesn't send a signal if the new value
        is the same as the old one (which makes sense, it's just not what we
        need here).

        NOTE: this method is a basic spot fix grafted onto a pvt class. it is
        not complete and will fail if non-integer values are passed in, so it
        doesn't fully coincide with the class. just providing it for now
        """
        if idx == super().value():
            super().setValue(idx)
            self.valueChanged.emit(idx)
        else:
            super().setValue(idx)

    def revise_range(self, config: TrackbarConfig):
        self.config = config
        self.setMaximum(self.config.value_range.size - 1)
        self.setValue(self.config.init_index)

    def value(self) -> int:
        """
        An override of the base class method since the value held by the
        underlying slider refers to an index in the ndarray range held by
        instances of this class. Said index is used to return the target value
        to the caller.
        :return: the value at index referenced by the trackbar position
        """
        return self.config.value_at(super().value())


# todo: update docs for all tbar funcs/methods
class LabeledTrackbar(QWidget):

    def __init__(self, config: TrackbarConfig, label: str, signals_mediator: TrackbarSignals | None = None):
        """
        A stateful trackbar widget which can be used to explore results from a
        range of possible parameter inputs.

        IMPORTANT: Understand there is a limit on the number of events which
        can be emitting within a fixed time interval built-in to the Qt
        library. The developers assert that it exists to ensure the widget/interface
        remains response even when a large change of values has been detected.
        In other words, if you near-instantly move the slider from 0 to 1,000
        when the step size is only one, only a fraction of the events will be
        processed and result in callbacks being triggered to change the UI.

        :param key: key name for the state
        :param label: optional label to appear on the right side of the slider.
            defaults to `key` if not assigned.
        """

        super().__init__()
        self.signals_mediator = signals_mediator if signals_mediator is not None else TrackbarSignals()

        # set up the controls
        self.label_text = label
        self.w_label = QLabel()
        self.w_trackbar = Trackbar(config, signals_mediator=self.signals_mediator)
        self.set_label_value(self.w_trackbar.value())
        self.w_label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)

        # wire up signals/slots
        self.w_trackbar.signals_mediator.value_changed.connect(self._on_trackbar_value_changed)

        # squelch, then set default orientation
        self.set_orientation_horizontal()

    @Slot(object)
    def _on_trackbar_value_changed(self, *_):
        self.set_label_value(self.w_trackbar.value())

    @Slot()
    def set_orientation_horizontal(self):
        self.__set_orientation(is_horizontal=True)

    @Slot()
    def set_orientation_vertical(self):
        self.__set_orientation(is_horizontal=False)

    def set_label_value(self, value: float | int):
        self.w_label.setText(f"{self.label_text}: {value: 06.5f}")

    def __set_orientation(self, is_horizontal: bool):
        layout_old = self.layout()
        if layout_old is not None:
            layout_old.removeWidget(self.w_trackbar)
            layout_old.removeWidget(self.w_label)

            # yeah this looks ridiculous, but it's the simplest way to get the
            # python bindings for the Qt library to actually repaint the window
            # properly when you change the display of subwidgets.
            #
            # yeah it's also true that a QStackedLayout could provide similar
            # functionality, but the previous layout should be deallocated, not
            # retained.
            # TODO: need to link to the stackoverflow forum post which
            # discusses this bullshit line below.
            QWidget().setLayout(layout_old)

        if is_horizontal:
            layout = QHBoxLayout()
            self.w_trackbar.set_orientation_horizontal()
        else:
            layout = QVBoxLayout()
            self.w_trackbar.set_orientation_vertical()

        layout.addWidget(self.w_trackbar)
        layout.addWidget(self.w_label)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)

    def value(self):
        return self.w_trackbar.value()


class ToggleConfig:
    """
    An encapsulation of the toggle control widget config parameters. It's
    defined like this primarily for organization and to simplify any necessary
    future updates.
    """

    def __init__(
        self,
        checked: object | None = None,
        unchecked: object | None = None,
        init_checked: bool = False,
    ) -> None:
        """
        :param checked: value to associate with the "checked" (on) state
        :param unchecked: value to associate with the "unchecked" (off) state
        :param init_checked: flag which determines whether the toggle is
            in the checked state upon creation
        """
        self.value_checked = True if checked is None else checked
        self.value_unchecked = False if unchecked is None else unchecked
        self.__init_checked = init_checked

    @property
    def initial_value(self):
        return self.value_at(self.__init_checked)

    @property
    def initial_state(self):
        return self.__init_checked

    def value_at(self, is_checked: bool):
        return self.value_checked if is_checked else self.value_unchecked


# todo: consider a "generic" signals mediator that applies to all mods.
# result would be fewer definitions, but introduces potential for ambiguities
class ToggleSignals(QObject):
    value_changed = Signal(object)


class Toggle(QCheckBox):

    def __init__(self, values: ToggleConfig | None = None, signals_mediator: ToggleSignals | None = None):
        super().__init__()
        self._signals_mediator = signals_mediator if signals_mediator is not None else ToggleSignals()
        self._values = values if values is not None else ToggleConfig()
        self.setChecked(self._values.initial_state)
        self.stateChanged.connect(self._on_value_changed)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    @Slot(object)
    def _on_value_changed(self, *_):
        self._signals_mediator.value_changed.emit(self.value())

    def value(self):
        return self._values.value_at(self.isChecked())


class LabeledToggle(QWidget):
    """
    TODO: NEEDS DOC UPDATES.
    An adapter of Qt's QCheckBox for use as a labeled checkbox / toggle widget
    in this library.

    :param signals_mediator:
    :param label_text:
    :param w_label:
    :param w_toggle:
    """

    def __init__(
        self,
        label: str,
        values: ToggleConfig | None = None,
        signals_mediator: ToggleSignals | None = None,
    ):

        super().__init__()
        self.signals_mediator = signals_mediator if signals_mediator is not None else ToggleSignals()
        self.label_text = label

        # set up the controls
        self.w_label = QLabel()
        self.w_toggle = Toggle(values=values, signals_mediator=self.signals_mediator)
        self.w_label.setText(self.label_text)
        self.w_label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)

        # wire up signals/slots
        self.signals_mediator.value_changed.connect(self._on_value_changed)

        # set default orientation
        layout = QHBoxLayout()
        layout.addWidget(self.w_toggle)
        layout.addWidget(self.w_label)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)

    @Slot(object)
    def _on_value_changed(self, *_):
        """
        Explicitly written to mirror look and feel of other class definitions
        above. However, the label for this control doesn't need to be updated,
        so this is just a verbose way of stating "squelch".
        """
        pass

    def value(self):
        return self.w_toggle.value()
