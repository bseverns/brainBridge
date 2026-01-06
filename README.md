# sb-rig-bridge-starter

A starter repo for a **performance-grade OSC bridge** that:
- receives a stable house OSC API (`/rig/*`)
- forwards to TouchDesigner, Samplebrain, and Processing
- supports scenes + macro smoothing (slew)
- includes a **Morph Space** (SHIFT bank) with musical physics

## Morph Space: three laws
1) **Inertia** — your hand becomes glide, not jitter  
2) **Gravity + Snap** — landmarks you can land on (A / midpoint / B)  
3) **Fracture** — controlled “grain cracks” that you can weight toward **audio** or **visuals**

Tune the laws in `config/*.yaml` (`morph:` and `fracture:`).  
Map SHIFT controls via ReaLearn using `docs/realearn-morph-bank.md`.

## Quickstart
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run_bridge.py --config config/ports.two-computer.audio.yaml
```

## Docs
- `docs/pcr-30-layout.md`
- `docs/realearn-morph-bank.md`
- `docs/performance-laws.md`
- `docs/osc-address-space.md`
- `docs/samplebrain-setup.md`

## TouchDesigner MIDI→OSC (single machine)
If you’re using TouchDesigner as the controller mapper (PCR-30 → OSC), start here:
- `touchdesigner/README.md`

A ready mapping for **S7/S8/B1 → Fracture** is documented in `docs/pcr-30-td-fracture-map.md`.
