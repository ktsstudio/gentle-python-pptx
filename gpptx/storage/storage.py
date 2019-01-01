from gpptx.storage.cache.cacher import Cacher
from gpptx.storage.cache.stats import Stats
from gpptx.storage.pptx.loader import Loader


class PresentationStorage:
    def __init__(self, loader: Loader, cacher: Cacher, do_log_stats: bool = False):
        self._loader = loader
        self._cacher = cacher
        self._stats = Stats()
        self._do_log_stats = do_log_stats

    @property
    def loader(self) -> Loader:
        return self._loader

    @property
    def cacher(self) -> Cacher:
        return self._cacher

    @property
    def stats(self) -> Stats:
        return self._stats

    @property
    def do_log_stats(self) -> bool:
        return self._do_log_stats

    @do_log_stats.setter
    def do_log_stats(self, v: bool) -> None:
        self._do_log_stats = v
