# REAPER + ReaLearn Setup (PCR-30 → Bridge over OSC)

Goal: REAPER is the "score" and controller hub. ReaLearn turns MIDI into OSC and sends it to the bridge.

## Why this setup works well
ReaLearn’s `OSC: Send message` target can send OSC with **up to one argument**.  
So, for ReaLearn, we use *single-argument (or zero-argument)* OSC addresses like:

- `/rig/energy <0..1>`
- `/rig/density <0..1>`
- `/rig/chaos <0..1>`
- `/rig/cue/embers` (no args)
- `/rig/panic` (no args)

## 1) Create the sender track
1) Create a track named **SHOW CONTROL**.
2) Add **ReaLearn** to it.

## 2) Add an OSC output device in ReaLearn
In ReaLearn’s **Input/Output** section:
- Create/select an OSC device named `Bridge`
- Host: `127.0.0.1` (if bridge is on the same machine) or the Audio Brain’s IP
- Port: `9000`

If anything downstream struggles with OSC bundles, disable bundling in ReaLearn’s OSC output settings.

Tip: ReaLearn can log outgoing OSC messages via its menu bar for debugging.

## 3) First “prove it works” mapping (do this before building 30 mappings)
Map **R1** to send:
- Target: `OSC: Send message`
- Device: `Bridge`
- Address: `/rig/energy`
- Argument: 1 (send the incoming absolute control value as the argument)

Then map **B6** to:
- Address: `/rig/panic`
- Argument: (none)

Once you see the rig respond, continue.

## 4) Performance bank mappings (Bank A)
Knobs:
- R1 `/rig/energy`
- R2 `/rig/density`
- R3 `/rig/grain`
- R4 `/rig/tightness`
- R5 `/rig/chaos`
- R6 `/rig/drift`
- R7 `/rig/space`
- R8 `/rig/color`

Buttons:
- B1 `/rig/cue/embers`
- B2 `/rig/cue/steel`
- B3 `/rig/cue/flood`
- B4 `/rig/cue/stutter`
- B5 `/rig/freeze/toggle`
- B6 `/rig/panic`

(You can keep S1/S2/etc inside REAPER as track/send mappings, without involving the bridge.)

## 5) Shift bank (optional, later)
If you want a Shift layer:
- Use a ReaLearn parameter as your SHIFT flag (0/1).
- Map L3 to set that flag while held.
- Use conditional activation so Shift-only mappings are active only when the flag is on.
