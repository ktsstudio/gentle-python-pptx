from abc import ABCMeta
from io import BytesIO

from lxml.etree import ElementTree

from gpptx.types.xml_node import XmlNode


class Image(XmlNode, metaclass=ABCMeta):
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

    @property
    def blob(self) -> bytes:
        raise NotImplementedError  # TODO

    @property
    def blob_ext(self) -> str:
        raise NotImplementedError
