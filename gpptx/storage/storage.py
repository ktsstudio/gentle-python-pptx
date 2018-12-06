from gpptx.storage.cache.cacher import Cacher
from gpptx.storage.pptx.loader import Loader


class PresentationStorage:
    def __init__(self, loader: Loader, cacher: Cacher):
        self._loader = loader
        self._cacher = cacher

    @property
    def loader(self) -> Loader:
        return self._loader

    @property
    def cacher(self) -> Cacher:
        return self._cacher
