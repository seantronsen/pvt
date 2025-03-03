from PySide6 import QtGui
from PySide6.QtCore import Slot
from PySide6.QtWidgets import QLabel, QSizePolicy, QVBoxLayout, QWidget
from dataclasses import dataclass
from numpy.typing import NDArray
from numpy.typing import NDArray
from pvt.decorators import perflog
from pvt.identifier import IdManager
from pyqtgraph import GraphicsLayoutWidget, PlotItem
from pyqtgraph.colormap import ColorMap
from typing import Any, Callable, cast
import pyqtgraph as pg


def colors_from_cmap(cmap: ColorMap, ncolors: int):
    """
    Return a list of QColor objects from the from the provided colormap.

    :param cmap: ColorMap instance
    :param ncolors: number of colors to return
    :return: The list of QColor objects.
    """
    result: list[QtGui.QColor] = [
        cmap.map(x / ncolors, mode=ColorMap.QCOLOR) for x in range(ncolors)
    ]  # pyright: ignore
    return result


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
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)

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

    # fucking pyright and qt slots...
    @Slot(object)
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
    def __compute_data(self, **kwargs: Any):
        return self.__callback(**kwargs)

    @perflog(event="pyqtgraph-render")
    def __render_data(self, *args: Any):
        self._render_data(*args)

    def _render_data(self, *args: Any) -> None:
        """
        IMPORTANT: Stateful display derivations must override this method with
        the logic required for Qt to display any data to be rendered..

        NOTE: It's set up like this because python decorators (see perflog) do
        not apply to methods overridden in a derived class.
        """
        raise NotImplementedError


@dataclass
class ImageViewConfig:
    autoRange: bool = True
    autoLevels: bool = True
    autoHistogramRange: bool = True
    border_color: str | None = None


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

    def __init__(
        self,
        callback: Callable[..., object],
        title: str | None = None,
        config: ImageViewConfig = ImageViewConfig(),
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
        super().__init__(callback, title=title)
        self._config = config
        self.displaypane = pg.ImageView()
        self.displaypane.layout().setContentsMargins(0, 0, 0, 0)  # pyright: ignore
        self.displaypane.layout().setSpacing(0)  # pyright: ignore
        self._add_widget(self.displaypane)
        if self._config.border_color is not None:
            self.displaypane.imageItem.setBorder(self._config.border_color)

    def _render_data(self, *args: Any):
        image: NDArray[Any] = args[0]
        self.displaypane.setImage(
            image,
            autoRange=self._config.autoRange,
            autoLevels=self._config.autoLevels,
            autoHistogramRange=self._config.autoHistogramRange,
        )


@dataclass
class PlotView2DConfig:
    """
    Configuration for a 2D plot view.

    Attributes
    ----------
    background_color : str
        Background color for the plot. Defaults to "black".
    auto_colors_cmap : str
        Name of the colormap used for generating automatic colors.
        Accepts any valid matplotlib colormap name if matplotlib is present in
        the environment. Defaults to "CET-C7s".
    auto_colors_nunique : int
        Number of unique colors to generate before repeating the color sequence.
        Colors are sampled equidistantly from the colormap gradient. Defaults to 9.
    log_scale_x : bool
        If True, the x-axis is displayed on a logarithmic scale. Defaults to False.
    log_scale_y : bool
        If True, the y-axis is displayed on a logarithmic scale. Defaults to False.
    gridlines_x : bool
        If True, grid lines are shown along the x-axis. Defaults to False.
    gridlines_y : bool
        If True, grid lines are shown along the y-axis. Defaults to False.
    title : str or None
        Title of the plot. Defaults to None.
    label_x : str or None
        Optional label to add to the x-axis
    label_y : str or None
        Optional label to add to the y-axis
    legend : bool
        If True, the plot legend is displayed. Defaults to False.
    """

    # colors
    background_color: str = "black"
    auto_colors_cmap: str = "CET-C7s"
    auto_colors_nunique: int = 9

    # graph characteristics
    log_scale_x: bool = False
    log_scale_y: bool = False
    gridlines_x: bool = False
    gridlines_y: bool = False

    # descriptors
    title: str | None = None
    legend: bool = False
    label_x: str | None = None
    label_y: str | None = None


@dataclass
class PlotDataBase:
    """
    Base data container for plot elements.

    Attributes
    ----------
    x : NDArray[Any]
        A one-dimensional array-like sequence of x-axis values.
        The required shape is (N,) and must match the shape of y.
        Lists are acceptable but not advised.
    y : NDArray[Any]
        A one-dimensional array-like sequence of y-axis values.
        Must have the same shape as x. Lists are acceptable but not advised.
    color : str or None, optional
        Color specification for the plot element. If None, the parent plot view automatically
        selects the next default color based on the assigned colormap.
        If specified, the color can be one of: 'r', 'g', 'b', 'c', 'm', 'y', 'k', 'w',
        an SVG color keyword, or a hex string (e.g., "#RRGGBB").
    name : str or None, optional
        The label used in the plot legend, if legends are enabled.
    """

    x: NDArray[Any]
    y: NDArray[Any]
    color: str | None = None
    name: str | None = None


@dataclass
class PlotDataScatter(PlotDataBase):
    """
    Data container for scatter plot elements. Extends PlotDataBase with
    additional options specific to scatter plots.

    Attributes
    ----------
    marker : str
        Marker style used for the scatter plot. Defaults to "o".
        (TODO: Provide a comprehensive list or reference to all available marker options.)
    marker_size : int
        Size of the marker. Defaults to 10.

    Marker Options:
        - 'o': circle (default)
        - 's': square
        - 't': triangle
        - 'd': diamond
        - '+': plus
        - 't1': triangle pointing upwards
        - 't2': triangle pointing right side
        - 't3': triangle pointing left side
        - 'p': pentagon
        - 'h': hexagon
        - 'star': star
        - '|': vertical line
        - '_': horizontal line
        - 'x': cross
        - 'arrow_up': arrow pointing up
        - 'arrow_right': arrow pointing right
        - 'arrow_down': arrow pointing down
        - 'arrow_left': arrow pointing left
        - 'crosshair': crosshair
    """

    marker: str = "o"  # TODO: NEEDS A LIST OF ALL OPTIONS
    marker_size: int = 10


@dataclass
class PlotDataLine(PlotDataBase):
    """
    Data container for line plot elements. Extends PlotDataBase with additional
    options specific to line plots.

    Attributes
    ----------
    line_width : int
        Width of the line. It is recommended to keep this value at 1 since
        other values will decrease performance.
    marker : str or None
        Optional marker style to accentuate individual data points along the line.
        When specified, it effectively combines scatter and line plot features. Defaults to None.
    marker_size : int or None
        Size of the marker if markers are enabled. Defaults to None.
    marker_color : str or None
        Color for the marker. If None and markers are enabled, the marker color defaults to the
        value of the `color` attribute from the base class.
    """

    line_width: int = 1
    marker: str | None = None
    marker_size: int | None = None
    marker_color: str | None = None


class StatefulPlotView2D(StatefulDisplay):
    """
    The Base/Abstract class in which all 2D plotting panes are derived. The
    purpose of this class is merely to provide a basic set up for inheritors
    and reduce the amount of typing required to add new kinds of 2D plots in
    the future.
    """

    def __init__(
        self,
        callback: Callable[..., object] | None = None,
        title: str | None = None,
        config: PlotView2DConfig = PlotView2DConfig(),
    ) -> None:
        super().__init__(callback=callback, title=title)

        # setup the underlying graphics
        _w_graphics = GraphicsLayoutWidget()
        self._canvas = cast(PlotItem, _w_graphics.addPlot(title=config.title))  # pyright: ignore
        cmap = pg.colormap.get(config.auto_colors_cmap)
        assert isinstance(cmap, ColorMap), f"'{config.auto_colors_cmap=}', either not valid or not findable."
        self._default_colors = colors_from_cmap(cmap, config.auto_colors_nunique)

        # todo: re-assign the _render_data method to avoid plotting overhead if
        # no legend is requested
        # configure graph appearance
        # self._legend = self._canvas.addLegend() if config.legend else None
        self._canvas.setLogMode(x=config.log_scale_x, y=config.log_scale_y)
        self._canvas.showGrid(x=config.gridlines_x, y=config.gridlines_y)
        if config.label_x:
            self._canvas.setLabel(axis="bottom", text=config.label_x)

        if config.label_y:
            self._canvas.setLabel(axis="left", text=config.label_x)

        self._add_widget(_w_graphics)

    def _render_data(self, *args: PlotDataLine | PlotDataScatter) -> None:

        # todo: add slow legend logic bullshit
        self._canvas.clear()
        for i, data_item in enumerate(args[0]):
            kargs: dict[str, object] = dict(x=data_item.x, y=data_item.y)
            color = data_item.color if data_item.color else self._default_colors[i % len(self._default_colors)]
            if isinstance(data_item, PlotDataScatter):
                kargs["symbol"] = data_item.marker
                kargs["symbolSize"] = data_item.marker_size
                kargs["symbolBrush"] = color
                self._canvas.plot(
                    pen=None,  # otherwise connections are drawn
                    **kargs,
                )
            elif isinstance(data_item, PlotDataLine):
                if data_item.marker:
                    kargs["symbol"] = data_item.marker
                    kargs["symbolSize"] = data_item.marker_size
                    kargs["symbolBrush"] = data_item.marker_color if data_item.marker_color else color
                self._canvas.plot(
                    pen=dict(
                        color=color,
                        width=data_item.line_width,
                    ),
                    **kargs,
                )
            else:
                raise ValueError("unknown plot data item detected")
