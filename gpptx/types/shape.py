from abc import ABCMeta
from enum import Enum
from typing import Optional, List
from xml.etree import ElementTree

from gpptx.pptx_tools.xml_namespaces import pptx_xml_ns
from gpptx.storage.cache.cacher import CacheKey
from gpptx.storage.cache.decorators import cache_persist, cache_local, CacheDecoratable
from gpptx.storage.storage import PresentationStorage
from gpptx.types.color_resolver import ColorResolver
from gpptx.types.emu import Emu
from gpptx.types.fill import Fill
from gpptx.types.image import Image
from gpptx.types.shapes_coll import ShapesCollection
from gpptx.types.slide import SlideLike
from gpptx.types.text import TextFrame
from gpptx.types.xml_node import XmlNode
from gpptx.util.list import first_or_none


class ShapeType(Enum):
    TEXT = 1
    PATTERN_SOLID = 2
    PATTERN_GRADIENT = 3
    IMAGE = 4
    GROUP = 5
    PLACEHOLDER = 6
    UNKNOWN = 7


class Shape(CacheDecoratable, XmlNode, metaclass=ABCMeta):
    __slots__ = ('_shape_xml', '_slide')
    
    def __init__(self, storage: PresentationStorage, cache_key: CacheKey, shape_xml: ElementTree, slide: SlideLike):
        super().__init__()
        self._storage = storage
        self._storage_cache_key = cache_key
        self._shape_xml = shape_xml
        self._slide = slide

    @property
    def xml(self) -> ElementTree:
        return self._shape_xml
    
    @property
    def slide(self) -> SlideLike:
        return self._slide

    @property
    def shape_type(self) -> ShapeType:
        raise NotImplementedError

    @cache_persist
    @property
    def shape_id(self) -> int:
        assert self._c_nv_pr is not None
        id_str = self._c_nv_pr.get('id')
        assert id_str is not None
        return int(id_str)

    @cache_persist
    @property
    def name(self) -> str:
        assert self._c_nv_pr is not None
        return self._c_nv_pr.get('name', default='')

    @cache_persist
    @property
    def x(self) -> Optional[Emu]:
        if self._xfrm_off is not None:
            x_str = self._xfrm_off.get('x')
            if x_str is not None:
                return Emu(int(x_str))
        if self.do_use_defaults_when_null:
            return Emu(0)
        return None

    @cache_persist
    @property
    def y(self) -> Optional[Emu]:
        if self._xfrm_off is not None:
            y_str = self._xfrm_off.get('y')
            if y_str is not None:
                return Emu(int(y_str))
        if self.do_use_defaults_when_null:
            return Emu(0)
        return None

    @cache_persist
    def width(self) -> Optional[Emu]:
        if self._xfrm_ext is not None:
            cx_str = self._xfrm_ext.get('cx')
            if cx_str is not None:
                return Emu(int(cx_str))
        if self.do_use_defaults_when_null:
            return Emu(0)
        return None

    @cache_persist
    @property
    def height(self) -> Optional[Emu]:
        if self._xfrm_ext is not None:
            cy_str = self._xfrm_ext.get('cy')
            if cy_str is not None:
                return Emu(int(cy_str))
        if self.do_use_defaults_when_null:
            return Emu(0)
        return None

    @property
    def color_resolver(self) -> ColorResolver:
        return ColorResolver(self)

    @cache_local
    @property
    def _c_nv_pr(self) -> Optional[ElementTree]:
        return first_or_none(self._shape_xml.xpath('p:nvSpPr/p:cNvPr[1]', namespaces=pptx_xml_ns))

    @cache_local
    @property
    def _xfrm(self) -> Optional[ElementTree]:
        return first_or_none(self._shape_xml.xpath('a:xfrm[1]', namespaces=pptx_xml_ns))

    @cache_local
    @property
    def _xfrm_off(self) -> Optional[ElementTree]:
        if self._xfrm is None:
            return None
        return first_or_none(self._xfrm.xpath('a:off[1]', namespaces=pptx_xml_ns))

    @cache_local
    @property
    def _xfrm_ext(self) -> Optional[ElementTree]:
        if self._xfrm is None:
            return None
        return first_or_none(self._xfrm.xpath('a:ext[1]', namespaces=pptx_xml_ns))


class TextShape(Shape):
    __slots__ = ()

    def __init__(self, storage: PresentationStorage, cache_key: CacheKey, shape_xml: ElementTree, slide: SlideLike):
        super().__init__(storage, cache_key, shape_xml, slide)

    @property
    def shape_type(self) -> ShapeType:
        return ShapeType.TEXT

    @property
    def text_frame(self) -> TextFrame:
        return TextFrame(self._storage, self._storage_cache_key.make_son('text_frame'), self._tx_body)

    @cache_local
    @property
    def _tx_body(self) -> Optional[ElementTree]:
        return first_or_none(self.xml.xpath('a:txBody[1]', namespaces=pptx_xml_ns))


class PatternType(Enum):
    SOLID = 1
    GRADIENT = 2


class PatternShape(Shape):
    __slots__ = ('_pattern_type',)

    def __init__(self, storage: PresentationStorage, cache_key: CacheKey, shape_xml: ElementTree, slide: SlideLike,
                 pattern_type: PatternType):
        super().__init__(storage, cache_key, shape_xml, slide)
        self._pattern_type = pattern_type

    @property
    def shape_type(self):
        if self._pattern_type == PatternType.SOLID:
            return ShapeType.PATTERN_SOLID
        elif self._pattern_type == PatternType.GRADIENT:
            return ShapeType.PATTERN_GRADIENT

    @property
    def fill(self) -> Fill:
        raise NotImplementedError  # TODO


class ImageShape(Shape):
    __slots__ = ()

    def __init__(self, storage: PresentationStorage, cache_key: CacheKey, shape_xml: ElementTree, slide: SlideLike):
        super().__init__(storage, cache_key, shape_xml, slide)

    @property
    def shape_type(self) -> ShapeType:
        return ShapeType.IMAGE

    @property
    def image(self) -> Image:
        raise NotImplementedError  # TODO


class GroupShape(Shape):
    __slots__ = ()

    def __init__(self, storage: PresentationStorage, cache_key: CacheKey, shape_xml: ElementTree, slide: SlideLike):
        super().__init__(storage, cache_key, shape_xml, slide)

    @property
    def shape_type(self) -> ShapeType:
        return ShapeType.GROUP

    @property
    def shapes(self) -> ShapesCollection:
        return ShapesCollection(self._storage, self._storage_cache_key.make_son('shapes'), self._shape_xmls, self._slide)

    @property
    def children_offset_x(self) -> Emu:
        if self._xfrm_ch_off is not None:
            x_str = self._xfrm_ch_off.get('x')
            if x_str is not None:
                return Emu(int(x_str))
        return Emu(0)

    @property
    def children_offset_y(self) -> Emu:
        if self._xfrm_ch_off is not None:
            y_str = self._xfrm_ch_off.get('y')
            if y_str is not None:
                return Emu(int(y_str))
        return Emu(0)

    @cache_local
    @property
    def _xfrm_ch_off(self) -> Optional[ElementTree]:
        if self._xfrm is None:
            return None
        return first_or_none(self._xfrm.xpath('a:chOff[1]', namespaces=pptx_xml_ns))

    @cache_local
    @property
    def _shape_xmls(self) -> List[ElementTree]:
        return list(self.xml.xpath('./*/p:spPr/..', namespaces=pptx_xml_ns))


class PlaceholderType(Enum):
    BITMAP = 1
    BODY = 2
    CENTER_TITLE = 3
    CHART = 4
    DATE = 5
    FOOTER = 6
    HEADER = 7
    MEDIA_CLIP = 8
    OBJECT = 9
    ORG_CHART = 10
    PICTURE = 11
    SLIDE_IMAGE = 12
    SLIDE_NUMBER = 13
    SUBTITLE = 14
    TABLE = 15
    TITLE = 16
    UNKNOWN = 17

    
class PlaceholderShape(Shape):
    __slots__ = ()

    def __init__(self, storage: PresentationStorage, cache_key: CacheKey, shape_xml: ElementTree, slide: SlideLike):
        super().__init__(storage, cache_key, shape_xml, slide)

    @property
    def shape_type(self) -> ShapeType:
        return ShapeType.PLACEHOLDER

    @cache_persist
    @property
    def placeholder_type(self) -> PlaceholderType:
        type_ = self.xml.get('type')
        if type_ == 'clipArt':
            return PlaceholderType.BITMAP
        elif type_ == 'body':
            return PlaceholderType.BODY
        elif type_ == 'ctrTitle':
            return PlaceholderType.CENTER_TITLE
        elif type_ == 'chart':
            return PlaceholderType.CHART
        elif type_ == 'dt':
            return PlaceholderType.DATE
        elif type_ == 'ftr':
            return PlaceholderType.FOOTER
        elif type_ == 'hdr':
            return PlaceholderType.HEADER
        elif type_ == 'media':
            return PlaceholderType.MEDIA_CLIP
        elif type_ == 'obj':
            return PlaceholderType.OBJECT
        elif type_ == 'dgm':
            return PlaceholderType.ORG_CHART
        elif type_ == 'pic':
            return PlaceholderType.PICTURE
        elif type_ == 'sldImg':
            return PlaceholderType.SLIDE_IMAGE
        elif type_ == 'sldNum':
            return PlaceholderType.SLIDE_NUMBER
        elif type_ == 'subTitle':
            return PlaceholderType.SUBTITLE
        elif type_ == 'tbl':
            return PlaceholderType.TABLE
        elif type_ == 'title':
            return PlaceholderType.TITLE
        return PlaceholderType.UNKNOWN


class UnknownShape(Shape):
    __slots__ = ()

    def __init__(self, storage: PresentationStorage, cache_key: CacheKey, shape_xml: ElementTree, slide: SlideLike):
        super().__init__(storage, cache_key, shape_xml, slide)

    @property
    def shape_type(self) -> ShapeType:
        return ShapeType.UNKNOWN
