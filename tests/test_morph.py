"""Tests for sbrig.morph module."""
import math
from sbrig.morph import clamp01, apply_curve, apply_wells, apply_snap, SnapState


class TestClamp01:
    """Tests for clamp01 function."""

    def test_within_range(self):
        assert clamp01(0.5) == 0.5

    def test_at_boundaries(self):
        assert clamp01(0.0) == 0.0
        assert clamp01(1.0) == 1.0

    def test_below_zero(self):
        assert clamp01(-0.5) == 0.0
        assert clamp01(-100.0) == 0.0

    def test_above_one(self):
        assert clamp01(1.5) == 1.0
        assert clamp01(100.0) == 1.0


class TestApplyCurve:
    """Tests for apply_curve function."""

    def test_linear(self):
        assert apply_curve(0.0, "linear") == 0.0
        assert apply_curve(0.5, "linear") == 0.5
        assert apply_curve(1.0, "linear") == 1.0

    def test_smoothstep_endpoints(self):
        assert apply_curve(0.0, "smoothstep") == 0.0
        assert apply_curve(1.0, "smoothstep") == 1.0

    def test_smoothstep_midpoint(self):
        # smoothstep(0.5) = 3*(0.25) - 2*(0.125) = 0.75 - 0.25 = 0.5
        assert apply_curve(0.5, "smoothstep") == 0.5

    def test_smoothstep_quarter(self):
        # smoothstep(0.25) = 3*(0.0625) - 2*(0.015625) = 0.1875 - 0.03125 = 0.15625
        result = apply_curve(0.25, "smoothstep")
        assert abs(result - 0.15625) < 1e-6

    def test_sine_endpoints(self):
        assert apply_curve(0.0, "sine") == 0.0
        assert abs(apply_curve(1.0, "sine") - 1.0) < 1e-10

    def test_sine_midpoint(self):
        assert abs(apply_curve(0.5, "sine") - 0.5) < 1e-10

    def test_unknown_curve_falls_back_to_linear(self):
        assert apply_curve(0.5, "unknown_curve") == 0.5

    def test_clamps_input(self):
        assert apply_curve(-0.5, "linear") == 0.0
        assert apply_curve(1.5, "linear") == 1.0


class TestApplyWells:
    """Tests for apply_wells gravity function."""

    def test_at_well_point_stays(self):
        """Values at well points should stay there."""
        result = apply_wells(0.5, points=[0.0, 0.5, 1.0], radius=0.12, strength=0.35)
        assert abs(result - 0.5) < 0.01

    def test_near_well_is_pulled(self):
        """Values near a well should be pulled toward it."""
        result = apply_wells(0.45, points=[0.5], radius=0.12, strength=0.5)
        assert result > 0.45  # Should be pulled toward 0.5

    def test_far_from_wells_minimal_effect(self):
        """Values far from wells should have minimal pull."""
        result = apply_wells(0.25, points=[0.0, 1.0], radius=0.05, strength=0.5)
        # 0.25 is far from both 0.0 and 1.0 with small radius
        assert abs(result - 0.25) < 0.1

    def test_zero_strength_no_effect(self):
        """Zero strength should not move the value."""
        result = apply_wells(0.3, points=[0.5], radius=0.12, strength=0.0)
        assert result == 0.3

    def test_result_clamped(self):
        """Result should always be clamped to [0, 1]."""
        result = apply_wells(0.99, points=[1.0], radius=0.5, strength=1.0)
        assert 0.0 <= result <= 1.0


class TestApplySnap:
    """Tests for apply_snap with hysteresis."""

    def test_snap_when_close(self):
        """Snaps to point when within threshold."""
        state = SnapState()
        result = apply_snap(0.48, points=[0.5], threshold=0.05, hysteresis=0.03, state=state)
        assert result == 0.5
        assert state.snapped is True
        assert state.point == 0.5

    def test_no_snap_when_far(self):
        """Does not snap when outside threshold."""
        state = SnapState()
        result = apply_snap(0.3, points=[0.5], threshold=0.05, hysteresis=0.03, state=state)
        assert result == 0.3
        assert state.snapped is False

    def test_hysteresis_keeps_snapped(self):
        """Stays snapped until outside threshold + hysteresis."""
        state = SnapState(snapped=True, point=0.5)
        
        # Still within threshold + hysteresis (0.05 + 0.03 = 0.08)
        result = apply_snap(0.44, points=[0.5], threshold=0.05, hysteresis=0.03, state=state)
        assert result == 0.5
        assert state.snapped is True

    def test_hysteresis_releases(self):
        """Releases snap when outside threshold + hysteresis."""
        state = SnapState(snapped=True, point=0.5)
        
        # Outside threshold + hysteresis (0.42 - 0.5 = 0.08, need > 0.08)
        result = apply_snap(0.40, points=[0.5], threshold=0.05, hysteresis=0.03, state=state)
        assert result == 0.40
        assert state.snapped is False

    def test_snap_to_nearest_point(self):
        """Snaps to the nearest point when multiple are close."""
        state = SnapState()
        result = apply_snap(0.26, points=[0.0, 0.25, 0.5], threshold=0.05, hysteresis=0.03, state=state)
        assert result == 0.25
        assert state.point == 0.25

    def test_snap_endpoints(self):
        """Can snap to 0.0 and 1.0."""
        state = SnapState()
        result = apply_snap(0.02, points=[0.0, 0.5, 1.0], threshold=0.05, hysteresis=0.03, state=state)
        assert result == 0.0

        state = SnapState()
        result = apply_snap(0.98, points=[0.0, 0.5, 1.0], threshold=0.05, hysteresis=0.03, state=state)
        assert result == 1.0
