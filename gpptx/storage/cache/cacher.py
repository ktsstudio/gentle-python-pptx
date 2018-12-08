import copy
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
        self._is_persisting_cache_changed_since_load = False

    def cache_persist(self, key: CacheKey, value: Any, do_change_flag: bool = True) -> None:
        if not self._is_ok_for_persisting_cache(value):
            raise ValueError(f'Value of type {type(value)} is not allowed for persisting cache')

        self._persisting_cache[str(key)] = value

        if do_change_flag:
            self._is_persisting_cache_changed_since_load = True

    def cache_local(self, key: CacheKey, value: Any) -> None:
        self._local_cache[str(key)] = value

    def delete_from_persisting_cache(self, key: CacheKey) -> None:
        key_str = str(key)

        keys_to_delete: List[str] = list()
        for k in self._persisting_cache.keys():
            if k.startswith(key_str):
                keys_to_delete.append(k)

        for k in keys_to_delete:
            del self._persisting_cache[k]

    def delete_from_local_cache(self, key: CacheKey) -> None:
        key_str = str(key)

        keys_to_delete: List[str] = list()
        for k in self._local_cache.keys():
            if k.startswith(key_str):
                keys_to_delete.append(k)

        for k in keys_to_delete:
            del self._local_cache[k]

    def delete_from_any_cache(self, key: CacheKey) -> None:
        self.delete_from_persisting_cache(key)
        self.delete_from_local_cache(key)

    def get_from_persisting_cache(self, key: CacheKey) -> Optional[Any]:
        return self._persisting_cache.get(str(key))

    def get_from_local_cache(self, key: CacheKey) -> Optional[Any]:
        return self._local_cache.get(str(key))

    def load_persisting_cache(self, cache: Dict[str, Any]) -> None:
        for k, v in cache:
            self.cache_persist(k, v, do_change_flag=False)

    def dump_persisting_cache(self) -> Dict[str, Any]:
        return self._persisting_cache

    def duplicate(self):
        new_cacher = Cacher()

        new_cacher._persisting_cache = copy.copy(self._persisting_cache)
        new_cacher._local_cache = copy.deepcopy(self._local_cache)
        new_cacher._is_persisting_cache_changed_since_load = self._is_in_persisting_cache_allowed_types

        return new_cacher

    @property
    def is_persisting_cache_changed_since_load(self) -> bool:
        return self._is_persisting_cache_changed_since_load

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
