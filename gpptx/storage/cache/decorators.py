from abc import ABCMeta
from functools import wraps
from typing import Callable, List, Any, Dict, Tuple

from gpptx.storage.cache.cacher import CacheKey


class CacheDecoratable(metaclass=ABCMeta):
    __slots__ = ('_storage', '_storage_cache_key')


def cache_persist(f: Callable) -> Callable:
    @wraps(f)
    def wrapped(self: CacheDecoratable, *args, **kwargs) -> Any:
        if not self._storage_cache_key.do_disable_cache:
            son_cache_key: CacheKey = self._storage_cache_key.make_son(_make_cache_key_name(f.__name__, args, kwargs))
        else:
            son_cache_key = None

        if not self._storage_cache_key.do_disable_cache:
            value = self._storage.cacher.get_from_persisting_cache(son_cache_key)
            if value is not None:
                return value

        value = f(self, *args, **kwargs)
        if not self._storage_cache_key.do_disable_cache:
            self._storage.cacher.cache_persist(son_cache_key, value)
        return value

    return wrapped


def cache_local(f: Callable) -> Callable:
    @wraps(f)
    def wrapped(self: CacheDecoratable, *args, **kwargs) -> Any:
        if not self._storage_cache_key.do_disable_cache:
            son_cache_key: CacheKey = self._storage_cache_key.make_son(_make_cache_key_name(f.__name__, args, kwargs))
        else:
            son_cache_key = None

        if not self._storage_cache_key.do_disable_cache:
            value = self._storage.cacher.get_from_local_cache(son_cache_key)
            if value is not None:
                return value

        value = f(self, *args, **kwargs)
        if not self._storage_cache_key.do_disable_cache:
            self._storage.cacher.cache_local(son_cache_key, value)
        return value

    return wrapped


def _make_cache_key_name(func_name: str, args: Tuple[Any], kwargs: Dict[str, Any]) -> str:
    parts: List[str] = list()
    parts.append(func_name)
    if len(args) != 0:
        for i, it in enumerate(args):
            parts.append(str(i))
            parts.append(str(it))
    if len(kwargs) != 0:
        for k, v in kwargs.items():
            parts.append(str(k))
            parts.append(str(v))
    return '.'.join(parts)
