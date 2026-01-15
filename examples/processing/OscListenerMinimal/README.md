# OscListenerMinimal (Processing)

A tiny, loud-and-clear Processing sketch for **receiving `/rig/*` OSC** during bridge
bring-up. Think of it as your **visual stethoscope**: it doesn’t make art, it tells
you the signals are alive.

## What this sketch is for
- **Sanity check** that the bridge is sending OSC to the Processing destination.
- **Learn your port wiring** (who listens where) before you build fancy visuals.
- **Debug** address formats and argument types without guessing.

## Quickstart (the short version)
1) Install the Processing libraries:
   - **oscP5**
   - **netP5**

2) Open `OscListenerMinimal.pde` in Processing.

3) Make sure the sketch is listening on the same port the bridge targets.
   - Default in this repo: `9003` (see `config/ports.yaml`).

4) Run the sketch, then send something like:

```bash
python tools/sb_probe.py --host 127.0.0.1 --port 9000 --addr /rig/energy --value 0.5
```

If you see messages arriving in Processing, your pipeline is alive.

## Port wiring (single machine default)
- **Bridge listens on:** `127.0.0.1:9000`
- **Processing destination (bridge → Processing):** `127.0.0.1:9003`

Check and update `config/ports.yaml` if you’re on a different port or a
multi‑machine setup.

## What to look for in the console
You should see incoming messages like:
- `/rig/energy 0.5`
- `/rig/scene steel`
- `/rig/morph/t_applied 0.42`

If you’re seeing nothing:
- verify the bridge is running
- verify the **Processing destination is enabled** in `config/ports.yaml`
- confirm the port matches the Processing listener

## Next steps (make it useful)
- Map a few `/rig/*` addresses to visual behaviors (color, speed, mode, density).
- Start with **one parameter per system** so you can feel the bridge’s smoothing.
- Then graduate to scenes + morphs when your eyes trust the data.

This sketch is intentionally minimal. The goal is signal truth, not a full demo.
