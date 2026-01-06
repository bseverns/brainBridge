# Two-computer layout (recommended)

Keep audio stable and visuals hungry, with only OSC crossing the wire.

## Roles

**Audio Brain (Computer A)**
- REAPER (+ ReaLearn)
- Samplebrain
- sb-rig-bridge (this repo)
- MIDI controllers
- Audio interface + monitoring

**Light Brain (Computer B)**
- TouchDesigner (listens to `/rig/*`)
- Projector / display outputs

## Ports (suggested)
- Bridge listens: 9000 (Audio Brain)
- TouchDesigner listens: 9001 (Light Brain)
- Samplebrain listens: 9002 (Audio Brain)
- Processing listens: 9003 (optional)

## Run
On Audio Brain:
```bash
python run_bridge.py --config config/ports.two-computer.audio.yaml
```

Test:
```bash
python tools/sb_probe.py --host 127.0.0.1 --port 9000 --cue embers
python tools/sb_probe.py --host 127.0.0.1 --port 9000 --energy 0.6
```
