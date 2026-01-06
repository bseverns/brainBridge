#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import ThreadingOSCUDPServer

def main() -> int:
    ap = argparse.ArgumentParser(description="Listen and print all OSC messages on a port.")
    ap.add_argument("--host", default="0.0.0.0")
    ap.add_argument("--port", type=int, required=True)
    args = ap.parse_args()

    disp = Dispatcher()
    disp.set_default_handler(lambda addr, *vals: print(addr, vals))

    server = ThreadingOSCUDPServer((args.host, args.port), disp)
    print(f"[sniff] listening on {args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[sniff] done")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
