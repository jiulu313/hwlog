import math
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class Request:
    ts: datetime
    method: str
    path: str
    status: int
    duration_ms: float | None = None


def normalize_duration(value: object) -> float | None:
    if type(value) not in (int, float):
        return None
    try:
        number = float(value)
    except OverflowError:
        return None
    return number if math.isfinite(number) and number >= 0 else None
