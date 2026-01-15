# Operator Checklist (Showtime Runbook)

One-page checklist for a live run. Keep it nearby.

## 1) Start the bridge

Pick the right ports config, then start:

```bash
python run_bridge.py --config config/ports.yaml
```

If you use a two-computer setup, use the matching config under `config/`.

## 2) Verify ports and destinations

Open `config/ports.yaml` and confirm:
- `listen_host` and `listen_port` match your controller output.
- Destinations (TouchDesigner, Samplebrain, Processing) are correct and enabled.

## 3) Sniff OSC traffic (sanity check)

Listen on the bridge input port to confirm incoming messages:

```bash
python tools/osc_sniff.py --port 9000
```

If you can, also listen on destination ports to confirm outgoing OSC.

## 4) Set a scene, then set morph A/B

```bash
# Load a scene
python tools/sb_probe.py --host 127.0.0.1 --port 9000 --cue embers

# Set morph endpoints from last loaded scene
python tools/sb_probe.py --host 127.0.0.1 --port 9000 --addr /rig/morph/setA
python tools/sb_probe.py --host 127.0.0.1 --port 9000 --addr /rig/morph/setB
```

You can also set endpoints directly:

```bash
python tools/sb_probe.py --host 127.0.0.1 --port 9000 --addr /rig/morph/a/embers
python tools/sb_probe.py --host 127.0.0.1 --port 9000 --addr /rig/morph/b/steel
```

## 5) Test morph

```bash
python tools/sb_probe.py --host 127.0.0.1 --port 9000 --addr /rig/morph/t --value 0.0
python tools/sb_probe.py --host 127.0.0.1 --port 9000 --addr /rig/morph/t --value 1.0
```

## 6) Test fracture

```bash
python tools/sb_probe.py --host 127.0.0.1 --port 9000 --addr /rig/fracture/enable --value 1
python tools/sb_probe.py --host 127.0.0.1 --port 9000 --addr /rig/fracture/amount --value 0.4
python tools/sb_probe.py --host 127.0.0.1 --port 9000 --addr /rig/fracture/balance --value 0.7
```

## 7) Panic safety

```bash
python tools/sb_probe.py --host 127.0.0.1 --port 9000 --panic
```
