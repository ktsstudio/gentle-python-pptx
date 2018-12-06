import re

from gpptx.pptx_tools.paths import SLIDES_PATH_PREFIX
from gpptx.storage.cache.cacher import CacheKey
from gpptx.storage.cache.decorators import cache_persist, CacheDecoratable
from gpptx.storage.storage import PresentationStorage
from gpptx.types.slides_coll import SlidesCollection


class Presentation(CacheDecoratable):
    __slots__ = ()

    _SLIDE_INDEX_REGEX = re.compile('slide(\d+)\.xml')

    def __init__(self, storage: PresentationStorage, cache_key: CacheKey):
        self._storage = storage
        self._storage_cache_key = cache_key

    @property
    def slides(self) -> SlidesCollection:
        return SlidesCollection(self._storage, self._storage_cache_key.make_son('slides'), self._slide_count)

    @cache_persist
    @property
    def _slide_count(self) -> int:
        slide_paths = (path for path in self._storage.loader.get_filelist() if path.startswith(SLIDES_PATH_PREFIX))
        last_slide_filepath = max(slide_paths)
        slide_index_match = self._SLIDE_INDEX_REGEX.match(last_slide_filepath)
        last_slide_index = int(slide_index_match[1])

        slides_count = last_slide_index  # because pptx slides' indexes start from 1
        return slides_count
