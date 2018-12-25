import copy
from typing import Union, Any, List, Optional, Dict, Iterator, Tuple

from lxml.etree import ElementTree

from gpptx.pptx_tools.xml_namespaces import pptx_xml_ns
from gpptx.storage.cache.cacher import CacheKey
from gpptx.storage.cache.decorator import cache_local, CacheDecoratable, cache_persist, cache_persist_property, \
    clear_decorator_cache, update_decorator_cache
from gpptx.storage.cache.lazy import LazyList, Lazy
from gpptx.storage.storage import PresentationStorage
from gpptx.types.shape import Shape, GroupShape, ShapeType, TextShape, PatternShape, PatternType, ImageShape, \
    PlaceholderShape, UnknownShape
from gpptx.util.annotations import dangerous_method


class ShapesCollection(CacheDecoratable):
    __slots__ = ('_shape_xml_getters', '_shapes_root_getter', '_slide')

    def __init__(self, storage: PresentationStorage, cache_key: CacheKey,
                 shape_xml_getters: LazyList, shapes_root_getter: Lazy, slide):
        from gpptx.types.slide import SlideLike

        self._storage = storage
        self._storage_cache_key = cache_key
        self._shape_xml_getters = shape_xml_getters
        self._shapes_root_getter = shapes_root_getter
        self._slide: SlideLike = slide

    def __iter__(self):
        for shape_index in self._shape_xml_getters.iter_indexes():
            yield self.make_shape(shape_index)

    def __len__(self):
        return len(self._shape_xml_getters)

    def return_recursive(self, shape_id: int) -> Union[Shape, Any]:
        shape = self.get_recursive(shape_id)
        if shape is None:
            raise ValueError(f'No shape with id {shape_id}')
        return shape

    def get_recursive(self, shape_id: int, default=None) -> Union[Shape, Any]:
        return self.flatten_as_dict(keep_groups=True).get(shape_id, default)

    def return_direct(self, shape_id: int) -> Shape:
        shape = self.get_direct(shape_id)
        if shape is None:
            raise ValueError(f'No shape with id {shape_id}')
        return shape

    def get_direct(self, shape_id: int, default=None) -> Union[Shape, Any]:
        shape_index = self.get_index_direct(shape_id)
        if shape_index is None:
            return default
        return self.make_shape(shape_index)

    def return_index_direct(self, shape_id: int) -> int:
        index = self.get_index_direct(shape_id)
        if index is None:
            raise ValueError(f'No shape with id {shape_id}')
        return index

    def get_index_direct(self, shape_id: int, default=None) -> Union[int, Any]:
        shape_index = None
        for i in self._shape_xml_getters.iter_indexes():
            shape = self.make_shape(i, fast=True)
            if shape.shape_id == shape_id:
                shape_index = i
        if shape_index is None:
            return default
        return shape_index

    @cache_local
    def get_shape_parents_bloodline(self, shape_id: int) -> List[Shape]:
        def dfs(node: Optional[Shape], children: ShapesCollection) -> Optional[List[Shape]]:
            for child in children:
                if child.shape_id == shape_id:
                    return [child]
                elif isinstance(child, GroupShape):
                    path = dfs(child, child.shapes)
                    if path is not None:
                        if node is not None:
                            path.append(node)
                        return path
            return None

        reversed_path = dfs(None, self)
        return list(reversed(reversed_path))

    def get_shape_parent(self, shape_id: int) -> Optional[Shape]:
        parents_line = self.get_shape_parents_bloodline(shape_id)
        if len(parents_line) == 0:
            return None
        return parents_line[-1]

    @cache_persist_property
    def last_shape_id(self) -> int:
        return max(it.shape_id for it in self.flatten())

    def iter_enumerate(self) -> Iterator[Tuple[int, Shape]]:
        for shape_index in self._shape_xml_getters.iter_indexes():
            yield shape_index, self.make_shape(shape_index)

    def make_shape(self, shape_index: int, fast: bool = False):
        if fast:
            shape_type = ShapeType.UNKNOWN
        else:
            shape_type = self._get_shape_type(shape_index)
        return self._make_shape(shape_type, shape_index)

    @cache_local
    def flatten(self, keep_groups: bool = True) -> List[Shape]:
        result = list()

        for shape in self:
            if isinstance(shape, GroupShape):
                if keep_groups:
                    result.append(shape)
                inner_shapes = shape.shapes.flatten(keep_groups=keep_groups)
                result.extend(inner_shapes)
            else:
                result.append(shape)

        return result

    @cache_local
    def flatten_as_dict(self, keep_groups: bool = True) -> Dict[int, Shape]:
        return {shape.shape_id: shape for shape in self.flatten(keep_groups=keep_groups)}

    @dangerous_method
    def add(self, new_xml: ElementTree) -> int:
        raise NotImplementedError  # TODO

    @dangerous_method
    def delete(self, shape_id: int, do_affect_xml: bool = True, i_wont_save_cache: bool = False) -> None:
        if not do_affect_xml:
            assert i_wont_save_cache

        # find
        shape_index = self.return_index_direct(shape_id)

        # delete
        if do_affect_xml:
            shape_xml = self._shape_xml_getters[shape_index]()
            shape_xml.getparent().remove(shape_xml)
            self._slide.save_xml()

        # update cache
        clear_decorator_cache(self, 'last_shape_id')
        clear_decorator_cache(self, 'flatten')
        clear_decorator_cache(self, 'flatten_as_dict')

        self._shape_xml_getters.pop(shape_index)

    @dangerous_method
    def duplicate(self, shape_id: int) -> int:
        shape_index = self.return_index_direct(shape_id)
        shape = self.make_shape(shape_index, fast=True)
        last_shape_id = self.last_shape_id

        # copy
        xml_copy = copy.deepcopy(shape.xml)
        copy_shape_id = last_shape_id + 1
        xml_copy.xpath('p:nvSpPr[1]/p:cNvPr[1]', namespaces=pptx_xml_ns)[0].set('id', str(copy_shape_id))

        # add
        self._slide.shapes_root_getter().append(xml_copy)
        self._slide.save_xml()

        # update cache
        self._shape_xml_getters.append(xml_copy)
        update_decorator_cache(self, 'last_shape_id', value=copy_shape_id,
                               do_change_persisting_cache=True)
        update_decorator_cache(self, '_get_shape_type', func_args=(len(self._shape_xml_getters)-1,),
                               value=self._get_shape_type(shape_index).value,
                               do_change_persisting_cache=True)
        clear_decorator_cache(self, 'flatten')
        clear_decorator_cache(self, 'flatten_as_dict')

        return copy_shape_id

    @cache_persist
    def _get_shape_type(self, shape_index: int) -> ShapeType:
        shape_xml = self._shape_xml_getters[shape_index]()

        is_group = 'grpSp' in shape_xml.tag
        if is_group:
            return ShapeType.GROUP

        is_pic = 'pic' in shape_xml.tag
        if is_pic:
            return ShapeType.IMAGE

        has_tx_body = len(shape_xml.xpath('p:txBody[1]', namespaces=pptx_xml_ns)) == 1
        if has_tx_body:
            return ShapeType.TEXT

        has_solid_fill = len(shape_xml.xpath('p:spPr[1]/a:solidFill[1]', namespaces=pptx_xml_ns)) == 1
        if has_solid_fill:
            return ShapeType.PATTERN_SOLID

        has_grad_fill = len(shape_xml.xpath('p:spPr[1]/a:gradFill[1]', namespaces=pptx_xml_ns)) == 1
        if has_grad_fill:
            return ShapeType.PATTERN_GRADIENT

        has_placeholder = len(shape_xml.xpath('p:nvSpPr[1]/p:nvPr[1]/p:ph[1]', namespaces=pptx_xml_ns)) == 1
        if has_placeholder:
            return ShapeType.PLACEHOLDER

        return ShapeType.UNKNOWN

    @_get_shape_type.cache_serializer
    def _get_shape_type(self, v: ShapeType) -> int:
        return v.value

    @_get_shape_type.cache_unserializer
    def _get_shape_type(self, v: int) -> ShapeType:
        return ShapeType(v)

    def _make_shape(self, shape_type: ShapeType, shape_index: int) -> Shape:
        shape_xml_getter = self._shape_xml_getters[shape_index]
        cache_key = self._storage_cache_key.make_son(str(shape_index))

        if shape_type == ShapeType.TEXT:
            return TextShape(self._storage, cache_key, shape_xml_getter, self._slide)
        if shape_type == ShapeType.PATTERN_SOLID:
            return PatternShape(self._storage, cache_key, shape_xml_getter, self._slide, PatternType.SOLID)
        if shape_type == ShapeType.PATTERN_GRADIENT:
            return PatternShape(self._storage, cache_key, shape_xml_getter, self._slide, PatternType.GRADIENT)
        if shape_type == ShapeType.IMAGE:
            return ImageShape(self._storage, cache_key, shape_xml_getter, self._slide)
        if shape_type == ShapeType.GROUP:
            return GroupShape(self._storage, cache_key, shape_xml_getter, self._slide)
        if shape_type == ShapeType.PLACEHOLDER:
            return PlaceholderShape(self._storage, cache_key, shape_xml_getter, self._slide)
        if shape_type == ShapeType.UNKNOWN:
            return UnknownShape(self._storage, cache_key, shape_xml_getter, self._slide)
