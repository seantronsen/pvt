from PySide6.QtCore import Slot
from PySide6.QtWidgets import QLabel, QSizePolicy, QVBoxLayout, QWidget
from dataclasses import dataclass
from numpy.typing import NDArray
from pvt.callback import Callback
from pvt.decorators import perflog
from pvt.identifier import IdManager
from pvt.utils import colors_from_cmap
from pyqtgraph import GraphicsLayoutWidget, GraphicsView, ImageItem, PlotDataItem, PlotItem, ViewBox
from pyqtgraph.colormap import ColorMap
from typing import Any, Callable, cast
import pyqtgraph as pg


class StatefulDisplay(QWidget):
    """
    A base data display class which subscribes to application state changes via
    a Qt slot. The user-specified callback, provided to the constructor, is
    executed to update the display with the most recent data each time the slot
    receives state signal data.

    IMPORTANT: Callback functions should be stateless.
    """

    def __init__(self, callback: Callable[..., Any], title: str | None = None) -> None:
        """
        Initialize an instance of the class.

        :param callback: A callback for updating the rendered data on state changes.
        :param title: an optional title to render as a label above the display
        """
        assert callable(callback)
        if not isinstance(callback, Callback):
            callback = Callback(func=callback)

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
        if self.__callback.should_run(**kwargs_as_dict):
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
class _ImageViewConfigBase:
    on_render_reset_viewport: bool = True
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

    @dataclass
    class Config(_ImageViewConfigBase):
        on_render_rescale_intensity: bool = True
        on_render_reset_histogram_range: bool = True

    def __init__(
        self,
        callback: Callable[..., object],
        title: str | None = None,
        config: Config = Config(),
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

        # profile_paint_events(self.displaypane)

    def _render_data(self, *args: Any):
        self.displaypane.setImage(
            args[0],
            autoRange=self._config.on_render_reset_viewport,
            autoLevels=self._config.on_render_rescale_intensity,
            autoHistogramRange=self._config.on_render_reset_histogram_range,
        )


class StatefulImageViewLightweight(StatefulDisplay):
    """
    This widget is the lightweight variant of the standard image view and only
    supports ndarray images with dtype=np.uint8. It assumes that any image data
    provided is already within the [0, 255] range and scaled as desired within
    that range. In other words, fancier features like input data type
    flexibility and live intensity rescaling are left to the developer/user to
    implement.

    In exchange, the widget minimizes rendering overhead—-a cost that can
    increase significantly with image size. The primary purpose of this
    implementation is to facilitate fast rendering of large RGB images.
    PyQtGraph is highly optimized for single-channel image visualization, which
    allows the standard image view widget to include a wide range of features
    while still delivering high render speeds regardless of image dimensions.
    One key optimization is offloading certain tasks directly to Qt.

    For single-channel grayscale images, when the user modifies the intensity
    histogram, PyQtGraph generates a lookup table (LUT) and passes both the
    image and the LUT to Qt. For images that are not single-channel ubytes, the
    most computationally expensive step is rescaling the image to the desired
    range. Even if auto-level adjustments are disabled, the default behavior of
    the histogram LUT widget still incurs this cost by setting the image-view
    levels.

    See `pyqtgraph.functions_qtimage._combine_levels_and_lut` for additional
    details on the rendering costs involved.
    """

    @dataclass
    class Config(_ImageViewConfigBase): ...

    def __init__(
        self,
        callback: Callable[..., object],
        title: str | None = None,
        config: Config = Config(),
    ) -> None:
        super().__init__(callback, title=title)
        self._config = config
        self.ii = ImageItem()
        if self._config.border_color is not None:
            self.ii.setBorder(self._config.border_color)

        gv, vb = GraphicsView(), ViewBox()
        vb.addItem(self.ii)
        vb.setAspectLocked()
        vb.invertY()  # fix coordinate space, else image is upside down
        gv.setCentralItem(vb)

        self._add_widget(gv)
        # profile_paint_events(gv)

    def _render_data(self, *args: Any):
        self.ii.setImage(
            args[0],
            # NOTE: enabling autolevels or setting levels will yield an extreme
            # degradation in RGB render performance.
            levels=None,
            autoLevels=False,
            # NOTE: enabling auto downsample will cause errors for images where
            # at least one axis has more than 30K pixels. Not entirely sure
            # why, but when this is true, `pyqtgraph`'s idea of downsampling is
            # to average chunks of the image instead of subsampling. Not only
            # is that slow, but the devs decided not to return the data to the
            # original dtype after the operation, hence the reason this error
            # will appear, even if your input image.dtype=np.uint8...
            #
            # the real question is: if `pyqtgraph`'s downsampling doesn't kick
            # in until 2^15 pixels are detected on at least one axis, then what
            # happens when this is disabled and the size of the image is
            # increased further? our local testing only went up to 30Kx30Kx3,
            # but that's still under the limit imposed by their package...
            autoDownsample=False,
        )


@dataclass
class _PlotDataBase:
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


class StatefulPlotView2D(StatefulDisplay):
    """
    A pane which displays plot data with a fast refresh rate. An callback
    function for updating the display must be provided to the constructor
    function. See the encapsulated configuration and plot kind classes for
    feature details.

    NOTE: Each plot item returned by the user defined callback will be
    overlayed within the same plot display to imitate the behavior of
    matplotlib.
    """

    @dataclass
    class Config:
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
        optimization_fixed_data_order : bool
            If True, the tool assumes the data callback always returns the same number of items in a fixed order,
            enabling reuse of existing plot components and achieving up to 10x faster performance.
            If False, the canvas is cleared and repopulated with new data on each frame, which is significantly slower.
            Defaults to True.
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

        # optimization settings
        optimization_fixed_data_order: bool = True

    @dataclass
    class Scatter(_PlotDataBase):
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

        marker: str = "o"
        marker_size: int = 10

    @dataclass
    class Line(_PlotDataBase):
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

    def __init__(
        self,
        callback: Callable[..., object],
        title: str | None = None,
        config: Config = Config(),
    ) -> None:
        super().__init__(callback=callback, title=title)

        # check for optimizations
        self._optim_fixed_data_order = config.optimization_fixed_data_order

        # setup the underlying graphics
        _w_graphics = GraphicsLayoutWidget()
        _w_graphics.setBackground(config.background_color)
        self._canvas = cast(PlotItem, _w_graphics.addPlot(title=config.title))  # pyright: ignore
        cmap = pg.colormap.get(config.auto_colors_cmap)
        assert isinstance(cmap, ColorMap), f"'{config.auto_colors_cmap=}', either not valid or not findable."
        self._default_colors = colors_from_cmap(cmap, config.auto_colors_nunique)

        # configure graph appearance
        self._legend = self._canvas.addLegend() if config.legend else None
        self._canvas.setLogMode(x=config.log_scale_x, y=config.log_scale_y)
        self._canvas.showGrid(x=config.gridlines_x, y=config.gridlines_y)
        if config.label_x:
            self._canvas.setLabel(axis="bottom", text=config.label_x)

        if config.label_y:
            self._canvas.setLabel(axis="left", text=config.label_x)

        self._add_widget(_w_graphics)

        # state
        self._curves: list[PlotDataItem] = []

    def _render_data(self, *args: list[Line | Scatter]) -> None:

        # try to be cheap if the optimization is enabled...
        data_updates: list[StatefulPlotView2D.Line | StatefulPlotView2D.Scatter] = args[0]
        if self._optim_fixed_data_order and len(data_updates) == len(self._curves):
            for data_new, plot_item in zip(data_updates, self._curves):
                plot_item.setData(x=data_new.x, y=data_new.y)
            return

        # otherwise do an expensive repaint.
        self._canvas.clear()
        self._curves = []
        if self._legend:
            self._legend.clear()

        for i, data in enumerate(data_updates):

            # setup common keyword args for the plot call
            color_auto = data.color if data.color else self._default_colors[i % len(self._default_colors)]
            kargs: dict[str, object] = dict(x=data.x, y=data.y)

            # pen=None required to avoid drawing connecting lines
            if isinstance(data, StatefulPlotView2D.Scatter):
                kargs["symbol"] = data.marker
                kargs["symbolSize"] = data.marker_size
                kargs["symbolBrush"] = color_auto
                self._curves.append(self._canvas.plot(pen=None, **kargs))

            elif isinstance(data, StatefulPlotView2D.Line):
                if data.marker:
                    kargs["symbol"] = data.marker
                    kargs["symbolSize"] = data.marker_size
                    kargs["symbolBrush"] = data.marker_color if data.marker_color else color_auto

                self._curves.append(self._canvas.plot(pen=dict(color=color_auto, width=data.line_width), **kargs))

            else:
                raise ValueError(f"unknown plot type received: '{type(data)}'")

            if self._legend and data.name:
                self._legend.addItem(self._curves[-1], data.name)
