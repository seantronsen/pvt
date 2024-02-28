import signal
import sys
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QVBoxLayout, QWidget, QApplication

# from qtpy.QtWidgets import QVBoxLayout, QWidget, QApplication


class VisionViewer:
    """
    A wrapper around QApplication which provides several creature comforts.
    Serves as a root node for any qtviewer GUI.
    """

    app: QApplication
    panel: QWidget

    def __init__(self, title="CV Image Viewer") -> None:

        self.app = QApplication([])
        self.app.startTimer
        self.panel = QWidget()
        self.panel.setWindowTitle(title)
        layout = QVBoxLayout()
        self.panel.setLayout(layout)

        # enable close on ctrl-c
        signal.signal(signal.SIGINT, self.handler_sigint)
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_signal)
        self.timer.start(100)

    def check_signal(self, *args, **kwargs):
        pass

    def handler_sigint(self, signal, frame):
        print("received interrupt signal")
        self.app.quit()

    def add_pane(self, pane: QWidget):
        """
        Add the provided pane to the GUI window layout.

        :param pane: any instance of a QtWidget
        """

        self.panel.layout().addWidget(pane)

    def run(self):
        """
        A conveniece function with launches the Qt GUI and displays the window
        simultaneously.
        """
        self.panel.show()
        sys.exit(self.app.exec())
