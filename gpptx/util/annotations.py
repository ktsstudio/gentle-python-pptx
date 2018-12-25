from typing import Callable


def dangerous_method(f: Callable) -> Callable:
    return f
