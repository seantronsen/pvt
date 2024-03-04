from typing import Callable, Optional
import numpy as np
from PySide6.QtCore import QTimer
from numpy.typing import NDArray
import pyqtgraph as pg
from pyqtgraph import GraphicsLayoutWidget, LayoutWidget

from qtviewer.state import State
from qtviewer.widgets import StatefulWidget


class StatefulPane(LayoutWidget):
    """
    A simple pane/panel class that holds some state used for event handling /
    processing. Pane-level layouts are created vertically merely for simplicity
    as it allows for the maximum possible viewport for data analysis. Override
    the methods related to layout if different behavior is desired.

    TODO: CONSIDER CREATING A TIMED STATEFUL PANE SUBCLASS
    IMPORTANT: If using the timer for sequence data, provide

    IMPORTANT: For most intents and purposes, you will want to attach control
    widgets to the main application window and not to an instance of a display
    pane directly. Doing such allows a common state to be shared among all data
    display panes which allows for a state change within a control widget to
    affect all related data display panes (i.e. no need for duplicate control
    widgets).

    IMPORTANT: Data immutability is a property that should be abided by when
    defining callback functions. That is, the callback function should either
    return new or a modified copy of the original data. Failing to abide by
    this suggestion will require users to restart the application in order to
    re-obtain the initial state of the image later mutated by the callback.
    Specifically, the scope of this class and all derivations does not include
    managing the state of your data. It only includes management of the state
    of tuning parameters.

    NOTE: A base class for deriving implementations.
    """

    __state: State
    callback: Callable
    timer: Optional[QTimer]
    timer_ptr: np.uintp

    def __init__(self, data, callback: Optional[Callable] = None, fps: Optional[float] = None, **_) -> None:
        self.callback = callback if callback is not None else lambda **_: data  # potential name clash
        super().__init__()
        self.__state = State(self.update)
        if fps is not None:
            assert not fps < 0
            interval = int(0 if fps == 0 else 1000 / fps)
            self.timer_ptr = np.uintp(0)
            self.timer = QTimer()
            self.timer.timeout.connect(self.__timer_timeout)
            self.__state = State(lambda **kwargs: self.update(timer_ptr=self.timer_ptr, **kwargs))
            self.timer.start(interval)

    def __timer_timeout(self):
        """
        Exists to provide a timed update feature for animation / sequence data
        where new frames should be delivered at the specified interval.
        """
        self.timer_ptr += np.uintp(1)
        self.force_flush()

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
        self.__state.flush()

    def enchain(self, widget: StatefulWidget):
        """
        Bond a stateful widget with the pane state such that updates to this control
        widget will affect the pane when configured properly. Ensure proper
        configuration by naming a variable in the user specified call back
        function with the key value for the widget state component.

        :param widget: [TODO:description]
        """

        widget.attach(self.__state)

    def attach_widget(self, widget: StatefulWidget):
        """
        Enchain the pane state with the specified widget and position it
        beneath the main feature pane. Use this method when a control widget
        should be directly associated with a specific data display pane.

        :param widget: [TODO:description]
        """
        self.enchain(widget)
        self.addWidget(widget)
        self.nextRow()


class ImagePane(StatefulPane):
    """
    A pane which can be used to display and analyze image data with a fast
    refresh rate. An initial image to display must be provided to the
    constructor along with an optional callback function which may be used to
    update the display.

    IMPORTANT: Image data should be normalized and converted to standard bytes
    (uint8). Note the underlying pyqtgraph library supports uint16 and small
    floats, but visualization works best and renders fastest for bytes.
    """

    iv: pg.ImageView

    def __init__(self, image: NDArray, calculate: Optional[Callable] = None, **kwargs) -> None:
        super().__init__(image, calculate, **kwargs)
        self.iv = pg.ImageView()
        self.addWidget(self.iv)

        # prepare for data display
        self.set_data(image)

    def set_data(self, *args):
        """
        OVERRIDE: See parent definition
        """
        self.iv.setImage(args[0], autoRange=True, autoLevels=True, autoHistogramRange=True)


class GraphicsPane(StatefulPane):
    """
    A more complicated to implement image pane which may display data at a
    faster FPS depending on the user's machine and operating system.
    Functionality dictates an initial image be provided to the constructor
    along with the user specified callback function. The callback function can
    be used to chaneg the currently display image.

    IMPORTANT: Image data should be normalized and converted to standard bytes
    (uint8). Note the underlying pyqtgraph library supports uint16 and small
    floats, but visualization works best and renders fastest for bytes.
    """

    iv: pg.ImageItem

    def __init__(self, image: NDArray, calculate: Optional[Callable] = None, **kwargs) -> None:
        super().__init__(self.update, calculate, **kwargs)

        self.iv = pg.ImageItem()

        # set up mod image view
        vb = pg.ViewBox()
        vb.setAspectLocked()
        vb.addItem(self.iv)
        gp = pg.GraphicsView()
        gp.setCentralWidget(vb)

        # prepare for data display
        self.set_data(image)
        self.addWidget(gp)

    def set_data(self, *args):
        """
        OVERRIDE: See parent definition
        """
        self.iv.setImage(args[0])


class Plot2DPane(StatefulPane):

    plots_window: pg.GraphicsLayoutWidget
    plotPrimary: pg.PlotItem

    def __init__(self, data: NDArray, calculate: Optional[Callable] = None, **kwargs) -> None:
        kflag = lambda x: kwargs.get(x) if kwargs.get(x) is not None else False
        super().__init__(data, calculate, **kwargs)

        # prepare the graphics layout
        self.plots_window = GraphicsLayoutWidget()
        self.plotPrimary = self.plots_window.addPlot(title=kwargs.get("title"))
        if kflag("legend"):
            self.plotPrimary.addLegend()

        self.plotPrimary.setLogMode(x=kflag("logx"), y=kflag("logy"))
        self.plotPrimary.showGrid(x=kflag("gridx"), y=kflag("gridy"))

        plot_args = dict()
        plot_args["pen"] = None if kflag("scatter") else 'g'
        plot_args["symbol"] = 't' if kflag("scatter") else None
        plot_args["symbolSize"] = 10
        plot_args["symbolBrush"] = (0, 255, 0, 90)

        self.curve = self.plotPrimary.plot(**plot_args)
        self.set_data(data)
        self.addWidget(self.plots_window)

    def set_data(self, *args):
        """
        OVERRIDE: See parent definition.

        Provide an NDArray either of shape (N,) or (N, 2). When the first case
        is true, the plotter assumes you have provided the y-coordinates and a
        uniform spacing of x-coordinates will be generated for you. In the
        second case, it is assumed that both kinds of points were provided.

        :param data: [TODO:description]
        """

        self.curve.setData(args[0])
