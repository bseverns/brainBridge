from __future__ import annotations

class Slew:
    """Simple slew limiter for smoothing values over time."""
    def __init__(self, initial: float = 0.0, units_per_sec: float = 2.0):
        self.value = float(initial)
        self.target = float(initial)
        self.units_per_sec = float(units_per_sec)

    def set_target(self, target: float) -> None:
        self.target = float(target)

    def step(self, dt: float) -> float:
        if dt <= 0:
            return self.value
        max_delta = self.units_per_sec * dt
        delta = self.target - self.value
        if abs(delta) <= max_delta:
            self.value = self.target
        else:
            self.value += max_delta if delta > 0 else -max_delta
        return self.value
