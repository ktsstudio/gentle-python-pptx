from typing import Iterator, List

from gpptx.pptx_tools.index import make_pptx_index
from gpptx.pptx_tools.slide import delete_slide, delete_all_slides_except
from gpptx.storage.cache.cacher import CacheKey
from gpptx.storage.cache.decorator import CacheDecoratable
from gpptx.storage.storage import PresentationStorage
from gpptx.types.slide import Slide


class SlidesCollection(CacheDecoratable):
    __slots__ = ('_presentation', '_slide_paths')

    def __init__(self, storage: PresentationStorage, cache_key: CacheKey, presentation, slide_paths: List[str]):
        from gpptx.types.presentation import Presentation

        super().__init__(storage, cache_key)
        self._presentation: Presentation = presentation
        self._slide_paths = slide_paths

    def __getitem__(self, index: int) -> Slide:
        return Slide(self._storage, self._storage_cache_key.make_son(str(index)), self._presentation, self._slide_paths[index])

    def __iter__(self) -> Iterator[Slide]:
        for i, path in enumerate(self._slide_paths):
            yield Slide(self._storage, self._storage_cache_key.make_son(str(i)), self._presentation, path)

    def __len__(self):
        return len(self._slide_paths)

    def delete(self, index: int, do_garbage_collection: bool = True) -> None:
        # delete
        delete_slide(loader=self._storage.loader, slide_index=make_pptx_index(index),
                     do_garbage_collection=do_garbage_collection)

        # update cache
        self._storage.cacher.delete_from_any_cache(self._storage_cache_key.make_son(str(index)))

        for i in range(index+1, len(self)):
            self._storage.cacher.rename_branch_in_any_cache(self._storage_cache_key.make_son(str(i)), str(i-1))

        self._slide_paths.pop(index)

    def delete_all_except(self, index: int) -> None:
        # delete
        delete_all_slides_except(loader=self._storage.loader, slide_index=make_pptx_index(index))

        # update cache
        for i in range(0, len(self)):
            if i == index:
                continue
            self._storage.cacher.delete_from_any_cache(self._storage_cache_key.make_son(str(i)))

        self._storage.cacher.rename_branch_in_any_cache(self._storage_cache_key.make_son(str(index)), str(0))

        self._slide_paths = [self._slide_paths[index]]
