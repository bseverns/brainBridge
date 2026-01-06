# TouchDesigner Setup (listen to /rig/*)

1) Add an OSC In CHOP.
2) Set Network Port to 9001 (or whatever you put in the bridge config).
3) Verify you see channels appear when you run:
   ```bash
   python tools/sb_probe.py --host <LIGHT_BRAIN_IP> --port 9001 --addr /rig/energy --value 0.5
   ```

Optional: use OSC Out CHOP to send readiness/health back to the bridge.
