class Cheese:
    aprop: int

    def __init__(self) -> None:
        print("new cheese")
        self.aprop = 5

    def printer(self):
        print(f"aprop: {self.aprop}")


class Wrapper:
    another: Cheese

    def __init__(self, another_class_instance) -> None:
        self.another = another_class_instance

    def __getattr__(self, name):
        print("getting")
        return getattr(self.another, name)

    def printer(self):
        print("now in the wrapped printer")
        self.another.printer()


def main():

    print("starting")
    wrapped_chese = Wrapper(Cheese())
    wrapped_chese.printer()


main()
