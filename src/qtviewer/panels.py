from numpy.typing import NDArray
from pyqtgraph import GraphicsLayoutWidget, LayoutWidget, PlotDataItem
from qtviewer.decorators import performance_log
from qtviewer.identifier import IdManager
from qtviewer.state import State
from qtviewer.widgets import StatefulWidget
from typing import Callable, Dict, List, Optional
import numpy as np
import pyqtgraph as pg
import pyqtgraph.opengl as pggl
from PySide6.QtWidgets import QLabel, QSizePolicy, QWidget


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
        assert callback is not None
        super().__init__(**kwargs)
        self.identifier = f"{self.__class__.__name__}-{IdManager().generate_identifier()}"
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # pyright: ignore
        self.callback = callback
        self.pane_state = State(self.update)
        self.identifier_label = QLabel(self.identifier)
        # self.identifier_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed) # pyright: ignore
        self.addWidget(self.identifier_label)
        self.nextRow()

    @performance_log
    def update(self, **kwargs):
        """
        This function is the callback provided to the State instance and is
        executed on each state change. The user specified callback is executed
        by this callback. If you wish to exist in user land, don't worry about
        anything other than the one callback you're required to define.
        """
        data = self.callback(**kwargs)
        self.set_data(data)

    def set_data(self, *args):
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

    def __init__(self, callback: Callable, autoRange=True, autoLevels=True, autoHistogramRange=True, **kwargs) -> None:
        """
        Constructor function

        :param callback: user defined callback responsible for yielding new data for display
        :param autoRange: flag which specifies whether display zoom and panning
        should be reset on each render. disable this if you want to focus on a
        particular set of pixels for any frame to be displayed.

        :param autoLevels: flag which specifies whether to update the intensity
        range when displaying the image (normalization)

        :param autoHistogramRange: flag which specifies whether the histogram
        widget is scaled to fit the data.
        """
        super().__init__(callback, **kwargs)
        self.dargs = dict(autoRange=autoRange, autoLevels=autoLevels, autoHistogramRange=autoHistogramRange)
        self.displaypane = pg.ImageView()
        self.addWidget(self.displaypane)

    def set_data(self, *args):
        self.displaypane.setImage(args[0], **self.dargs)


class BasePlot2DPane(StatefulPane):
    """
    The Base/Abstract class in which all 2D plotting panes are derived. The
    purpose of this class is merely to provide a basic set up for inheritors
    and reduce the amount of typing required to add new 2D plot kinds in the
    future.
    """

    plot_item: pg.PlotItem
    plot_layout: pg.GraphicsLayoutWidget
    curves: List[PlotDataItem]
    plot_args: Dict

    def __init__(self, callback: Callable, **kwargs) -> None:
        kflag = lambda x: kwargs.get(x) if kwargs.get(x) is not None else False
        super().__init__(callback, **kwargs)

        # prepare the graphics layout
        self.plot_layout = GraphicsLayoutWidget()
        self.plot_item = self.plot_layout.addPlot(title=kwargs.get("title"))
        if kflag("legend"):
            self.plot_item.addLegend()

        self.plot_item.setLogMode(x=kflag("logx"), y=kflag("logy"))
        self.plot_item.showGrid(x=kflag("gridx"), y=kflag("gridy"))
        self.curves = []
        self.plot_args = {}
        self.addWidget(self.plot_layout)

    def __reinitialize_curves(self, ncurves: int):
        """
        If the number of curves to plot on the next render differs from the
        number currently known, reinitialize the curves collection such that it
        holds the required number of curve instances.

        :param ncurves: the number of required curves to plot
        """
        for x in self.curves:
            self.plot_item.removeItem(x)
        self.curves = []
        for x in range(ncurves):
            self.curves.append(self.plot_item.plot(**self.plot_args))

    def set_data(self, *args):
        """
        OVERRIDE: See parent definition.
        Use the provided data to update the curves on the 2D PlotView.

        IMPORTANT: Ensure data provided to other methods is formatted
        appropriately. Valid formats are:
            - (N,)
            - (N,2)
            - (M,N)
            - (M,N,2)

        :param args[0]: an ndarray of data points
        """
        data: NDArray = args[0]
        n_curves = data.shape[0]
        if n_curves != len(self.curves):
            self.__reinitialize_curves(n_curves)

        for i in range(n_curves):
            self.curves[i].setData(data[i])


class Plot2DLinePane(BasePlot2DPane):
    """
    Display a pane which draws all provided data as a set of one or more
    lines/curves.
    """

    def __init__(self, callback: Callable, **kwargs) -> None:
        super().__init__(callback, **kwargs)
        self.plot_args["pen"] = 'g'


class Plot2DScatterPane(BasePlot2DPane):
    """
    Display a pane which draws all provided data as a set of one or more
    scatter plots.
    """

    def __init__(self, callback: Callable, **kwargs) -> None:
        super().__init__(callback, **kwargs)
        self.plot_args["pen"] = None
        self.plot_args["symbol"] = 't'
        self.plot_args["symbolSize"] = 10
        self.plot_args["symbolBrush"] = (0, 255, 0, 90)


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
        self.plot_space.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # pyright: ignore
        self.plot_space.setCameraPosition(distance=100)
        gx = pggl.GLGridItem()
        gx.rotate(90, 0, 1, 0)
        gx.translate(-10, 0, 0)
        # gx.scale(x,y,z)
        # g.setDepthValue(10)  # draw grid after surfaces since they may be translucent
        self.plot_space.addItem(gx)
        gy = pggl.GLGridItem()
        gy.rotate(90, 1, 0, 0)
        gy.translate(0, -10, 0)
        self.plot_space.addItem(gy)
        gz = pggl.GLGridItem()
        gz.translate(0, 0, -10)
        self.plot_space.addItem(gz)
        self.plot_surface = pggl.GLSurfacePlotItem(
            shader='heightColor', color=(0, 0.5, 0, 0.9), computeNormals=False, smooth=True, glOptions="additive"
        )
        self.plot_space.addItem(self.plot_surface)
        self.addWidget(self.plot_space)

    def set_data(self, *args):
        if len(args) == 3:
            x, y, z = args
            self.plot_surface.setData(x=x, y=y, z=z)
        else:
            z = args[0]
            x = np.arange(z.shape[1]) - 10
            y = np.arange(z.shape[0]) - 10
            self.plot_surface.setData(x=x, y=y, z=args[0])


# ## CITATION: THIS IS PULLED DIRECTLY FROM PYQTGRAPH'S EXAMPLES
# ## Simple surface plot example
# ## x, y values are not specified, so assumed to be 0:50
# z = pg.gaussianFilter(np.random.normal(size=(50, 50)), (1, 1))
# p1 = gl.GLSurfacePlotItem(z=z, shader='shaded', color=(0.5, 0.5, 1, 1))
# p1.scale(16.0 / 49.0, 16.0 / 49.0, 1.0)
# p1.translate(-18, 2, 0)
# w.addItem(p1)
#
#
# ## Animated example
# ## compute surface vertex data
# cols = 90
# rows = 100
# x = np.linspace(-8, 8, cols + 1).reshape(cols + 1, 1)
# y = np.linspace(-8, 8, rows + 1).reshape(1, rows + 1)
# d = (x**2 + y**2) * 0.1
# d2 = d**0.5 + 0.1
#
# ## precompute height values for all frames
# phi = np.arange(0, np.pi * 2, np.pi / 20.0)
# z = np.sin(d[np.newaxis, ...] + phi.reshape(phi.shape[0], 1, 1)) / d2[np.newaxis, ...]
#
#
# ## create a surface plot, tell it to use the 'heightColor' shader
# ## since this does not require normal vectors to render (thus we
# ## can set computeNormals=False to save time when the mesh updates)
# p4 = gl.GLSurfacePlotItem(x=x[:, 0], y=y[0, :], shader='heightColor', computeNormals=False, smooth=False)
# p4.shader()['colorMap'] = np.array([0.2, 2, 0.5, 0.2, 1, 1, 0.2, 0, 2])
# p4.translate(10, 10, 0)
# w.addItem(p4)
#
# index = 0
#
#
# def update():
#     global p4, z, index
#     index -= 1
#     p4.setData(z=z[index % z.shape[0]])
#
#
# timer = QtCore.QTimer()
# timer.timeout.connect(update)
# timer.start(30)
#
# if __name__ == '__main__':
#     pg.exec()
