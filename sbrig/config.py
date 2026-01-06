from __future__ import annotations

from dataclasses import dataclass
from typing import Dict
import yaml

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

    return BridgeConfig(
        listen_host=str(listen.get("host", "0.0.0.0")),
        listen_port=int(listen.get("port", 9000)),
        destinations=destinations,
        slew_units_per_sec={k: float(v) for k, v in (raw.get("slew_units_per_sec", {}) or {}).items()},
        rate_limit_hz=float(raw.get("rate_limit_hz", 120)),
    )
