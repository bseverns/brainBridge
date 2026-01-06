# Samplebrain OSC Discovery & Binding

Samplebrain can listen on OSC ports (and in some builds can emit OSC, too). The exact message surface may change
between versions, and it is not always fully documented.

This repo keeps Samplebrain behind an adapter:

- you keep your rig stable (`/rig/*`)
- you bind the subset of Samplebrain controls you care about in `bindings/samplebrain.yaml`
- everything else stays optional

---

## 1) Confirm ports + connectivity

In Samplebrain:
- set **OSC input port** to match the `samplebrain` destination in `config/ports.yaml`
- (optional) set **OSC output port** to a port where you run a sniffer (below)

In this repo:
```bash
python run_bridge.py --config config/ports.yaml
```

You should see health pings echoed to any enabled destinations (TouchDesigner/Processing/etc).

---

## 2) If Samplebrain emits OSC: sniff it

If Samplebrain can send OSC while you move sliders/press UI buttons:

```bash
python tools/osc_sniff.py --port 9002
```

Then in Samplebrain, set its OSC output port to `9002` and wiggle a control.
You’ll see addresses scroll by.

---

## 3) If Samplebrain does NOT emit OSC: extract candidates from the app

Even if Samplebrain only *receives* OSC, the OSC address strings often live inside the executable.

### macOS (app bundle)
```bash
python tools/sb_strings.py \
  --binary "/Applications/Samplebrain.app/Contents/MacOS/samplebrain" \
  --filter "/"
```

### Windows / Linux
Point `--binary` at the Samplebrain executable.

This prints likely OSC-ish strings (deduped). Use them as candidates to probe.

---

## 4) Probe candidates (one at a time)

Once you have a candidate address, try sending to it:

```bash
python tools/sb_probe.py --host 127.0.0.1 --port 9000 --addr "/some/address" --value 0.5
```

Or probe *through the bridge* using semantic controls:

```bash
python tools/sb_probe.py --host 127.0.0.1 --port 9000 --macro chaos --macro-value 0.3
```

---

## 5) Bind the ones you like

Edit `bindings/samplebrain.yaml` and set addresses for the semantic keys you want.
Example:

```yaml
macros:
  energy:
    address: "/samplebrain/whatever_energy_is_called"
    type: f
  chaos:
    address: "/samplebrain/whatever_chaos_is_called"
    type: f
```

Restart the bridge. Now `/rig/energy` and `/rig/chaos` will forward into Samplebrain (if enabled in config).
