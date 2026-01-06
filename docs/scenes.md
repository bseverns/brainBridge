# Scene Schema (sbrig/scenes.py)

This doc is the **scene contract** used by `sbrig/scenes.py`. It’s a small, readable YAML format that keeps a rig *playable* under pressure: half studio notebook, half teaching guide.

Scene files live in a directory (whatever you pass into `load_scene(scene_dir, name)`), and each file is named `<scene>.yaml`. Example: `scenes/forest-pulse.yaml`.

## Top-level keys (required vs optional)

`load_scene()` reads a YAML dict and turns it into a `Scene` dataclass. These keys are expected:

| Key | Required? | Type | Notes |
| --- | --- | --- | --- |
| `name` | Optional | string | Defaults to filename (`name` passed into `load_scene`). Always stored as a string. |
| `notes` | Optional | string | Freeform text. Use it to explain vibe, cues, or what *not* to touch. |
| `touchdesigner` | Optional | map/dict | Defaults to `{}`. Key/value controls for TouchDesigner. |
| `samplebrain` | Optional | map/dict | Defaults to `{}`. Key/value controls for Samplebrain. |
| `processing` | Optional | map/dict | Defaults to `{}`. Key/value controls for Processing. |

**The minimum valid scene** is an empty YAML file (`{}`) or a file with just `name:`. Everything else is optional.

## Example scene file

```yaml
name: "forest-pulse"
notes: "Slow inhale → big trunk pulses. Keep this wide and patient."

touchdesigner:
  blur: 0.15
  trail_amount: 0.8
  palette: "green"

samplebrain:
  energy: 0.2
  grain: 0.65
  texture: "mossy"  # non-numeric, so it *snaps* during morphs

processing:
  swirl: 0.4
  particles: 1200
  mode: "lofi"
```

## Morphing rules (numeric vs non-numeric)

When you morph between scenes (`morph_scenes(a, b, t)`), the bridge **interpolates numbers** and **snaps everything else**. That’s the whole rule. Simple. Musical.

- **Numeric values** (`int` or `float`) are linearly interpolated.
- **Non-numeric values** (strings, arrays, dicts, booleans, `null`) **snap**:
  - if `t < 0.5`, you get scene A’s value
  - if `t >= 0.5`, you get scene B’s value
- **Booleans** are explicitly **not** treated as numbers. (`True`/`False` are *not* interpolated.)

### Numeric morph example

```yaml
# Scene A
samplebrain:
  energy: 0.2

# Scene B
samplebrain:
  energy: 0.8

# t = 0.25 → 0.35
# t = 0.50 → 0.50
# t = 0.75 → 0.65
```

### Non-numeric snap example

```yaml
# Scene A
processing:
  mode: "lofi"

# Scene B
processing:
  mode: "hires"

# t = 0.49 → "lofi"
# t = 0.50 → "hires"
```

If you need a parameter to *glide*, make it numeric. If you want it to *jump*, make it non-numeric. That’s the punk-rock contract.

## How `samplebrain` keys map to Samplebrain bindings

The keys inside `samplebrain` should match the **macro names** in `bindings/samplebrain.yaml`.

In `bindings/samplebrain.yaml`, the top-level `macros` section lists known macro names (e.g. `energy`, `density`, `grain`, etc.) and the OSC address/type each macro should send to.

```yaml
macros:
  energy: { address: null, type: "f" }
  density: { address: null, type: "f" }
  grain: { address: null, type: "f" }
  # ...
```

### Mapping rule of thumb

- **Scene key → Samplebrain macro of the same name**.
- If the macro is unbound (`address: null`), the bridge can still run, but Samplebrain won’t receive updates until you wire it.

### Example mapping

```yaml
# scene
samplebrain:
  energy: 0.45
  grain: 0.9
```

```yaml
# bindings/samplebrain.yaml
macros:
  energy: { address: "/samplebrain/energy", type: "f" }
  grain: { address: "/samplebrain/grain", type: "f" }
```

That’s it: name matches name. No magic, no hidden registry, just human-readable intent.

## TL;DR

- **`name`, `notes` are optional**.
- `touchdesigner`, `samplebrain`, `processing` are **optional dicts**.
- **Numbers glide. Everything else snaps.**
- **`samplebrain` keys should match `bindings/samplebrain.yaml` macros**.
