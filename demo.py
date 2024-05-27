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
from pvt import *
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

    # For the time being, specifying a "dummy" lambda is the best way to render
    # static content. The downside being that if the pane is connected to the
    # global state, the content is redrawn each and every time the state
    # changes. While the cost is miniscule on the compute side, the same cannot
    # be said for the rendering side where there is a real cost to repainting
    # the window unnecessarily. Keep an eye on issue #43 for more information
    # and changes related to improving the efficiency of static content. For
    # now, take comfort by realizing the cost for images less than 8K
    # resolution is still low enough that you shouldn't notice a difference
    # (though you really should consider shrinking the images at that point
    # just for faster processing in your own code).
    #
    # NOTE: Users can now specify a `border` keyword argument to automatically
    # draw a border of the specified color around the image. This reduces the
    # need to do it yourself and considering the scaling / width for arbitrary
    # resolutions and is particularly useful for when the content being
    # displayed has the same background color as the panel (which typically
    # results in making it difficult to determine where the image begins and
    # ends).
    ip = ImagePane(lambda **_: img_test, border="red")
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
    pl = Plot2DLinePane(callback, ncolors=3, cmap="plasma", line_width=1, fillLevel=None)  # 0)
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
    # - https://github.com/seantronsen/pvt/issues/14
    # - https://github.com/seantronsen/pvt/issues/22

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


# NOTE: both this feature and demo are a work in progress. thus far, pyvista seems
# like it has a lot that it could offer for this project. however, after doing
# some performance testing for rather simple scenes, there are some concerns as
# for whether it could maintain a suitable framerate for more complex scenes.
# for reference, the pyvista prototype can animate it's demo at a max of around
# 144 FPS. The PyQtGraph/OpenGL version can peak at well over 6,000 FPS based
# on the log output.
def demo_pvt3dplotter_prototype():
    import pyvista as pv

    viewer = Viewer("demo of pyvista animated noisy sphere mesh")

    # define meshes, must be done prior to defining any callbacks which modify them
    sphere = pv.Sphere()

    def callback(**_):
        sigma = 1e-3
        noise = np.random.normal(loc=0, scale=sigma, size=np.prod(sphere.points.shape))
        sphere.points += noise.reshape(*sphere.points.shape)

    plotter = Pvt3DPlotPane(callback=callback)
    plotter.add_mesh(sphere, cmap="magma")
    anim = Animator(fps=144, contents=plotter)
    bar = AnimatorControlBar(animator=anim)

    viewer.add_panes(anim.animation_content, bar)
    viewer.run()


# For a simpler experience regarding choosing demos to run, pass the CLI call
# an additional argument with the name of the demo.
#
# Example: `python demo.py demo_image_viewer`
if __name__ == "__main__":
    if len(sys.argv) == 1:
        demo_plot_viewer()
    else:
        globals()[sys.argv[1]]()
