"""Tests for sbrig.morph_controller module."""
import tempfile
import os
from sbrig.morph_controller import MorphController, MorphTelemetry
from sbrig.morph import MorphConfig
from sbrig.scenes import Scene


def _write_scene(scene_dir: str, name: str, content: dict) -> None:
    import yaml
    path = os.path.join(scene_dir, f"{name}.yaml")
    with open(path, "w") as f:
        yaml.dump(content, f)


class TestMorphController:
    """Tests for MorphController class."""

    def test_set_target_clamps(self):
        """Target is clamped to 0..1."""
        cfg = MorphConfig()
        ctrl = MorphController(cfg, "/tmp")
        
        ctrl.set_target(1.5)
        assert ctrl.target == 1.0
        
        ctrl.set_target(-0.5)
        assert ctrl.target == 0.0

    def test_step_advances_slew(self):
        """Step advances the slew toward target."""
        cfg = MorphConfig(inertia_units_per_sec=10.0)
        ctrl = MorphController(cfg, "/tmp")
        
        ctrl.set_target(1.0)
        ctrl.step(0.1)  # 10 units/sec * 0.1s = 1.0
        
        assert ctrl.raw == 1.0

    def test_set_endpoint_with_valid_scene(self):
        """Setting endpoint with valid scene works."""
        with tempfile.TemporaryDirectory() as scene_dir:
            _write_scene(scene_dir, "test", {"name": "test", "samplebrain": {"energy": 0.5}})
            
            cfg = MorphConfig()
            ctrl = MorphController(cfg, scene_dir)
            
            result = ctrl.set_endpoint("A", "test")
            
            assert result is True
            assert ctrl.a_key == "test"
            assert ctrl.a_scene is not None

    def test_set_endpoint_with_missing_scene(self):
        """Setting endpoint with missing scene returns False."""
        cfg = MorphConfig()
        ctrl = MorphController(cfg, "/nonexistent")
        
        result = ctrl.set_endpoint("A", "missing")
        
        assert result is False
        assert ctrl.a_scene is None

    def test_swap_endpoints(self):
        """Swap exchanges A and B."""
        with tempfile.TemporaryDirectory() as scene_dir:
            _write_scene(scene_dir, "a", {"name": "a"})
            _write_scene(scene_dir, "b", {"name": "b"})
            
            cfg = MorphConfig()
            ctrl = MorphController(cfg, scene_dir)
            ctrl.set_endpoint("A", "a")
            ctrl.set_endpoint("B", "b")
            
            ctrl.swap_endpoints()
            
            assert ctrl.a_key == "b"
            assert ctrl.b_key == "a"

    def test_get_telemetry(self):
        """Telemetry reflects current state."""
        cfg = MorphConfig()
        ctrl = MorphController(cfg, "/tmp")
        ctrl.target = 0.5
        ctrl.raw = 0.4
        ctrl.applied = 0.35
        
        tel = ctrl.get_telemetry()
        
        assert isinstance(tel, MorphTelemetry)
        assert tel.t_target == 0.5


class TestSceneValidation:
    """Tests for scene validation."""

    def test_valid_scene_returns_empty(self):
        from sbrig.scenes import validate_scene, Scene
        
        scene = Scene(
            name="test",
            notes=None,
            touchdesigner={"/rig/energy": 0.5},
            samplebrain={"energy": 0.5},
            processing={"/rig/mode": 1},
        )
        
        warnings = validate_scene(scene)
        assert warnings == []

    def test_missing_name_raises(self):
        from sbrig.scenes import validate_scene, Scene, SceneValidationError
        import pytest
        
        scene = Scene(
            name="",
            notes=None,
            touchdesigner={},
            samplebrain={},
            processing={},
        )
        
        with pytest.raises(SceneValidationError):
            validate_scene(scene)

    def test_warns_on_missing_slash(self):
        from sbrig.scenes import validate_scene, Scene
        
        scene = Scene(
            name="test",
            notes=None,
            touchdesigner={"rig/energy": 0.5},  # missing leading /
            samplebrain={},
            processing={},
        )
        
        warnings = validate_scene(scene)
        assert len(warnings) == 1
        assert "should start with '/'" in warnings[0]

    def test_warns_on_out_of_range_macro(self):
        from sbrig.scenes import validate_scene, Scene
        
        scene = Scene(
            name="test",
            notes=None,
            touchdesigner={},
            samplebrain={"energy": 1.5},  # out of range
            processing={},
        )
        
        warnings = validate_scene(scene)
        assert len(warnings) == 1
        assert "expected 0.0-1.0" in warnings[0]
