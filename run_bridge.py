#!/usr/bin/env python3
from __future__ import annotations

import argparse
from sbrig.logging_config import setup_logging, get_logger
from sbrig.config import load_config
from sbrig.bridge import Bridge


def main() -> int:
    ap = argparse.ArgumentParser(description="sb-rig-bridge starter")
    ap.add_argument("--config", default="config/ports.yaml")
    ap.add_argument("--scene-dir", default="config/scenes")
    ap.add_argument("--bindings", default="bindings/samplebrain.yaml")
    ap.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Set the logging level (default: INFO)"
    )
    args = ap.parse_args()

    setup_logging(level=args.log_level)
    log = get_logger()

    cfg = load_config(args.config)
    bridge = Bridge(cfg=cfg, scene_dir=args.scene_dir, bindings_path=args.bindings)

    log.info(f"Listening on {cfg.listen_host}:{cfg.listen_port}")
    for name, ep in cfg.destinations.items():
        status = "ENABLED" if ep.enabled else "disabled"
        log.info(f"Destination {name}: {status} -> {ep.host}:{ep.port}")
    log.info("Press Ctrl+C to stop")

    try:
        bridge.start()
    except KeyboardInterrupt:
        log.info("Stopping...")
        bridge.stop()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
