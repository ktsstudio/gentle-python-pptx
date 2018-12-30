import math
from typing import Union


class Emu(int):
    _EMUS_PER_CENTIPOINT = 127
    _EMUS_PER_INCH = 914400
    _EMUS_PER_CM = 360000
    _EMUS_PER_MM = 36000
    _EMUS_PER_PT = 12700
    _PT_PER_PX = 12 / 16

    def __new__(cls, emu: Union[int, float, str]):
        if isinstance(emu, str):
            emu = int(emu)
        # noinspection PyArgumentList
        # because of Pycharm internal error
        return int.__new__(cls, emu)

    @property
    def centipoints(self) -> int:
        return self // self._EMUS_PER_CENTIPOINT

    @property
    def inches(self) -> float:
        return self / self._EMUS_PER_INCH

    @property
    def cm(self) -> float:
        return self / self._EMUS_PER_CM

    @property
    def emu(self) -> int:
        return self

    @property
    def mm(self) -> float:
        return self / self._EMUS_PER_MM

    @property
    def pt(self) -> float:
        return self / self._EMUS_PER_PT

    @property
    def px(self) -> float:
        return self.pt / self._PT_PER_PX

    @classmethod
    def from_centripoints(cls, centripoints: int):
        return cls(centripoints * cls._EMUS_PER_CENTIPOINT)

    @classmethod
    def from_inches(cls, inches: float):
        return cls(inches * cls._EMUS_PER_INCH)

    @classmethod
    def from_cm(cls, cm: float):
        return cls(cm * cls._EMUS_PER_CM)

    @classmethod
    def from_mm(cls, mm: float):
        return cls(mm * cls._EMUS_PER_MM)

    @classmethod
    def from_pt(cls, pt: float):
        return cls(pt * cls._EMUS_PER_PT)

    @classmethod
    def from_px(cls, px: float):
        return cls(px * cls._PT_PER_PX * cls._EMUS_PER_PT)


class Angle(int):
    _ANGLE_POINTS = 60000

    def __new__(cls, angle_points: Union[int, float, str]):
        if isinstance(angle_points, str):
            angle_points = int(angle_points)
        # noinspection PyArgumentList
        # because of Pycharm internal error
        return int.__new__(cls, angle_points)

    @property
    def degrees(self) -> float:
        return self / self._ANGLE_POINTS

    @property
    def radians(self) -> float:
        return math.radians(self.degrees)

    @classmethod
    def from_degrees(cls, degrees: float):
        return cls(degrees * cls._ANGLE_POINTS)

    @classmethod
    def from_radians(cls, radians: float):
        return cls.from_degrees(math.degrees(radians))

    def rotate_clock_direction(self):
        if self == 0:
            return self
        else:
            return Angle((360 * self._ANGLE_POINTS) - self)
