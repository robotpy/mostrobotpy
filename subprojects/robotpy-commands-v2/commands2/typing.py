from collections.abc import Callable
from typing import TypeAlias

# Type Aliases
FloatSupplier: TypeAlias = Callable[[], float]
FloatOrFloatSupplier: TypeAlias = float | Callable[[], float]
