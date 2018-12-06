from typing import Iterator

from gpptx.pptx_tools.index import make_pptx_index
from gpptx.pptx_tools.paths import make_slide_path
from gpptx.pptx_tools.slide import delete_slide, delete_all_slides_except
from gpptx.storage.cache.cacher import CacheKey
from gpptx.storage.cache.decorators import CacheDecoratable
from gpptx.storage.storage import PresentationStorage
from gpptx.types.slide import Slide


class SlidesCollection(CacheDecoratable):
    __slots__ = ('_slides_count',)

    def __init__(self, storage: PresentationStorage, cache_key: CacheKey, slides_count: int):
        self._storage = storage
        self._storage_cache_key = cache_key
        self._slides_count = slides_count

    def __getitem__(self, index: int) -> Slide:
        return Slide(self._storage, self._storage_cache_key.make_son(str(index)), make_slide_path(index))

    def __iter__(self) -> Iterator[Slide]:
        for i in range(self._slides_count):
            yield Slide(self._storage, self._storage_cache_key, make_slide_path(i))

    def delete(self, index: int, do_garbage_collection: bool = True) -> None:
        delete_slide(loader=self._storage.loader, slide_index=make_pptx_index(index),
                     do_garbage_collection=do_garbage_collection)

    def delete_all_except(self, index: int) -> None:
        delete_all_slides_except(loader=self._storage.loader, slide_index=make_pptx_index(index))
