# ReaLearn + PCR-30: MorphSpace mapping (bridge-first)

This is the “get sound + light talking” setup: **PCR-30 → ReaLearn → sb-rig-bridge → TouchDesigner/Samplebrain**.

The PCR-30 is your hands; ReaLearn is your router; the bridge is your translator.

## 0) Prereqs

- Reaper + Helgobox/ReaLearn installed.
- `sb-rig-bridge` running (see repo `README.md`).
- The PCR-30 visible as a MIDI input in Reaper.

## 1) Create the OSC device in ReaLearn

In ReaLearn’s **Input/Output** section, click **Manage OSC devices** and create one device:

- Name: `SB Bridge (in)`
- Local port: `9100`  (any free port is fine)
- Device address (IP): `127.0.0.1`  *(or the Audio Brain IP if two-computer)*
- Device port: `9000`  *(this is the bridge listen port)*

This gives ReaLearn a destination for the target **OSC: Send message**.

## 2) Put ReaLearn on a dedicated “control bus” track

In Reaper:

1. Create a track called `SB CONTROL`.
2. Insert **ReaLearn** as an FX.
3. Set the track input to **PCR-30 → All channels**.
4. Monitor input (so ReaLearn sees live MIDI).

## 3) Make the core MorphSpace mappings

For each mapping:

- Touch the PCR-30 control (Learn the source).
- Set **Target category** to `OSC`.
- Choose **Target**: `OSC: Send message`.
- Set the **OSC address**.
- If it’s continuous, set **Argument number = 1** (so the incoming value becomes the argument). ReaLearn supports up to one argument. (See target docs.)

Suggested starting layout:

### Morph travel (continuous)

- Knob 1 → `/rig/morph/t` (arg 1)
- Knob 2 → *(optional)* map to another macro (e.g. `/rig/density`, `/rig/drift`, or `/rig/space`)

`/rig/morph/t` is the current MorphSpace “slider” between scene A and scene B. Think of it as
one, deliberate musical lever rather than a 2D pad: **0 = fully A, 1 = fully B**. If you want
to keep two knobs dedicated to MorphSpace, use Knob 2 as a second “performance axis” (like
energy or chaos) so the morph has attitude, not just position.

### Macro “energy/chaos” (continuous)

- Slider 1 → `/rig/energy` (arg 1)
- Slider 2 → `/rig/chaos`  (arg 1)

### Optional macro trims (continuous)

- Slider 3 → `/rig/density` (arg 1)
- Slider 4 → `/rig/drift`   (arg 1)
- Knob 3   → `/rig/space`   (arg 1)
- Knob 4   → `/rig/color`   (arg 1)

### Cues (address-only)

For cue triggers, **leave Argument number blank** so it sends a pure address.

- Button 1 → `/rig/cue/a`
- Button 2 → `/rig/cue/b`
- Button 3 → `/rig/cue/c`
- Button 4 → `/rig/cue/d`

(Scenes are arbitrary; use whatever naming feels right.)

## 4) Glue that makes it feel like an instrument

In each mapping’s **Glue** section, set:

- Mode: Absolute
- Value range: 0..1
- Optional: add a small deadzone for sliders if they’re jittery.

Also consider enabling logging while you’re wiring:
- In the ReaLearn menu bar: enable **Log real control messages** and **Log real feedback messages**.

## 5) Verify end-to-end

Use the probe tool to verify the bridge is receiving:

```bash
python tools/sb_probe.py --host 127.0.0.1 --port 9000 --addr /rig/energy --value 0.5
```

Then verify TouchDesigner sees it (listening on 9001).

---

If you want, the next refinement is a *banked morph space*: one button flips what the knobs mean (e.g. X/Y vs. Density/Drift) without touching your hands’ muscle memory.
