from pvt.context import VisualizerContext
from pvt.displays import StatefulDisplay, StatefulImageView, StatefulImageViewLightweight


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
# class TestImagePane(TestStatefulPane):
# 
#     targ_class = ImagePane
#     cback_ret = np.arange(16).reshape(4, 4)
