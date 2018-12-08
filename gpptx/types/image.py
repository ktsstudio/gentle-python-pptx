from abc import ABC
from io import BytesIO

from lxml.etree import ElementTree

from gpptx.types.xml_node import XmlNode


class Image(XmlNode, ABC):
    @property
    def blob(self) -> bytes:
        raise NotImplementedError

    @property
    def blob_ext(self) -> str:
        raise NotImplementedError


class RasterImage(Image):
    def __init__(self):
        super().__init__()
        raise NotImplementedError  # TODO

    @property
    def xml(self) -> ElementTree:
        raise NotImplementedError  # TODO

    def save_xml(self) -> None:
        raise NotImplementedError  # TODO

    @property
    def blob(self) -> bytes:
        raise NotImplementedError  # TODO

    @property
    def blob_ext(self) -> str:
        raise NotImplementedError  # TODO

    def replace_image(self, new_image_bytes: BytesIO) -> None:
        raise NotImplementedError  # TODO


class VectorImage(Image):
    def __init__(self):
        super().__init__()
        raise NotImplementedError  # TODO

    @property
    def xml(self) -> ElementTree:
        raise NotImplementedError  # TODO

    def save_xml(self) -> None:
        raise NotImplementedError  # TODO

    @property
    def blob(self) -> bytes:
        raise NotImplementedError  # TODO

    @property
    def blob_ext(self) -> str:
        raise NotImplementedError
