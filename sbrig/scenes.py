from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict
import os
import yaml

@dataclass
class Scene:
    name: str
    notes: str | None
    touchdesigner: Dict[str, Any]
    samplebrain: Dict[str, Any]
    processing: Dict[str, Any]

def load_scene(scene_dir: str, name: str) -> Scene:
    path = os.path.join(scene_dir, f"{name}.yaml")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Scene not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}
    return Scene(
        name=str(raw.get("name", name)),
        notes=raw.get("notes"),
        touchdesigner=dict(raw.get("touchdesigner", {}) or {}),
        samplebrain=dict(raw.get("samplebrain", {}) or {}),
        processing=dict(raw.get("processing", {}) or {}),
    )

def _is_number(x: Any) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)

def morph_scenes(a: Scene, b: Scene, t: float) -> Scene:
    t = max(0.0, min(1.0, float(t)))

    def morph_dict(da: Dict[str, Any], db: Dict[str, Any]) -> Dict[str, Any]:
        keys = set(da.keys()) | set(db.keys())
        out: Dict[str, Any] = {}
        for k in keys:
            va = da.get(k)
            vb = db.get(k)
            if _is_number(va) and _is_number(vb):
                out[k] = (1.0 - t) * float(va) + t * float(vb)
            else:
                out[k] = va if t < 0.5 else vb
        return out

    return Scene(
        name=f"{a.name}→{b.name}@{t:.2f}",
        notes="morphed",
        touchdesigner=morph_dict(a.touchdesigner, b.touchdesigner),
        samplebrain=morph_dict(a.samplebrain, b.samplebrain),
        processing=morph_dict(a.processing, b.processing),
    )
