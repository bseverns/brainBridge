# ReaLearn "Morph Space" (SHIFT bank)

Morph Space turns two cues into a playable continuum.

## Core (SHIFT held)
Buttons:
- B1 -> `/rig/morph/setA`
- B2 -> `/rig/morph/setB`
- B3 -> `/rig/morph/swap`
- B4 -> `/rig/morph/commit`
- B6 -> `/rig/panic`

Continuous:
- R1 -> `/rig/morph/t` (0..1)

## Fracture (SHIFT held, "shiftable weights")
- R2 -> `/rig/fracture/amount` (0..1)
- R3 -> `/rig/fracture/balance` (0..1)  **0 = audio cracks, 1 = visual cracks**
Optional (if you want independent weights):
- R4 -> `/rig/fracture/w_audio`
- R5 -> `/rig/fracture/w_visual`
- R6 -> `/rig/fracture/w_processing`
Button:
- B5 -> `/rig/fracture/enable`

Telemetry you can visualize in TouchDesigner:
- `/rig/morph/t_target`, `/rig/morph/t_raw`, `/rig/morph/t_applied`
- `/rig/fracture/env`, `/rig/fracture/w_audio`, `/rig/fracture/w_visual`
