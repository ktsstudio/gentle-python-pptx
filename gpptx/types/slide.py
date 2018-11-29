from gpptx.types.shape import ShapesCollection


class SlidesCollection:
    def __init__(self):
        raise NotImplementedError

    def __iter__(self):
        raise NotImplementedError

    def delete(self, index: int) -> None:
        raise NotImplementedError

    def delete_all_except(self, index: int) -> None:
        raise NotImplementedError


class Slide:
    def __init__(self):
        raise NotImplementedError

    @property
    def shapes(self, with_layout_shapes: bool = False) -> ShapesCollection:
        raise NotImplementedError

