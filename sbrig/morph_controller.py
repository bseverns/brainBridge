"""Morph controller for scene crossfading with musical physics."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional

from .config import BridgeConfig
from .morph import MorphConfig, clamp01, apply_curve, apply_wells, apply_snap, SnapState
from .slew import Slew
from .scenes import Scene, morph_scenes, load_scene
from .fracture import FractureConfig, FractureState, trigger_if_crossed


@dataclass
class MorphTelemetry:
    """Telemetry data from morph processing."""
    t_target: float = 0.0
    t_raw: float = 0.0
    t_applied: float = 0.0
    snapped: bool = False
    snap_point: Optional[float] = None
    a_key: Optional[str] = None
    b_key: Optional[str] = None


class MorphController:
    """Manages scene morphing with inertia, wells, and snap physics.
    
    Implements the "Morph Space" with three laws:
    1. Inertia — smooths controller input
    2. Gravity + Snap — pulls toward and locks on landmarks
    3. Fracture triggers — detected here, applied separately
    """

    def __init__(self, cfg: MorphConfig, scene_dir: str):
        self.cfg = cfg
        self.scene_dir = scene_dir
        
        # Scene endpoints
        self.a_key: Optional[str] = None
        self.b_key: Optional[str] = None
        self.a_scene: Optional[Scene] = None
        self.b_scene: Optional[Scene] = None
        
        # Morph position state
        self.target: float = 0.0       # controller target
        self.raw: float = 0.0          # after inertia slew
        self.applied: float = 0.0      # after curve/wells/snap
        
        # Physics state
        self.slew = Slew(initial=0.0, units_per_sec=cfg.inertia_units_per_sec)
        self.snap_state = SnapState()
        
        # Rate limiting
        self._last_apply_time: float = 0.0
        self._min_interval = 1.0 / max(1.0, cfg.apply_hz)

    def set_target(self, t: float) -> None:
        """Set the morph target position (0..1)."""
        self.target = clamp01(t)

    def set_endpoint(self, which: str, scene_key: str) -> bool:
        """Set morph endpoint A or B to a scene.
        
        Returns True if successful, False if scene not found.
        """
        try:
            scene = load_scene(self.scene_dir, scene_key)
        except FileNotFoundError:
            return False
        
        if which.upper() == "A":
            self.a_key = scene_key
            self.a_scene = scene
        else:
            self.b_key = scene_key
            self.b_scene = scene
        return True

    def swap_endpoints(self) -> None:
        """Swap A and B endpoints."""
        self.a_key, self.b_key = self.b_key, self.a_key
        self.a_scene, self.b_scene = self.b_scene, self.a_scene
        self.snap_state.snapped = False
        self.snap_state.point = None

    def commit(self) -> Optional[Scene]:
        """Commit current morph position as new A endpoint.
        
        Returns the committed scene, or None if endpoints not set.
        """
        if not self.a_scene or not self.b_scene:
            return None
        
        committed = morph_scenes(self.a_scene, self.b_scene, self.applied)
        self.a_scene = committed
        self.a_key = committed.name
        self.target = 0.0
        self.slew.set_target(0.0)
        return committed

    def step(self, dt: float) -> None:
        """Advance morph physics by dt seconds."""
        self.slew.set_target(self.target)
        self.raw = self.slew.step(dt)

    def apply(self, now: float, fracture_cfg: Optional[FractureConfig] = None,
              fracture_state: Optional[FractureState] = None,
              force: bool = False) -> Optional[Scene]:
        """Apply morph physics and return morphed scene if ready.
        
        Args:
            now: Current time
            fracture_cfg: Optional fracture config for trigger detection
            fracture_state: Optional fracture state for trigger detection
            force: Force application regardless of rate limit
            
        Returns:
            Morphed scene if applied, None if rate-limited or endpoints not set
        """
        if not force and (now - self._last_apply_time) < self._min_interval:
            return None
        
        if not self.a_scene or not self.b_scene:
            return None
        
        # Apply physics laws
        t = clamp01(self.raw)
        t = apply_curve(t, self.cfg.curve)
        
        if self.cfg.wells_enabled:
            t = apply_wells(
                t,
                points=self.cfg.well_points,
                radius=self.cfg.well_radius,
                strength=self.cfg.well_strength,
            )
        
        if self.cfg.snap_enabled:
            t = apply_snap(
                t,
                points=self.cfg.snap_points,
                threshold=self.cfg.snap_threshold,
                hysteresis=self.cfg.snap_hysteresis,
                state=self.snap_state,
            )
        
        # Detect fracture triggers
        if fracture_cfg and fracture_state and fracture_cfg.enabled:
            trigger_if_crossed(fracture_state, t, fracture_cfg.thresholds)
        
        # Check if actually changed
        if not force and abs(t - self.applied) < 1e-3:
            return None
        
        self.applied = t
        self._last_apply_time = now
        
        return morph_scenes(self.a_scene, self.b_scene, t)

    def get_telemetry(self) -> MorphTelemetry:
        """Get current telemetry for OSC broadcast."""
        return MorphTelemetry(
            t_target=self.target,
            t_raw=clamp01(self.raw),
            t_applied=self.applied,
            snapped=self.snap_state.snapped,
            snap_point=self.snap_state.point,
            a_key=self.a_key,
            b_key=self.b_key,
        )

    def has_endpoints(self) -> bool:
        """Check if both endpoints are set."""
        return self.a_scene is not None and self.b_scene is not None
