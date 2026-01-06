# Samplebrain OSC setup + binding discovery

This is your **how-to wire Samplebrain into the house `/rig/*` universe**. The goal: figure out *what* OSC addresses Samplebrain listens to, then map those into `bindings/samplebrain.yaml` so the bridge can drive it.

Keep it punk-rock: **probe fast, listen hard, write down the addresses that actually move things.**

## What you need
- Samplebrain running.
- The OSC input port Samplebrain is listening on.
- The bridge running (optional, but nice to keep `/rig/*` messages in context).
- `tools/sb_probe.py` (included in this repo).

## Minimal walkthrough (discover + bind)

### 1) Turn on OSC in Samplebrain
Find Samplebrain’s OSC settings (usually in preferences/settings) and enable OSC **input**. Note the **host** and **port** it’s listening on.

> Example: `127.0.0.1:7771`

If Samplebrain has an OSC monitor/log window, open it. Watching incoming messages while you poke values is the fastest way to confirm you’ve got the right address and type.

### 2) Poke Samplebrain with `sb_probe.py`
Use the probe tool to send a single OSC message and watch Samplebrain react:

```bash
python tools/sb_probe.py --host 127.0.0.1 --port 7771 --addr /samplebrain/energy --value 0.6
```

Try a few candidate addresses (from Samplebrain docs, menus, or on-screen labels). If Samplebrain has an OSC monitor, it should show the address and type it received.

You can also send a **no-argument** message if the target is a trigger/toggle:

```bash
python tools/sb_probe.py --host 127.0.0.1 --port 7771 --addr /samplebrain/regen
```

### 3) Bind the addresses in `bindings/samplebrain.yaml`
Once you’ve found addresses that move real controls, drop them into the bindings file. This maps the bridge macros to Samplebrain’s OSC surface.

Example entries (replace with your real addresses):

```yaml
macros:
  energy: { address: "/samplebrain/energy", type: "f" }
  density: { address: "/samplebrain/density", type: "f" }
  grain: { address: "/samplebrain/grain", type: "f" }
  tightness: { address: "/samplebrain/tightness", type: "f" }
```

Tip: keep types honest. If Samplebrain expects an int or a trigger, use `type: "i"` or send no-arg messages as needed.

### 4) Run the bridge and verify
Start the bridge, then move your controller macros or send `/rig/*` messages. Samplebrain should respond.

If something doesn’t move:
- Re-check the Samplebrain OSC address (case and slashes matter).
- Confirm the port is correct.
- Use `sb_probe.py` to send directly again and watch the response.

## Extra: Samplebrain-side discovery
If Samplebrain can **emit** OSC when you touch a control, you can reverse-map:
1. Enable OSC output in Samplebrain.
2. Point it at an OSC monitor (e.g., a simple listener or any OSC logging tool).
3. Touch a control — note the address it emits.
4. Bind that address in `bindings/samplebrain.yaml`.

That’s it. Find the addresses, bind the macros, and let the bridge do the rest.
