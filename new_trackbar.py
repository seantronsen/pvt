"""
Tests the speed of image updates for an ImageItem and RawImageWidget.
The speed will generally depend on the type of data being shown, whether
it is being scaled and/or converted by lookup table, and whether OpenGL
is used by the view widget
"""

from typing import Callable, Dict, Optional
from PySide6.QtWidgets import QVBoxLayout, QWidget, QApplication, QSlider, QLabel, QGridLayout
from PySide6.QtCore import Qt
import pyqtgraph as pg
import numpy as np
import os
import cv2

pg.setConfigOption('imageAxisOrder', 'row-major')  # best performance


def run_pyqtgraph_examples():
    import pyqtgraph.examples

    pyqtgraph.examples.run()  # pyright: ignore


# alright, let's fucking make it.


"""

the expected callbcak interface is
function callback(state, *rest):
    // do stuff using the state and the other expected params

"""


class State:
    __storage: Dict
    onUpdate: Callable

    def __init__(
        self,
        callback,
        init: Optional[Dict] = None,
    ) -> None:
        self.__storage = init if init is not None else {}
        self.onUpdate = callback

    def __getitem__(self, key):
        return self.__storage.get(key)

    def __setitem__(self, key, value):
        self.__storage[key] = value

    def flush(self):
        self.onUpdate(**self.__storage)


class VisionViewer:

    app: QApplication
    panel: QWidget

    def __init__(self, title="CV Image Viewer") -> None:

        self.app = QApplication([])
        self.panel = QWidget()
        self.panel.setWindowTitle(title)
        layout = QVBoxLayout()
        self.panel.setLayout(layout)

    def add_pane(self, pane: QWidget):
        layout = self.panel.layout()
        layout.addWidget(pane)  # pyright: ignore

    def run(self):
        self.panel.show()
        self.app.exec()


class StatefulWidget(QWidget):

    state: Optional[State]
    key: str

    def __init__(self, key, init) -> None:
        self.key = key
        self.init = init
        self.state = None
        super().__init__()

    def attach(self, state: State):
        self.state = state
        self.state[self.key] = self.init

    def state_update(self, value):
        """
        will fail if not attached to a parent state
        i.e. self.state == None

        :param value [TODO:type]: [TODO:description]
        """
        self.state[self.key] = value  # pyright: ignore
        self.state.flush()  # pyright: ignore


class LabeledTrackbar(StatefulWidget):
    label: str
    s: QSlider
    t: QLabel

    # instantiated with a detached state for future integration ergonomics
    def __init__(self, label: str, start: int, stop: int, step: int, init: int, key: Optional[str] = None) -> None:
        assert init < stop + 1 and init > start - 1
        skey = key if key is not None else label
        super().__init__(skey, init)
        self.label = label
        self.s = QSlider(Qt.Horizontal)  # pyright: ignore
        self.t = QLabel()
        l, s, t = self.label, self.s, self.t
        s.setMinimum(start)
        s.setMaximum(stop)
        s.setSingleStep(step)
        t.setText(f"{l}: {s.value()}")
        s.valueChanged.connect(self.on_change)

        layout = QGridLayout()
        self.setLayout(layout)
        layout.addWidget(s, 0, 0)  # left
        layout.addWidget(t, 0, 6)  # far-right

    def on_change(self, *_):
        value = self.s.value()
        self.t.setText(f"{self.label}: {value}")
        self.state_update(value)


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

    def force_flush(self):
        """
        more so here for possible future convenience.
        don't really have a use for this right now... maybe debugging later?
        depends on the obnoxious level of inheritance this aspires to.
        """
        self.state.flush()


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

    def force_flush(self):
        """
        more so here for possible future convenience.
        don't really have a use for this right now... maybe debugging later?
        depends on the obnoxious level of inheritance this aspires to.
        """
        self.state.flush()


"""
callback interface

for the image pane, the callback should take a series of integer, float, or
string kwargs and return an image. if you wish to display images as a series,
then one kwarg could be an indexer variable n whose slider chooses a new index.
on update, this will cause a new image to be displayed.


"""

img_test = cv2.imread(os.path.expandvars("$HOME/checkboard_non_planar.png"))
img_test = np.array(img_test, dtype=np.uint8)


def norm_uint8(ndarray):
    converted = ndarray.astype(np.float_)
    minval, maxval = np.min(converted), np.max(converted)
    top = ndarray - minval
    bottom = maxval - minval
    result = np.divide(top, bottom)
    return (255 * result).astype(np.uint8)


def bad_callback(yar, yar2, **kwargs):
    ratio = np.max([0.01, yar / 100])
    new_shape = np.array(img_test.shape[:2][::-1], dtype=np.uintp) * ratio
    new_shape = tuple(new_shape.astype(np.uintp).tolist())
    print(f"yarratio: {ratio} new shape: {new_shape}")
    resized = cv2.resize(img_test, new_shape, interpolation=cv2.INTER_LINEAR)
    if yar2 != 0:
        noise = np.random.randn(*(resized.shape)).astype(np.int16) * yar2
        resized = norm_uint8(resized.astype(np.int16) + noise)
    return resized


# create test version (stateless)
image_viewer = VisionViewer()
trackbar = LabeledTrackbar("yar", 0, 10000, 2, 0)
trackbar2 = LabeledTrackbar("yar2", 0, 100, 2, 0)
ip = GraphicsPane(img_test, bad_callback)
ip.attach_widget(trackbar)
ip.attach_widget(trackbar2)
ip.force_flush()
image_viewer.add_pane(ip)
image_viewer.run()
