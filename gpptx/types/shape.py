from abc import ABC
from enum import Enum
from operator import xor
from typing import Optional, Callable, Type

from lxml import etree
from lxml.etree import ElementTree

from gpptx.pptx_tools.xml_namespaces import pptx_xml_ns
from gpptx.storage.cache.cacher import CacheKey
from gpptx.storage.cache.decorator import cache_persist_property, cache_local_property, update_decorator_cache, \
    help_lazy_list_property, help_lazy_property
from gpptx.storage.cache.lazy import Lazy, LazyList, LazyByFunction
from gpptx.storage.storage import PresentationStorage
from gpptx.types.color_maker import ColorMaker
from gpptx.types.fill import Fill, SolidFill, GradientFill
from gpptx.types.image import Image, SolidPatternImage, GradientPatternImage, PlaceholderImage
from gpptx.types.text import TextFrame, VerticalAlign, HorizontalAlign
from gpptx.types.units import Emu
from gpptx.types.xml_node import CacheDecoratableXmlNode
from gpptx.util.list import first_or_none


class ShapeType(Enum):
    TEXT = 1
    DUAL_IMAGE_AND_PATTERN_SOLID = 2
    DUAL_IMAGE_AND_PATTERN_GRADIENT = 3
    RASTER_IMAGE = 4
    GROUP = 5
    PLACEHOLDER = 6
    UNKNOWN = 7
    VECTOR_IMAGE = 8
    DUAL_TEXT_AND_PLACEHOLDER = 9
    DUAL_IMAGE_AND_PLACEHOLDER = 10
    DUAL_TEXT_AND_IMAGE_AND_PATTERN_SOLID = 11
    DUAL_TEXT_AND_IMAGE_AND_PATTERN_GRADIENT = 12


class Shape(CacheDecoratableXmlNode, ABC):
    __slots__ = ('_shape_xml_getter', '_slide_like')

    def __init__(self, storage: PresentationStorage, cache_key: CacheKey, shape_xml_getter: Lazy, slide_like):
        super().__init__(storage, cache_key)
        self._shape_xml_getter = shape_xml_getter
        self._slide_like = slide_like

    @property
    def xml(self) -> ElementTree:
        return self._shape_xml_getter()

    def save_xml(self) -> None:
        self.slide.save_xml()

    @property
    def slide(self):
        return self._slide_like

    @cache_persist_property
    def shape_id(self) -> int:
        assert self._c_nv_pr is not None
        id_str = self._c_nv_pr.get('id')
        assert id_str is not None
        return int(id_str)

    @cache_persist_property
    def name(self) -> str:
        assert self._c_nv_pr is not None
        return self._c_nv_pr.get('name', default='')

    @cache_persist_property
    def x(self) -> Optional[Emu]:
        if self._xfrm_off is not None:
            x_str = self._xfrm_off.get('x')
            if x_str is not None:
                return Emu(x_str)
        if self.do_use_defaults_when_null:
            return self._default_x
        return None

    @property
    def _default_x(self) -> Emu:
        return Emu(0)

    @x.serializer
    def x(self, v: Emu) -> int:
        return int(v)

    @x.unserializer
    def x(self, v: int) -> Emu:
        return Emu(v)

    @x.setter
    def x(self, v: Emu) -> None:
        if self._xfrm_off is None:
            if self._sp_pr is None:
                self._make_new_sp_pr()
            if self._xfrm is None:
                self._make_new_xfrm()
            else:
                self._make_new_xfrm_off()
        self._xfrm_off.set('x', str(v))
        self.save_xml()

    @cache_persist_property
    def y(self) -> Optional[Emu]:
        if self._xfrm_off is not None:
            y_str = self._xfrm_off.get('y')
            if y_str is not None:
                return Emu(y_str)
        if self.do_use_defaults_when_null:
            return self._default_y
        return None

    @property
    def _default_y(self) -> Emu:
        return Emu(0)

    @y.serializer
    def y(self, v: Emu) -> int:
        return int(v)

    @y.unserializer
    def y(self, v: int) -> Emu:
        return Emu(v)

    @y.setter
    def y(self, v: Emu) -> None:
        if self._xfrm_off is None:
            if self._sp_pr is None:
                self._make_new_sp_pr()
            if self._xfrm is None:
                self._make_new_xfrm()
            else:
                self._make_new_xfrm_off()
        self._xfrm_off.set('y', str(v))
        self.save_xml()

    @cache_persist_property
    def width(self) -> Optional[Emu]:
        if self._xfrm_ext is not None:
            cx_str = self._xfrm_ext.get('cx')
            if cx_str is not None:
                return Emu(cx_str)
        if self.do_use_defaults_when_null:
            return self._default_width
        return None

    @property
    def _default_width(self) -> Emu:
        return Emu(0)

    @width.serializer
    def width(self, v: Emu) -> int:
        return int(v)

    @width.unserializer
    def width(self, v: int) -> Emu:
        return Emu(v)

    @width.setter
    def width(self, v: Emu) -> None:
        if self._xfrm_ext is None:
            if self._sp_pr is None:
                self._make_new_sp_pr()
            if self._xfrm is None:
                self._make_new_xfrm()
            else:
                self._make_new_xfrm_ext()
        self._xfrm_ext.set('cx', str(v))
        self.save_xml()

    @cache_persist_property
    def height(self) -> Optional[Emu]:
        if self._xfrm_ext is not None:
            cy_str = self._xfrm_ext.get('cy')
            if cy_str is not None:
                return Emu(cy_str)
        if self.do_use_defaults_when_null:
            return self._default_height
        return None

    @property
    def _default_height(self) -> Emu:
        return Emu(0)

    @height.serializer
    def height(self, v: Emu) -> int:
        return int(v)

    @height.unserializer
    def height(self, v: int) -> Emu:
        return Emu(v)

    @height.setter
    def height(self, v: Emu) -> None:
        if self._xfrm_ext is None:
            if self._sp_pr is None:
                self._make_new_sp_pr()
            if self._xfrm is None:
                self._make_new_xfrm()
            else:
                self._make_new_xfrm_ext()
        self._xfrm_ext.set('cy', str(v))
        self.save_xml()

    @property
    def color_maker(self) -> ColorMaker:
        return ColorMaker(self)

    @cache_local_property
    def _c_nv_pr(self) -> Optional[ElementTree]:
        return first_or_none(self.xml.xpath('.//p:cNvPr[1]', namespaces=pptx_xml_ns))

    @cache_local_property
    def _sp_pr(self) -> Optional[ElementTree]:
        return first_or_none(self.xml.xpath('p:spPr[1]', namespaces=pptx_xml_ns))

    @cache_local_property
    def _xfrm(self) -> Optional[ElementTree]:
        if self._sp_pr is None:
            return None
        return first_or_none(self._sp_pr.xpath('a:xfrm[1]', namespaces=pptx_xml_ns))

    @cache_local_property
    def _xfrm_off(self) -> Optional[ElementTree]:
        if self._xfrm is None:
            return None
        return first_or_none(self._xfrm.xpath('a:off[1]', namespaces=pptx_xml_ns))

    @cache_local_property
    def _xfrm_ext(self) -> Optional[ElementTree]:
        if self._xfrm is None:
            return None
        return first_or_none(self._xfrm.xpath('a:ext[1]', namespaces=pptx_xml_ns))

    def _make_new_sp_pr(self):
        new_sp_pr = etree.Element('{%s}spPr' % pptx_xml_ns['p'])
        self.xml.append(new_sp_pr)
        update_decorator_cache(self, '_sp_pr', new_sp_pr, do_change_persisting_cache=False)

    def _make_new_xfrm(self):
        new_xfrm = etree.Element('{%s}xfrm' % pptx_xml_ns['a'])
        self._sp_pr.append(new_xfrm)
        update_decorator_cache(self, '_xfrm', new_xfrm, do_change_persisting_cache=False)
        self._make_new_xfrm_off()
        self._make_new_xfrm_ext()

    def _make_new_xfrm_off(self):
        new_xfrm_off = etree.Element('{%s}off' % pptx_xml_ns['a'])
        new_xfrm_off.set('x', '0')
        new_xfrm_off.set('y', '0')
        self._xfrm.append(new_xfrm_off)
        update_decorator_cache(self, '_xfrm_off', new_xfrm_off, do_change_persisting_cache=False)

    def _make_new_xfrm_ext(self):
        new_xfrm_ext = etree.Element('{%s}ext' % pptx_xml_ns['a'])
        new_xfrm_ext.set('cx', '0')
        new_xfrm_ext.set('cy', '0')
        self._xfrm.append(new_xfrm_ext)
        update_decorator_cache(self, '_xfrm_ext', new_xfrm_ext, do_change_persisting_cache=False)


class TextShape(Shape):
    __slots__ = ()

    def __init__(self, storage: PresentationStorage, cache_key: CacheKey, shape_xml_getter: Lazy, slide_like):
        super().__init__(storage, cache_key, shape_xml_getter, slide_like)

    @property
    def text_frame(self) -> TextFrame:
        return TextFrame(self._storage, self._storage_cache_key.make_son('text_frame'),
                         LazyByFunction(lambda: self._tx_body), self)

    @property
    def _default_vertical_align(self) -> VerticalAlign:
        return VerticalAlign.TOP

    @property
    def _default_horizontal_align(self) -> HorizontalAlign:
        return HorizontalAlign.LEFT

    @cache_local_property
    def _tx_body(self) -> Optional[ElementTree]:
        return first_or_none(self.xml.xpath('p:txBody[1]', namespaces=pptx_xml_ns))


class PatternType(Enum):
    SOLID = 1
    GRADIENT = 2


class PatternShape(Shape):
    __slots__ = ('_pattern_type',)

    def __init__(self, storage: PresentationStorage, cache_key: CacheKey, shape_xml_getter: Lazy, slide_like,
                 pattern_type: PatternType):
        super().__init__(storage, cache_key, shape_xml_getter, slide_like)
        self._pattern_type = pattern_type

    @property
    def fill(self) -> Fill:
        if self._pattern_type == PatternType.SOLID:
            return SolidFill(self)
        elif self._pattern_type == PatternType.GRADIENT:
            return GradientFill(self)


class ImageShape(Shape):
    __slots__ = ('_image',)

    def __init__(self, storage: PresentationStorage, cache_key: CacheKey, shape_xml_getter: Lazy, slide_like,
                 image: Optional[Image] = None, image_maker: Callable[[Shape], Image] = None):
        super().__init__(storage, cache_key, shape_xml_getter, slide_like)
        assert xor(image is None, image_maker is None)
        if image is not None:
            self._image = image
        elif image_maker is not None:
            self._image = image_maker(self)

    @property
    def image(self) -> Image:
        return self._image


class GroupShape(Shape):
    __slots__ = ()

    def __init__(self, storage: PresentationStorage, cache_key: CacheKey, shape_xml_getter: Lazy, slide_like):
        super().__init__(storage, cache_key, shape_xml_getter, slide_like)

    @property
    def shapes(self):
        from gpptx.types.shapes_coll import ShapesCollection

        return ShapesCollection(self._storage, self._storage_cache_key.make_son('shapes'),
                                self._shape_xmls, self.shapes_root_getter, self._slide_like)

    @cache_persist_property
    def children_offset_x(self) -> Emu:
        if self._xfrm_ch_off is not None:
            x_str = self._xfrm_ch_off.get('x')
            if x_str is not None:
                return Emu(x_str)
        return Emu(0)

    @children_offset_x.serializer
    def children_offset_x(self, v: Emu) -> int:
        return int(v)

    @children_offset_x.unserializer
    def children_offset_x(self, v: int) -> Emu:
        return Emu(v)

    @cache_persist_property
    def children_offset_y(self) -> Emu:
        if self._xfrm_ch_off is not None:
            y_str = self._xfrm_ch_off.get('y')
            if y_str is not None:
                return Emu(y_str)
        return Emu(0)

    @children_offset_y.serializer
    def children_offset_y(self, v: Emu) -> int:
        return int(v)

    @children_offset_y.unserializer
    def children_offset_y(self, v: int) -> Emu:
        return Emu(v)

    @cache_local_property
    def _xfrm_ch_off(self) -> Optional[ElementTree]:
        if self._xfrm is None:
            return None
        return first_or_none(self._xfrm.xpath('a:chOff[1]', namespaces=pptx_xml_ns))

    @help_lazy_list_property
    def _shape_xmls(self) -> LazyList:
        def find():
            els = self.xml.xpath('./*/p:spPr[1]/..', namespaces=pptx_xml_ns)

            els_at_indexes_to_remove = list()
            for i, el in enumerate(els):
                if el.tag.endswith('Pr'):
                    els_at_indexes_to_remove.append(i)
            delete_shift = 0
            for i in els_at_indexes_to_remove:
                els.pop(i - delete_shift)
                delete_shift += 1

            return els

        return LazyList(find)

    @help_lazy_property
    def shapes_root_getter(self) -> Lazy:
        def find():
            return self.xml

        return LazyByFunction(find)


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


# noinspection PyUnresolvedReferences,PyProtectedMember
class _PlaceholderShapeOverrides:
    """
    Deriving class must have attributes:
        _placeholder_type_fn: Callable[[], PlaceholderType]
        _slide_like: SlideLike
    """

    __slots__ = ()

    @property
    def _default_x(self) -> Emu:
        if self._placeholder_type_fn() == PlaceholderType.CENTER_TITLE:
            return Emu(0)
        else:
            return super()._default_x

    @property
    def _default_y(self) -> Emu:
        if self._placeholder_type_fn() == PlaceholderType.CENTER_TITLE:
            return Emu(0)
        else:
            return super()._default_y

    @property
    def _default_width(self) -> Emu:
        if self._placeholder_type_fn() == PlaceholderType.CENTER_TITLE:
            return self._slide_like.width
        else:
            return super()._default_width

    @property
    def _default_height(self) -> Emu:
        if self._placeholder_type_fn() == PlaceholderType.CENTER_TITLE:
            return self._slide_like.height
        else:
            return super()._default_height

    @property
    def _default_vertical_align(self) -> VerticalAlign:
        if self._placeholder_type_fn() == PlaceholderType.CENTER_TITLE:
            return VerticalAlign.CENTER
        else:
            return super()._default_vertical_align

    @property
    def _default_horizontal_align(self) -> HorizontalAlign:
        if self._placeholder_type_fn() == PlaceholderType.CENTER_TITLE:
            return HorizontalAlign.CENTER
        else:
            return super()._default_horizontal_align


class PlaceholderShape(_PlaceholderShapeOverrides, Shape):
    __slots__ = ('_placeholder_type_fn',)

    def __init__(self, storage: PresentationStorage, cache_key: CacheKey, shape_xml_getter: Lazy, slide_like):
        super().__init__(storage, cache_key, shape_xml_getter, slide_like)
        self._placeholder_type_fn = lambda: self.placeholder_type

    @cache_persist_property
    def placeholder_type(self) -> PlaceholderType:
        type_ = self._ph.get('type')
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

    @placeholder_type.serializer
    def placeholder_type(self, v: PlaceholderType) -> int:
        return v.value

    @placeholder_type.unserializer
    def placeholder_type(self, v: int) -> PlaceholderType:
        return PlaceholderType(v)

    @cache_local_property
    def _ph(self) -> ElementTree:
        return self.xml.xpath('p:nvSpPr[1]/p:nvPr[1]/p:ph[1]', namespaces=pptx_xml_ns)[0]


class UnknownShape(Shape):
    __slots__ = ()

    def __init__(self, storage: PresentationStorage, cache_key: CacheKey, shape_xml_getter: Lazy, slide_like):
        super().__init__(storage, cache_key, shape_xml_getter, slide_like)


class ShapeDual(Shape, ABC):
    __slots__ = ()

    def can_convert_to(self, t: Type[Shape]) -> bool:
        raise NotImplementedError

    def convert_to(self, t: Type[Shape]):
        raise NotImplementedError


class TextAndPlaceholderShapeDual(_PlaceholderShapeOverrides, ShapeDual):
    __slots__ = ('_placeholder_type_fn',)

    class _TextShapeOverrided(_PlaceholderShapeOverrides, TextShape):
        __slots__ = ('_placeholder_type_fn',)

        def __init__(self, *args, placeholder_type_fn, **kwargs):
            super().__init__(*args, **kwargs)
            self._placeholder_type_fn = placeholder_type_fn

    def __init__(self, storage: PresentationStorage, cache_key: CacheKey, shape_xml_getter: Lazy, slide_like):
        super().__init__(storage, cache_key, shape_xml_getter, slide_like)
        self._placeholder_type_fn = lambda: self.as_placeholder.placeholder_type

    @property
    def as_text(self) -> TextShape:
        return self._TextShapeOverrided(self._storage, self._storage_cache_key, self._shape_xml_getter, self._slide_like,
                                        placeholder_type_fn=self._placeholder_type_fn)

    @property
    def as_placeholder(self) -> PlaceholderShape:
        return PlaceholderShape(self._storage, self._storage_cache_key, self._shape_xml_getter, self._slide_like)

    def can_convert_to(self, t: Type[Shape]) -> bool:
        return t == TextShape or t == PlaceholderShape

    def convert_to(self, t: Type[Shape]):
        if t == TextShape:
            return self.as_text
        elif t == PlaceholderShape:
            return self.as_placeholder


class ImageAndPlaceholderShapeDual(ShapeDual):
    __slots__ = ()

    def __init__(self, storage: PresentationStorage, cache_key: CacheKey, shape_xml_getter: Lazy, slide_like):
        super().__init__(storage, cache_key, shape_xml_getter, slide_like)

    @property
    def as_image(self) -> ImageShape:
        return ImageShape(self._storage, self._storage_cache_key, self._shape_xml_getter, self._slide_like,
                          image=PlaceholderImage(self))

    @property
    def as_placeholder(self) -> PlaceholderShape:
        return PlaceholderShape(self._storage, self._storage_cache_key, self._shape_xml_getter, self._slide_like)

    def can_convert_to(self, t: Type[Shape]) -> bool:
        return t == ImageShape or t == PlaceholderShape

    def convert_to(self, t: Type[Shape]):
        if t == ImageShape:
            return self.as_image
        elif t == PlaceholderShape:
            return self.as_placeholder


class ImageAndPatternShapeDual(ShapeDual):
    __slots__ = ('_pattern_type',)

    def __init__(self, storage: PresentationStorage, cache_key: CacheKey, shape_xml_getter: Lazy, slide_like,
                 pattern_type: PatternType):
        super().__init__(storage, cache_key, shape_xml_getter, slide_like)
        self._pattern_type = pattern_type

    @property
    def as_image(self) -> ImageShape:
        if self._pattern_type == PatternType.SOLID:
            image = SolidPatternImage(self.as_pattern)
        elif self._pattern_type == PatternType.GRADIENT:
            image = GradientPatternImage(self.as_pattern)
        else:
            raise ValueError
        return ImageShape(self._storage, self._storage_cache_key, self._shape_xml_getter, self._slide_like, image=image)

    @property
    def as_pattern(self) -> PatternShape:
        return PatternShape(self._storage, self._storage_cache_key, self._shape_xml_getter, self._slide_like,
                            self._pattern_type)

    def can_convert_to(self, t: Type[Shape]) -> bool:
        return t == ImageShape or t == PatternShape

    def convert_to(self, t: Type[Shape]):
        if t == ImageShape:
            return self.as_image
        elif t == PatternShape:
            return self.as_pattern


class TextAndImageAndPatternShapeDual(ShapeDual):
    __slots__ = ('_pattern_type',)

    def __init__(self, storage: PresentationStorage, cache_key: CacheKey, shape_xml_getter: Lazy, slide_like,
                 pattern_type: PatternType):
        super().__init__(storage, cache_key, shape_xml_getter, slide_like)
        self._pattern_type = pattern_type

    @property
    def as_text(self) -> TextShape:
        return TextShape(self._storage, self._storage_cache_key, self._shape_xml_getter, self._slide_like)

    @property
    def as_image(self) -> ImageShape:
        if self._pattern_type == PatternType.SOLID:
            image = SolidPatternImage(self.as_pattern)
        elif self._pattern_type == PatternType.GRADIENT:
            image = GradientPatternImage(self.as_pattern)
        else:
            raise ValueError
        return ImageShape(self._storage, self._storage_cache_key, self._shape_xml_getter, self._slide_like, image=image)

    @property
    def as_pattern(self) -> PatternShape:
        return PatternShape(self._storage, self._storage_cache_key, self._shape_xml_getter, self._slide_like,
                            self._pattern_type)

    def can_convert_to(self, t: Type[Shape]) -> bool:
        return t == TextShape or t == ImageShape or t == PatternShape

    def convert_to(self, t: Type[Shape]):
        if t == TextShape:
            return self.as_text
        elif t == ImageShape:
            return self.as_image
        elif t == PatternShape:
            return self.as_pattern


def check_shape_type(shape: Shape, t: Type[Shape]) -> bool:
    return isinstance(shape, t) or (isinstance(shape, ShapeDual) and shape.can_convert_to(t))


def check_and_convert_shape_type(shape: Shape, t: Type[Shape]):
    if isinstance(shape, t):
        return shape
    if isinstance(shape, ShapeDual) and shape.can_convert_to(t):
        return shape.convert_to(t)
    return None
