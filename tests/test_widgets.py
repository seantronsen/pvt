from pytest import fixture, raises
from qtviewer.widgets import *
from qtviewer.state import State


@fixture
def swidget():
    return StatefulWidget(key="test", init=0)


@fixture
def state(mocker):
    cmock = mocker.Mock()
    return State(callback=cmock, init={})


@fixture
def swidget_w_state(swidget, state):
    swidget.attach(state)
    return swidget


def test_stateful_widget_init(qtbot, benchmark):
    key = "test"
    swidget = benchmark(StatefulWidget, key=key, init=0)
    qtbot.addWidget(swidget)
    assert len(swidget.states) == 0
    assert swidget.key == key


def test_stateful_widget_attach(qtbot, benchmark, swidget, state):

    qtbot.addWidget(swidget)
    benchmark(swidget.attach, state=state)
    assert state.storage.get(swidget.key, None) is not None
    assert state[swidget.key] == swidget.init
    assert state in swidget.states


def test_state_widget_on_change_abstract(qtbot, swidget):
    qtbot.addWidget(swidget)
    with raises(NotImplementedError):
        swidget.on_change()


def test_state_widget_state_update(qtbot, benchmark, swidget_w_state):
    qtbot.addWidget(swidget_w_state)
    state = swidget_w_state.states[0]
    cmock = state.onUpdate
    assert state[swidget_w_state.key] == 0
    swidget_w_state.state_update(1)
    assert state[swidget_w_state.key] == 1
    assert cmock.call_count == 1
    assert cmock.call_args.kwargs == state.storage
    benchmark(swidget_w_state.state_update, 1)


@fixture
def toggle(state):
    t = ParameterToggle(key="toggle", init=False)
    t.attach(state)
    return t


def test_parameter_toggle_init(qtbot, benchmark):
    toggle = benchmark(ParameterToggle, key="toggle", init=False)
    qtbot.addWidget(toggle)


def test_parameter_toggle_on_change(qtbot, benchmark, toggle):
    state = toggle.states[0]
    qtbot.addWidget(toggle)
    assert state[toggle.key] == 0
    benchmark(toggle.s.setChecked, True)
    assert state[toggle.key] == 1


@fixture
def trackbar(state):
    s = ParameterTrackbar(key="slide", start=0, stop=100, init=50)
    s.attach(state)
    return s


def test_parameter_trackbar_init(qtbot, benchmark):
    t = benchmark(ParameterTrackbar, "slider", 0, 100)
    qtbot.addWidget(t)


def test_parameter_trackbar_on_change(qtbot, benchmark, trackbar):
    new_value = 75
    state = trackbar.states[0]
    qtbot.addWidget(trackbar)
    assert state[trackbar.key] == 50
    assert trackbar.t.text() == f"{trackbar.key}: {state[trackbar.key]}"
    benchmark(trackbar.s.setValue, 75)
    assert state[trackbar.key] == new_value
    assert trackbar.t.text() == f"{trackbar.key}: {new_value}"
