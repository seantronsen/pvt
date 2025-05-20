from pvt.context import VisualizerContext
from pvt.displays import StatefulDisplay
from pytest import fixture, raises


class TestStatefulDisplay:

    def test__init__(self):
        raise NotImplementedError

    def test_add_widget(self):
        raise NotImplementedError

    def test_on_viewer_state_changed(self):
        """
        # needs to test callback object, callback should run, and callback
        # should not run
        """
        raise NotImplementedError

    def test__compute_data(self):
        """requires changing this method from private to protected"""
        raise NotImplementedError

    def test__render_data(self):
        """requires changing this method from private to protected"""
        raise NotImplementedError

    def test_render_data(self):
        """requires changing this method from protected to public"""
        raise NotImplementedError


# class TestStatefulPane:
#
#     targ_class = StatefulPane
#     cback_ret = None
#
#     @fixture
#     def sargs(self):
#         return dict(that=0)
#
#     @fixture
#     def fpane(self, qtbot, mocker):
#         cback = mocker.Mock(return_value=self.cback_ret)
#         widget = self.targ_class(callback=cback)
#         qtbot.addWidget(widget)
#         return widget
#
#     @fixture
#     def bench_fpane(self, qtbot):
#         widget = self.targ_class(callback=lambda **_: self.cback_ret)
#         qtbot.addWidget(widget)
#         return widget
#
#     @fixture
#     def trackbar(self, qtbot):
#         s = ParameterTrackbar(key="slide", start=0, stop=100, init=50)
#         qtbot.addWidget(s)
#         return s
#
#     def test_init(self, qtbot, benchmark):
#         cback = lambda **_: self.cback_ret
#         widget = benchmark(self.targ_class, callback=cback)
#         qtbot.addWidget(widget)
#         assert widget.callback == cback
#
#     def test_update(self, fpane, sargs):
#         if type(self) != TestStatefulPane:
#             fpane.update(**sargs)
#             assert fpane.callback.call_count != 0
#         else:
#             with raises(NotImplementedError):
#                 fpane.update(**sargs)
#             assert fpane.callback.call_count == 1
#         assert fpane.callback.call_args.kwargs == sargs
#
#     def test_update_b(self, benchmark, bench_fpane, sargs):
#         if type(self) != TestStatefulPane:
#             benchmark(bench_fpane.update, **sargs)
#         else:
#             with raises(NotImplementedError):
#                 bench_fpane.update(**sargs)
#
#     def test_compute_data(self, fpane, sargs):
#         fpane.compute_data(**sargs)
#         assert fpane.callback.call_args.kwargs == sargs
#
#     def test_compute_data_b(self, benchmark, bench_fpane, sargs):
#         benchmark(bench_fpane.compute_data, **sargs)
#
#     def test_render_data(self, fpane, sargs):
#         if type(self) != TestStatefulPane:
#             fpane.render_data(fpane.compute_data(**sargs))
#         else:
#             with raises(NotImplementedError):
#                 fpane.render_data(None)
#
#     def test_render_data_b(self, benchmark, bench_fpane, sargs):
#         if type(self) != TestStatefulPane:
#             a = bench_fpane.compute_data(**sargs)
#             benchmark(bench_fpane.render_data, a)
#         else:
#             with raises(NotImplementedError):
#                 bench_fpane.render_data(None)
#
#     def test_force_flush(self, fpane):
#         if type(self) != TestStatefulPane:
#             fpane.force_flush()
#         else:
#             with raises(NotImplementedError):
#                 fpane.force_flush()
#         assert fpane.callback.call_count != 0
#
#     def test_force_flush_b(self, benchmark, bench_fpane):
#         if type(self) != TestStatefulPane:
#             benchmark(bench_fpane.force_flush)
#         else:
#             with raises(NotImplementedError):
#                 bench_fpane.force_flush()
#
#     def test_enchain(self, fpane, trackbar):
#         fpane.enchain(trackbar)
#         assert fpane.pane_state in trackbar.states
#         assert fpane.pane_state["slide"] == 50
#
#     def test_enchain_b(self, benchmark, bench_fpane, trackbar):
#         benchmark(bench_fpane.enchain, trackbar)
#
#     def test_attach_widget(self, mocker, fpane, trackbar):
#         spy = mocker.spy(fpane, "enchain")
#         fpane.attach_widget(trackbar)
#         # not sure why that was set to != before...
#         # and now I remember that it was because benchmark called the function
#         # multiple times
#         assert spy.call_count == 1
#         assert trackbar.parent() == fpane
#
#     def test_attach_widget_b(self, benchmark, bench_fpane, trackbar):
#         benchmark(bench_fpane.attach_widget, trackbar)
#
#
# class TestImagePane(TestStatefulPane):
#
#     targ_class = ImagePane
#     cback_ret = np.arange(16).reshape(4, 4)
#
#
# class TestBasePlot2DPane(TestStatefulPane):
#
#     targ_class = BasePlot2DPane
#     cback_ret = np.arange(100).reshape(-1, 2)
#
#     def test_plot_tailored(self, fpane):
#         fpane.plot(i=1)
#
#     def test_plot_tailored_b(self, benchmark, bench_fpane):
#         benchmark(bench_fpane.plot, i=1)
#
#     def test__reinitialize_curves_few(self, fpane):
#         n = 10
#         fpane.reinitialize_curves(n)
#         assert len(fpane.curves) == n
#
#     def test__reinitialize_curves_few_b(self, benchmark, bench_fpane):
#         n = 10
#         benchmark(bench_fpane.reinitialize_curves, n)
#
#     def test__reinitialize_curves_many(self, fpane):
#         n = 100
#         fpane.reinitialize_curves(n)
#         assert len(fpane.curves) == n
#
#     def test__reinitialize_curves_many_b(self, benchmark, bench_fpane):
#         n = 100
#         benchmark(bench_fpane.reinitialize_curves, n)
#
#
# class TestPlot2DLinePane(TestBasePlot2DPane):
#     targ_class = Plot2DLinePane
#
#
# class TestPlot2DScatterPane(TestBasePlot2DPane):
#     targ_class = Plot2DScatterPane
#
#
# class TestPlot3DPane(TestStatefulPane):
#     targ_class = Plot3DPane
#     cback_ret = np.arange(100).reshape(10, 10)
