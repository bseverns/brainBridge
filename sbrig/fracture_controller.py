"""Fracture controller for controlled grain-cracks during morph transitions."""
from __future__ import annotations

import random
from dataclasses import dataclass

from .fracture import (
    FractureConfig,
    FractureState,
    update_envelope,
    apply_fracture,
    compute_phase,
)
from .morph import clamp01
from .scenes import Scene


@dataclass
class FractureTelemetry:
    """Telemetry data from fracture processing."""
    enabled: bool = False
    env: float = 0.0
    amount: float = 0.0
    w_audio: float = 0.0
    w_visual: float = 0.0
    w_processing: float = 0.0


class FractureController:
    """Manages fracture effects (Law 3) for morph transitions.
    
    Fractures are "controlled cracks" that add micro-jitter to parameters
    when crossing landmarks in the morph space. Weights control how much
    the effect applies to audio vs visual destinations.
    """

    def __init__(self, cfg: FractureConfig):
        self.cfg = cfg
        self.state = FractureState()
        
        # Controls
        self.enabled = bool(cfg.enabled)
        self.amount = float(cfg.amount)  # base intensity
        
        # Per-destination weights
        self.w_audio = 0.75
        self.w_visual = 0.75
        self.w_processing = 0.55  # visual-adjacent by default
        
        # Deterministic randomness
        self._rng = random.Random(1337)

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable fracture effects."""
        self.enabled = enabled

    def toggle_enabled(self) -> None:
        """Toggle fracture enabled state."""
        self.enabled = not self.enabled

    def set_amount(self, amount: float) -> None:
        """Set fracture intensity (0..1)."""
        self.amount = clamp01(amount)

    def set_weight_audio(self, weight: float) -> None:
        """Set audio destination weight (0..1)."""
        self.w_audio = clamp01(weight)

    def set_weight_visual(self, weight: float) -> None:
        """Set visual destination weight (0..1)."""
        self.w_visual = clamp01(weight)

    def set_weight_processing(self, weight: float) -> None:
        """Set processing destination weight (0..1)."""
        self.w_processing = clamp01(weight)

    def set_balance(self, balance: float) -> None:
        """Set audio/visual balance (0=audio, 1=visual)."""
        b = clamp01(balance)
        self.w_audio = clamp01(1.0 - b)
        self.w_visual = clamp01(b)

    def step(self, dt: float) -> None:
        """Decay the fracture envelope over time."""
        update_envelope(self.state, dt, self.cfg.decay_sec)

    def apply(self, scene: Scene, now: float) -> Scene:
        """Apply fracture effects to a scene.
        
        Args:
            scene: Scene to apply fracture to
            now: Current time for phase computation
            
        Returns:
            Scene with fracture effects applied (or unchanged if disabled)
        """
        if not self.enabled:
            return scene
        
        env_amount = clamp01(self.amount) * clamp01(self.state.env)
        if env_amount <= 0:
            return scene
        
        phase = compute_phase(now, self.cfg.rate_hz)
        
        return apply_fracture(
            scene,
            env_amount,
            w_audio=self.w_audio,
            w_visual=self.w_visual,
            w_processing=self.w_processing,
            cfg=self.cfg,
            rng=self._rng,
            phase=phase,
        )

    def is_active(self) -> bool:
        """Check if fracture effect is currently active."""
        return self.enabled and self.state.env > 0.001

    def get_telemetry(self) -> FractureTelemetry:
        """Get current telemetry for OSC broadcast."""
        return FractureTelemetry(
            enabled=self.enabled,
            env=self.state.env,
            amount=self.amount,
            w_audio=self.w_audio,
            w_visual=self.w_visual,
            w_processing=self.w_processing,
        )
