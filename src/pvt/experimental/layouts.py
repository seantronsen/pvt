from PySide6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QWidget
from pvt_experimental.controls import STP, StatefulTrackbar


class VSliderGroup(QFrame):
    """
    Create a vertical slider group GUI component from a list of trackbar
    parameters.
    """

    def __init__(self, tparams: list[STP]) -> None:
        super().__init__()
        self.setLayout(QHBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)

        for p in tparams:
            tbar = StatefulTrackbar(p.tb_range, p.key, p.label)
            tbar.set_orientation_vertical()
            self._add_widget(tbar)

    def _add_widget(self, w: QWidget):
        self.layout().addWidget(w)


class HSliderGroup(QFrame):
    """
    Create a horizontal slider group GUI component from a list of trackbar
    parameters.
    """

    def __init__(self, tparams: list[STP]) -> None:
        super().__init__()
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)

        for p in tparams:
            tbar = StatefulTrackbar(p.tb_range, p.key, p.label)
            tbar.set_orientation_horizontal()
            self._add_widget(tbar)

    def _add_widget(self, w: QWidget):
        self.layout().addWidget(w)
