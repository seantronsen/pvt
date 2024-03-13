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
        min_setting, max_setting, width = self.minimum(), self.maximum(), self.width()
        boundary_truncation = lambda value: min(max(value, 0), width)

        # determine position
        new_position = boundary_truncation(ev.position().x())

        # calculate prereqs to determine nearest tick
        total_steps = (max_setting - min_setting) / self._stepSize  # n steps => n + 1 settings
        step_width_px = width / total_steps

        # calculate nearest tick and assign as widget value.
        self.setValue(np.round(new_position / step_width_px).astype(np.intp) * self._stepSize + min_setting)
        return ev.accept()

    def setStepSizeForAllEvents(self, stepSize):
        self.setSingleStep(stepSize)
        self.setPageStep(stepSize)
        self._stepSize = stepSize
