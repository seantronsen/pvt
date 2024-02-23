from typing import Callable, Dict, Optional


class State:
    __storage: Dict
    onUpdate: Callable

    def __init__(
        self,
        callback,
        init: Optional[Dict] = None,
    ) -> None:
        self.__storage = init if init is not None else {}
        self.onUpdate = callback

    def __getitem__(self, key):
        return self.__storage.get(key)

    def __setitem__(self, key, value):
        self.__storage[key] = value

    def flush(self):
        self.onUpdate(**self.__storage)
