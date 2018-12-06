from typing import Union, Any, List, Optional, Dict
from xml.etree import ElementTree

from gpptx.pptx_tools.xml_namespaces import pptx_xml_ns
from gpptx.storage.cache.cacher import CacheKey
from gpptx.storage.cache.decorators import cache_local, CacheDecoratable, cache_persist
from gpptx.storage.storage import PresentationStorage
from gpptx.types.shape import Shape, GroupShape, ShapeType, TextShape, PatternShape, PatternType, ImageShape, \
    PlaceholderShape, UnknownShape
from gpptx.types.slide import SlideLike


class ShapesCollection(CacheDecoratable):
    __slots__ = ('_shape_xmls', '_slide')

    def __init__(self, storage: PresentationStorage, cache_key: CacheKey, shape_xmls: List[ElementTree],
                 slide: SlideLike):
        self._storage = storage
        self._storage_cache_key = cache_key
        self._shape_xmls = shape_xmls
        self._slide = slide

    def __getitem__(self, shape_id: int) -> Shape:
        shape = self.get(shape_id)
        if shape is None:
            raise ValueError(f'No shape with id {shape_id}')
        return shape

    def __iter__(self):
        for shape_index in range(len(self._shape_xmls)):
            yield self._make_shape(self._get_shape_type(shape_index), shape_index)

    def get(self, shape_id: int, default=None) -> Union[Shape, Any]:
        return self.flatten_as_dict(keep_groups=True).get(shape_id, default=default)

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

    def add(self) -> None:
        raise NotImplementedError  # TODO

    def delete(self, shape_id: int) -> None:
        raise NotImplementedError  # TODO

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

    @cache_persist
    def _get_shape_type(self, shape_index: int) -> ShapeType:
        shape_xml = self._shape_xmls[shape_index]

        is_group = 'grpSp' in shape_xml.tag
        if is_group:
            return ShapeType.GROUP

        is_pic = 'pic' in shape_xml.tag
        if is_pic:
            return ShapeType.IMAGE

        has_tx_body = len(shape_xml.xpath('p:txBody[1]', namespaces=pptx_xml_ns)) == 1
        if has_tx_body:
            return ShapeType.TEXT

        has_solid_fill = len(shape_xml.xpath('p:spPr/a:solidFill[1]', namespaces=pptx_xml_ns)) == 1
        if has_solid_fill:
            return ShapeType.PATTERN_SOLID

        has_grad_fill = len(shape_xml.xpath('p:spPr/a:gradFill[1]', namespaces=pptx_xml_ns)) == 1
        if has_grad_fill:
            return ShapeType.PATTERN_GRADIENT

        has_placeholder = len(shape_xml.xpath('p:nvSpPr/p:nvPr/p:ph[1]', namespaces=pptx_xml_ns)) == 1
        if has_placeholder:
            return ShapeType.PLACEHOLDER

        return ShapeType.UNKNOWN

    def _make_shape(self, shape_type: ShapeType, shape_index: int) -> Shape:
        shape_xml = self._shape_xmls[shape_index]
        cache_key = self._storage_cache_key.make_son(str(shape_index))

        if shape_type == ShapeType.TEXT:
            return TextShape(self._storage, cache_key, shape_xml, self._slide)
        if shape_type == ShapeType.PATTERN_SOLID:
            return PatternShape(self._storage, cache_key, shape_xml, self._slide, PatternType.SOLID)
        if shape_type == ShapeType.PATTERN_GRADIENT:
            return PatternShape(self._storage, cache_key, shape_xml, self._slide, PatternType.GRADIENT)
        if shape_type == ShapeType.IMAGE:
            return ImageShape(self._storage, cache_key, shape_xml, self._slide)
        if shape_type == ShapeType.GROUP:
            return GroupShape(self._storage, cache_key, shape_xml, self._slide)
        if shape_type == ShapeType.PLACEHOLDER:
            return PlaceholderShape(self._storage, cache_key, shape_xml, self._slide)
        if shape_type == ShapeType.UNKNOWN:
            return UnknownShape(self._storage, cache_key, shape_xml, self._slide)
