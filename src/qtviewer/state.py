from typing import Callable, Dict, Optional


class State:
    """
    An abstract collection of state created using simple python dictionaries.
    Changes in state followed by the flush operation execute a user specifiable
    callback.

    Currently links the behaviors between control widgets and data/content
    display panes.
    """

    storage: Dict
    onUpdate: Callable

    def __init__(
        self,
        callback,
        init: Optional[Dict] = None,
    ) -> None:
        self.storage = init if init is not None else {}
        self.onUpdate = callback

    def __getitem__(self, key):
        return self.storage.get(key)

    def __setitem__(self, key, value):
        self.storage[key] = value

    def flush(self):
        """
        Execute the user specified callback function. Intended use is to flush
        all state changes to the interface when called.
        """
        self.onUpdate(**self.storage)
