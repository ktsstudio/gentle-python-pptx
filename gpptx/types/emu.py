class Emu(int):
    _EMUS_PER_INCH = 914400
    _EMUS_PER_CENTIPOINT = 127
    _EMUS_PER_CM = 360000
    _EMUS_PER_MM = 36000
    _EMUS_PER_PT = 12700
    _PT_PER_PX = 12 / 16

    def __new__(cls, emu):
        # noinspection PyArgumentList
        # because of Pycharm internal error
        return int.__new__(cls, emu)

    @property
    def inches(self) -> float:
        return self / self._EMUS_PER_INCH

    @property
    def centipoints(self) -> int:
        return self // self._EMUS_PER_CENTIPOINT

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
    def from_inches(cls, inches: int):
        return cls(inches * cls._EMUS_PER_INCH)

    @classmethod
    def from_centripoints(cls, centripoints: int):
        return cls(centripoints * cls._EMUS_PER_CENTIPOINT)

    @classmethod
    def from_cm(cls, cm: int):
        return cls(cm * cls._EMUS_PER_CM)

    @classmethod
    def from_mm(cls, mm: int):
        return cls(mm * cls._EMUS_PER_MM)

    @classmethod
    def from_pt(cls, pt: int):
        return cls(pt * cls._EMUS_PER_PT)

    @classmethod
    def from_px(cls, px: int):
        return cls(px * cls._PT_PER_PX * cls._EMUS_PER_PT)
