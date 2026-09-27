from collections.abc import Sequence
from typing import Union

ValueT = Union[
    bool,
    int,
    float,
    str,
    bytes,
    Sequence[bool],
    Sequence[int],
    Sequence[float],
    Sequence[str],
]
