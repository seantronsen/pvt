from PySide6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QWidget
from .controls import STP, StatefulTrackbar


class VSliderGroup(QFrame):
    """
    Create a vertical slider group GUI component from a list of trackbar
    parameters.
    """

    def __init__(self, tparams: list[STP]) -> None:
        super().__init__()
        self.setLayout(QHBoxLayout())

        # flip the setLayout order on these to get rid of the nuisance static
        # typing warnings.
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)

        for p in tparams:
            tbar = StatefulTrackbar(key=p.key, config=p.config, label=p.label)
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

        # flip the setLayout order on these to get rid of the nuisance static
        # typing warnings.
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)

        for p in tparams:
            tbar = StatefulTrackbar(key=p.key, config=p.config, label=p.label)
            tbar.set_orientation_horizontal()
            self._add_widget(tbar)

    def _add_widget(self, w: QWidget):
        self.layout().addWidget(w)
