from abc import ABC
from typing import Callable, List, Any, Dict, Collection, Type

from gpptx.storage.storage import PresentationStorage


class CacheDecoratable(ABC):
    __slots__ = ('_storage', '_storage_cache_key')


def cache_persist(f: Callable) -> Callable:
    return _CacheDecorator(f, do_use_persisting_cache=True)


def cache_local(f: Callable) -> Callable:
    return _CacheDecorator(f, do_use_persisting_cache=False)


class _CacheDecorator:
    _DECORATOR_MEMBERS = ('_fn', '_do_use_persisting_cache', '_is_fn_property_descriptor')

    def __init__(self, fn: Callable, do_use_persisting_cache: bool):
        self._fn = fn
        self._do_use_persisting_cache = do_use_persisting_cache
        self._is_fn_property_descriptor = isinstance(self.__dict__['_fn'], property)

    def __call__(self, fn_self: CacheDecoratable, *args, **kwargs) -> Any:
        if not self._is_fn_property_descriptor:
            return self._call(self.__dict__['_fn'], fn_self, args, kwargs)
        else:
            raise AttributeError

    def __get__(self, fn_self: CacheDecoratable, fn_cls: Type) -> Any:
        if self._is_fn_property_descriptor:
            # noinspection PyUnresolvedReferences
            return self._call(self.__dict__['_fn'].__get__, fn_self, args=(fn_cls,), do_note_args=False)
        else:
            return self

    def __set__(self, fn_self: CacheDecoratable, value: Any) -> None:
        if self._is_fn_property_descriptor:
            # noinspection PyUnresolvedReferences
            self.__dict__['_fn'].__set__(fn_self, value)
            self.clear_cache()
        else:
            raise AttributeError

    def __getattr__(self, k: str) -> Any:
        if k in self._DECORATOR_MEMBERS:
            return self.__dict__[k]
        return getattr(self.__dict__['_fn'], k)

    def __setattr__(self, k: str, v: Any) -> None:
        if k in self._DECORATOR_MEMBERS:
            self.__dict__[k] = v
            return
        setattr(self.__dict__['_fn'], k, v)

    def clear_cache(self) -> None:
        fn_self: CacheDecoratable = self.__self__
        call_cache_key_name = self._make_call_cache_key_name(self.__dict__['_fn'].__name__)
        # noinspection PyProtectedMember
        son_cache_key = fn_self._storage_cache_key.make_son(call_cache_key_name)
        # noinspection PyProtectedMember
        fn_self._storage.cacher.delete_from_any_cache(son_cache_key)

    def _call(self, fn_call: Callable,
              fn_self: CacheDecoratable, args: Collection[Any] = None, kwargs: Dict[str, Any] = None,
              do_note_args: bool = True):
        # noinspection PyProtectedMember
        if not fn_self._storage_cache_key.do_disable_cache:
            if do_note_args:
                call_cache_key_name = self._make_call_cache_key_name(self.__dict__['_fn'].__name__, args, kwargs)
            else:
                call_cache_key_name = self._make_call_cache_key_name(self.__dict__['_fn'].__name__)
            # noinspection PyProtectedMember
            son_cache_key = fn_self._storage_cache_key.make_son(call_cache_key_name)
        else:
            son_cache_key = None

        # noinspection PyProtectedMember
        if not fn_self._storage_cache_key.do_disable_cache:
            # noinspection PyProtectedMember
            value = self._get_cache_get_fn(fn_self._storage)(son_cache_key)
            if value is not None:
                return value

        if args is None:
            args = tuple()
        if kwargs is None:
            kwargs = dict()
        value = fn_call(fn_self, *args, **kwargs)

        # noinspection PyProtectedMember
        if not fn_self._storage_cache_key.do_disable_cache:
            # noinspection PyProtectedMember
            self._get_cache_save_fn(fn_self._storage)(son_cache_key, value)
        return value

    def _get_cache_get_fn(self, storage: PresentationStorage) -> Callable:
        if self._do_use_persisting_cache:
            return storage.cacher.get_from_persisting_cache
        else:
            return storage.cacher.get_from_local_cache

    def _get_cache_save_fn(self, storage: PresentationStorage) -> Callable:
        if self._do_use_persisting_cache:
            return storage.cacher.cache_persist
        else:
            return storage.cacher.cache_local

    @staticmethod
    def _make_call_cache_key_name(func_name: str, args: Collection[Any] = None, kwargs: Dict[str, Any] = None) -> str:
        parts: List[str] = list()
        parts.append(func_name)
        if args is not None and len(args) != 0:
            for i, it in enumerate(args):
                parts.append(str(i))
                parts.append(str(it))
        if kwargs is not None and len(kwargs) != 0:
            for k, v in kwargs.items():
                parts.append(str(k))
                parts.append(str(v))
        return '.'.join(parts)
