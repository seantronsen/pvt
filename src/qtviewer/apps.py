from PySide6.QtWidgets import QVBoxLayout, QWidget, QApplication


class VisionViewer:

    app: QApplication
    panel: QWidget

    def __init__(self, title="CV Image Viewer") -> None:

        self.app = QApplication([])
        self.panel = QWidget()
        self.panel.setWindowTitle(title)
        layout = QVBoxLayout()
        self.panel.setLayout(layout)

    def add_pane(self, pane: QWidget):
        layout = self.panel.layout()
        layout.addWidget(pane)  # pyright: ignore

    def run(self):
        self.panel.show()
        self.app.exec()
