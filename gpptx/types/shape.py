from abc import ABCMeta
from typing import List, Optional, Union, Any

from gpptx.types.emu import Emu
from gpptx.types.fill import Fill
from gpptx.types.image import Image
from gpptx.types.text import TextFrame


class Shape(metaclass=ABCMeta):
    def __init__(self):
        raise NotImplementedError

    @property
    def shape_id(self) -> int:
        raise NotImplementedError

    @property
    def name(self) -> str:
        raise NotImplementedError

    @property
    def lxml(self) -> object:  # TODO
        raise NotImplementedError

    @property
    def x(self, null_as_zero: bool = True) -> Optional[Emu]:
        raise NotImplementedError

    @property
    def y(self, null_as_zero: bool = True) -> Optional[Emu]:
        raise NotImplementedError

    @property
    def width(self, null_as_zero: bool = True) -> Optional[Emu]:
        raise NotImplementedError

    @property
    def height(self, null_as_zero: bool = True) -> Optional[Emu]:
        raise NotImplementedError


class ShapesCollection:
    def __init__(self):
        raise NotImplementedError

    def get(self, shape_id: int, default=None) -> Union[Shape, Any]:
        raise NotImplementedError

    def delete(self, index: int) -> None:
        raise NotImplementedError

    @property
    def flattened(self, keep_groups: bool = True, with_layout_shapes: bool = False) -> List[Shape]:
        raise NotImplementedError

    def get_shape_parents_bloodline(self, shape: Shape) -> List[Shape]:
        raise NotImplementedError

    def get_shape_parent(self, shape: Shape) -> Optional[Shape]:
        parents_line = self.get_shape_parents_bloodline(shape)
        if len(parents_line) == 0:
            return None
        return parents_line[-1]

    def __getitem__(self, shape_id: int) -> Shape:
        shape = self.get(shape_id)
        if shape is None:
            raise ValueError(f'No shape with id {shape_id}')
        return shape

    def __iter__(self):
        raise NotImplementedError


class TextShape(Shape):
    def __init__(self):
        super().__init__()
        raise NotImplementedError

    @property
    def text_frame(self) -> TextFrame:
        raise NotImplementedError


class PatternShape(Shape):
    def __init__(self):
        super().__init__()
        raise NotImplementedError

    @property
    def fill(self) -> Fill:
        raise NotImplementedError


class ImageShape(Shape):
    def __init__(self):
        super().__init__()
        raise NotImplementedError

    @property
    def image(self) -> Image:
        raise NotImplementedError


class GroupShape(Shape):
    def __init__(self):
        super().__init__()
        raise NotImplementedError

    @property
    def shapes(self) -> ShapesCollection:
        raise NotImplementedError

    @property
    def offset_x(self) -> Emu:
        raise NotImplementedError

    @property
    def offset_y(self) -> Emu:
        raise NotImplementedError


class UnknownShape(Shape):
    def __init__(self):
        super().__init__()
        raise NotImplementedError
