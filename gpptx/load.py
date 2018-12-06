from io import BytesIO
from typing import Union, BinaryIO, Dict, Any

from gpptx.storage.cache.cacher import Cacher, CacheKey
from gpptx.storage.pptx.loader import Loader
from gpptx.storage.storage import PresentationStorage
from gpptx.types.presentation import Presentation


class PresentationContainer:
    def __init__(self, file: Union[BinaryIO, BytesIO], cache: Dict[str, Any] = None):
        loader = Loader()
        loader.load(file)

        cacher = Cacher()
        cacher.load_persisting_cache(cache)

        self._storage = PresentationStorage(loader, cacher)
        self._root_cache_key = CacheKey('')

    @property
    def presentation(self) -> Presentation:
        return Presentation(self._storage, self._root_cache_key)

    def dump_cache(self) -> Dict[str, Any]:
        return self._storage.cacher.dump_persisting_cache()

