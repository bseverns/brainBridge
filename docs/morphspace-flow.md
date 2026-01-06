# MorphSpace flow: PCR-30 → ReaLearn → sb-rig-bridge → TouchDesigner / Samplebrain

This is the *high-level loop* for the MorphSpace mode.

## Signal flow

1. **PCR-30** (MIDI controller)
2. **Reaper + ReaLearn**
   - maps MIDI → OSC
   - sends `/rig/*` to the bridge (UDP `9000`)
3. **sb-rig-bridge**
   - normalizes + slews values
   - forwards to:
     - TouchDesigner (UDP `9001`)
     - Samplebrain (UDP `9002`) *(only for addresses you bind in `bindings/samplebrain.yaml`)*

## Why this split works

- ReaLearn becomes the *human-facing* mapping layer (fast to rewire live).
- The bridge becomes the *behavior layer* (stable address space; smoothing; rate limiting).
- TouchDesigner + Samplebrain stay focused on what they do best.

## Minimal test

1. Start the bridge:

```bash
python -m sbrig.cli run --config config/ports.yaml
```

2. From ReaLearn, send `/rig/energy` and watch the bridge console log.
3. In TouchDesigner, set OSC In CHOP port to `9001` and confirm channels appear.

## When you’re ready for meaning

The MorphSpace values are meant to be *shared metaphors* across your stack:

- `energy` = *how hard the system breathes*
- `density` = *how packed the grain field is*
- `chaos` = *how willing it is to betray you*
- `drift` = *how quickly it forgets the center*
- `(x,y)` = *where you are in the field*

You can keep Samplebrain bound to only 2–4 of these, and let TouchDesigner eat the whole set.
