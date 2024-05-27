from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QPushButton
from pyqtgraph import LayoutWidget
from pvt.panels import StatefulPane
import numpy as np


class Animator:
    animation_content: StatefulPane
    timer: QTimer
    animation_tick: np.uintp

    def __init__(
        self,
        fps: float,
        contents: StatefulPane,
    ) -> None:
        assert not fps <= 0
        super().__init__()
        self.animation_content = contents
        self.animation_content.pane_state.onUpdate = self.update
        self.animation_tick = np.uintp(0)
        self.timer = QTimer(parent=self.animation_content)
        self.timer.timeout.connect(self.on_tick)
        self.tick_time = int(1000 / fps)
        self.timer.start(self.tick_time)

    def __getattr__(self, name):
        return getattr(self.animation_content, name)

    def content_flush(self):
        self.animation_content.force_flush()

    def on_tick(self):
        """
        Exists to provide a timed update feature for animation / sequence data
        where new frames should be delivered at the specified interval.
        """
        self.animation_tick += np.uintp(1)
        self.content_flush()

    def update(self, **kwargs):
        """
        This function is the callback provided to the State instance and is
        executed on each state change. The user specified callback is executed
        by this callback. If you wish to exist in user land, don't worry about
        anything other than the one callback you're required to define.
        """

        self.animation_content.update(animation_tick=int(self.animation_tick), **kwargs)

    def is_running(self):
        return self.timer.isActive()

    def pause_toggle(self, *a, **k):
        if self.is_running():
            self.timer.stop()
        else:
            self.timer.start(self.tick_time)

    def forward_one_step(self, *a, **k):
        self.animation_tick += 1
        self.content_flush()

    def reverse_one_step(self, *a, **k):
        self.animation_tick -= 1
        self.content_flush()

    def reset(self, *a, **k):
        self.animation_tick = np.uintp(0)
        self.content_flush()


class AnimatorControlBar(LayoutWidget):

    animator: Animator

    def __init__(self, animator: Animator):
        super().__init__()
        self.animator = animator

        self.b_reset = QPushButton("RESET")
        self.b_one_forward = QPushButton(">")
        self.b_one_reverse = QPushButton("<")

        self.b_reset.clicked.connect(self.animator.reset)
        self.b_one_forward.clicked.connect(self.animator.forward_one_step)
        self.b_one_reverse.clicked.connect(self.animator.reverse_one_step)

        self.b_toggle = QPushButton("PLAY")
        self.b_toggle.setCheckable(True)
        self.b_toggle.setChecked(self.animator.is_running())
        self.b_toggle.clicked.connect(self.animator.pause_toggle)

        self.addWidget(self.b_reset, row=0, col=0)
        self.addWidget(self.b_one_reverse, row=0, col=1)
        self.addWidget(self.b_toggle, row=0, col=2)
        self.addWidget(self.b_one_forward, row=0, col=3)
