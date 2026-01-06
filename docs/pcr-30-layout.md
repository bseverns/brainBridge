# PCR-30 as the main hands (Performance Bank + Morph Space)

This plan assumes:
- Bridge on Audio Brain listening at `127.0.0.1:9000`
- ReaLearn sends OSC into the bridge using target **OSC: Send message** (up to one argument)
- The bridge fans out to TouchDesigner + Samplebrain

## Control inventory (PCR-30 / PCR series)
- R1–R8 = 8 knobs
- S1–S8 = 8 sliders
- B1–B6 + L1–L3 = 9 buttons
- P1/P2 = 2 pedal inputs

---

## Bank A (default): Play the show

### Knobs (R1–R8) — 8 macro intentions (single-float OSC)
R1  -> `/rig/energy`
R2  -> `/rig/density`
R3  -> `/rig/grain`
R4  -> `/rig/tightness`
R5  -> `/rig/chaos`
R6  -> `/rig/drift`
R7  -> `/rig/space`
R8  -> `/rig/color`

### Sliders (S1–S8) — trims & mixes
Keep these inside REAPER unless you explicitly want visuals to follow them.
S1  -> Samplebrain wet/dry (REAPER)
S2  -> Samplebrain send level (REAPER)
S3  -> `/rig/vis_trim` (optional)
S4  -> `/rig/vis_density_trim` (optional)
S5  -> FX send A (REAPER)
S6  -> FX send B (REAPER)
S7  -> Master headroom trim (REAPER)
S8  -> `/rig/global_trim` (optional)

### Buttons (B1–B6 + L1–L3) — cues + safety
B1 -> `/rig/cue/embers`
B2 -> `/rig/cue/steel`
B3 -> `/rig/cue/flood`
B4 -> `/rig/cue/stutter`
B5 -> (free) freeze/toggle if you implement it
B6 -> `/rig/panic`

L3 -> SHIFT (hold)  -> activates Morph Space group in ReaLearn

---

## Morph Space (hold SHIFT): crossfade between two scenes

### Buttons (set endpoints)
SHIFT+B1 -> `/rig/morph/setA`   (store current scene as A)
SHIFT+B2 -> `/rig/morph/setB`   (store current scene as B)
SHIFT+B3 -> `/rig/morph/swap`   (swap A and B)
SHIFT+B4 -> `/rig/morph/commit` (commit current morph into A; reset t)

### Knob
SHIFT+R1 -> `/rig/morph/t` (0..1)

Workflow:
1) Hit a cue (embers) -> SHIFT+B1
2) Hit a cue (steel)  -> SHIFT+B2
3) Hold SHIFT, ride R1 as your crossfader between the worlds

See `docs/realearn-morph-bank.md`.


---

## TouchDesigner mapping (single-machine alternative)
If you prefer TouchDesigner as your MIDI→OSC mapper (instead of ReaLearn), see:
- `touchdesigner/README.md`
- `docs/pcr-30-td-fracture-map.md`
