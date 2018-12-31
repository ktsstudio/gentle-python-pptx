from enum import Enum
from typing import List, Optional, Union, Any

from lxml import etree
from lxml.etree import ElementTree

from gpptx.pptx_tools.xml_namespaces import pptx_xml_ns
from gpptx.storage.cache.cacher import CacheKey
from gpptx.storage.cache.decorator import cache_local, CacheDecoratable, cache_persist_property, \
    cache_local_property, clear_decorator_cache, help_lazy_list_property
from gpptx.storage.cache.lazy import LazyList, Lazy
from gpptx.storage.storage import PresentationStorage
from gpptx.types.color import Color, CustomSetColor
from gpptx.types.units import Emu
from gpptx.types.xml_node import CacheDecoratableXmlNode
from gpptx.util.annotations import dangerous_method
from gpptx.util.list import first_or_none


class HorizontalAlign(Enum):
    LEFT = 1
    CENTER = 2
    RIGHT = 3


class VerticalAlign(Enum):
    TOP = 1
    CENTER = 2
    BOTTOM = 3


class Run(CacheDecoratableXmlNode):
    _DEFAULT_FONT_SIZE = Emu.from_pt(16)

    __slots__ = ('_run_xml_getter', '_paragraph')

    def __init__(self, storage: PresentationStorage, cache_key: CacheKey, run_xml_getter: Lazy,
                 paragraph):
        super().__init__(storage, cache_key)
        self._run_xml_getter = run_xml_getter
        self._paragraph: Paragraph = paragraph

    @property
    def xml(self) -> ElementTree:
        return self._run_xml_getter()

    def save_xml(self) -> None:
        self._paragraph.save_xml()

    @property
    def paragraph(self):
        return self._paragraph

    @property
    def text_frame(self):
        return self._paragraph.text_frame

    @cache_persist_property
    def text(self) -> str:
        if self._t is not None:
            return ''.join(self._t.itertext())
        return ''

    @text.setter
    def text(self, v: str) -> None:
        if self._t is None:
            new_xml = etree.Element('{%s}t' % pptx_xml_ns['a'])
            self.xml.append(new_xml)
            clear_decorator_cache(self, '_t')
        self._t.text = v
        self._paragraph.save_xml()

    @cache_persist_property
    def font_name(self) -> Optional[str]:
        latin_xml = self._get_elem('a:latin', do_recursive_find=self.do_use_defaults_when_null)
        if latin_xml is not None:
            return latin_xml.get('typeface')
        return None

    @cache_persist_property
    def font_size(self) -> Optional[Emu]:
        sz_str = self._get_attrib('sz', do_recursive_find=self.do_use_defaults_when_null)
        if sz_str is not None:
            return Emu.from_centripoints(int(sz_str))
        return self._DEFAULT_FONT_SIZE

    @font_size.cache_serializer
    def font_size(self, v: Emu) -> int:
        return int(v)

    @font_size.cache_unserializer
    def font_size(self, v: int) -> Emu:
        return Emu(v)

    @cache_persist_property
    def color_rgb(self) -> Optional[str]:
        color = self._get_color()
        if color is not None:
            return color.rgb_str
        return None

    @cache_persist_property
    def color_alpha(self) -> Optional[float]:
        color = self._get_color()
        if color is not None:
            return color.alpha
        return None

    @cache_persist_property
    def is_bold(self) -> Optional[bool]:
        b_str = self._get_attrib('b', do_recursive_find=self.do_use_defaults_when_null)
        if b_str is not None:
            return bool(b_str)
        return False

    @cache_persist_property
    def is_italic(self) -> Optional[bool]:
        i_str = self._get_attrib('i', do_recursive_find=self.do_use_defaults_when_null)
        if i_str is not None:
            return bool(i_str)
        return False

    @cache_local_property
    def _r_pr(self) -> Optional[ElementTree]:
        return first_or_none(self.xml.xpath('a:rPr[1]', namespaces=pptx_xml_ns))

    @cache_local_property
    def _t(self) -> Optional[ElementTree]:
        return first_or_none(self.xml.xpath('a:t[1]', namespaces=pptx_xml_ns))

    @cache_local
    def _get_color(self) -> Optional[Color]:
        # find xml
        fill_xml = self._get_elem('a:solidFill', do_recursive_find=self.do_use_defaults_when_null)

        if fill_xml is not None:
            clr_xml = first_or_none(list(fill_xml))
            if clr_xml is not None:
                color_resolver = self.paragraph.text_frame.shape.color_maker
                return color_resolver.make_color(clr_xml)

        # use theme
        if self.do_use_defaults_when_null:
            theme = self.paragraph.text_frame.shape.slide.theme
            return CustomSetColor(theme.color_rgbs['tx1'])
        
        return None

    def _get_attrib(self, name: str, do_recursive_find: bool) -> Any:
        if do_recursive_find:
            # noinspection PyProtectedMember
            sources = (self._r_pr, self.paragraph._def_r_pr, self.text_frame._list_def_r_pr, self.text_frame._def_r_pr)
        else:
            sources = (self._r_pr,)
        for xml in sources:
            if xml is not None:
                value = xml.get(name)
                if value is not None:
                    return value
        return None

    def _get_elem(self, name: str, do_recursive_find: bool) -> Any:
        if do_recursive_find:
            # noinspection PyProtectedMember
            sources = (self._r_pr, self.paragraph._def_r_pr, self.text_frame._list_def_r_pr, self.text_frame._def_r_pr)
        else:
            sources = (self._r_pr,)
        for xml in sources:
            if xml is not None:
                matched_elems = xml.xpath(f'{name}[1]', namespaces=pptx_xml_ns)
                if len(matched_elems) != 0:
                    return matched_elems[0]
        return None


class RunCollection(CacheDecoratable):
    __slots__ = ('_run_xml_getters', '_paragraph')

    def __init__(self, storage: PresentationStorage, cache_key: CacheKey,
                 run_xml_getters: LazyList, paragraph):
        self._storage = storage
        self._storage_cache_key = cache_key
        self._run_xml_getters = run_xml_getters
        self._paragraph: Paragraph = paragraph

    def __getitem__(self, index: int) -> Run:
        return Run(self._storage, self._storage_cache_key.make_son(str(index)), self._run_xml_getters[index],
                   self._paragraph)

    def __iter__(self):
        for i, xml in self._run_xml_getters.iter_enumerate():
            yield Run(self._storage, self._storage_cache_key.make_son(str(i)), xml, self._paragraph)

    def __len__(self):
        return len(self._run_xml_getters)

    @dangerous_method
    def add_run(self, new_xml: ElementTree = None) -> int:
        # create
        if new_xml is None:
            new_xml = etree.Element('{%s}r' % pptx_xml_ns['a'])
            new_xml_r_pr = etree.Element('{%s}rPr' % pptx_xml_ns['a'])
            new_xml.append(new_xml_r_pr)
            new_xml_t = etree.Element('{%s}t' % pptx_xml_ns['a'])
            new_xml.append(new_xml_t)

        self._paragraph.xml.append(new_xml)
        self._paragraph.save_xml()

        # update cache
        self._run_xml_getters.append(new_xml)

        # make run object
        new_run_index = self._run_xml_getters.len_with_holes - 1
        return new_run_index

    @dangerous_method
    def delete_run(self, index: int, do_affect_xml: bool = True, i_wont_save_cache: bool = False) -> None:
        if not do_affect_xml:
            assert i_wont_save_cache

        # delete
        if do_affect_xml:
            run_xml = self._run_xml_getters[index]()
            run_xml.getparent().remove(run_xml)
            self._paragraph.save_xml()

        # update cache
        self._run_xml_getters.pop(index)
        self._storage.cacher.delete_from_any_cache(self._storage_cache_key.make_son(str(index)))


class Paragraph(CacheDecoratableXmlNode):
    __slots__ = ('_paragraph_xml_getter', '_text_frame')

    def __init__(self, storage: PresentationStorage, cache_key: CacheKey,
                 paragraph_xml_getter: Lazy, text_frame):
        super().__init__(storage, cache_key)
        self._paragraph_xml_getter = paragraph_xml_getter
        self._text_frame: TextFrame = text_frame

    @property
    def xml(self) -> ElementTree:
        return self._paragraph_xml_getter()

    def save_xml(self) -> None:
        self._text_frame.save_xml()

    @property
    def text_frame(self):
        return self._text_frame

    @property
    def runs(self) -> RunCollection:
        return RunCollection(self._storage, self._storage_cache_key.make_son('runs'), self._run_xmls, self)

    @property
    def text(self) -> str:
        return ' '.join(r.text for r in self.runs)

    @cache_persist_property
    def align(self) -> Optional[HorizontalAlign]:
        if self._p_pr is not None:
            align_str = self._p_pr.get('algn')
            if align_str == 'l':
                return HorizontalAlign.LEFT
            elif align_str == 'ctr':
                return HorizontalAlign.CENTER
            elif align_str == 'r':
                return HorizontalAlign.RIGHT
        if self.do_use_defaults_when_null:
            return HorizontalAlign.LEFT
        return None

    @align.cache_serializer
    def align(self, v: HorizontalAlign) -> int:
        return v.value

    @align.cache_unserializer
    def align(self, v: int) -> HorizontalAlign:
        return HorizontalAlign(v)

    @cache_persist_property
    def line_height(self) -> Union[float, Emu, None]:
        ln_spc_spc_pct = first_or_none(self.xml.xpath('a:lnSpc[1]/a:spcPct[1]', namespaces=pptx_xml_ns))
        if ln_spc_spc_pct is not None:
            val_str = ln_spc_spc_pct.get('val')
            if val_str is not None:
                return int(val_str)
        ln_spc_spc_pts = first_or_none(self.xml.xpath('a:lnSpc[1]/a:spcPts[1]', namespaces=pptx_xml_ns))
        if ln_spc_spc_pts is not None:
            val_str = ln_spc_spc_pct.get('val')
            if val_str is not None:
                return float(val_str)
        if self.do_use_defaults_when_null:
            return 1.00001
        return None

    @line_height.cache_serializer
    def line_height(self, v: Union[float, Emu]) -> Union[float, int]:
        if isinstance(v, Emu):
            return int(v)
        elif isinstance(v, float):
            return v
        elif isinstance(v, int):
            return float(v)

    @line_height.cache_unserializer
    def line_height(self, v: Union[float, int]) -> Union[float, Emu]:
        if isinstance(v, float):
            return v
        elif isinstance(v, int):
            return Emu(v)

    @cache_persist_property
    def level(self) -> Optional[int]:
        if self._p_pr is not None:
            level_str = self._p_pr.get('lvl')
            if level_str is not None:
                return int(level_str)
        if self.do_use_defaults_when_null:
            return 0
        return None

    @cache_persist_property
    def level_width(self) -> Optional[Emu]:
        if self._p_pr is not None:
            level_width_str = self._p_pr.get('defTabSz')
            if level_width_str is not None:
                return Emu(level_width_str)
        if self.do_use_defaults_when_null:
            return Emu.from_px(32)
        return None

    @level_width.cache_serializer
    def level_width(self, v: Emu) -> int:
        return int(v)

    @level_width.cache_unserializer
    def level_width(self, v: int) -> Emu:
        return Emu(v)

    @cache_persist_property
    def margin_top(self) -> Optional[Emu]:
        spc_bef_spc_pts = first_or_none(self.xml.xpath('a:spcBef[1]/a:spcPts[1]', namespaces=pptx_xml_ns))
        if spc_bef_spc_pts is not None:
            val = spc_bef_spc_pts.get('val')
            if val is not None:
                return Emu.from_centripoints(val)
        if self.do_use_defaults_when_null:
            return Emu(0)
        return None

    @margin_top.cache_serializer
    def margin_top(self, v: Emu) -> int:
        return int(v)

    @margin_top.cache_unserializer
    def margin_top(self, v: int) -> Emu:
        return Emu(v)

    @cache_persist_property
    def margin_bottom(self) -> Optional[Emu]:
        spc_aft_spc_pts = first_or_none(self.xml.xpath('a:spcAft[1]/a:spcPts[1]', namespaces=pptx_xml_ns))
        if spc_aft_spc_pts is not None:
            val = spc_aft_spc_pts.get('val')
            if val is not None:
                return Emu.from_centripoints(val)
        if self.do_use_defaults_when_null:
            return Emu(0)
        return None

    @margin_bottom.cache_serializer
    def margin_bottom(self, v: Emu) -> int:
        return int(v)

    @margin_bottom.cache_unserializer
    def margin_bottom(self, v: int) -> Emu:
        return Emu(v)

    @cache_local_property
    def _p_pr(self) -> Optional[ElementTree]:
        return first_or_none(self.xml.xpath('a:pPr[1]', namespaces=pptx_xml_ns))

    @cache_local_property
    def _def_r_pr(self) -> Optional[ElementTree]:
        if self._p_pr is None:
            return None
        return first_or_none(self._p_pr.xpath('a:defRPr[1]', namespaces=pptx_xml_ns))

    @help_lazy_list_property
    def _run_xmls(self) -> LazyList:
        def find():
            return self.xml.xpath('a:r', namespaces=pptx_xml_ns)

        return LazyList(find)


class ParagraphCollection(CacheDecoratable):
    __slots__ = ('_paragraph_xml_getters', '_text_frame')

    def __init__(self, storage: PresentationStorage, cache_key: CacheKey,
                 paragraph_xml_getters: LazyList, text_frame):
        self._storage = storage
        self._storage_cache_key = cache_key
        self._paragraph_xml_getters = paragraph_xml_getters
        self._text_frame: TextFrame = text_frame

    def __getitem__(self, index: int) -> Paragraph:
        return Paragraph(self._storage, self._storage_cache_key.make_son(str(index)),
                         self._paragraph_xml_getters[index],
                         self._text_frame)

    def __iter__(self):
        for i, xml in self._paragraph_xml_getters.iter_enumerate():
            yield Paragraph(self._storage, self._storage_cache_key.make_son(str(i)), xml, self._text_frame)

    def __len__(self):
        return len(self._paragraph_xml_getters)

    @dangerous_method
    def add_paragraph(self, new_xml: ElementTree = None, do_auto_new_xml_with_run: bool = True) -> int:
        # create
        if new_xml is None:
            new_xml = etree.Element('{%s}p' % pptx_xml_ns['a'])
            if do_auto_new_xml_with_run:
                new_xml_r = etree.Element('{%s}r' % pptx_xml_ns['a'])
                new_xml.append(new_xml_r)
                new_xml_r_pr = etree.Element('{%s}rPr' % pptx_xml_ns['a'])
                new_xml_r.append(new_xml_r_pr)
                new_xml_t = etree.Element('{%s}t' % pptx_xml_ns['a'])
                new_xml_r.append(new_xml_t)

        self._text_frame.xml.append(new_xml)
        self._text_frame.save_xml()

        # update cache
        # noinspection PyProtectedMember
        self._text_frame._paragraph_xmls.append(new_xml)

        # make run object
        new_paragraph_index = self._paragraph_xml_getters.len_with_holes - 1
        return new_paragraph_index

    @dangerous_method
    def delete_paragraph(self, index: int, do_affect_xml: bool = True, i_wont_save_cache: bool = False) -> None:
        if not do_affect_xml:
            assert i_wont_save_cache

        # delete
        if do_affect_xml:
            paragraph_xml = self._paragraph_xml_getters[index]()
            paragraph_xml.getparent().remove(paragraph_xml)
            self._text_frame.save_xml()

        # update cache
        self._paragraph_xml_getters.pop(index)
        self._storage.cacher.delete_from_any_cache(self._storage_cache_key.make_son(str(index)))

    @dangerous_method
    def clear(self) -> None:
        # delete
        for paragraph_xml_getter in self._paragraph_xml_getters:
            self._text_frame.xml.remove(paragraph_xml_getter())
        self._text_frame.save_xml()

        # update cache
        self._paragraph_xml_getters.clear()


class TextFrame(CacheDecoratableXmlNode):
    __slots__ = ('_tx_body_xml_getter', '_shape')

    def __init__(self, storage: PresentationStorage, cache_key: CacheKey, tx_body_xml_getter: Lazy,
                 shape):
        from gpptx.types.shape import Shape

        super().__init__(storage, cache_key)
        self._tx_body_xml_getter = tx_body_xml_getter
        self._shape: Shape = shape

    @property
    def xml(self) -> ElementTree:
        return self._tx_body_xml_getter()

    def save_xml(self) -> None:
        self._shape.save_xml()

    @property
    def shape(self):
        return self._shape

    @property
    def paragraphs(self) -> ParagraphCollection:
        return ParagraphCollection(self._storage, self._storage_cache_key.make_son('paragraphs'),
                                   self._paragraph_xmls, self)

    @property
    def text(self) -> str:
        return '\n'.join(p.text for p in self.paragraphs)

    @cache_persist_property
    def margin_left(self) -> Optional[Emu]:
        if self._body_pr is not None:
            l_ins_str = self._body_pr.get('lIns')
            if l_ins_str is not None:
                return Emu(l_ins_str)
        if self.do_use_defaults_when_null:
            return Emu(0)
        return None

    @margin_left.cache_serializer
    def margin_left(self, v: Emu) -> int:
        return int(v)

    @margin_left.cache_unserializer
    def margin_left(self, v: int) -> Emu:
        return Emu(v)

    @cache_persist_property
    def margin_top(self) -> Optional[Emu]:
        if self._body_pr is not None:
            t_ins_str = self._body_pr.get('tIns')
            if t_ins_str is not None:
                return Emu(t_ins_str)
        if self.do_use_defaults_when_null:
            return Emu(0)
        return None

    @margin_top.cache_serializer
    def margin_top(self, v: Emu) -> int:
        return int(v)

    @margin_top.cache_unserializer
    def margin_top(self, v: int) -> Emu:
        return Emu(v)

    @cache_persist_property
    def margin_right(self) -> Optional[Emu]:
        if self._body_pr is not None:
            r_ins_str = self._body_pr.get('rIns')
            if r_ins_str is not None:
                return Emu(r_ins_str)
        if self.do_use_defaults_when_null:
            return Emu(0)
        return None

    @margin_right.cache_serializer
    def margin_right(self, v: Emu) -> int:
        return int(v)

    @margin_right.cache_unserializer
    def margin_right(self, v: int) -> Emu:
        return Emu(v)

    @cache_persist_property
    def margin_bottom(self) -> Optional[Emu]:
        if self._body_pr is not None:
            b_ins_str = self._body_pr.get('bIns')
            if b_ins_str is not None:
                return Emu(b_ins_str)
        if self.do_use_defaults_when_null:
            return Emu(0)
        return None

    @margin_bottom.cache_serializer
    def margin_bottom(self, v: Emu) -> int:
        return int(v)

    @margin_bottom.cache_unserializer
    def margin_bottom(self, v: int) -> Emu:
        return Emu(v)

    @cache_persist_property
    def vertical_align(self) -> Optional[VerticalAlign]:
        if self._body_pr is not None:
            anchor_str = self._body_pr.get('anchor')
            if anchor_str is not None:
                if anchor_str == 't':
                    return VerticalAlign.TOP
                elif anchor_str == 'ctr':
                    return VerticalAlign.CENTER
                elif anchor_str == 'b':
                    return VerticalAlign.BOTTOM
        if self.do_use_defaults_when_null:
            return VerticalAlign.TOP
        return None

    @vertical_align.cache_serializer
    def vertical_align(self, v: VerticalAlign) -> int:
        return v.value

    @vertical_align.cache_unserializer
    def vertical_align(self, v: int) -> VerticalAlign:
        return VerticalAlign(v)

    @cache_persist_property
    def do_word_wrap(self) -> Optional[bool]:
        if self._body_pr is not None:
            wrap_str = self._body_pr.get('wrap')
            if wrap_str is not None:
                if wrap_str == 'square':
                    return True
                elif wrap_str == 'node':
                    return False
        if self.do_use_defaults_when_null:
            return True
        return None

    @cache_local_property
    def _def_r_pr(self) -> Optional[ElementTree]:
        return first_or_none(self.xml.xpath('a:defRPr[1]', namespaces=pptx_xml_ns))

    @cache_local_property
    def _list_def_r_pr(self) -> Optional[ElementTree]:
        return first_or_none(self.xml.xpath('a:lstStyle[1]/a:lvl1pPr[1]/a:defRPr[1]', namespaces=pptx_xml_ns))

    @help_lazy_list_property
    def _paragraph_xmls(self) -> LazyList:
        def find() -> List[ElementTree]:
            return self.xml.xpath('a:p', namespaces=pptx_xml_ns)

        return LazyList(find)

    @cache_local_property
    def _body_pr(self) -> Optional[ElementTree]:
        return first_or_none(self.xml.xpath('a:bodyPr[1]', namespaces=pptx_xml_ns))
