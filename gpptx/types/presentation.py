from typing import List

from gpptx.pptx_tools.paths import SLIDES_PATH_PREFIX
from gpptx.storage.cache.cacher import CacheKey
from gpptx.storage.cache.decorator import cache_persist, CacheDecoratable
from gpptx.storage.storage import PresentationStorage
from gpptx.types.slides_coll import SlidesCollection


class Presentation(CacheDecoratable):
    __slots__ = ()

    def __init__(self, storage: PresentationStorage, cache_key: CacheKey):
        self._storage = storage
        self._storage_cache_key = cache_key

    @property
    def slides(self) -> SlidesCollection:
        return SlidesCollection(self._storage, self._storage_cache_key.make_son('slides'), self._slide_paths)

    @cache_persist
    @property
    def _slide_paths(self) -> List[str]:
        return [path for path in self._storage.loader.get_filelist() if path.startswith(SLIDES_PATH_PREFIX)]
