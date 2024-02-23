##################################################
# FILE: demo.py
# AUTHOR: SEAN TRONSEN (LANL)
#
# SUMMARY:
# The contents of this file are written with the intent to illustrate basic
# usage of the package utilities. By no means should it be expected to be
# comprehensive, but it provides a good foundation nonetheless.
#
# Should the reader have any questions, they are advised to first skim through
# the source code and read the inline documentation. For any questions that
# still remain, please get in touch with the author.
##################################################
##################################################
from numpy.typing import NDArray
import qtviewer as vwr
import numpy as np
import cv2


def norm_uint8(ndarray: NDArray):
    """
    Re-center the data between zero and one and then convert to 8-bit unsigned
    integers after a scaling operation.

    :param ndarray: any contiguous memory collection of ndarray encoded data
    """
    converted = ndarray.astype(np.float_)
    minval, maxval = np.min(converted), np.max(converted)
    top = ndarray - minval
    bottom = maxval - minval
    result = np.divide(top, bottom)
    return (255 * result).astype(np.uint8)


# load the sample image and ensure data type
img_test = cv2.imread("checkboard_non_planar.png").astype(np.uint8)
img_test = cv2.cvtColor(img_test, cv2.COLOR_BGR2GRAY)
img_test = norm_uint8(img_test)  # extra cautious / dtype paranoia


# define a callback with parameters that share names with the state keys
# provided to widgets
def callback_interface_example(yar, yar2, **kwargs):
    ratio = np.max([0.01, yar / 100])
    new_shape = np.array(img_test.shape[:2][::-1], dtype=np.uintp) * ratio
    new_shape = tuple(new_shape.astype(np.uintp).tolist())
    print(f"yarratio: {ratio} new shape: {new_shape}")
    resized = cv2.resize(img_test, new_shape, interpolation=cv2.INTER_LINEAR)
    if yar2 != 0:
        noise = np.random.randn(*(resized.shape)).astype(np.int16) * yar2  # pyright: ignore
        resized = norm_uint8(resized.astype(np.int16) + noise)
    return resized


# create test version (stateless)
image_viewer = vwr.VisionViewer()
trackbar = vwr.LabeledTrackbar("yar", 0, 10000, 2, 0)
trackbar2 = vwr.LabeledTrackbar("yar2", 0, 100, 2, 0)
ip = vwr.GraphicsPane(img_test, callback_interface_example)
ip.attach_widget(trackbar)
ip.attach_widget(trackbar2)
ip.force_flush()
image_viewer.add_pane(ip)
image_viewer.run()
