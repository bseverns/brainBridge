# ReaLearn "Morph Space" (SHIFT bank)

ReaLearn's target **OSC: Send message** can send OSC messages with **up to one argument**.  
So: in Morph Space we use **address-only triggers** and **single-float controls**.  
(See official docs for the one-argument limit.) 

## Concept
- You keep two remembered scenes: **A** and **B**
- A single control (**morph_t**) crossfades between them
- You can "snapshot" the current moment back into A (commit), so the morph becomes a path you can keep walking

## OSC addresses used

### Set / manage morph endpoints (buttons)
- `/rig/morph/setA` (no args) : store current scene as A
- `/rig/morph/setB` (no args) : store current scene as B
- `/rig/morph/swap` (no args) : swap A and B
- `/rig/morph/commit` (no args) : commit current morph position into A and reset morph_t to 0

Optional (direct set by name):
- `/rig/morph/a/<scene>` (no args)
- `/rig/morph/b/<scene>` (no args)

### Drive the morph (knob/pedal)
- `/rig/morph/t` (float 0..1)

### Safety
- `/rig/panic` (no args)

---

## Suggested PCR-30 mapping in ReaLearn

### SHIFT button
Use L3 as SHIFT. In ReaLearn, put morph mappings into their own group and set its activation condition
based on a ReaLearn parameter or modifier controlled by L3.

### Bank A (no shift): your normal macros + cues
- R1..R8 -> `/rig/energy`, `/rig/density`, `/rig/grain`, `/rig/tightness`, `/rig/chaos`, `/rig/drift`, `/rig/space`, `/rig/color`
- B1..B4 -> `/rig/cue/embers`, `/rig/cue/steel`, `/rig/cue/flood`, `/rig/cue/stutter`
- B6 -> `/rig/panic`

### Morph Space (while holding SHIFT)
- R1 -> `/rig/morph/t` (0..1)
- B1 -> `/rig/morph/setA`
- B2 -> `/rig/morph/setB`
- B3 -> `/rig/morph/swap`
- B4 -> `/rig/morph/commit`
- B6 -> `/rig/panic`

Workflow:
1) Tap a cue (e.g. embers)
2) SHIFT+B1 (setA)
3) Tap another cue (e.g. steel)
4) SHIFT+B2 (setB)
5) SHIFT+R1 becomes your morph crossfader

Tip:
- Map P2 expression pedal to `/rig/morph/t` if you want your hands free for other macros.
