import signal
import sys
from typing import List
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QWidget, QApplication
from pyqtgraph import LayoutWidget
from qtviewer.panels import StatefulPane
from qtviewer.widgets import StatefulWidget


class AppViewer:
    """
    A wrapper around QApplication which provides several creature comforts.
    Serves as a root node for any qtviewer GUI.
    """

    app: QApplication
    panel: LayoutWidget
    timer: QTimer

    data_displays: List[StatefulPane]
    data_controls: List[StatefulWidget]

    def __init__(self, title="") -> None:

        self.app = QApplication([])
        self.panel = LayoutWidget()
        self.panel.setWindowTitle(title)

        # set up storage
        self.data_controls = []
        self.data_displays = []

        # enable close on ctrl-c
        signal.signal(signal.SIGINT, self.__handler_sigint)
        self.timer = QTimer()
        self.timer.timeout.connect(self.__squelch)
        self.timer.start(100)

    def __squelch(self, *args, **kwargs):
        """
        exists purely to return process control to the python layer, allowing
        signals to be processed and actions to be taken accordingly.
        """
        pass

    def __handler_sigint(self, signal, frame):
        print("received interrupt signal")
        self.app.quit()

    def add_panes(self, panes: List[QWidget]):
        """
        A convenience wrapper function.

        :param panes: [TODO:description]
        """

        for x in panes:
            self.add_pane(x)

    def add_pane(self, pane: QWidget):
        """
        Add the provided pane to the GUI window layout.
        Override in inheriting classes if different behavior is desired.

        :param pane: any instance of a QtWidget
        """
        self.panel.addWidget(pane)
        self.panel.nextRow()

        pane_type = type(pane)
        if issubclass(pane_type, StatefulPane):
            s_pane: StatefulPane = pane  # pyright: ignore
            for x in self.data_controls:
                s_pane.enchain(x)
            self.data_displays.append(s_pane)

        if issubclass(pane_type, StatefulWidget):
            s_widget: StatefulWidget = pane  # pyright: ignore
            for x in self.data_displays:
                x.enchain(s_widget)
            self.data_controls.append(s_widget)

    def run(self):
        """
        A conveniece function with launches the Qt GUI and displays the window
        simultaneously.
        """
        self.panel.show()
        for x in self.data_displays:
            x.force_flush()
        sys.exit(self.app.exec())


class VisionViewer(AppViewer):
    """
    An image data focused viewer. At the time of writing, there are no true
    differences between this class and the parent. Instead, it exists for the
    event more custom changes are needed, reducing future code duplication.
    """

    def __init__(self, title="CV Image Viewer") -> None:
        super().__init__(title=title)
