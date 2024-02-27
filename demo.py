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


def resize_by_ratio(image: NDArray, ratio: float):
    """
    Provided a fractional ratio in the form of a floating point number, resize
    the image dimensions (width, height) by scaling each axis by the ratio.
    Note this does not include axes outside of the realm of width and height
    and the procedure assumes the axes are ordered as (height, width,
    a,b,c,...).

    Understand any fractional portions of the new resulting axes will be
    truncated and no rounding will occur.

    Example: Specifying `ratio=0.5` will halve each axis (height, width) and
    thus return an image 25% of the original size.

    :param image: ndarray encoded image
    :param ratio: a positive floating point number representing the resize ratio
    """
    shape = image.shape[:2]
    nshape = np.array(shape, dtype=np.float_) * ratio
    nshape = nshape.astype(np.uintp)  # purposely truncate / math floor
    nshape = tuple(nshape.tolist())
    return cv2.resize(image, nshape[::-1])


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

# expensive computations are completed prior. recall the purpose of this demo
# is to illustrate the fast rendering speed made possible by using PyQtGraph
# and PySide6 (along with several other packages). As such, realize slow
# rendering times are simply the result of a bottleneck in the code written
# into the callback interface. For an example, compare the rendering speed for
# when the resize slider is moved compared to when changes are specifed for the
# noise sigma parameter (resize performs more computation, making it slower in
# comparison).
img_test = resize_by_ratio(img_test, 10)
noise_image = np.random.randn(*(img_test.shape)).astype(np.int16)  # pyright: ignore


# define a callback with parameters that share names with the state keys
# provided to widgets
def callback_interface_example(rho, sigma, **kwargs):
    global noise_image, var_2_prev
    ratio = np.max([0.01, rho / 100])
    resized = resize_by_ratio(img_test, ratio)
    noise_slice = noise_image[: resized.shape[0], : resized.shape[1]]
    print(f"ratio: {ratio} new shape: {resized.shape}")
    if sigma != 0:
        return norm_uint8(resized.astype(np.int16) + (noise_slice * sigma))
    return norm_uint8(resized.astype(np.int16) + noise_slice)


image_viewer = vwr.VisionViewer()
trackbar_rho = vwr.LabeledTrackbar("rho", 0, 100, 2, 100)
trackbar_sigma = vwr.LabeledTrackbar("sigma", 0, 100, 2, 0)
ip = vwr.ImagePane(img_test, callback_interface_example)
ip.attach_widget(trackbar_rho)
ip.attach_widget(trackbar_sigma)
ip.force_flush()
image_viewer.add_pane(ip)
image_viewer.run()
