from xml.etree import ElementTree

from gpptx.types.color import ColorType, Color, SrgbColor, HslColor, PresetColor, SchemeColor, UnknownColor
from gpptx.types.shape import Shape


class ColorResolver:
    __slots__ = ('_shape',)

    def __init__(self, shape: Shape):
        self._shape = shape

    def make_color(self, xml: ElementTree) -> Color:
        color_type = self._get_color_type(xml)
        return self._make_color(color_type, xml)

    @staticmethod
    def _get_color_type(xml: ElementTree) -> ColorType:
        if 'srgbClr' in xml.tag:
            return ColorType.SRGB
        if 'hslClr' in xml.tag:
            return ColorType.HSL
        if 'prstClr' in xml.tag:
            return ColorType.PRESET
        if 'schemeClr' in xml.tag:
            return ColorType.SCHEME

        return ColorType.UNKNOWN

    def _make_color(self, color_type: ColorType, xml: ElementTree) -> Color:
        if color_type == ColorType.SRGB:
            return SrgbColor(xml)
        elif color_type == ColorType.HSL:
            return HslColor(xml)
        elif color_type == ColorType.PRESET:
            return PresetColor(xml)
        elif color_type == ColorType.SCHEME:
            return SchemeColor(xml, self._shape.slide.theme)
        elif color_type == ColorType.UNKNOWN:
            return UnknownColor(xml)
