"""Tests for sbrig.fracture module."""
import random
from sbrig.fracture import (
    FractureConfig,
    FractureState,
    update_envelope,
    trigger_if_crossed,
    apply_fracture,
    compute_phase,
)
from sbrig.scenes import Scene


class TestUpdateEnvelope:
    """Tests for envelope decay."""

    def test_decay_over_time(self):
        """Envelope decays toward zero."""
        state = FractureState(env=1.0)
        
        update_envelope(state, dt=0.09, decay_sec=0.18)
        
        # After half the decay time, should be at 0.5
        assert abs(state.env - 0.5) < 1e-6

    def test_full_decay(self):
        """Envelope reaches zero after full decay period."""
        state = FractureState(env=1.0)
        
        update_envelope(state, dt=0.18, decay_sec=0.18)
        
        assert state.env == 0.0

    def test_zero_decay_sec_zeroes_env(self):
        """Zero decay_sec immediately zeroes envelope."""
        state = FractureState(env=0.8)
        
        update_envelope(state, dt=0.1, decay_sec=0.0)
        
        assert state.env == 0.0

    def test_does_not_go_negative(self):
        """Envelope never goes below zero."""
        state = FractureState(env=0.1)
        
        update_envelope(state, dt=1.0, decay_sec=0.18)
        
        assert state.env == 0.0


class TestTriggerIfCrossed:
    """Tests for threshold crossing detection."""

    def test_crossing_triggers(self):
        """Crossing a threshold sets env to 1."""
        state = FractureState(env=0.0, last_t=0.4)
        
        triggered = trigger_if_crossed(state, t=0.6, thresholds=[0.5])
        
        assert triggered is True
        assert state.env == 1.0
        assert state.last_t == 0.6

    def test_crossing_downward_triggers(self):
        """Crossing downward also triggers."""
        state = FractureState(env=0.0, last_t=0.6)
        
        triggered = trigger_if_crossed(state, t=0.4, thresholds=[0.5])
        
        assert triggered is True
        assert state.env == 1.0

    def test_no_crossing_no_trigger(self):
        """No trigger when not crossing threshold."""
        state = FractureState(env=0.0, last_t=0.3)
        
        triggered = trigger_if_crossed(state, t=0.4, thresholds=[0.5])
        
        assert triggered is False
        assert state.env == 0.0
        assert state.last_t == 0.4

    def test_multiple_thresholds(self):
        """Triggers on any threshold crossing."""
        state = FractureState(env=0.0, last_t=0.2)
        
        triggered = trigger_if_crossed(state, t=0.3, thresholds=[0.25, 0.5, 0.75])
        
        assert triggered is True

    def test_exact_threshold_value(self):
        """Landing exactly on threshold counts as crossing."""
        state = FractureState(env=0.0, last_t=0.4)
        
        triggered = trigger_if_crossed(state, t=0.5, thresholds=[0.5])
        
        assert triggered is True


class TestApplyFracture:
    """Tests for fracture jitter application."""

    def test_zero_env_no_change(self):
        """Zero env_amount returns unchanged scene."""
        scene = Scene(
            name="test", notes=None,
            touchdesigner={"/rig/energy": 0.5},
            samplebrain={"grain": 0.5},
            processing={"/rig/mode": 0.5},
        )
        cfg = FractureConfig()
        rng = random.Random(42)
        
        result = apply_fracture(
            scene, env_amount=0.0,
            w_audio=1.0, w_visual=1.0, w_processing=1.0,
            cfg=cfg, rng=rng, phase=0
        )
        
        assert result.touchdesigner["/rig/energy"] == 0.5
        assert result.samplebrain["grain"] == 0.5

    def test_fracture_modifies_values(self):
        """Non-zero env_amount modifies target values."""
        scene = Scene(
            name="test", notes=None,
            touchdesigner={"/rig/energy": 0.5},
            samplebrain={"grain": 0.5},
            processing={"/rig/mode": 0.5},
        )
        cfg = FractureConfig()
        rng = random.Random(42)
        
        result = apply_fracture(
            scene, env_amount=0.5,
            w_audio=1.0, w_visual=1.0, w_processing=1.0,
            cfg=cfg, rng=rng, phase=0
        )
        
        # Values should be modified (jittered)
        assert result.samplebrain["grain"] != 0.5

    def test_weight_zero_no_modification(self):
        """Zero weight for a domain prevents modification."""
        scene = Scene(
            name="test", notes=None,
            touchdesigner={"/rig/energy": 0.5},
            samplebrain={"grain": 0.5},
            processing={"/rig/mode": 0.5},
        )
        cfg = FractureConfig()
        rng = random.Random(42)
        
        result = apply_fracture(
            scene, env_amount=1.0,
            w_audio=0.0, w_visual=1.0, w_processing=0.0,
            cfg=cfg, rng=rng, phase=0
        )
        
        # Audio (samplebrain) should be unchanged
        assert result.samplebrain["grain"] == 0.5

    def test_values_stay_clamped(self):
        """Fractured values are clamped to [0, 1] for normalized params."""
        scene = Scene(
            name="test", notes=None,
            touchdesigner={"/rig/energy": 0.99},
            samplebrain={"grain": 0.01},
            processing={},
        )
        cfg = FractureConfig()
        rng = random.Random(42)
        
        # High env_amount to force potential out-of-range
        result = apply_fracture(
            scene, env_amount=1.0,
            w_audio=1.0, w_visual=1.0, w_processing=1.0,
            cfg=cfg, rng=rng, phase=0
        )
        
        # All values should still be in valid range
        for v in result.samplebrain.values():
            if isinstance(v, (int, float)):
                assert 0.0 <= v <= 1.0


class TestComputePhase:
    """Tests for phase computation."""

    def test_phase_increases_with_time(self):
        """Phase increases as time progresses."""
        phase1 = compute_phase(0.0, rate_hz=10.0)
        phase2 = compute_phase(0.1, rate_hz=10.0)
        phase3 = compute_phase(0.2, rate_hz=10.0)
        
        assert phase2 > phase1
        assert phase3 > phase2

    def test_phase_rate_scaling(self):
        """Higher rate_hz produces more phase changes per second."""
        slow = compute_phase(1.0, rate_hz=10.0)
        fast = compute_phase(1.0, rate_hz=20.0)
        
        assert fast == 2 * slow

    def test_min_rate_clamped(self):
        """Very low rate_hz is clamped to prevent division issues."""
        # Should not raise, even with very low rate
        phase = compute_phase(1.0, rate_hz=0.01)
        assert isinstance(phase, int)
