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
# still remain, please get in touch with the author or submit a github issue.
##################################################
##################################################

# OPTIONAL IMPORTS
import os


# NOTE: Performance logging can be enabled with this environment variable.
# IMPORTANT: It must be set via the command line or prior to library import
os.environ["VIEWER_PERF_LOG"] = "1"  # remove to disable performance logging


# STANDARD IMPORTS
import cv2
import numpy as np
from qtviewer import *
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
    # computation, making it slower by comparison).
    img_test_small = img_test.copy()
    img_test = resize_by_ratio(img_test, 10)
    noise_image = np.random.randn(*(img_test.shape)).astype(np.int8)  # pyright: ignore

    # IMPORTANT: Specifying a kwargs parameter allows the function interface to
    # remain generic which is an important quality for any callbacks associated
    # with the global application state (e.g. panes or controls added to the
    # display via the `add_panes` or `add_mosaic` method calls). If this
    # parameter isn't specified, the callback must have a defined parameter for
    # each state variable associated with a global control widget or else
    # Python will raise an exception. If your callback doesn't need all of
    # these variables, then this kwargs variable specification will save you
    # some typing.

    def callback_0(rho, sigma, **_):
        resized = resize_by_ratio(img_test, rho)
        noise_slice = noise_image[: resized.shape[0], : resized.shape[1]]
        result = resized + (noise_slice * sigma)
        return result

    def callback_1(sigma, **_):
        noise_slice = noise_image[: img_test_small.shape[0], : img_test_small.shape[1]]
        result = img_test_small + (noise_slice * sigma)
        return result

    # define the viewer interface and run the application
    # happy tuning / visualizing!
    image_viewer = Viewer(title="A Showcase Example for Rapid Image Display")
    trackbar_rho = ParameterTrackbar("rho", 0.001, 1, step=0.001, init=0.5)
    trackbar_sigma = ParameterTrackbar("sigma", 0, 100, 2)

    # set to False if panning and zoom should not reset when rendering each new
    # frame
    ip = ImagePane(callback_0, autoRange=True)
    ip2 = ImagePane(callback_1)

    # Users can easily generated a row/column like layout using `add_mosiac`.
    # For the default vertical layout, use the `add_panes` method call.
    image_viewer.add_mosaic([[ip, ip2], [trackbar_rho, trackbar_sigma]])
    image_viewer.run()


# An example of how to display static / unchanging content
def demo_static_image_viewer():
    img_test = cv2.imread("sample-media/checkboard_non_planar.png").astype(np.uint8)
    img_test = norm_uint8(cv2.cvtColor(img_test, cv2.COLOR_BGR2GRAY))

    image_viewer = Viewer()
    ip = ImagePane(lambda **_: img_test)
    image_viewer.add_panes(ip)
    image_viewer.run()


# An example to showcase various plotting features
def demo_plot_viewer():
    def callback(nsamples, sigma, omega, phasem, animation_tick, **_):
        cphase = (animation_tick / (2 * np.pi)) * phasem
        sinusoid = np.sin((np.linspace(0, omega * 2 * np.pi, nsamples) + cphase))
        noise = np.random.randn(nsamples)
        result = sinusoid + (noise[:nsamples] * sigma)
        waves = 5
        return np.array([result] * waves) + (np.arange(waves).reshape(-1, 1) - ((waves - 1) / 2))

    viewer = Viewer(title="Multiple Plots: A Visual Illustration of Signal Aliasing")
    trackbar_n = ParameterTrackbar("nsamples", 100, 1000, 100)
    trackbar_omega = ParameterTrackbar("omega", 1, 50, init=50)
    trackbar_sigma = ParameterTrackbar("sigma", 0, 3, 0.1)
    trackbar_phasem = ParameterTrackbar("phasem", 0.1, 10, 0.1, init=0.1)

    # For any kind of 2D plot made available by this library, users may specify
    # a color map and the number of unique colors to use from that colormap. If
    # the number of colors specified is less than the number of curves /
    # featuers to be plotted, then modulo arithmetic is used to loop over the
    # available colors.
    #
    # NOTE: Check out PyQtGraph's examples which detail which colormaps are
    # available for a specific list of options with gradients displayed
    # alongside them. The available colormaps differ from other libraries and
    # only include extras like those from Matplotlib under certain
    # circumstances (which have yet to be tested).
    #
    # For line plots, users may also specify a line_width argument which sets
    # the width of any curve in pixels. The final option currently available is
    # fillLevel, which causes the area under any curve to be shaded between the
    # curve and this value. The default value is None which results in the area
    # under the curve not being shaded.
    pl = Plot2DLinePane(callback, ncolors=3, cmap="plasma", line_width=1, fillLevel=0)
    pl.set_title("Signal Aliasing: Labeled Graph")
    pl.set_xlabel("Sample Number")
    pl.set_ylabel("Amplitude")

    # Users can animate any display pane by wrapping the associated widget in
    # an `Animator`. Here, an fps value can be specified to limit the refresh
    # rate. Do note that the user specified callback must execute quickly
    # enough for the desired animation rate to be achievable. In addition, it
    # must provide a named parameter `animation_tick` which provides the
    # function the current tick value of the animation timer. This can be
    # paired up with modulo arithmetic (% operator) to loop over data sequences
    # or modify the output as "time" moves forward.
    pl = Animator(fps=60, contents=pl).animation_content

    # Scatter panes are another feature provided by the current version of the
    # library. Like line plots, color maps can be specified here as well. In
    # addition, the user has be option to specify the size of each point symbol
    # as well as the kind of symbol drawn.
    # For a full list of symbols, visit the documentation for PyQtGraph and
    # review their resouces for scatter plots.
    ps = Animator(fps=60, contents=Plot2DScatterPane(callback, symbolSize=10, symbol="t", ncolors=2)).animation_content

    # IMPORTANT: Rendering multiple animations does not occur simultaneously,
    # at least not yet. Use caution if you are animating many windows at the
    # same time as the time to update each window will stack. Follow these
    # issues for updates on the features planned which solve this problem.
    # - https://github.com/seantronsen/qtviewer/issues/14
    # - https://github.com/seantronsen/qtviewer/issues/22

    viewer.add_mosaic([[pl, ps], [trackbar_n, trackbar_omega], [trackbar_phasem, trackbar_sigma]])
    viewer.run()


def demo_3d_prototype():

    def callback(animation_tick, sigma, **_):
        gaussian = cv2.getGaussianKernel(20, sigma=sigma)
        gaussian = gaussian * gaussian.T  # pyright: ignore
        gaussian = gaussian / np.sum(gaussian)
        return gaussian * ((animation_tick % 500) + 1) * 10

    viewer = Viewer("Deprecated 3D prototype. We will soon integrate with PyVista for 3D data display features")
    animator = Animator(fps=60, contents=Plot3DPane(callback))
    d3plot = animator.animation_content

    # Users can create their own animation controls or make use of Animation
    # control bar widget we provide for convenience.
    control_bar = AnimatorControlBar(animator=animator)
    t_sigma = ParameterTrackbar("sigma", 0.1, 25, step=0.1, init=5)
    viewer.add_panes(d3plot, control_bar, t_sigma)
    viewer.run()


# For a simpler experience regarding choosing demos to run, pass the CLI call
# an additional argument with the name of the demo.
#
# Example: `python demo.py demo_image_viewer`
if __name__ == "__main__":
    options = {}
    options[demo_image_viewer.__name__] = demo_image_viewer
    options[demo_static_image_viewer.__name__] = demo_static_image_viewer
    options[demo_plot_viewer.__name__] = demo_plot_viewer
    options[demo_3d_prototype.__name__] = demo_3d_prototype
    if len(sys.argv) >= 2:
        options[sys.argv[1]]()
    else:
        demo_plot_viewer()
