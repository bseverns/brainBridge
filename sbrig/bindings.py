from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Union
import yaml


@dataclass
class Binding:
    """A single OSC control in Samplebrain."""
    address: str
    type: str  # 'f', 'i', 's'


@dataclass
class SamplebrainBindings:
    """Bindings grouped by semantic key.

    - macros: high-level performance controls (energy/chaos/etc.)
    - params: additional parameters (named however you like)

    Any entry with address: null / empty is treated as UNBOUND and ignored.
    """
    macros: Dict[str, Binding]
    params: Dict[str, Binding]


def _parse_binding_value(v: Any) -> Optional[Binding]:
    """Parse a YAML binding entry.

    Supported forms:
      energy: {address: "/foo", type: "f"}
      energy: "/foo"          # shorthand, assumes float
      energy: null              # unbound (ignored)
    """
    if v is None:
        return None

    # Shorthand: key: "/osc/address"
    if isinstance(v, str):
        addr = v.strip()
        if not addr:
            return None
        return Binding(address=addr, type="f")

    if not isinstance(v, dict):
        return None

    addr_val = v.get("address", None)
    if addr_val is None:
        return None

    addr = str(addr_val).strip()
    if not addr or addr.lower() in ("none", "null", "unbound", "disabled"):
        return None

    typ = str(v.get("type", "f")).strip().lower() or "f"
    if typ not in ("f", "i", "s"):
        typ = "f"
    return Binding(address=addr, type=typ)


def load_samplebrain_bindings(path: str) -> SamplebrainBindings:
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    def parse_map(m: Dict[str, Any]) -> Dict[str, Binding]:
        out: Dict[str, Binding] = {}
        for k, v in (m or {}).items():
            b = _parse_binding_value(v)
            if b is None:
                continue
            out[str(k)] = b
        return out

    return SamplebrainBindings(
        macros=parse_map(raw.get("macros", {}) or {}),
        params=parse_map(raw.get("params", {}) or {}),
    )
