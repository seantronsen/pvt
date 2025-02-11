from PySide6.QtCore import Slot
from PySide6.QtWidgets import QLabel, QSizePolicy, QVBoxLayout, QWidget
from typing import Callable, Dict, Optional, Any
from pvt_experimental.decorators import perflog
from pvt_experimental.identifier import IdManager
import pyqtgraph as pg


class StatefulDisplay(QWidget):
    """
    A base data display class which subscribes to application state changes via
    a Qt slot. The user-specified callback, provided to the constructor, is
    executed to update the display with the most recent data each time the slot
    receives state signal data.

    IMPORTANT: Callback functions should be stateless.
    """

    __callback: Callable[..., object]

    def __init__(self, callback: Callable[..., object] | None = None, title: str | None = None) -> None:
        """
        Initialize an instance of the class.

        :param callback: A callback for updating the rendered data on state changes.
        :param title: an optional title to render as a label above the display
        """
        assert callback is not None
        super().__init__()
        self.__callback = callback

        # todo: abstract this shit into superclass. also shared by controls
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)

        self.identifier = f"{self.__class__.__name__}-{IdManager().generate_identifier()}".lower()
        self.identifier_label = QLabel(self.identifier)

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.identifier_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)

        self._add_widget(self.identifier_label)

        if title is not None:
            tlabel = QLabel(text=title)
            tlabel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
            self._add_widget(tlabel)

    def _add_widget(self, w: QWidget):
        self.layout().addWidget(w)

    @Slot(dict)
    def on_viewer_state_changed(self, kwargs_as_dict: dict[str, object]):
        """
        This function is an event handler which executes the user specified
        callback when the state of the application changes.

        :param kwargs: a dictionary of key value pairs. for each pair, the key
            is the keyname assigned to a stateful control and the value is the
            current value held by that same control.
        :type kwargs: kwargs dict
        """
        data = self.__compute_data(**kwargs_as_dict)
        self.__render_data(data)

    @perflog(event="callback-compute")
    def __compute_data(self, **kwargs):
        return self.__callback(**kwargs)

    @perflog(event="pyqtgraph-render")
    def __render_data(self, *args):
        self._render_data(*args)

    def _render_data(self, *args):
        """
        IMPORTANT: Stateful display derivations must override this method with
        the logic required for Qt to display any data to be rendered..

        NOTE: It's set up like this because python decorators (see perflog) do
        not apply to methods overridden in a derived class.
        """
        raise NotImplementedError


class StatefulImageView(StatefulDisplay):
    """
    A pane which can be used to display and analyze image data with a fast
    refresh rate. An callback function for updating the display must be
    provided to the constructor function.

    IMPORTANT: Image data should be normalized and converted to standard bytes
    (uint8). Note the underlying pyqtgraph library supports uint16 and small
    floats, but visualization works best and renders fastest for bytes (e.g.,
    u8 uint8 uchar, etc.).
    """

    displaypane: pg.ImageView
    dargs: Dict

    def __init__(
        self,
        callback: Callable,
        autoRange=True,
        autoLevels=True,
        autoHistogramRange=True,
        border: Optional[Any] = None,
        title: str | None = None,
        **kwargs,
    ) -> None:
        """
        Initialize an instance of the class.

        :param callback: A callback function which updates the rendered data.
        :param autoRange: A flag which specifies whether display zoom and panning
            should be reset on each render. Disable this if you want to focus on a
            particular set of pixels for any frame to be displayed.
        :param autoLevels: A flag which specifies whether to update the intensity
            range when displaying the image (normalization)
        :param autoHistogramRange: flag which specifies whether the histogram
            widget is scaled to fit the data.
        :param title: an optional title to render as a label above the display
        """
        super().__init__(callback, title=title, **kwargs)
        self.dargs = dict(autoRange=autoRange, autoLevels=autoLevels, autoHistogramRange=autoHistogramRange)
        self.displaypane = pg.ImageView()
        self.displaypane.layout().setContentsMargins(0, 0, 0, 0)
        self.displaypane.layout().setSpacing(0)
        self._add_widget(self.displaypane)
        if border is not None:
            self.set_border(border)

    def _render_data(self, *args):
        self.displaypane.setImage(args[0], **self.dargs)

    def set_border(self, border: Any):
        self.displaypane.imageItem.setBorder(border)
