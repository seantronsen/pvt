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
import cv2
import numpy as np
import os
import qtviewer as vwr
import sys
from demo_utils import *


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

    def callback(nsamples=1000, sigma=1, omega=1, phasem=1, timer_ptr=0, **kwargs):
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
    animated_plot = vwr.Animator(fps=60, contents=vwr.Plot2DPane(callback=callback))
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


def demo_3d_prototype():

    viewer = vwr.PlotViewer(title="Multiple Plots: A Visual Illustration of Signal Aliasing")

    def callback(hm=1, sigma=1, **_):
        gaussian = cv2.getGaussianKernel(20, sigma=sigma)
        gaussian = gaussian * gaussian.T  # pyright: ignore
        return gaussian * hm

    d3plot = vwr.Plot3DPane(callback=callback)
    t_hm = vwr.ParameterTrackbar("hm", 1, 10000, 1, 100)
    t_sigma = vwr.ParameterTrackbar("sigma", 0, 100, 1, 3)
    viewer.add_mosaic([[d3plot], [t_hm, t_sigma]])
    viewer.run()


if __name__ == "__main__":
    os.environ["VIEWER_PERF_LOG"] = "1"
    options = {}
    options[demo_image_viewer.__name__] = demo_image_viewer
    options[demo_plot_viewer.__name__] = demo_plot_viewer
    options[demo_huge_trackbar_performance.__name__] = demo_huge_trackbar_performance
    options[demo_3d_prototype.__name__] = demo_3d_prototype
    if len(sys.argv) >= 2:
        options[sys.argv[1]]()
    else:
        demo_3d_prototype()
