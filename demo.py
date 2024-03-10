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
    img_test = cv2.imread("sample-media/checkboard_non_planar.png").astype(np.uint8)
    img_test = norm_uint8(cv2.cvtColor(img_test, cv2.COLOR_BGR2GRAY))

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

    # IMPORTANT: Ensure the kwargs parameter is specified to allow the function
    # interface to remain generic for top level controls and ignore extra
    # arguments without failing. To elaborate, parameters associated with
    # global control widgets are passed to the callbacks for all top level
    # display panes.
    def callback_example(rho, sigma, **_):
        ratio = np.max([0.001, rho / 1000])
        resized = resize_by_ratio(img_test, ratio)
        noise_slice = noise_image[: resized.shape[0], : resized.shape[1]]
        result = resized + (noise_slice * sigma)
        print(f"resolution: ({result.shape[0]:05d}, {result.shape[1]:05d})")
        return result

    def callback_example_2(sigma, **_):
        noise_slice = noise_image[: img_test_small.shape[0], : img_test_small.shape[1]]
        result = img_test_small + (noise_slice * sigma)
        print(f"resolutionb: ({result.shape[0]:05d}, {result.shape[1]:05d})")
        return result

    # define the viewer interface and run the application
    # happy tuning / visualizing!
    image_viewer = vwr.VisionViewer()
    trackbar_rho = vwr.ParameterTrackbar("rho", 0, 100, step=1, init=50)
    trackbar_sigma = vwr.ParameterTrackbar("sigma", 0, 100, 2)
    ip = vwr.ImagePane(img_test, callback_example)
    ip2 = vwr.ImagePane(img_test_small, callback_example_2)
    image_viewer.add_mosaic([[ip, ip2], [trackbar_rho], [trackbar_sigma]])
    image_viewer.run()


def demo_line_plot_viewer():

    def callback(nsamples=1000, sigma=1, omega=1, phasem=1, animation_tick=0, **_):
        cphase = animation_tick / (2 * np.pi)
        cphase *= phasem / 10
        sinusoid = np.sin((np.linspace(0, omega * 2 * np.pi, nsamples) + cphase))
        noise = np.random.randn(nsamples)
        result = sinusoid + (noise[:nsamples] * (sigma / 10))
        waves = 3
        return np.array([result] * waves) + np.arange(waves).reshape(-1, 1)

    viewer = vwr.PlotViewer(title="Multiple Plots: A Visual Illustration of Signal Aliasing")
    trackbar_n = vwr.ParameterTrackbar("nsamples", 100, 1000, step=100)
    trackbar_sigma = vwr.ParameterTrackbar("sigma", 0, 30)
    trackbar_omega = vwr.ParameterTrackbar("omega", 1, 50, init=50)
    trackbar_phasem = vwr.ParameterTrackbar("phasem", 1, 100)
    animated_plot = vwr.Animator(fps=60, contents=vwr.Plot2DLinePane(callback=callback))
    viewer.add_panes(animated_plot.animation_content, trackbar_n, trackbar_omega, trackbar_phasem, trackbar_sigma)
    viewer.run()


def demo_scatter_plot_viewer():

    def callback(nsamples=1000, sigma=1, omega=1, phasem=1, animation_tick=0, **_):
        cphase = animation_tick / (2 * np.pi)
        cphase *= phasem / 10
        sinusoid = np.sin((np.linspace(0, omega * 2 * np.pi, nsamples) + cphase))
        noise = np.random.randn(nsamples)
        result = sinusoid + (noise[:nsamples] * (sigma / 10))
        waves = 3
        return np.array([result] * waves) + np.arange(waves).reshape(-1, 1)

    viewer = vwr.PlotViewer(title="Multiple Plots: A Visual Illustration of Signal Aliasing")
    trackbar_n = vwr.ParameterTrackbar("nsamples", 100, 1000, step=100)
    trackbar_sigma = vwr.ParameterTrackbar("sigma", 0, 30)
    trackbar_omega = vwr.ParameterTrackbar("omega", 1, 50, init=50)
    trackbar_phasem = vwr.ParameterTrackbar("phasem", 1, 100)
    animated_plot = vwr.Animator(fps=60, contents=vwr.Plot2DScatterPane(callback=callback))
    viewer.add_panes(animated_plot.animation_content, trackbar_n, trackbar_omega, trackbar_phasem, trackbar_sigma)
    viewer.run()


def demo_huge_trackbar_bad_performance():
    """
    An example to illustrate that trackbars with extreme ranges of values are
    slow and cumbersome, even when used alone.
    """

    viewer = vwr.PlotViewer(title="Multiple Plots: A Visual Illustration of Signal Aliasing")
    trackbar_n = vwr.ParameterTrackbar("nsamples", 0, 10000)
    viewer.add_panes(trackbar_n)
    viewer.run()


def demo_3d_prototype():

    viewer = vwr.PlotViewer(title="Multiple Plots: A Visual Illustration of Signal Aliasing")

    def callback(hm=1, sigma=1, **_):
        gaussian = cv2.getGaussianKernel(20, sigma=sigma)
        gaussian = gaussian * gaussian.T  # pyright: ignore
        return gaussian * hm

    d3plot = vwr.Plot3DPane(callback=callback)
    t_hm = vwr.ParameterTrackbar("hm", 1, 10000, step=100)
    t_sigma = vwr.ParameterTrackbar("sigma", 0, 100, init=3)
    viewer.add_mosaic([[d3plot], [t_hm, t_sigma]])
    viewer.run()


if __name__ == "__main__":
    os.environ["VIEWER_PERF_LOG"] = "1"
    options = {}
    options[demo_image_viewer.__name__] = demo_image_viewer
    options[demo_line_plot_viewer.__name__] = demo_line_plot_viewer
    options[demo_scatter_plot_viewer.__name__] = demo_scatter_plot_viewer
    options[demo_huge_trackbar_bad_performance.__name__] = demo_huge_trackbar_bad_performance
    options[demo_3d_prototype.__name__] = demo_3d_prototype
    if len(sys.argv) >= 2:
        options[sys.argv[1]]()
    else:
        demo_3d_prototype()
