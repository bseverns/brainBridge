# Failure Modes & Stage-Safe Behaviors

- Slew smoothing prevents hard parameter jumps.
- Panic loads a known-safe scene.
- Rate limiting reduces packet storms.

Suggested upgrades:
- watchdog timeouts per destination
- last-known-good restore after reconnect
- cue/param logs to disk (timestamped)
