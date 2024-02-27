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
        self.panel = QWidget()
        self.panel.setWindowTitle(title)
        layout = QVBoxLayout()
        self.panel.setLayout(layout)

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
        self.app.exec()
