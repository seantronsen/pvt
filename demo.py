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
import cv2
import numpy as np
import os
import qtviewer as vwr
import time
import sys


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


def demo_image_viewer():
    # load the sample image and ensure data type
    img_test = cv2.imread("sample-media/checkboard_non_planar.png").astype(np.uint8)
    img_test = cv2.cvtColor(img_test, cv2.COLOR_BGR2GRAY)
    img_test = norm_uint8(img_test)  # extra cautious / data type paranoia

    # IMPORTANT: Expensive and avoidable computations should be completed prior for
    # best results. Slow rendering times result from a bottleneck in the code
    # written into a provided callback function.
    #
    # EXAMPLE: Compare the rendering speed for when the resize slider is moved
    # versus when the sigma parameter is updated (resize performs more
    # computation in this case, making it slower in comparison).
    img_test_small = img_test.copy()
    img_test = resize_by_ratio(img_test, 10)
    noise_image = np.random.randn(*(img_test.shape)).astype(np.int8)  # pyright: ignore

    # Define a callback with parameters whose names are a subset of the state keys
    # specified for the control widgets.
    #
    # IMPORTANT: Ensure both the args and kwargs parameters are specified, even if
    # they remain unused. Doing such allows the interface to remain generic and
    # simple for top level controls. More specifically, parameters associated with
    # global (top-level) control widgets are passed to the callbacks for all top
    # level data display panels, even if those panels make no use of the
    # parameters. Put most simply, specifying args and kwargs allows any display
    # pane to ignore extra parameters without crashing the program from failing to
    # adhere to the defined functional interface.
    def callback_example(rho, sigma, **kwargs):
        ratio = np.max([0.001, rho / 1000])
        resized = resize_by_ratio(img_test, ratio)
        noise_slice = noise_image[: resized.shape[0], : resized.shape[1]]
        result = resized + (noise_slice * sigma)
        print(f"resolution: ({result.shape[0]:05d}, {result.shape[1]:05d})")
        return result

    def callback_example_2(sigma, **kwargs):
        noise_slice = noise_image[: img_test_small.shape[0], : img_test_small.shape[1]]
        result = img_test_small + (noise_slice * sigma)
        print(f"resolutionb: ({result.shape[0]:05d}, {result.shape[1]:05d})")
        return result

    # define the viewer interface and run the application
    # happy tuning / visualizing!
    image_viewer = vwr.VisionViewer()
    trackbar_rho = vwr.ParameterTrackbar("rho", 0, 100, 1, 50)
    trackbar_sigma = vwr.ParameterTrackbar("sigma", 0, 100, 2, 0)
    ip = vwr.ImagePane(img_test, callback_example)
    ip2 = vwr.ImagePane(img_test_small, callback_example_2)
    image_viewer.add_mosaic([[ip, ip2], [trackbar_rho], [trackbar_sigma]])
    image_viewer.run()


def demo_plot_viewer():

    def callback(nsamples, sigma=1, omega=1, phasem=1, timer_ptr=0, **kwargs):
        cphase = timer_ptr / (2 * np.pi)
        cphase *= phasem / 10
        sinusoid = np.sin((np.linspace(0, omega * 2 * np.pi, nsamples) + cphase))
        noise = np.random.randn(nsamples)
        result = sinusoid + (noise[:nsamples] * (sigma / 10))
        waves = 5
        return np.array([result] * waves) + np.arange(waves).reshape(-1, 1)

    viewer = vwr.PlotViewer(title="Multiple Plots: A Visual Illustration of Signal Aliasing")
    trackbar_n = vwr.ParameterTrackbar("nsamples", 100, 1000, 100)
    trackbar_sigma = vwr.ParameterTrackbar("sigma", 0, 30, 1)
    trackbar_omega = vwr.ParameterTrackbar("omega", 1, 50, 1, 50)
    trackbar_phasem = vwr.ParameterTrackbar("phasem", 1, 100, 1)
    animated_plot = vwr.Animator(fps=60, contents=vwr.Plot2DPane(callback(1000), callback))
    viewer.add_panes(animated_plot.anim_content, trackbar_n, trackbar_omega, trackbar_phasem, trackbar_sigma)
    viewer.run()


def demo_huge_trackbar_performance():
    """
    An example to illustrate that trackbars with extreme ranges of values are
    slow and cumbersome, even when used alone.
    """

    viewer = vwr.PlotViewer(title="Multiple Plots: A Visual Illustration of Signal Aliasing")
    trackbar_n = vwr.ParameterTrackbar("nsamples", 0, 10000, 1)
    viewer.add_panes(trackbar_n)
    viewer.run()


if __name__ == "__main__":
    os.environ["VIEWER_PERF_LOG"] = "1"
    options = {}
    options[demo_image_viewer.__name__] = demo_image_viewer
    options[demo_plot_viewer.__name__] = demo_plot_viewer
    options[demo_huge_trackbar_performance.__name__] = demo_huge_trackbar_performance
    if len(sys.argv) >= 2:
        options[sys.argv[1]]()
    else:
        demo_plot_viewer()
