from typing import BinaryIO

from gpptx.types.presentation import Presentation


def load_from_buf(buf: BinaryIO) -> Presentation:
    raise NotImplementedError
