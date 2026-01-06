# TouchDesigner: PCR-30 → OSC (Bridge Control)

This folder documents a minimal TouchDesigner patch that turns **PCR-30 MIDI** into the
bridge's **/rig/** OSC messages, with a simple sanity-check workflow so you always know
S7/S8/B1 are really what you think they are.

This assumes **single-machine** operation.

## Ports (single machine)
- Bridge listens: `127.0.0.1:9000`
- TouchDesigner sends to: `127.0.0.1:9000`
- TouchDesigner receives telemetry on: `127.0.0.1:9001`
- Bridge sends to TouchDesigner (dest `touchdesigner`): `127.0.0.1:9001`

## The mapping you asked for
- **Slider 7 (S7)** → `/rig/fracture/amount` (float 0..1)
- **Slider 8 (S8)** → `/rig/fracture/balance` (float 0..1)  
  (`0 = audio cracks`, `1 = visual cracks`)
- **Button 1 (B1)** → `/rig/fracture/enable` (int 0/1 or toggle)

## Network (CHOP chain)
A minimal chain:

1) **MIDI In CHOP**
2) **Select CHOP** (keep only S7, S8, B1 channels)
3) **Math CHOP** (scale 0..127 → 0..1 for sliders)
4) **Lag CHOP** (optional smoothing: ~0.02–0.06s)
5) **Logic CHOP** (button only; optional toggle)
6) **Rename CHOP** (rename channels to OSC addresses)
7) **OSC Out CHOP** (send to `127.0.0.1:9000`)

## Sanity check (fast, repeatable)
Your goal is to identify which MIDI channels/CCs correspond to S7, S8, and B1 **on this day**.

### A) Verify inside TouchDesigner
1. Drop a **MIDI In CHOP** and select the PCR-30 device.
2. Open the CHOP viewer so you can see channels updating.
3. Move **only S7** (leave everything else still).
4. Look for the channel that changes smoothly as you move S7. Note its name.
5. Repeat for **S8**.
6. Press **B1**. Note which channel spikes / toggles.

Tip: if your PCR-30 has been re-assigned, S7/S8 might not be CC7/CC8. That’s fine — TD doesn’t care.
You only need to *identify the correct channels* and then Select/Rename them.

### B) Verify what TD is sending (without the bridge)
Run this in a terminal from the repo:

```bash
source .venv/bin/activate
python tools/osc_sniff.py --port 9000
```

Now enable your **OSC Out CHOP**.
Move S7/S8/B1 and confirm you see:

- `/rig/fracture/amount <value>`
- `/rig/fracture/balance <value>`
- `/rig/fracture/enable <value>`

If the addresses are correct but values look wrong:
- sliders should be floats 0..1 (fix Math CHOP)
- button can be 0/1 or 0/127 (Logic CHOP can normalize)

### C) Verify telemetry (bridge → TD)
1) Start the bridge:
```bash
python run_bridge.py --config config/ports.yaml
```

2) In TouchDesigner, add **OSC In CHOP** listening on `9001`.

You should see things like:
- `/rig/morph/t_applied`
- `/rig/fracture/env`
- `/rig/fracture/w_audio`, `/rig/fracture/w_visual`

If you don’t see telemetry:
- confirm `config/ports.yaml` has TouchDesigner destination set to port `9001`
- confirm your OSC In CHOP port matches

## Suggested “feel” defaults
- Fracture amount: 0.15–0.35 is usually plenty
- Balance: treat it like “mix” between sound-tear and image-tear
- Button: toggle fracture on/off so you can “arm” the behavior between sections
