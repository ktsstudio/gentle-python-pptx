from enum import Enum
from typing import List, Optional, Union, Any

from lxml.etree import ElementTree

from gpptx.pptx_tools.xml_namespaces import pptx_xml_ns
from gpptx.storage.cache.cacher import CacheKey
from gpptx.storage.cache.decorators import cache_local, cache_persist, CacheDecoratable
from gpptx.storage.storage import PresentationStorage
from gpptx.types.color import Color, NoneColor
from gpptx.types.emu import Emu
from gpptx.types.shape import Shape
from gpptx.types.xml_node import XmlNode
from gpptx.util.list import first_or_none


class Align(Enum):
    LEFT = 1
    CENTER = 2
    RIGHT = 3


class Run(CacheDecoratable, XmlNode):
    _DEFAULT_FONT_SIZE = Emu.from_pt(16)

    def __init__(self, storage: PresentationStorage, cache_key: CacheKey, run_xml: ElementTree, paragraph):
        super().__init__()
        self._storage = storage
        self._storage_cache_key = cache_key
        self._run_xml = run_xml
        self._paragraph: Paragraph = paragraph

    @property
    def xml(self) -> ElementTree:
        return self._run_xml

    @property
    def paragraph(self):
        return self._paragraph

    @property
    def text_frame(self):
        return self._paragraph.text_frame

    @cache_persist
    @property
    def text(self) -> str:
        t = first_or_none(self.xml.xpath('a:t[1]', namespaces=pptx_xml_ns))
        if t is not None:
            return ''.join(t.itertext())
        return ''

    @cache_persist
    @property
    def font_name(self) -> Optional[str]:
        latin_xml = self._get_elem('a:latin')
        if latin_xml is not None:
            return latin_xml.get('typeface')
        return None

    @cache_persist
    @property
    def font_size(self) -> Optional[Emu]:
        sz_str = self._get_attrib('sz')
        if sz_str is not None:
            return Emu.from_centripoints(int(sz_str))
        return self._DEFAULT_FONT_SIZE

    @cache_persist
    @property
    def color_rgb(self) -> Optional[str]:
        color = self._get_color()
        if color is not None:
            return color.rgb_str
        if self.do_use_defaults_when_null:
            return '000000'
        return None

    @cache_persist
    @property
    def color_alpha(self) -> Optional[float]:
        color = self._get_color()
        if color is not None:
            return color.alpha
        if self.do_use_defaults_when_null:
            return 1
        return None

    @cache_persist
    @property
    def is_bold(self) -> Optional[bool]:
        b_str = self._get_attrib('b')
        if b_str is not None:
            return bool(b_str)
        return False

    @cache_persist
    @property
    def is_italic(self) -> Optional[bool]:
        i_str = self._get_attrib('i')
        if i_str is not None:
            return bool(i_str)
        return False

    @cache_local
    @property
    def _r_pr(self) -> Optional[ElementTree]:
        return first_or_none(self.xml.xpath('a:rPr[1]', namespaces=pptx_xml_ns))

    @cache_local
    def _get_color(self) -> Optional[Color]:
        fill_xml = self._get_elem('a:solidFill')
        if fill_xml is not None:
            clr_xml = next(iter(fill_xml))
            color_resolver = self.paragraph.text_frame.shape.color_resolver
            return color_resolver.make_color(clr_xml)
        if self.do_use_defaults_when_null:
            return NoneColor()
        return None

    def _get_attrib(self, name: str) -> Any:
        if self.do_use_defaults_when_null:
            sources = (self._r_pr, self.paragraph._def_r_pr, self.text_frame._list_def_r_pr, self.text_frame._def_r_pr)
        else:
            sources = (self._r_pr,)
        for xml in sources:
            if xml is not None:
                value = xml.get(name)
                if value is not None:
                    return value
        return None

    def _get_elem(self, name: str) -> Any:
        if self.do_use_defaults_when_null:
            sources = (self._r_pr, self.paragraph._def_r_pr, self.text_frame._list_def_r_pr, self.text_frame._def_r_pr)
        else:
            sources = (self._r_pr,)
        for xml in sources:
            if xml is not None:
                matched_elems = xml.xpath(f'{name}[1]', namespaces=pptx_xml_ns)
                if len(matched_elems) != 0:
                    return matched_elems[0]
        return None


class Paragraph(CacheDecoratable, XmlNode):
    def __init__(self, storage: PresentationStorage, cache_key: CacheKey, paragraph_xml: ElementTree, text_frame):
        super().__init__()
        self._storage = storage
        self._storage_cache_key = cache_key
        self._paragraph_xml = paragraph_xml
        self._text_frame: TextFrame = text_frame

    @property
    def xml(self) -> ElementTree:
        return self._paragraph_xml

    @property
    def text_frame(self):
        return self._text_frame

    @property
    def runs(self) -> List[Run]:
        return [Run(self._storage, self._storage_cache_key, xml, self) for xml in self._run_xmls]

    def add_run(self) -> Run:
        raise NotImplementedError  # TODO

    def delete_run(self, index: int) -> None:
        raise NotImplementedError  # TODO

    @property
    def text(self) -> str:
        return ' '.join(r.text for r in self.runs)

    @cache_persist
    @property
    def align(self) -> Optional[Align]:
        if self._p_pr is not None:
            align_str = self._p_pr.get('algn')
            if align_str == 'l':
                return Align.LEFT
            elif align_str == 'ctr':
                return Align.CENTER
            elif align_str == 'r':
                return Align.RIGHT
        if self.do_use_defaults_when_null:
            return Align.LEFT
        return None

    @cache_persist
    @property
    def line_height(self) -> Union[float, Emu, None]:
        ln_spc_spc_pct = first_or_none(self.xml.xpath('a:lnSpc/a:spcPct[1]', namespaces=pptx_xml_ns))
        if ln_spc_spc_pct is not None:
            val_str = ln_spc_spc_pct.get('val')
            if val_str is not None:
                return int(val_str)
        ln_spc_spc_pts = first_or_none(self.xml.xpath('a:lnSpc/a:spcPts[1]', namespaces=pptx_xml_ns))
        if ln_spc_spc_pts is not None:
            val_str = ln_spc_spc_pct.get('val')
            if val_str is not None:
                return float(val_str)
        if self.do_use_defaults_when_null:
            return 1
        return None

    @cache_persist
    @property
    def level(self) -> Optional[int]:
        if self._p_pr is not None:
            level_str = self._p_pr.get('lvl')
            if level_str is not None:
                return int(level_str)
        if self.do_use_defaults_when_null:
            return 0
        return None

    @cache_persist
    @property
    def level_width(self) -> Optional[Emu]:
        if self._p_pr is not None:
            level_width_str = self._p_pr.get('defTabSz')
            if level_width_str is not None:
                return Emu(int(level_width_str))
        if self.do_use_defaults_when_null:
            return Emu.from_px(32)
        return None

    @cache_persist
    @property
    def margin_top(self) -> Optional[Emu]:
        spc_bef_spc_pts = first_or_none(self.xml.xpath('a:spcBef/a:spcPts[1]', namespaces=pptx_xml_ns))
        if spc_bef_spc_pts is not None:
            val = spc_bef_spc_pts.get('val')
            if val is not None:
                return Emu.from_centripoints(val)
        if self.do_use_defaults_when_null:
            return Emu(0)
        return None

    @cache_persist
    @property
    def margin_down(self) -> Optional[Emu]:
        spc_aft_spc_pts = first_or_none(self.xml.xpath('a:spcAft/a:spcPts[1]', namespaces=pptx_xml_ns))
        if spc_aft_spc_pts is not None:
            val = spc_aft_spc_pts.get('val')
            if val is not None:
                return Emu.from_centripoints(val)
        if self.do_use_defaults_when_null:
            return Emu(0)
        return None

    @cache_local
    @property
    def _p_pr(self) -> Optional[ElementTree]:
        return first_or_none(self.xml.xpath('a:pPr[1]', namespaces=pptx_xml_ns))

    @cache_local
    @property
    def _def_r_pr(self) -> Optional[ElementTree]:
        return first_or_none(self.xml.xpath('a:defRPr[1]', namespaces=pptx_xml_ns))

    @cache_local
    @property
    def _run_xmls(self) -> List[ElementTree]:
        return self.xml.xpath('a:r', namespaces=pptx_xml_ns)


class TextFrame(CacheDecoratable, XmlNode):
    __slots__ = ('_txbody_xml', '_shape')

    def __init__(self, storage: PresentationStorage, cache_key: CacheKey, txbody_xml: ElementTree, shape: Shape):
        super().__init__()
        self._storage = storage
        self._storage_cache_key = cache_key
        self._txbody_xml = txbody_xml
        self._shape = shape

    @property
    def xml(self) -> ElementTree:
        return self._txbody_xml

    @property
    def shape(self) -> Shape:
        return self._shape

    @property
    def paragraphs(self) -> List[Paragraph]:
        return [Paragraph(self._storage, self._storage_cache_key, xml, self) for xml in self._paragraph_xmls]

    def add_paragraph(self) -> Paragraph:
        raise NotImplementedError  # TODO

    def delete_paragraph(self, index: int) -> None:
        raise NotImplementedError  # TODO

    @property
    def text(self) -> str:
        return '\n'.join(p.text for p in self.paragraphs)

    @cache_persist
    def margin_left(self) -> Optional[Emu]:
        if self._body_pr is not None:
            l_ins_str = self._body_pr.get('lIns')
            if l_ins_str is not None:
                return Emu(int(l_ins_str))
        if self.do_use_defaults_when_null:
            return Emu(0)
        return None

    @cache_persist
    def margin_top(self) -> Optional[Emu]:
        if self._body_pr is not None:
            t_ins_str = self._body_pr.get('tIns')
            if t_ins_str is not None:
                return Emu(int(t_ins_str))
        if self.do_use_defaults_when_null:
            return Emu(0)
        return None

    @cache_persist
    def margin_right(self) -> Optional[Emu]:
        if self._body_pr is not None:
            r_ins_str = self._body_pr.get('rIns')
            if r_ins_str is not None:
                return Emu(int(r_ins_str))
        if self.do_use_defaults_when_null:
            return Emu(0)
        return None

    @cache_persist
    def margin_down(self) -> Optional[Emu]:
        if self._body_pr is not None:
            b_ins_str = self._body_pr.get('bIns')
            if b_ins_str is not None:
                return Emu(int(b_ins_str))
        if self.do_use_defaults_when_null:
            return Emu(0)
        return None

    @cache_local
    @property
    def _def_r_pr(self) -> Optional[ElementTree]:
        return first_or_none(self.xml.xpath('a:defRPr[1]', namespaces=pptx_xml_ns))

    @cache_local
    @property
    def _list_def_r_pr(self) -> Optional[ElementTree]:
        return first_or_none(self.xml.xpath('a:lstStyle/a:lvl1pPr/a:defRPr[1]', namespaces=pptx_xml_ns))

    @cache_local
    @property
    def _paragraph_xmls(self) -> List[ElementTree]:
        return self.xml.xpath('a:p', namespaces=pptx_xml_ns)

    @cache_local
    @property
    def _body_pr(self) -> Optional[ElementTree]:
        return first_or_none(self.xml.xpath('a:bodyPr[1]', namespaces=pptx_xml_ns))
