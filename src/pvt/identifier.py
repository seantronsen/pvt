class IdManager(object):
    """
    Simple singleton class that spits out incremental hexidecimal IDs. This
    class is primarily used to associate performance logs with specific widgets
    on the currently displayed window.
    """

    counter = 0
    singleton: "IdManager"

    def __new__(cls):
        if not hasattr(cls, "singleton"):
            cls.singleton = super(IdManager, cls).__new__(cls)
        return cls.singleton

    def generate_identifier(self):
        id = self.counter
        self.counter += 1
        return f"{id:08x}"
