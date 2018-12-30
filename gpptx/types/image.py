import os
from abc import ABC
from io import BytesIO
from typing import Optional, List

from PIL import Image as PIL_Image
from lxml.etree import ElementTree

from gpptx.pptx_tools.xml_namespaces import pptx_xml_ns
from gpptx.storage.cache.decorator import cache_local_property, cache_persist_property
from gpptx.types.fill import SolidFill, GradientFill
from gpptx.types.shape import PatternShape
from gpptx.types.units import Emu
from gpptx.types.xml_node import CacheDecoratableXmlNode
from gpptx.util.list import first_or_none


class Image(CacheDecoratableXmlNode, ABC):
    __slots__ = ('_shape',)

    def __init__(self, shape):
        from gpptx.types.shape import Shape

        # noinspection PyProtectedMember
        super().__init__(shape._storage, shape._storage_cache_key)
        self._shape: Shape = shape

    @property
    def xml(self) -> ElementTree:
        return self._shape.xml

    def save_xml(self) -> None:
        self._shape.save_xml()

    @property
    def blob(self) -> bytes:
        raise NotImplementedError

    @property
    def ext(self) -> str:
        raise NotImplementedError


class RasterImage(Image):
    __slots__ = ()

    @property
    def original_blob(self) -> bytes:
        return self._storage.loader.get_file(self._blob_path)

    @property
    def blob(self) -> bytes:
        return self._transform(self.original_blob)

    @property
    def ext(self) -> str:
        parts = os.path.splitext(self._blob_path)
        ext_with_dot = parts[1]
        return ext_with_dot[1:]

    @property
    def crop_left(self) -> Optional[Emu]:
        if self._src_rect is not None:
            return Emu(self._src_rect.get('l'))
        if self._do_use_defaults_when_null:
            return Emu(0)
        return None

    @property
    def crop_top(self) -> Optional[Emu]:
        if self._src_rect is not None:
            return Emu(self._src_rect.get('t'))
        if self._do_use_defaults_when_null:
            return Emu(0)
        return None

    @property
    def crop_right(self) -> Optional[Emu]:
        if self._src_rect is not None:
            return Emu(self._src_rect.get('r'))
        if self._do_use_defaults_when_null:
            return Emu(0)
        return None

    @property
    def crop_bottom(self) -> Optional[Emu]:
        if self._src_rect is not None:
            return Emu(self._src_rect.get('b'))
        if self._do_use_defaults_when_null:
            return Emu(0)
        return None

    def replace_image(self, new_image_bytes: bytes) -> None:
        self._storage.loader.save_file(self._blob_path, new_image_bytes)

    def _transform(self, blob: bytes) -> bytes:
        need_crop = self.crop_left != 0 or self.crop_top != 0 or self.crop_right != 0 or self.crop_bottom != 0
        if need_crop:
            blob = self._crop(blob)
        return blob

    def _crop(self, blob: bytes) -> bytes:
        with BytesIO(blob) as in_buf:
            pil_image = PIL_Image.open(in_buf)

            box = (int(self.crop_left * pil_image.width),
                   int(self.crop_top * pil_image.height),
                   int((1 - self.crop_right) * pil_image.width),
                   int((1 - self.crop_bottom) * pil_image.height))
            cropped_image = pil_image.crop(box=box)

            with BytesIO() as out_buf:
                cropped_image.save(out_buf, format=pil_image.format, optimize=True)
                blob = out_buf.getvalue()

        return blob

    @cache_local_property
    def _blip_fill(self) -> ElementTree:
        return self.xml.xpath('p:blipFill[1]', namespaces=pptx_xml_ns)[0]

    @cache_local_property
    def _src_rect(self) -> Optional[ElementTree]:
        return first_or_none(self._blip_fill.xpath('a:srcRect[1]', namespaces=pptx_xml_ns))

    @cache_local_property
    def _rel_id(self) -> str:
        return self._blip_fill.xpath('a:blip[1]/@r:embed', namespaces=pptx_xml_ns)[0]

    @cache_persist_property
    def _blob_path(self) -> str:
        return self._shape.slide.rels.xpath(f"(Relationship[@Id='{self._rel_id}'])[1]/@Target")[0]


class VectorImage(Image):
    __slots__ = ()

    @cache_local_property
    def blob(self) -> bytes:
        return self._make_svg(self._path).encode('utf-8')

    @property
    def ext(self) -> str:
        return 'svg'

    @cache_local_property
    def _path(self) -> ElementTree:
        return first_or_none(self.xml.xpath('p:spPr[1]/a:custGeom[1]/a:pathLst[1]/a:path[1]'))

    @staticmethod
    def _make_svg(path: ElementTree) -> str:
        accum_x = 0
        accum_y = 0

        svg_path = ''
        for it in path:
            if it.tag == '{http://schemas.openxmlformats.org/drawingml/2006/main}moveTo':
                command = 'M'
            elif it.tag == '{http://schemas.openxmlformats.org/drawingml/2006/main}lnTo':
                command = 'L'
            elif it.tag == '{http://schemas.openxmlformats.org/drawingml/2006/main}close':
                command = 'Z'
            elif it.tag == '{http://schemas.openxmlformats.org/drawingml/2006/main}cubicBezTo':
                command = 'C'
            elif it.tag == '{http://schemas.openxmlformats.org/drawingml/2006/main}quadBezTo':
                command = 'Q'
            elif it.tag == '{http://schemas.openxmlformats.org/drawingml/2006/main}arcTo':
                continue  # TODO
            else:
                continue
            points = list()
            max_x = None
            max_y = None
            for inner_it in it:
                x = Emu(inner_it.attrib["x"]).px
                y = Emu(inner_it.attrib["y"]).px
                if max_x is None or x > max_x:
                    max_x = x
                if max_y is None or y > max_y:
                    max_y = y
                points.append(f'{x} {y}')
            if max_x is not None:
                accum_x += max_x
            if max_y is not None:
                accum_y += max_y
            svg_path += f'{command} {", ".join(points)} '

        if 'w' in path.attrib:
            width = Emu(path.attrib['w']).px
        else:
            width = accum_x
        if 'h' in path.attrib:
            height = Emu(path.attrib['h']).px
        else:
            height = accum_y

        return f"""
            <svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
                <path d="{svg_path}"/>
            </svg>
        """


class SolidPatternImage(Image):
    __slots__ = ()

    def __init__(self, pattern_shape):
        super().__init__(pattern_shape)

    @cache_local_property
    def blob(self) -> bytes:
        return self._make_svg().encode('utf-8')

    @property
    def ext(self) -> str:
        return 'svg'

    def _make_svg(self) -> str:
        shape: PatternShape = self._shape
        fill: SolidFill = shape.fill
        return self._make_svg_solid(width=shape.width.px, height=shape.height.px,
                                    color=fill.color.rgb_str, opacity=fill.color.alpha)

    @staticmethod
    def _make_svg_solid(width: float, height: float, color: str, opacity: float):
        return f"""
            <svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
                <rect x="0" y="0" width="{width}" height="{height}" fill="#{color}" fill-opacity="{opacity}" />
            </svg>
        """


class GradientPatternImage(Image):
    __slots__ = ()

    def __init__(self, pattern_shape):
        super().__init__(pattern_shape)

    @cache_local_property
    def blob(self) -> bytes:
        return self._make_svg().encode('utf-8')

    @property
    def ext(self) -> str:
        return 'svg'

    def _make_svg(self) -> str:
        shape: PatternShape = self._shape
        fill: GradientFill = shape.fill

        if fill.is_linear_gradient:
            return self._make_svg_linear_gradient(width=shape.width.px, height=shape.height.px,
                                                  stops=fill.gradient_stops, direction=fill.gradient_direction)
        else:
            raise NotImplementedError

    @staticmethod
    def _make_svg_linear_gradient(width: float, height: float,
                                  stops: List[GradientFill.GradientStop], direction: GradientFill.GradientDirection):
        def make_stop(percent: int, color: str, alpha: float) -> str:
            return f'<stop offset="{percent}%" stop-color="#{color}" stop-alpha="{alpha}" />'

        return f"""
            <svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
                <defs>
                    <linearGradient id="gradient" 
                                    x1="{direction.x1}%" y1="{direction.y1}%"
                                    x2="{direction.x2}%" y2="{direction.y2}%">
                        {''.join(make_stop(s.percent, s.color_rgb, s.alpha) for s in stops)}
                    </linearGradient>
                </defs>

                <rect x="0" y="0" width="{width}" height="{height}" fill="url(#gradient)" />
            </svg>
        """


class PlaceholderImage(Image):
    PLACEHOLDER_IMAGE_PATH = os.path.join(os.path.dirname(__file__), 'resources', 'picture_placeholder.png')

    __slots__ = ()

    @property
    def blob(self) -> bytes:
        with open(self.PLACEHOLDER_IMAGE_PATH, mode='rb') as f:
            return f.read()

    @property
    def ext(self) -> str:
        return 'png'
