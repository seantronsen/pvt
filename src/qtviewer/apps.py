import signal
import sys
from typing import List
from PySide6.QtCore import QCoreApplication, QTimer
from PySide6.QtWidgets import QHBoxLayout, QMainWindow, QWidget, QApplication
from pyqtgraph import LayoutWidget
from qtviewer.panels import StatefulPane
from qtviewer.widgets import StatefulWidget
from PySide6.QtWidgets import QSizePolicy


class MainWindow(QMainWindow):

    panel: LayoutWidget

    def __init__(self, title="qtviewer") -> None:
        super().__init__()
        self.setWindowTitle(title)
        self.panel = LayoutWidget(parent=self)
        self.setCentralWidget(self.panel)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # pyright: ignore

    def addWidget(self, widget: QWidget):
        self.panel.addWidget(widget)

    def nextRow(self):
        self.panel.nextRow()


class Skeleton(QApplication):
    """
    A general refactoring of the larger application class which extracts some
    of the more basic elements.
    """

    timer: QTimer
    main_window: MainWindow

    def __init__(self, title):
        super().__init__([])
        self.main_window = MainWindow(title=title)

        # enable terminate on sigint / ctrl-c
        signal.signal(signal.SIGINT, self.sigint)
        self.timer = QTimer(parent=self)
        self.timer.timeout.connect(lambda **_: None)
        self.timer.start(100)

    def screen_height(self):
        return QCoreApplication.instance().primaryScreen().geometry().height()  # pyright: ignore

    def sigint(self, signal, frame):
        """
        A component of the timed event check used to "gracefully shutdown"
        (kill) the application if the user sends the interrupt signal.

        :param signal: [TODO:description]
        :param frame: [TODO:description]
        """
        print("received interrupt signal: attempting graceful program termination")
        self.quit()

    def run(self) -> None:
        """
        A conveniece function with launches the Qt GUI and displays the window
        simultaneously.
        """
        self.main_window.show()
        sys.exit(self.exec())


class App(Skeleton):
    """
    A wrapper around QApplication which provides several creature comforts.
    Serves as a root node for any qtviewer GUI.
    """

    data_displays: List[StatefulPane]
    data_controls: List[StatefulWidget]

    def __init__(self, title="", **kwargs) -> None:
        super().__init__(title=title)
        self.data_controls = []
        self.data_displays = []

        # a most ugly spot fix for issue #033
        sheight = self.screen_height()
        window_height = kwargs.get("window_height", sheight - (0.1 * sheight))
        window_width = kwargs.get("window_width", 1080)
        self.main_window.resize(window_width, window_height)

    def enchain_global(self, pane: QWidget):
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

    def add_panes(self, *panes: QWidget):
        """
        Add the provided pane to the GUI window layout.
        Override in inheriting classes if different behavior is desired.

        :param panes: [TODO:description]
        """

        for x in panes:
            self.main_window.addWidget(x)
            self.main_window.nextRow()
            self.enchain_global(x)

    def add_mosaic(self, mosaic: List[List[QWidget]]):
        assert type(mosaic) == list
        assert len(mosaic) != 0 and type(mosaic[0]) == list

        for row in mosaic:
            wrapper = QWidget(parent=self.main_window)
            wrapper.setLayout(QHBoxLayout())
            for element in row:
                wrapper.layout().addWidget(element)
                self.enchain_global(element)
            self.main_window.addWidget(wrapper)
            self.main_window.nextRow()

    def run(self):
        # TODO/FIX: should all panes solely use global state, then this results
        # in many unnecessary re-renders on start up. not a major issue for now.
        for x in self.data_displays:
            x.force_flush()
        super().run()


class VisionViewer(App):
    """
    An image data focused viewer. At the time of writing, there are no true
    differences between this class and the parent. Instead, it exists for the
    event more custom changes are needed, reducing future code duplication.
    """

    def __init__(self, title="CV Image Viewer", **kwargs) -> None:
        super().__init__(title=title, **kwargs)


class PlotViewer(App):
    """
    Another superficial class that may exist only temporarily.
    """

    def __init__(self, title="Plot Viewer", **kwargs) -> None:
        super().__init__(title=title, **kwargs)
