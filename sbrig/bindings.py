from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional
import yaml

@dataclass
class Binding:
    address: Optional[str]
    type: str  # 'f', 'i', 's'

@dataclass
class SamplebrainBindings:
    macros: Dict[str, Binding]
    params: Dict[str, Binding]

def load_samplebrain_bindings(path: str) -> SamplebrainBindings:
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    def parse_map(m: Dict[str, Any]) -> Dict[str, Binding]:
        out: Dict[str, Binding] = {}
        for k, v in (m or {}).items():
            addr = v.get("address", None)
            addr = None if addr in (None, "", "null") else str(addr)
            out[str(k)] = Binding(address=addr, type=str(v.get("type", "f")))
        return out

    return SamplebrainBindings(
        macros=parse_map(raw.get("macros", {}) or {}),
        params=parse_map(raw.get("params", {}) or {}),
    )
