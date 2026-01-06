# Samplebrain OSC Discovery & Binding

Samplebrain supports configurable OSC ports, but the message surface may not be fully documented.
This repo keeps Samplebrain behind an adapter: you discover addresses, then fill `bindings/samplebrain.yaml`.

## Sniff
```bash
python tools/osc_sniff.py --port 9002
```

## Probe
Once you know a candidate address, try sending to it. Or send semantic values to the bridge:
```bash
python tools/sb_probe.py --host 127.0.0.1 --port 9000 --macro chaos --macro-value 0.3
```
