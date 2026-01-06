from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional
import math

@dataclass
class MorphConfig:
    # "linear" | "smoothstep" | "ease_in_out_sine"
    curve: str = "smoothstep"

    # Inertia smoothing: how fast the morph can change (units per second).
    # Higher = snappier. Lower = glidier.
    inertia_units_per_sec: float = 2.0

    # Apply morphed scene at most this often (avoids flooding downstream).
    apply_hz: float = 45.0

    # Gravity wells gently pull the morph position toward certain anchor points.
    wells_enabled: bool = True
    well_points: List[float] = None  # defaults in __post_init__
    well_radius: float = 0.12        # how wide each well feels
    well_strength: float = 0.35      # how hard it pulls (0..1-ish)

    # Snap locks to points when close enough (with hysteresis).
    snap_enabled: bool = True
    snap_points: List[float] = None  # defaults in __post_init__
    snap_threshold: float = 0.05     # snap when within this distance
    snap_hysteresis: float = 0.03    # stay snapped until this much farther

    def __post_init__(self):
        if self.well_points is None:
            self.well_points = [0.0, 0.5, 1.0]
        if self.snap_points is None:
            self.snap_points = [0.0, 0.5, 1.0]

def clamp01(x: float) -> float:
    return max(0.0, min(1.0, float(x)))

def apply_curve(t: float, curve: str) -> float:
    t = clamp01(t)
    c = (curve or "linear").lower().strip()

    if c == "linear":
        return t

    if c == "smoothstep":
        # classic: 3t^2 - 2t^3
        return t * t * (3.0 - 2.0 * t)

    if c in ("ease_in_out_sine", "sine"):
        return 0.5 - 0.5 * math.cos(math.pi * t)

    # fallback
    return t

def apply_wells(t: float, points: List[float], radius: float, strength: float) -> float:
    """Pull t toward each point with a gaussian-like influence."""
    t = clamp01(t)
    radius = max(1e-6, float(radius))
    strength = max(0.0, float(strength))

    for p in points:
        p = clamp01(p)
        d = t - p
        influence = math.exp(- (d * d) / (2.0 * radius * radius))
        t = t + (p - t) * strength * influence

    return clamp01(t)

@dataclass
class SnapState:
    snapped: bool = False
    point: Optional[float] = None

def apply_snap(t: float, points: List[float], threshold: float, hysteresis: float, state: SnapState) -> float:
    """Snap with hysteresis: if snapped, stay snapped until leaving threshold+hysteresis."""
    t = clamp01(t)
    threshold = max(0.0, float(threshold))
    hysteresis = max(0.0, float(hysteresis))

    pts = [clamp01(p) for p in points]

    if state.snapped and state.point is not None:
        if abs(t - state.point) <= (threshold + hysteresis):
            return state.point
        state.snapped = False
        state.point = None

    closest = None
    best = 1e9
    for p in pts:
        d = abs(t - p)
        if d < best:
            best = d
            closest = p

    if closest is not None and best <= threshold:
        state.snapped = True
        state.point = closest
        return closest

    return t
