from PySide6.QtCore import QTimer
from qtviewer.panels import StatefulPane
import numpy as np


class Animator:
    __contents: StatefulPane
    timer: QTimer
    timer_ptr: np.uintp

    def __init__(
        self,
        fps: float,
        **_,
    ) -> None:
        super().__init__()
        assert not fps <= 0
        self.__contents.__state.onUpdate = self.update
        self.timer_ptr = np.uintp(0)
        self.timer = QTimer()
        self.timer.timeout.connect(self.timer_timeout)
        self.timer.start(int(1000 / fps))

    def __getattr__(self, name):
        return getattr(self.__contents, name)

    def timer_timeout(self):
        """
        Exists to provide a timed update feature for animation / sequence data
        where new frames should be delivered at the specified interval.
        """
        self.timer_ptr += np.uintp(1)
        self.__contents.force_flush()

    def update(self, **kwargs):
        """
        This function is the callback provided to the State instance and is
        executed on each state change. The user specified callback is executed
        by this callback. If you wish to exist in user land, don't worry about
        anything other than the one callback you're required to define.
        """

        self.__contents.update(timer_ptr=self.timer_ptr, **kwargs)
