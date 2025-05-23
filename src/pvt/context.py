from PySide6.QtWidgets import QHBoxLayout, QLayout, QVBoxLayout, QWidget
from pvt.controls import StatefulControl
from pvt.displays import StatefulDisplay
from pvt.state import VisualizerState
from pvt.utils import find_children_of_types


def configure_state(
    displays: list[StatefulDisplay],
    controls: list[StatefulControl],
    state: VisualizerState | None = None,
) -> VisualizerState:
    """
    Link controls and data displays to a common exchange (e.g., bus) such that
    none of the parties involved are truly aware of the existence of the
    others. Uses Qt's signal/slot mechanism to implement the desired behavior.

    :param displays: a list of widgets which consume state updates
    :param controls: a list of widgets that produce state updates
    :param state: optionally link controls and displays to an existing state instance
    :return: the state instance which links the specified controls and displays
    """
    state = state if state is not None else VisualizerState()

    # avoid triggering unnecessary renders by handling controls states first.
    #
    # ensure no two controls share a parameter key name. better to scream
    # a loud failure here than to have the users complain about witnessing
    # unexpected changes from their visualizations because the law of python
    # land dictionaries says kwarg parameters can overwrite one another.
    keyset: set[str] = set()
    for c in controls:
        if c.key in keyset:
            raise ValueError(f"detected multiple controls sharing the same parameter key '{c.key}'")
        keyset.add(c.key)
        c.on_control_signal_changed.connect(state.modify_state)
        state.modify_state(c.query_control_signal())

    # wire up the displays
    for d in displays:
        state.state_changed.connect(d.on_viewer_state_changed)

    # ensure displays are initialized with the current state as dictated by the
    # linked controls
    state.flush()
    return state


class VisualizerContext(QWidget):
    """
    A container widget that serves as the central hub for visualizations
    sharing common parameters. This class automatically connects user-defined
    control and display widgets, ensuring they communicate and synchronize
    seamlessly.
    """

    def __init__(self, layout: QLayout, state: VisualizerState | None = None) -> None:
        super().__init__()
        self.setLayout(layout)
        interesting_nodes = find_children_of_types(self, StatefulDisplay, StatefulControl)
        self.state = configure_state(
            displays=interesting_nodes.get(StatefulDisplay, []),  # pyright: ignore
            controls=interesting_nodes.get(StatefulControl, []),  # pyright: ignore
            state=state,
        )
        self.state.setParent(self)

    @staticmethod
    def create_viewer_with_vertical_layout(panes: list[QWidget], state: VisualizerState | None = None):
        """
        Add the provided pane(s) to the GUI window layout, vertically (top down).

        :param panes: A sequence of one or more widgets to add to the display.
        """
        layout = QVBoxLayout()
        for w in panes:
            layout.addWidget(w)

        return VisualizerContext(layout=layout, state=state)

    @staticmethod
    def create_viewer_from_mosaic(mosaic: list[list[QWidget]], state: VisualizerState | None = None):
        """
        A convenience method which provides users a simple method for
        specifying a row/column layout to be displayed in the viewer. Passing
        in a list of lists, each sub-list becomes a row added to the display as
        the next bottom-most element. Elements of each sub-list are placed as
        columns from left to right.

        :param mosaic: A list of lists of widgets
        """
        assert type(mosaic) == list
        assert len(mosaic) != 0 and type(mosaic[0]) == list
        main_layout = QVBoxLayout()
        for row in mosaic:
            sub_layout = QHBoxLayout()
            for element in row:
                sub_layout.addWidget(element)
            main_layout.addLayout(sub_layout)

        return VisualizerContext(layout=main_layout, state=state)
