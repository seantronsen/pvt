import signal
import sys
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QWidget, QApplication
from pyqtgraph import LayoutWidget


class AppViewer:
    """
    A wrapper around QApplication which provides several creature comforts.
    Serves as a root node for any qtviewer GUI.
    """

    app: QApplication
    panel: QWidget
    timer: QTimer
    layout: LayoutWidget

    def __init__(self, title="") -> None:

        self.app = QApplication([])
        self.panel = QWidget()
        self.panel.setWindowTitle(title)
        self.layout = LayoutWidget()
        self.panel.setLayout(self.layout)

        # enable close on ctrl-c
        signal.signal(signal.SIGINT, self.handler_sigint)
        self.timer = QTimer()
        self.timer.timeout.connect(self.squelch)
        self.timer.start(100)

    def squelch(self, *args, **kwargs):
        """
        exists purely to return process control to the python layer, allowing
        signals to be processed and actions to be taken accordingly.
        """
        pass

    def handler_sigint(self, signal, frame):
        print("received interrupt signal")
        self.app.quit()

    def add_pane(self, pane: QWidget):
        """
        Add the provided pane to the GUI window layout.
        Override in inheriting classes if different behavior is desired.

        :param pane: any instance of a QtWidget
        """
        self.layout.addWidget(pane)
        self.layout.nextRow()

    def run(self):
        """
        A conveniece function with launches the Qt GUI and displays the window
        simultaneously.
        """
        self.panel.show()
        sys.exit(self.app.exec())


class VisionViewer(AppViewer):
    """
    An image data focused viewer. At the time of writing, there are no true
    differences between this class and the parent. Instead, it exists for the
    event more custom changes are needed, reducing future code duplication.
    """

    def __init__(self, title="CV Image Viewer") -> None:
        super().__init__(title=title)
