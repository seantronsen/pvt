from PySide6.QtCore import Qt
from PySide6.QtWidgets import QSlider
import numpy as np
from typing import Optional, Union
from decimal import Decimal


class Trackbar(QSlider):
    """
    A derivation of Qt's QSlider class that allows use of both integer and
    floating point ranges.
    """

    def __init__(
        self,
        start: Union[int, float],
        stop: Union[int, float],
        step: Union[int, float] = 1,
        init: Optional[Union[int, float]] = None,
    ):
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
        # set unset optionals
        init_value = init if init is not None else start

        # set / check range
        nrange = stop - start
        assert step > 0, f"error: step must be a positive real or integer number, received {step}"
        assert step < nrange, f"error: step value exceeds range ({step=} > {nrange=})"

        # calculate number of steps with truncated integer divison
        # decimal types are used to bypass some floating point arithmetic issues
        # with standard python floats: 24.9 / 0.1 = 248.99999999999997 => 248
        # (after truncated integer division)
        nsteps = int(Decimal(str(nrange)) // Decimal(str(step))) + 1
        values = np.arange(nsteps, dtype=np.intp) * step
        values = values + start

        # ensure initial value is a valid setting
        init_index = np.where(np.isclose(values, init_value))[0]
        assert init_index.size != 0, f"error: {init_value=} does not exist in the specified range {values}"

        # initialize
        super().__init__(Qt.Horizontal)  # pyright: ignore
        self.setFocusPolicy(Qt.StrongFocus)  # pyright: ignore
        self.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.setMaximum(values.size - 1)
        self.value_range = values
        self.setValue(init_index.item())

    def value(self) -> int:
        """
        An override of the base class method since the value held by the
        underlying slider refers to an index in the ndarray range held by
        instances of this class. Said index is used to return the target value
        to the caller.
        :return: the value at index referenced by the trackbar position
        """
        return self.value_range[super().value()].item()
