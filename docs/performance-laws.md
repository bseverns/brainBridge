# Performance Laws (Morph Space)

These are the "musical physics" that make the morph crossfader feel like an instrument,
not a parameter slider.

They live in the bridge, so **every downstream tool** (TouchDesigner, Samplebrain, Processing)
inherits the same behavior.

---

## Law 1 — Inertia (the crossfader has mass)

**Feel:** you push; it glides. Tiny hand jitter doesn't become strobing state.

**Tuning:** `morph.inertia_units_per_sec`

- 1.0–1.8: syrup / drone-friendly
- 2.0–3.0: expressive but stable (recommended)
- 4.0+: snappy, “DJ crossfader” energy

---

## Law 2 — Gravity + Snap (the space has landmarks)

**Feel:**
- near A, you *land* on A
- near B, you *land* on B
- the midpoint (0.5) can be its own resting place

**Gravity wells:** gentle pull toward anchor points.
**Snap:** if you get close enough, it locks with hysteresis so it doesn’t chatter.

Tuning:
- `well_strength` higher = more magnetic
- `well_radius` higher = wider magnet field
- `snap_threshold` higher = easier to lock
- `snap_hysteresis` higher = stays locked longer

---

## Law 3 — Fracture (controlled cracks, weighted per domain)

**Feel:** the morph stays smooth, but *selected parameters* briefly “grain-crack”
when you cross landmarks in the morph space.

By default, fractures trigger when `t_applied` crosses:
- 0.25, 0.5, 0.75 (configurable)

Cracks are **weighted** separately for:
- **Audio** (Samplebrain semantic keys)
- **Visual** (TouchDesigner OSC addresses)
- **Processing** (optional, often visual/logic)

That means: you can push the same gesture toward *sound tearing* or *image tearing*,
with SHIFTable weights.

### Live OSC controls (ReaLearn-friendly)
- `/rig/fracture/enable` (int or no-arg toggle)
- `/rig/fracture/amount` (f 0..1)
- `/rig/fracture/w_audio` (f 0..1)
- `/rig/fracture/w_visual` (f 0..1)
- `/rig/fracture/w_processing` (f 0..1)
- `/rig/fracture/balance` (f 0..1) convenience: 0=audio, 1=visual

Telemetry (for TouchDesigner UI):
- `/rig/fracture/env` (f 0..1)
- `/rig/fracture/w_audio`, `/rig/fracture/w_visual`, `/rig/fracture/w_processing`

---

## Where to tune (config)

```yaml
morph:
  curve: smoothstep
  inertia_units_per_sec: 2.0
  apply_hz: 45
  wells_enabled: true
  well_points: [0.0, 0.5, 1.0]
  well_radius: 0.12
  well_strength: 0.35
  snap_enabled: true
  snap_points: [0.0, 0.5, 1.0]
  snap_threshold: 0.05
  snap_hysteresis: 0.03

fracture:
  enabled: true
  thresholds: [0.25, 0.5, 0.75]
  decay_sec: 0.18
  amount: 0.35
  rate_hz: 18
  samplebrain_keys: ["grain", "chaos", "tightness", "density"]
  touchdesigner_addrs: ["/rig/energy", "/rig/vis_trim", "/rig/vis_density_trim"]
  processing_addrs: ["/rig/mode"]
```

---

## Practical performance ritual
1) Pick A (cue → setA)
2) Pick B (cue → setB)
3) Ride t; inertia does the cleanup
4) Cross landmarks to spark fractures
5) SHIFT-weight the cracks toward sound or image
6) Commit when you find a beautiful in-between
