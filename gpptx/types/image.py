from abc import ABCMeta
from io import BytesIO


class Image(metaclass=ABCMeta):
    def __init__(self):
        raise NotImplementedError

    @property
    def blob(self) -> bytes:
        raise NotImplementedError

    @property
    def blob_ext(self) -> str:
        raise NotImplementedError


class RasterImage(Image):
    def __init__(self):
        super().__init__()
        raise NotImplementedError

    @property
    def blob(self) -> bytes:
        raise NotImplementedError

    @property
    def blob_ext(self) -> str:
        raise NotImplementedError

    def replace_image(self, new_image_bytes: BytesIO) -> None:
        raise NotImplementedError


class VectorImage(Image):
    def __init__(self):
        super().__init__()
        raise NotImplementedError

    @property
    def blob(self) -> bytes:
        raise NotImplementedError

    @property
    def blob_ext(self) -> str:
        raise NotImplementedError


class PlaceholderImage(Image):
    def __init__(self):
        super().__init__()
        raise NotImplementedError

    @property
    def blob(self) -> bytes:
        raise NotImplementedError

    @property
    def blob_ext(self) -> str:
        raise NotImplementedError
