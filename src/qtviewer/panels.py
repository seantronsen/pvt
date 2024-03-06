from numpy.typing import NDArray
from pyqtgraph import GraphicsLayoutWidget, LayoutWidget, PlotDataItem
from qtviewer.decorators import performance_log
from qtviewer.state import State
from qtviewer.widgets import StatefulWidget
from qtviewer.exceptions import PlotDataValueError
from typing import Callable, Dict, List, Optional
import numpy as np
import pyqtgraph as pg


class StatefulPane(LayoutWidget):
    """
    A simple pane/panel class that holds some state used for event handling /
    processing. The intended design has it such that this class acts as a base
    for more specific implementations to derive from. Pane-level layouts are
    created vertically merely for simplicity as it allows for the maximum
    possible viewport for data analysis. Override the methods related to layout
    if different behavior is desired.

    IMPORTANT: Data immutability is a property that should be abided by when
    defining callback functions. That is, the callback function should either
    return new or a modified copy of the original data. Failing to abide by
    this suggestion will require users to restart the application in order to
    re-obtain the initial state of the image later mutated by the callback.
    Specifically, the scope of this class and all derivations does not include
    managing the state of your data. It only includes management of the state
    of tuning parameters.

    IMPORTANT: For most intents and purposes, you will want to attach control
    widgets to the main application window and not to an instance of a display
    pane directly. Doing such allows a common state to be shared among all data
    display panes which allows for a state change within a control widget to
    affect all related data display panes (i.e. no need for duplicate control
    widgets).
    """

    __state: State
    callback: Callable

    def __init__(self, data, callback: Optional[Callable] = None, **_) -> None:
        self.callback = callback if callback is not None else lambda **_: data
        super().__init__()
        self.__state = State(self.update)

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


class Plot2DPane(StatefulPane):

    plots_window: pg.GraphicsLayoutWidget
    plotPrimary: pg.PlotItem
    curves: List[PlotDataItem]
    plot_args: Dict

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
        self.plot_args = plot_args
        self.curves = []
        self.set_data(data)
        self.addWidget(self.plots_window)

    # TODO: ensure this doesn't cost that much time. otherwise remove and
    # provide a format guide for users. this viewer is concerned with speed and
    # less so with formatting hand holding.
    @staticmethod
    def format_data(data: NDArray):
        """
        Ensure data provided to other methods is formatted appropriately.

        Valid formats are:
            - (N,)
            - (N,2)
            - (M,N)
            - (M,N,2)

        :param data: an ndarray of data points
        :raises PlotDataValueError: error raised when the provided data cannot
        be formatted with simple efforts.
        """
        if len(data.shape) == 2 and data.shape[0] == 1:
            data = data.reshape(-1)
        if len(data.shape) == 1:
            data = data[np.newaxis, ...]
        # convert from (N,2) to (1,N,2)
        if len(data.shape) == 2 and data.shape[1] == 2:
            data = data[np.newaxis, ...]
        # ensure valid shape for 3D ndarray
        if len(data.shape) == 3 and data.shape[2] != 2:
            raise PlotDataValueError(data.shape)

        return data

    def set_data(self, *args):
        """
        OVERRIDE: See parent definition.

        Use the provided data to update the curves (PlotDataItem's) on the 2D
        PlotView. See format related methods for details on what constitutes a
        valid format.

        :param data: an ndarray of data points
        """
        data: NDArray = args[0]
        data = self.format_data(data)

        n_curves = data.shape[0]
        if n_curves != len(self.curves):
            for x in self.curves:
                self.plotPrimary.removeItem(x)
            self.curves = []
            for x in range(n_curves):
                self.curves.append(self.plotPrimary.plot(**self.plot_args))

        for i in range(n_curves):
            self.curves[i].setData(data[i])
