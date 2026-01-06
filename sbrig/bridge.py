from __future__ import annotations

import time
import threading
import random
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import ThreadingOSCUDPServer
from pythonosc.udp_client import SimpleUDPClient

from .config import BridgeConfig
from .slew import Slew
from .scenes import load_scene, morph_scenes, Scene
from .bindings import load_samplebrain_bindings, SamplebrainBindings
from .osc_util import coerce_arg
from .morph import clamp01, apply_curve, apply_wells, apply_snap, SnapState
from .fracture import FractureState, trigger_if_crossed, update_envelope, apply_fracture, compute_phase

@dataclass
class Destination:
    name: str
    client: SimpleUDPClient
    enabled: bool

class Bridge:
    """Stage-oriented OSC hub.

    Receives a stable house API (/rig/*), fans out to destinations,
    and provides scenes + a Morph Space with stage-musical behavior.
    """

    MACRO_NAMES = [
        "energy", "density", "grain", "tightness", "chaos", "drift", "space", "color",
        "vis_trim", "vis_density_trim", "global_trim",
    ]

    def __init__(self, cfg: BridgeConfig, scene_dir: str, bindings_path: str):
        self.cfg = cfg
        self.scene_dir = scene_dir
        self.samplebrain_bindings: SamplebrainBindings = load_samplebrain_bindings(bindings_path)

        self.destinations: Dict[str, Destination] = {}
        for name, ep in cfg.destinations.items():
            self.destinations[name] = Destination(
                name=name,
                client=SimpleUDPClient(ep.host, ep.port),
                enabled=ep.enabled,
            )

        # Slew for continuous macros
        self.slews: Dict[str, Slew] = {}
        for k, units in cfg.slew_units_per_sec.items():
            self.slews[k] = Slew(initial=0.0, units_per_sec=units)

        self.state: Dict[str, Any] = {}
        self.active_scene: Optional[str] = None
        self.last_scene_key: Optional[str] = None

        # Morph space memory + physics
        self.morph_a_key: Optional[str] = None
        self.morph_b_key: Optional[str] = None
        self.morph_a_scene: Optional[Scene] = None
        self.morph_b_scene: Optional[Scene] = None

        self.morph_target: float = 0.0      # controller target
        self.morph_raw: float = 0.0         # after inertia slew
        self.morph_applied: float = 0.0     # after curve/wells/snap
        self._last_morph_apply_time: float = 0.0
        self._morph_min_interval = 1.0 / max(1.0, cfg.morph.apply_hz)

        self.morph_slew = Slew(initial=0.0, units_per_sec=cfg.morph.inertia_units_per_sec)
        self.snap_state = SnapState()

        # Fracture (Law 3)
        self.fracture_state = FractureState()
        self.fracture_enabled = bool(cfg.fracture.enabled)
        self.fracture_amount = float(cfg.fracture.amount)  # base
        self.fracture_w_audio = 0.75
        self.fracture_w_visual = 0.75
        self.fracture_w_processing = 0.55  # visual-adjacent by default
        self._fracture_rng = random.Random(1337)

        self._last_send_time: Dict[Tuple[str, str], float] = {}
        self._min_send_interval = 1.0 / max(1.0, cfg.rate_limit_hz)

        self.dispatcher = Dispatcher()
        self._register_routes()
        self.dispatcher.set_default_handler(self._on_any)

        self.server = ThreadingOSCUDPServer((cfg.listen_host, cfg.listen_port), self.dispatcher)
        self._server_thread: Optional[threading.Thread] = None
        self._running = False

    def _register_routes(self) -> None:
        self.dispatcher.map("/rig/cue", self._on_cue)

        for name in self.MACRO_NAMES:
            self.dispatcher.map(f"/rig/{name}", self._on_macro, name)

        self.dispatcher.map("/rig/param", self._on_param)
        self.dispatcher.map("/rig/panic", self._on_panic)

        # Morph space
        self.dispatcher.map("/rig/morph/t", self._on_morph_t)
        self.dispatcher.map("/rig/morph/setA", self._on_morph_setA)
        self.dispatcher.map("/rig/morph/setB", self._on_morph_setB)
        self.dispatcher.map("/rig/morph/swap", self._on_morph_swap)
        self.dispatcher.map("/rig/morph/commit", self._on_morph_commit)

        # Fracture controls (weights are "shiftable" in ReaLearn)
        self.dispatcher.map("/rig/fracture/enable", self._on_fracture_enable)
        self.dispatcher.map("/rig/fracture/amount", self._on_fracture_amount)
        self.dispatcher.map("/rig/fracture/w_audio", self._on_fracture_w_audio)
        self.dispatcher.map("/rig/fracture/w_visual", self._on_fracture_w_visual)
        self.dispatcher.map("/rig/fracture/w_processing", self._on_fracture_w_processing)
        self.dispatcher.map("/rig/fracture/balance", self._on_fracture_balance)

    # ------------------------
    # Incoming OSC handlers
    # ------------------------

    def _on_any(self, address: str, *args: Any) -> None:
        # Address-only cues: /rig/cue/<scene>
        if address.startswith("/rig/cue/"):
            scene = address.split("/rig/cue/", 1)[1].strip("/")
            if scene:
                self.apply_scene_name(scene)
            return

        # Optional direct morph set: /rig/morph/a/<scene> or /rig/morph/b/<scene>
        if address.startswith("/rig/morph/a/"):
            scene = address.split("/rig/morph/a/", 1)[1].strip("/")
            if scene:
                self._set_morph_endpoint("A", scene)
            return
        if address.startswith("/rig/morph/b/"):
            scene = address.split("/rig/morph/b/", 1)[1].strip("/")
            if scene:
                self._set_morph_endpoint("B", scene)
            return

    def _on_cue(self, address: str, *args: Any) -> None:
        if not args:
            return
        self.apply_scene_name(str(args[0]).strip())

    def _on_macro(self, address: str, macro_name: str, *args: Any) -> None:
        if not args:
            return
        try:
            self.set_macro(macro_name, float(args[0]))
        except Exception:
            return

    def _on_param(self, address: str, *args: Any) -> None:
        if len(args) < 2:
            return
        self.set_param(str(args[0]).strip(), args[1])

    def _on_panic(self, address: str, *args: Any) -> None:
        if not args:
            self.apply_scene_name("panic")
            return
        try:
            if int(float(args[0])) != 0:
                self.apply_scene_name("panic")
        except Exception:
            self.apply_scene_name("panic")

    # ---- Morph space ----

    def _on_morph_t(self, address: str, *args: Any) -> None:
        if not args:
            return
        try:
            t = float(args[0])
        except Exception:
            return
        self.set_morph_target(t)

    def _on_morph_setA(self, address: str, *args: Any) -> None:
        if self.last_scene_key:
            self._set_morph_endpoint("A", self.last_scene_key)

    def _on_morph_setB(self, address: str, *args: Any) -> None:
        if self.last_scene_key:
            self._set_morph_endpoint("B", self.last_scene_key)

    def _on_morph_swap(self, address: str, *args: Any) -> None:
        self.morph_a_key, self.morph_b_key = self.morph_b_key, self.morph_a_key
        self.morph_a_scene, self.morph_b_scene = self.morph_b_scene, self.morph_a_scene
        self.snap_state.snapped = False
        self.snap_state.point = None
        self._apply_morph(force=True)

    def _on_morph_commit(self, address: str, *args: Any) -> None:
        a, b = self._get_morph_scenes()
        if not a or not b:
            return
        committed = morph_scenes(a, b, self.morph_applied)
        self.morph_a_scene = committed
        self.morph_a_key = committed.name
        self.set_morph_target(0.0)
        self.apply_scene(committed)

    # ---- Fracture (Law 3) ----

    def _on_fracture_enable(self, address: str, *args: Any) -> None:
        if not args:
            self.fracture_enabled = not self.fracture_enabled
        else:
            try:
                self.fracture_enabled = bool(int(float(args[0])))
            except Exception:
                self.fracture_enabled = True
        self._send_all("/rig/fracture/enabled", 1 if self.fracture_enabled else 0)

    def _on_fracture_amount(self, address: str, *args: Any) -> None:
        if not args:
            return
        try:
            self.fracture_amount = clamp01(float(args[0]))
        except Exception:
            return
        self._send_all("/rig/fracture/amount", self.fracture_amount)

    def _on_fracture_w_audio(self, address: str, *args: Any) -> None:
        if not args:
            return
        try:
            self.fracture_w_audio = clamp01(float(args[0]))
        except Exception:
            return
        self._send_all("/rig/fracture/w_audio", self.fracture_w_audio)

    def _on_fracture_w_visual(self, address: str, *args: Any) -> None:
        if not args:
            return
        try:
            self.fracture_w_visual = clamp01(float(args[0]))
        except Exception:
            return
        self._send_all("/rig/fracture/w_visual", self.fracture_w_visual)

    def _on_fracture_w_processing(self, address: str, *args: Any) -> None:
        if not args:
            return
        try:
            self.fracture_w_processing = clamp01(float(args[0]))
        except Exception:
            return
        self._send_all("/rig/fracture/w_processing", self.fracture_w_processing)

    def _on_fracture_balance(self, address: str, *args: Any) -> None:
        """Convenience: one control sets audio/visual weights in opposite directions."""
        if not args:
            return
        try:
            b = clamp01(float(args[0]))
        except Exception:
            return
        self.fracture_w_audio = clamp01(1.0 - b)
        self.fracture_w_visual = clamp01(b)
        self._send_all("/rig/fracture/w_audio", self.fracture_w_audio)
        self._send_all("/rig/fracture/w_visual", self.fracture_w_visual)

    # ------------------------
    # Server lifecycle
    # ------------------------

    def start(self) -> None:
        self._running = True
        self._server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self._server_thread.start()
        self._broadcast_health()
        self._run_loop()

    def stop(self) -> None:
        self._running = False
        try:
            self.server.shutdown()
        except Exception:
            pass

    def _run_loop(self) -> None:
        last = time.time()
        while self._running:
            now = time.time()
            dt = now - last
            last = now

            # Slew continuous macros
            for name, slew in self.slews.items():
                prev = self.state.get(name, None)
                v = slew.step(dt)
                self.state[name] = v

                if prev is None or abs(float(prev) - float(v)) > 1e-4:
                    self._send_all("/rig/" + name, v)

                    if name in self.samplebrain_bindings.macros:
                        b = self.samplebrain_bindings.macros[name]
                        self._send_dest("samplebrain", b.address, coerce_arg(v, b.type))

            # Fracture envelope decay
            update_envelope(self.fracture_state, dt, self.cfg.fracture.decay_sec)

            # Morph inertia + laws
            self.morph_slew.set_target(self.morph_target)
            self.morph_raw = self.morph_slew.step(dt)
            self._apply_morph(now=now)

            time.sleep(1.0 / 120.0)

    # ------------------------
    # State mutations
    # ------------------------

    def set_macro(self, name: str, value: float) -> None:
        value = clamp01(value)
        if name in self.slews:
            self.slews[name].set_target(value)
        else:
            self.state[name] = value
            self._send_all(f"/rig/{name}", value)

    def set_param(self, name: str, value: Any) -> None:
        self.state[name] = value
        self._send_all(f"/rig/param/{name}", value)

        if name in self.samplebrain_bindings.params:
            b = self.samplebrain_bindings.params[name]
            self._send_dest("samplebrain", b.address, coerce_arg(value, b.type))
        if name in self.samplebrain_bindings.macros:
            b = self.samplebrain_bindings.macros[name]
            self._send_dest("samplebrain", b.address, coerce_arg(value, b.type))

    def apply_scene_name(self, name: str) -> None:
        self.last_scene_key = name
        self.apply_scene(load_scene(self.scene_dir, name))

    def apply_scene(self, scene: Scene) -> None:
        self.active_scene = scene.name
        self._send_all("/rig/scene", scene.name)

        for addr, val in scene.touchdesigner.items():
            self._send_dest("touchdesigner", addr, val)
        for addr, val in scene.processing.items():
            self._send_dest("processing", addr, val)

        for key, val in scene.samplebrain.items():
            if key in self.samplebrain_bindings.macros:
                b = self.samplebrain_bindings.macros[key]
                self._send_dest("samplebrain", b.address, coerce_arg(val, b.type))
                if key in self.slews and isinstance(val, (int, float)):
                    self.slews[key].set_target(float(val))
            elif key in self.samplebrain_bindings.params:
                b = self.samplebrain_bindings.params[key]
                self._send_dest("samplebrain", b.address, coerce_arg(val, b.type))
            else:
                self.set_param(key, val)

    # ---- Morph helpers ----

    def set_morph_target(self, t: float) -> None:
        self.morph_target = clamp01(t)
        self._send_all("/rig/morph/t_target", self.morph_target)

    def _set_morph_endpoint(self, which: str, scene_key: str) -> None:
        try:
            sc = load_scene(self.scene_dir, scene_key)
        except FileNotFoundError:
            return
        if which.upper() == "A":
            self.morph_a_key = scene_key
            self.morph_a_scene = sc
            self._send_all("/rig/morph/a", scene_key)
        else:
            self.morph_b_key = scene_key
            self.morph_b_scene = sc
            self._send_all("/rig/morph/b", scene_key)

    def _get_morph_scenes(self) -> tuple[Optional[Scene], Optional[Scene]]:
        return self.morph_a_scene, self.morph_b_scene

    def _apply_morph(self, *, now: float, force: bool = False) -> None:
        if not force and (now - self._last_morph_apply_time) < self._morph_min_interval:
            return

        a, b = self._get_morph_scenes()
        if not a or not b:
            return

        # --- Performance laws (Morph) ---
        t = clamp01(self.morph_raw)                # inertia already applied via morph_slew
        t = apply_curve(t, self.cfg.morph.curve)   # curve (feel)

        if self.cfg.morph.wells_enabled:
            t = apply_wells(
                t,
                points=self.cfg.morph.well_points,
                radius=self.cfg.morph.well_radius,
                strength=self.cfg.morph.well_strength,
            )

        if self.cfg.morph.snap_enabled:
            t = apply_snap(
                t,
                points=self.cfg.morph.snap_points,
                threshold=self.cfg.morph.snap_threshold,
                hysteresis=self.cfg.morph.snap_hysteresis,
                state=self.snap_state,
            )

        # Trigger fracture when crossing landmarks
        if self.fracture_enabled and self.cfg.fracture.enabled:
            trigger_if_crossed(self.fracture_state, t, self.cfg.fracture.thresholds)

        # telemetry for visuals / debugging
        self._send_all("/rig/morph/t_raw", clamp01(self.morph_raw))
        self._send_all("/rig/morph/t_applied", t)
        self._send_all("/rig/morph/snapped", 1 if self.snap_state.snapped else 0)
        if self.snap_state.point is not None:
            self._send_all("/rig/morph/snap_point", float(self.snap_state.point))

        # fracture telemetry
        self._send_all("/rig/fracture/env", float(self.fracture_state.env))
        self._send_all("/rig/fracture/w_audio", float(self.fracture_w_audio))
        self._send_all("/rig/fracture/w_visual", float(self.fracture_w_visual))
        self._send_all("/rig/fracture/w_processing", float(self.fracture_w_processing))

        if (not force) and abs(t - self.morph_applied) < 1e-3 and self.fracture_state.env <= 0.001:
            return

        self.morph_applied = t
        self._last_morph_apply_time = now

        morphed = morph_scenes(a, b, t)

        # --- Law 3: Fracture (micro-jitters in select params) ---
        env_amount = clamp01(self.fracture_amount) * clamp01(self.fracture_state.env)
        phase = compute_phase(now, self.cfg.fracture.rate_hz)

        if self.fracture_enabled and env_amount > 0:
            morphed = apply_fracture(
                morphed,
                env_amount,
                w_audio=self.fracture_w_audio,
                w_visual=self.fracture_w_visual,
                w_processing=self.fracture_w_processing,
                cfg=self.cfg.fracture,
                rng=self._fracture_rng,
                phase=phase,
            )

        self.apply_scene(morphed)

    # ------------------------
    # OSC send helpers
    # ------------------------

    def _send_all(self, osc_address: str, arg: Any) -> None:
        for name in self.destinations.keys():
            self._send_dest(name, osc_address, arg)

    def _send_dest(self, dest_name: str, osc_address: Optional[str], arg: Any) -> None:
        dest = self.destinations.get(dest_name)
        if not dest or not dest.enabled:
            return

        if not osc_address:
            return  # ignore unbound destinations / placeholder bindings

        key = (dest_name, osc_address)
        now = time.time()
        last = self._last_send_time.get(key, 0.0)
        if (now - last) < self._min_send_interval:
            return
        self._last_send_time[key] = now

        try:
            dest.client.send_message(osc_address, arg if arg is not None else [])
        except Exception:
            self._send_health(dest_name, 0)

    def _broadcast_health(self) -> None:
        for name, d in self.destinations.items():
            self._send_health(name, 1 if d.enabled else 0)

    def _send_health(self, dest_name: str, connected: int) -> None:
        for name, d in self.destinations.items():
            if not d.enabled:
                continue
            try:
                d.client.send_message("/rig/health/connected", [dest_name, int(connected)])
            except Exception:
                pass
