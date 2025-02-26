from PySide6 import QtGui
from PySide6.QtCore import Slot
from PySide6.QtWidgets import QLabel, QSizePolicy, QVBoxLayout, QWidget
from numpy.typing import NDArray
from pvt.decorators import perflog
from pvt.identifier import IdManager
from pyqtgraph import GraphicsLayoutWidget, PlotDataItem
from pyqtgraph.colormap import ColorMap
from typing import Callable
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


class ImagePane(StatefulPane):
    """
    A pane which can be used to display and analyze image data with a fast
    refresh rate. An callback function for updating the display must be
    provided to the constructor function.

    IMPORTANT: Image data should be normalized and converted to standard bytes
    (uint8). Note the underlying pyqtgraph library supports uint16 and small
    floats, but visualization works best and renders fastest for bytes.
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
        """
        super().__init__(callback, **kwargs)
        self.dargs = dict(autoRange=autoRange, autoLevels=autoLevels, autoHistogramRange=autoHistogramRange)
        self.displaypane = pg.ImageView()
        self.addWidget(self.displaypane)
        if border is not None:
            self.set_border(border)

    def render_data(self, *args):
        self.displaypane.setImage(args[0], **self.dargs)

    def set_border(self, border: Any):
        """
        A convenience wrapper function which can be used to draw a static color
        border around the image displayed in the panel. It's nothing more then
        a wrapper around the PyQtGraph function listed below.

        ```
        def set_border(self, b):
            Defines the border drawn around the image. Accepts all arguments supported by
            :func:`~pyqtgraph.mkPen`.
            self.border = fn.mkPen(b)
            self.update()
        ```
        :param border: Any argument style accepted by `pyqtgraph.mkPen`. Color
        strings defined by the W3C should work (at least for simple ones like
        "red") as well as hex strings or an integer list containing the RGB
        values. For fancier features like `width`, check out the documentation
        for the pen function discussed above.
        """
        self.displaypane.imageItem.setBorder(border)


def colors_from_cmap(cmap: ColorMap, ncolors: int):
    """
    Return a list of QColor objects from the from the provided colormap.

    :param cmap: ColorMap instance
    :param ncolors: number of colors to return
    :return: The list of QColor objects.
    """
    result: List[QtGui.QColor] = [
        cmap.map(x / ncolors, mode=ColorMap.QCOLOR) for x in range(ncolors)
    ]  # pyright: ignore
    return result


class BasePlot2DPane(StatefulPane):
    """
    The Base/Abstract class in which all 2D plotting panes are derived. The
    purpose of this class is merely to provide a basic set up for inheritors
    and reduce the amount of typing required to add new kinds of 2D plots in
    the future.
    """

    plot_item: pg.PlotItem
    plot_layout: pg.GraphicsLayoutWidget
    curves: List[PlotDataItem]
    plot_args: Dict

    def __init__(self, callback: Callable, **kwargs) -> None:
        """
        Instantiate an instance of the class.

        :param callback: A callback function to update the rendered data.
        :param kwargs: The keyword arguments are:
            - `title` (str): Plot title
            - `cmap` (str): Name of the desired colormap. Check PyQtGraph
              colormap options for details.
            - `ncolors` (int): Number of unique colors to use for plots with
              multiple components (lines, scatters, etc.)
            - `legend` (bool): A flag which specifies whether the legend is
              displayed. IMPORTANT, this hasn't been thoroughly tested.
            - `logx` (bool): A flag which specifies whether the x-axis is
              displayed as a log scale.
            - `logy` (bool): A flag which specifies whether the y-axis is
              displayed as a log scale.
            - `gridx` (bool): A flag which specifies whether the x-axis grid is
              shown.
            - `gridy` (bool): A flag which specifies whether the y-axis grid is
              shown.
        """
        self.plot_layout = GraphicsLayoutWidget()
        self.plot_item = self.plot_layout.addPlot(title=kwargs.pop("title", None))

        # prepare colors
        self.cmap = pg.colormap.get(kwargs.pop("cmap", "CET-C7s"))
        self.cmap_colors = colors_from_cmap(self.cmap, kwargs.pop("ncolors", 1))  # pyright: ignore

        if kwargs.pop("legend", False):
            self.plot_item.addLegend()

        self.plot_item.setLogMode(x=kwargs.pop("logx", False), y=kwargs.pop("logy", False))
        self.plot_item.showGrid(x=kwargs.pop("gridx", False), y=kwargs.pop("gridy", False))
        self.curves = []
        self.plot_args = {}

        super().__init__(callback, **kwargs)
        self.addWidget(self.plot_layout)

    def nth_color(self, n: int):
        """
        A convenience method which returns the nth QColor from the set of
        available colors created during initialization using modulo arithmetic.

        :param n: The nth color to be returned
        :return: The nth QColor
        """
        return self.cmap_colors[n % len(self.cmap_colors)]

    def set_xlabel(self, label: str, units: Optional[str] = None):
        """
        Set the x-axis label to the provided string.

        :param label: New label value to be assigned
        :param units: An optional unit value. If specified, the PyQtGraph will
        format the value using the appropriate SI prefix based on the data
        range.
        """
        self.plot_item.setLabel(axis="bottom", text=label, units=units)

    def set_ylabel(self, label: str, units: Optional[str] = None):
        """
        Set the y-axis label to the provided string.

        :param label: New label value to be assigned
        :param units: An optional unit value. If specified, the PyQtGraph will
        format the value using the appropriate SI prefix based on the data
        range.
        """
        self.plot_item.setLabel(axis="left", text=label, units=units)

    def set_title(self, title: str):
        """
        Set the plot title.

        :param title: Title string to be assigned.
        """
        self.plot_item.setTitle(title=title)

    def plot(self, i: int, **kwargs):
        """
        A method which executes a tailored version of the plotting function.
        Deriving classes are encouraged to override this function, especially
        for cases where different plot features (e.g. lines) must have
        different properties based on their order of appearance (e.g.
        coloring).

        NOTE: By design, this method should only be called by __reinitialize
        curves. As such, if different behavior is desired, create a subclass
        that overrides the default design features.

        :param i: index number of appearance in the plotting order.
        """
        return self.plot_item.plot(**self.plot_args, **kwargs)

    def reinitialize_curves(self, ncurves: int):
        """
        If the number of curves to plot on the next render differs from the
        number currently known, reinitialize the curves collection such that it
        holds the required number of curve instances.

        :param ncurves: the number of required curves
        """
        for x in self.curves:
            self.plot_item.removeItem(x)
        self.curves = []
        for x in range(ncurves):
            self.curves.append(self.plot(x))

    def render_data(self, *args):
        """
        OVERRIDE: See parent definition.
        Use the provided data to update the curves on the 2D PlotView.

        IMPORTANT: Ensure data provided to other methods is formatted
        appropriately. Valid formats are:
            - (M,N) -> M plots, each with N y-values (x generated as range(y_0, y_n-1))
            - (M,N,2) -> M plots, each with N x,y points

        :param args[0]: an ndarray of data points
        """
        data: NDArray = args[0]
        n_curves = data.shape[0]
        if n_curves != len(self.curves):
            self.reinitialize_curves(n_curves)

        for i in range(n_curves):
            self.curves[i].setData(data[i])
            # self.curves[i].setData(data)


class Plot2DLinePane(BasePlot2DPane):
    """
    Display a pane which draws all provided data as a set of one or more
    curves.
    """

    def __init__(self, callback: Callable, line_width: int = 1, fillLevel: Optional[float] = None, **kwargs) -> None:
        """
        Instantiate an instance of the class.

        :param callback: A callback to update rendered data
        :param line_width: The width of each line/curve in pixels
        :param fillLevel: If specified, the area between the curve and
        fillLevel is filled using a transparent version of the line color.
        """
        super().__init__(callback, **kwargs)
        self.line_width = line_width
        self.plot_args["fillLevel"] = fillLevel

    def plot(self, i, **_):
        color = self.nth_color(i)
        fill_color = QtGui.QColor(color)
        fill_color.setAlphaF(0.7)
        return super().plot(i, pen=dict(color=color, width=self.line_width), fillBrush=fill_color)


class Plot2DScatterPane(BasePlot2DPane):
    """
    Display a pane which draws all provided data as a set of one or more
    scatter plots.
    """

    def __init__(self, callback: Callable, symbol='t', symbolSize=10, **kwargs) -> None:
        """
        Instantiate an instance of the class.

        :param callback: A callback to update rendered data
        :param symbol: The symbol kind to use. Review the PyQtGraph
        documentation for a list of options.
        :param symbolSize: Size of each symbol to be drawn in pixels
        """
        super().__init__(callback, **kwargs)
        self.plot_args["symbol"] = symbol
        self.plot_args["symbolSize"] = symbolSize

        # DO NOT CONNECT POINTS
        self.plot_args["pen"] = None

    def plot(self, i, **_):
        return super().plot(i, symbolBrush=self.nth_color(i))
