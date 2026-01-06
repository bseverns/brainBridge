# TouchDesigner: SB MorphSpace stub

Goal: listen to OSC from `sb-rig-bridge` (default: UDP **9001**) and expose `/rig/*` as CHOP channels.

## Build the COMP automatically

In TouchDesigner:

1. Open **Textport**.
2. Run (adjust the path):

```python
run('/ABS/PATH/TO/sb-rig-bridge-starter/touchdesigner/build_sb_morphspace_comp.py')
```

This creates `/project1/sb_morphspace` with an `oscin1` CHOP and an `OUT` null.

## Manual build (if you prefer)

1. Create a **baseCOMP** named `sb_morphspace`.
2. Inside it, create an **OSC In CHOP** (`oscin1`) and set **Port = 9001**.
3. Pipe it to a **Null CHOP** (`OUT`).
4. Optionally add a **Lag CHOP** for smoothing.

## Addresses you’ll see

Typical bridge outputs:
- `/rig/energy`, `/rig/density`, `/rig/chaos`, `/rig/drift` (floats 0..1)
- `/rig/morph/x`, `/rig/morph/y` (floats 0..1)
- `/rig/cue/<scene>` (no args)

## Test signal

From the repo root:

```bash
python tools/sb_probe.py --host 127.0.0.1 --port 9001 --addr /rig/energy --value 0.5
```
