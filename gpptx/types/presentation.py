from gpptx.types.slide import SlidesCollection


class Presentation:
    def __init__(self):
        raise NotImplementedError

    @property
    def slides(self) -> SlidesCollection:
        raise NotImplementedError
