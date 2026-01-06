from __future__ import annotations
from typing import Any

def coerce_arg(arg: Any, type_tag: str) -> Any:
    type_tag = (type_tag or "f").lower()
    if type_tag == "f":
        return float(arg)
    if type_tag == "i":
        return int(float(arg))
    if type_tag == "s":
        return str(arg)
    return arg
