#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pythonosc.udp_client import SimpleUDPClient

def _coerce_value(v: str):
    if v is None:
        return None
    s = str(v)
    if s.lower() in ("true", "false"):
        return 1 if s.lower() == "true" else 0
    try:
        return int(s)
    except ValueError:
        try:
            return float(s)
        except ValueError:
            return s

def main() -> int:
    ap = argparse.ArgumentParser(description="Send a quick test OSC message.")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, required=True)

    ap.add_argument("--addr", help="OSC address to send (e.g. /rig/energy or /rig/cue/embers)")
    ap.add_argument("--value", help="Optional value (int/float/string). Omit for no-arg send.")

    # Convenience options
    ap.add_argument("--cue")
    ap.add_argument("--energy", type=float)
    ap.add_argument("--morph_t", type=float)
    ap.add_argument("--panic", action="store_true")

    args = ap.parse_args()
    c = SimpleUDPClient(args.host, args.port)

    if args.cue:
        c.send_message("/rig/cue", args.cue)
        print("[probe] /rig/cue", args.cue)

    if args.energy is not None:
        c.send_message("/rig/energy", float(args.energy))
        print("[probe] /rig/energy", args.energy)

    if args.morph_t is not None:
        c.send_message("/rig/morph/t", float(args.morph_t))
        print("[probe] /rig/morph/t", args.morph_t)

    if args.panic:
        c.send_message("/rig/panic", [])
        print("[probe] /rig/panic []")

    if args.addr:
        v = _coerce_value(args.value) if args.value is not None else None
        if v is None:
            c.send_message(args.addr, [])
            print("[probe]", args.addr, "[]")
        else:
            c.send_message(args.addr, v)
            print("[probe]", args.addr, v)

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
