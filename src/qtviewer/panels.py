from typing import Callable, Optional
from PySide6.QtWidgets import QWidget, QGridLayout
# from qtpy.QtWidgets import QWidget, QGridLayout
from numpy.typing import NDArray
import pyqtgraph as pg

from qtviewer.state import State
from qtviewer.widgets import StatefulWidget


class StatefulPane(QWidget):

    state: State
    layout: QGridLayout

    def __init__(self, callback) -> None:
        super().__init__()
        self.state = State(callback)
        self.layout = QGridLayout()
        self.setLayout(self.layout)

    def update(self, **_):
        """
        IMPORTANT: A parent method which will fail if not overridden/shadowed.

        This function is the callback provided to the State instance and is
        executed on each state change. The user specified callback is executed
        by this callback. If you wish to exist in user land, don't worry about
        anything other than the one callback you're required to define as this
        detail isn't important to the experience.

        """
        raise NotImplementedError

    def force_flush(self):
        """
        more so here for possible future convenience. don't really have a use
        for this right now... maybe debugging later? depends on the obnoxious
        level of inheritance object oriented programming can aspire to.

        """
        self.state.flush()

    def attach_widget(self, widget: StatefulWidget):
        """
        Bond a stateful widget with the pane state such that updates to this control
        widget will affect the pane if configured properly. Ensure proper
        configuration by naming a variable in the user specified call back
        function with the key value for the widget state component.

        Attached widgets will appear beneath the main feature pane.

        :param widget: [TODO:description]
        """
        widget.attach(self.state)
        self.layout.addWidget(widget)


class ImagePane(StatefulPane):
    """
    A pane which can be used to display and analyze image data with a fast
    refresh rate. Functionality dictates an initial image be provided to the
    constructor along with the user specified callback function. The callback
    function can be used to chaneg the currently display image.

    IMPORTANT: Data immutability is a property that should be abided by when
    defining the callback function. That is, the callback function should
    either return entirely new data or a modified copy of the original data.
    Failing to abide by this suggestion will require users to restart the
    application in order to re-obtain the initial state of the image later
    mutated by the callback.

    IMPORTANT: Image data should be normalized and converted to standard bytes
    (uint8). Note the underlying pyqtgraph library supports uint16 and small
    floats, but visualization works best and renders fastest for bytes.
    """

    iv: pg.ImageView
    callback: Optional[Callable]

    def __init__(self, image: NDArray, calculate: Optional[Callable] = None) -> None:
        super().__init__(self.update)
        self.iv = pg.ImageView()
        self.callback = calculate
        self.set_image(image)
        self.layout.addWidget(self.iv)

    def set_image(self, image: NDArray):
        """
        Set the currently displayed image and immediately render the update on
        the pane.

        :param image: a new image to render encoded as an ndarray
        """
        self.iv.setImage(image, autoRange=True, autoLevels=True, autoHistogramRange=True)

    def update(self, **args):
        new_image = self.callback(**args)  # pyright: ignore
        self.set_image(new_image)


class GraphicsPane(StatefulPane):
    """
    A more complicated to implement image pane which may display data at a
    faster FPS depending on the user's machine and operating system.
    Functionality dictates an initial image be provided to the constructor
    along with the user specified callback function. The callback function can
    be used to chaneg the currently display image.

    IMPORTANT: Data immutability is a property that should be abided by when
    defining the callback function. That is, the callback function should
    either return entirely new data or a modified copy of the original data.
    Failing to abide by this suggestion will require users to restart the
    application in order to re-obtain the initial state of the image later
    mutated by the callback.

    IMPORTANT: Image data should be normalized and converted to standard bytes
    (uint8). Note the underlying pyqtgraph library supports uint16 and small
    floats, but visualization works best and renders fastest for bytes.

    """

    gp: pg.GraphicsView
    callback: Optional[Callable]
    img_item: pg.ImageItem
    vb: pg.ViewBox

    def __init__(self, image: NDArray, calculate: Optional[Callable] = None) -> None:
        super().__init__(self.update)
        self.gp = pg.GraphicsView()
        self.layout.addWidget(self.gp)
        self.callback = calculate
        self.vb = pg.ViewBox()
        self.gp.setCentralWidget(self.vb)
        self.img_item = pg.ImageItem()
        self.set_image(image)
        self.vb.setAspectLocked()
        self.vb.addItem(self.img_item)

    def set_image(self, image: NDArray):
        """
        Set the currently displayed image and immediately render the update on
        the pane.

        :param image: a new image to render encoded as an ndarray
        """
        self.img_item.setImage(image)

    def update(self, **args):
        new_image = self.callback(**args)  # pyright: ignore
        self.set_image(new_image)
