from PySide6.QtCore import QTimer, QLibraryInfo
from PySide6.QtWidgets import QMainWindow, QWidget, QApplication
from PySide6.QtWidgets import QSizePolicy
from pyqtgraph import LayoutWidget
from typing import Literal
import os
import signal
import sys


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
    The foundational element for any GUI application built with this library.
    This class extends QApplication with additional features to simplify GUI
    development.

    Advanced users may specify alternative platform display types. One useful
    non-default is the "vnc" type, which routes the application's display
    through a VNC server. This enables remote access when the visualization
    host differs from the user’s local machine — for instance, when running
    compute-intensive tasks on a cluster or a system with specialized hardware
    (e.g., GPUs, stream processors). Note that the VNC feature is primarily
    available on Linux systems, although remote hosts on any operating system
    can connect to the VNC session.

    If no platform type is specified, the default for the host system is used.
    For barebones Linux systems that do not support xcb (X Window Server) or
    Wayland, using the "vnc" type is a practical workaround that avoids the
    need to install or build additional libraries.

    IMPORTANT: Choosing a non-default platform type can result in performance
    penalties. By default, Qt selects the most efficient backend unless
    otherwise specified. Manually specifying a platform type may require extra
    translation to render content correctly on the target display.
    Additionally, remote display types like "vnc" incur extra latency due to
    bidirectional network communication.
    """

    def __init__(
        self,
        title: str = "Data Viewer & Algorithm Tuner",
        width: int = 1280,
        height: int = 720,
        platform: Literal['default', 'vnc'] = "default",
    ) -> None:
        """
        :param title: window title
        :param width: window width
        :param height: window height
        :param platform: the name of the display server type
        :raises ValueError: if the specified `platform` is not a valid option
            for the host system.
        """
        if platform != "default":

            path_plugins = QLibraryInfo.path(QLibraryInfo.LibraryPath.PluginsPath)
            path_platforms = os.path.join(path_plugins, "platforms")
            available_platforms = os.listdir(path_platforms)
            available_platforms = [s.split(sep=".")[0] for s in available_platforms]  # remove extension
            available_platforms = [s.removeprefix("libq") for s in available_platforms]  # remove lib prefix
            platforms_available = set(available_platforms)

            if platform not in platforms_available:
                message = "\n".join(
                    [
                        f"{platform=} is not available on this host.",
                        f"The following Qt platform types are available: {platforms_available=}",
                    ]
                )
                raise ValueError(message)
            elif platform == "vnc":
                os.environ["QT_QPA_PLATFORM"] = f"vnc:size={width}x{height}"
            else:
                os.environ["QT_QPA_PLATFORM"] = f"{platform}"

        super().__init__(title=title)
        self.resize(width, height)  # a spot fix for github issue #033
