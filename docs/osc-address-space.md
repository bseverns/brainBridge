# OSC Address Space (House API)

Your rig speaks one OSC language: `/rig/*`.

ReaLearn's target **OSC: Send message** can send OSC messages with **up to one argument**.  
So this API supports **address-only triggers** and **single-argument controls**.

## Inputs (into the bridge)

### Cues (recommended for button mappings)
- `/rig/cue/<scene>` (no args)
  - examples: `/rig/cue/embers`, `/rig/cue/steel`

Also supported:
- `/rig/cue` (s) : trigger a named scene (e.g. `"embers"`)
- `/rig/scene/load` (s) : same as cue

### Macros (recommended for knobs/faders)
- `/rig/energy` (f 0..1)
- `/rig/density` (f 0..1)
- `/rig/grain` (f 0..1)
- `/rig/tightness` (f 0..1)
- `/rig/chaos` (f 0..1)
- `/rig/drift` (f 0..1)
- `/rig/space` (f 0..1)
- `/rig/color` (f 0..1)
- `/rig/vis_trim` (f 0..1)
- `/rig/vis_density_trim` (f 0..1)
- `/rig/global_trim` (f 0..1)

(Still supported for multi-arg senders:)
- `/rig/param` (s, f|i|s)

### Morph space (SHIFT bank)
- `/rig/morph/setA` (no args)
- `/rig/morph/setB` (no args)
- `/rig/morph/swap` (no args)
- `/rig/morph/commit` (no args)
- `/rig/morph/t` (f 0..1)
Optional direct set:
- `/rig/morph/a/<scene>` (no args)
- `/rig/morph/b/<scene>` (no args)

### Safety
- `/rig/panic` (no args or int) : if nonzero (or message received), load `panic`

## Outputs (from the bridge)
- `/rig/scene` (s) : current scene (or morph state label)
- `/rig/energy` (f) : smoothed energy
- `/rig/health/connected` (s, i) : per-destination status (best-effort)

Suggested extensions (later):
- `/rig/telemetry/rms` (f)
- `/rig/telemetry/onset` (i)
- `/rig/clock/bpm` (f)
