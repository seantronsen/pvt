##################################################
# FILE: demo.py
# AUTHOR: SEAN TRONSEN
#
# SUMMARY:
# This file demonstrates basic usage of the package utilities. It provides
# examples and best practices for using the library's features, though it is
# not exhaustive.
#
# For further details, review the inline documentation and source code.
# If you have questions, contact the author or submit a GitHub issue.
##################################################
##################################################

# NOTE: Enable performance logging by setting the environment variable
# before importing the library (or via the command line).
import os

os.environ["VIEWER_DEBUG"] = "1"  # remove to disable performance logging


# STANDARD IMPORTS
from pvt.app import App
from pvt.context import VisualizerContext
from pvt.controls import StatefulAnimator, StatefulTrackbar
from pvt.decorators import use_parameter_cache
from pvt.displays import StatefulImageView, StatefulImageViewLightweight, StatefulPlotView2D
from pvt.qtmods import TrackbarConfig
from pvt.utils import norm_uint8, resize_by_ratio
import cv2
import numpy as np
import sys

# IMPORTANT: Visualizer Context & Callback Parameter Handling
#
# The VisualizerContext groups control and display widgets so that only components
# within the same context communicate, preventing state or refresh conflicts.
#
# Callback Parameter Handling:
#   - Callbacks receive parameters as keyword arguments from control widgets.
#   - The keys emitted by controls must exactly match the callback's parameter names.
#   - Use **kwargs in your callback to ignore extra parameters when only a subset is needed.
#   - Without **kwargs, every control widget parameter must be explicitly defined.
#
# This design lets you focus on essential parameters while the context manages the rest.
def demo_image_viewer():
    img_test = cv2.imread("sample-media/checkboard_non_planar.png").astype(np.uint8)
    img_test = norm_uint8(cv2.cvtColor(img_test, cv2.COLOR_BGR2GRAY))

    # IMPORTANT: Precompute any expensive or avoidable computations to improve
    # performance. Slow rendering is likely due to bottlenecks in your callback
    # functions. Enable performance logging with VIEWER_DEBUG=1 for additional
    # insights.
    #
    # EXAMPLE: Compare the rendering speeds between the resize and sigma
    # sliders. (Resize involves more computation and will be slower.)
    img_test_small = img_test.copy()
    img_test = resize_by_ratio(img_test, 10)
    noise_image = np.random.randn(*(img_test.shape)).astype(np.int8)  # pyright: ignore

    # TODO: Consider redesigning to remove the need for kwargs, though this may
    # degrade performance.
    def callback_a(rho, sigma, **_):
        resized = resize_by_ratio(img_test, rho)
        noise_slice = noise_image[: resized.shape[0], : resized.shape[1]]
        result = resized + (noise_slice * sigma)
        return result

    # NOTE: The default configuration for the decorator whitelists all named
    # parameters, excluding positional arguments (*args) and **kwargs. In this
    # library, **kwargs is used to ignore extra parameters not explicitly
    # defined in the callback. For example, since `rho` is not a named
    # parameter in callback_b, it is passed in **kwargs.
    #
    # This behavior is equivalent to: @use_parameter_cache(whitelist=["sigma"])
    @use_parameter_cache
    def callback_b(sigma, **_):
        noise_slice = noise_image[: img_test_small.shape[0], : img_test_small.shape[1]]
        result = img_test_small + (noise_slice * sigma)
        return result

    # Set up the interface and run the application.
    # Enjoy tuning and visualizing!
    app = App(title="Example for Displaying Rapid Image Updates")

    trackbar_rho = StatefulTrackbar(key="rho", config=TrackbarConfig(start=0.001, stop=1, step=0.001, init=0.5))
    trackbar_sigma = StatefulTrackbar("sigma", TrackbarConfig(0, 100, 2))
    ip_a = StatefulImageView(callback_a, title="resized image")
    ip_b = StatefulImageView(
        callback_b,
        title="small image for perf",
        config=StatefulImageView.Config(
            border_color="red",
            on_render_reset_viewport=False,
        ),
    )
    # IMPORTANT: Group all display and control widgets within a
    # VisualizerContext so they can communicate. This helper function also
    # automatically arranges them in a mosaic (grid-like) layout.
    context = VisualizerContext.create_viewer_from_mosaic([[ip_a, ip_b], [trackbar_rho, trackbar_sigma]])
    app.set_window_content(context)
    app.run()


def demo_static_image_viewer():

    # EXAMPLE: This demo illustrates callback optimization using the decorator.
    # Here, "fake caching" lets you specify which parameters should trigger a
    # new frame computation.
    #
    # There are two tracking options:
    #   - Inclusive (whitelist)
    #   - Exclusive (blacklist)
    #
    # Only one type can be used at a time.
    #
    # NOTE: This is useful when:
    #   - a specific paramter should not trigger an update on change
    #   - a display does not subscribe to all possible callback parameters
    #   - the context contains an animator, but not all displays require
    #   updates on every animation tick.
    #
    # IMPORTANT: Only the named parameters defined in your callback are used.
    # Extra parameters passed via **kwargs are automatically ignored.
    img_test = norm_uint8(cv2.imread("sample-media/checkboard_non_planar.png"))

    # NOTE: With blacklist="all", only one render will ever occur for the
    # associated display at runtime.
    @use_parameter_cache(blacklist="all")
    def callback(**_):
        return img_test

    app = App(title="Example: Static Image")
    trackbar_sigma = StatefulTrackbar("sigma", TrackbarConfig(0, 100, 2))
    ip = StatefulImageView(callback)
    context = VisualizerContext.create_viewer_from_mosaic([[ip], [trackbar_sigma]])
    app.set_window_content(context)
    app.run()


def demo_plot_viewer():
    N_WAVES = 5
    AUTO_COLORS = 4
    Line = StatefulPlotView2D.Line
    Scatter = StatefulPlotView2D.Scatter

    def _callback_base(nsamples, sigma, omega, phasem, animation_tick, **_):
        cphase = (animation_tick / (2 * np.pi)) * phasem
        sinusoid = np.sin((np.linspace(0, omega * 2 * np.pi, nsamples) + cphase))
        noise = np.random.randn(nsamples)
        result = sinusoid + (noise[:nsamples] * sigma)
        return np.array([result] * N_WAVES) + (np.arange(N_WAVES).reshape(-1, 1) - ((N_WAVES - 1) / 2))

    def callback_line(nsamples, sigma, omega, phasem, animation_tick, **_):
        result = _callback_base(nsamples, sigma, omega, phasem, animation_tick, **_)
        return [Line(x=np.arange(signal.size), y=signal, name=f"item: {i}") for i, signal in enumerate(result)]

    def callback_scatter(nsamples, sigma, omega, phasem, animation_tick, **_):
        result = _callback_base(nsamples, sigma, omega, phasem, animation_tick, **_)
        return [Scatter(x=np.arange(signal.size), y=signal, marker="x") for signal in result]

    app = App(title="Multiple Plots: An Illustration of Signal Aliasing")

    trackbar_n = StatefulTrackbar("nsamples", config=TrackbarConfig(100, 1000, 100))
    trackbar_omega = StatefulTrackbar("omega", config=TrackbarConfig(1, 50, init=50))
    trackbar_sigma = StatefulTrackbar("sigma", config=TrackbarConfig(0, 3, 0.1))
    trackbar_phasem = StatefulTrackbar("phasem", config=TrackbarConfig(0.1, 10, 0.1, init=0.1))

    # For 2D plots, you can specify a colormap and the number of unique colors.
    # If there are more curves than unique colors, modulo arithmetic cycles
    # through them.

    # NOTE: Refer to PyQtGraph's examples for details on available colormaps.
    # The available options may differ from other libraries and can include
    # additional options from Matplotlib (untested) if the package is present
    # in the runtime environment.
    pv_a = StatefulPlotView2D(
        callback=callback_line,
        config=StatefulPlotView2D.Config(
            auto_colors_cmap="plasma",
            auto_colors_nunique=AUTO_COLORS,
            title="Signal Aliasing: Labeled Line Graph",
            label_x="Sample Number",
            label_y="Sample Height",
            legend=True,
        ),
        title="Line Plot Version",
    )
    pv_b = StatefulPlotView2D(
        callback=callback_scatter,
        config=StatefulPlotView2D.Config(
            background_color="white",
            title="Signal Aliasing: Labeled Scatter Graph",
        ),
    )

    # To animate display panes within a context, add a `StatefulAnimator` to
    # the same context. This widget appears as a control bar in the GUI,
    # allowing you to pause, play, and skip frames forward or backward. A reset
    # button is provided to reset the `animation_tick` to zero and it also
    # provides the option to display UPS diagnostic information (e.g., current
    # framerate and maximum possible framerate).
    #
    # NOTE: The callback functions must execute quickly to support the desired
    # `ups` rate (updates per second). They must also include a named
    # parameter, `animation_tick`, which receives the current tick value from
    # the animator. This value can be used with modulo arithmetic to cycle
    # through data sequences or adjust output over time.
    animator = StatefulAnimator(ups=60, auto_start=True, show_ups_info=True)

    # IMPORTANT: Rendering for multiple animated displays does not occur
    # simultaneously, at least not yet. Use caution if you are animating many
    # displays at the same time as the time to update and render each will
    # stack.
    context = VisualizerContext.create_viewer_from_mosaic(
        [
            [pv_a, pv_b],
            [animator],
            [trackbar_n, trackbar_omega],
            [trackbar_phasem, trackbar_sigma],
        ],
    )
    app.set_window_content(context)
    app.run()


def demo_plot_viewer_over_vnc():
    Line = StatefulPlotView2D.Line

    def callback(nsamples, omega, animation_tick, **_):
        sigma = 0.05
        phasem = 0.2
        cphase = (animation_tick / (2 * np.pi)) * phasem
        sinusoid = np.sin((np.linspace(0, omega * 2 * np.pi, nsamples) + cphase))
        noise = np.random.randn(nsamples)
        result = sinusoid + (noise[:nsamples] * sigma)
        return [Line(x=np.arange(result.size), y=result)]

    # For Linux hosts that support serving content via VNC, you can specify the
    # "vnc" platform. This is useful when your callbacks require more compute
    # than your local system can provide, or when the target host has
    # specialized hardware (e.g., clusters, GPU accelerators, stream
    # processors, etc.). It also serves as a workaround when the default
    # platform (e.g., "xcb" for X Window Server) fails due to missing shared
    # libraries, but the necessary VNC libraries are available.
    #
    # To connect to the VNC server, launch a VNC client and use the connection
    # address and port (the default is 5900; refer to STDOUT for the active
    # port). For remote servers, it is often easiest to tunnel the server port
    # through SSH using the `-L` flag.
    #
    # TODO: include a POSIX-compliant SSH tunnel script in the library.
    app = App(title="Look at me, now through VNC", platform="vnc")

    animator = StatefulAnimator(ups=60, auto_start=True, show_ups_info=True)
    trackbar_n = StatefulTrackbar("nsamples", config=TrackbarConfig(100, 1000, 100))
    trackbar_omega = StatefulTrackbar("omega", config=TrackbarConfig(1, 50, init=50))

    pv_a = StatefulPlotView2D(callback=callback)

    context = VisualizerContext.create_viewer_from_mosaic(
        [
            [pv_a],
            [animator],
            [trackbar_n, trackbar_omega],
        ],
    )
    app.set_window_content(context)
    app.run()


# TODO: This function is a remnant from our tests for faster RGB rendering and
# is not yet a full demo. For extremely fast RGB rendering, use the lightweight
# image view as demonstrated here. Do note that it imposes extra requirements
# on your callback function.
#
# NOTE: The slower performance for RGB images stems from Python's limitations
# and the current lack of optimized support in Qt for rapid RGB intensity
# scaling.
def test_rgb_image_render_speed():

    img_test = norm_uint8(cv2.imread("sample-media/checkboard_non_planar.png", cv2.IMREAD_GRAYSCALE))
    img_test = cv2.applyColorMap(img_test, colormap=cv2.COLORMAP_MAGMA)
    img_test = cv2.GaussianBlur(img_test, ksize=(17, 17), sigmaX=9, sigmaY=9)
    img_test = resize_by_ratio(img_test, ratio=30)
    img_test = np.asarray(cv2.cvtColor(img_test, cv2.COLOR_BGR2RGB), dtype=np.uint8)

    def callback(**_):
        return img_test

    app = App(title="Test RGB Render Speed")
    animator = StatefulAnimator(ups=240, auto_start=True, show_ups_info=True)
    ip = StatefulImageViewLightweight(
        callback,
        config=StatefulImageViewLightweight.Config(
            border_color="red",
        ),
    )

    context = VisualizerContext.create_viewer_from_mosaic([[ip], [animator]])
    app.set_window_content(context)
    app.run()


# TODO: Create a demo that demonstrates using
# use_parameter_cache(blacklist="animation_tick") to ignore animation tick
# updates for specific displays. This is particularly useful when only one
# display should animate while others remain static.

################################################################################
################################################################################
#
# To select a specific demo, pass its name as a command line argument.
# Example: `python demo.py demo_image_viewer`
#
################################################################################
################################################################################
if __name__ == "__main__":
    if len(sys.argv) == 1:
        demo_plot_viewer()
    else:
        globals()[sys.argv[1]]()
