from __future__ import annotations

import time
import threading
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import ThreadingOSCUDPServer
from pythonosc.udp_client import SimpleUDPClient

from .config import BridgeConfig
from .slew import Slew
from .scenes import load_scene, Scene
from .bindings import load_samplebrain_bindings, SamplebrainBindings
from .osc_util import coerce_arg
from .morph import clamp01
from .morph_controller import MorphController
from .fracture_controller import FractureController
from .logging_config import get_logger


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
        self.log = get_logger("bridge")
        self.samplebrain_bindings: SamplebrainBindings = load_samplebrain_bindings(bindings_path)

        # Destinations
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

        # Controllers (extracted logic)
        self.morph = MorphController(cfg.morph, scene_dir)
        self.fracture = FractureController(cfg.fracture)

        # Rate limiting
        self._last_send_time: Dict[Tuple[str, str], float] = {}
        self._min_send_interval = 1.0 / max(1.0, cfg.rate_limit_hz)

        # OSC server
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

        # Fracture controls
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

        # Direct morph set: /rig/morph/a/<scene> or /rig/morph/b/<scene>
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

    # ---- Morph space handlers ----

    def _on_morph_t(self, address: str, *args: Any) -> None:
        if not args:
            return
        try:
            t = float(args[0])
        except Exception:
            return
        self.morph.set_target(t)
        self._send_all("/rig/morph/t_target", self.morph.target)

    def _on_morph_setA(self, address: str, *args: Any) -> None:
        if self.last_scene_key:
            self._set_morph_endpoint("A", self.last_scene_key)

    def _on_morph_setB(self, address: str, *args: Any) -> None:
        if self.last_scene_key:
            self._set_morph_endpoint("B", self.last_scene_key)

    def _on_morph_swap(self, address: str, *args: Any) -> None:
        self.morph.swap_endpoints()
        self._apply_morph(force=True)

    def _on_morph_commit(self, address: str, *args: Any) -> None:
        committed = self.morph.commit()
        if committed:
            self.apply_scene(committed)

    # ---- Fracture handlers ----

    def _on_fracture_enable(self, address: str, *args: Any) -> None:
        if not args:
            self.fracture.toggle_enabled()
        else:
            try:
                self.fracture.set_enabled(bool(int(float(args[0]))))
            except Exception:
                self.fracture.set_enabled(True)
        self._send_all("/rig/fracture/enabled", 1 if self.fracture.enabled else 0)

    def _on_fracture_amount(self, address: str, *args: Any) -> None:
        if not args:
            return
        try:
            self.fracture.set_amount(float(args[0]))
        except Exception:
            return
        self._send_all("/rig/fracture/amount", self.fracture.amount)

    def _on_fracture_w_audio(self, address: str, *args: Any) -> None:
        if not args:
            return
        try:
            self.fracture.set_weight_audio(float(args[0]))
        except Exception:
            return
        self._send_all("/rig/fracture/w_audio", self.fracture.w_audio)

    def _on_fracture_w_visual(self, address: str, *args: Any) -> None:
        if not args:
            return
        try:
            self.fracture.set_weight_visual(float(args[0]))
        except Exception:
            return
        self._send_all("/rig/fracture/w_visual", self.fracture.w_visual)

    def _on_fracture_w_processing(self, address: str, *args: Any) -> None:
        if not args:
            return
        try:
            self.fracture.set_weight_processing(float(args[0]))
        except Exception:
            return
        self._send_all("/rig/fracture/w_processing", self.fracture.w_processing)

    def _on_fracture_balance(self, address: str, *args: Any) -> None:
        if not args:
            return
        try:
            self.fracture.set_balance(float(args[0]))
        except Exception:
            return
        self._send_all("/rig/fracture/w_audio", self.fracture.w_audio)
        self._send_all("/rig/fracture/w_visual", self.fracture.w_visual)

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

            # Step controllers
            self.fracture.step(dt)
            self.morph.step(dt)
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
        try:
            self.apply_scene(load_scene(self.scene_dir, name))
        except FileNotFoundError:
            self.log.warning(f"Scene not found: {name}")

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

    def _set_morph_endpoint(self, which: str, scene_key: str) -> None:
        if self.morph.set_endpoint(which, scene_key):
            if which.upper() == "A":
                self._send_all("/rig/morph/a", scene_key)
            else:
                self._send_all("/rig/morph/b", scene_key)

    def _apply_morph(self, *, now: float = None, force: bool = False) -> None:
        if now is None:
            now = time.time()

        # Broadcast telemetry
        morph_tel = self.morph.get_telemetry()
        self._send_all("/rig/morph/t_raw", morph_tel.t_raw)
        self._send_all("/rig/morph/t_applied", morph_tel.t_applied)
        self._send_all("/rig/morph/snapped", 1 if morph_tel.snapped else 0)
        if morph_tel.snap_point is not None:
            self._send_all("/rig/morph/snap_point", float(morph_tel.snap_point))

        frac_tel = self.fracture.get_telemetry()
        self._send_all("/rig/fracture/env", float(frac_tel.env))
        self._send_all("/rig/fracture/w_audio", float(frac_tel.w_audio))
        self._send_all("/rig/fracture/w_visual", float(frac_tel.w_visual))
        self._send_all("/rig/fracture/w_processing", float(frac_tel.w_processing))

        # Apply morph with fracture trigger detection
        morphed = self.morph.apply(
            now,
            fracture_cfg=self.cfg.fracture,
            fracture_state=self.fracture.state,
            force=force
        )

        if morphed is None:
            return

        # Apply fracture effects
        morphed = self.fracture.apply(morphed, now)
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
            return

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
