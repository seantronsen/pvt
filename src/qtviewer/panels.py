from typing import Callable, Optional
from PySide6.QtWidgets import QWidget, QGridLayout
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
        a parent method which will fail if not overridden/shadowed

        :raises [TODO:name]: [TODO:description]
        """
        raise NotImplementedError

    def force_flush(self):
        """
        more so here for possible future convenience.
        don't really have a use for this right now... maybe debugging later?
        depends on the obnoxious level of inheritance this aspires to.
        """
        self.state.flush()

    def attach_widget(self, widget: StatefulWidget):
        """
        bond a stateful widget with the pane state, updates to the control
        widget will now affect the pane if everything is configured properly

        :param widget: [TODO:description]
        """
        widget.attach(self.state)
        self.layout.addWidget(widget)


class ImagePane(StatefulPane):

    iv: pg.ImageView
    callback: Optional[Callable]

    def __init__(self, image, calculate: Optional[Callable] = None) -> None:
        super().__init__(self.update)
        self.iv = pg.ImageView()
        self.callback = calculate
        self.set_image(image)
        self.layout.addWidget(self.iv)

    def set_image(self, image):
        self.iv.setImage(image, autoRange=True, autoLevels=True, autoHistogramRange=True)

    def update(self, **args):
        """
        will fail if the user didn't specify a callback originally.
        """
        new_image = self.callback(**args)  # pyright: ignore
        self.set_image(new_image)


class GraphicsPane(StatefulPane):

    gp: pg.GraphicsView
    callback: Optional[Callable]
    img_item: pg.ImageItem
    vb: pg.ViewBox

    def __init__(self, image, calculate: Optional[Callable] = None) -> None:
        super().__init__(self.update)
        self.gp = pg.GraphicsView()
        self.layout.addWidget(self.gp)
        self.callback = calculate
        self.vb = pg.ViewBox()
        self.gp.setCentralWidget(self.vb)
        self.img_item = pg.ImageItem()
        print(f"the type is: {type(self.img_item)}")
        self.set_image(image)
        self.vb.setAspectLocked()
        self.vb.addItem(self.img_item)

    def set_image(self, image):
        self.img_item.setImage(image)

    def update(self, **args):
        """
        will fail if the user didn't specify a callback originally.
        """
        new_image = self.callback(**args)  # pyright: ignore
        self.set_image(new_image)
