# Minimal world state and tools for the demo; designed to be pure and easy to test.
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Tuple, Any, List, Optional, Set, Union
from pathlib import Path
import json
import math
import random
import re
try:
    from agentscope.tool import ToolResponse  # type: ignore
    from agentscope.message import TextBlock  # type: ignore
except Exception:
    # Lightweight fallbacks for local tests without agentscope installed
    class ToolResponse:  # type: ignore
        def __init__(self, content=None, metadata=None):
            self.content = content or []
            self.metadata = metadata or {}

class TextBlock(dict):  # type: ignore
        def __init__(self, type: str = "text", text: str = ""):
            super().__init__(type=type, text=text)


# --- Config loaders (migrated from main) ---
# Keep the logic close to the world so the component owns how its data is sourced.

def project_root() -> Path:
    """Return repository root (folder that contains configs/ and src/).

    Walk upwards from this file to find a directory that contains a
    `configs/` folder. Fallback heuristics mirror the ones used in main.
    """
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "configs").exists():
            return parent
    try:
        return (
            here.parents[1]
            if (here.parents[1] / "configs").exists()
            else here.parents[2]
        )
    except Exception:
        return here.parents[1]


def _configs_dir() -> Path:
    return project_root() / "configs"


def _load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"expected object at {path}, got {type(data).__name__}")
    return data


def load_story_config(selected_id: Optional[str] = None) -> dict:
    """Load story configuration.

    Supports two shapes:
      1) Single-story (legacy): the file is the story object itself.
      2) Multi-story container: {"active_id": "id", "stories": {"id": {..}, ...}}

    Always returns a single-story object (the active one).
    """
    data = _load_json(_configs_dir() / "story.json")
    if not data:
        raise FileNotFoundError("configs/story.json is missing or empty; fallback removed")
    try:
        if isinstance(data, dict) and isinstance(data.get("stories"), dict):
            stories = data.get("stories") or {}
            sid = ""
            sel = str(selected_id).strip() if selected_id is not None else ""
            if sel and sel in stories:
                sid = sel
            else:
                sid = sorted(stories.keys())[0] if stories else ""
            story = stories.get(sid) if sid else None
            if isinstance(story, dict):
                return story
    except Exception:
        pass
    return data


def load_characters() -> dict:
    return _load_json(_configs_dir() / "characters.json")


def load_weapons() -> dict:
    return _load_json(_configs_dir() / "weapons.json")


def load_arts() -> dict:
    path = _configs_dir() / "arts.json"
    if not path.exists():
        return {}
    data = _load_json(path)
    if not isinstance(data, dict):
        return {}
    return data


# --- Core grid configuration ---
# Distances use grid steps only (简称“步”).
DEFAULT_MOVE_SPEED_STEPS = 6  # standard humanoid walk in steps per turn
DEFAULT_REACH_STEPS = 1       # default melee reach in steps
# Dying rules: per-user request, a character at 0 HP enters a "dying" state and
# dies after N of their own turns (or immediately upon taking damage again).
DYING_TURNS_DEFAULT = 3

# Action restriction rules for control/system statuses
# Keys are lower-case effect names expected from arts_defs.control.effect
CONTROL_STATUS_RULES: Dict[str, Dict[str, Any]] = {
    # Hard disables
    "stunned": {"blocks": {"all"}},
    "paralyzed": {"blocks": {"all"}},
    "sleep": {"blocks": {"all"}},
    "frozen": {"blocks": {"all"}},
    # Partial
    "silenced": {"blocks": {"cast"}},
    "rooted": {"blocks": {"move"}},
    "immobilized": {"blocks": {"move"}},
    "restrained": {"blocks": {"move", "attack"}},
}

# Human-readable labels for actions
_ACTION_LABEL = {
    "move": "移动",
    "attack": "发动攻击",
    "cast": "施放术式",
    "dash": "冲刺",
    "disengage": "脱离接触",
    "help": "协助",
    "first_aid": "急救",
    "set_protection": "建立守护",
    "clear_protection": "清除守护",
    "transfer_item": "交付物品",
    "action": "进行该行动",
}


def format_distance_steps(steps: int) -> str:
    """Format a grid distance for narration in steps, e.g., "6步"."""
    try:
        s = int(steps)
    except Exception:
        s = 0
    if s < 0:
        s = 0
    return f"{s}步"


def _default_move_steps() -> int:
    return int(DEFAULT_MOVE_SPEED_STEPS) if DEFAULT_MOVE_SPEED_STEPS > 0 else 1


def _pair_key(a: str, b: str) -> Tuple[str, str]:
    """Return a sorted key for undirected pair-based state."""
    return tuple(sorted([str(a), str(b)]))


def _rel_key(a: str, b: str) -> Tuple[str, str]:
    """Return a directed key representing a->b relation."""
    return str(a), str(b)


@dataclass
class World:
    # Monotonic version to help higher layers cache snapshots/runtime.
    version: int = 0
    time_min: int = 8 * 60  # 08:00 in minutes
    weather: str = "sunny"
    relations: Dict[Tuple[str, str], int] = field(default_factory=dict)
    inventory: Dict[str, Dict[str, int]] = field(default_factory=dict)
    characters: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    positions: Dict[str, Tuple[int, int]] = field(default_factory=dict)
    objective_positions: Dict[str, Tuple[int, int]] = field(default_factory=dict)
    location: str = "罗德岛·会议室"
    objectives: List[str] = field(default_factory=list)
    objective_status: Dict[str, str] = field(default_factory=dict)
    objective_notes: Dict[str, str] = field(default_factory=dict)
    # Scene flavor/details lines to help agents ground their narration
    scene_details: List[str] = field(default_factory=list)
    events: List[Dict[str, Any]] = field(default_factory=list)
    tension: int = 1  # 0-5
    marks: List[str] = field(default_factory=list)
    # Compatibility: legacy field referenced by tests; remains a no-op container
    hidden_enemies: Dict[str, Any] = field(default_factory=dict)
    # --- Combat (rounds) removed ---
    # World no longer owns turn/round/initiative state; orchestrator drives order
    # per-turn tokens/state for each name
    turn_state: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    # default walking speeds stored as grid steps
    speeds: Dict[str, int] = field(default_factory=dict)
    # simple cover levels per character
    cover: Dict[str, str] = field(default_factory=dict)
    # conditions container retained for compatibility, but only 'dying' is kept in logic now.
    # Other states like hidden/prone/grappled/etc. are removed.
    conditions: Dict[str, Set[str]] = field(default_factory=dict)
    # lightweight triggers queue (ready/opportunity_attack, etc.)
    triggers: List[Dict[str, Any]] = field(default_factory=list)
    # --- Weapons/Arts (simple dictionaries, configured at startup) ---
    weapon_defs: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    arts_defs: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    # Participants order for the current scene (names only)
    participants: List[str] = field(default_factory=list)
    # Protection links: protectee -> ordered list of guardians
    guardians: Dict[str, List[str]] = field(default_factory=dict)
    # --- Multi-scene (entrances) minimal support ---
    # Scenes registry and per-actor scene membership
    scenes: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    entrances: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    scene_of: Dict[str, str] = field(default_factory=dict)
    # --- Endings (multi-rule) ---
    # Normalized endings definitions loaded from story config
    endings_defs: List[Dict[str, Any]] = field(default_factory=list)
    # Frozen result once an ending is reached; None when not ended yet
    ending_state: Optional[Dict[str, Any]] = None

    def _touch(self) -> None:
        try:
            self.version += 1
        except Exception:
            # be defensive; never fail mutators due to versioning
            self.version = int(self.version or 0) + 1

    # snapshot() removed by design. Only use visible_snapshot_for(name, filter_to_scene=True).


WORLD = World()


# --- tools ---

def _parse_story_positions(obj: Any, out: Dict[str, Tuple[int, int]]) -> None:
    """Merge name->[x,y] mappings into `out` dict (later calls override earlier)."""
    if not isinstance(obj, dict):
        return
    for k, v in obj.items():
        if isinstance(v, (list, tuple)) and len(v) >= 2:
            try:
                x, y = int(v[0]), int(v[1])
            except Exception:
                continue
            out[str(k)] = (x, y)


def _normalize_scene_cfg(sc: Optional[Dict[str, Any]]):
    name = None
    objectives: List[str] = []
    details: List[str] = []
    weather: Optional[str] = None
    time_min: Optional[int] = None
    if isinstance(sc, dict):
        if isinstance(sc.get("name"), str) and sc["name"].strip():
            name = sc["name"].strip()
        objs = sc.get("objectives")
        if isinstance(objs, list):
            for obj in objs:
                if isinstance(obj, str) and obj.strip():
                    objectives.append(obj.strip())
        det = sc.get("details")
        if isinstance(det, str) and det.strip():
            details = [det.strip()]
        elif isinstance(det, list):
            for d in det:
                if isinstance(d, (str, int, float)):
                    s = str(d).strip()
                    if s:
                        details.append(s)
        # Accept legacy fields 'description' or 'opening' and append into details
        for k in ("description", "opening"):
            v = sc.get(k)
            if isinstance(v, str) and v.strip():
                details.append(v.strip())
        t = sc.get("time")
        if isinstance(t, str) and t:
            try:
                hh_str, mm_str = t.strip().split(":")
                hh, mm = int(hh_str), int(mm_str)
                if 0 <= hh < 24 and 0 <= mm < 60:
                    time_min = hh * 60 + mm
            except Exception:
                pass
        if time_min is None and isinstance(sc.get("time_min"), (int, float)):
            try:
                time_min = int(sc.get("time_min"))
            except Exception:
                time_min = None
        if isinstance(sc.get("weather"), str) and sc["weather"].strip():
            weather = sc["weather"].strip()
    return name, objectives, details, weather, time_min


# ---- Ending config helpers ----
def _parse_time_to_min(v: Any) -> Optional[int]:
    try:
        if isinstance(v, (int, float)):
            iv = int(v)
            return iv if iv >= 0 else None
        if isinstance(v, str) and v.strip():
            s = v.strip()
            m = re.match(r"^(\d{1,2}):(\d{2})$", s)
            if m:
                hh, mm = int(m.group(1)), int(m.group(2))
                if 0 <= hh < 24 and 0 <= mm < 60:
                    return hh * 60 + mm
            # Allow plain integer strings as minutes
            if s.isdigit():
                return int(s)
    except Exception:
        return None
    return None


def _normalize_endings_list(defs: Any) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    if not isinstance(defs, list):
        return out
    for item in defs:
        if not isinstance(item, dict):
            continue
        d: Dict[str, Any] = {}
        try:
            d["id"] = str(item.get("id") or "").strip() or None
        except Exception:
            d["id"] = None
        try:
            d["label"] = str(item.get("label") or "").strip() or None
        except Exception:
            d["label"] = None
        try:
            oc = str(item.get("outcome") or "").strip().lower()
            d["outcome"] = oc if oc in {"success", "failure", "neutral"} else None
        except Exception:
            d["outcome"] = None
        try:
            pr = int(item.get("priority"))
        except Exception:
            pr = 0
        d["priority"] = pr
        # when-clause may be dict (tree) or list -> treat list as any
        w = item.get("when")
        if isinstance(w, list):
            w = {"any": list(w)}
        d["when"] = w if isinstance(w, (dict, list)) else None
        out.append(d)
    return out


def init_world_from_configs(*, selected_story_id: Optional[str] = None, reset: bool = True) -> dict:
    """Initialise WORLD from configs folder in a single call.

    - Loads story/characters/weapons/arts from configs.
    - Optionally resets WORLD before applying.
    - Applies weapon/arts defs, character sheets/meta/inventory, positions/participants,
      scene fields, and relations.

    Returns the current WORLD snapshot for convenience.
    """
    if reset:
        reset_world()
    # Load tables
    story = load_story_config(selected_story_id)
    chars = load_characters()
    weapons = load_weapons() or {}
    arts = load_arts() or {}
    # Weapon/Arts defs
    try:
        set_weapon_defs(weapons)
    except Exception:
        pass
    try:
        set_arts_defs(arts)
    except Exception:
        pass
    # Characters: meta + stat block + inventory
    actor_entries: Dict[str, Any] = dict(chars or {})
    # Extract and remove relations from the character map for easier iteration
    relations_map = dict(actor_entries.pop("relations", {}) or {}) if isinstance(actor_entries, dict) else {}
    for nm, entry in actor_entries.items():
        if not isinstance(entry, dict):
            continue
        # type hint for agent orchestration (npc/player)
        try:
            tval = str((entry or {}).get("type", "npc")).lower()
            if tval:
                st = WORLD.characters.setdefault(str(nm), {})
                st["type"] = tval
        except Exception:
            pass
        # meta
        try:
            set_character_meta(
                nm,
                persona=entry.get("persona"),
                appearance=entry.get("appearance"),
                quotes=entry.get("quotes"),
            )
        except Exception:
            pass
        # sheet
        try:
            coc_block = entry.get("coc")
            if isinstance(coc_block, dict):
                set_coc_character_from_config(name=nm, coc=coc_block or {})
            else:
                set_coc_character(
                    name=nm,
                    characteristics={
                        "STR": 50,
                        "DEX": 50,
                        "CON": 50,
                        "INT": 50,
                        "POW": 50,
                        "APP": 50,
                        "EDU": 60,
                        "SIZ": 50,
                        "LUCK": 50,
                    },
                )
        except Exception:
            pass
        # inventory
        try:
            inv = entry.get("inventory") or {}
            if isinstance(inv, dict):
                for it, cnt in inv.items():
                    try:
                        grant_item(target=nm, item=str(it), n=int(cnt))
                    except Exception:
                        pass
        except Exception:
            pass
    # Positions and participants from story
    positions: Dict[str, Tuple[int, int]] = {}
    try:
        _parse_story_positions(story.get("initial_positions") or {}, positions)
    except Exception:
        pass
    try:
        _parse_story_positions(story.get("positions") or {}, positions)
    except Exception:
        pass
    try:
        initial = story.get("initial") if isinstance(story, dict) else None
        if isinstance(initial, dict):
            _parse_story_positions(initial.get("positions") or {}, positions)
    except Exception:
        pass
    for nm, (x, y) in positions.items():
        try:
            set_position(nm, x, y)
        except Exception:
            pass
    try:
        set_participants(list(positions.keys()))
    except Exception:
        pass
    # Relations from characters config top-level
    if isinstance(relations_map, dict):
        for src, mp in relations_map.items():
            if not isinstance(mp, dict):
                continue
            for dst, val in mp.items():
                try:
                    score = max(-100, min(100, int(val)))
                except Exception:
                    continue
                try:
                    set_relation(str(src), str(dst), score, reason="配置设定")
                except Exception:
                    pass
    # Scenes/Entrances (optional, minimal)
    try:
        sc_map = story.get("scenes") if isinstance(story, dict) else None
        if isinstance(sc_map, dict):
            WORLD.scenes = {str(k): dict(v or {}) for k, v in sc_map.items()}
    except Exception:
        pass
    try:
        ent_map = story.get("entrances") if isinstance(story, dict) else None
        if isinstance(ent_map, dict):
            WORLD.entrances = {str(k): dict(v or {}) for k, v in ent_map.items()}
    except Exception:
        pass
    # Events (optional, loaded into WORLD.events)
    try:
        ev_list = story.get("events") if isinstance(story, dict) else None
        if isinstance(ev_list, list):
            items = []
            for ev in ev_list:
                if not isinstance(ev, dict):
                    continue
                name = str(ev.get("name") or ev.get("id") or "(事件)")
                # Accept minutes in 'at' or time string in 'time' / 'time_min'
                at_val = ev.get("at")
                at_min = None
                try:
                    if at_val is not None:
                        at_min = int(at_val)
                except Exception:
                    at_min = None
                if at_min is None:
                    at_min = _parse_time_to_min(ev.get("time")) or _parse_time_to_min(ev.get("time_min"))
                if at_min is None:
                    # fallback: use current WORLD.time_min to avoid crashes
                    at_min = int(WORLD.time_min)
                note = str(ev.get("note") or ev.get("message") or "")
                effects = list(ev.get("effects") or []) if isinstance(ev.get("effects"), list) else []
                items.append({"name": name, "at": int(at_min), "note": note, "effects": effects})
            items.sort(key=lambda x: int(x.get("at", 0)))
            WORLD.events = items
    except Exception:
        pass
    # Endings (optional)
    try:
        ends = story.get("endings") if isinstance(story, dict) else None
        WORLD.endings_defs = _normalize_endings_list(ends)
        WORLD.ending_state = None
    except Exception:
        WORLD.endings_defs = []
        WORLD.ending_state = None
    try:
        init_scenes = story.get("initial_scenes") if isinstance(story, dict) else None
        if isinstance(init_scenes, dict):
            for nm, sc in init_scenes.items():
                if isinstance(sc, str) and sc.strip():
                    WORLD.scene_of[str(nm)] = sc.strip()
    except Exception:
        pass
    try:
        sp = story.get("scene_positions") if isinstance(story, dict) else None
        if isinstance(sp, dict):
            for scid, mp in sp.items():
                if not isinstance(mp, dict):
                    continue
                for nm, v in mp.items():
                    if isinstance(v, (list, tuple)) and len(v) >= 2:
                        try:
                            x, y = int(v[0]), int(v[1])
                        except Exception:
                            continue
                        try:
                            set_position(str(nm), x, y)
                        except Exception:
                            pass
                        # If actor has no scene set yet, inherit this scene id
                        try:
                            WORLD.scene_of.setdefault(str(nm), str(scid))
                        except Exception:
                            pass
    except Exception:
        pass

    # Scene from story (legacy single-scene header)
    sc = story.get("scene") if isinstance(story, dict) else None
    name, obj, det, weather, time_min = _normalize_scene_cfg(sc if isinstance(sc, dict) else None)
    if any([name, obj, det, weather, time_min is not None]):
        try:
            set_scene(
                name or (WORLD.location or ""),
                obj or None,
                append=False,
                details=det or None,
                weather=weather,
                time_min=time_min,
            )
        except Exception:
            pass
    # Do not expose a global snapshot; return minimal ack
    return {"ok": True}

# ---- Scene/Entrance helpers (minimal) ----

def set_scenes(defs: Dict[str, Dict[str, Any]]) -> ToolResponse:
    WORLD.scenes = {str(k): dict(v or {}) for k, v in (defs or {}).items()}
    WORLD._touch()
    return ToolResponse(content=[TextBlock(type="text", text=f"载入场景：{len(WORLD.scenes)} 项")], metadata={"ok": True, "count": len(WORLD.scenes)})


def set_entrances(defs: Dict[str, Dict[str, Any]]) -> ToolResponse:
    WORLD.entrances = {str(k): dict(v or {}) for k, v in (defs or {}).items()}
    WORLD._touch()
    return ToolResponse(content=[TextBlock(type="text", text=f"载入入口：{len(WORLD.entrances)} 项")], metadata={"ok": True, "count": len(WORLD.entrances)})


def _actor_scene(name: str) -> Optional[str]:
    s = WORLD.scene_of.get(str(name))
    if isinstance(s, str) and s:
        return s
    return None


def _scene_name(scene_id: str) -> str:
    sc = WORLD.scenes.get(str(scene_id), {}) if WORLD.scenes else {}
    return str(sc.get("name", scene_id))


def use_entrance(
    name: str,
    *,
    entrance: Optional[str] = None,
    reason: str = "",
) -> ToolResponse:
    """Use an entrance to change scene. Minimal behavior:

    - If not at the entrance tile, move towards it using remaining movement for this turn.
    - If after movement the actor is at the entrance tile, switch scene and place at spawn.
    - No door locks/hidden handling; choose by `entrance` id/label or by `to` scene.
    """
    nm = str(name)
    cur_scene = _actor_scene(nm)
    if not cur_scene:
        # Fallback: infer from WORLD.location when not set
        try:
            for sid, cfg in (WORLD.scenes or {}).items():
                if str(cfg.get("name", "")) == str(WORLD.location):
                    cur_scene = str(sid)
                    WORLD.scene_of[nm] = cur_scene
                    break
        except Exception:
            cur_scene = None
    # Resolve entrance candidate
    cand_id = None
    ent = None
    term = (entrance or "").strip()
    if term:
        # match by id first
        if term in (WORLD.entrances or {}):
            cand_id = term
            ent = WORLD.entrances.get(cand_id)
        else:
            # match by label within current scene
            for eid, e in (WORLD.entrances or {}).items():
                try:
                    if str(e.get("from_scene")) != str(cur_scene):
                        continue
                    if str(e.get("label", "")) == term:
                        cand_id = str(eid)
                        ent = e
                        break
                except Exception:
                    continue
    if ent is None:
        return ToolResponse(
            content=[TextBlock(type="text", text=f"未找到可用入口（from={cur_scene} term={term or '(未提供)'}）")],
            metadata={"ok": False, "error_type": "entrance_not_found", "from_scene": cur_scene, "entrance": entrance},
        )
    # Validate from_scene
    if cur_scene and str(ent.get("from_scene")) != str(cur_scene):
        return ToolResponse(
            content=[TextBlock(type="text", text=f"入口不在当前场景：{ent.get('label','')} 属于 {ent.get('from_scene')}。")],
            metadata={"ok": False, "error_type": "wrong_scene", "from_scene": cur_scene, "entrance_id": cand_id},
        )
    # Extract coordinates
    at = ent.get("at") or []
    if not (isinstance(at, (list, tuple)) and len(at) >= 2):
        return ToolResponse(content=[TextBlock(type="text", text=f"入口坐标无效：{cand_id}")], metadata={"ok": False, "error_type": "invalid_entrance"})
    ex, ey = int(at[0]), int(at[1])
    # Move towards if not yet there
    pos = WORLD.positions.get(nm)
    if pos is None:
        pos = (0, 0)
        WORLD.positions[nm] = pos
    if tuple(pos) != (ex, ey):
        mv = move_towards(nm, (ex, ey))
        meta = dict(mv.metadata or {})
        # If after movement we've arrived, fall through to enter
        pos2 = tuple(WORLD.positions.get(nm) or pos)
        if pos2 != (ex, ey):
            text = f"朝入口靠近：{ent.get('label','')}（剩余 {meta.get('remaining', _grid_distance(pos2, (ex,ey)))} 步）"
            blocks = list(mv.content or [])
            blocks.append(TextBlock(type="text", text=text))
            return ToolResponse(
                content=blocks,
                metadata={
                    "ok": True,
                    "status": "approaching",
                    "entrance_id": cand_id,
                    "entrance_label": ent.get("label"),
                    "from_scene": cur_scene,
                    "to_scene": ent.get("to_scene"),
                    "remaining_steps": meta.get("remaining", _grid_distance(pos2, (ex, ey))),
                },
            )
    # Enter and switch scene
    spawn = ent.get("spawn") or []
    try:
        sx, sy = int(spawn[0]), int(spawn[1])
    except Exception:
        sx, sy = 0, 0
    WORLD.scene_of[nm] = str(ent.get("to_scene", ""))
    set_position(nm, sx, sy)
    # Apply scene presentation if known
    dst_scene_id = str(ent.get("to_scene", ""))
    sc = WORLD.scenes.get(dst_scene_id, {}) if WORLD.scenes else {}
    try:
        set_scene(
            sc.get("name", dst_scene_id),
            details=(sc.get("details") if isinstance(sc.get("details"), list) else None),
            weather=sc.get("weather"),
            time=sc.get("time"),
        )
    except Exception:
        pass
    WORLD._touch()
    text = f"通过入口 {ent.get('label','')} 进入 {_scene_name(dst_scene_id)}"
    return ToolResponse(
        content=[TextBlock(type="text", text=text)],
        metadata={
            "ok": True,
            "status": "arrived",
            "entrance_id": cand_id,
            "entrance_label": ent.get("label"),
            "from_scene": cur_scene,
            "to_scene": dst_scene_id,
            "position": [sx, sy],
        },
    )


def _resolve_named_target_for_move(name: str, term: str) -> Optional[Tuple[Tuple[int, int], Dict[str, Any]]]:
    """Resolve a human-friendly target term into coordinates for movement.

    Resolution order (stop on first hit):
    - "X,Y" string with two integers -> (x, y)
    - Entrance label in the actor's current scene -> entrance.at
    - Entrance id (key in WORLD.entrances) -> entrance.at (must match from_scene if actor has one)
    - WORLD.objective_positions[name]
    - Another actor's current position (same-scene only when both sides have a scene)

    Returns ((x, y), meta) or None if not resolvable. Meta includes keys:
    { kind: 'coords'|'entrance'|'objective'|'actor', id/label?: str }
    """
    nm = str(name)
    s = (term or "").strip()
    if not s:
        return None
    # 1) "X,Y" literal
    m = re.match(r"^\s*([+-]?\d+)\s*,\s*([+-]?\d+)\s*$", s)
    if m:
        try:
            x, y = int(m.group(1)), int(m.group(2))
            return (x, y), {"kind": "coords"}
        except Exception:
            pass
    # Current scene for scoping entrances/actors
    cur_scene = _actor_scene(nm)
    # 2) Entrance by label in current scene
    for eid, e in (WORLD.entrances or {}).items():
        try:
            if cur_scene and str(e.get("from_scene")) != str(cur_scene):
                continue
            if str(e.get("label", "")) != s:
                continue
            at = e.get("at") or []
            x, y = int(at[0]), int(at[1])
            return (x, y), {"kind": "entrance", "id": str(eid), "label": str(e.get("label", ""))}
        except Exception:
            continue
    # 3) Entrance by id (respect from_scene if actor has one)
    if s in (WORLD.entrances or {}):
        try:
            e = WORLD.entrances.get(s) or {}
            if cur_scene and str(e.get("from_scene")) not in (str(cur_scene), "", "None"):
                pass  # wrong scene; fall through
            else:
                at = e.get("at") or []
                x, y = int(at[0]), int(at[1])
                return (x, y), {"kind": "entrance", "id": str(s), "label": str(e.get("label", ""))}
        except Exception:
            pass
    # 4) Objective position registry
    try:
        if s in (WORLD.objective_positions or {}):
            pos = WORLD.objective_positions.get(s)
            if isinstance(pos, (tuple, list)) and len(pos) >= 2:
                return (int(pos[0]), int(pos[1])), {"kind": "objective", "id": s}
    except Exception:
        pass
    # 5) Another actor by name (same-scene only when both scenes known)
    try:
        pos = (WORLD.positions or {}).get(s)
        if isinstance(pos, (tuple, list)) and len(pos) >= 2:
            sc_tgt = _actor_scene(str(s))
            if cur_scene and sc_tgt and str(cur_scene) != str(sc_tgt):
                return None
            return (int(pos[0]), int(pos[1])), {"kind": "actor", "id": s}
    except Exception:
        pass
    return None


def list_world_ids() -> List[str]:
    """Return available world ids from configs/story.json.

    - If the file is a container with `stories`, return sorted keys.
    - If it's a single-story object, return ["default"].
    - On read error, return [].
    """
    try:
        d = _load_json(_configs_dir() / "story.json")
        if isinstance(d.get("stories"), dict):
            return sorted(list((d.get("stories") or {}).keys()))
        return ["default"]
    except Exception:
        return []


def select_world(world_id: Optional[str] = None) -> dict:
    """Convenience wrapper to initialise world for a chosen id and return snapshot."""
    return init_world_from_configs(selected_story_id=world_id, reset=True)

# ---- Visibility helpers and environment rendering ----

def visible_snapshot_for(
    name: Optional[str], *, filter_to_scene: bool = True
) -> dict:
    """Return a filtered snapshot representing what `name` can see.

    - Always scoped to a scene; if无法解析角色场景且 filter_to_scene=True，则返回空结构。
    - 不提供全局快照路径。
    """
    # Resolve current scene id
    cur_scene_id: Optional[str] = None
    if name:
        s = (WORLD.scene_of or {}).get(str(name))
        if isinstance(s, str) and s:
            cur_scene_id = s
    if not cur_scene_id and not filter_to_scene:
        # Fallback to mapping location->scene when explicitly unscoped is requested
        try:
            loc = str(WORLD.location or "")
            for sid, cfg in (WORLD.scenes or {}).items():
                if str((cfg or {}).get("name", sid)) == loc:
                    cur_scene_id = sid
                    break
        except Exception:
            cur_scene_id = None

    if filter_to_scene and not cur_scene_id:
        # No scene resolved -> empty view
        return {
            "meta": {"scope": "scene", "scene_id": None},
            "positions": {},
            "characters": {},
            "participants": [],
            "scene_of": dict(WORLD.scene_of or {}),
            "location": WORLD.location,
        }

    # Build scene-scoped view
    scene_of = dict(WORLD.scene_of or {})
    keep: Set[str] = set()
    if cur_scene_id:
        for nm, sc in scene_of.items():
            if str(sc) == str(cur_scene_id):
                keep.add(str(nm))
    positions = {k: list(v) for k, v in (WORLD.positions or {}).items() if not cur_scene_id or str(k) in keep}
    characters = {k: dict(v or {}) for k, v in (WORLD.characters or {}).items() if not cur_scene_id or str(k) in keep}
    parts = [nm for nm in (WORLD.participants or []) if not cur_scene_id or str(nm) in keep]
    # Minimal refs for weapons/arts/inventory so UIs can render HUD
    out: Dict[str, Any] = {
        "meta": {"scope": "scene", "scene_id": str(cur_scene_id) if cur_scene_id else None},
        "time_min": WORLD.time_min,
        "weather": WORLD.weather,
        "location": WORLD.location,
        "scene_details": list(WORLD.scene_details or []),
        "objectives": list(WORLD.objectives or []),
        "objective_status": dict(WORLD.objective_status or {}),
        "positions": positions,
        "characters": characters,
        "participants": parts,
        "scene_of": scene_of,
        "weapon_defs": {wid: {
            "label": str((wd or {}).get("label", "")),
            "desc": str((wd or {}).get("desc") or (wd or {}).get("description", "")),
            "reach_steps": int((wd or {}).get("reach_steps", DEFAULT_REACH_STEPS)),
            "skill": str((wd or {}).get("skill", "")),
            "defense_skill": str((wd or {}).get("defense_skill", "")),
            "damage": str((wd or {}).get("damage", "")),
            "damage_type": str((wd or {}).get("damage_type", "physical")),
        } for wid, wd in (WORLD.weapon_defs or {}).items()},
        "inventory": dict(WORLD.inventory or {}),
        "scenes": {k: {"name": str((v or {}).get("name", k))} for k, v in (WORLD.scenes or {}).items()},
        "entrances": {eid: {
            "label": str((e or {}).get("label", "")),
            "from_scene": str((e or {}).get("from_scene", "")),
            "to_scene": str((e or {}).get("to_scene", "")),
            "at": (list((e or {}).get("at", [])) if isinstance((e or {}).get("at"), list) else None),
            "spawn": (list((e or {}).get("spawn", [])) if isinstance((e or {}).get("spawn"), list) else None),
            "desc": str((e or {}).get("desc") or (e or {}).get("description", "")),
        } for eid, e in (WORLD.entrances or {}).items()},
    }
    # Expose relations in a lightweight form: "A->B": score. Scope to current scene when applicable.
    try:
        rel_items = list((WORLD.relations or {}).items())
        rel_map: Dict[str, int] = {}
        for (a, b), v in rel_items:
            if cur_scene_id and not (str(a) in keep and str(b) in keep):
                continue
            try:
                rel_map[f"{a}->{b}"] = int(v)
            except Exception:
                continue
        out["relations"] = rel_map
    except Exception:
        pass
    return out


def render_env_for(
    name: Optional[str],
    *,
    filter_to_scene: bool = True,
    include_entrances: bool = True,
    max_entrances: int = 3,
    include_objectives: bool = True,
    show_positions: bool = True,
    show_chars: bool = True,
) -> ToolResponse:
    """Render a concise environment text for `name` suitable for prompt injection.

    The text mirrors the structure used by main._world_summary_text but scoped and
    sorted from the actor's perspective. Metadata includes scope/scene markers.
    """
    snap = visible_snapshot_for(name, filter_to_scene=filter_to_scene)
    try:
        t = int(snap.get("time_min", 0))
    except Exception:
        t = 0
    hh, mm = t // 60, t % 60
    weather = snap.get("weather", "unknown")
    location = snap.get("location", "未知")
    lines: List[str] = [f"现在：地点 {location}；时间 {hh:02d}:{mm:02d}；天气 {weather}"]
    # Details
    details = [d for d in (snap.get("scene_details") or []) if isinstance(d, str) and d.strip()]
    if details:
        lines.append("环境细节：" + "；".join(details))
    # Objectives
    if include_objectives:
        objectives = snap.get("objectives", []) or []
        obj_status = snap.get("objective_status", {}) or {}
        if objectives:
            s = "; ".join((f"{str(o)}({obj_status.get(str(o))})" if obj_status.get(str(o)) else str(o)) for o in objectives)
        else:
            s = "无"
        lines.append("目标：" + s)
    # Positions (sorted by distance; 'name' first)
    pos_map = dict((snap.get("positions") or {}))
    if show_positions and pos_map:
        items = list(pos_map.items())
        me = pos_map.get(str(name)) if name else None
        if me:
            mx, my = int(me[0]), int(me[1])
            def _dist_xy(xy: Any) -> int:
                try:
                    return abs(mx - int(xy[0])) + abs(my - int(xy[1]))
                except Exception:
                    return 10 ** 9
            items.sort(key=lambda kv: (0 if kv[0] == str(name) else 1, _dist_xy(kv[1]), kv[0]))
        pos_line = "; ".join(f"{nm}({xy[0]}, {xy[1]})" for nm, xy in items)
        lines.append("坐标：" + (pos_line if pos_line else "未记录"))
    # Characters (HP, dying/dead; sorted by distance)
    ch_map = dict((snap.get("characters") or {}))
    if show_chars and ch_map:
        entries: List[Tuple[str, str]] = []
        for nm, st in ch_map.items():
            hp = st.get("hp")
            max_hp = st.get("max_hp")
            if hp is None or max_hp is None:
                continue
            extra = ""
            try:
                dt = st.get("dying_turns_left", None)
                if dt is not None:
                    extra = f"（濒死{int(dt)}）"
                elif int(hp) <= 0:
                    extra = "（死亡）"
            except Exception:
                pass
            entries.append((str(nm), f"{nm}(HP {hp}/{max_hp}){extra}"))
        if entries:
            me_xy = pos_map.get(str(name)) if name else None
            if me_xy:
                def _dist_nm(nm: str) -> int:
                    xy = pos_map.get(nm)
                    if not xy:
                        return 10 ** 9
                    try:
                        return abs(int(xy[0]) - int(me_xy[0])) + abs(int(xy[1]) - int(me_xy[1]))
                    except Exception:
                        return 10 ** 9
                entries.sort(key=lambda t: (0 if t[0] == str(name) else 1, _dist_nm(t[0]), t[0]))
            lines.append("角色：" + "; ".join(txt for _, txt in entries))
        else:
            lines.append("角色：未登记")
    # Entrances (limited to current scene)
    if include_entrances:
        meta = dict(snap.get("meta") or {})
        cur_scene_id = meta.get("scene_id") if meta.get("scope") == "scene" else None
        scenes = snap.get("scenes", {}) or {}
        entrances = snap.get("entrances", {}) or {}
        me_xy = pos_map.get(str(name)) if name else None
        ents: List[Tuple[int, str]] = []
        for _, e in entrances.items():
            try:
                if cur_scene_id and str(e.get("from_scene", "")) != str(cur_scene_id):
                    continue
                label = str(e.get("label", ""))
                to_id = str(e.get("to_scene", ""))
                to_name = str((scenes.get(to_id, {}) or {}).get("name", to_id))
                at = e.get("at")
                steps = None
                if me_xy and isinstance(at, (list, tuple)) and len(at) >= 2:
                    try:
                        steps = abs(int(at[0]) - int(me_xy[0])) + abs(int(at[1]) - int(me_xy[1]))
                    except Exception:
                        steps = None
                if isinstance(at, (list, tuple)) and len(at) >= 2:
                    head = f"{label} @ ({int(at[0])},{int(at[1])})（通往{to_name}）"
                else:
                    head = f"{label}（通往{to_name}）"
                text = head + (f"，距你{steps}步" if steps is not None else "")
                ents.append((steps if steps is not None else 10 ** 9, text))
            except Exception:
                continue
        if ents:
            ents.sort(key=lambda t: (t[0], t[1]))
            lines.append("入口：" + "；".join([t[1] for t in ents[: max_entrances if max_entrances and max_entrances > 0 else 3]]))
    # Note: 已移除“其它场景：N 人”的汇总行，避免向模型暴露跨场景人数噪音。

    text = "\n".join(lines)
    md = {"ok": True, **(snap.get("meta") or {})}
    if name is not None:
        md["actor"] = str(name)
    return ToolResponse(content=[TextBlock(type="text", text=text)], metadata=md)


# ---- Reach preview rendering (scoped) ----

# Relation thresholds for categorization (keep in world to avoid UI coupling)
RELATION_INTIMATE_FRIEND = 60
RELATION_CLOSE_ALLY = 40
RELATION_ALLY = 10
RELATION_HOSTILE = -10
RELATION_ENEMY = -40
RELATION_ARCH_ENEMY = -60

def _relation_category(score: int) -> str:
    if score >= RELATION_INTIMATE_FRIEND:
        return "挚友"
    if score >= RELATION_CLOSE_ALLY:
        return "亲密同伴"
    if score >= RELATION_ALLY:
        return "盟友"
    if score <= RELATION_ARCH_ENEMY:
        return "死敌"
    if score <= RELATION_ENEMY:
        return "仇视"
    if score <= RELATION_HOSTILE:
        return "敌对"
    return "中立"

# Labels used in preview text
_REACH_RULE_LINE = "作战规则：只能对reach_preview的“可及目标”使用 perform_attack。"
_REACH_LABEL_ADJ = "相邻（≤1步）{tail}："
_REACH_LABEL_TARGETS = "可及武器（{weapon}，触及 {steps}步）可用目标："
_REACH_LABEL_ARTS = "可及术式（{art}，触及 {steps}步）可用目标："

def render_reach_preview_for(name: str) -> ToolResponse:
    """Render reach preview lines for `name` including adjacency, weapons and arts.

    - Scopes to current world; does not include entities from other scenes explicitly,
      but preview is inherently based on positions grid and inventory/known arts.
    - Includes one rule line on top to guide valid actions.
    """
    nm = str(name)
    lines: List[str] = [_REACH_RULE_LINE]

    # Scene scoping: only show units that are in the same scene as the actor.
    # If the actor's scene cannot be resolved, return only the rule line to avoid
    # leaking cross-scene targets/noise.
    cur_scene_id: Optional[str] = None
    try:
        sc = (WORLD.scene_of or {}).get(nm)
        if isinstance(sc, str) and sc:
            cur_scene_id = str(sc)
    except Exception:
        cur_scene_id = None
    keep: Set[str] = set()
    if cur_scene_id:
        try:
            for _nm, _sc in (WORLD.scene_of or {}).items():
                if str(_sc) == cur_scene_id:
                    keep.add(str(_nm))
        except Exception:
            keep = set()
    else:
        return ToolResponse(
            content=[TextBlock(type="text", text="\n".join(lines))],
            metadata={"ok": True, "actor": nm, "scene_id": None},
        )
    # Relation lookup: nm->other
    rel_map: Dict[str, int] = {}
    try:
        for (a, b), v in (WORLD.relations or {}).items():
            if str(a) == nm and str(b) != nm:
                try:
                    rel_map[str(b)] = int(v)
                except Exception:
                    continue
    except Exception:
        rel_map = {}

    def _fmt_steps(n: int) -> str:
        try:
            s = int(n)
        except Exception:
            s = 0
        if s < 0:
            s = 0
        return f"{s}步"

    def _rel_cat(sc: Optional[int]) -> Optional[str]:
        if sc is None:
            return None
        try:
            return _relation_category(int(sc))
        except Exception:
            return None

    def _fmt_with_rel(nm2: str, steps: int) -> str:
        tag = _rel_cat(rel_map.get(str(nm2)))
        return f"{nm2}({_fmt_steps(steps)}; {tag})" if tag else f"{nm2}({_fmt_steps(steps)})"

    # Adjacent units (≤1 step)
    try:
        adj = list(list_adjacent_units(nm))
    except Exception:
        adj = []
    # Filter adjacency to same-scene units only
    if keep:
        adj = [(n, d) for n, d in adj if n in keep]
    if adj:
        try:
            react_avail = bool(reaction_available(nm))
        except Exception:
            react_avail = True
        tail = "（反应：可用）" if react_avail else "（反应：已用）"
        parts = [_fmt_with_rel(n, d) for n, d in adj]
        lines.append(_REACH_LABEL_ADJ.format(tail=tail) + ", ".join(parts))

    # Weapons preview
    inv = dict((WORLD.inventory or {}).get(nm, {}) or {})
    wdefs = dict(WORLD.weapon_defs or {})
    weapons: List[Tuple[str, int]] = []
    for wid, cnt in inv.items():
        try:
            if int(cnt) <= 0:
                continue
        except Exception:
            continue
        wid_str = str(wid)
        if wid_str not in wdefs:
            continue
        try:
            rsteps = int((wdefs[wid_str] or {}).get("reach_steps", 1))
        except Exception:
            rsteps = 1
        weapons.append((wid_str, max(1, rsteps)))
    weapons.sort(key=lambda t: (t[1], t[0]))
    for wid, rsteps in weapons:
        try:
            items = list(reachable_targets_for_weapon(nm, wid))
        except Exception:
            items = []
        # Filter weapon targets to same-scene units only
        if keep and items:
            items = [(n, d) for n, d in items if n in keep]
        if not items:
            continue
        parts = [_fmt_with_rel(n, d) for n, d in items]
        try:
            desc = str((wdefs.get(wid) or {}).get("desc") or "")
        except Exception:
            desc = ""
        label_line = _REACH_LABEL_TARGETS.format(weapon=wid, steps=int(rsteps))
        if desc:
            head = label_line.replace("可用目标：", "")
            lines.append(head + "：" + desc)
            lines.append("可用目标：" + ", ".join(parts))
        else:
            lines.append(label_line + ", ".join(parts))

    # Arts preview
    try:
        # Use world state directly for known arts; preview text itself is scene-scoped via `keep`
        ch = dict((WORLD.characters or {}).get(nm, {}) or {})
        known = list((ch.get("coc") or {}).get("arts_known") or [])
        arts_defs = get_arts_defs() if callable(get_arts_defs) else {}
        for aid in known:
            a = (arts_defs or {}).get(str(aid)) or {}
            rsteps = int(a.get("range_steps", 6) or 6)
            try:
                items = list(reachable_targets_for_art(nm, str(aid)))
            except Exception:
                items = []
            # Filter arts targets to same-scene units only
            if keep and items:
                items = [(n, d) for n, d in items if n in keep]
            if not items:
                continue
            parts = [_fmt_with_rel(n, d) for n, d in items]
            desc = str((a or {}).get("desc") or "")
            label_line = _REACH_LABEL_ARTS.format(art=str(aid), steps=int(rsteps))
            if desc:
                head = label_line.replace("可用目标：", "")
                lines.append(head + "：" + desc)
                lines.append("可用目标：" + ", ".join(parts))
            else:
                lines.append(label_line + ", ".join(parts))
    except Exception:
        pass

    text = "\n".join(lines)
    return ToolResponse(content=[TextBlock(type="text", text=text)], metadata={"ok": True, "actor": nm})

# ---- Query helpers (pure data; no narration) ----
def reaction_available(name: str) -> bool:
    """Return whether the actor still has their Reaction available this round.

    Defaults to True when turn_state is uninitialised to keep preview permissive.
    """
    try:
        st = WORLD.turn_state.get(str(name), {})
        return bool(st.get("reaction_available", True))
    except Exception:
        return True


def list_adjacent_units(name: str) -> List[Tuple[str, int]]:
    """Return units within 1 step (Manhattan) of `name` as (unit, steps).

    - Excludes self; ignores participants gating (consistent with prior preview).
    - Returns a list sorted by (steps, name).
    """
    me = WORLD.positions.get(str(name))
    if not (isinstance(me, tuple) or isinstance(me, list)):
        return []
    mx, my = int(me[0]), int(me[1])
    out: List[Tuple[str, int]] = []
    for nm, pos in (WORLD.positions or {}).items():
        if str(nm) == str(name):
            continue
        if not (isinstance(pos, tuple) or isinstance(pos, list)):
            continue
        try:
            d = abs(mx - int(pos[0])) + abs(my - int(pos[1]))
        except Exception:
            continue
        if d <= 1:
            out.append((str(nm), int(d)))
    out.sort(key=lambda t: (t[1], t[0]))
    return out


def reachable_targets_for_weapon(attacker: str, weapon: str) -> List[Tuple[str, int]]:
    """Return targets within weapon reach (steps) for `attacker`.

    - Requires attacker position and weapon definition; if attacker lacks the
      weapon in inventory (count <= 0), returns empty list (consistent with preview).
    - Ignores participants gating and guard interception by design (preview only).
    - Returns list sorted by (steps, name).
    """
    att = str(attacker)
    pos_a = WORLD.positions.get(att)
    if not (isinstance(pos_a, tuple) or isinstance(pos_a, list)):
        return []
    wid = str(weapon)
    wdef = (WORLD.weapon_defs or {}).get(wid)
    if not isinstance(wdef, dict):
        return []
    try:
        reach_steps = max(1, int(wdef.get("reach_steps", DEFAULT_REACH_STEPS)))
    except Exception:
        reach_steps = int(DEFAULT_REACH_STEPS)
    # Ownership gate for preview (match main's previous behavior)
    bag = dict(WORLD.inventory.get(att, {}) or {})
    try:
        if int(bag.get(wid, 0)) <= 0:
            return []
    except Exception:
        return []
    ax, ay = int(pos_a[0]), int(pos_a[1])
    out: List[Tuple[str, int]] = []
    for nm, pos in (WORLD.positions or {}).items():
        if str(nm) == att:
            continue
        if not (isinstance(pos, tuple) or isinstance(pos, list)):
            continue
        try:
            d = abs(ax - int(pos[0])) + abs(ay - int(pos[1]))
        except Exception:
            continue
        if d <= reach_steps:
            out.append((str(nm), int(d)))
    out.sort(key=lambda t: (t[1], t[0]))
    return out


def reachable_targets_for_art(attacker: str, art: str) -> List[Tuple[str, int]]:
    """Return targets within art range (steps) for `attacker`.

    - Uses arts_defs.range_steps; ignores LOS/participants/guards (preview only).
    - Returns list sorted by (steps, name).
    """
    att = str(attacker)
    pos_a = WORLD.positions.get(att)
    if not (isinstance(pos_a, tuple) or isinstance(pos_a, list)):
        return []
    ad = (WORLD.arts_defs or {}).get(str(art)) or {}
    try:
        rng = max(1, int(ad.get("range_steps", 6)))
    except Exception:
        rng = 6
    ax, ay = int(pos_a[0]), int(pos_a[1])
    out: List[Tuple[str, int]] = []
    for nm, pos in (WORLD.positions or {}).items():
        if str(nm) == att:
            continue
        if not (isinstance(pos, tuple) or isinstance(pos, list)):
            continue
        try:
            d = abs(ax - int(pos[0])) + abs(ay - int(pos[1]))
        except Exception:
            continue
        if d <= rng:
            out.append((str(nm), int(d)))
    out.sort(key=lambda t: (t[1], t[0]))
    return out


# ---- World-level rule queries used by engine orchestration ----
def is_dead(name: Optional[str]) -> bool:
    """Return True if the character is dead (hp<=0 and not in dying)."""
    if not name:
        return False
    try:
        st = WORLD.characters.get(str(name), {})
        hp = int(st.get("hp", 0) if st else 0)
        dying = st.get("dying_turns_left") is not None
        return (hp <= 0) and (not dying)
    except Exception:
        return False


def hostiles_present(participants: Optional[List[str]] = None, threshold: int = -10) -> bool:
    """Return True if there exists a hostile pair (relation<=threshold) among living actors.

    - Candidate set priority: participants if provided; else those with positions; else all characters.
    - Living: hp > 0（濒死也视为不“存活”以匹配原主循环用于战斗继续性的语义）。
    - Relations source: WORLD.relations (tuple keys (a,b)).
    """
    # Resolve field names
    if participants:
        names = [str(n) for n in participants]
    else:
        pos_keys = list((WORLD.positions or {}).keys())
        if pos_keys:
            names = [str(n) for n in pos_keys]
        else:
            names = [str(n) for n in (WORLD.characters or {}).keys()]
    # Filter living (hp>0)
    live = []
    for nm in names:
        try:
            st = WORLD.characters.get(str(nm), {})
            if int(st.get("hp", 1)) > 0:
                live.append(str(nm))
        except Exception:
            live.append(str(nm))
    if len(live) <= 1:
        return False
    # Build relation lookup
    rel = dict(WORLD.relations or {})
    thr = int(threshold)
    for i, a in enumerate(live):
        for b in live[i + 1 :]:
            try:
                sc_ab = int(rel.get((a, b), 0))
            except Exception:
                sc_ab = 0
            try:
                sc_ba = int(rel.get((b, a), 0))
            except Exception:
                sc_ba = 0
            if sc_ab <= thr or sc_ba <= thr:
                return True
    return False

def reset_world() -> None:
    """Reset the global WORLD to a fresh, empty instance.

    Used by server restarts to guarantee a clean state across sessions.
    """
    global WORLD
    WORLD = World()

def set_participants(names: List[str]) -> ToolResponse:
    """Replace the participants list with the given ordered names.

    Stores only strings; preserves order and removes empty/dupes while keeping first occurrence.
    """
    seq: List[str] = []
    seen = set()
    for n in list(names or []):
        s = str(n).strip()
        if not s or s in seen:
            continue
        seen.add(s)
        seq.append(s)
    WORLD.participants = seq
    WORLD._touch()
    return ToolResponse(content=[TextBlock(type="text", text="参与者设定：" + (", ".join(seq) if seq else "(无)"))], metadata={"ok": True, "participants": list(seq)})


def set_character_meta(
    name: str,
    *,
    persona: Optional[str] = None,
    appearance: Optional[str] = None,
    quotes: Optional[Union[List[str], str]] = None,
) -> ToolResponse:
    """Set human-facing meta info for a character (persona/appearance/quotes).

    These fields live with the character sheet for agent prompting purposes.
    """
    nm = str(name)
    sheet = WORLD.characters.setdefault(nm, {})
    if persona is not None:
        p = str(persona).strip()
        if p:
            sheet["persona"] = p
    if appearance is not None:
        a = str(appearance).strip()
        if a:
            sheet["appearance"] = a
    if quotes is not None:
        if isinstance(quotes, (list, tuple)):
            sheet["quotes"] = [str(q).strip() for q in quotes if str(q).strip()]
        else:
            q = str(quotes).strip()
            if q:
                sheet["quotes"] = q
    WORLD._touch()
    return ToolResponse(
        content=[TextBlock(type="text", text=f"设定角色元信息：{nm}")],
        metadata={"ok": True, **{k: sheet.get(k) for k in ("persona", "appearance", "quotes")}},
    )

def advance_time(mins: int):
    """Advance in-game time by a number of minutes.

    Args:
        mins: Minutes to advance (positive integer).

    Returns:
        dict: { ok: bool, time_min: int }
    """
    WORLD.time_min += int(mins)
    WORLD._touch()
    res = {"ok": True, "time_min": WORLD.time_min}
    blocks = [TextBlock(type="text", text=f"时间推进 {int(mins)} 分钟，当前时间(分钟)={WORLD.time_min}")]
    # Auto process events due
    try:
        ev = process_events()
        if ev and ev.content:
            blocks.extend(ev.content)
    except Exception:
        pass
    return ToolResponse(content=blocks, metadata={"ok": True, **res})


def change_relation(a: str, b: str, delta: int, reason: str = ""):
    """Adjust relation score between two characters.

    Args:
        a: Character A name.
        b: Character B name.
        delta: Relation change (can be negative).
        reason: Optional description for auditing.

    Returns:
        dict: { ok: bool, pair: [str,str], score: int, reason: str }
    """
    k = _rel_key(a, b)
    WORLD.relations[k] = WORLD.relations.get(k, 0) + int(delta)
    WORLD._touch()
    res = {"ok": True, "pair": list(k), "score": WORLD.relations[k], "reason": reason}
    return ToolResponse(
        content=[TextBlock(type="text", text=f"关系调整 {k[0]}->{k[1]}：{int(delta)}，当前分数={WORLD.relations[k]}。理由：{reason}")],
        metadata={"ok": True, **res},
    )


def set_relation(a: str, b: str, value: int, reason: str = "初始化") -> ToolResponse:
    k = _rel_key(a, b)
    WORLD.relations[k] = int(value)
    WORLD._touch()
    res = {"ok": True, "pair": list(k), "score": WORLD.relations[k], "reason": reason}
    return ToolResponse(
        content=[TextBlock(type="text", text=f"关系设定 {k[0]}->{k[1]} = {WORLD.relations[k]}。理由：{reason}")],
        metadata={"ok": True, **res},
    )


def grant_item(target: str, item: str, n: int = 1):
    """Give items to a target's inventory.

    Args:
        target: Target name (NPC/player).
        item: Item id or name.
        n: Quantity to add (default 1).

    Returns:
        dict: { ok: bool, target: str, item: str, count: int }
    """
    bag = WORLD.inventory.setdefault(target, {})
    bag[item] = bag.get(item, 0) + int(n)
    WORLD._touch()
    res = {"ok": True, "target": target, "item": item, "count": bag[item]}
    return ToolResponse(
        content=[TextBlock(type="text", text=f"给予 {target} 物品 {item} x{int(n)}，现有数量={bag[item]}")],
        metadata={"ok": True, **res},
    )


def set_position(name: str, x: int, y: int) -> ToolResponse:
    """Set or update the grid position of an actor."""
    # Note: position can still be updated externally (e.g., shove/push). We do not
    # block here for dying/dead, because forced movement is allowed. Voluntary
    # movement is gated in move_towards().
    WORLD.positions[str(name)] = (int(x), int(y))
    WORLD._touch()
    return ToolResponse(
        content=[TextBlock(type="text", text=f"设定 {name} 位置 -> ({int(x)}, {int(y)})")],
        metadata={"ok": True, "name": name, "position": [int(x), int(y)]},
    )


def set_guard(guardian: str, protectee: str) -> ToolResponse:
    """Register a protection link: `guardian` will attempt to intercept attacks against `protectee`.

    - Order is preserved; duplicates are ignored.
    - Interception rules are enforced at attack time.
    """
    g = str(guardian)
    blocked, msg = _blocked_action(g, "action")
    if blocked:
        return ToolResponse(
            content=[TextBlock(type="text", text=msg)],
            metadata={"ok": False, "error_type": "attacker_unable", "actor": g}
        )
    p = str(protectee)
    lst = WORLD.guardians.setdefault(p, [])
    if g not in lst:
        lst.append(g)
        WORLD._touch()
    return ToolResponse(
        content=[TextBlock(type="text", text=f"守护：{g} -> {p}")],
        metadata={"ok": True, "protectee": p, "guardians": list(lst), "added": g},
    )


def clear_guard(guardian: Optional[str] = None, protectee: Optional[str] = None) -> ToolResponse:
    """Clear protection links.

    - guardian=None & protectee=None: clear all
    - guardian=None & protectee= P: clear all guardians of P
    - guardian= G & protectee=None: remove G from all protectees
    - guardian= G & protectee= P: remove only G protecting P
    """
    g = guardian if guardian is None else str(guardian)
    p = protectee if protectee is None else str(protectee)
    changed = 0
    if g is None and p is None:
        changed = sum(len(v) for v in WORLD.guardians.values())
        WORLD.guardians.clear()
        WORLD._touch()
        return ToolResponse(content=[TextBlock(type="text", text=f"已清空所有守护关系（{changed} 条）")], metadata={"ok": True, "cleared": changed})
    if p is not None and g is None:
        lst = WORLD.guardians.pop(p, [])
        changed = len(lst)
        if changed:
            WORLD._touch()
        return ToolResponse(content=[TextBlock(type="text", text=f"已清除 {p} 的全部守护（{changed} 名）")], metadata={"ok": True, "protectee": p, "cleared": changed})
    if g is not None and p is None:
        removed = 0
        for key in list(WORLD.guardians.keys()):
            lst = WORLD.guardians.get(key, [])
            if not lst:
                continue
            if g in lst:
                lst = [x for x in lst if x != g]
                removed += 1
                if lst:
                    WORLD.guardians[key] = lst
                else:
                    WORLD.guardians.pop(key, None)
        if removed:
            WORLD._touch()
        return ToolResponse(content=[TextBlock(type="text", text=f"已将 {g} 从所有守护中移除（涉及 {removed} 名被保护者）")], metadata={"ok": True, "guardian": g, "affected": removed})
    # both provided
    lst = WORLD.guardians.get(p, [])
    if g in lst:
        lst = [x for x in lst if x != g]
        if lst:
            WORLD.guardians[p] = lst
        else:
            WORLD.guardians.pop(p, None)
        changed = 1
    if changed:
        WORLD._touch()
    return ToolResponse(content=[TextBlock(type="text", text=f"已移除守护：{g} -> {p}")], metadata={"ok": True, "removed": changed, "protectee": p, "guardian": g})


def get_position(name: str) -> ToolResponse:
    pos = WORLD.positions.get(str(name))
    if pos is None:
        return ToolResponse(
            content=[TextBlock(type="text", text=f"未记录 {name} 的坐标")],
            metadata={"found": False},
        )
    return ToolResponse(
        content=[TextBlock(type="text", text=f"{name} 当前位置：({pos[0]}, {pos[1]})")],
        metadata={"found": True, "position": list(pos)},
    )


def set_objective_position(name: str, x: int, y: int) -> ToolResponse:
    WORLD.objective_positions[str(name)] = (int(x), int(y))
    WORLD._touch()
    return ToolResponse(
        content=[TextBlock(type="text", text=f"目标 {name} 坐标设为 ({int(x)}, {int(y)})")],
        metadata={"ok": True, "name": name, "position": [int(x), int(y)]},
    )


# Removed hidden-enemy utilities by request: use explicit participants/relations only.


def _grid_distance(a: Tuple[int, int], b: Tuple[int, int]) -> int:
    """Manhattan distance in steps (4-way). Used by movement logic.

    Keep this for movement semantics to remain 4-directional.
    """
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


## L∞-style (diagonal=1) distance helpers removed: project enforces Manhattan (L1) only.


def get_distance_steps_between(name_a: str, name_b: str) -> Optional[int]:
    """Return grid steps between two actors; None if any position missing or not in the same scene.

    Minimal multi-scene rule: distance is only defined within the same scene.
    """
    # Cross-scene: undefined distance
    try:
        sa = WORLD.scene_of.get(str(name_a))
        sb = WORLD.scene_of.get(str(name_b))
        if sa is not None and sb is not None and str(sa) != str(sb):
            return None
    except Exception:
        pass
    pa = WORLD.positions.get(str(name_a))
    pb = WORLD.positions.get(str(name_b))
    if pa is None or pb is None:
        return None
    return _grid_distance(pa, pb)


## Legacy L∞ helper removed: use get_distance_steps_between (Manhattan) instead.


# Removed meter-based distance helper; use steps only (get_distance_steps_between).


def _resolve_guard_interception(attacker: str, defender: str, reach_steps: int) -> tuple[str, Optional[Dict[str, Any]], List[TextBlock]]:
    """Resolve protection interception.

    Rules (as confirmed by user):
    - Guardian must be adjacent (<=1 step) to protectee.
    - Consumes the guardian's Reaction (one per round).
    - If multiple guardians are eligible, choose the one closest to the attacker;
      ties break by registration order.
    - Applies to all attacks that check reach/range by steps; guardian must also
      be within the attacker's current reach (steps) for the interception to hold.
    - No auto cleanup; explicit clear only.

    Returns: (final_defender, guard_meta or None, pre_logs)
    """
    protectee = str(defender)
    guardians = list(WORLD.guardians.get(protectee, []) or [])
    if not guardians:
        return defender, None, []

    # Build candidate list with computed distances
    cand = []  # (distance_attacker_to_guardian, order_index, guardian)
    for idx, g in enumerate(guardians):
        g = str(g)
        # must be alive
        if not _is_alive(g):
            continue
        # adjacency to protectee (Manhattan distance)
        d_gp = get_distance_steps_between(g, protectee)
        if d_gp is None or d_gp > 1:
            continue
        # reaction available
        st = WORLD.turn_state.get(g, {})
        if not st.get("reaction_available", True):
            continue
        # attacker must be within reach vs guardian as well (Manhattan)
        d_ag = get_distance_steps_between(attacker, g)
        if d_ag is None or d_ag > int(reach_steps):
            continue
        cand.append((int(d_ag), idx, g))

    if not cand:
        return defender, None, []

    # choose by nearest to attacker (ascending), tiebreaker by registration order (ascending idx)
    cand.sort(key=lambda t: (t[0], t[1]))
    chosen = None
    for _, _, g in cand:
        # spend reaction; if cannot, try next
        resp = use_action(str(g), "reaction")
        ok = bool((resp.metadata or {}).get("ok", False))
        if ok:
            chosen = str(g)
            break
    if not chosen:
        return defender, None, []

    pre = [TextBlock(type="text", text=f"{chosen} 保护 {protectee}，消耗反应，挡在其前，成为被攻击目标。")]
    meta = {"protector": chosen, "protected": protectee, "used_reaction": True}
    return chosen, meta, pre


def _band_for_steps(steps: int) -> str:
    if steps <= 1:
        return "engaged"
    if steps <= 6:
        return "near"
    if steps <= 12:
        return "far"
    return "long"


"""Range bands removed: engaged/near/far/long classification no longer maintained."""


def get_move_speed_steps(name: str) -> int:
    """Return walking speed (steps/turn), derived from CoC if missing in cache.

    - Ignores any sheet-level `move_speed_steps` field (已废弃显式指定)。
    - If not cached, derive from CoC characteristics on demand.
    - Falls back to global default only when无法派生（无 CoC 面板）。
    """
    # If not cached, try derive from CoC on the fly (无其他规则/回退)
    if name not in WORLD.speeds:
        st = WORLD.characters.get(name, {})
        if isinstance(st.get("coc"), dict):
            try:
                derive_move_speed_steps(name)
            except Exception:
                pass
    return int(WORLD.speeds.get(name, _default_move_steps()))


def derive_move_speed_steps(name: str) -> ToolResponse:
    """按 CoC 7e 规则从角色数值派生移动力（步/回合），并写入缓存。

    只保留 CoC 方案：
    - 基础 MOV=8；若 DEX>SIZ 且 STR>SIZ → 9；若 DEX<SIZ 且 STR<SIZ → 7；否则 8。
    - 步数 = round(MOV/1.5)，并限制在 [3,10]。
    - 将 {MOV, move_steps, move_rule='coc7e'} 写回到 coc.derived。
    - 已移除“显式指定移动力”的优先级，始终以派生为准（除非外部直接修改 WORLD.speeds）。
    """
    nm = str(name)
    st = WORLD.characters.setdefault(nm, {})
    coc = dict(st.get("coc") or {})
    ch = {k.upper(): int(v) for k, v in (coc.get("characteristics") or {}).items()}
    if not ch:
        # 无 CoC 面板时不做其他回退，直接报错信息
        return ToolResponse(
            content=[TextBlock(type="text", text=f"速度派生失败：{nm} 缺少 CoC 特性（characteristics）")],
            metadata={"ok": False, "error_type": "no_coc_characteristics", "name": nm},
        )
    dex = int(ch.get("DEX", 50))
    str_v = int(ch.get("STR", 50))
    siz = int(ch.get("SIZ", 50))
    mov = 8
    if dex > siz and str_v > siz:
        mov = 9
    elif dex < siz and str_v < siz:
        mov = 7
    steps_calc = int(round(float(mov) / 1.5))
    steps = max(3, min(10, steps_calc))
    # Persist into CoC derived block for transparency
    try:
        derived = dict((coc.get("derived") or {}))
        derived.update({"MOV": int(mov), "move_steps": int(steps), "move_rule": "coc7e"})
        coc["derived"] = derived
        st["coc"] = coc
    except Exception:
        pass
    WORLD.speeds[nm] = int(steps)
    WORLD._touch()
    note = f"{nm} MOV {mov} => {steps}步/回合"
    return ToolResponse(
        content=[TextBlock(type="text", text=f"速度派生：{note}")],
        metadata={"ok": True, "name": nm, "speed_steps": int(steps), "rule": "coc"},
    )


def derive_all_speeds_from_stats() -> ToolResponse:
    """按 CoC 方案为所有已知角色重算并缓存步数，返回汇总。"""
    content: List[TextBlock] = []
    out_map: Dict[str, int] = {}
    for nm in list(WORLD.characters.keys()):
        try:
            res = derive_move_speed_steps(nm)
            if res and isinstance(res.metadata, dict):
                out_map[nm] = int(res.metadata.get("speed_steps", get_move_speed_steps(nm)))
            if res and res.content:
                # keep individual lines concise
                content.extend(res.content)
        except Exception:
            pass
    return ToolResponse(content=content, metadata={"ok": True, "speeds": out_map, "rule": "coc"})


def get_reach_steps(name: str) -> int:
    """Deprecated: kept for backward-compat in tests only.

    New flow should pass reach via weapon defs. This function now only returns
    a project-wide default when character sheet lacks explicit reach_steps.
    """
    sheet = WORLD.characters.get(name, {})
    try:
        val = sheet.get("reach_steps")
        if val is not None:
            return max(1, int(val))
    except Exception:
        pass
    return max(1, int(DEFAULT_REACH_STEPS))


def move_towards(name: str, target: Tuple[int, int], steps: Optional[int] = None, target_label: Optional[str] = None, target_kind: Optional[str] = None) -> ToolResponse:
    """Move an actor toward target grid using available movement.

    - If `steps` is None, use remaining movement this turn (turn_state.move_left);
      if not initialized for this actor, fall back to their move speed steps.
    - Movement cannot exceed the available movement for this call; leftover
      movement for the turn is reduced accordingly.
    - Voluntary movement is blocked for dying/dead actors (unchanged behavior).
    """
    if WORLD.participants and str(name) not in WORLD.participants:
        pos = WORLD.positions.get(str(name)) or (0, 0)
        return ToolResponse(
            content=[TextBlock(type="text", text=f"参与者限制：仅当前场景参与者可主动移动。")],
            metadata={"ok": False, "moved": 0, "position": list(pos), "error_type": "not_participant"},
        )
    # Gate voluntary movement by system/control statuses
    pos = WORLD.positions.get(str(name)) or (0, 0)
    blocked, msg = _blocked_action(str(name), "move")
    if blocked:
        return ToolResponse(
            content=[TextBlock(type="text", text=msg)],
            metadata={
                "ok": False,
                "error_type": "attacker_unable",
                "moved": 0,
                "position": list(pos),
                "blocked": True,
                "actor": str(name),
            },
        )
    # Determine how many steps are allowed for this move
    nm = str(name)
    ts = WORLD.turn_state.setdefault(nm, {})
    try:
        default_steps = int(WORLD.speeds.get(nm, _default_move_steps()))
    except Exception:
        default_steps = _default_move_steps()
    try:
        left = int(ts.get("move_left", default_steps))
    except Exception:
        left = default_steps

    if steps is None:
        steps_eff = left
    else:
        try:
            steps_eff = int(steps)
        except Exception:
            steps_eff = 0
    steps = max(0, int(min(max(0, steps_eff), max(0, left))))
    if steps == 0:
        pos = WORLD.positions.get(str(name)) or (0, 0)
        return ToolResponse(
            content=[TextBlock(type="text", text=f"{name} 保持在 ({pos[0]}, {pos[1]})，未移动。")],
            metadata={"ok": True, "moved": 0, "position": list(pos)},
        )
    current = WORLD.positions.get(str(name))
    if current is None:
        current = WORLD.positions[str(name)] = (0, 0)
    x, y = current
    tx, ty = int(target[0]), int(target[1])
    moved = 0
    while moved < steps and (x, y) != (tx, ty):
        if x != tx:
            x += 1 if tx > x else -1
        elif y != ty:
            y += 1 if ty > y else -1
        moved += 1
    WORLD.positions[str(name)] = (x, y)
    # Deduct movement for this turn
    try:
        st_left = int(ts.get("move_left", default_steps))
        ts["move_left"] = max(0, st_left - int(moved))
    except Exception:
        # Be defensive; do not fail movement due to token accounting
        ts["move_left"] = max(0, int(default_steps) - int(moved))
    remaining = _grid_distance((x, y), (tx, ty))
    reached = (x, y) == (tx, ty)
    # Render: include friendly label when provided (e.g., entrance/actor/objective)
    label_prefix = f"{str(target_label)} " if (target_label or "").strip() else ""
    text = (
        f"{name} 向 {label_prefix}({tx}, {ty}) 移动 {format_distance_steps(moved)}，现位于 ({x}, {y})。"
        + (" 已抵达目标。" if reached else f" 距目标还差 {format_distance_steps(remaining)}。")
    )
    WORLD._touch()
    return ToolResponse(
        content=[TextBlock(type="text", text=text)],
        metadata={
            "ok": True,
            "moved": moved,
            "reached": reached,
            "remaining": remaining,
            "position": [x, y],
            "moved_steps": moved,
            "remaining_steps": remaining,
            "target_label": (str(target_label).strip() or None),
            "target_kind": (str(target_kind).strip() if target_kind else None),
        },
    )


# describe_world has been removed by design. Use visible_snapshot_for(None, filter_to_scene=False)
# and let higher layers render any human-readable summary.


def set_scene(
    location: str,
    objectives: Optional[List[str]] = None,
    append: bool = False,
    *,
    time_min: Optional[int] = None,
    time: Optional[str] = None,
    weather: Optional[str] = None,
    details: Optional[Union[str, List[str]]] = None,
):
    """Set the current scene and optionally update objectives/time/weather/details.

    Args:
        location: 新地点描述
        objectives: 目标列表；append=True 时为追加，否则替换
        append: 是否在现有目标后追加
        time_min: 以分钟表示的时间
        time: 字符串时间 "HH:MM"（若提供则优先生效）
        weather: 天气文本
        details: 细节文本或文本列表
    """
    WORLD.location = str(location)
    if objectives is not None:
        items = list(objectives)
        if append:
            WORLD.objectives.extend(items)
        else:
            WORLD.objectives = items
        for o in items:
            WORLD.objective_status[str(o)] = WORLD.objective_status.get(str(o), "pending")
    # Optional updates: weather
    if weather is not None:
        w = str(weather).strip()
        if w:
            WORLD.weather = w
    # Optional updates: time (prefer HH:MM string if provided)
    if isinstance(time, str) and time:
        s = time.strip()
        try:
            hh_str, mm_str = s.split(":")
            hh, mm = int(hh_str), int(mm_str)
            if 0 <= hh < 24 and 0 <= mm < 60:
                WORLD.time_min = hh * 60 + mm
        except Exception:
            pass
    elif time_min is not None:
        try:
            WORLD.time_min = max(0, int(time_min))
        except Exception:
            pass
    # Optional updates: scene details
    if details is not None:
        vals: List[str] = []
        if isinstance(details, str):
            s = details.strip()
            if s:
                vals = [s]
        elif isinstance(details, list):
            for d in details:
                if isinstance(d, (str, int, float)):
                    s = str(d).strip()
                    if s:
                        vals.append(s)
        WORLD.scene_details = vals
    WORLD._touch()
    text = f"设定场景：{WORLD.location}；目标：{'; '.join(WORLD.objectives) if WORLD.objectives else '(无)'}"
    return ToolResponse(content=[TextBlock(type="text", text=text)], metadata={"ok": True, "location": WORLD.location, "time_min": WORLD.time_min, "weather": WORLD.weather})


def add_objective(obj: str):
    """Append a single objective into the world's objectives list."""
    name = str(obj)
    WORLD.objectives.append(name)
    WORLD.objective_status[name] = WORLD.objective_status.get(name, "pending")
    text = f"新增目标：{name}"
    return ToolResponse(content=[TextBlock(type="text", text=text)], metadata={"objectives": list(WORLD.objectives), "status": dict(WORLD.objective_status)})


def _coc_dex_of(name: str) -> int:
    st = WORLD.characters.get(name, {})
    coc = dict(st.get("coc") or {})
    try:
        return int((coc.get("characteristics") or {}).get("DEX", 50))
    except Exception:
        return 50


def set_speed(name: str, value: float = DEFAULT_MOVE_SPEED_STEPS, unit: str = "steps"):
    """(禁用显式设定) 移动力现由 CoC 数值自动派生，禁止手动设定。

    保留函数以保持 API 兼容，但不再修改 WORLD.speeds。
    返回 ok=False 与提示信息。
    """
    return ToolResponse(
        content=[TextBlock(type="text", text=f"速度设定被禁用：{name} 的移动力由 CoC 派生，仅可通过数值变动间接影响。")],
        metadata={"ok": False, "error_type": "disabled", "name": str(name), "reason": "speed_derived_from_coc"},
    )


def compute_action_order(participants: Optional[List[str]] = None, policy: str = "dex") -> ToolResponse:
    """Compute an action order without mutating WORLD state.

    - Default policy 'dex': order by CoC DEX descending; tie-breaker by name.
    - Filters out dead actors to avoid unusable turns.
    - Returns ToolResponse(metadata={"ok", "order", "scores", "policy"}).
    """
    # Determine input names
    if participants is None:
        base: List[str] = (
            list(WORLD.participants)
            if WORLD.participants
            else list(WORLD.characters.keys())
        )
    else:
        base = list(participants)
    names = [n for n in base if _is_alive(n)]

    scores: Dict[str, int] = {}
    if str(policy).lower() == "dex":
        for nm in names:
            scores[nm] = _coc_dex_of(nm)
        # Deterministic: sort by (DEX desc, name asc)
        ordered = sorted(names, key=lambda n: (scores.get(n, 0), str(n)), reverse=True)
    else:
        # Unknown policy -> fallback to name order
        for nm in names:
            scores[nm] = 0
        ordered = sorted(names)

    txt = "顺序：" + ", ".join(f"{n}({scores.get(n, 0)})" for n in ordered)
    return ToolResponse(
        content=[TextBlock(type="text", text=txt)],
        metadata={"ok": True, "order": ordered, "scores": scores, "policy": str(policy)},
    )


def roll_initiative(participants: Optional[List[str]] = None):
    """Compatibility wrapper: compute initiative order without side effects.

    Previous behavior mutated WORLD to enter combat and reset tokens. This
    implementation is intentionally side-effect-free and only returns the
    calculated order and scores.
    """
    res = compute_action_order(participants=participants, policy="dex")
    # Align metadata keys with historical callers (initiative -> order)
    meta = dict(res.metadata or {})
    ordered = list(meta.get("order") or [])
    scores = dict(meta.get("scores") or {})
    txt = "先攻：" + ", ".join(f"{n}({scores.get(n, 0)})" for n in ordered)
    return ToolResponse(
        content=[TextBlock(type="text", text=txt)],
        metadata={"ok": True, "initiative": ordered, "scores": scores, "policy": meta.get("policy", "dex")},
    )



def rotation_for_focus(
    protagonists: Optional[List[str]] = None,
    *,
    policy: str = "dex",
    same_scene: bool = True,
    include_types: Tuple[str, ...] = ("npc", "player"),
    include_dying: bool = True,
    mutate: bool = True,
) -> ToolResponse:
    """Compute the per-round rotation list anchored by the player (主角) scene.

    - Focus scene: prefer the first `player`'s scene; if none, map WORLD.location to scene id.
    - Filter: by scene (when `same_scene=True`), by type (npc/player), and by life state
      (exclude only true deaths; keep dying when `include_dying=True`).
    - Order: reuse `compute_action_order` (DEX desc, then name asc).
    - mutate=True: write the result into WORLD.participants for orchestrator consumption.

    Returns ToolResponse with metadata {ok, order, scores, policy, focus_scene, candidates}.
    """
    # Resolve protagonist list; default to the first player in participants/positions/characters order
    protos: List[str] = []
    if protagonists:
        for n in protagonists:
            s = str(n).strip()
            if s:
                protos.append(s)
    if not protos:
        # deterministic base order: participants -> positions -> characters
        base = (
            list(WORLD.participants)
            if WORLD.participants
            else (list(WORLD.positions.keys()) if WORLD.positions else list(WORLD.characters.keys()))
        )
        for nm in base:
            tval = str((WORLD.characters.get(str(nm), {}) or {}).get("type", "npc")).lower()
            if tval == "player":
                protos.append(str(nm))
                break

    # Determine focus scene id
    scene_map = dict(WORLD.scene_of or {})
    focus_scene: Optional[str] = None
    for p in protos:
        sc = scene_map.get(str(p))
        if isinstance(sc, str) and sc:
            focus_scene = sc
            break
    if not focus_scene:
        # Fallback: map WORLD.location to a scene id
        try:
            loc = str(WORLD.location or "")
            for sid, cfg in (WORLD.scenes or {}).items():
                if str((cfg or {}).get("name", sid)) == loc:
                    focus_scene = str(sid)
                    break
        except Exception:
            focus_scene = None

    # Build candidate list
    # Candidate base: use all known characters to allow newcomers in the focus scene
    # to be added into rotation even if they were not in previous participants.
    base_names = list((WORLD.characters or {}).keys())
    candidates: List[str] = []
    for nm in base_names:
        name = str(nm)
        # type filter
        tval = str((WORLD.characters.get(name, {}) or {}).get("type", "npc")).lower()
        if tval not in include_types:
            continue
        # scene filter
        if same_scene and focus_scene and scene_map.get(name) != focus_scene:
            continue
        # life filter
        if include_dying:
            if is_dead(name):
                continue
        else:
            try:
                st = WORLD.characters.get(name, {}) or {}
                if int(st.get("hp", 1)) <= 0:
                    continue
            except Exception:
                pass
        candidates.append(name)

    # Order by policy (default: DEX)
    res = compute_action_order(participants=candidates, policy=policy)
    meta = dict(res.metadata or {})
    order = list(meta.get("order") or [])

    if mutate:
        try:
            set_participants(order)
        except Exception:
            pass

    out_meta = {
        "ok": True,
        "order": order,
        "scores": dict(meta.get("scores") or {}),
        "policy": meta.get("policy", policy),
        "focus_scene": focus_scene,
        "candidates": list(candidates),
    }
    return ToolResponse(
        content=[TextBlock(type="text", text="轮转：" + (", ".join(order) if order else "(无)"))],
        metadata=out_meta,
    )


## end_combat removed: world does not own combat lifecycle


 # World no longer tracks current-actor pointer; orchestrator owns scheduling


def _is_alive(name: Optional[str]) -> bool:
    """Return True if the character is alive (hp>0).

    A missing sheet is treated as alive to avoid accidental soft-locks.
    """
    if not name:
        return False
    try:
        st = WORLD.characters.get(str(name), {})
        hp = int(st.get("hp", 1))
        return hp > 0
    except Exception:
        # Be permissive; if we cannot determine, assume alive
        return True


def _is_dying(name: Optional[str]) -> bool:
    """Return True if character is in dying state (dying_turns_left present)."""
    if not name:
        return False
    try:
        st = WORLD.characters.get(str(name), {})
        return st.get("dying_turns_left") is not None
    except Exception:
        return False

def _reset_turn_tokens_for(name: Optional[str]):
    if not name:
        return
    spd = int(WORLD.speeds.get(name, _default_move_steps()))
    WORLD.turn_state[name] = {
        "action_used": False,
        "bonus_used": False,
        "reaction_available": True,
        "move_left": spd,
        "disengage": False,
        "help_target": None,
        "ready": None,  # {trigger: str, action: dict}
    }
    # Note: legacy 'dodge' condition/token removed; no per-turn cleanup needed.


## next_turn removed: orchestrator schedules actors


## get_turn removed: orchestrator owns turn context


def reset_actor_turn(name: str) -> ToolResponse:
    """Reset per-turn tokens for the given actor, regardless of combat mode.

    This aligns the per-回合资源（移动/动作/反应）与 Host 的普通轮转一致，
    不再依赖战斗状态或先攻顺序。
    """
    nm = str(name)
    _reset_turn_tokens_for(nm)
    st = dict(WORLD.turn_state.get(nm, {}))
    WORLD._touch()
    return ToolResponse(
        content=[TextBlock(type="text", text=f"[系统] {nm} 回合资源重置")],
        metadata={"ok": True, "name": nm, "state": st},
    )


def use_action(name: str, kind: str = "action") -> ToolResponse:
    nm = str(name)
    st = WORLD.turn_state.setdefault(nm, {})
    if kind == "action":
        if st.get("action_used"):
            return ToolResponse(content=[TextBlock(type="text", text=f"[已用] {nm} 本回合动作已用完")], metadata={"ok": False, "error_type": "resource_spent", "kind": kind})
        st["action_used"] = True
        WORLD._touch()
        return ToolResponse(content=[TextBlock(type="text", text=f"{nm} 使用 动作")], metadata={"ok": True})
    if kind == "bonus":
        if st.get("bonus_used"):
            return ToolResponse(content=[TextBlock(type="text", text=f"[已用] {nm} 本回合附赠动作已用完")], metadata={"ok": False, "error_type": "resource_spent", "kind": kind})
        st["bonus_used"] = True
        WORLD._touch()
        return ToolResponse(content=[TextBlock(type="text", text=f"{nm} 使用 附赠动作")], metadata={"ok": True})
    if kind == "reaction":
        if not st.get("reaction_available", True):
            return ToolResponse(content=[TextBlock(type="text", text=f"[已用] {nm} 本轮反应不可用")], metadata={"ok": False, "error_type": "resource_spent", "kind": kind})
        st["reaction_available"] = False
        WORLD._touch()
        return ToolResponse(content=[TextBlock(type="text", text=f"{nm} 使用 反应")], metadata={"ok": True})
    return ToolResponse(content=[TextBlock(type="text", text=f"未知动作类型 {kind}")], metadata={"ok": False, "error_type": "unknown_action"})


def consume_movement(name: str, distance_steps: float) -> ToolResponse:
    """Spend movement measured in grid steps."""

    nm = str(name)
    st = WORLD.turn_state.setdefault(nm, {})
    default_steps = int(WORLD.speeds.get(nm, _default_move_steps()))
    left = int(st.get("move_left", default_steps))
    steps = int(math.ceil(max(0.0, float(distance_steps))))
    if steps <= 0:
        return ToolResponse(
            content=[TextBlock(type="text", text=f"{nm} 不移动")],
            metadata={"ok": True, "left_steps": left},
        )
    if steps > left:
        st["move_left"] = 0
        return ToolResponse(
            content=[TextBlock(type="text", text=f"{nm} 试图移动 {format_distance_steps(steps)}，但仅剩 {format_distance_steps(left)}；按剩余移动结算")],
            metadata={"ok": False, "error_type": "insufficient_movement", "left_steps": 0, "attempted_steps": steps},
        )
    st["move_left"] = left - steps
    return ToolResponse(
        content=[TextBlock(type="text", text=f"{nm} 移动 {format_distance_steps(steps)}（剩余 {format_distance_steps(st['move_left'])}）")],
        metadata={"ok": True, "left_steps": st["move_left"], "spent_steps": steps},
    )


## auto_move_into_reach removed: attacks no longer auto-move into reach.


"""Range band system removed: engaged/near/far/long not maintained nor exposed."""


def set_cover(name: str, level: str):
    level = str(level)
    if level not in ("none", "half", "three_quarters", "total"):
        return ToolResponse(content=[TextBlock(type="text", text=f"未知掩体等级 {level}")], metadata={"ok": False, "error_type": "invalid_value", "param": "level", "value": level})
    WORLD.cover[str(name)] = level
    return ToolResponse(content=[TextBlock(type="text", text=f"掩体：{name} -> {level}")], metadata={"ok": True, "name": name, "cover": level})


def get_cover(name: str) -> str:
    return WORLD.cover.get(str(name), "none")


# ---- Unified status management ----
def _statuses_for(name: str) -> Dict[str, Dict[str, Any]]:
    """Internal: return mutable status dict for a character.

    Structure: { state_name: {"remaining": Optional[int], "kind": str, "source": Optional[str], "data": dict} }
    - kind: 'system' | 'control'
    - remaining: number of actor-turn ticks left; None means indefinite
    """
    # Reuse WORLD.conditions container for compatibility, but store structured entries.
    d = WORLD.conditions.setdefault(str(name), set())
    # If legacy set encountered, convert to empty dict (we no longer use string-sets)
    if isinstance(d, set):
        WORLD.conditions[str(name)] = {}
    if not isinstance(WORLD.conditions.get(str(name)), dict):
        WORLD.conditions[str(name)] = {}
    return WORLD.conditions[str(name)]  # type: ignore[return-value]


def add_status(name: str, state: str, *, duration_rounds: Optional[int] = None, kind: str = "control", source: Optional[str] = None, data: Optional[Dict[str, Any]] = None) -> ToolResponse:
    st = _statuses_for(str(name))
    st[str(state)] = {
        "remaining": (int(duration_rounds) if duration_rounds is not None else None),
        "kind": str(kind),
        "source": (str(source) if source is not None else None),
        "data": dict(data or {}),
    }
    return ToolResponse(content=[TextBlock(type="text", text=f"状态：{name} +{state}{f'（{duration_rounds}轮）' if duration_rounds else ''}")], metadata={"ok": True, "name": name, "state": state, "remaining": st[str(state)]["remaining"], "kind": kind})


def remove_status(name: str, state: str) -> ToolResponse:
    st = _statuses_for(str(name))
    if str(state) in st:
        st.pop(str(state), None)
    return ToolResponse(content=[TextBlock(type="text", text=f"状态：{name} -{state}")], metadata={"ok": True, "name": name, "state": state})


def has_status(name: str, state: str) -> bool:
    st = _statuses_for(str(name))
    return str(state) in st


def list_statuses(name: str) -> Dict[str, Dict[str, Any]]:
    return dict(_statuses_for(str(name)))


def _tick_control_statuses(name: str) -> List[TextBlock]:
    """Decrement per-turn duration for control statuses of `name`; remove expired.

    Returns a list of text blocks describing expirations.
    """
    out: List[TextBlock] = []
    st = _statuses_for(str(name))
    expired: List[str] = []
    for k, info in list(st.items()):
        try:
            if str(info.get("kind")) != "control":
                continue
            rem = info.get("remaining")
            if rem is None:
                continue
            rem2 = int(rem) - 1
            info["remaining"] = rem2
            if rem2 <= 0:
                expired.append(k)
        except Exception:
            # be defensive: remove malformed entry
            expired.append(k)
    for k in expired:
        st.pop(k, None)
        out.append(TextBlock(type="text", text=f"状态结束：{name} -{k}"))
    return out


def _blocked_action(name: str, action: str) -> Tuple[bool, str]:
    """Return (blocked, message) if `name` cannot perform `action`.

    Actions: 'move' | 'attack' | 'cast' | 'dash' | 'disengage' | 'help' | 'first_aid' | 'action'
    """
    nm = str(name)
    act = str(action)
    # System gating: dying/dead
    st = WORLD.characters.get(nm, {})
    try:
        hp_now = int(st.get("hp", 0)) if st else 0
    except Exception:
        hp_now = 0
    if st.get("dying_turns_left") is not None:
        # Block specific actions with tailored message
        lab = _ACTION_LABEL.get(act, "行动")
        # Dying: block move/attack/cast by design
        if act in ("move", "attack", "cast", "dash", "disengage", "action"):
            return True, f"{nm} 处于濒死状态，无法{lab}。"
    if hp_now <= 0:
        if act in ("move", "attack", "cast", "dash", "disengage", "action"):
            lab = _ACTION_LABEL.get(act, "行动")
            return True, f"{nm} 已倒地，无法{lab}。"
    # Control gating: check unified statuses
    try:
        sts = list_statuses(nm)
    except Exception:
        sts = {}
    for k, info in (sts or {}).items():
        rule = CONTROL_STATUS_RULES.get(str(k).lower())
        if not rule:
            continue
        blocks = set(rule.get("blocks", set()))
        if "all" in blocks or act in blocks or (act != "move" and "action" in blocks):
            lab = _ACTION_LABEL.get(act, "行动")
            return True, f"{nm} 处于{k}状态，无法{lab}。"
    return False, ""


def get_action_restrictions(name: str) -> Dict[str, bool]:
    """Return a dict of action -> blocked for the given actor.

    Keys: move, attack, cast, action
    """
    out = {}
    for act in ("move", "attack", "cast", "action"):
        b, _ = _blocked_action(str(name), act)
        out[act] = bool(b)
    return out


def queue_trigger(kind: str, payload: Optional[Dict[str, Any]] = None):
    WORLD.triggers.append({"kind": str(kind), "payload": dict(payload or {})})
    return ToolResponse(content=[TextBlock(type="text", text=f"触发：{kind}")], metadata={"queued": len(WORLD.triggers)})


def pop_triggers() -> List[Dict[str, Any]]:
    out = list(WORLD.triggers)
    WORLD.triggers.clear()
    return out


# DnD遗留移除：不再提供 AC/掩体加值/优势相关接口。


# ---- Standard actions (thin wrappers) ----
def act_hide(name: str, dc: int = 13):
    # CoC: Perform Stealth check; ignore DC, use skill value.
    # State system trimmed: no longer applies 'hidden' condition.
    nm = str(name)
    blocked, msg = _blocked_action(nm, "action")
    if blocked:
        return ToolResponse(content=[TextBlock(type="text", text=msg)], metadata={"ok": False, "error_type": "attacker_unable"})
    res = skill_check_coc(nm, "Stealth")
    success = bool((res.metadata or {}).get("success"))
    out = list(res.content or [])
    return ToolResponse(content=out, metadata={"ok": success})


def act_search(name: str, skill: str = "Perception", dc: int = 50):
    # CoC: generic skill check; DC is ignored (percentile system)
    return skill_check_coc(str(name), str(skill))


def contest(a: str, a_skill: str, b: str, b_skill: str) -> ToolResponse:
    """CoC opposed check with dying short-circuit.

    - If either side is dying, skip rolls: non-dying side wins automatically.
    - Else compare success levels; tie breaks by lower roll wins; if still tied, defender wins.
    """
    # Dying short-circuit
    if _is_dying(a) and not _is_dying(b):
        return ToolResponse(content=[TextBlock(type="text", text=f"对抗跳过：{a} 濒死，{b} 自动胜")], metadata={"winner": b, "skip_reason": "attacker_dying"})
    if _is_dying(b) and not _is_dying(a):
        return ToolResponse(content=[TextBlock(type="text", text=f"对抗跳过：{b} 濒死，{a} 自动胜")], metadata={"winner": a, "skip_reason": "defender_dying"})
    if _is_dying(a) and _is_dying(b):
        return ToolResponse(content=[TextBlock(type="text", text=f"对抗跳过：双方均濒死，判 {b} 胜")], metadata={"winner": b, "skip_reason": "both_dying"})

    # Regular opposed check
    ar = skill_check_coc(a, a_skill)
    br = skill_check_coc(b, b_skill)
    a_meta = ar.metadata or {}
    b_meta = br.metadata or {}
    def _lvl(m):
        return {"extreme": 3, "hard": 2, "regular": 1, "fail": 0}.get(str(m.get("success_level", "fail")), 0)
    la, lb = _lvl(a_meta), _lvl(b_meta)
    if la != lb:
        winner = a if la > lb else b
    else:
        ra = int(a_meta.get("roll", 101) or 101)
        rb = int(b_meta.get("roll", 101) or 101)
        if ra != rb:
            winner = a if ra < rb else b
        else:
            winner = b  # exact tie favors defender
    text = f"对抗：{a}({a_skill})[{a_meta.get('success_level','fail')}] vs {b}({b_skill})[{b_meta.get('success_level','fail')}] -> {winner} 胜"
    return ToolResponse(content=[TextBlock(type="text", text=text)], metadata={"a": a_meta, "b": b_meta, "winner": winner})


"""act_dash/act_disengage/act_help/act_grapple/act_ready 已删除：避免 DnD 动作命名残留。"""


# ---- Character/stat tools ----
def set_character(name: str, hp: int, max_hp: int):
    """Create/update a character with hp and max_hp."""
    WORLD.characters[name] = {"hp": int(hp), "max_hp": int(max_hp)}
    return ToolResponse(
        content=[TextBlock(type="text", text=f"设定角色 {name}：HP {int(hp)}/{int(max_hp)}")],
        metadata={"name": name, "hp": int(hp), "max_hp": int(max_hp)},
    )


# ================= CoC 7e support (percentile) =================
def _coc7_hp_max(con: int, siz: int) -> int:
    """Compute CoC 7e HP Max from percentile CON/SIZ.

    Formula (7e): floor((CON + SIZ) / 10), min 1.
    """
    try:
        con_i = int(con)
    except Exception:
        con_i = 0
    try:
        siz_i = int(siz)
    except Exception:
        siz_i = 0
    val = (max(0, con_i) + max(0, siz_i)) // 10
    return max(1, int(val))


def set_coc_character(
    name: str,
    *,
    characteristics: Dict[str, int],
    skills: Optional[Dict[str, int]] = None,
    terra: Optional[Dict[str, Any]] = None,
) -> ToolResponse:
    """Create/update a CoC 7e character and derive HP by CoC 7e rule.

    Input characteristics are percentile scores like {STR, CON, DEX, INT, POW, APP, EDU, SIZ, LUCK}.
    HP Max = floor((CON + SIZ) / 10), at least 1. Starts at full HP.
    Also derives basic SAN/MP if POW present; leaves others to callers.
    """
    nm = str(name)
    char = {k.upper(): int(v) for k, v in (characteristics or {}).items()}
    con = int(char.get("CON", 0))
    siz = int(char.get("SIZ", 0))
    hp_max = _coc7_hp_max(con, siz)
    # Start at full HP/MP
    hp_now = int(hp_max)
    pow_v = int(char.get("POW", 0))
    mp_cap = max(0, pow_v // 5) if pow_v > 0 else 0
    # Deriveds recorded inside CoC block for transparency
    derived = {"hp": hp_max}
    if pow_v > 0:
        derived.update({"san": pow_v, "mp": mp_cap})
    sheet = WORLD.characters.setdefault(nm, {})
    sheet.update(
        {
            "hp": hp_now,
            "max_hp": hp_max,
            "coc": {
                "characteristics": char,
                "derived": derived,
                **({"skills": {k: int(v) for k, v in (skills or {}).items()}} if skills else {}),
                **({"terra": dict(terra)} if terra else {}),
            },
        }
    )
    # Top-level MP numeric resource (for quick access and combat math)
    try:
        sheet["max_mp"] = mp_cap
        # Only set current mp to full if missing; avoid clobbering existing values
        if "mp" not in sheet or sheet.get("mp") is None:
            sheet["mp"] = mp_cap
    except Exception:
        pass
    # Clear any dying flag when creating a fresh sheet
    sheet.pop("dying_turns_left", None)
    # Derive default walking speed from CoC stats（显式指定已废弃，始终派生）
    try:
        derive_move_speed_steps(nm)
    except Exception:
        pass
    WORLD._touch()
    return ToolResponse(
        content=[
            TextBlock(
                type="text",
                text=f"设定(CoC) {nm}：HP {hp_now}/{hp_max}（公式：floor((CON+SIZ)/10)）",
            )
        ],
        metadata={"ok": True, "name": nm, "hp": hp_now, "max_hp": hp_max},
    )


def recompute_coc_derived(name: str) -> ToolResponse:
    """Recompute CoC derived values (HP, SAN/MP if POW present) from stored characteristics.

    Safe no-op if the character has no CoC block.
    """
    nm = str(name)
    st = WORLD.characters.get(nm, {})
    coc = dict(st.get("coc") or {})
    if not coc:
        return ToolResponse(content=[], metadata={"ok": False, "error_type": "no_coc_block", "name": nm})
    ch = {k.upper(): int(v) for k, v in (coc.get("characteristics") or {}).items()}
    con = int(ch.get("CON", 0))
    siz = int(ch.get("SIZ", 0))
    hp_max = _coc7_hp_max(con, siz)
    # Keep current damage by preserving ratio of current to old max, but clamp to new max.
    try:
        old_max = int(st.get("max_hp", hp_max))
        old_hp = int(st.get("hp", hp_max))
        ratio = (old_hp / old_max) if old_max > 0 else 1.0
    except Exception:
        ratio = 1.0
    new_hp = min(hp_max, max(0, int(math.floor(hp_max * max(0.0, float(ratio))))))
    # Update top-level and coc.derived
    st["max_hp"] = hp_max
    st["hp"] = new_hp
    pow_v = int(ch.get("POW", 0))
    derived = dict(coc.get("derived") or {})
    derived.update({"hp": hp_max})
    if pow_v > 0:
        derived.update({"san": pow_v, "mp": max(0, pow_v // 5)})
    coc["derived"] = derived
    st["coc"] = coc
    WORLD.characters[nm] = st
    # Sync top-level MP caps; keep current mp but clamp to new max
    try:
        mp_cap = max(0, int(pow_v // 5))
        st["max_mp"] = mp_cap
        cur_mp = int(st.get("mp", mp_cap))
        st["mp"] = max(0, min(mp_cap, cur_mp))
    except Exception:
        pass
    WORLD._touch()
    return ToolResponse(
        content=[TextBlock(type="text", text=f"重算(CoC)：{nm} HP {new_hp}/{hp_max}")],
        metadata={"ok": True, "name": nm, "hp": new_hp, "max_hp": hp_max},
    )


def set_coc_character_from_config(name: str, coc: Dict[str, Any]) -> ToolResponse:
    """Normalize a `coc` dict from config and persist all known fields.

    Recognised blocks:
      - characteristics: percentile stats (STR/DEX/...)
      - skills: mapping of skill -> value
      - terra: nested Terra attachments (infection/protection/...)
    Any other top-level keys under the `coc` block (e.g., `arts_known`) are
    preserved verbatim on the stored character sheet at `characters[name].coc`.
    This keeps authoring flexible without requiring engine changes per field.
    """
    d = dict(coc or {})
    # Extract primary blocks
    chars = d.get("characteristics")
    if not isinstance(chars, dict):
        # Allow flat layout fallback for ability-like keys
        chars = {k: v for k, v in d.items() if isinstance(v, (int, float)) and str(k).isupper()}
    skills = d.get("skills") if isinstance(d.get("skills"), dict) else None
    terra = d.get("terra") if isinstance(d.get("terra"), dict) else None

    # Create/update the base CoC sheet first
    res = set_coc_character(
        name=name,
        characteristics={k: int(v) for k, v in (chars or {}).items()},
        skills=skills,
        terra=terra,
    )

    # Preserve additional fields (e.g., arts_known) under the coc block
    extras = {k: v for k, v in d.items() if k not in ("characteristics", "skills", "terra")}
    if extras:
        st = WORLD.characters.setdefault(str(name), {})
        coc_st = dict(st.get("coc") or {})
        for k, v in extras.items():
            coc_st[k] = v
        st["coc"] = coc_st
        WORLD._touch()
    # Derive default walking speed after ingesting full CoC block（始终派生）
    try:
        derive_move_speed_steps(str(name))
    except Exception:
        pass
    return res


# ---- Oripathy / infection track (Terra-CoC glue) ----

def _infection_stage_floor(stage: int) -> int:
    """Return minimum stress value for a given infection stage."""
    s = int(stage)
    if s <= 0:
        return 0
    if s == 1:
        return 20
    if s == 2:
        return 50
    return 80


def _ensure_infection_block(name: str) -> Dict[str, Any]:
    """Return normalized infection block for `name`, creating defaults if needed."""
    nm = str(name)
    st = WORLD.characters.setdefault(nm, {})
    coc = st.setdefault("coc", {})
    terra = coc.setdefault("terra", {})
    inf = terra.setdefault("infection", {})
    try:
        stage = max(0, min(3, int(inf.get("stage", 0))))
    except Exception:
        stage = 0
    try:
        stress = max(0, int(inf.get("stress", 0)))
    except Exception:
        stress = 0
    try:
        cd = max(0, int(inf.get("crystal_density", 0)))
    except Exception:
        cd = 0
    # Clamp stress to current stage floor (doc: 普通恢复不会低于阶段下限)
    floor = _infection_stage_floor(stage)
    if stress < floor:
        stress = floor
    inf.update({"stage": stage, "stress": stress, "crystal_density": cd})
    terra["infection"] = inf
    coc["terra"] = terra
    st["coc"] = coc
    return inf


def get_infection_state(name: str) -> ToolResponse:
    """Return current infection track for `name`."""
    nm = str(name)
    inf = _ensure_infection_block(nm)
    floor = _infection_stage_floor(int(inf.get("stage", 0)))
    return ToolResponse(
        content=[
            TextBlock(
                type="text",
                text=(
                    f"{nm} 感染轨道：阶段 {inf.get('stage', 0)}，应激 {inf.get('stress', 0)}"
                    f"（阶段下限 {floor}），结晶密度 {inf.get('crystal_density', 0)}"
                ),
            )
        ],
        metadata={"ok": True, "name": nm, "infection": dict(inf), "stage_floor": floor},
    )


def _infection_resist_target(name: str, bonus: int = 0) -> Tuple[int, Dict[str, Any]]:
    """Compute infection resist target for `name` and return (target, meta)."""
    nm = str(name)
    st = WORLD.characters.get(nm, {})
    coc = dict((st or {}).get("coc") or {})
    ch = {k.upper(): int(v) for k, v in (coc.get("characteristics") or {}).items()}
    con_v = int(ch.get("CON", 50))
    pow_v = int(ch.get("POW", 50))
    half_sum = int(round((con_v + pow_v) / 2.0))
    terra = dict(coc.get("terra") or {})
    arts = dict(terra.get("arts") or {})
    # Terra sheet value; fall back to skill default if absent
    try:
        arts_resist_sheet = int(arts.get("resist", 0))
    except Exception:
        arts_resist_sheet = 0
    if arts_resist_sheet <= 0:
        try:
            arts_resist_sheet = int(_coc_skill_value(nm, "Arts_Resist"))
        except Exception:
            arts_resist_sheet = 40
    base = max(arts_resist_sheet, half_sum)
    inf = _ensure_infection_block(nm)
    stage = int(inf.get("stage", 0))
    stage_penalty = {0: 0, 1: 10, 2: 20, 3: 30}.get(stage, 0)
    tgt = max(1, int(base + int(bonus) - stage_penalty))
    meta = {
        "con": con_v,
        "pow": pow_v,
        "half_con_pow": half_sum,
        "arts_resist_sheet": arts_resist_sheet,
        "base": base,
        "bonus": int(bonus),
        "stage": stage,
        "stage_penalty": stage_penalty,
        "target": tgt,
    }
    return tgt, meta


def advance_infection_stage(name: str, choice: str = "auto") -> ToolResponse:
    """Advance infection stage by 1 (up to 3) and apply long-term effects.

    choice:
      - 'con': 体能衰退，CON -5
      - 'resist': 术式抗性下降，arts.resist -10
      - 'affinity': 术式亲和上升，arts.affinity +5（并记标记供过载规则使用）
      - 'auto': 当前实现中等同于 'con'
    """
    import math as _math

    nm = str(name)
    st = WORLD.characters.setdefault(nm, {})
    coc = st.setdefault("coc", {})
    terra = coc.setdefault("terra", {})
    inf = _ensure_infection_block(nm)
    old_stage = int(inf.get("stage", 0))
    if old_stage >= 3:
        return ToolResponse(
            content=[TextBlock(type="text", text=f"{nm} 感染阶段已达 3（晚期），无法继续提升。")],
            metadata={"ok": False, "name": nm, "stage": old_stage, "error_type": "stage_max"},
        )
    new_stage = min(3, old_stage + 1)
    inf["stage"] = new_stage
    inf["crystal_density"] = int(inf.get("crystal_density", 0)) + 1
    floor = _infection_stage_floor(new_stage)
    try:
        cur_stress = int(inf.get("stress", 0))
    except Exception:
        cur_stress = 0
    if cur_stress < floor:
        cur_stress = floor
    inf["stress"] = cur_stress
    # Long-term effect
    ch = {k.upper(): int(v) for k, v in (coc.get("characteristics") or {}).items()}
    arts = dict(terra.get("arts") or {})
    choice_norm = str(choice or "auto").lower()
    if choice_norm not in ("con", "resist", "affinity"):
        choice_norm = "con"
    logs: List[TextBlock] = []
    if choice_norm == "con":
        old_con = int(ch.get("CON", 50))
        new_con = max(1, old_con - 5)
        ch["CON"] = new_con
        logs.append(TextBlock(type="text", text=f"{nm} 体能衰退：CON {old_con} -> {new_con}"))
    elif choice_norm == "resist":
        try:
            old_res = int(arts.get("resist", 40))
        except Exception:
            old_res = 40
        new_res = max(0, old_res - 10)
        arts["resist"] = new_res
        logs.append(TextBlock(type="text", text=f"{nm} 术式抗性下降：arts.resist {old_res} -> {new_res}"))
    else:  # affinity
        try:
            old_aff = int(arts.get("affinity", 0))
        except Exception:
            old_aff = 0
        new_aff = old_aff + 5
        arts["affinity"] = new_aff
        # Flag for potential use by overcharge rules
        inf["overcharge_step"] = int(inf.get("overcharge_step", 0)) + 1
        logs.append(TextBlock(type="text", text=f"{nm} 术式亲和上升：arts.affinity {old_aff} -> {new_aff}（过载惩罚阶提升）"))
    # Persist back
    coc["characteristics"] = ch
    terra["arts"] = arts
    terra["infection"] = inf
    coc["terra"] = terra
    st["coc"] = coc
    WORLD.characters[nm] = st
    # Recompute derived HP / SAN / MP from new stats
    try:
        rec = recompute_coc_derived(nm)
        rec_logs = [blk for blk in (rec.content or []) if isinstance(blk, dict) and blk.get("type") == "text"]
    except Exception:
        rec_logs = []
    WORLD._touch()
    head = TextBlock(
        type="text",
        text=f"{nm} 感染阶段提升：{old_stage} -> {new_stage}，结晶密度 {inf.get('crystal_density', 0)}，应激重置为阶段下限 {floor}",
    )
    return ToolResponse(
        content=[head] + logs + rec_logs,
        metadata={
            "ok": True,
            "name": nm,
            "stage_before": old_stage,
            "stage_after": new_stage,
            "stress": cur_stress,
            "crystal_density": inf.get("crystal_density", 0),
            "choice": choice_norm,
        },
    )


def apply_exposure(
    name: str,
    level: str = "light",
    source: str = "",
    *,
    dice_expr: Optional[str] = None,
    bonus: int = 0,
) -> ToolResponse:
    """Apply an Oripathy exposure to `name` following docs/coc_terra.md.

    Parameters
    ----------
    name: 受暴露角色名称。
    level: 暴露等级（轻/中/重/灾害 或 light/medium/heavy/disaster），仅在 dice_expr 为空时用于选取应激骰。
    source: 文本来源说明（如 \"矿区塌方扬尘\"），仅用于日志。
    dice_expr: 自定义应激骰表达式（如 \"1d6+1\"）。提供时优先于 level。
    bonus: 总抗性加值（装备/去污/医学），直接加到目标值上。

    流程
    ----
    1. 根据 level/dice_expr 掷应激骰。
    2. 计算感染抗性目标值：max(arts.resist, round((CON+POW)/2)) + bonus - 阶段惩罚。
    3. 掷 1d100 抗性检定：极难成功→本次应激 0；一般成功→应激减半；大失败→应激×1.5。
    4. 增加 infection.stress，处理 20/50/80 阈值发作与 stage 进展（stress>100 或两次重度发作）。"""
    import math as _math

    nm = str(name)
    inf_before = _ensure_infection_block(nm)
    stage_before = int(inf_before.get("stage", 0))
    stress_before = int(inf_before.get("stress", 0))

    # 1) Determine stress dice
    lvl = str(level or "light").lower()
    expr = dice_expr
    if not expr:
        if lvl in ("light", "轻", "minor"):
            expr = "1d4"
        elif lvl in ("medium", "中", "moderate"):
            expr = "1d6+1"
        elif lvl in ("heavy", "重"):
            expr = "2d6"
        elif lvl in ("disaster", "灾害", "catastrophic"):
            expr = "2d10"
        else:
            expr = "1"
    roll_res = roll_dice(expr)
    raw = int((roll_res.metadata or {}).get("total", 0))

    # 2) Infection resist target
    tgt, resist_meta = _infection_resist_target(nm, bonus=bonus)
    roll = random.randint(1, 100)
    t = max(1, int(tgt))
    hard = max(1, t // 2)
    extreme = max(1, t // 5)
    if roll <= extreme:
        level_str = "extreme"
        success = True
    elif roll <= hard:
        level_str = "hard"
        success = True
    elif roll <= t:
        level_str = "regular"
        success = True
    else:
        level_str = "fail"
        success = False
    fumble = (not success) and roll >= 96
    txt_check = f"感染抗性检定：{nm} d100={roll} / {t} -> {('成功['+level_str+']') if success else '失败'}"

    # 3) Adjust stress by resist result
    if raw <= 0:
        adj = 0
        factor = 0.0
    else:
        if success and level_str == "extreme":
            adj = 0
            factor = 0.0
        else:
            if success:
                factor = 0.5
            elif fumble:
                factor = 1.5
            else:
                factor = 1.0
            adj = int(_math.floor(raw * factor))
            if adj <= 0 and factor > 0.0:
                adj = 1

    # 4) Apply to infection.stress and handle flares / stage advance
    inf = _ensure_infection_block(nm)
    try:
        cur_stress = int(inf.get("stress", 0))
    except Exception:
        cur_stress = 0
    stress_raw_after = cur_stress + max(0, adj)
    inf["stress"] = stress_raw_after

    logs: List[TextBlock] = []
    # Show exposure source and dice
    src_note = f"（来源：{source}）" if source else ""
    logs.append(
        TextBlock(
            type="text",
            text=f"{nm} 感染暴露：{expr} -> {raw} 点应激{src_note}",
        )
    )
    logs.append(TextBlock(type="text", text=txt_check))
    logs.append(
        TextBlock(
            type="text",
            text=f"本次应激结算：基础 {raw}，系数 {factor:.1f} -> 实际 {adj}",
        )
    )

    def _handle_flares(nm: str, before: int, after: int) -> Tuple[int, List[TextBlock], bool]:
        """Process 20/50/80 thresholds; may advance stage via advance_infection_stage.

        Returns (final_stress, logs, stage_advanced).
        """
        out_logs: List[TextBlock] = []
        stage_advanced = False
        thresholds = [(20, "mild"), (50, "moderate"), (80, "severe")]
        inf_local = _ensure_infection_block(nm)
        for th, kind in thresholds:
            if before < th <= after:
                if kind == "mild":
                    # 轻度发作：以叙述为主，留给上层决定具体减值
                    out_logs.append(
                        TextBlock(
                            type="text",
                            text=f"{nm} 感染发作（轻度，阈值 20）：剧痛/咳血，持续约 1d10 分钟；建议物理/施术检定 −10（由 GM 裁定）。",
                        )
                    )
                elif kind == "moderate":
                    out_logs.append(
                        TextBlock(
                            type="text",
                            text=(
                                f"{nm} 感染发作（中度，阈值 50）：行动吃力，建议相关检定 −20，"
                                "每轮 CON 困难检定决定行动受限；继续施术可额外承受 +1d4 应激（由 GM 决定是否触发）。"
                            ),
                        )
                    )
                else:  # severe
                    # 记录严重发作次数供阶段进展使用
                    try:
                        inf_local["severe_flare_count"] = int(inf_local.get("severe_flare_count", 0)) + 1
                    except Exception:
                        inf_local["severe_flare_count"] = 1
                    WORLD.characters[str(nm)]["coc"]["terra"]["infection"] = inf_local  # type: ignore[index]
                    out_logs.append(
                        TextBlock(
                            type="text",
                            text=(
                                f"{nm} 感染发作（重度，阈值 80）：源石结晶剧烈活化，"
                                "将进行 CON 极难检定与 POW 检定以判定后续伤害与眩晕。"
                            ),
                        )
                    )
                    # CON 极难检定：非极难视作失败
                    con_chk = skill_check_coc(nm, "CON")
                    for blk in (con_chk.content or []):
                        if isinstance(blk, dict) and blk.get("type") == "text":
                            out_logs.append(blk)
                    con_meta = con_chk.metadata or {}
                    con_level = str(con_meta.get("success_level", "fail"))
                    if con_level != "extreme":
                        dmg_roll = roll_dice("1d6")
                        dmg_raw = int((dmg_roll.metadata or {}).get("total", 0))
                        # arts_barrier 可对这次 HP 伤害减半（物理护甲无效）
                        try:
                            coc_d = dict(WORLD.characters.get(nm, {}).get("coc") or {})
                            terra_d = dict(coc_d.get("terra") or {})
                            prot = dict(terra_d.get("protection") or {})
                            barrier = int(prot.get("arts_barrier", 0))
                        except Exception:
                            barrier = 0
                        if barrier > 0:
                            dmg = int(_math.ceil(dmg_raw / 2.0))
                        else:
                            dmg = dmg_raw
                        out_logs.append(
                            TextBlock(
                                type="text",
                                text=f"重度发作伤害：1d6 -> {dmg_raw}（术式护盾 {'减半' if barrier > 0 else '未减免'}），实际 HP 伤害 {dmg}",
                            )
                        )
                        dmg_res = damage(nm, dmg)
                        for blk in (dmg_res.content or []):
                            if isinstance(blk, dict) and blk.get("type") == "text":
                                out_logs.append(blk)
                    # POW 检定：失败则眩晕 1d3 轮
                    pow_chk = skill_check_coc(nm, "POW")
                    for blk in (pow_chk.content or []):
                        if isinstance(blk, dict) and blk.get("type") == "text":
                            out_logs.append(blk)
                    pow_meta = pow_chk.metadata or {}
                    if not bool(pow_meta.get("success", False)):
                        turns_roll = roll_dice("1d3")
                        turns = int((turns_roll.metadata or {}).get("total", 1))
                        turns = max(1, turns)
                        out_logs.append(
                            TextBlock(
                                type="text",
                                text=f"POW 检定失败：{nm} 眩晕 {turns} 轮（stunned），无法进行行动。",
                            )
                        )
                        try:
                            st_res = add_status(nm, "stunned", duration_rounds=turns, kind="control")
                            for blk in (st_res.content or []):
                                if isinstance(blk, dict) and blk.get("type") == "text":
                                    out_logs.append(blk)
                        except Exception:
                            pass
        # 阶段进展：stress>100 或两次重度发作
        try:
            severe_count = int(inf_local.get("severe_flare_count", 0))
        except Exception:
            severe_count = 0
        stage_now = int(inf_local.get("stage", 0))
        final_stress = after
        if (after > 100 or severe_count >= 2) and stage_now < 3:
            adv = advance_infection_stage(nm, choice="auto")
            for blk in (adv.content or []):
                if isinstance(blk, dict) and blk.get("type") == "text":
                    out_logs.append(blk)
            meta = adv.metadata or {}
            stage_advanced = bool(meta.get("ok", False))
            # 取更新后的应激值
            inf2 = _ensure_infection_block(nm)
            try:
                final_stress = int(inf2.get("stress", final_stress))
            except Exception:
                pass
            # 重置重度发作计数
            try:
                inf2["severe_flare_count"] = 0
            except Exception:
                pass
            WORLD.characters[str(nm)]["coc"]["terra"]["infection"] = inf2  # type: ignore[index]
        return final_stress, out_logs, stage_advanced

    stress_after, flare_logs, stage_advanced = _handle_flares(nm, stress_before, stress_raw_after)
    inf_final = _ensure_infection_block(nm)
    inf_final["stress"] = stress_after
    WORLD._touch()
    logs.extend(flare_logs)

    return ToolResponse(
        content=logs,
        metadata={
            "ok": True,
            "name": nm,
            "source": source,
            "level": lvl,
            "stress_before": stress_before,
            "stress_after": int(stress_after),
            "stress_delta": max(0, int(stress_after - stress_before)),
            "stage_before": stage_before,
            "stage_after": int(inf_final.get("stage", stage_before)),
            "crystal_density": int(inf_final.get("crystal_density", 0)),
            "resist_roll": roll,
            "resist_target": t,
            "resist_success": bool(success),
            "resist_level": level_str,
            "resist_fumble": bool(fumble),
            "resist_meta": resist_meta,
            "exposure_expr": expr,
            "raw_stress": raw,
            "adjusted_stress": max(0, adj),
            "stage_advanced": bool(stage_advanced),
        },
    )


# DnD compatibility removed; use set_coc_character_from_config or set_coc_character directly.


def get_character(name: str):
    st = WORLD.characters.get(name, {})
    if not st:
        return ToolResponse(content=[TextBlock(type="text", text=f"未找到角色 {name}")], metadata={"found": False})
    hp = st.get("hp"); max_hp = st.get("max_hp")
    return ToolResponse(
        content=[TextBlock(type="text", text=f"{name}: HP {hp}/{max_hp}")],
        metadata={"found": True, **st},
    )


def _enter_dying(name: str, *, turns: int = DYING_TURNS_DEFAULT) -> ToolResponse:
    """Put character into dying state: HP=0, set turns-left, add condition tag.

    This does not broadcast; callers compose its text with their own narration.
    """
    nm = str(name)
    st = WORLD.characters.setdefault(nm, {"hp": 0, "max_hp": 0})
    st["hp"] = 0
    st["dying_turns_left"] = int(max(0, turns))
    # Also record a unified 'dying' status for visibility.
    try:
        add_status(nm, "dying", duration_rounds=st["dying_turns_left"], kind="system")
    except Exception:
        pass
    note = TextBlock(type="text", text=f"{nm} 进入濒死（{st['dying_turns_left']}回合后死亡；再次受伤即死）")
    WORLD._touch()
    return ToolResponse(content=[note], metadata={"ok": True, "name": nm, "dying": True, "turns_left": st["dying_turns_left"]})


def _die(name: str, *, reason: str = "wounds") -> ToolResponse:
    """Finalize death: HP=0, clear dying, add dead condition."""
    nm = str(name)
    st = WORLD.characters.setdefault(nm, {"hp": 0, "max_hp": 0})
    st["hp"] = 0
    # Clear dying bookkeeping
    if "dying_turns_left" in st:
        try:
            st.pop("dying_turns_left", None)
        except Exception:
            st["dying_turns_left"] = None
    # Remove unified 'dying' status if present; add a persistent 'dead' status for visibility.
    try:
        remove_status(nm, "dying")
    except Exception:
        pass
    try:
        add_status(nm, "dead", duration_rounds=None, kind="system")
    except Exception:
        pass
    note = TextBlock(type="text", text=f"{nm} 死亡。")
    WORLD._touch()
    return ToolResponse(content=[note], metadata={"ok": True, "name": nm, "dead": True, "reason": reason})


def tick_dying_for(name: str) -> ToolResponse:
    """Decrement dying turns for a character (their own 'turn' tick).

    - If not dying: no-op.
    - If reaches 0: die.
    """
    nm = str(name)
    # Always tick control statuses for the actor at end of their own turn
    notes: List[TextBlock] = []
    try:
        notes.extend(_tick_control_statuses(nm))
    except Exception:
        pass
    st = WORLD.characters.get(nm, {})
    if not st or st.get("dying_turns_left") is None:
        return ToolResponse(content=[], metadata={"ok": True, "name": nm, "affected": False})
    try:
        left = int(st.get("dying_turns_left", 0))
    except Exception:
        left = 0
    # Already scheduled to die
    if left <= 0:
        res = _die(nm, reason="timeout")
        # Append any control-expiration notes before death
        return ToolResponse(content=notes + (res.content or []), metadata=res.metadata)
    st["dying_turns_left"] = left - 1
    if st["dying_turns_left"] <= 0:
        res = _die(nm, reason="timeout")
        return ToolResponse(content=notes + (res.content or []), metadata=res.metadata)
    # Otherwise, report remaining
    note = TextBlock(type="text", text=f"{nm} 濒死剩余 {st['dying_turns_left']} 回合。")
    WORLD._touch()
    return ToolResponse(content=notes + [note], metadata={"ok": True, "name": nm, "turns_left": st["dying_turns_left"], "affected": True})


def damage(name: str, amount: int):
    amt = max(0, int(amount))
    nm = str(name)
    st = WORLD.characters.setdefault(nm, {"hp": 0, "max_hp": 0})
    # Mark a new injury instance for First Aid gating
    if amt > 0:
        try:
            st["injury_id"] = int(st.get("injury_id", 0)) + 1
        except Exception:
            st["injury_id"] = 1
    hp_before = int(st.get("hp", 0))
    # If already dying, any damage kills immediately
    if st.get("dying_turns_left") is not None:
        die_res = _die(nm, reason="reinjury")
        parts: List[TextBlock] = [TextBlock(type="text", text=f"{nm} 在濒死状态下再次受到 {amt} 伤害，立即死亡。")]
        parts.extend(die_res.content or [])
        return ToolResponse(content=parts, metadata={"ok": True, "name": nm, "hp": 0, "max_hp": st.get("max_hp"), "dead": True})

    # Apply damage normally
    st["hp"] = max(0, hp_before - amt)
    dead_or_down = st["hp"] <= 0
    parts = [TextBlock(type="text", text=f"{nm} 受到 {amt} 伤害，HP {st['hp']}/{st.get('max_hp', st['hp'])}{'（倒地）' if dead_or_down else ''}")]
    # Transition to dying if this hit reduces to 0
    if st["hp"] <= 0:
        # Enter dying instead of immediate death
        res = _enter_dying(nm, turns=DYING_TURNS_DEFAULT)
        parts.extend(res.content or [])
        return ToolResponse(content=parts, metadata={"name": nm, "hp": 0, "max_hp": st.get("max_hp"), "dead": True, "dying": True, "turns_left": st.get("dying_turns_left")})
    WORLD._touch()
    return ToolResponse(
        content=parts,
        metadata={"ok": True, "name": nm, "hp": st["hp"], "max_hp": st.get("max_hp"), "dead": False},
    )


def first_aid(name: str, target: str) -> ToolResponse:
    """Attempt First Aid on target.

    - Roll CoC FirstAid skill for the rescuer.
    - On success:
      * If target is dying: stabilize (clear dying flag) and set HP to at least 1.
      * Else if target is wounded (0<HP<Max): restore 1 HP, at most once per injury instance.
    - On failure: no effect.
    - We gate the per-injury 1 HP by `target.injury_id` and `target.first_aid_applied_on`.
    """
    rescuer = str(name)
    blocked, msg = _blocked_action(rescuer, "action")
    if blocked:
        return ToolResponse(
            content=[TextBlock(type="text", text=msg)],
            metadata={"ok": False, "error_type": "attacker_unable", "rescuer": rescuer, "target": str(target)}
        )
    tgt = str(target)
    st = WORLD.characters.setdefault(tgt, {"hp": 0, "max_hp": 0})
    logs: List[TextBlock] = []
    # Skill check
    chk = skill_check_coc(rescuer, "FirstAid")
    if chk.content:
        for blk in chk.content:
            if isinstance(blk, dict) and blk.get("type") == "text":
                logs.append(blk)
    ok = bool((chk.metadata or {}).get("success"))
    if not ok:
        return ToolResponse(
            content=logs + [TextBlock(type="text", text=f"{rescuer} 急救失败，{tgt} 状态未变")],
            metadata={"ok": False, "error_type": "check_failed", "rescuer": rescuer, "target": tgt}
        )

    # Success path
    # If dying: stabilize and set hp to at least 1
    if st.get("dying_turns_left") is not None:
        st["dying_turns_left"] = None
        try:
            remove_status(tgt, "dying")
        except Exception:
            pass
        # Raise HP to at least 1
        try:
            st["hp"] = max(1, int(st.get("hp", 0)))
        except Exception:
            st["hp"] = 1
        logs.append(TextBlock(type="text", text=f"{rescuer} 成功稳定 {tgt}（HP 至少 1，脱离濒死）"))
        WORLD._touch()
        return ToolResponse(content=logs, metadata={"ok": True, "rescuer": rescuer, "target": tgt, "stabilized": True, "hp": st.get("hp")})

    # Non-dying healing: +1 HP once per injury
    try:
        hp = int(st.get("hp", 0))
        max_hp = int(st.get("max_hp", 0))
    except Exception:
        hp = st.get("hp", 0) or 0
        max_hp = st.get("max_hp", 0) or 0
    if max_hp and 0 < hp < max_hp:
        injury_id = int(st.get("injury_id", 0))
        applied_on = int(st.get("first_aid_applied_on", -1))
        if applied_on == injury_id and injury_id > 0:
            logs.append(TextBlock(type="text", text=f"{tgt} 该伤势已急救过（本次不再恢复 HP）"))
            return ToolResponse(content=logs, metadata={"ok": True, "rescuer": rescuer, "target": tgt, "healed": 0, "already_applied": True})
        st["hp"] = min(max_hp, hp + 1)
        st["first_aid_applied_on"] = injury_id
        logs.append(TextBlock(type="text", text=f"{rescuer} 急救成功，{tgt} 恢复 1 点 HP（{st['hp']}/{max_hp}）"))
        WORLD._touch()
        return ToolResponse(content=logs, metadata={"ok": True, "rescuer": rescuer, "target": tgt, "healed": 1, "hp": st.get("hp")})

    # Otherwise nothing to do
    logs.append(TextBlock(type="text", text=f"{tgt} 当前无需急救（HP={hp}/{max_hp}）"))
    return ToolResponse(content=logs, metadata={"ok": True, "rescuer": rescuer, "target": tgt, "healed": 0})


def heal(name: str, amount: int):
    amt = max(0, int(amount))
    nm = str(name)
    st = WORLD.characters.setdefault(nm, {"hp": 0, "max_hp": 0})
    max_hp = int(st.get("max_hp", 0))
    st["hp"] = min(max_hp if max_hp > 0 else st.get("hp", 0), int(st.get("hp", 0)) + amt)
    parts = [TextBlock(type="text", text=f"{nm} 恢复 {amt} 点生命，HP {st['hp']}/{st.get('max_hp', st['hp'])}")]
    # If healed above 0 while dying, clear dying state
    if st.get("hp", 0) > 0 and st.get("dying_turns_left") is not None:
        try:
            st.pop("dying_turns_left", None)
        except Exception:
            st["dying_turns_left"] = None
        try:
            remove_status(nm, "dying")
        except Exception:
            pass
        parts.append(TextBlock(type="text", text=f"{nm} 脱离濒死。"))
    return ToolResponse(
        content=parts,
        metadata={"name": nm, "hp": st["hp"], "max_hp": st.get("max_hp")},
    )


# ---- MP tools ----
def spend_mp(name: str, amount: int) -> ToolResponse:
    nm = str(name)
    amt = max(0, int(amount))
    st = WORLD.characters.setdefault(nm, {})
    cur = int(st.get("mp", 0))
    if amt <= 0:
        return ToolResponse(content=[TextBlock(type="text", text=f"{nm} 未消耗 MP")], metadata={"ok": True, "mp": cur, "spent": 0})
    if cur < amt:
        return ToolResponse(content=[TextBlock(type="text", text=f"{nm} MP 不足（需要 {amt}，当前 {cur}）")], metadata={"ok": False, "error_type": "mp_insufficient", "need": amt, "mp": cur})
    st["mp"] = cur - amt
    return ToolResponse(content=[TextBlock(type="text", text=f"{nm} 消耗 MP {amt}（剩余 {st['mp']}）")], metadata={"ok": True, "mp": st["mp"], "spent": amt})


def recover_mp(name: str, amount: int) -> ToolResponse:
    nm = str(name)
    amt = max(0, int(amount))
    st = WORLD.characters.setdefault(nm, {})
    cap = int(st.get("max_mp", 0))
    cur = int(st.get("mp", 0))
    st["mp"] = min(cap if cap > 0 else cur + amt, cur + amt)
    return ToolResponse(content=[TextBlock(type="text", text=f"{nm} 恢复 MP {amt}（{st['mp']}/{cap or '?'}）")], metadata={"ok": True, "mp": st["mp"], "max_mp": cap})


# ---- Dice tools ----
def roll_dice(expr: str = "1d20"):
    """Roll dice expression like '1d20+3', '2d6+1', 'd20'."""
    expr = expr.lower().replace(" ", "")
    total = 0
    parts: List[str] = []
    i = 0
    sign = 1
    # Simple parser supporting NdM, +/-, and constants
    token = ""
    tokens: List[str] = []
    for ch in expr:
        if ch in "+-":
            if token:
                tokens.append(token)
                token = ""
            tokens.append(ch)
        else:
            token += ch
    if token:
        tokens.append(token)
    # Evaluate tokens
    sign = 1
    breakdown: List[str] = []
    for tk in tokens:
        if tk == "+":
            sign = 1
            continue
        if tk == "-":
            sign = -1
            continue
        if "d" in tk:
            n_str, _, m_str = tk.partition("d")
            n = int(n_str) if n_str else 1
            m = int(m_str) if m_str else 20
            rolls = [random.randint(1, m) for _ in range(max(1, n))]
            subtotal = sum(rolls) * sign
            total += subtotal
            breakdown.append(f"{sign:+d}{n}d{m}({','.join(map(str, rolls))})")
        else:
            val = sign * int(tk)
            total += val
            breakdown.append(f"{val:+d}")
    text = f"掷骰 {expr} = {total} [{' '.join(breakdown)}]"
    return ToolResponse(
        content=[TextBlock(type="text", text=text)],
        metadata={"expr": expr, "total": total, "breakdown": breakdown},
    )


def skill_check_coc(name: str, skill: str, *, value: Optional[int] = None, difficulty: str = "regular") -> ToolResponse:
    """CoC 7e percentile skill check.

    - If `value` omitted, read from character's coc.skills; otherwise derive default by name.
    - difficulty affects only the text/threshold (regular/hard/extreme), we still roll once and report level.
    """
    nm = str(name)
    st = WORLD.characters.get(nm, {})
    target = int(value) if value is not None else _coc_skill_value(nm, skill)
    roll = random.randint(1, 100)
    t = max(1, int(target))
    hard = max(1, t // 2)
    extreme = max(1, t // 5)
    if roll <= extreme:
        level = "extreme"
        success = True
    elif roll <= hard:
        level = "hard"
        success = True
    elif roll <= t:
        level = "regular"
        success = True
    else:
        level = "fail"
        success = False
    txt = f"检定（CoC）：{nm} {skill} d100={roll} / {t} -> {('成功['+level+']') if success else '失败'}"
    return ToolResponse(content=[TextBlock(type="text", text=txt)], metadata={
        "name": nm,
        "skill": str(skill),
        "roll": roll,
        "target": t,
        "success": success,
        "success_level": level,
        "difficulty": str(difficulty),
    })


# DnD遗留移除：不再提供 d20/DC 风格的近战求解（统一走 attack_with_weapon）。


def get_stat_block(name: str) -> ToolResponse:
    st = WORLD.characters.get(name, {})
    if not st:
        return ToolResponse(content=[TextBlock(type="text", text=f"未找到 {name}")], metadata={"found": False})
    # CoC view
    if isinstance(st.get("coc"), dict):
        coc = dict(st.get("coc") or {})
        chars = {k.upper(): v for k, v in (coc.get("characteristics") or {}).items()}
        der = dict(coc.get("derived") or {})
        line_chars = ", ".join(f"{k} {int(v)}" for k, v in chars.items() if k in ("STR", "DEX", "CON", "INT", "POW", "APP", "EDU", "SIZ", "LUCK"))
        extras = []
        if "san" in der:
            extras.append(f"SAN {int(der['san'])}")
        if "mp" in der:
            extras.append(f"MP {int(der['mp'])}")
        extra_line = ("，" + ", ".join(extras)) if extras else ""
        txt = (
            f"{name} HP {st.get('hp','?')}/{st.get('max_hp','?')}{extra_line}\n"
            f"特征：{line_chars}"
        )
        return ToolResponse(content=[TextBlock(type="text", text=txt)], metadata=st)

    # Default fallback view
    txt = f"{name} HP {st.get('hp','?')}/{st.get('max_hp','?')}"
    return ToolResponse(content=[TextBlock(type="text", text=txt)], metadata=st)




# ---- Weapons (reach sourced from weapon defs; no auto-move) ----
def set_weapon_defs(defs: Dict[str, Dict[str, Any]]):
    """Replace the entire weapon definition table (extended schema only).

    Required per weapon id:
      - label: str
      - reach_steps: int (>0)
      - skill: str
      - defense_skill: str
      - damage: NdM[+/-K]
      - damage_type: 'physical' | 'arts' (free string, engine treats others as physical)
    Legacy fields like ability/damage_expr are not supported.
    """
    try:
        cleaned: Dict[str, Dict[str, Any]] = {}
        for k, v in (defs or {}).items():
            d = dict(v or {})
            # Basic validation
            missing = [
                f for f in ("label", "reach_steps", "skill", "defense_skill", "damage", "damage_type")
                if f not in d
            ]
            if missing:
                raise ValueError(f"weapon {k} missing fields: {', '.join(missing)}")
            try:
                rs = int(d.get("reach_steps"))
                if rs <= 0:
                    raise ValueError
            except Exception:
                raise ValueError(f"weapon {k}.reach_steps must be > 0 integer")
            # Strip legacy keys if present; they are ignored
            for legacy in ("ability", "damage_expr", "proficient_default"):
                d.pop(legacy, None)
            cleaned[str(k)] = d
        WORLD.weapon_defs = cleaned
    except Exception:
        WORLD.weapon_defs = {}
        raise
    return ToolResponse(content=[TextBlock(type="text", text=f"武器表载入：{len(WORLD.weapon_defs)} 项")], metadata={"count": len(WORLD.weapon_defs)})


def define_weapon(weapon_id: str, data: Dict[str, Any]):
    wid = str(weapon_id)
    WORLD.weapon_defs[wid] = dict(data or {})
    return ToolResponse(content=[TextBlock(type="text", text=f"武器登记：{wid}")], metadata={"id": wid, **WORLD.weapon_defs[wid]})


# ---- Attack pipeline (pure-ish helpers) ----

def _attack_resolve_guard_interception(attacker: str, defender: str, reach_steps: int) -> tuple[str, Optional[Dict[str, Any]], List[TextBlock]]:
    """Resolve protection/guard interception without mutating attacker/defender state.

    Returns: (final_defender, guard_meta, pre_logs)
    """
    pre_logs: List[TextBlock] = []
    guard_meta: Optional[Dict[str, Any]] = None
    new_defender, meta_guard, pre = _resolve_guard_interception(attacker, defender, reach_steps)
    if pre:
        pre_logs.extend(pre)
    if meta_guard:
        guard_meta = dict(meta_guard)
    return (new_defender, guard_meta, pre_logs)


def _attack_compute_distance(attacker: str, defender: str) -> Optional[int]:
    try:
        return get_distance_steps_between(attacker, defender)
    except Exception:
        return None


def _attack_run_check_or_contest(
    attacker: str,
    defender: str,
    *,
    skill_name: str,
    defense_skill_name: str,
    attacker_value: Optional[int] = None,
    defender_value: Optional[int] = None,
) -> tuple[bool, List[TextBlock], Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """Run opposed check (or single check if defender dying).

    Returns: (success, logs, opposed_meta_or_none, attack_check_meta_or_none)

    - When attacker_value/defender_value is None, use sheet skill values (contest()).
    - When attacker_value is provided, perform an inline opposed check using that
      value for attacker (used by过载施术一类的固定修正)。"""
    parts: List[TextBlock] = []
    oppose_meta: Optional[Dict[str, Any]] = None
    atk_check_meta: Optional[Dict[str, Any]] = None

    # Defender dying: skip contest, only attack roll (with optional override)
    if _is_dying(defender):
        parts.append(TextBlock(type="text", text=f"对抗跳过：{defender} 濒死，本次仅进行命中检定"))
        if attacker_value is not None:
            atk_res = skill_check_coc(attacker, skill_name, value=int(attacker_value))
        else:
            atk_res = skill_check_coc(attacker, skill_name)
        if atk_res.content:
            for blk in atk_res.content:
                if isinstance(blk, dict) and blk.get("type") == "text":
                    parts.append(blk)
        atk_check_meta = dict(atk_res.metadata or {})
        return bool((atk_res.metadata or {}).get("success")), parts, None, atk_check_meta

    # No overrides: delegate to generic contest() to keep behaviour identical
    if attacker_value is None and defender_value is None:
        oppose = contest(attacker, skill_name, defender, defense_skill_name)
        if oppose.content:
            for blk in oppose.content:
                if isinstance(blk, dict) and blk.get("type") == "text":
                    parts.append(blk)
        oppose_meta = dict(oppose.metadata or {})
        winner = (oppose.metadata or {}).get("winner")
        return (winner == attacker), parts, oppose_meta, None

    # Inline opposed check with explicit values (mirrors contest() semantics)
    # Dying short-circuit for attacker kept minimal; defender-dying handled above.
    if _is_dying(attacker) and not _is_dying(defender):
        parts.append(TextBlock(type="text", text=f"对抗跳过：{attacker} 濒死，{defender} 自动胜"))
        oppose_meta = {"winner": defender, "skip_reason": "attacker_dying"}
        return False, parts, oppose_meta, None

    ar = skill_check_coc(attacker, skill_name, value=int(attacker_value) if attacker_value is not None else None)
    br = skill_check_coc(defender, defense_skill_name, value=int(defender_value) if defender_value is not None else None)
    a_meta = ar.metadata or {}
    b_meta = br.metadata or {}

    def _lvl(m):
        return {"extreme": 3, "hard": 2, "regular": 1, "fail": 0}.get(str(m.get("success_level", "fail")), 0)

    la, lb = _lvl(a_meta), _lvl(b_meta)
    if la != lb:
        winner = attacker if la > lb else defender
    else:
        ra = int(a_meta.get("roll", 101) or 101)
        rb = int(b_meta.get("roll", 101) or 101)
        if ra != rb:
            winner = attacker if ra < rb else defender
        else:
            winner = defender  # exact tie favors defender
    txt = f"对抗：{attacker}({skill_name})[{a_meta.get('success_level','fail')}] vs {defender}({defense_skill_name})[{b_meta.get('success_level','fail')}] -> {winner} 胜"
    parts.append(TextBlock(type="text", text=txt))
    oppose_meta = {"a": a_meta, "b": b_meta, "winner": winner}
    return (winner == attacker), parts, oppose_meta, None


def _attack_apply_damage(
    defender: str,
    *,
    damage_expr_base: str,
    damage_type: str,
    defender_sheet: Dict[str, Any],
) -> tuple[List[TextBlock], int, int, int]:
    """Apply damage to defender and return (logs, total, reduced, final).

    This step mutates world state (HP) via damage().
    """
    logs: List[TextBlock] = []
    dmg_res = roll_dice(damage_expr_base)
    total = int((dmg_res.metadata or {}).get("total", 0))
    # Fixed reduction by armor/barrier depending on damage_type
    reduced = 0
    final = total
    try:
        coc_d = dict(defender_sheet.get("coc") or {})
        terra = dict(coc_d.get("terra") or {})
        prot = dict(terra.get("protection") or {})
        if str(damage_type).lower() == "arts":
            reduced = max(0, int(prot.get("arts_barrier", 0)))
        else:
            reduced = max(0, int(prot.get("physical_armor", 0)))
    except Exception:
        reduced = 0
    final = max(0, total - int(reduced))
    dmg_apply = damage(defender, final)
    logs.append(
        TextBlock(
            type="text",
            text=f"伤害：{damage_expr_base} -> {total}{('（减伤 ' + str(reduced) + '）') if reduced else ''}",
        )
    )
    for blk in (dmg_apply.content or []):
        if isinstance(blk, dict) and blk.get("type") == "text":
            logs.append(blk)
    return logs, int(total), int(reduced), int(final)


def attack_with_weapon(
    attacker: str,
    defender: str,
    weapon: str,
    advantage: str = "none",
) -> ToolResponse:
    """Attack using a named weapon (extended schema only).

    - No auto-move; if distance > reach_steps, fail early.
    - Uses weapon.skill vs weapon.defense_skill; damage from weapon.damage (NdM[+/-K]).
    - damage_type controls armor/barrier reduction.
    """
    # participants gate: when participants are set, both attacker and defender must be participants
    if WORLD.participants:
        if str(attacker) not in WORLD.participants or str(defender) not in WORLD.participants:
            return ToolResponse(
                content=[TextBlock(type="text", text=f"参与者限制：仅当前场景参与者可以进行/承受攻击。")],
                metadata={"ok": False, "error_type": "not_participant", "attacker": attacker, "defender": defender},
            )
    # Gate by system/control statuses
    blocked, msg = _blocked_action(str(attacker), "attack")
    if blocked:
        return ToolResponse(content=[TextBlock(type="text", text=msg)], metadata={"attacker": attacker, "defender": defender, "weapon_id": weapon, "ok": False, "error_type": "attacker_unable"})
    atk = WORLD.characters.get(attacker, {})
    w = WORLD.weapon_defs.get(str(weapon), {})
    try:
        reach_steps = max(1, int(w.get("reach_steps", DEFAULT_REACH_STEPS)))
    except Exception:
        reach_steps = int(DEFAULT_REACH_STEPS)

    # Extended-only implementation continues below

    # Branch B: extended schema (damage/defense_skill/damage_type)
    try:
        defense_skill_name = str(w["defense_skill"])  # required
        damage_expr_base = str(w["damage"]).lower()   # required NdM(+/-K)
        damage_type = str(w.get("damage_type", "physical")).lower()
    except Exception as exc:
        return ToolResponse(
            content=[TextBlock(type="text", text=f"武器定义缺失字段：{exc}")],
            metadata={"ok": False, "error_type": "weapon_def_invalid", "weapon_id": weapon},
        )

    # Distance string helper
    def _fmt_distance(steps: Optional[int]) -> str:
        if steps is None:
            return "未知"
        return format_distance_steps(int(steps))

    # Ownership gate: attacker must possess the weapon (count > 0)
    bag = WORLD.inventory.get(str(attacker), {}) or {}
    if int(bag.get(str(weapon), 0)) <= 0:
        msg = TextBlock(type="text", text=f"{attacker} 未持有武器 {weapon}，攻击取消。")
        return ToolResponse(
            content=[msg],
            metadata={
                "ok": False,
                "attacker": attacker,
                "defender": defender,
                "weapon_id": weapon,
                "error_type": "weapon_not_owned",
            },
        )

    # Protection interception (may change defender)
    defender2, guard_meta, pre_logs = _attack_resolve_guard_interception(attacker, defender, reach_steps)
    defender = defender2

    # Post-interception snapshot for defender stat and distance gate
    dfd = WORLD.characters.get(defender, {})
    distance_before = _attack_compute_distance(attacker, defender)
    # Cross-scene or unknown distance -> treat as unreachable in this minimal scheme
    if distance_before is None:
        msg = TextBlock(type="text", text=f"不可达：{attacker} 与 {defender} 不在同一场景，无法以 {weapon} 攻击")
        return ToolResponse(
            content=pre_logs + [msg],
            metadata={
                "ok": False,
                "error_type": "out_of_reach",
                "attacker": attacker,
                "defender": defender,
                "weapon_id": weapon,
                "hit": False,
                "reach_ok": False,
                "distance_before": None,
                "reach_steps": reach_steps,
                **({"guard": guard_meta} if guard_meta else {}),
            },
        )
    if distance_before is not None and distance_before > reach_steps:
        msg = TextBlock(type="text", text=f"距离不足：{attacker} 使用 {weapon} 攻击 {defender} 失败（距离 {_fmt_distance(distance_before)}，触及 {_fmt_distance(reach_steps)}）")
        return ToolResponse(
            content=pre_logs + [msg],
            metadata={
                "ok": False,
                "error_type": "out_of_reach",
                "attacker": attacker,
                "defender": defender,
                "weapon_id": weapon,
                "hit": False,
                "reach_ok": False,
                "distance_before": distance_before,
                "distance_after": distance_before,
                "reach_steps": reach_steps,
                **({"guard": guard_meta} if guard_meta else {}),
            },
        )

    # Attack resolution
    try:
        skill_name = str(w["skill"])  # required
    except Exception:
        return ToolResponse(
            content=[TextBlock(type="text", text=f"武器缺少进攻技能 skill: {weapon}")],
            metadata={"ok": False, "error_type": "weapon_def_invalid", "weapon_id": weapon},
        )
    parts: List[TextBlock] = list(pre_logs)
    success, logs_check, oppose_meta, atk_check_meta = _attack_run_check_or_contest(
        attacker,
        defender,
        skill_name=skill_name,
        defense_skill_name=defense_skill_name,
    )
    if logs_check:
        parts.extend(logs_check)
    hp_before = int(WORLD.characters.get(defender, {}).get("hp", dfd.get("hp", 0)))
    dmg_total = 0
    if success:
        dmg_logs, total, reduced, final = _attack_apply_damage(
            defender,
            damage_expr_base=damage_expr_base,
            damage_type=damage_type,
            defender_sheet=dfd,
        )
        parts.extend(dmg_logs)
        dmg_total = final
    hp_after = int(WORLD.characters.get(defender, {}).get("hp", dfd.get("hp", 0)))
    distance_after = distance_before
    # Any hit/miss still mutates state through damage(); touch once per attack
    WORLD._touch()
    meta: Dict[str, Any] = {
        "ok": True,
        "attacker": attacker,
        "defender": defender,
        "weapon_id": weapon,
        "hit": success,
        "base_mod": 0,
        "damage_total": int(dmg_total),
        "hp_before": int(hp_before),
        "hp_after": int(hp_after),
        "reach_ok": True,
        "distance_before": distance_before,
        "distance_after": distance_after,
        "reach_steps": reach_steps,
        **({"guard": guard_meta} if guard_meta else {}),
    }
    # Attach contest/check metadata to align with previous behavior
    if _is_dying(defender):
        meta.update({"opposed": False, "defender_dying": True, "attack_check": atk_check_meta})
    else:
        meta.update({"opposed": True, "opposed_meta": oppose_meta})
    return ToolResponse(content=parts, metadata=meta)


def _replace_ability_tokens(expr: str, ability_mod: int) -> str:
    """Replace ability tokens in damage expressions with 0 (attribute bonus removed).

    Historical note: We previously allowed "POW" here by converting CoC POW to a
    D&D-style modifier. Per user request, usage of "+POW" in damage expressions is
    removed. We therefore no longer replace "POW" tokens in expressions. Any
    occurrence of POW will be treated as invalid upstream and should be rejected
    before calling the dice roller.
    """
    s = expr
    # Intentionally exclude POW from the replacement list to deprecate
    # "+POW" usage in weapon damage expressions.
    for token in ("STR", "DEX", "CON", "INT", "SIZ", "APP", "EDU"):
        if token in s:
            s = s.replace(token, "0")
    return s

def _coc_to_dnd_score(x: int) -> int:
    try:
        return max(1, int(round(int(x) / 5.0)))
    except Exception:
        return 10

def _coc_ability_mod_for(name: str, ab_name: str) -> int:
    st = WORLD.characters.get(str(name), {})
    coc = dict(st.get("coc") or {})
    ch = {k.upper(): int(v) for k, v in (coc.get("characteristics") or {}).items()}
    val = int(ch.get(str(ab_name).upper(), 50))
    score = _coc_to_dnd_score(val)
    return (score - 10) // 2

def _weapon_skill_for(weapon_id: str, reach_steps: int, ability: str) -> str:
    # Heuristic: reach<=2 and STR/DEX-based -> MeleeWeapons; otherwise RangedWeapons
    if reach_steps <= 2 and ability.upper() in ("STR", "DEX"):
        return "MeleeWeapons"
    return "RangedWeapons"

def _coc_skill_value(name: str, skill: str) -> int:
    """Return a CoC percentile value for a skill or characteristic.

    - If `skill` matches a known characteristic name (STR/DEX/CON/INT/POW/APP/EDU/SIZ/LUCK),
      return the raw characteristic percentile from the sheet.
    - Else, look up in coc.skills; fall back to sensible defaults.
    """
    nm = str(name)
    st = WORLD.characters.get(nm, {})
    coc = dict(st.get("coc") or {})
    # Characteristic passthrough
    if str(skill).upper() in {"STR", "DEX", "CON", "INT", "POW", "APP", "EDU", "SIZ", "LUCK"}:
        try:
            ch = {k.upper(): int(v) for k, v in (coc.get("characteristics") or {}).items()}
        except Exception:
            ch = {}
        return int(ch.get(str(skill).upper(), 50))
    # Skills (explicit)
    skills = coc.get("skills") or {}
    if isinstance(skills, dict):
        v = skills.get(skill) or skills.get(str(skill).title()) or skills.get(str(skill).lower())
        if isinstance(v, (int, float)):
            return max(0, int(v))
    # Defaults
    ch = {k.upper(): int(v) for k, v in (coc.get("characteristics") or {}).items()}
    defaults = {
        # Core skills
        "Stealth": 20,
        "Perception": 25,  # Spot Hidden analogue
        "Dodge": max(1, int(ch.get("DEX", 50) // 2)),
        "Arts_Resist": 40,
        "FirstAid": 30,
        "Medicine": 5,
        # Coarse combat fallbacks
        "MeleeWeapons": 25,
        "RangedWeapons": 25,
        # Standard set (Terra-flavored)
        "Fighting_Brawl": 25,
        "Fighting_Blade": 30,
        "Fighting_DualBlade": 25,
        "Fighting_Polearm": 30,
        "Fighting_Blunt": 25,
        "Fighting_Shield": 20,
        "Firearms_Handgun": 25,
        "Firearms_Rifle_Crossbow": 30,
        "Firearms_Shotgun": 25,
        "Heavy_Weapons": 20,
        "Throwables_Explosives": 30,
        # Arts (mutable, choose table-rules as needed)
        "Arts_Offense": 40,
        "Arts_Control": 40,
    }
    return int(defaults.get(skill, 25))


# ---- Arts helpers ----
def set_arts_defs(defs: Dict[str, Dict[str, Any]]):
    """Strictly set arts definitions (CoC-flavored), with POW removed from usage.

    Required per art:
      - label: str
      - cast_skill: str
      - resist: str (skill name; "POW" is NOT allowed)
      - range_steps: int
      - damage_type: str ('arts' or 'physical')
    Optional:
      - mp: {cost:int, variable:bool, max:int}
      - damage: str (NdM[+/-K] or integer expression; may reference MP only)
      - heal: str
      - control: {effect:str, duration:str}
      - tags: list[str]
    Note: +POW/POWER 相关写法已移除，不允许在术式中使用 POW/POWER 占位符。
    """
    # Allow optional one-line description; canonical key is 'desc'.
    allowed = {"label","cast_skill","resist","range_steps","damage_type","mp","damage","heal","control","tags","desc","description"}
    try:
        cleaned: Dict[str, Dict[str, Any]] = {}
        for k, v in (defs or {}).items():
            if not isinstance(v, dict):
                raise ValueError(f"art {k} must be an object")
            d = {str(kk): vv for kk, vv in v.items()}
            extra = set(d.keys()) - allowed
            if extra:
                raise ValueError(f"art {k} has unknown keys: {sorted(extra)}")
            for req in ("label","cast_skill","resist","range_steps","damage_type"):
                if req not in d:
                    raise ValueError(f"art {k} missing required field '{req}'")
            d["label"] = str(d.get("label") or "")
            # normalize description aliases to 'desc'
            if "desc" in d:
                d["desc"] = str(d.get("desc") or "")
            elif "description" in d:
                d["desc"] = str(d.get("description") or "")
                d.pop("description", None)
            d["cast_skill"] = str(d.get("cast_skill") or "")
            d["resist"] = str(d.get("resist") or "")
            if d["resist"].upper() == "POW":
                raise ValueError(f"art {k}.resist cannot be 'POW' (removed); use a skill like 'Arts_Resist'")
            d["range_steps"] = int(d.get("range_steps") or 0)
            d["damage_type"] = str(d.get("damage_type") or "arts").lower()
            if d["range_steps"] <= 0:
                raise ValueError(f"art {k}.range_steps must be > 0")
            # Normalize optional shapes
            if "mp" in d and isinstance(d["mp"], dict):
                mp = d["mp"]
                d["mp"] = {"cost": int(mp.get("cost", 0) or 0), "variable": bool(mp.get("variable", False)), "max": int(mp.get("max", 0) or 0)}
            if "control" in d and isinstance(d["control"], dict):
                c = d["control"]
                d["control"] = {"effect": str(c.get("effect", "")), "duration": str(c.get("duration", ""))}
            if "tags" in d and isinstance(d["tags"], list):
                d["tags"] = [str(x) for x in d["tags"]]
            cleaned[str(k)] = d
        WORLD.arts_defs = cleaned
    except Exception:
        WORLD.arts_defs = {}
        raise
    return ToolResponse(content=[TextBlock(type="text", text=f"术式表载入：{len(WORLD.arts_defs)} 项")], metadata={"count": len(WORLD.arts_defs)})


def define_art(art_id: str, data: Dict[str, Any]):
    aid = str(art_id)
    res = set_arts_defs({aid: dict(data or {})})
    return ToolResponse(content=[TextBlock(type="text", text=f"术式登记：{aid}")], metadata={"id": aid, **WORLD.arts_defs[aid]})


def get_arts_defs() -> Dict[str, Dict[str, Any]]:
    """Return a sanitized copy of arts definitions (strict CoC schema).

    Exposed fields (for prompts/front-end): label, cast_skill, resist, range_steps,
    damage_type, mp, damage, heal, control
    """
    out: Dict[str, Dict[str, Any]] = {}
    for aid, data in (WORLD.arts_defs or {}).items():
        try:
            d = dict(data or {})
        except Exception:
            d = {}
        mp_cfg = dict(d.get("mp") or {}) if isinstance(d.get("mp"), dict) else {}
        out[str(aid)] = {
            "label": str(d.get("label", "")),
            **({"desc": str(d.get("desc", ""))} if d.get("desc") else {}),
            "cast_skill": str(d.get("cast_skill", "")),
            "resist": str(d.get("resist", "")),
            "range_steps": int(d.get("range_steps", 6) or 6),
            "damage_type": str(d.get("damage_type", "arts")),
            "mp": {
                "cost": int(mp_cfg.get("cost", 0) or 0),
                "variable": bool(mp_cfg.get("variable", False)),
                "max": int(mp_cfg.get("max", 0) or 0),
            },
            **({"damage": str(d.get("damage"))} if d.get("damage") else {}),
            **({"heal": str(d.get("heal"))} if d.get("heal") else {}),
            **({"control": {"effect": str((d.get("control") or {}).get("effect", "")), "duration": str((d.get("control") or {}).get("duration", ""))}} if isinstance(d.get("control"), dict) else {}),
        }
    return out


def _replace_art_tokens(attacker: str, expr: str, *, mp_spent: int = 0, base_cost: int = 0) -> str:
    """Replace token placeholders in arts formulas (no POW/POWER/MP in expressions).

    Supported tokens（词边界匹配）仅限：
    - Ability tokens（不含 POW）：STR/DEX/CON/INT/SIZ/APP/EDU → floor(val/10)
      扩展：TOKEN_RAW, TOKEN_10, TOKEN_5（同样不含 POW_* 变体）。

    说明：不再支持 POWER/POW/MP 类占位符。若表达式仍包含这些标记，将在调用处被判定为无效表达式。
    """
    import re  # local import to avoid changing module top

    def _coc_raw_for(name: str, ab_name: str) -> int:
        st = WORLD.characters.get(str(name), {})
        coc = dict(st.get("coc") or {})
        ch = {k.upper(): int(v) for k, v in (coc.get("characteristics") or {}).items()}
        return int(ch.get(str(ab_name).upper(), 50))

    def _tens(v: int) -> int:
        try:
            return max(0, int(v) // 10)
        except Exception:
            return 0

    def _div5(v: int) -> int:
        try:
            return max(0, int(v) // 5)
        except Exception:
            return 0

    s = str(expr or "")

    # MP 不再被替换；在调用处统一做表达式有效性检查

    # Extended CoC ability forms: *_RAW, *_10, *_5 (exclude POW)
    for token in ("STR", "DEX", "CON", "INT", "SIZ", "APP", "EDU"):
        raw = _coc_raw_for(attacker, token)
        s = re.sub(rf"\b{token}_RAW\b", str(raw), s)
        s = re.sub(rf"\b{token}_10\b", str(_tens(raw)), s)
        s = re.sub(rf"\b{token}_5\b", str(_div5(raw)), s)

    # Base ability tokens -> tens by default (exclude POW)
    for token in ("STR", "DEX", "CON", "INT", "SIZ", "APP", "EDU"):
        raw = _coc_raw_for(attacker, token)
        s = re.sub(rf"\b{token}\b", str(_tens(raw)), s)

    return s


def cast_arts(attacker: str, art: str, target: Optional[str] = None, center: Optional[Tuple[int, int]] = None, mp_spent: Optional[int] = None, reason: str = "") -> ToolResponse:
    """Cast an Originium Art.

    Minimal single-target implementation:
    - contest: cast_skill vs resist skill（不再支持 POW 作为对抗属性，统一使用技能，如 Arts_Resist）
    - MP: fixed or variable; mp_spent participates in formulas（不再支持 POWER 占位符）
    - reduction: arts -> arts_barrier; physical -> physical_armor
    - tags: no-guard-intercept (skips guard), line-of-sight (cover==total blocks)
    """
    # Gate by statuses (dying/control)
    blocked, msg = _blocked_action(str(attacker), "cast")
    if blocked:
        return ToolResponse(content=[TextBlock(type="text", text=msg)], metadata={"ok": False, "attacker": attacker, "art_id": str(art), "error_type": "attacker_unable"})
    # participants gate
    if WORLD.participants:
        if str(attacker) not in WORLD.participants:
            return ToolResponse(content=[TextBlock(type="text", text=f"参与者限制：{attacker} 非参与者")], metadata={"ok": False, "error_type": "not_participant", "attacker": attacker})
        if target and str(target) not in WORLD.participants:
            return ToolResponse(content=[TextBlock(type="text", text=f"参与者限制：{target} 非参与者")], metadata={"ok": False, "error_type": "not_participant", "target": target})

    ad = dict((WORLD.arts_defs or {}).get(str(art), {}) or {})
    if not ad:
        return ToolResponse(content=[TextBlock(type="text", text=f"未知术式 {art}")], metadata={"ok": False, "error_type": "unknown_art"})

    cast_skill = str(ad.get("cast_skill") or "")
    resist = str(ad.get("resist") or "")
    if not cast_skill or not resist:
        return ToolResponse(content=[TextBlock(type="text", text=f"术式定义不完整（缺少 cast_skill 或 resist）：{art}")], metadata={"ok": False, "error_type": "art_def_invalid", "art": art})
    rng = int(ad.get("range_steps", 6))
    dtype = str(ad.get("damage_type", "arts")).lower()
    dmg_expr = str(ad.get("damage") or "")
    heal_expr = str(ad.get("heal") or "")
    ctrl = dict(ad.get("control") or {}) if isinstance(ad.get("control"), dict) else {}
    tags = set(ad.get("tags") or [])
    mp_cfg = dict(ad.get("mp") or {}) if isinstance(ad.get("mp"), dict) else {}
    mp_cost = int(mp_cfg.get("cost", 0))
    mp_mode = "variable" if bool(mp_cfg.get("variable", False)) else "fixed"
    mp_max = int(mp_cfg.get("max", 0) or 0)

    # Target resolution (single target minimal)
    tgt = str(target) if target else None
    if not tgt:
        return ToolResponse(content=[TextBlock(type="text", text="缺少目标 target")], metadata={"ok": False, "error_type": "missing_param", "param": "target"})

    # Optional guard interception: default off to preserve current semantics.
    pre_logs: List[TextBlock] = []
    guard_meta: Optional[Dict[str, Any]] = None
    allow_guard = ("guard-intercept" in tags) or ("allow-guard-intercept" in tags)
    if allow_guard:
        tgt2, guard_meta, pre_logs = _attack_resolve_guard_interception(attacker, tgt, rng)
        tgt = tgt2

    # Range check（after possible guard interception）
    dist = _attack_compute_distance(attacker, tgt)
    if dist is None or dist > rng:
        return ToolResponse(
            content=pre_logs + [TextBlock(type="text", text=f"距离不足：{attacker}->{tgt} {dist if dist is not None else '?'}步/触及{rng}步")],
            metadata={"ok": False, "error_type": "out_of_reach", **({"guard": guard_meta} if guard_meta else {})},
        )

    # Line-of-sight check (simplified via cover)
    if "line-of-sight" in tags:
        try:
            if get_cover(tgt) == "total":
                return ToolResponse(content=[TextBlock(type="text", text=f"{tgt} 视线受阻，本术式需要视线")], metadata={"ok": False, "error_type": "no_los", "target": tgt})
        except Exception:
            pass

    # MP spending（支持“过载施术”分支）
    mp_logs: List[TextBlock] = []
    overcharge = False
    atk_value_override: Optional[int] = None
    if mp_mode == "fixed":
        eff_spent = max(0, int(mp_cost))
    else:
        req = max(0, int(mp_cost))
        want = int(mp_spent) if mp_spent is not None else req
        cap = int(WORLD.characters.get(attacker, {}).get("mp", req))
        hard_max = mp_max if mp_max > 0 else cap
        eff_spent = max(req, min(hard_max, want, cap))
    spent_res = spend_mp(attacker, eff_spent)
    if not (spent_res.metadata or {}).get("ok", False):
        meta = spent_res.metadata or {}
        err = str(meta.get("error_type") or "")
        # 仅在 MP 不足且术式确有 MP 消耗时允许过载；否则维持原有失败行为
        if err == "mp_insufficient" and mp_cost > 0:
            overcharge = True
            # 读当前 MP 与上限，执行“耗尽剩余 MP”并记录日志
            st = WORLD.characters.setdefault(str(attacker), {})
            try:
                cur_mp = int(st.get("mp", 0))
            except Exception:
                cur_mp = 0
            try:
                cap_mp = int(st.get("max_mp", 0))
            except Exception:
                cap_mp = 0
            if cur_mp > 0:
                st["mp"] = 0
                eff_spent = cur_mp
                mp_logs.append(
                    TextBlock(
                        type="text",
                        text=f"{attacker} MP 不足，强行过载施术，耗尽剩余 MP（0/{cap_mp or '?'}）。",
                    )
                )
            else:
                eff_spent = 0
                mp_logs.append(
                    TextBlock(
                        type="text",
                        text=f"{attacker} 在 MP 为 0 的状态下强行过载施术。",
                    )
                )
            # 过载施术：本次攻击检定 −20（通过显式 value 覆盖实现）
            try:
                base_val = _coc_skill_value(attacker, cast_skill)
            except Exception:
                base_val = 0
            atk_value_override = max(0, int(base_val) - 20)
            if atk_value_override <= 0:
                atk_value_override = 1
            mp_logs.append(
                TextBlock(
                    type="text",
                    text=f"过载惩罚：本次 {cast_skill} 检定视为在原值基础上 −20 进行。",
                )
            )
            # 过载应激：基础 1d4，应随 overcharge_step 升档
            over_expr = "1d4"

            def _step_expr(expr: str) -> str:
                e = expr.replace(" ", "")
                if e == "1d4":
                    return "1d6"
                if e in ("1d6", "1d6+0"):
                    return "1d6+1"
                if e in ("1d6+1", "1d6+2"):
                    return "2d6"
                if e == "2d6":
                    return "2d6+2"
                return expr

            try:
                inf = _ensure_infection_block(attacker)
                step = int(inf.get("overcharge_step", 0))
            except Exception:
                step = 0
            for _ in range(max(0, step)):
                over_expr = _step_expr(over_expr)
            try:
                exp_res = apply_exposure(
                    attacker,
                    level="light",
                    source="术式过载",
                    dice_expr=over_expr,
                    bonus=0,
                )
                for blk in (exp_res.content or []):
                    if isinstance(blk, dict) and blk.get("type") == "text":
                        mp_logs.append(blk)
            except Exception:
                # 过载应激失败不阻断施术本体，仅不追加说明
                pass
        else:
            return spent_res

    # Contest / check
    parts: List[TextBlock] = list(pre_logs) + mp_logs
    success, logs_check, oppose_meta, atk_check_meta = _attack_run_check_or_contest(
        attacker,
        tgt,
        skill_name=cast_skill,
        defense_skill_name=resist,
        attacker_value=atk_value_override,
    )
    if logs_check:
        parts.extend(logs_check)

    # Success level only for narration; no multiplier in damage/heal
    level = (
        (atk_check_meta or {}).get("success_level")
        if atk_check_meta is not None
        else (oppose_meta or {}).get("a", {}).get("success_level")
    )
    lvl = str(level or "fail")
    mult = 1.0

    effects: List[Dict[str, Any]] = []
    hp_before = int(WORLD.characters.get(tgt, {}).get("hp", 0))
    dmg_total = 0
    healed = 0
    if success and dmg_expr:
        expr = _replace_art_tokens(attacker, dmg_expr, mp_spent=eff_spent, base_cost=mp_cost)
        # 表达式中不允许出现字母（仅允许 NdM 与 +/- 常数）；若含未替换标记（如 MP/POW），直接报错
        import re as _re
        # Allow classic dice notation NdM with optional +/- constants. We forbid any
        # letters other than 'd' (case-insensitive) to prevent leaking tokens like
        # POW/MP/skill names into the arithmetic expression.
        expr_norm = str(expr or "").lower().replace(" ", "")
        if _re.search(r"[^0-9d+\-]", expr_norm):
            return ToolResponse(
                content=parts + [TextBlock(type="text", text=f"术式伤害表达式不被支持：{dmg_expr}")],
                metadata={"ok": False, "error_type": "art_damage_expr_invalid", "expr": dmg_expr},
            )
        # Apply using unified damage step
        dfd = WORLD.characters.get(tgt, {})
        dmg_logs, total, reduced, final = _attack_apply_damage(
            tgt,
            damage_expr_base=expr,
            damage_type=dtype,
            defender_sheet=dfd,
        )
        # Reword first log for arts clarity (optional; keep as-is for consistency)
        parts.extend(dmg_logs)
        dmg_total = final
        effects.append({"who": tgt, "damage": final, "reduced_by": reduced})

    if success and heal_expr:
        expr = _replace_art_tokens(attacker, heal_expr, mp_spent=eff_spent, base_cost=mp_cost)
        import re as _re
        expr_norm = str(expr or "").lower().replace(" ", "")
        if _re.search(r"[^0-9d+\-]", expr_norm):
            return ToolResponse(
                content=parts + [TextBlock(type="text", text=f"术式治疗表达式不被支持：{heal_expr}")],
                metadata={"ok": False, "error_type": "art_heal_expr_invalid", "expr": heal_expr},
            )
        roll = roll_dice(expr)
        val = int((roll.metadata or {}).get("total", 0))
        healed = max(0, val)
        parts.append(TextBlock(type="text", text=f"术式治疗：{expr} -> {healed}"))
        heal_res = heal(tgt, healed)
        for blk in (heal_res.content or []):
            if isinstance(blk, dict) and blk.get("type") == "text":
                parts.append(blk)
        effects.append({"who": tgt, "heal": healed})

    # Control effect (unified status management)
    if success and ctrl.get("effect"):
        eff = str(ctrl.get("effect"))
        dur_expr = str(ctrl.get("duration") or "1")
        dur_str = _replace_art_tokens(attacker, dur_expr, mp_spent=eff_spent, base_cost=mp_cost)
        import re as _re
        if _re.search(r"[A-Za-z]", dur_str):
            return ToolResponse(content=parts + [TextBlock(type="text", text=f"术式持续时间表达式不被支持：{dur_expr}")], metadata={"ok": False, "error_type": "art_duration_expr_invalid", "expr": dur_expr})
        try:
            dur_val = int(eval(dur_str, {"__builtins__": {}}, {}))  # simple integer expression
        except Exception:
            dur_val = 1
        parts.append(TextBlock(type="text", text=f"控制：{eff}（持续 {dur_val} 轮）"))
        try:
            sr = add_status(tgt, eff, duration_rounds=dur_val, kind="control", source=attacker)
            for blk in (sr.content or []):
                if isinstance(blk, dict) and blk.get("type") == "text":
                    parts.append(blk)
        except Exception:
            pass
        effects.append({"who": tgt, "state": eff, "duration_rounds": int(dur_val)})

    hp_after = int(WORLD.characters.get(tgt, {}).get("hp", 0))
    WORLD._touch()
    meta = {
        "ok": True,
        "attacker": attacker,
        "art_id": str(art),
        "target": tgt,
        "mp_spent": int(eff_spent),
        "success": bool(success),
        "success_level": lvl,
        "hp_before": hp_before,
        "hp_after": hp_after,
        "effects": effects,
    }
    if guard_meta:
        meta["guard"] = guard_meta
    return ToolResponse(content=parts, metadata=meta)


def _signed(x: int) -> str:
    return f"+{x}" if x >= 0 else str(x)


# ---- Objective status helpers ----
def complete_objective(name: str, note: str = ""):
    nm = str(name)
    if nm not in WORLD.objectives:
        WORLD.objectives.append(nm)
    WORLD.objective_status[nm] = "done"
    if note:
        WORLD.objective_notes[nm] = note
    return ToolResponse(content=[TextBlock(type="text", text=f"目标完成：{nm}")], metadata={"objectives": list(WORLD.objectives), "status": dict(WORLD.objective_status)})

def block_objective(name: str, reason: str = ""):
    nm = str(name)
    if nm not in WORLD.objectives:
        WORLD.objectives.append(nm)
    WORLD.objective_status[nm] = "blocked"
    if reason:
        WORLD.objective_notes[nm] = reason
    suffix = f"，理由：{reason}" if reason else ""
    return ToolResponse(content=[TextBlock(type="text", text=f"目标受阻：{nm}{suffix}")], metadata={"objectives": list(WORLD.objectives), "status": dict(WORLD.objective_status)})

# ---- Event clock ----
def schedule_event(name: str, at_min: int, note: str = "", effects: Optional[List[Dict[str, Any]]] = None):
    WORLD.events.append({"name": str(name), "at": int(at_min), "note": str(note), "effects": list(effects or [])})
    WORLD.events.sort(key=lambda x: x.get("at", 0))
    return ToolResponse(content=[TextBlock(type="text", text=f"计划事件：{name}@{int(at_min)}分钟")], metadata={"queued": len(WORLD.events)})

def process_events():
    outputs: List[TextBlock] = []
    due = [ev for ev in WORLD.events if int(ev.get("at", 0)) <= WORLD.time_min]
    WORLD.events = [ev for ev in WORLD.events if int(ev.get("at", 0)) > WORLD.time_min]
    for ev in due:
        name = ev.get("name", "(事件)")
        note = ev.get("note", "")
        outputs.append(TextBlock(type="text", text=f"[事件] {name}：{note}")) if note else outputs.append(TextBlock(type="text", text=f"[事件] {name}"))
        for eff in (ev.get("effects") or []):
            try:
                kind = eff.get("kind")
                if kind == "add_objective":
                    add_objective(str(eff.get("name")))
                elif kind == "complete_objective":
                    complete_objective(str(eff.get("name")))
                elif kind == "block_objective":
                    block_objective(str(eff.get("name")), str(eff.get("reason", "")))
                elif kind == "relation":
                    # require absolute target (value or target); delta fallback removed
                    a, b = eff.get("a"), eff.get("b")
                    if a and b:
                        if "value" in eff:
                            v = eff.get("value")
                        elif "target" in eff:
                            v = eff.get("target")
                        else:
                            raise ValueError("relation effect requires 'value' or 'target'")
                        set_relation(str(a), str(b), int(v), reason=str(eff.get("reason", "")))
                elif kind == "grant":
                    grant_item(str(eff.get("target")), str(eff.get("item")), int(eff.get("n", 1)))
                elif kind == "damage":
                    damage(str(eff.get("target")), int(eff.get("amount", 0)))
                elif kind == "heal":
                    heal(str(eff.get("target")), int(eff.get("amount", 0)))
                elif kind == "end":
                    # Allow timeline events to force an ending
                    eid = eff.get("ending_id")
                    note = eff.get("note") or eff.get("message") or ""
                    try:
                        end_now(str(eid) if eid is not None else None, note=str(note))
                    except Exception:
                        pass
            except Exception:
                outputs.append(TextBlock(type="text", text=f"[事件执行失败] {eff}"))
    if outputs:
        return ToolResponse(content=outputs, metadata={"fired": len(due)})
    return ToolResponse(content=[], metadata={"fired": 0})

# ---- Atmosphere helpers ----
def adjust_tension(delta: int):
    WORLD.tension = max(0, min(5, int(WORLD.tension) + int(delta)))
    return ToolResponse(content=[TextBlock(type="text", text=f"(气氛){'升' if delta>0 else '降' if delta<0 else '稳'}至 {WORLD.tension}")], metadata={"tension": WORLD.tension})

def add_mark(text: str):
    s = str(text or "").strip()
    if s:
        WORLD.marks.append(s)
        if len(WORLD.marks) > 10:
            WORLD.marks = WORLD.marks[-10:]
    return ToolResponse(content=[TextBlock(type="text", text=f"(环境刻痕)+{s}")], metadata={"marks": list(WORLD.marks)})


# ---- Endings evaluation ----

def set_endings(defs: List[Dict[str, Any]]) -> ToolResponse:
    """Replace endings table with a normalized list and clear any previous result."""
    WORLD.endings_defs = _normalize_endings_list(defs)
    WORLD.ending_state = None
    WORLD._touch()
    return ToolResponse(
        content=[TextBlock(type="text", text=f"载入结局规则：{len(WORLD.endings_defs)} 项")],
        metadata={"ok": True, "count": len(WORLD.endings_defs)},
    )


def _alive(name: str) -> bool:
    try:
        st = WORLD.characters.get(str(name), {}) or {}
        hp = int(st.get("hp", 0))
        dying = st.get("dying_turns_left") is not None
        return hp > 0 and not dying
    except Exception:
        return False


def _eval_when(node: Any) -> tuple[bool, List[str]]:
    """Evaluate a when-clause recursively and return (matched, reasons)."""
    reasons: List[str] = []
    # Logical composition
    if isinstance(node, dict):
        if "all" in node:
            parts = node.get("all")
            if not isinstance(parts, list):
                return False, []
            acc = True
            all_reasons: List[str] = []
            for p in parts:
                ok, rs = _eval_when(p)
                if ok:
                    all_reasons.extend(rs)
                else:
                    acc = False
            return acc, (all_reasons if acc else [])
        if "any" in node:
            parts = node.get("any")
            if not isinstance(parts, list):
                return False, []
            any_reasons: List[str] = []
            for p in parts:
                ok, rs = _eval_when(p)
                if ok:
                    any_reasons.extend(rs)
                    return True, any_reasons
            return False, []
        if "not" in node:
            ok, _ = _eval_when(node.get("not"))
            return (not ok), ([] if ok else ["not"])  # minimal reason

        # Leaf conditions
        # 1) objectives
        if "objectives" in node:
            spec = node.get("objectives") or {}
            if not isinstance(spec, dict):
                return False, []
            names = spec.get("names")
            require = str(spec.get("require", "all")).lower()
            status = str(spec.get("status", "done")).lower()
            objs = list(WORLD.objectives or [])
            status_map = dict(WORLD.objective_status or {})
            target_names = [str(n) for n in (names or objs)] if names else objs
            if not target_names:
                return False, []
            def _match_one(nm: str) -> bool:
                st = str(status_map.get(str(nm), "pending")).lower()
                return (status == "any") or (st == status)
            vals = [_match_one(n) for n in target_names]
            ok = all(vals) if require == "all" else any(vals)
            if ok:
                reasons.append(
                    f"目标{('全部' if require=='all' else '部分')}达成(status={status})"
                )
            return ok, reasons

        # 2) time gates
        if "time_before" in node or "time_at_least" in node:
            if "time_before" in node:
                t = _parse_time_to_min(node.get("time_before"))
                if t is None:
                    return False, []
                ok = int(WORLD.time_min) < int(t)
                if ok:
                    reasons.append(f"时间早于{t}分钟")
                return ok, reasons
            if "time_at_least" in node:
                t = _parse_time_to_min(node.get("time_at_least"))
                if t is None:
                    return False, []
                ok = int(WORLD.time_min) >= int(t)
                if ok:
                    reasons.append(f"时间不早于{t}分钟")
                return ok, reasons

        # 3) actors_alive / actors_dead
        if "actors_alive" in node or "actors_dead" in node:
            key = "actors_alive" if "actors_alive" in node else "actors_dead"
            spec = node.get(key) or {}
            if not isinstance(spec, dict):
                return False, []
            names = [str(n) for n in (spec.get("names") or [])]
            require = str(spec.get("require", "all")).lower()
            if not names:
                return False, []
            vals = [(_alive(n) if key == "actors_alive" else (not _alive(n))) for n in names]
            ok = all(vals) if require == "all" else any(vals)
            if ok:
                reasons.append(
                    ("角色存活:" if key == "actors_alive" else "角色死亡:") + ", ".join(names)
                )
            return ok, reasons

        # 4) participants alive counts
        if "participants_alive_at_least" in node or "participants_alive_at_most" in node:
            try:
                cur = [n for n in (WORLD.participants or []) if _alive(n)]
            except Exception:
                cur = []
            if "participants_alive_at_least" in node:
                try:
                    need = int(node.get("participants_alive_at_least"))
                except Exception:
                    need = None
                ok = (need is not None) and (len(cur) >= int(need))
                if ok:
                    reasons.append(f"存活参与者≥{need}")
                return ok, reasons
            if "participants_alive_at_most" in node:
                try:
                    cap = int(node.get("participants_alive_at_most"))
                except Exception:
                    cap = None
                ok = (cap is not None) and (len(cur) <= int(cap))
                if ok:
                    reasons.append(f"存活参与者≤{cap}")
                return ok, reasons

        # 5) hostiles_present gate
        if "hostiles_present" in node:
            val = node.get("hostiles_present")
            thr = None
            if isinstance(val, dict):
                try:
                    thr = int(val.get("threshold"))
                except Exception:
                    thr = None
                want = bool(val.get("value", True))
            else:
                want = bool(val)
            hp = hostiles_present(WORLD.participants or None, threshold=(thr if thr is not None else -10))
            ok = (hp is True) if want else (hp is False)
            if ok:
                reasons.append("敌对存在" if want else "已清场")
            return ok, reasons

        # 6) marks_contains
        if "marks_contains" in node:
            val = node.get("marks_contains")
            marks = list(WORLD.marks or [])
            if isinstance(val, str):
                ok = val in marks
                if ok:
                    reasons.append(f"刻痕包含：{val}")
                return ok, reasons
            if isinstance(val, list):
                # require any by default
                ok = any(str(x) in marks for x in val)
                if ok:
                    reasons.append("刻痕命中任一")
                return ok, reasons
            return False, []

        # 7) tension gate
        if "tension_at_least" in node or "tension_at_most" in node:
            try:
                tv = int(WORLD.tension)
            except Exception:
                tv = 0
            if "tension_at_least" in node:
                try:
                    need = int(node.get("tension_at_least"))
                except Exception:
                    need = None
                ok = (need is not None) and (tv >= int(need))
                if ok:
                    reasons.append(f"气氛≥{need}")
                return ok, reasons
            if "tension_at_most" in node:
                try:
                    cap = int(node.get("tension_at_most"))
                except Exception:
                    cap = None
                ok = (cap is not None) and (tv <= int(cap))
                if ok:
                    reasons.append(f"气氛≤{cap}")
                return ok, reasons

        # 8) location_is
        if "location_is" in node:
            val = node.get("location_is")
            loc = str(WORLD.location or "")
            if isinstance(val, str):
                ok = (loc == val)
                if ok:
                    reasons.append(f"地点={val}")
                return ok, reasons
            if isinstance(val, list):
                ok = any(loc == str(x) for x in val)
                if ok:
                    reasons.append("地点命中")
                return ok, reasons
            return False, []

    # Unknown/unhandled clause -> no match
    return False, []


def evaluate_endings() -> ToolResponse:
    """Evaluate all configured endings and cache the first matching result.

    Returns ToolResponse with metadata: { ok, ended, ending_id?, label?, outcome?, reasons, matched_ids }
    """
    # If already ended, keep it stable
    if WORLD.ending_state and bool(WORLD.ending_state.get("ended")):
        return ToolResponse(content=[], metadata=dict(WORLD.ending_state))

    defs = list(WORLD.endings_defs or [])
    if not defs:
        return ToolResponse(content=[], metadata={"ok": True, "ended": False, "matched_ids": []})
    # Sort by priority desc, keep original order for ties
    defs.sort(key=lambda d: int(d.get("priority", 0) or 0), reverse=True)
    matched: List[str] = []
    for d in defs:
        cond = d.get("when")
        ok, reasons = _eval_when(cond)
        if ok:
            eid = d.get("id") or ""
            matched.append(str(eid))
            # Freeze outcome
            st = {
                "ok": True,
                "ended": True,
                "ending_id": (str(eid) or None),
                "label": (d.get("label") or None),
                "outcome": (d.get("outcome") or None),
                "reasons": reasons,
                "time_min": int(WORLD.time_min),
            }
            WORLD.ending_state = dict(st)
            WORLD._touch()
            return ToolResponse(content=[TextBlock(type="text", text=f"结局触发：{d.get('label') or d.get('id') or ''}")], metadata={**st, "matched_ids": matched})
    return ToolResponse(content=[], metadata={"ok": True, "ended": False, "matched_ids": matched})


def story_ended() -> Dict[str, Any]:
    """Lightweight query for main/orchestrator to check end-state.

    - If ended already, return frozen WORLD.ending_state
    - Else, evaluate once and return the result
    """
    if WORLD.ending_state and bool(WORLD.ending_state.get("ended")):
        return dict(WORLD.ending_state)
    res = evaluate_endings()
    return dict(res.metadata or {})


def end_now(ending_id: Optional[str] = None, note: str = "") -> ToolResponse:
    """Force an immediate ending with an optional id/label note.

    Idempotent: if already ended, returns the existing result.
    """
    if WORLD.ending_state and bool(WORLD.ending_state.get("ended")):
        return ToolResponse(content=[], metadata=dict(WORLD.ending_state))
    eid = str(ending_id).strip() if ending_id is not None else ""
    st = {
        "ok": True,
        "ended": True,
        "ending_id": (eid or None),
        "label": (note or None),
        "outcome": None,
        "reasons": ([note] if note else []),
        "time_min": int(WORLD.time_min),
    }
    WORLD.ending_state = dict(st)
    WORLD._touch()
    return ToolResponse(content=[TextBlock(type="text", text=f"结局触发：{eid or '(manual)'}")], metadata=st)


# ============================================================
# Tool parameter validation (centralized in world)
# ============================================================

from dataclasses import dataclass as _dataclass

@_dataclass(frozen=True)
class ToolSpec:
    required: Set[str]
    actor_keys: Set[str] = frozenset()
    numeric_min0: Set[str] = frozenset()   # params that must be non-negative integers
    participants_policy: str = "none"      # one of: none | source | both
    source_param: Optional[str] = None     # when policy=source, which param holds the source actor name
    extra_policy: str = "ignore"           # ignore | error


TOOL_SPECS: Dict[str, ToolSpec] = {
    "perform_attack": ToolSpec(
        required={"attacker", "defender", "weapon"},
        actor_keys={"attacker", "defender"},
        participants_policy="both",
    ),
    "advance_position": ToolSpec(
        required={"name", "target"},
        actor_keys={"name"},
        numeric_min0=set(),
        participants_policy="source",
        source_param="name",
    ),
    "use_entrance": ToolSpec(
        required={"name"},
        actor_keys={"name"},
        participants_policy="source",
        source_param="name",
    ),
    "adjust_relation": ToolSpec(
        required={"a", "b", "value"},
        actor_keys={"a", "b"},
        participants_policy="none",
    ),
    "transfer_item": ToolSpec(
        required={"target", "item"},
        actor_keys={"target"},
        numeric_min0=set(),
        participants_policy="none",
    ),
    "set_protection": ToolSpec(
        required={"guardian", "protectee"},
        actor_keys={"guardian", "protectee"},
        participants_policy="both",
    ),
    "clear_protection": ToolSpec(
        required=set(),
        actor_keys={"guardian", "protectee"},
        participants_policy="none",
    ),
    "first_aid": ToolSpec(
        required={"name", "target"},
        actor_keys={"name", "target"},
        participants_policy="both",
    ),
    "cast_arts": ToolSpec(
        required={"attacker", "art", "target"},
        actor_keys={"attacker", "target"},
        participants_policy="both",
    ),
    "apply_exposure": ToolSpec(
        required={"name"},
        actor_keys={"name"},
        numeric_min0={"bonus"},
        participants_policy="source",
        source_param="name",
    ),
    "advance_infection_stage": ToolSpec(
        required={"name"},
        actor_keys={"name"},
        participants_policy="none",
    ),
    "get_infection_state": ToolSpec(
        required={"name"},
        actor_keys={"name"},
        participants_policy="none",
    ),
}


def _coerce_nonneg_int(v: Any) -> Optional[int]:
    try:
        iv = int(v)
    except Exception:
        return None
    return iv if iv >= 0 else None


def _normalize_params_for(tool: str, params: Dict[str, Any]) -> Dict[str, Any]:
    p = dict(params or {})
    # cast_arts: ignore any provided mp_spent (统一由系统自动结算，防止模型传入该参数)
    if tool == "cast_arts":
        if "mp_spent" in p:
            try:
                del p["mp_spent"]
            except Exception:
                p.pop("mp_spent", None)
    return p


def _validated_call(tool_name: str, fn, params: Dict[str, Any]) -> ToolResponse:
    spec = TOOL_SPECS.get(tool_name)
    if not spec:
        return ToolResponse(content=[TextBlock(type="text", text=f"未知工具 {tool_name}")], metadata={"ok": False, "error_type": "unknown_tool"})

    p = _normalize_params_for(tool_name, dict(params or {}))

    # 1) required
    for k in spec.required:
        if k not in p or p[k] in (None, ""):
            return ToolResponse(content=[TextBlock(type="text", text=f"缺少参数：{k}")], metadata={"ok": False, "error_type": "missing_param", "param": k})

    # 2) numeric_min0
    for k in spec.numeric_min0:
        if k in p:
            iv = _coerce_nonneg_int(p[k])
            if iv is None:
                return ToolResponse(content=[TextBlock(type="text", text=f"参数需为非负整数：{k}")], metadata={"ok": False, "error_type": "invalid_type", "param": k})
            p[k] = iv

    # 3) extra validation per tool
    # 3.1) actor_keys to str
    for k in spec.actor_keys:
        if k in p and p[k] is not None:
            p[k] = str(p[k])

    # 3.2) target normalization for advance_position: accept [x,y] or a named point
    if tool_name == "advance_position":
        tgt = p.get("target")
        # Case A: [x, y]
        if isinstance(tgt, (list, tuple)) and len(tgt) >= 2:
            try:
                tx, ty = int(tgt[0]), int(tgt[1])
                p["target"] = (tx, ty)
            except Exception:
                return ToolResponse(
                    content=[TextBlock(type="text", text="参数错误：target 元素必须为整数，如 [1, 1]")],
                    metadata={"ok": False, "error_type": "invalid_type", "param": "target"},
                )
        # Case B: string label -> resolve to coordinates
        elif isinstance(tgt, str):
            nm = str(p.get("name", ""))
            resolved = _resolve_named_target_for_move(nm, tgt)
            if not resolved:
                return ToolResponse(
                    content=[TextBlock(type="text", text=f"未能解析目标点：{tgt}。请使用 [x,y] 或入口名/角色名/目标点名称。")],
                    metadata={"ok": False, "error_type": "invalid_value", "param": "target", "value": tgt},
                )
            (tx, ty), meta = resolved
            p["target"] = (int(tx), int(ty))
            # Preserve friendly label for narration if available
            if meta.get("kind"):
                p["target_kind"] = str(meta.get("kind"))
            label = meta.get("label") or (tgt if meta.get("kind") != "coords" else None)
            if label:
                p["target_label"] = str(label)
        else:
            return ToolResponse(
                content=[TextBlock(type="text", text="参数错误：advance_position.target 必须为 [x,y] 或 目标点名称（字符串）")],
                metadata={"ok": False, "error_type": "invalid_type", "param": "target"},
            )

    # 4) participants policy
    if WORLD.participants:
        if spec.participants_policy == "source" and spec.source_param:
            src = str(p.get(spec.source_param, ""))
            if src and src not in WORLD.participants:
                return ToolResponse(content=[TextBlock(type="text", text=f"参与者限制：{spec.source_param}={src} 非参与者")], metadata={"ok": False, "error_type": "not_participant", "param": spec.source_param, "value": src})
        elif spec.participants_policy == "both":
            for k in spec.actor_keys:
                v = p.get(k)
                if isinstance(v, str) and v not in WORLD.participants:
                    return ToolResponse(content=[TextBlock(type="text", text=f"参与者限制：{k}={v} 非参与者")], metadata={"ok": False, "error_type": "not_participant", "param": k, "value": v})

    # 5) call
    try:
        return fn(**p)
    except TypeError as exc:
        return ToolResponse(content=[TextBlock(type="text", text=str(exc))], metadata={"ok": False, "error_type": "invalid_parameters"})
    except Exception as exc:  # pragma: no cover
        return ToolResponse(content=[TextBlock(type="text", text=str(exc))], metadata={"ok": False, "error_type": exc.__class__.__name__})


def validated_tool_dispatch() -> Dict[str, Any]:
    """Return a mapping of tool-name -> validated function callable(**params).

    These names are expected by the LLM prompt (perform_attack, advance_position, ...).
    """
    def _adv_no_steps(**p):
        # Drop any external 'steps' parameter to enforce auto-movement only
        if "steps" in p:
            p = {k: v for k, v in p.items() if k != "steps"}
        return _validated_call("advance_position", move_towards, p)

    return {
        "perform_attack": lambda **p: _validated_call("perform_attack", attack_with_weapon, p),
        "advance_position": _adv_no_steps,
        "use_entrance": lambda **p: _validated_call("use_entrance", use_entrance, p),
        "adjust_relation": lambda **p: _validated_call("adjust_relation", set_relation, p),
        "transfer_item": lambda **p: _validated_call("transfer_item", grant_item, p),
        "set_protection": lambda **p: _validated_call("set_protection", set_guard, p),
        "clear_protection": lambda **p: _validated_call("clear_protection", clear_guard, p),
        "first_aid": lambda **p: _validated_call("first_aid", first_aid, p),
        "cast_arts": lambda **p: _validated_call("cast_arts", cast_arts, p),
        "apply_exposure": lambda **p: _validated_call("apply_exposure", apply_exposure, p),
        "advance_infection_stage": lambda **p: _validated_call("advance_infection_stage", advance_infection_stage, p),
        "get_infection_state": lambda **p: _validated_call("get_infection_state", get_infection_state, p),
    }
