from typing import List, Optional, Any


def first_or_none(l: List[Any]) -> Optional[Any]:
    if len(l) == 0:
        return None
    else:
        return l[0]
