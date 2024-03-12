from PySide6.QtCore import Qt
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QSlider
import numpy as np


class TrackbarH(QSlider):
    """
    A derivation of Qt's QSlider class that allows the slider position to
    change according to the step size, even when dragged. Why this is not
    provided as an "in the box" feature for anything except keyboard arrow keys
    is unknown, especially considering how simple the solution is.
    """

    _stepSize: int = 1

    def __init__(self):
        super().__init__(Qt.Horizontal)  # pyright: ignore
        self.setFocusPolicy(Qt.StrongFocus)  # pyright: ignore
        self.setTickPosition(QSlider.TickPosition.TicksBelow)

    def mouseMoveEvent(self, ev: QMouseEvent) -> None:
        boundary_truncation = lambda value: min(max(value, 0), self.width())

        # determine position
        new_position = boundary_truncation(ev.position().x())

        # calculate prereqs to determine nearest tick
        max_setting = self.maximum()
        total_steps = max_setting / self._stepSize  # n steps => n + 1 settings
        step_width_px = self.width() / total_steps

        # calculate nearest tick and assign as widget value.
        # min with maxval to prevent undefined behaviors
        new_value = min(np.round(new_position / step_width_px) * self._stepSize, max_setting)
        self.setValue(int(new_value))
        return ev.accept()

    def setStepSizeForAllEvents(self, stepSize):
        self.setSingleStep(stepSize)
        self.setPageStep(stepSize)
        self._stepSize = stepSize
