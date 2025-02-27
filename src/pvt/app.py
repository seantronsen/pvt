import signal
import sys
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QHBoxLayout, QMainWindow, QWidget, QApplication
from pyqtgraph import LayoutWidget
from PySide6.QtWidgets import QSizePolicy


class MainWindow(QMainWindow):
    """
    A main window class which runs the setup for the default application
    display features.
    """

    panel: LayoutWidget

    def __init__(self, title: str = "Python Data Visualizer & Algorithm Tuner") -> None:
        """
        Initialize a new instance of the class.

        :param title: String value to be displayed in the window title bar.
        """
        super().__init__()
        self.setWindowTitle(title)
        self.panel = LayoutWidget()
        self.setCentralWidget(self.panel)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def addWidget(self, widget: QWidget):
        """
        Add a widget to the layout used by the window.
        :param widget: Widget to add to the layout.
        """
        self.panel.addWidget(widget) # pyright: ignore
        self.panel.nextRow() # pyright: ignore


class Skeleton(QApplication):
    """
    A general refactoring of the larger application class which extracts some
    of the more basic elements.
    """

    timer: QTimer
    main_window: MainWindow

    def __init__(self, title: str):
        """
        Initialize an instance of the class.

        :param title: Title string passed to the main window.
        """
        super().__init__([])
        self.main_window = MainWindow(title=title)

        # enable terminate on sigint / ctrl-c
        signal.signal(signal.SIGINT, self.sigint) # pyright: ignore
        self.timer = QTimer(parent=self)
        self.timer.timeout.connect(lambda **_: None) # pyright: ignore
        self.timer.start(100)

    def sigint(self, *_):
        """
        A component of the timed event check used to "gracefully shutdown"
        (kill) the application if the user sends the interrupt signal.
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
    Serves as the base root element for any pvt GUI.
    """

    def __init__(
        self,
        title: str = "Data Viewer & Algorithm Tuner",
        width: int = 1280,
        height: int = 720,
    ) -> None:
        super().__init__(title=title)

        # a spot fix for issue #033
        self.resize(width, height)

    def resize(self, width: int, height: int):
        """
        Executing this method with the proper arguments will cause the
        application window to be resized accordingly. It does nothing more than
        calling the method with the same name on the main window class, but it
        makes for less typing.

        :param width: width in pixels
        :param height: height in pixels
        """
        self.main_window.resize(width, height)

    def add_panes(self, *panes: QWidget):
        """
        Add the provided pane(s) to the GUI window layout.

        :param panes: A sequence of one or more widgets to add to the display.
        """

        for x in panes:
            self.main_window.addWidget(x)

    def add_mosaic(self, mosaic: list[list[QWidget]]):
        """
        A convenience method which provides users a simple method for
        specifying a row/column layout to be displayed in the viewer. Passing
        in a list of lists, each sub-list becomes a row added to the display as
        the next bottom-most element. Elements of each sub-list are placed as
        columns from left to right.

        :param mosaic: A list of lists containing widgets to add to the
        display.
        """
        assert type(mosaic) == list
        assert len(mosaic) != 0 and type(mosaic[0]) == list

        for row in mosaic:
            wrapper = QWidget(parent=self.main_window)
            wrapper.setLayout(QHBoxLayout())
            for element in row:
                wrapper.layout().addWidget(element)
            self.main_window.addWidget(wrapper)

    def run(self):
        """
        Launch the viewer.

        IMPORTANT: Executing this function will block the main thread.
        """
        super().run()
