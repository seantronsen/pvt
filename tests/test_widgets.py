from pytest import fixture, raises
from qtviewer.widgets import *
from qtviewer.state import State


class TestStatefulWidget:
    targ_class = StatefulWidget
    targ_args = dict(key="test", init=0)
    state_update_val = 1

    @fixture
    def state(self, mocker):
        cmock = mocker.Mock()
        return State(callback=cmock, init={})

    @fixture
    def sw(self, qtbot):
        w = self.targ_class(**self.targ_args)
        qtbot.addWidget(w)
        return w

    @fixture
    def sw_w_state(self, sw, state):
        sw.attach(state)
        return sw

    def func_update(self, x, y):
        return x.state_update(y)

    def test_init(self, qtbot, benchmark):
        swidget = benchmark(self.targ_class, **self.targ_args)
        qtbot.addWidget(swidget)
        assert len(swidget.states) == 0
        assert swidget.key == self.targ_args["key"]

    def test_attach(self, benchmark, sw, state):
        benchmark(sw.attach, state=state)
        assert state.storage.get(sw.key, None) is not None
        assert state[sw.key] == sw.init
        assert state in sw.states

    def test_on_change(self, benchmark, sw):
        if not type(self) == TestStatefulWidget:
            benchmark(sw.on_change)
        else:
            with raises(NotImplementedError):
                sw.on_change()

    def test_state_update(self, benchmark, sw_w_state):
        state = sw_w_state.states[0]
        cmock = state.onUpdate
        assert state[sw_w_state.key] == 0
        self.func_update(sw_w_state, self.state_update_val)
        assert state[sw_w_state.key] == self.state_update_val
        assert cmock.call_count == 1
        assert cmock.call_args.kwargs == state.storage
        benchmark(sw_w_state.state_update, self.state_update_val)


class TestParameterToggle(TestStatefulWidget):
    targ_class = ParameterToggle
    targ_args = dict(key="toggle", init=False)
    state_update_val = True

    def func_update(self, x, y):
        return x.s.setChecked(y)


class TestParameterTrackbar:
    targ_class = ParameterToggle
    targ_args = dict(key="slide", start=0, stop=100, init=50)
    state_update_val = 75

    def func_update(self, x, y):
        return x.s.setValue(y)
