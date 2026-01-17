"""Tests for sbrig.slew module."""
from sbrig.slew import Slew


class TestSlew:
    """Tests for the Slew rate limiter."""

    def test_initial_value(self):
        """Slew starts at the initial value."""
        slew = Slew(initial=0.5, units_per_sec=2.0)
        assert slew.value == 0.5
        assert slew.target == 0.5

    def test_step_toward_target(self):
        """Slew moves toward target at the specified rate."""
        slew = Slew(initial=0.0, units_per_sec=2.0)
        slew.set_target(1.0)
        
        # After 0.25s at 2 units/sec, should move 0.5 units
        result = slew.step(0.25)
        assert result == 0.5
        assert slew.value == 0.5

    def test_step_reaches_target_exactly(self):
        """Slew snaps to target when within step range."""
        slew = Slew(initial=0.9, units_per_sec=2.0)
        slew.set_target(1.0)
        
        # 0.1 units needed, step allows 0.2 units (0.1s * 2 units/sec)
        result = slew.step(0.1)
        assert result == 1.0
        assert slew.value == 1.0

    def test_step_negative_direction(self):
        """Slew moves correctly in negative direction."""
        slew = Slew(initial=1.0, units_per_sec=2.0)
        slew.set_target(0.0)
        
        result = slew.step(0.25)
        assert result == 0.5

    def test_zero_dt_returns_current(self):
        """Zero dt returns current value without change."""
        slew = Slew(initial=0.5, units_per_sec=2.0)
        slew.set_target(1.0)
        
        result = slew.step(0.0)
        assert result == 0.5
        assert slew.value == 0.5

    def test_negative_dt_returns_current(self):
        """Negative dt returns current value without change."""
        slew = Slew(initial=0.5, units_per_sec=2.0)
        slew.set_target(1.0)
        
        result = slew.step(-0.1)
        assert result == 0.5

    def test_convergence_over_multiple_steps(self):
        """Slew converges to target over multiple steps."""
        slew = Slew(initial=0.0, units_per_sec=1.0)
        slew.set_target(1.0)
        
        # 10 steps of 0.1s each = 1.0 units total
        for _ in range(10):
            slew.step(0.1)
        
        assert abs(slew.value - 1.0) < 1e-9

    def test_already_at_target(self):
        """Slew stays at target when already there."""
        slew = Slew(initial=0.5, units_per_sec=2.0)
        slew.set_target(0.5)
        
        result = slew.step(1.0)
        assert result == 0.5
