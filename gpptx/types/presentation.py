import re
from typing import List

from gpptx.pptx_tools.paths import SLIDES_PATH_PREFIX_WITH_FILE
from gpptx.storage.cache.cacher import CacheKey
from gpptx.storage.cache.decorator import CacheDecoratable, cache_persist_property
from gpptx.storage.storage import PresentationStorage
from gpptx.types.slides_coll import SlidesCollection


class Presentation(CacheDecoratable):
    _SLIDE_ID_REGEX = re.compile('ppt/slides/slide(\d+).xml')

    __slots__ = ()

    def __init__(self, storage: PresentationStorage, cache_key: CacheKey):
        self._storage = storage
        self._storage_cache_key = cache_key

    @property
    def slides(self) -> SlidesCollection:
        return SlidesCollection(self._storage, self._storage_cache_key.make_son('slides'), self._slide_paths)

    @cache_persist_property
    def _slide_paths(self) -> List[str]:
        paths = [path for path in self._storage.loader.get_filelist() if path.startswith(SLIDES_PATH_PREFIX_WITH_FILE)]
        paths.sort(key=lambda it: int(self._SLIDE_ID_REGEX.match(it)[1]))
        return paths
