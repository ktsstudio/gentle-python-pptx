from typing import Any, Dict, List, Optional


class CacheKey:
    __slots__ = ('name', 'parent', 'root', 'do_disable_cache')

    def __init__(self, name: str, parent=None, do_disable_cache: bool = None):
        self.name = name
        self.parent = parent

        if self.parent is None:
            self.root = self
        else:
            self.root = self.parent.root

        if do_disable_cache is not None:
            self.do_disable_cache = do_disable_cache
        else:
            if self.parent is not None:
                self.do_disable_cache = self.parent.do_disable_cache
            else:
                self.do_disable_cache = False

    def __str__(self) -> str:
        reversed_path: List[str] = list()

        current_key = self
        while current_key is not None:
            reversed_path.append(current_key.name)
            current_key = current_key.parent

        return '/'.join(reversed(reversed_path))

    def make_son(self, name: str):
        return CacheKey(name, parent=self)


class Cacher:
    _PERSISTING_CACHE_ALLOWED_TYPES = (int, float, str)

    def __init__(self):
        self._persisting_cache: Dict[str, Any] = dict()
        self._local_cache: Dict[str, Any] = dict()

    def cache_persist(self, key: CacheKey, value: Any) -> None:
        if not self._is_ok_for_persisting_cache(value):
            raise ValueError(f'Value of type {type(value)} is not allowed for persisting cache')
        self._persisting_cache[str(key)] = value

    def cache_local(self, key: CacheKey, value: Any) -> None:
        self._local_cache[str(key)] = value

    def load_persisting_cache(self, cache: Dict[str, Any]) -> None:
        for k, v in cache:
            self.cache_persist(k, v)

    def dump_persisting_cache(self) -> Dict[str, Any]:
        return self._persisting_cache

    def get_from_persisting_cache(self, key: CacheKey) -> Optional[Any]:
        return self._persisting_cache.get(str(key))

    def get_from_local_cache(self, key: CacheKey) -> Optional[Any]:
        return self._local_cache.get(str(key))

    def _is_ok_for_persisting_cache(self, value: Any) -> bool:
        if value is None:
            return True
        if self._is_in_persisting_cache_allowed_types(value):
            return True
        if isinstance(value, list) and \
                all(self._is_in_persisting_cache_allowed_types(it) for it in value):
            return True
        if isinstance(value, dict) and \
                all(isinstance(k, str) for k in value.keys()) and \
                all(self._is_in_persisting_cache_allowed_types(v) for v in value.values()):
            return True
        return False

    def _is_in_persisting_cache_allowed_types(self, value: Any) -> bool:
        return any(isinstance(value, t) for t in self._PERSISTING_CACHE_ALLOWED_TYPES)
