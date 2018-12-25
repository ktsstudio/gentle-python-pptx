from typing import Iterator, List

from gpptx.pptx_tools.index import make_pptx_index
from gpptx.pptx_tools.slide import delete_slide, delete_all_slides_except
from gpptx.storage.cache.cacher import CacheKey
from gpptx.storage.cache.decorator import CacheDecoratable
from gpptx.storage.storage import PresentationStorage
from gpptx.types.slide import Slide
from gpptx.util.annotations import dangerous_method


class SlidesCollection(CacheDecoratable):
    __slots__ = ('_slide_paths',)

    def __init__(self, storage: PresentationStorage, cache_key: CacheKey, slide_paths: List[str]):
        self._storage = storage
        self._storage_cache_key = cache_key
        self._slide_paths = slide_paths

    def __getitem__(self, index: int) -> Slide:
        return Slide(self._storage, self._storage_cache_key.make_son(str(index)), self._slide_paths[index])

    def __iter__(self) -> Iterator[Slide]:
        for i, path in enumerate(self._slide_paths):
            yield Slide(self._storage, self._storage_cache_key.make_son(str(i)), path)

    def __len__(self):
        return len(self._slide_paths)

    @dangerous_method
    def delete(self, index: int, do_garbage_collection: bool = True) -> None:
        delete_slide(loader=self._storage.loader, slide_index=make_pptx_index(index),
                     do_garbage_collection=do_garbage_collection)
        raise NotImplementedError  # TODO update cache

    @dangerous_method
    def delete_all_except(self, index: int) -> None:
        delete_all_slides_except(loader=self._storage.loader, slide_index=make_pptx_index(index))
        raise NotImplementedError  # TODO update cache
