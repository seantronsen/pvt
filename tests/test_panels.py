from pytest import fixture, raises
from qtviewer.panels import BasePlot2DPane, ImagePane, Plot2DLinePane, Plot2DScatterPane, Plot3DPane, StatefulPane
from qtviewer.widgets import ParameterTrackbar
import numpy as np


class TestStatefulPane:

    targ_class = StatefulPane
    cback_ret = None

    @fixture
    def sargs(self):
        return dict(that=0)

    @fixture
    def fpane(self, qtbot, mocker):
        cback = mocker.Mock(return_value=self.cback_ret)
        widget = self.targ_class(callback=cback)
        qtbot.addWidget(widget)
        return widget

    @fixture
    def trackbar(self, qtbot):
        s = ParameterTrackbar(key="slide", start=0, stop=100, init=50)
        qtbot.addWidget(s)
        return s

    def test_init(self, qtbot, benchmark, mocker):
        cback = mocker.Mock(return_value=self.cback_ret)
        widget = benchmark(self.targ_class, callback=cback)
        qtbot.addWidget(widget)
        assert widget.callback == cback

    def test_update(self, benchmark, fpane, sargs):
        if type(self) != TestStatefulPane:
            benchmark(fpane.update, **sargs)
            assert fpane.callback.call_count != 0
        else:
            with raises(NotImplementedError):
                fpane.update(**sargs)
            assert fpane.callback.call_count == 1
        assert fpane.callback.call_args.kwargs == sargs

    def test_compute_data(self, benchmark, fpane, sargs):
        benchmark(fpane.compute_data, **sargs)
        assert fpane.callback.call_args.kwargs == sargs

    def test_render_data(self, benchmark, fpane, sargs):
        if type(self) != TestStatefulPane:
            benchmark(fpane.render_data, fpane.compute_data(**sargs))
        else:
            with raises(NotImplementedError):
                fpane.render_data(None)

    def test_force_flush(self, benchmark, fpane):
        if type(self) != TestStatefulPane:
            benchmark(fpane.force_flush)
        else:
            with raises(NotImplementedError):
                fpane.force_flush()
        assert fpane.callback.call_count != 0

    def test_enchain(self, benchmark, fpane, trackbar):
        benchmark(fpane.enchain, trackbar)
        assert fpane.pane_state in trackbar.states
        assert fpane.pane_state["slide"] == 50

    def test_attach_widget(self, benchmark, mocker, fpane, trackbar):
        spy = mocker.spy(fpane, "enchain")
        benchmark(fpane.attach_widget, trackbar)
        assert spy.call_count != 1
        assert trackbar.parent() == fpane


class TestImagePane(TestStatefulPane):

    targ_class = ImagePane
    cback_ret = np.arange(16).reshape(4, 4)


class TestBasePlot2DPane(TestStatefulPane):

    targ_class = BasePlot2DPane
    cback_ret = np.arange(100).reshape(-1, 2)

    def test_plot_tailored(self, benchmark, fpane):
        benchmark(fpane.plot_tailored, i=1)

    def test__reinitialize_curves_few(self, benchmark, fpane):
        n = 10
        benchmark(fpane.reinitialize_curves, n)
        assert len(fpane.curves) == n

    def test__reinitialize_curves_many(self, benchmark, fpane):
        n = 100
        benchmark(fpane.reinitialize_curves, n)
        assert len(fpane.curves) == n


class TestPlot2DLinePane(TestBasePlot2DPane):
    targ_class = Plot2DLinePane


class TestPlot2DScatterPane(TestBasePlot2DPane):
    targ_class = Plot2DScatterPane


class TestPlot3DPane(TestStatefulPane):
    targ_class = Plot3DPane
    cback_ret = np.arange(100).reshape(10, 10)
