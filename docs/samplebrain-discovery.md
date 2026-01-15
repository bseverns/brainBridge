# Samplebrain Binding Discovery Guide

`bindings/samplebrain.yaml` ships with `null` addresses so you can fill in the
real Samplebrain OSC surface for your rig. This guide shows how to discover
addresses, confirm types, and bind them.

Related files:
- `bindings/samplebrain.yaml`
- `sbrig/bindings.py` (supported types: `f`, `i`, `s`)
- `tools/osc_sniff.py`
- `tools/sb_probe.py`

## 1) Find Samplebrain OSC input settings

In Samplebrain, enable OSC input and note the host/port it is listening on.
Example: `127.0.0.1:7771`.

If Samplebrain has an OSC monitor window, open it. It is the fastest way to
confirm addresses and types.

## 2) Discover addresses (two fast paths)

### A) If Samplebrain can emit OSC
1. Enable OSC output in Samplebrain.
2. Point it to a local listener:

```bash
python tools/osc_sniff.py --port 9002
```

3. Touch controls in Samplebrain and note the addresses that appear.

### B) If Samplebrain only receives OSC
Probe likely addresses until you see the UI move:

```bash
python tools/sb_probe.py --host 127.0.0.1 --port 7771 --addr /samplebrain/energy --value 0.6
python tools/sb_probe.py --host 127.0.0.1 --port 7771 --addr /samplebrain/regen
```

Notes:
- If a control expects a float, use a decimal value (0.0 to 1.0 is common).
- For toggles or triggers, send a no-arg message by omitting `--value`.

## 3) Determine the OSC argument type

Bindings support three types:
- `f` float
- `i` int
- `s` string

If Samplebrain reports the type in its OSC monitor, use that. Otherwise, test
with `sb_probe.py` using different values and see what sticks.

## 4) Fill in bindings/samplebrain.yaml

Map each macro or param name to the discovered address and type.

```yaml
macros:
  energy: { address: "/samplebrain/energy", type: "f" }
  density: { address: "/samplebrain/density", type: "f" }
  chaos: { address: "/samplebrain/chaos", type: "f" }

params:
  regen: { address: "/samplebrain/regen", type: "i" }
```

Tips:
- Leave unknown entries as `null` so the bridge ignores them safely.
- Match keys to scene files under `samplebrain:` (see `docs/scenes.md`).

## 5) Verify end-to-end

1. Start the bridge.
2. Send a macro value into the bridge:

```bash
python tools/sb_probe.py --host 127.0.0.1 --port 9000 --addr /rig/energy --value 0.35
```

3. Samplebrain should respond. If not, re-check the address, port, and type.
