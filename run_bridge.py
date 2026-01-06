#!/usr/bin/env python3
from __future__ import annotations

import argparse
from sbrig.config import load_config
from sbrig.bridge import Bridge

def main() -> int:
    ap = argparse.ArgumentParser(description="sb-rig-bridge starter")
    ap.add_argument("--config", default="config/ports.yaml")
    ap.add_argument("--scene-dir", default="config/scenes")
    ap.add_argument("--bindings", default="bindings/samplebrain.yaml")
    args = ap.parse_args()

    cfg = load_config(args.config)
    bridge = Bridge(cfg=cfg, scene_dir=args.scene_dir, bindings_path=args.bindings)

    print(f"[bridge] listening on {cfg.listen_host}:{cfg.listen_port}")
    for name, ep in cfg.destinations.items():
        print(f"[bridge] dest {name}: {'ENABLED' if ep.enabled else 'disabled'} -> {ep.host}:{ep.port}")
    print("[bridge] ctrl-c to stop")

    try:
        bridge.start()
    except KeyboardInterrupt:
        print("\n[bridge] stopping...")
        bridge.stop()

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
