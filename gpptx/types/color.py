from abc import ABCMeta


class Color(metaclass=ABCMeta):
    def __init__(self):
        raise NotImplementedError

    @property
    def rgb_str(self) -> str:
        raise NotImplementedError


class SrgbColor(Color):
    def __init__(self):
        super().__init__()
        raise NotImplementedError

    @property
    def rgb_str(self) -> str:
        raise NotImplementedError


class HslColor(Color):
    def __init__(self):
        super().__init__()
        raise NotImplementedError

    @property
    def rgb_str(self) -> str:
        raise NotImplementedError


class PresetColor(Color):
    def __init__(self):
        super().__init__()
        raise NotImplementedError

    @property
    def rgb_str(self) -> str:
        raise NotImplementedError


class SchemeColor(Color):
    def __init__(self):
        super().__init__()
        raise NotImplementedError

    @property
    def rgb_str(self) -> str:
        raise NotImplementedError
