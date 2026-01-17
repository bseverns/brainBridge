"""Tests for sbrig.scenes module."""
from sbrig.scenes import Scene, morph_scenes


class TestMorphScenes:
    """Tests for scene morphing."""

    def test_morph_at_zero_returns_scene_a(self):
        """At t=0, morphed scene equals scene A."""
        a = Scene(
            name="scene_a",
            notes="A",
            touchdesigner={"/rig/energy": 0.0},
            samplebrain={"chaos": 0.2},
            processing={"/rig/mode": "lofi"},
        )
        b = Scene(
            name="scene_b",
            notes="B",
            touchdesigner={"/rig/energy": 1.0},
            samplebrain={"chaos": 0.8},
            processing={"/rig/mode": "hires"},
        )
        
        result = morph_scenes(a, b, 0.0)
        
        assert result.touchdesigner["/rig/energy"] == 0.0
        assert result.samplebrain["chaos"] == 0.2
        assert result.processing["/rig/mode"] == "lofi"

    def test_morph_at_one_returns_scene_b(self):
        """At t=1, morphed scene equals scene B."""
        a = Scene(
            name="scene_a",
            notes="A",
            touchdesigner={"/rig/energy": 0.0},
            samplebrain={"chaos": 0.2},
            processing={"/rig/mode": "lofi"},
        )
        b = Scene(
            name="scene_b",
            notes="B",
            touchdesigner={"/rig/energy": 1.0},
            samplebrain={"chaos": 0.8},
            processing={"/rig/mode": "hires"},
        )
        
        result = morph_scenes(a, b, 1.0)
        
        assert result.touchdesigner["/rig/energy"] == 1.0
        assert result.samplebrain["chaos"] == 0.8
        assert result.processing["/rig/mode"] == "hires"

    def test_numeric_interpolation(self):
        """Numeric values are linearly interpolated."""
        a = Scene(
            name="a", notes=None,
            touchdesigner={"/rig/energy": 0.0},
            samplebrain={"chaos": 0.0},
            processing={},
        )
        b = Scene(
            name="b", notes=None,
            touchdesigner={"/rig/energy": 1.0},
            samplebrain={"chaos": 1.0},
            processing={},
        )
        
        result = morph_scenes(a, b, 0.25)
        
        assert abs(result.touchdesigner["/rig/energy"] - 0.25) < 1e-6
        assert abs(result.samplebrain["chaos"] - 0.25) < 1e-6

    def test_non_numeric_snaps_at_half(self):
        """Non-numeric values snap at t=0.5."""
        a = Scene(
            name="a", notes=None,
            touchdesigner={},
            samplebrain={},
            processing={"/rig/mode": "lofi"},
        )
        b = Scene(
            name="b", notes=None,
            touchdesigner={},
            samplebrain={},
            processing={"/rig/mode": "hires"},
        )
        
        # Before 0.5, use A
        result = morph_scenes(a, b, 0.49)
        assert result.processing["/rig/mode"] == "lofi"
        
        # At 0.5 and after, use B
        result = morph_scenes(a, b, 0.5)
        assert result.processing["/rig/mode"] == "hires"

    def test_mixed_keys_union(self):
        """Keys from both scenes are included in result."""
        a = Scene(
            name="a", notes=None,
            touchdesigner={"/rig/energy": 0.5},
            samplebrain={"only_a": 0.3},
            processing={},
        )
        b = Scene(
            name="b", notes=None,
            touchdesigner={"/rig/density": 0.8},
            samplebrain={"only_b": 0.7},
            processing={},
        )
        
        result = morph_scenes(a, b, 0.5)
        
        # Keys unique to A
        assert "only_a" in result.samplebrain
        # Keys unique to B
        assert "only_b" in result.samplebrain
        # Keys unique to each side's touchdesigner
        assert "/rig/energy" in result.touchdesigner
        assert "/rig/density" in result.touchdesigner

    def test_name_format(self):
        """Morphed scene name follows expected format."""
        a = Scene(name="embers", notes=None, touchdesigner={}, samplebrain={}, processing={})
        b = Scene(name="steel", notes=None, touchdesigner={}, samplebrain={}, processing={})
        
        result = morph_scenes(a, b, 0.75)
        
        assert "embers" in result.name
        assert "steel" in result.name
        assert "0.75" in result.name

    def test_clamps_t_to_valid_range(self):
        """t values outside [0, 1] are clamped."""
        a = Scene(
            name="a", notes=None,
            touchdesigner={"/rig/energy": 0.0},
            samplebrain={},
            processing={},
        )
        b = Scene(
            name="b", notes=None,
            touchdesigner={"/rig/energy": 1.0},
            samplebrain={},
            processing={},
        )
        
        result_below = morph_scenes(a, b, -0.5)
        assert result_below.touchdesigner["/rig/energy"] == 0.0
        
        result_above = morph_scenes(a, b, 1.5)
        assert result_above.touchdesigner["/rig/energy"] == 1.0

    def test_boolean_treated_as_non_numeric(self):
        """Booleans are not interpolated, they snap."""
        a = Scene(
            name="a", notes=None,
            touchdesigner={"/rig/flag": True},
            samplebrain={},
            processing={},
        )
        b = Scene(
            name="b", notes=None,
            touchdesigner={"/rig/flag": False},
            samplebrain={},
            processing={},
        )
        
        result = morph_scenes(a, b, 0.25)
        assert result.touchdesigner["/rig/flag"] is True
        
        result = morph_scenes(a, b, 0.75)
        assert result.touchdesigner["/rig/flag"] is False
