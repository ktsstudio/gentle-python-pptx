from abc import ABC
from colorsys import hls_to_rgb, rgb_to_hls
from enum import Enum
from typing import Tuple

from lxml.etree import ElementTree

from gpptx.pptx_tools.colors import PRESET_COLORS
from gpptx.pptx_tools.xml_namespaces import pptx_xml_ns
from gpptx.types.theme import Theme
from gpptx.types.xml_node import XmlNode
from gpptx.util.list import first_or_none
from gpptx.util.math import clamp


class ColorType(Enum):
    SRGB = 1
    HSL = 2
    PRESET = 3
    SCHEME = 4
    UNKNOWN = 5


class Color(XmlNode, ABC):
    @property
    def rgb_str(self) -> str:
        raise NotImplementedError

    @property
    def alpha(self) -> float:
        raise NotImplementedError


class SrgbColor(Color):
    def __init__(self, srgb_clr_xml: ElementTree):
        super().__init__()
        self._srgb_clr_xml = srgb_clr_xml

    @property
    def xml(self) -> ElementTree:
        return self._srgb_clr_xml

    def save_xml(self) -> None:
        raise NotImplementedError

    @property
    def rgb_str(self) -> str:
        r, g, b = _parse_rgb_str(self.xml.attrib['val'])
        r, g, b = _parse_color_change(self.xml, r, g, b)
        return _stringify_rgb(r, g, b)

    @property
    def alpha(self) -> float:
        return _parse_alpha(self.xml)


class HslColor(Color):
    def __init__(self, hsl_clr_xml: ElementTree):
        super().__init__()
        self._hsl_clr_xml = hsl_clr_xml

    @property
    def xml(self) -> ElementTree:
        return self._hsl_clr_xml

    def save_xml(self) -> None:
        raise NotImplementedError

    @property
    def rgb_str(self) -> str:
        h = int(self.xml.attrib['hue'])
        l = int(self.xml.attrib['lum'][:-1])
        s = int(self.xml.attrib['sat'][:-1])
        r, g, b = hls_to_rgb(h, l, s)
        r, g, b = _integerize_color_components(r, g, b)
        r, g, b = _parse_color_change(self.xml, r, g, b)
        return _stringify_rgb(r, g, b)

    @property
    def alpha(self) -> float:
        return _parse_alpha(self.xml)


class PresetColor(Color):
    def __init__(self, prst_clr_xml: ElementTree):
        super().__init__()
        self._prst_clr_xml = prst_clr_xml

    @property
    def xml(self) -> ElementTree:
        return self._prst_clr_xml

    def save_xml(self) -> None:
        raise NotImplementedError

    @property
    def rgb_str(self) -> str:
        color_name = self.xml.attrib['val']
        r, g, b = _parse_rgb_str(PRESET_COLORS[color_name])
        r, g, b = _parse_color_change(self.xml, r, g, b)
        return _stringify_rgb(r, g, b)

    @property
    def alpha(self) -> float:
        return _parse_alpha(self.xml)


class SchemeColor(Color):
    def __init__(self, scheme_clr_xml: ElementTree, theme: Theme):
        super().__init__()
        self._scheme_clr_xml = scheme_clr_xml
        self._theme = theme

    @property
    def xml(self) -> ElementTree:
        return self._scheme_clr_xml

    def save_xml(self) -> None:
        raise NotImplementedError

    @property
    def rgb_str(self) -> str:
        theme_color_name = self.xml.attrib['val']
        color_rgb = self._theme.color_rgbs[theme_color_name]
        r, g, b = _parse_rgb_str(color_rgb)
        r, g, b = _parse_color_change(self.xml, r, g, b)
        return _stringify_rgb(r, g, b)

    @property
    def alpha(self) -> float:
        return _parse_alpha(self.xml)


class UnknownColor(Color):
    def __init__(self, clr_xml: ElementTree):
        super().__init__()
        self._clr_xml = clr_xml

    @property
    def xml(self) -> ElementTree:
        return self._clr_xml

    def save_xml(self) -> None:
        raise NotImplementedError

    @property
    def rgb_str(self) -> str:
        return '000000'

    @property
    def alpha(self) -> float:
        return _parse_alpha(self.xml)


class CustomSetColor(Color):
    __slots__ = ('_rgb', '_alpha')

    def __init__(self, rgb: str = '000000', alpha: float = 1):
        super().__init__()
        self._rgb = rgb
        self._alpha = alpha

    @property
    def xml(self) -> ElementTree:
        return None

    def save_xml(self) -> None:
        raise NotImplementedError

    @property
    def rgb_str(self) -> str:
        return self._rgb

    @property
    def alpha(self) -> float:
        return self._alpha


def _parse_color_change(clr_xml: ElementTree, r: int, g: int, b: int) -> Tuple[int, int, int]:
    r, g, b = _floatize_color_components(r, g, b)
    h, l, s = rgb_to_hls(r, g, b)

    for it in clr_xml:
        if 'hueMod' in it.tag:
            val = int(it.attrib['val']) / 100000
            h *= val
            while h < 0:
                h = 1 - h
            while h > 1:
                h = h - 1
        elif 'hueOff' in it.tag:
            val = int(it.attrib['val']) / 100000
            h += val
            while h < 0:
                h = 1 - h
            while h > 1:
                h = h - 1
        elif 'lumMod' in it.tag:
            val = int(it.attrib['val']) / 100000
            l *= val
        elif 'lumOff' in it.tag:
            val = int(it.attrib['val']) / 100000
            l += val
        elif 'satMod' in it.tag:
            val = int(it.attrib['val']) / 100000
            s *= val
        elif 'satOff' in it.tag:
            val = int(it.attrib['val']) / 100000
            s += val

    r, g, b = hls_to_rgb(h, l, s)
    r, g, b = _integerize_color_components(r, g, b)
    return r, g, b


def _integerize_color_components(*args):
    for a in args:
        yield int(clamp(a, 0, 1) * 255)


def _floatize_color_components(*args):
    for a in args:
        yield clamp(a, 0, 255) / 255


def _parse_rgb_str(s: str) -> Tuple[int, int, int]:
    r = int(s[:2], 16)
    g = int(s[2:4], 16)
    b = int(s[4:], 16)
    return r, g, b


def _stringify_rgb(r: int, g: int, b: int) -> str:
    return f'{r:02X}{g:02X}{b:02X}'


def _parse_alpha(clr_xml: ElementTree) -> float:
    alpha_el = first_or_none(clr_xml.xpath('a:alpha[1]', namespaces=pptx_xml_ns))
    if alpha_el is None:
        return 1
    alpha_str = alpha_el.attrib['val']
    return int(alpha_str) / 100000
