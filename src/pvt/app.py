import signal
import sys
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QMainWindow, QWidget, QApplication
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
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.set_window_content(QWidget())

    def set_window_content(self, widget: QWidget):
        """
        Set the window to display the widget provided. The provided widget
        should be a composite which encapsulates complicated behaviors within a
        hierarchy of children.

        :param widget: any QWidget
        """
        self.setCentralWidget(widget)


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
        signal.signal(signal.SIGINT, self.sigint)  # pyright: ignore
        self.timer = QTimer(parent=self)
        self.timer.timeout.connect(lambda **_: None)  # pyright: ignore
        self.timer.start(100)

    def sigint(self, *_):
        """
        A component of the timed event check used to "gracefully shutdown"
        (kill) the application if the user sends the interrupt signal.
        """
        print("received interrupt: attempting graceful termination")
        self.quit()

    def resize(self, width: int, height: int):
        """
        Resize the application window.

        :param width: width in pixels
        :param height: height in pixels
        """
        self.main_window.resize(width, height)

    def set_window_content(self, widget: QWidget):
        """
        Set the window to display the widget provided. The provided widget
        should be a composite which encapsulates complicated behaviors within a
        hierarchy of children.

        :param widget: any QWidget
        """
        self.main_window.set_window_content(widget)

    def run(self) -> None:
        """
        A conveniece function with launches the Qt GUI and displays the window
        simultaneously.

        IMPORTANT: Executing this function will block the main thread.
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
        self.resize(width, height)  # a spot fix for github issue #033
