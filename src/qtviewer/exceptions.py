class PlotDataValueError(ValueError):
    def __init__(self, shape) -> None:
        message = f"expected data shape to be (N,), (N, 2), (M,N), or (M,N,2). received: {shape}"
        super().__init__(message)
