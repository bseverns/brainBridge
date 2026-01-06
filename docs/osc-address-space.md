# OSC Address Space (House API)

## Inputs (into the bridge)

### Cues
- `/rig/cue/<scene>` (no args)
- `/rig/cue` (s)  (optional)

See `docs/scenes.md` for the scene schema and morph rules that back `/rig/cue/*`.

### Macros (0..1 floats)
- `/rig/energy`
- `/rig/density`
- `/rig/grain`
- `/rig/tightness`
- `/rig/chaos`
- `/rig/drift`
- `/rig/space`
- `/rig/color`
- `/rig/vis_trim`
- `/rig/vis_density_trim`
- `/rig/global_trim`

### Morph space
- `/rig/morph/setA` (no args)
- `/rig/morph/setB` (no args)
- `/rig/morph/swap` (no args)
- `/rig/morph/commit` (no args)
- `/rig/morph/t` (f 0..1)

### Fracture (Law 3)
- `/rig/fracture/enable` (int or no-arg toggle)
- `/rig/fracture/amount` (f 0..1)
- `/rig/fracture/w_audio` (f 0..1)
- `/rig/fracture/w_visual` (f 0..1)
- `/rig/fracture/w_processing` (f 0..1)
- `/rig/fracture/balance` (f 0..1)

---

## Outputs (from the bridge)

Scenes / status:
- `/rig/scene` (s)
- `/rig/health/connected` (s, i)

Morph telemetry:
- `/rig/morph/a` (s)
- `/rig/morph/b` (s)
- `/rig/morph/t_target` (f)
- `/rig/morph/t_raw` (f)
- `/rig/morph/t_applied` (f)
- `/rig/morph/snapped` (i)
- `/rig/morph/snap_point` (f)

Fracture telemetry:
- `/rig/fracture/enabled` (i)
- `/rig/fracture/amount` (f)
- `/rig/fracture/env` (f)
- `/rig/fracture/w_audio` (f)
- `/rig/fracture/w_visual` (f)
- `/rig/fracture/w_processing` (f)
