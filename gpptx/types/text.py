from enum import Enum
from typing import List, Optional, Union

from gpptx.types.color import Color
from gpptx.types.emu import Emu


class Align(Enum):
    LEFT = 1
    CENTER = 2
    RIGHT = 3


class Run:
    def __init__(self):
        raise NotImplementedError

    @property
    def font_size(self, fallback_to_defaults: bool = True) -> Optional[Emu]:
        raise NotImplementedError

    @property
    def color(self, fallback_to_defaults: bool = True) -> Optional[Color]:
        raise NotImplementedError

    @property
    def is_bold(self, fallback_to_defaults: bool = True) -> Optional[bool]:
        raise NotImplementedError

    @property
    def is_italic(self, fallback_to_defaults: bool = True) -> Optional[bool]:
        raise NotImplementedError


class Paragraph:
    def __init__(self):
        raise NotImplementedError

    @property
    def runs(self) -> List[Run]:
        raise NotImplementedError

    def add_run(self) -> Run:
        raise NotImplementedError

    def delete_run(self, index: int) -> None:
        raise NotImplementedError

    @property
    def align(self) -> Align:
        raise NotImplementedError

    @property
    def line_height(self, null_as_one: bool = True) -> Union[float, Emu, None]:
        raise NotImplementedError

    @property
    def level(self, null_as_zero: bool = True) -> Optional[int]:
        raise NotImplementedError

    @property
    def level_width(self, null_as_default: bool = True) -> Optional[Emu]:
        raise NotImplementedError

    @property
    def margin_top(self, null_as_zero: bool = True) -> Optional[Emu]:
        raise NotImplementedError

    @property
    def margin_down(self, null_as_zero: bool = True) -> Optional[Emu]:
        raise NotImplementedError


class TextFrame:
    def __init__(self):
        raise NotImplementedError

    @property
    def paragraphs(self) -> List[Paragraph]:
        raise NotImplementedError

    def add_paragraph(self) -> Paragraph:
        raise NotImplementedError

    def delete_paragraph(self, index: int) -> None:
        raise NotImplementedError

    @property
    def text(self) -> str:
        raise NotImplementedError

    @property
    def margin_left(self, null_as_zero: bool = True) -> Optional[Emu]:
        raise NotImplementedError

    @property
    def margin_top(self, null_as_zero: bool = True) -> Optional[Emu]:
        raise NotImplementedError

    @property
    def margin_right(self, null_as_zero: bool = True) -> Optional[Emu]:
        raise NotImplementedError

    @property
    def margin_down(self, null_as_zero: bool = True) -> Optional[Emu]:
        raise NotImplementedError

