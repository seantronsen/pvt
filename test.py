class Root:

    def __init__(self) -> None:
        pass


class Plant(Root):

    color: int

    def __init__(self) -> None:
        super().__init__()


class Tree(Root):

    height: int

    def __init__(self) -> None:
        super().__init__()


def main():
    root0, root1 = Root(), Root()
    plant = Plant()
    tree = Tree()

    print(f"root to root: {type(root0) == type(root1)}")

    print(f"root to plant: {type(root0) == type(plant)}")
    print(f"plant to root: {type(plant) == type(root1)}")

    print(f"root to tree: {type(root0) == type(tree)}")
    print(f"tree to root: {type(tree) == type(root1)}")

    print(f"tree to plant: {type(tree) == type(plant)}")
    print(f"plant to tree: {type(plant) == type(tree)}")

    print(f"root isinstance of root: {isinstance(root1, type(root0))}")
    print(f"plant isinstance of root: {isinstance(plant, type(root0))}")
    print(f"tree isinstance of root: {isinstance(tree, type(root0))}")
    print(f"List isinstance of root: {isinstance([], type(root0))}")

    print(f"root issubclass of root: {issubclass(type(root1), type(root0))}")
    print(f"plant issubclass of root: {issubclass(type(plant), type(root0))}")
    print(f"tree issubclass of root: {issubclass(type(tree), type(root0))}")
    print(f"List issubclass of root: {issubclass(type([]), type(root0))}")


if __name__ == "__main__":
    main()
