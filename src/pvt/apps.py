import signal
import sys
from typing import List
from PySide6.QtCore import QCoreApplication, QTimer
from PySide6.QtWidgets import QHBoxLayout, QMainWindow, QWidget, QApplication
from pyqtgraph import LayoutWidget
from pvt.panels import StatefulPane
from pvt.widgets import StatefulWidget
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
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # pyright: ignore

    def addWidget(self, widget: QWidget):
        """
        Add a widget to the layout used by the window.
        :param widget: Widget to add to the layout.
        """
        self.panel.addWidget(widget)

    def nextRow(self):
        """
        Move the pointer of the window's layout widget to the next row.

        This function exists soly for the sake of convenience and is not
        intended to be called by user code.
        """
        self.panel.nextRow()


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
        signal.signal(signal.SIGINT, self.sigint)
        self.timer = QTimer(parent=self)
        self.timer.timeout.connect(lambda **_: None)
        self.timer.start(100)

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
    Serves as the base root element for any pvt GUI.
    """

    data_displays: List[StatefulPane]
    data_controls: List[StatefulWidget]

    def __init__(self, title: str, width: int, height: int, **kwargs) -> None:
        super().__init__(title=title)
        self.data_controls = []
        self.data_displays = []

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

    def enchain_global(self, pane: QWidget):
        """
        Enchain the specified widget to the shared global application state
        provided the widget derives from one of the classes configured to take
        advantage of this feature. Otherwise do nothing.

        :param pane: The widget to enchain.
        """
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
        Add the provided pane(s) to the GUI window layout.

        :param panes: A sequence of one or more widgets to add to the display.
        """

        for x in panes:
            self.main_window.addWidget(x)
            self.main_window.nextRow()
            self.enchain_global(x)

    def add_mosaic(self, mosaic: List[List[QWidget]]):
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
                self.enchain_global(element)
            self.main_window.addWidget(wrapper)
            self.main_window.nextRow()

    def run(self):
        """
        Launch the viewer.

        IMPORTANT: Executing this function will block the main thread.
        """
        for x in self.data_displays:
            x.force_flush()
        super().run()


class Viewer(App):
    """
    A data focused viewer. However, at the time of writing this class is no
    different than the parent class and instead only exists for the event more
    custom changes are added.
    """

    def __init__(
        self, title: str = "Data Viewer & Algorithm Tuner", width: int = 1280, height: int = 720, **kwargs
    ) -> None:
        """
        Instantiate a new instance of the class.

        :param title: string value displayed in the main window title bar.
        :param width: window width
        :param height: window height
        """
        super().__init__(title=title, width=width, height=height, **kwargs)
