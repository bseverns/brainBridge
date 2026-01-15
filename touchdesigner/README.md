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

---

## Patch Blueprint (concrete node plan)
Goal: one small network that handles **control**, **telemetry**, and **scene cues**.

### 1) MIDI -> OSC (controls)
Create these CHOPs in order (names suggested):
1. `midi_in` (MIDI In CHOP)
   - Device: PCR-30
2. `select_pcr` (Select CHOP)
   - Channels: the three you confirmed for S7, S8, B1
3. `math_scale` (Math CHOP)
   - From Range: 0..127
   - To Range: 0..1
4. `lag_smooth` (Lag CHOP)
   - Lag: 0.02..0.06
5. `logic_toggle` (Logic CHOP) **for B1 only**
   - Convert Input: On/Off
   - Combine Channels: By Channel
   - Toggle: On
6. `rename_osc` (Rename CHOP)
   - Rename to:
     - `/rig/fracture/amount`
     - `/rig/fracture/balance`
     - `/rig/fracture/enable`
7. `osc_out` (OSC Out CHOP)
   - Network Address: `127.0.0.1`
   - Port: `9000`

Tip: If you want more macros, add channels in `select_pcr`, map to `/rig/energy`,
`/rig/density`, etc., and keep the rest of the chain the same.

### 2) Telemetry (bridge -> TD)
Add these CHOPs:
1. `osc_in` (OSC In CHOP)
   - Port: `9001`
2. `select_telemetry` (Select CHOP)
   - Channels to keep:
     - `/rig/health/connected`
     - `/rig/morph/t_applied`
     - `/rig/morph/snapped`
     - `/rig/fracture/env`
     - `/rig/fracture/enabled`

Drive simple UI widgets (Value Ladder / LED / Slider) from `select_telemetry`
so you can see the bridge state at a glance.

### 3) Scene + morph controls (OSC Out DAT)
Use a single OSC Out DAT for discrete messages:
1. `osc_out_dat` (OSC Out DAT)
   - Network Address: `127.0.0.1`
   - Port: `9000`
2. Add Buttons with these messages:
   - `/rig/morph/setA`
   - `/rig/morph/setB`
   - `/rig/morph/swap`
   - `/rig/morph/commit`
3. Add a Text Field + Button for scene cues:
   - Message: `/rig/cue`
   - Argument: scene name (e.g. `embers`, `steel`, `panic`)

### 4) Optional safety gate
Add a single `arm` Toggle that multiplies/gates outgoing CHOP values:
1. `arm` (Constant CHOP, value 0 or 1)
2. `gate` (Math CHOP) after `lag_smooth`
   - Combine: Multiply with `arm`
This lets you rehearse without sending OSC.

---

## Macro Mapping Table (suggested)
Use this to expand `select_pcr` and `rename_osc` beyond S7/S8/B1.
These are **0..1 floats** unless noted.

| Control | OSC Address | Notes |
| --- | --- | --- |
| S1 | `/rig/energy` | Overall drive |
| S2 | `/rig/density` | Event density |
| S3 | `/rig/grain` | Grain size / granularity |
| S4 | `/rig/tightness` | Rhythmic lock |
| S5 | `/rig/chaos` | Controlled disorder |
| S6 | `/rig/drift` | Slow motion / sway |
| S7 | `/rig/fracture/amount` | Fracture depth |
| S8 | `/rig/fracture/balance` | 0 = audio, 1 = visual |
| K1 | `/rig/space` | Spatial spread |
| K2 | `/rig/color` | Visual hue / tint |
| K3 | `/rig/vis_trim` | Visual gain trim |
| K4 | `/rig/vis_density_trim` | Visual density trim |
| K5 | `/rig/global_trim` | Global trim |
| B1 | `/rig/fracture/enable` | Toggle (0/1) |

If your PCR-30 control names differ, just rename channels to match the addresses.
