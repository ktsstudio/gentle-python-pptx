class Emu:
    def __init__(self, value: int):
        self._value = value

    def __int__(self) -> int:
        return self._value
