# Brain Bridge

A starter repo for a **performance-grade OSC bridge** that:

- receives a **stable "house" OSC API** (`/rig/*`)
- forwards to **TouchDesigner**, **Samplebrain**, and **Processing**
- supports **scenes**, **macro smoothing (slew)**, and a **Morph Space** (SHIFT bank)

The idea: your controllers + DAW only ever learn one language (`/rig/*`).
Everything else becomes swappable.

---

## Quickstart

### 1) Install deps (venv)
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2) Configure ports
Edit:
- `config/ports.yaml` (single computer)
- or `config/ports.two-computer.audio.yaml` (two machines)

### 3) Run the bridge
```bash
python run_bridge.py --config config/ports.yaml
```

Now send OSC to the bridge at:
- `listen.host:listen.port` (default `0.0.0.0:9000`)

---

## The house API (`/rig/*`)

This repo is designed to work well with ReaLearn’s OSC sender constraint:
ReaLearn’s **OSC: Send message** can send **address-only** messages or messages with **one argument**.

That’s why this API is built around:

- cues like `/rig/cue/embers` (no args)
- macro controls like `/rig/energy 0.42` (one float)

See:
- `docs/osc-address-space.md`
- `docs/realearn-morph-bank.md`
- `docs/pcr-30-layout.md`

---

## Samplebrain integration (optional)

Samplebrain binding is intentionally *opt-in*.

1) Enable the `samplebrain` destination in your chosen config file.
2) Set Samplebrain’s OSC input port to match that destination.
3) Bind whichever Samplebrain controls you care about in:
   - `bindings/samplebrain.yaml`

Discovery helper:
- `docs/samplebrain-discovery.md`

---

## Two-computer layout

See `docs/two-computer-layout.md`.

---

## License

MIT (see `LICENSE`).

## MorphSpace mode

See `docs/morphspace-flow.md` and `realearn/README.md` for a practical PCR-30 → ReaLearn mapping plan.
