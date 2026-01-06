# PCR-30 CC plan (optional hardware programming)

If you want the PCR-30 to behave the same on every machine/DAW, program a dedicated controller memory
(e.g. "SB RIG") so the CC numbers are stable.

Suggested CC numbers (Channel 1):
- R1–R8: CC20–CC27
- S1–S8: CC30–CC37
- Buttons as CC (toggle/momentary):
  - B1–B6: CC40–CC45
  - L1–L3: CC46–CC48
- P1: CC64 (sustain style) or CC50 (if you want it separate)
- P2: CC11 (expression) or CC51

You can program this from the front panel (EDIT -> touch control -> choose CONTROL CHANGE -> set CC).
See Roland's "Assigning Controllers" notes for the PCR series.

In ReaLearn:
- Map CC20 -> `/rig/energy` (float 0..1)
- Map CC21.. etc -> `/rig/param ("density", value)` etc
