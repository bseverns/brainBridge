from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, List
import yaml

from .morph import MorphConfig
from .fracture import FractureConfig

@dataclass
class Endpoint:
    enabled: bool
    host: str
    port: int

@dataclass
class BridgeConfig:
    listen_host: str
    listen_port: int
    destinations: Dict[str, Endpoint]
    slew_units_per_sec: Dict[str, float]
    rate_limit_hz: float
    morph: MorphConfig
    fracture: FractureConfig

def _as_float_list(x: Any) -> List[float]:
    if x is None:
        return []
    if isinstance(x, (list, tuple)):
        out = []
        for v in x:
            try:
                out.append(float(v))
            except Exception:
                pass
        return out
    return []

def _as_str_list(x: Any) -> List[str]:
    if x is None:
        return []
    if isinstance(x, (list, tuple)):
        out = []
        for v in x:
            try:
                out.append(str(v))
            except Exception:
                pass
        return out
    return []

def load_config(path: str) -> BridgeConfig:
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    listen = raw.get("listen", {}) or {}
    destinations_raw = raw.get("destinations", {}) or {}

    destinations: Dict[str, Endpoint] = {}
    for name, d in destinations_raw.items():
        destinations[name] = Endpoint(
            enabled=bool(d.get("enabled", True)),
            host=str(d.get("host", "127.0.0.1")),
            port=int(d.get("port", 0)),
        )

    morph_raw = raw.get("morph", {}) or {}
    morph = MorphConfig(
        curve=str(morph_raw.get("curve", "smoothstep")),
        inertia_units_per_sec=float(morph_raw.get("inertia_units_per_sec", 2.0)),
        apply_hz=float(morph_raw.get("apply_hz", 45.0)),
        wells_enabled=bool(morph_raw.get("wells_enabled", True)),
        well_points=_as_float_list(morph_raw.get("well_points")) or None,
        well_radius=float(morph_raw.get("well_radius", 0.12)),
        well_strength=float(morph_raw.get("well_strength", 0.35)),
        snap_enabled=bool(morph_raw.get("snap_enabled", True)),
        snap_points=_as_float_list(morph_raw.get("snap_points")) or None,
        snap_threshold=float(morph_raw.get("snap_threshold", 0.05)),
        snap_hysteresis=float(morph_raw.get("snap_hysteresis", 0.03)),
    )

    frac_raw = raw.get("fracture", {}) or {}
    fracture = FractureConfig(
        enabled=bool(frac_raw.get("enabled", True)),
        thresholds=_as_float_list(frac_raw.get("thresholds")) or None,
        decay_sec=float(frac_raw.get("decay_sec", 0.18)),
        amount=float(frac_raw.get("amount", 0.35)),
        rate_hz=float(frac_raw.get("rate_hz", 18.0)),
        samplebrain_keys=_as_str_list(frac_raw.get("samplebrain_keys")) or None,
        touchdesigner_addrs=_as_str_list(frac_raw.get("touchdesigner_addrs")) or None,
        processing_addrs=_as_str_list(frac_raw.get("processing_addrs")) or None,
    )

    return BridgeConfig(
        listen_host=str(listen.get("host", "0.0.0.0")),
        listen_port=int(listen.get("port", 9000)),
        destinations=destinations,
        slew_units_per_sec={k: float(v) for k, v in (raw.get("slew_units_per_sec", {}) or {}).items()},
        rate_limit_hz=float(raw.get("rate_limit_hz", 120)),
        morph=morph,
        fracture=fracture,
    )
