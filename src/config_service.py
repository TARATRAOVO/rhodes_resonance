from __future__ import annotations

"""
Config service: centralized read/write/validate helpers for JSON configs under ./configs.

Covers: story.json, characters.json, weapons.json, arts.json, feature_flags.json.

Notes
- Read operations always return a dict as loaded from JSON.
- Write operations are atomic (write to .tmp then replace) and validate per type.
- Back-compat policy: story.active_id is considered legacy and will be hidden on reads
  and rejected on writes.
- This module contains no FastAPI dependency; main imports and wires it to HTTP endpoints.
"""

import json
from pathlib import Path
from typing import Any, Dict, Tuple, Optional


class ConfigService:
    def __init__(self, root: Path, world_module: Any | None = None) -> None:
        self._root = Path(root)
        self._cfg_dir = self._root / "configs"
        self._world = world_module

    # ---------- Core IO ----------
    def _cfg_path(self, name: str) -> Path:
        m = {
            "story": self._cfg_dir / "story.json",
            "characters": self._cfg_dir / "characters.json",
            "weapons": self._cfg_dir / "weapons.json",
            "arts": self._cfg_dir / "arts.json",
            "feature_flags": self._cfg_dir / "feature_flags.json",
        }
        if name not in m:
            raise KeyError(f"unsupported config: {name}")
        return m[name]

    def read(self, name: str) -> dict:
        p = self._cfg_path(str(name))
        with p.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return self._drop_legacy_fields(name, data)

    def write(self, name: str, data: dict) -> Tuple[bool, str]:
        name = str(name)
        try:
            path = self._cfg_path(name)
        except KeyError:
            return False, "unsupported config"
        # Hard-delete: reject legacy active_id for story configs
        if name == "story" and isinstance(data, dict) and ("active_id" in data):
            return False, "active_id is not supported"

        # Validate by type
        ok, msg = True, "ok"
        if name == "story":
            ok, msg = self.validate_story(data)
        elif name == "weapons":
            ok, msg = self.validate_weapons(data)
        elif name == "characters":
            ok, msg = self.validate_characters(data)
        elif name == "arts":
            ok, msg = self.validate_arts(data)
        elif name == "feature_flags":
            ok, msg = self.validate_feature_flags(data)
        else:
            ok, msg = False, "unsupported config"

        if not ok:
            return False, msg

        try:
            self._atomic_write(path, data)
        except Exception as exc:
            return False, f"write failed: {exc}"
        return True, "ok"

    # ---------- Validation ----------
    def validate_story(self, obj: dict) -> Tuple[bool, str]:
        """Validate story config.

        Accept either a single-story object, or a multi-story container:
          {"stories": {"id": {...}, ...}}
        """

        def _validate_one(story: dict) -> Tuple[bool, str]:
            if not isinstance(story, dict):
                return False, "story must be a JSON object"
            scene = story.get("scene")
            if scene is not None and not isinstance(scene, dict):
                return False, "scene must be object when provided"
            if isinstance(scene, dict):
                # details: list of strings
                det = scene.get("details")
                if det is not None:
                    if not isinstance(det, list) or not all(isinstance(x, str) for x in det):
                        return False, "scene.details must be an array of strings"
                # objectives: list of strings
                objs = scene.get("objectives")
                if objs is not None:
                    if not isinstance(objs, list) or not all(isinstance(x, str) for x in objs):
                        return False, "scene.objectives must be an array of strings"
            # initial_positions: { name: [x,y] }
            ip = story.get("initial_positions")
            if ip is not None:
                if not isinstance(ip, dict):
                    return False, "initial_positions must be an object"
                for k, v in ip.items():
                    if not (isinstance(v, (list, tuple)) and len(v) >= 2):
                        return False, f"initial_positions.{k} must be [x,y]"
                    try:
                        int(v[0]); int(v[1])
                    except Exception:
                        return False, f"initial_positions.{k} coordinates must be integers"
            # Optional: events timeline validation (lenient)
            evs = story.get("events")
            if evs is not None:
                if not isinstance(evs, list):
                    return False, "events must be an array"
                for i, ev in enumerate(evs):
                    if not isinstance(ev, dict):
                        return False, f"events[{i}] must be an object"
                    # name optional string
                    if ev.get("name") is not None and not isinstance(ev.get("name"), str):
                        return False, f"events[{i}].name must be string"
                    # at (int) or time/time_min (string/int) optional
                    if ev.get("at") is not None:
                        try:
                            int(ev.get("at"))
                        except Exception:
                            return False, f"events[{i}].at must be integer minutes"
                    if ev.get("time") is not None and not isinstance(ev.get("time"), str):
                        return False, f"events[{i}].time must be HH:MM string"
                    if ev.get("time_min") is not None:
                        try:
                            int(ev.get("time_min"))
                        except Exception:
                            return False, f"events[{i}].time_min must be integer"
                    # note optional string
                    if ev.get("note") is not None and not isinstance(ev.get("note"), str):
                        return False, f"events[{i}].note must be string"
                    # effects optional list
                    if ev.get("effects") is not None and not isinstance(ev.get("effects"), list):
                        return False, f"events[{i}].effects must be an array"
            return True, "ok"

        if not isinstance(obj, dict):
            return False, "story must be a JSON object"
        # Hard-delete policy: top-level active_id is not supported
        if "active_id" in obj:
            return False, "active_id is not supported"
        # Multi-story container
        if isinstance(obj.get("stories"), dict):
            stories = obj.get("stories") or {}
            for sid, s in stories.items():
                ok, msg = _validate_one(s)
                if not ok:
                    return False, f"story '{sid}' invalid: {msg}"
            return True, "ok"
        # Single-story legacy
        return _validate_one(obj)

    def validate_weapons(self, obj: dict) -> Tuple[bool, str]:
        if not isinstance(obj, dict):
            return False, "weapons must be an object"
        allowed = {"label", "reach_steps", "skill", "defense_skill", "damage", "damage_type", "desc"}
        for wid, w in obj.items():
            if not isinstance(w, dict):
                return False, f"weapon {wid} must be an object"
            extra = set(w.keys()) - allowed
            if extra:
                return False, f"weapon {wid} has unknown keys: {sorted(extra)}"
            for req in ("label", "reach_steps", "skill", "defense_skill", "damage", "damage_type"):
                if req not in w:
                    return False, f"weapon {wid} missing required field '{req}'"
            try:
                rs = int(w.get("reach_steps"))
                if rs <= 0:
                    return False, f"weapon {wid}.reach_steps must be > 0"
            except Exception:
                return False, f"weapon {wid}.reach_steps must be an integer"
            dmg = str(w.get("damage") or "").lower()
            import re as _re
            if not _re.fullmatch(r"\d*d\d+(?:[+-]\d+)?", dmg):
                return False, f"weapon {wid}.damage must be NdM[+/-K], got '{dmg}'"
        return True, "ok"

    def validate_characters(self, obj: dict) -> Tuple[bool, str]:
        if not isinstance(obj, dict):
            return False, "characters must be an object"
        # Loose validation: allow any keys except legacy 'dnd' which is no longer supported
        for nm, data in obj.items():
            if nm == "relations":
                # relations is object of name -> name -> int
                rel = data
                if not isinstance(rel, dict):
                    return False, "relations must be an object"
                for a, m in rel.items():
                    if not isinstance(m, dict):
                        return False, f"relations.{a} must be an object"
                    for b, val in m.items():
                        try:
                            int(val)
                        except Exception:
                            return False, f"relations.{a}.{b} must be integer"
                continue
            if not isinstance(data, dict):
                return False, f"character {nm} must be an object"
            if "dnd" in data:
                return False, f"character {nm}: 'dnd' block is not supported (use 'coc')"
        return True, "ok"

    def validate_arts(self, obj: dict) -> Tuple[bool, str]:
        if not isinstance(obj, dict):
            return False, "arts must be an object"
        allowed = {
            "label", "cast_skill", "resist", "range_steps", "damage_type",
            "damage", "control", "mp", "tags", "desc"
        }
        import re as _re
        for aid, a in obj.items():
            if not isinstance(a, dict):
                return False, f"arts {aid} must be an object"
            extra = set(a.keys()) - allowed
            if extra:
                return False, f"arts {aid} has unknown keys: {sorted(extra)}"
            # required
            for req in ("label", "cast_skill", "resist", "range_steps", "damage_type"):
                if req not in a:
                    return False, f"arts {aid} missing required field '{req}'"
            # range_steps
            try:
                rs = int(a.get("range_steps"))
                if rs <= 0:
                    return False, f"arts {aid}.range_steps must be > 0"
            except Exception:
                return False, f"arts {aid}.range_steps must be an integer"
            # optional damage
            if "damage" in a and a["damage"] is not None:
                dmg = str(a.get("damage") or "").lower()
                if dmg and not _re.fullmatch(r"\d*d\d+(?:[+-]\d+)?", dmg):
                    return False, f"arts {aid}.damage must be NdM[+/-K], got '{dmg}'"
            # control block
            ctrl = a.get("control")
            if ctrl is not None:
                if not isinstance(ctrl, dict):
                    return False, f"arts {aid}.control must be an object"
                eff = ctrl.get("effect")
                if eff is not None and not isinstance(eff, str):
                    return False, f"arts {aid}.control.effect must be a string"
                dur = ctrl.get("duration")
                if dur is not None and not isinstance(dur, str):
                    return False, f"arts {aid}.control.duration must be a string"
            # mp block
            mp = a.get("mp")
            if mp is not None:
                if not isinstance(mp, dict):
                    return False, f"arts {aid}.mp must be an object"
                cost = mp.get("cost")
                if cost is not None:
                    try:
                        if int(cost) < 0:
                            return False, f"arts {aid}.mp.cost must be >= 0"
                    except Exception:
                        return False, f"arts {aid}.mp.cost must be an integer"
                var = mp.get("variable")
                if var is not None and not isinstance(var, bool):
                    return False, f"arts {aid}.mp.variable must be boolean"
                mx = mp.get("max")
                if mx is not None:
                    try:
                        int(mx)
                    except Exception:
                        return False, f"arts {aid}.mp.max must be an integer"
            # tags
            tags = a.get("tags")
            if tags is not None:
                if not isinstance(tags, list) or not all(isinstance(x, str) for x in tags):
                    return False, f"arts {aid}.tags must be an array of strings"
            # desc optional string
            desc = a.get("desc")
            if desc is not None and not isinstance(desc, str):
                return False, f"arts {aid}.desc must be a string"
        return True, "ok"

    def validate_feature_flags(self, obj: dict) -> Tuple[bool, str]:
        if not isinstance(obj, dict):
            return False, "feature_flags must be an object"
        # Be permissive on keys but require boolean values
        for k, v in obj.items():
            if not isinstance(v, bool):
                return False, f"feature_flags.{k} must be boolean"
        return True, "ok"

    # removed: validate_model (model.json is not exposed via config API)

    # ---------- Utilities ----------
    def list_story_ids(self) -> list[str]:
        try:
            if self._world is not None:
                return list(self._world.list_world_ids())  # type: ignore[attr-defined]
        except Exception:
            pass
        return []

    def _drop_legacy_fields(self, name: str, data: dict) -> dict:
        # Hard delete policy: never expose legacy active_id back to clients
        if name == "story" and isinstance(data, dict) and ("active_id" in data):
            try:
                data = dict(data)
                data.pop("active_id", None)
            except Exception:
                pass
        return data

    @staticmethod
    def _atomic_write(path: Path, obj: dict) -> None:
        tmp = path.with_suffix(path.suffix + ".tmp")
        # ensure directory exists
        path.parent.mkdir(parents=True, exist_ok=True)
        with tmp.open("w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=2)
            f.write("\n")
        tmp.replace(path)
