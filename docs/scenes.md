# Scene Schema (sbrig/scenes.py)

This doc describes the scene file format used by `sbrig/scenes.py` and applied by
`sbrig/bridge.py`. Scenes are YAML files named `<scene>.yaml` and loaded by name.

Sample scenes live in:
- `config/scenes/embers.yaml`
- `config/scenes/steel.yaml`
- `config/scenes/panic.yaml`

## File location and naming

`load_scene(scene_dir, name)` reads `{scene_dir}/{name}.yaml`. The scene name defaults
to the filename if you omit `name:` in the file.

## Top-level keys

All keys are optional; missing maps default to `{}`.

| Key | Type | Default | Notes |
| --- | --- | --- | --- |
| `name` | string | filename | Stored as a string. |
| `notes` | string | null | Freeform stage notes. |
| `touchdesigner` | map | `{}` | OSC address to value; forwarded directly. |
| `samplebrain` | map | `{}` | Macro/param names; mapped via `bindings/samplebrain.yaml`. |
| `processing` | map | `{}` | OSC address to value; forwarded directly. |

Minimum valid scene: `{}` or a file with only `name:`.

## Destination behavior

- `touchdesigner` and `processing` are sent as-is: keys are OSC addresses, values are
  the argument payload. Example: `"/rig/energy": 0.7`.
- `samplebrain` keys are looked up in `bindings/samplebrain.yaml`.
  - If the key matches a `macros` or `params` entry, the bridge sends the mapped
    address and type to Samplebrain.
  - If the key is not bound, it is treated as a generic rig param and sent as
    `/rig/param/<key>`.

## Morphing rules (numeric vs non-numeric)

`morph_scenes(a, b, t)` interpolates numbers and snaps everything else.

- Numeric values: `int` or `float` (but not `bool`) are linearly interpolated.
- Non-numeric values: strings, lists, dicts, booleans, `null` snap at `t = 0.5`.

### Numeric morph example

```yaml
# Scene A
samplebrain:
  energy: 0.2

# Scene B
samplebrain:
  energy: 0.8

# t = 0.25 -> 0.35
# t = 0.50 -> 0.50
# t = 0.75 -> 0.65
```

### Non-numeric snap example

```yaml
# Scene A
processing:
  /rig/mode: "lofi"

# Scene B
processing:
  /rig/mode: "hires"

# t = 0.49 -> "lofi"
# t = 0.50 -> "hires"
```

## Example scene (real file shape)

```yaml
name: embers
notes: "Quiet heat. Low energy, slow drift."

touchdesigner:
  /rig/scene: "embers"
  /rig/energy: 0.20
  /rig/palette: 1

samplebrain:
  energy: 0.20
  chaos: 0.10

processing:
  /rig/mode: 1
```
