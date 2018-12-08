from enum import Enum
from typing import List, Optional, Union, Any

from lxml import etree
from lxml.etree import ElementTree

from gpptx.pptx_tools.xml_namespaces import pptx_xml_ns
from gpptx.storage.cache.cacher import CacheKey
from gpptx.storage.cache.decorator import cache_local, cache_persist, CacheDecoratable
from gpptx.storage.storage import PresentationStorage
from gpptx.types.color import Color, NoneColor
from gpptx.types.emu import Emu
from gpptx.types.xml_node import CacheDecoratableXmlNode
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

    def __init__(self, storage: PresentationStorage, cache_key: CacheKey, run_xml: ElementTree, paragraph):
        super().__init__()
        self._storage = storage
        self._storage_cache_key = cache_key
        self._run_xml = run_xml
        self._paragraph: Paragraph = paragraph

    @property
    def xml(self) -> ElementTree:
        return self._run_xml

    def save_xml(self) -> None:
        self._paragraph.save_xml()

    @property
    def paragraph(self):
        return self._paragraph

    @property
    def text_frame(self):
        return self._paragraph.text_frame

    @cache_persist
    @property
    def text(self) -> str:
        if self._t is not None:
            return ''.join(self._t.itertext())
        return ''

    @text.setter
    def text(self, v: str) -> None:
        if self._t is None:
            xml_str = '<a:t></a:t>'
            new_xml = etree.fromstring(xml_str)
            self.xml.append(new_xml)
            raise NotImplementedError  # TODO clear cache
        self._t.text = v
        self._paragraph.save_xml()

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
    @property
    def _t(self) -> Optional[ElementTree]:
        return first_or_none(self.xml.xpath('a:t[1]', namespaces=pptx_xml_ns))

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


class RunCollection(CacheDecoratable):
    __slots__ = ('_run_xmls', '_paragraph')

    def __init__(self, storage: PresentationStorage, cache_key: CacheKey,
                 run_xmls: List[ElementTree], paragraph):
        self._storage = storage
        self._storage_cache_key = cache_key
        self._run_xmls = run_xmls
        self._paragraph: Paragraph = paragraph

    def __getitem__(self, index: int) -> Run:
        return Run(self._storage, self._storage_cache_key.make_son(str(index)), self._run_xmls[index], self._paragraph)

    def __iter__(self):
        for i, xml in enumerate(self._run_xmls):
            yield Run(self._storage, self._storage_cache_key.make_son(str(i)), xml, self._paragraph)

    def __len__(self):
        return len(self._run_xmls)

    def add_run(self, new_xml: ElementTree = None) -> Run:
        # create
        if new_xml is None:
            xml_str = """
                <a:r>
                    <a:rPr></a:rPr>
                    <a:t></a:t>
                </a:r>
            """
            new_xml = etree.fromstring(xml_str)

        self._paragraph.xml.append(new_xml)
        self._paragraph.save_xml()

        # update cache
        self._run_xmls.append(new_xml)  # because it is a pointer

        # make run object
        new_run_index = len(self._run_xmls) - 1
        return Run(self._storage, self._storage_cache_key.make_son(str(new_run_index)), new_xml, self._paragraph)

    def delete_run(self, index: int) -> None:
        # delete
        self._paragraph.xml.remove(self._run_xmls[index])
        self._paragraph.save_xml()

        # update cache
        for i in range(index, len(self._run_xmls)):
            run_cache = self._storage_cache_key.make_son(str(i))
            self._storage.cacher.delete_from_any_cache(run_cache)

        self._run_xmls.pop(index)


class Paragraph(CacheDecoratableXmlNode):
    def __init__(self, storage: PresentationStorage, cache_key: CacheKey, paragraph_xml: ElementTree, text_frame):
        super().__init__()
        self._storage = storage
        self._storage_cache_key = cache_key
        self._paragraph_xml = paragraph_xml
        self._text_frame: TextFrame = text_frame

    @property
    def xml(self) -> ElementTree:
        return self._paragraph_xml

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

    @cache_persist
    @property
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

    @cache_persist
    @property
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
        spc_bef_spc_pts = first_or_none(self.xml.xpath('a:spcBef[1]/a:spcPts[1]', namespaces=pptx_xml_ns))
        if spc_bef_spc_pts is not None:
            val = spc_bef_spc_pts.get('val')
            if val is not None:
                return Emu.from_centripoints(val)
        if self.do_use_defaults_when_null:
            return Emu(0)
        return None

    @cache_persist
    @property
    def margin_bottom(self) -> Optional[Emu]:
        spc_aft_spc_pts = first_or_none(self.xml.xpath('a:spcAft[1]/a:spcPts[1]', namespaces=pptx_xml_ns))
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


class ParagraphCollection(CacheDecoratable):
    __slots__ = ('_paragraph_xmls', '_text_frame')

    def __init__(self, storage: PresentationStorage, cache_key: CacheKey,
                 paragraph_xmls: List[ElementTree], text_frame):
        self._storage = storage
        self._storage_cache_key = cache_key
        self._paragraph_xmls = paragraph_xmls
        self._text_frame: TextFrame = text_frame

    def __getitem__(self, index: int) -> Paragraph:
        return Paragraph(self._storage, self._storage_cache_key.make_son(str(index)), self._paragraph_xmls[index],
                         self._text_frame)

    def __iter__(self):
        for i, xml in enumerate(self._paragraph_xmls):
            yield Paragraph(self._storage, self._storage_cache_key.make_son(str(i)), xml, self._text_frame)

    def __len__(self):
        return len(self._paragraph_xmls)

    def add_paragraph(self, new_xml: ElementTree = None) -> Paragraph:
        # create
        if new_xml is None:
            raise NotImplementedError  # TODO

        self._text_frame.xml.append(new_xml)
        self._text_frame.save_xml()

        # update cache
        self._text_frame.xml.append(new_xml)  # because it is a pointer

        # make run object
        new_paragraph_index = len(self._paragraph_xmls) - 1
        return Paragraph(self._storage, self._storage_cache_key.make_son(str(new_paragraph_index)), new_xml,
                         self._text_frame)

    def delete_run(self, index: int) -> None:
        # delete
        self._text_frame.xml.remove(self._paragraph_xmls[index])

        # update cache
        for i in range(index, len(self._paragraph_xmls)):
            run_cache = self._storage_cache_key.make_son(str(i))
            self._storage.cacher.delete_from_any_cache(run_cache)

        self._paragraph_xmls.pop(index)


class TextFrame(CacheDecoratableXmlNode):
    __slots__ = ('_txbody_xml', '_shape')

    def __init__(self, storage: PresentationStorage, cache_key: CacheKey, txbody_xml: ElementTree, shape):
        from gpptx.types.shape import Shape

        super().__init__()
        self._storage = storage
        self._storage_cache_key = cache_key
        self._txbody_xml = txbody_xml
        self._shape: Shape = shape

    @property
    def xml(self) -> ElementTree:
        return self._txbody_xml

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
    def margin_bottom(self) -> Optional[Emu]:
        if self._body_pr is not None:
            b_ins_str = self._body_pr.get('bIns')
            if b_ins_str is not None:
                return Emu(int(b_ins_str))
        if self.do_use_defaults_when_null:
            return Emu(0)
        return None

    @cache_persist
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

    @cache_persist
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

    @cache_local
    @property
    def _def_r_pr(self) -> Optional[ElementTree]:
        return first_or_none(self.xml.xpath('a:defRPr[1]', namespaces=pptx_xml_ns))

    @cache_local
    @property
    def _list_def_r_pr(self) -> Optional[ElementTree]:
        return first_or_none(self.xml.xpath('a:lstStyle[1]/a:lvl1pPr[1]/a:defRPr[1]', namespaces=pptx_xml_ns))

    @cache_local
    @property
    def _paragraph_xmls(self) -> List[ElementTree]:
        return self.xml.xpath('a:p', namespaces=pptx_xml_ns)

    @cache_local
    @property
    def _body_pr(self) -> Optional[ElementTree]:
        return first_or_none(self.xml.xpath('a:bodyPr[1]', namespaces=pptx_xml_ns))
