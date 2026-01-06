# ReaLearn workflow notes (why we keep it simple)

ReaLearn is extremely capable, but its **import/export formats** and controller definitions evolve quickly.

This repo therefore takes a pragmatic approach:

- Use ReaLearn’s *native* Learn workflow to capture the **PCR-30 sources**.
- Standardize on a stable, human-readable **house OSC API** (`/rig/*`).
- Let the bridge do routing + safety (rate limiting, slew smoothing, fan-out).

## Useful ReaLearn menu items

In ReaLearn’s menu bar:

- **Logging → Log real control messages** (confirm your PCR-30 is coming in)
- **Logging → Log real feedback messages** (confirm OSC is leaving)

## A nice “first hour” checklist

1. Create the OSC device `SB Bridge` (IP + port 9000).
2. Make 2 mappings:
   - Knob 1 → `/rig/morph/x` (arg #1)
   - Knob 2 → `/rig/morph/y` (arg #1)
3. Confirm TouchDesigner sees those updates.
4. Only then add the rest.

When things get weird: reduce complexity.

- One mapping.
- One address.
- One machine.

Then add layers back.
