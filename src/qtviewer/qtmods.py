from PySide6.QtCore import Qt
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QSlider
import numpy as np
from typing import Optional, Union


class Trackbar(QSlider):
    """
    A derivation of Qt's QSlider class that allows the slider position to
    change according to the step size, even when dragged. Why this is not
    provided as an "in the box" feature for anything except keyboard arrow keys
    is unknown, especially considering how simple the solution is.

    NEW:
    Instances of this class are now able to work with floating point or integer
    numbers. Implementation instantiates an ndarray to hold the specified range
    with values returned by using the tick position to index into the range.
    """

    def __init__(
        self,
        start: Union[int, float],
        stop: Union[int, float],
        step: Union[int, float] = 1,
        init: Optional[Union[int, float]] = None,
    ):
        assert step < stop, f"error: step value exceeds range ({step=} > {stop=})"
        init_value = init if init is not None else start
        min_value, max_value = start, stop + step  # np arange excludes final value by default
        values = np.arange(start=min_value, stop=max_value, step=step)
        init_value = np.array(init_value, dtype=values.dtype).item()
        init_index = np.where(np.isclose(values, init_value))[0]
        assert init_index.size != 0, f"error: {init_value=} does not exist in the specified range {values}"
        init_index = init_index.item()
        super().__init__(Qt.Horizontal)  # pyright: ignore
        self.setFocusPolicy(Qt.StrongFocus)  # pyright: ignore
        self.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.setRange(0, values.size - 1)
        self.setSingleStep(1)
        self.setPageStep(1)
        self.value_range = values
        self.setValue(init_index)

    def value(self) -> int:
        """
        override to use ndarray range instead.
        :return: the value at index referenced by the trackbar position
        """
        index = super().value()
        return self.value_range[index].item()

    def mouseMoveEvent(self, ev: QMouseEvent) -> None:
        width = self.width()

        # determine position
        new_position = np.clip(ev.position().x(), a_min=0, a_max=width)

        # calculate prereqs to determine nearest tick
        total_steps = self.value_range.size
        step_width_px = width / total_steps

        # calculate nearest tick and assign as widget value.
        self.setValue(np.round(new_position / step_width_px).astype(np.intp))
        return ev.accept()
