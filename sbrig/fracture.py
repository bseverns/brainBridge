from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
import random
import time

from .morph import clamp01
from .scenes import Scene

@dataclass
class FractureConfig:
    enabled: bool = True

    # Where fractures trigger (0..1 morph space). Crossing a threshold "sparks" the crack.
    thresholds: List[float] = None  # defaults in __post_init__

    # How long a crack lasts after triggering
    decay_sec: float = 0.18

    # Base intensity of the crack (0..1-ish). It's multiplied by an envelope (0..1).
    amount: float = 0.35

    # How fast the crack jitter changes (Hz). Higher = more granular.
    rate_hz: float = 18.0

    # Which semantic keys to fracture for Samplebrain (audio)
    samplebrain_keys: List[str] = None

    # Which OSC addresses to fracture for TouchDesigner (visual)
    touchdesigner_addrs: List[str] = None

    # Which OSC addresses to fracture for Processing (often visual/logic)
    processing_addrs: List[str] = None

    def __post_init__(self):
        if self.thresholds is None:
            self.thresholds = [0.25, 0.5, 0.75]
        if self.samplebrain_keys is None:
            self.samplebrain_keys = ["grain", "chaos", "tightness", "density"]
        if self.touchdesigner_addrs is None:
            self.touchdesigner_addrs = ["/rig/energy", "/rig/vis_trim", "/rig/vis_density_trim"]
        if self.processing_addrs is None:
            self.processing_addrs = ["/rig/mode"]

@dataclass
class FractureState:
    env: float = 0.0
    last_t: float = 0.0
    last_step_time: float = 0.0
    last_phase: int = 0

def _is_number(x: Any) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)

def _clamp_like(v: float, original: Any) -> float:
    # If original looks like a normalized control, clamp; otherwise leave it.
    if _is_number(original) and 0.0 <= float(original) <= 1.0:
        return clamp01(v)
    return v

def _jitter(rng: random.Random, strength: float) -> float:
    # -1..1
    return (rng.random() * 2.0 - 1.0) * strength

def update_envelope(state: FractureState, dt: float, decay_sec: float) -> None:
    if decay_sec <= 0:
        state.env = 0.0
        return
    state.env = max(0.0, state.env - (dt / decay_sec))

def trigger_if_crossed(state: FractureState, t: float, thresholds: List[float]) -> bool:
    prev = float(state.last_t)
    cur = float(t)
    trig = False
    for th in thresholds:
        th = clamp01(th)
        crossed = (prev < th <= cur) or (prev > th >= cur)
        if crossed:
            trig = True
            break
    if trig:
        state.env = 1.0
    state.last_t = cur
    return trig

def apply_fracture(
    scene: Scene,
    env_amount: float,
    *,
    w_audio: float,
    w_visual: float,
    w_processing: float,
    cfg: FractureConfig,
    rng: random.Random,
    phase: int,
) -> Scene:
    """Return a new Scene with small 'cracks' applied.

    env_amount: 0..1 envelope-scaled intensity (already includes cfg.amount * env)
    weights: per-destination multipliers
    phase: changes only at cfg.rate_hz, so jitter doesn't strobe at morph apply rate
    """
    if env_amount <= 0:
        return scene

    # Deterministic-ish per phase to avoid ultra-fast noise
    rng.seed(phase)

    def crack_dict(d: Dict[str, Any], keys: List[str], w: float) -> Dict[str, Any]:
        if env_amount <= 0 or w <= 0:
            return d
        out = dict(d)
        strength = env_amount * w
        for k in keys:
            if k in out and _is_number(out[k]):
                out[k] = _clamp_like(float(out[k]) + _jitter(rng, strength), out[k])
        return out

    def crack_addrs(d: Dict[str, Any], addrs: List[str], w: float) -> Dict[str, Any]:
        if env_amount <= 0 or w <= 0:
            return d
        out = dict(d)
        strength = env_amount * w
        for a in addrs:
            if a in out and _is_number(out[a]):
                out[a] = _clamp_like(float(out[a]) + _jitter(rng, strength), out[a])
        return out

    return Scene(
        name=scene.name,
        notes=scene.notes,
        touchdesigner=crack_addrs(scene.touchdesigner, cfg.touchdesigner_addrs, w_visual),
        samplebrain=crack_dict(scene.samplebrain, cfg.samplebrain_keys, w_audio),
        processing=crack_addrs(scene.processing, cfg.processing_addrs, w_processing),
    )

def compute_phase(now: float, rate_hz: float) -> int:
    rate_hz = max(0.1, float(rate_hz))
    return int(now * rate_hz)
