# PCR-30 → TouchDesigner → Bridge (S7 / S8 / B1)

A tiny control surface that makes the Morph Space breathe and break.

## Controls
- **S7**: `/rig/fracture/amount` — how much the crack exists (0..1)
- **S8**: `/rig/fracture/balance` — 0 = mostly audio crack; 1 = mostly visual crack
- **B1**: `/rig/fracture/enable` — toggle fracture on/off

## Why this works
The bridge treats morphing as a smooth continuum (inertia + gravity/snap),
then fracture adds brief, controlled “grain cracks” when you cross landmarks.

You’re not animating chaos everywhere;
you’re deciding **how much** and **where it lands**.

See:
- `docs/performance-laws.md` (Law 3: Fracture)
- `touchdesigner/README.md` (how to patch + sanity check)
