import math
from abc import ABC
from typing import List, Optional, Tuple

from lxml.etree import ElementTree

from gpptx.pptx_tools.xml_namespaces import pptx_xml_ns
from gpptx.storage.cache.decorator import cache_local_property, cache_persist_property
from gpptx.types.color import Color
from gpptx.types.units import Angle
from gpptx.types.xml_node import XmlNode
from gpptx.util.list import first_or_none


class Fill(XmlNode, ABC):
    __slots__ = ('_shape',)

    def __init__(self, shape):
        from gpptx.types.shape import Shape

        super().__init__()
        self._shape: Shape = shape

    @property
    def xml(self) -> ElementTree:
        return self._shape.xml

    def save_xml(self) -> None:
        self._shape.save_xml()


class SolidFill(Fill):
    __slots__ = ()

    @cache_persist_property
    def color_rgb(self) -> str:
        return self._color.rgb

    @cache_persist_property
    def color_alpha(self) -> float:
        return self._color.alpha

    @cache_local_property
    def _color(self) -> Color:
        color_maker = self._shape.color_maker
        color_xml = next(iter(self._solid_fill))
        return color_maker.make_color(color_xml)

    @cache_local_property
    def _solid_fill(self) -> Optional[ElementTree]:
        return first_or_none(self.xml.xpath('p:spPr[1]/a:solidFill[1]', namespaces=pptx_xml_ns))


class GradientFill(Fill):
    __slots__ = ()

    class GradientStop:
        __slots__ = ('percent', 'color_rgb', 'alpha')

        def __init__(self, percent: int, color_rgb: str, alpha: float):
            self.percent = percent
            self.color_rgb = color_rgb
            self.alpha = alpha

    class GradientDirection:
        __slots__ = ('x1', 'y1', 'x2', 'y2')

        def __init__(self, x1: int, y1: int, x2: int, y2: int):
            self.x1 = x1
            self.y1 = y1
            self.x2 = x2
            self.y2 = y2

    @cache_persist_property
    def gradient_stops(self) -> List[GradientStop]:
        if self._gs_lst is None:
            return list()
        result = list()
        color_maker = self._shape.color_maker
        for gs in self._gs_lst:
            percent = int(gs.get('pos'))
            color_xml = next(iter(gs))
            color = color_maker.make_color(color_xml)
            result.append(self.GradientStop(percent, color.rgb_str, color.alpha))
        return result

    @gradient_stops.serializer
    def gradient_stops(self, v: List[GradientStop]) -> List[Tuple[int, str, float]]:
        return [(it.percent, it.color_rgb, it.alpha) for it in v]

    @gradient_stops.unserializer
    def gradient_stops(self, v: List[Tuple[int, str, float]]) -> List[GradientStop]:
        return [self.GradientStop(*it) for it in v]

    @cache_persist_property
    def is_linear_gradient(self) -> bool:
        return self._lin is not None

    @cache_persist_property
    def gradient_angle(self) -> Angle:
        if not self.is_linear_gradient:
            raise ValueError('not a linear gradient')

        clockwise_angle = Angle(self._lin.get('ang'))
        counter_clockwise_angle = clockwise_angle.rotate_clock_direction()
        return counter_clockwise_angle

    @gradient_angle.serializer
    def gradient_angle(self, v: Angle) -> int:
        return int(v)

    @gradient_angle.unserializer
    def gradient_angle(self, v: int) -> Angle:
        return Angle(v)

    @property
    def gradient_direction(self) -> GradientDirection:
        angle = self.gradient_angle.degrees - 90
        angle_rad = math.radians(angle)
        return self.GradientDirection(
            x1=round(50 + math.sin(angle_rad) * 50),
            y1=round(50 + math.cos(angle_rad) * 50),
            x2=round(50 + math.sin(angle_rad + math.pi) * 50),
            y2=round(50 + math.cos(angle_rad + math.pi) * 50),
        )

    @cache_local_property
    def _grad_fill(self) -> Optional[ElementTree]:
        return first_or_none(self.xml.xpath('p:spPr[1]/a:gradFill[1]', namespaces=pptx_xml_ns))

    @cache_local_property
    def _lin(self) -> Optional[ElementTree]:
        if self._grad_fill is None:
            return None
        return first_or_none(self._grad_fill.xpath('a:lin[1]', namespaces=pptx_xml_ns))

    @cache_local_property
    def _gs_lst(self) -> Optional[ElementTree]:
        if self._grad_fill is None:
            return None
        return first_or_none(self._grad_fill.xpath('a:gsLst[1]', namespaces=pptx_xml_ns))
