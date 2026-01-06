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
from .scenes import load_scene, morph_scenes, Scene
from .bindings import load_samplebrain_bindings, SamplebrainBindings
from .osc_util import coerce_arg

@dataclass
class Destination:
    name: str
    client: SimpleUDPClient
    enabled: bool

class Bridge:
    """Stage-oriented OSC hub.

    Goals:
    - Receive a stable house API (/rig/*)
    - Translate and fan out to TouchDesigner / Samplebrain / Processing
    - Provide smoothing, scenes, and a morph space
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

        self.slews: Dict[str, Slew] = {}
        for k, units in cfg.slew_units_per_sec.items():
            self.slews[k] = Slew(initial=0.0, units_per_sec=units)

        self.state: Dict[str, Any] = {}
        self.active_scene: Optional[str] = None
        self.last_scene_key: Optional[str] = None

        # Morph space memory
        self.morph_a_key: Optional[str] = None
        self.morph_b_key: Optional[str] = None
        self.morph_a_scene: Optional[Scene] = None
        self.morph_b_scene: Optional[Scene] = None
        self.morph_t: float = 0.0

        self._last_send_time: Dict[Tuple[str, str], float] = {}
        self._min_send_interval = 1.0 / max(1.0, cfg.rate_limit_hz)

        self.dispatcher = Dispatcher()
        self._register_routes()

        # Catch address-only cue triggers like /rig/cue/embers
        self.dispatcher.set_default_handler(self._on_any)

        self.server = ThreadingOSCUDPServer((cfg.listen_host, cfg.listen_port), self.dispatcher)
        self._server_thread: Optional[threading.Thread] = None
        self._running = False

    def _register_routes(self) -> None:
        # String-based cues (optional)
        self.dispatcher.map("/rig/cue", self._on_cue)
        self.dispatcher.map("/rig/scene/load", self._on_cue)

        # Direct macro endpoints (ReaLearn-friendly)
        for name in self.MACRO_NAMES:
            self.dispatcher.map(f"/rig/{name}", self._on_macro, name)

        # Legacy multi-arg param setter
        self.dispatcher.map("/rig/param", self._on_param)

        # Safety
        self.dispatcher.map("/rig/panic", self._on_panic)

        # Morph space (SHIFT bank)
        self.dispatcher.map("/rig/morph/t", self._on_morph_t)
        self.dispatcher.map("/rig/morph/setA", self._on_morph_setA)
        self.dispatcher.map("/rig/morph/setB", self._on_morph_setB)
        self.dispatcher.map("/rig/morph/swap", self._on_morph_swap)
        self.dispatcher.map("/rig/morph/commit", self._on_morph_commit)

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
        # /rig/param (name, value)
        if len(args) < 2:
            return
        self.set_param(str(args[0]).strip(), args[1])

    def _on_panic(self, address: str, *args: Any) -> None:
        # any value or no-arg triggers panic
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
        self.set_morph_t(t)

    def _on_morph_setA(self, address: str, *args: Any) -> None:
        # store current "last scene key" as A
        if self.last_scene_key:
            self._set_morph_endpoint("A", self.last_scene_key)

    def _on_morph_setB(self, address: str, *args: Any) -> None:
        if self.last_scene_key:
            self._set_morph_endpoint("B", self.last_scene_key)

    def _on_morph_swap(self, address: str, *args: Any) -> None:
        self.morph_a_key, self.morph_b_key = self.morph_b_key, self.morph_a_key
        self.morph_a_scene, self.morph_b_scene = self.morph_b_scene, self.morph_a_scene
        # keep t as-is but re-apply
        self.set_morph_t(self.morph_t)

    def _on_morph_commit(self, address: str, *args: Any) -> None:
        # Commit current morph position into A and reset t to 0
        a, b = self._get_morph_scenes()
        if not a or not b:
            return
        committed = morph_scenes(a, b, self.morph_t)
        self.morph_a_scene = committed
        self.morph_a_key = committed.name
        self.morph_t = 0.0
        self._send_all("/rig/morph/t", 0.0)
        self.apply_scene(committed)

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

                    # If this macro is bound to Samplebrain, forward it
                    if name in self.samplebrain_bindings.macros:
                        b = self.samplebrain_bindings.macros[name]
                        self._send_dest("samplebrain", b.address, coerce_arg(v, b.type))

            time.sleep(1.0 / 120.0)

    # ------------------------
    # State mutations
    # ------------------------

    def set_macro(self, name: str, value: float) -> None:
        value = max(0.0, min(1.0, float(value)))
        if name in self.slews:
            self.slews[name].set_target(value)
        else:
            self.state[name] = value
            self._send_all(f"/rig/{name}", value)

    def set_param(self, name: str, value: Any) -> None:
        self.state[name] = value
        self._send_all(f"/rig/param/{name}", value)

        # Forward to Samplebrain if bound
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

        # TouchDesigner + Processing: send raw addresses
        for addr, val in scene.touchdesigner.items():
            self._send_dest("touchdesigner", addr, val)
        for addr, val in scene.processing.items():
            self._send_dest("processing", addr, val)

        # Samplebrain: interpret semantic keys via bindings
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
                # If unbound, treat it as a generic param
                self.set_param(key, val)

    # ---- Morph helpers ----

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
        a = self.morph_a_scene
        b = self.morph_b_scene
        return a, b

    def set_morph_t(self, t: float) -> None:
        t = max(0.0, min(1.0, float(t)))
        self.morph_t = t
        self._send_all("/rig/morph/t", t)

        a, b = self._get_morph_scenes()
        if not a or not b:
            return

        # Apply the morphed scene (numeric values interpolate)
        morphed = morph_scenes(a, b, t)
        self.apply_scene(morphed)

    # ------------------------
    # OSC send helpers
    # ------------------------

    def _send_all(self, osc_address: str, arg: Any) -> None:
        for name in self.destinations.keys():
            self._send_dest(name, osc_address, arg)

    def _send_dest(self, dest_name: str, osc_address: str, arg: Any) -> None:
        dest = self.destinations.get(dest_name)
        if not dest or not dest.enabled:
            return
        key = (dest_name, osc_address)
        now = time.time()
        last = self._last_send_time.get(key, 0.0)
        if (now - last) < self._min_send_interval:
            return
        self._last_send_time[key] = now
        try:
            if arg is None:
                dest.client.send_message(osc_address, [])
            else:
                dest.client.send_message(osc_address, arg)
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
