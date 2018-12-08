from io import BytesIO
from typing import Union, BinaryIO, Dict, Any

from gpptx.storage.cache.cacher import Cacher, CacheKey
from gpptx.storage.pptx.loader import Loader
from gpptx.storage.storage import PresentationStorage
from gpptx.types.presentation import Presentation


class PresentationContainer:
    def __init__(self, file: Union[BinaryIO, BytesIO] = None, cache: Dict[str, Any] = None):
        loader = Loader()
        if file is not None:
            loader.load(file)

        cacher = Cacher()
        if cache is not None:
            cacher.load_persisting_cache(cache)

        self._storage = PresentationStorage(loader, cacher)
        self._root_cache_key = CacheKey('')

    def save(self, dest: Union[BinaryIO, BytesIO]) -> None:
        self._storage.loader.save(dest)

    def dump_cache(self) -> Dict[str, Any]:
        return self._storage.cacher.dump_persisting_cache()

    def duplicate(self):
        new_container = PresentationContainer()
        new_container._storage._loader = self._storage.loader.duplicate()
        new_container._storage._cacher = self._storage.cacher.duplicate()
        return new_container

    @property
    def presentation(self) -> Presentation:
        return Presentation(self._storage, self._root_cache_key)

    @property
    def is_cache_changed_since_load(self) -> bool:
        return self._storage.cacher.is_persisting_cache_changed_since_load
