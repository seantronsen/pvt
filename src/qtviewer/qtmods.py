from PySide6.QtCore import Qt
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QSlider
import numpy as np


class TrackbarH(QSlider):
    """
    A derivation of Qt's QSlider class that allows the slider position to
    change according to the step size, even when dragged. Why this is not
    provided as an "in the box" feature for anything except keyboard arrow keys
    is unknown.
    """

    _stepSize: int = 1

    def __init__(self):
        super().__init__(Qt.Horizontal)  # pyright: ignore
        self.setFocusPolicy(Qt.StrongFocus)  # pyright: ignore
        self.setTickPosition(QSlider.TickPosition.TicksBelow)

    def mousePressEvent(self, ev: QMouseEvent) -> None:

        # capture click position
        self._initialClickPosition = ev.position().x()
        ev.accept()

    def mouseMoveEvent(self, ev: QMouseEvent) -> None:
        # change to set the new value based off the current position and discard the entire notion of tracking the position
        # calc step => bounded pos / (width / num steps)
        # round to closest
        # calculate the position delta
        bound = lambda value: min(max(value, 0), self.width())
        # step_total = (self.maximum() / self._stepSize) - 1
        step_total = (self.maximum() / self._stepSize) 
        step_distance = np.round(self.width() / step_total)
        new_position = bound(ev.position().x())
        diff = new_position - self._initialClickPosition

        # calculate step delta
        steps = np.round(diff / step_distance)
        print(f"{ev.position().x()=} {new_position=} {diff=} {steps=} {step_total=} {step_distance=}")
        if steps:
            next_position = bound(self._initialClickPosition + (steps * step_distance))
            self.setValue(self.value() + int(steps * self._stepSize))
            self._initialClickPosition = int(next_position)
        return ev.accept()

    def setStepSizeForAllEvents(self, stepSize):
        self.setSingleStep(stepSize)
        self.setPageStep(stepSize)
        self._stepSize = stepSize
