from PySide6 import QtGui
from numpy.typing import NDArray
from pyqtgraph import GraphicsLayoutWidget, LayoutWidget, PlotDataItem
from pyqtgraph.colormap import ColorMap
from pvt.decorators import performance_log
from pvt.identifier import IdManager
from pvt.state import State
from pvt.widgets import StatefulWidget
from typing import Callable, Dict, List, Optional, Any
import numpy as np
import pyqtgraph as pg
import pyqtgraph.opengl as pggl
from PySide6.QtWidgets import QLabel, QSizePolicy
from pyvistaqt import BackgroundPlotter


class StatefulPane(LayoutWidget):
    """
    A simple pane/panel class that holds some state used for event handling /
    processing. The intended design has it such that this class acts as a base
    for more specific implementations to derive from. Pane-level layouts are
    created vertically merely for simplicity as it allows for the maximum
    possible viewport for data analysis. Override the methods related to layout
    if different behavior is desired.

    IMPORTANT: Data immutability is a property that should be abided by when
    defining callback functions. Management of specific data is external to the
    design scope of this class.

    IMPORTANT: For most intents and purposes, attach control widgets to the
    main application window and not a derivation of this class. Doing such
    allows a common state to be shared among all data display panes and allows
    for a state change within a control widget to be reflected across all
    related data display panes (i.e. no need for duplicate control widgets).
    """

    pane_state: State
    callback: Callable
    identifier: str

    def __init__(self, callback: Optional[Callable] = None, **kwargs) -> None:
        """
        Initialize an instance of the class.

        :param callback: A callback to update the rendered data.
        """
        assert callback is not None
        super().__init__(**kwargs)
        self.identifier = f"{self.__class__.__name__}-{IdManager().generate_identifier()}".lower()
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # pyright: ignore
        self.callback = callback
        self.pane_state = State(self.update)
        self.identifier_label = QLabel(self.identifier)
        self.identifier_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)  # pyright: ignore
        self.addWidget(self.identifier_label)
        self.nextRow()

    def update(self, **kwargs):
        """
        This function is the callback provided to the State instance and is
        executed on each state change. The user specified callback is executed
        by this callback. If you wish to exist in user land, don't worry about
        anything other than the one callback you're required to define.
        """
        data = self.compute_data(**kwargs)
        self.__render_data(data)

    @performance_log(event="compute")
    def compute_data(self, **kwargs):
        """
        Execute the user specified callback and return the resulting data.

        This function is a general abstraction which exists merely to simplify
        optional performance logging.
        """
        return self.callback(**kwargs)

    @performance_log(event="render")
    def __render_data(self, *args):
        """
        Execute the widget render routines and repaint the display.

        This function is a general abstraction which exists merely to simplify
        optional performance logging.
        """
        self.render_data(*args)

    def render_data(self, *args):
        """
        IMPORTANT: A parent method which will fail if not overridden/shadowed.

        :raises [TODO:name]: [TODO:description]
        """
        raise NotImplementedError

    def force_flush(self):
        """
        more so here for possible future convenience. don't really have a use
        for this right now... maybe debugging later? depends on the obnoxious
        level of inheritance object oriented programming can aspire to.

        """
        self.pane_state.flush()

    def enchain(self, widget: StatefulWidget):
        """
        Bond a stateful widget with the pane state such that updates to this control
        widget will affect the pane when configured properly. Ensure proper
        configuration by naming a variable in the user specified call back
        function with the key value for the widget state component.

        :param widget: [TODO:description]
        """

        widget.attach(self.pane_state)

    def attach_widget(self, widget: StatefulWidget):
        """
        Enchain the pane state with the specified widget and position it
        beneath the feature pane. Use this method when a control widget
        should be directly associated with a specific data display pane.

        :param widget: [TODO:description]
        """
        self.enchain(widget)
        widget.setParent(self)
        self.addWidget(widget)
        self.nextRow()


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


class Pvt3DPlotPane(StatefulPane):
    """
    This is a work in progress integration. One of the authors will add onto
    and clean this up within the week (Sun Apr  7 06:32:06 PM MDT 2024) since
    they require as a component of a project demonstration.


    IMPORTANT: This is a **really** basic integration implementation which is
    meant solely to get the ball rolling. There has been little in the way of
    performance testing and/or quantification. In practice, the noisy sphere
    demo reached a maximum of 144 FPS (rendering bottleneck, compute max was
    almost 4,000 FPS). It allows the user to do whatever they want as long as
    they know PyVista. The authors are working on learning more about this
    library and additional abstractions / API simplifications will come with
    time.
    """

    def __init__(self, callback: Optional[Callable] = None, **kwargs) -> None:
        super().__init__(callback, **kwargs)
        self.pvtp = BackgroundPlotter(
            show=False,
            update_app_icon=False,
            allow_quit_keypress=False,
            editor=False,
            auto_update=False,
            title=None,
            menu_bar=False,
        )
        # self.addWidget(self.pvtp.main_menu)
        self.addWidget(self.pvtp)

    def __getattr__(self, attr: str):
        return getattr(self.pvtp, attr)

    def render_data(self, *_):
        self.pvtp.update()
        self.pvtp.render()


# SWITCHING OVER TO PYVISTA FOR 3D GRAPHICS SOON
# unfortunately, I just don't have the time to create a full 3D solution and
# integrating a new library which shares a ton of features with ParaView seems
# like an obvious choice.
class Plot3DPane(StatefulPane):
    """
    An OpenGL-enabled 3D plotting pane. The current documentation for PyQtGraph
    reveals features related to this plotting technique remain in early
    development and will improve over time.

    Quoting the current capabilities within the backticks:

    ```
    - 3D view widget with zoom/rotate controls (mouse drag and wheel)
    - Scenegraph allowing items to be added/removed from scene with per-item
      transformations and parent/child relationships.
    - Triangular meshes
    - Basic mesh computation functions: isosurfaces, per-vertex normals
    - Volumetric rendering item
    - Grid/axis items

    ```
    """

    plot_space: pggl.GLViewWidget
    plot_surface: pggl.GLSurfacePlotItem

    def __init__(self, callback: Callable, **kwargs) -> None:
        """
        borrowed" directly from the demos"
        needs:
            - auto scale grid sizes to data.
        """
        super().__init__(callback, **kwargs)
        self.plot_space = pggl.GLViewWidget()
        self.plot_space.setCameraPosition(distance=100)
        gx = pggl.GLGridItem()
        gx.rotate(90, 0, 1, 0)
        gx.translate(-10, 0, 10)
        # gx.scale(x,y,z)
        # g.setDepthValue(10)  # draw grid after surfaces since they may be translucent
        self.plot_space.addItem(gx)
        gy = pggl.GLGridItem()
        gy.rotate(90, 1, 0, 0)
        gy.translate(0, -10, 10)
        self.plot_space.addItem(gy)
        gz = pggl.GLGridItem()
        # gz.translate(0, 0, -10)
        self.plot_space.addItem(gz)
        self.plot_surface = pggl.GLSurfacePlotItem(
            shader='heightColor', color=(0, 0.5, 0, 0.9), computeNormals=False, smooth=True, glOptions="additive"
        )
        self.plot_space.addItem(self.plot_surface)
        self.addWidget(self.plot_space)

    def render_data(self, *args):
        if len(args) == 3:
            x, y, z = args
            self.plot_surface.setData(x=x, y=y, z=z)
        else:
            z = args[0]
            x = np.arange(z.shape[1]) - 10
            y = np.arange(z.shape[0]) - 10
            self.plot_surface.setData(x=x, y=y, z=args[0])
