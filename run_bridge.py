#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os

from sbrig.config import load_config
from sbrig.bridge import Bridge


def main() -> int:
    ap = argparse.ArgumentParser(description="sb-rig-bridge — stage-oriented OSC hub")
    ap.add_argument(
        "--config",
        default=os.environ.get("SB_RIG_CONFIG", "config/ports.yaml"),
        help="YAML config (listen + destinations).",
    )
    ap.add_argument(
        "--scene-dir",
        default=os.environ.get("SB_RIG_SCENES", "config/scenes"),
        help="Directory of scene YAML files.",
    )
    ap.add_argument(
        "--bindings",
        default=os.environ.get("SB_RIG_BINDINGS", "bindings/samplebrain.yaml"),
        help="Samplebrain binding YAML (optional; unbound entries are ignored).",
    )
    args = ap.parse_args()

    cfg = load_config(args.config)
    bridge = Bridge(cfg=cfg, scene_dir=args.scene_dir, bindings_path=args.bindings)

    print(f"[bridge] listen {cfg.listen_host}:{cfg.listen_port}")
    for name, ep in cfg.destinations.items():
        state = "ENABLED" if ep.enabled else "disabled"
        print(f"[bridge] dest {name}: {state} -> {ep.host}:{ep.port}")
    print("[bridge] ctrl-c to stop")

    try:
        bridge.start()
    except KeyboardInterrupt:
        print("\n[bridge] stopping...")
        bridge.stop()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
