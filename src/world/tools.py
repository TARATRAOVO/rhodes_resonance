# Minimal world state and tools for the demo; designed to be pure and easy to test.
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Tuple, Any, List, Optional, Set, Union
import math
import random
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
    # --- Combat (rounds) ---
    in_combat: bool = False
    round: int = 1
    turn_idx: int = 0
    initiative_order: List[str] = field(default_factory=list)
    initiative_scores: Dict[str, int] = field(default_factory=dict)
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

    def _touch(self) -> None:
        try:
            self.version += 1
        except Exception:
            # be defensive; never fail mutators due to versioning
            self.version = int(self.version or 0) + 1

    def snapshot(self) -> dict:
        # Build a sanitized weapon-def summary for consumers (id -> selected fields)
        def _weapon_summary():
            out: Dict[str, Dict[str, Any]] = {}
            for wid, data in (self.weapon_defs or {}).items():
                try:
                    d = dict(data or {})
                except Exception:
                    d = {}
                try:
                    rs = int(d.get("reach_steps", DEFAULT_REACH_STEPS))
                except Exception:
                    rs = int(DEFAULT_REACH_STEPS)
                out[str(wid)] = {
                    "reach_steps": max(1, rs),
                    "skill": str(d.get("skill", "")),
                    "defense_skill": str(d.get("defense_skill", "")),
                    "damage": str(d.get("damage", "")),
                    "damage_type": str(d.get("damage_type", "physical")),
                }
            return out

        return {
            "version": int(self.version),
            "time_min": self.time_min,
            "weather": self.weather,
            "relations": {f"{a}->{b}": v for (a, b), v in self.relations.items()},
            "inventory": self.inventory,
            "characters": self.characters,
            "positions": {k: list(v) for k, v in self.positions.items()},
            "objective_positions": {k: list(v) for k, v in self.objective_positions.items()},
            # removed hidden_enemies entirely per design (no implicit enemies)
            "location": self.location,
            "objectives": list(self.objectives),
            "scene_details": list(self.scene_details),
            "objective_status": dict(self.objective_status),
            "objective_notes": dict(self.objective_notes),
            "tension": int(self.tension),
            "marks": list(self.marks),
            "participants": list(self.participants),
            "guardians": {k: list(v) for k, v in self.guardians.items()},
            "combat": {
                "in_combat": bool(self.in_combat),
                "round": int(self.round),
                "turn_idx": int(self.turn_idx),
                "initiative": list(self.initiative_order),
                "initiative_scores": dict(self.initiative_scores),
                "turn_state": {k: dict(v) for k, v in self.turn_state.items()},
            },
            # Weapon data
            "weapons": sorted(list(self.weapon_defs.keys())),
            "weapon_defs": _weapon_summary(),
            # Arts data (for diagnostics; full details are available via get_arts_defs())
            "arts": sorted(list(self.arts_defs.keys())),
        }


WORLD = World()

# --- tools ---

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
        return ToolResponse(content=[TextBlock(type="text", text=msg)], metadata={"ok": False})
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
    """Return grid steps between two actors; None if any position missing."""
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
    sheet = WORLD.characters.get(name, {})
    try:
        val = sheet.get("move_speed_steps")
        if val is not None:
            return int(val)
    except Exception:
        pass
    return int(WORLD.speeds.get(name, _default_move_steps()))


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


def move_towards(name: str, target: Tuple[int, int], steps: Optional[int] = None) -> ToolResponse:
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
            metadata={"ok": False, "moved": 0, "position": list(pos), "blocked": True},
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
    text = (
        f"{name} 向 ({tx}, {ty}) 移动 {format_distance_steps(moved)}，现位于 ({x}, {y})。"
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
        },
    )


# describe_world has been removed by design. Use WORLD.snapshot() for raw data
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
    return ToolResponse(content=[TextBlock(type="text", text=text)], metadata={"ok": True, **WORLD.snapshot()})


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
    """Set walking speed for an actor (steps only by default).

    Args:
        name: Actor identifier.
        value: Numeric speed value.
        unit: 'steps' (default) or 'feet'.
    """

    unit_norm = (unit or "steps").lower()
    if unit_norm not in {"steps", "feet"}:
        unit_norm = "steps"

    if unit_norm == "feet":
        # Assume standard 5ft per grid step
        steps = max(0, int(math.ceil(float(value) / 5.0)))
    else:
        steps = max(0, int(round(float(value))))

    if steps == 0 and value > 0:
        steps = 1
    WORLD.speeds[str(name)] = steps
    WORLD._touch()
    return ToolResponse(
        content=[TextBlock(type="text", text=f"速度设定：{name} {format_distance_steps(steps)}")],
        metadata={"ok": True, "name": name, "speed_steps": steps},
    )


def roll_initiative(participants: Optional[List[str]] = None):
    names = list(participants or list(WORLD.characters.keys()))
    # Remove any downed participants up-front so turns never start on a dead unit
    names = [n for n in names if _is_alive(n)]
    import random as _rand
    scores: Dict[str, int] = {}
    for nm in names:
        scores[nm] = _coc_dex_of(nm)
    # sort desc by DEX; tiebreaker by random then name
    ordered = sorted(names, key=lambda n: (scores.get(n, 0), _rand.random(), str(n)), reverse=True)
    WORLD.initiative_scores = scores
    WORLD.initiative_order = ordered
    WORLD.round = 1
    WORLD.turn_idx = 0
    WORLD.in_combat = True
    WORLD._touch()
    # reset tokens for first actor (if any)
    first = _current_actor_name()
    if first:
        _reset_turn_tokens_for(first)
    txt = "先攻：" + ", ".join(f"{n}({scores[n]})" for n in ordered)
    return ToolResponse(content=[TextBlock(type="text", text=txt)], metadata={"ok": True, "initiative": ordered, "scores": scores})



def end_combat():
    WORLD.in_combat = False
    WORLD.initiative_order.clear()
    WORLD.initiative_scores.clear()
    WORLD.turn_state.clear()
    WORLD.cover.clear()
    WORLD.conditions.clear()
    WORLD.triggers.clear()
    WORLD._touch()
    return ToolResponse(content=[TextBlock(type="text", text="战斗结束")], metadata={"ok": True, "in_combat": False})


def _current_actor_name() -> Optional[str]:
    try:
        if not WORLD.in_combat:
            return None
        order = WORLD.initiative_order
        if not order:
            return None
        idx = int(WORLD.turn_idx)
        if idx < 0 or idx >= len(order):
            return None
        return order[idx]
    except Exception:
        return None


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


def next_turn():
    """Advance to the next alive actor and start their turn.

    - Skips over any actors whose HP<=0.
    - Increments round when wrapping from the end to the start.
    - If no alive actors exist, preserves indices and reports accordingly.
    """
    if not WORLD.in_combat or not WORLD.initiative_order:
        return ToolResponse(content=[TextBlock(type="text", text="未处于战斗中")], metadata={"ok": False, "in_combat": False})

    order = WORLD.initiative_order
    if not order:
        return ToolResponse(content=[TextBlock(type="text", text="未处于战斗中")], metadata={"ok": False, "in_combat": False})

    prev_idx = int(WORLD.turn_idx)
    n = len(order)

    # Search for the next alive actor within one full cycle
    chosen_idx: Optional[int] = None
    wrapped = False
    for step in range(1, n + 1):
        idx = (prev_idx + step) % n
        if idx <= prev_idx:
            wrapped = True
        cand = order[idx]
        if _is_alive(cand):
            chosen_idx = idx
            break

    if chosen_idx is None:
        # No alive participants; nothing to do
        note = TextBlock(type="text", text="[系统] 无可行动单位（全部倒地或未登记）")
        return ToolResponse(content=[note], metadata={"round": WORLD.round, "actor": None, "ok": False})

    WORLD.turn_idx = chosen_idx
    if wrapped:
        WORLD.round += 1

    cur = order[WORLD.turn_idx]
    _reset_turn_tokens_for(cur)
    WORLD._touch()
    return ToolResponse(
        content=[TextBlock(type="text", text=f"回合推进：R{WORLD.round} 轮到 {cur}")],
        metadata={"ok": True, "round": WORLD.round, "actor": cur},
    )


def get_turn() -> ToolResponse:
    return ToolResponse(content=[TextBlock(type="text", text=f"当前：R{WORLD.round} idx={WORLD.turn_idx} actor={_current_actor_name() or '(未定)'}")], metadata={
        "ok": True,
        "round": WORLD.round,
        "turn_idx": WORLD.turn_idx,
        "actor": _current_actor_name(),
        "order": list(WORLD.initiative_order),
        "state": dict(WORLD.turn_state.get(_current_actor_name() or "", {})),
    })


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
            return ToolResponse(content=[TextBlock(type="text", text=f"[已用] {nm} 本回合动作已用完")], metadata={"ok": False})
        st["action_used"] = True
        WORLD._touch()
        return ToolResponse(content=[TextBlock(type="text", text=f"{nm} 使用 动作")], metadata={"ok": True})
    if kind == "bonus":
        if st.get("bonus_used"):
            return ToolResponse(content=[TextBlock(type="text", text=f"[已用] {nm} 本回合附赠动作已用完")], metadata={"ok": False})
        st["bonus_used"] = True
        WORLD._touch()
        return ToolResponse(content=[TextBlock(type="text", text=f"{nm} 使用 附赠动作")], metadata={"ok": True})
    if kind == "reaction":
        if not st.get("reaction_available", True):
            return ToolResponse(content=[TextBlock(type="text", text=f"[已用] {nm} 本轮反应不可用")], metadata={"ok": False})
        st["reaction_available"] = False
        WORLD._touch()
        return ToolResponse(content=[TextBlock(type="text", text=f"{nm} 使用 反应")], metadata={"ok": True})
    return ToolResponse(content=[TextBlock(type="text", text=f"未知动作类型 {kind}")], metadata={"ok": False})


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
            metadata={"ok": False, "left_steps": 0, "attempted_steps": steps},
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
        return ToolResponse(content=[TextBlock(type="text", text=f"未知掩体等级 {level}")], metadata={"ok": False})
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


def get_ac(name: str) -> int:
    try:
        return int(WORLD.characters.get(str(name), {}).get("ac", 10))
    except Exception:
        return 10


def cover_bonus(name: str) -> Tuple[int, bool]:
    """Return (ac_bonus, total_cover_blocked)."""
    c = get_cover(name)
    if c == "half":
        return 2, False
    if c == "three_quarters":
        return 5, False
    if c == "total":
        return 0, True
    return 0, False


def advantage_for_attack(attacker: str, defender: str) -> str:
    """Advantage calculation simplified: state-based modifiers removed.
    Always return 'none'.
    """
    return "none"


# ---- Standard actions (thin wrappers) ----
def act_dash(name: str):
    nm = str(name)
    # Gate by statuses (dash counts as moving this turn)
    blocked, msg = _blocked_action(nm, "move")
    if blocked:
        return ToolResponse(content=[TextBlock(type="text", text=msg)], metadata={"ok": False})
    use_action(nm, "action")
    st = WORLD.turn_state.setdefault(nm, {})
    spd_steps = int(WORLD.speeds.get(nm, _default_move_steps()))
    st["move_left"] = int(st.get("move_left", spd_steps)) + spd_steps
    return ToolResponse(
        content=[TextBlock(type="text", text=f"{nm} 冲刺（移动力+{format_distance_steps(spd_steps)}）")],
        metadata={"ok": True, "move_left_steps": st["move_left"]}
    )


def act_disengage(name: str):
    nm = str(name)
    # Gate by statuses (disengage is a movement-related action)
    blocked, msg = _blocked_action(nm, "move")
    if blocked:
        return ToolResponse(content=[TextBlock(type="text", text=msg)], metadata={"ok": False})
    use_action(nm, "action")
    st = WORLD.turn_state.setdefault(nm, {})
    st["disengage"] = True
    return ToolResponse(content=[TextBlock(type="text", text=f"{nm} 脱离接触（本回合移动不引发借机攻击）")], metadata={"ok": True})


# Removed: explicit Dodge action. Dodge is no longer modeled as a state/token.


def act_help(name: str, target: str):
    nm = str(name)
    # Gate generic actions under control statuses
    blocked, msg = _blocked_action(nm, "action")
    if blocked:
        return ToolResponse(content=[TextBlock(type="text", text=msg)], metadata={"ok": False})
    use_action(nm, "action")
    st = WORLD.turn_state.setdefault(nm, {})
    st["help_target"] = str(target)
    return ToolResponse(content=[TextBlock(type="text", text=f"{nm} 协助 {target}（其下一次检定或攻击获得优势）")], metadata={"ok": True, "target": target})


def act_hide(name: str, dc: int = 13):
    # CoC: Perform Stealth check; ignore DC, use skill value.
    # State system trimmed: no longer applies 'hidden' condition.
    nm = str(name)
    blocked, msg = _blocked_action(nm, "action")
    if blocked:
        return ToolResponse(content=[TextBlock(type="text", text=msg)], metadata={"ok": False})
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


def act_grapple(attacker: str, defender: str) -> ToolResponse:
    # State system trimmed: contest still rolls, but no status applied on success.
    res = contest(attacker, "athletics", defender, "athletics")
    winner = res.metadata.get("winner") if res.metadata else None
    out = list(res.content or [])
    return ToolResponse(content=out, metadata={"ok": winner == attacker})


"""act_shove removed along with range band system."""


def act_ready(name: str, trigger: str, reaction_action: Dict[str, Any]) -> ToolResponse:
    nm = str(name)
    use_action(nm, "action")
    st = WORLD.turn_state.setdefault(nm, {})
    st["ready"] = {"trigger": str(trigger or ""), "action": dict(reaction_action or {})}
    return ToolResponse(content=[TextBlock(type="text", text=f"{nm} 预备：{trigger}")], metadata={"ok": True})


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
        return ToolResponse(content=[], metadata={"ok": False, "name": nm, "reason": "no_coc_block"})
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
    return res


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
        return ToolResponse(content=[TextBlock(type="text", text=msg)], metadata={"ok": False, "rescuer": rescuer, "target": str(target)})
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
        return ToolResponse(content=logs + [TextBlock(type="text", text=f"{rescuer} 急救失败，{tgt} 状态未变")], metadata={"ok": False, "rescuer": rescuer, "target": tgt})

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


def resolve_melee_attack(attacker: str, defender: str, atk_mod: int = 0, dc: int = 12, dmg_expr: str = "1d4", advantage: str = "none"):
    """Resolve a simple melee attack: d20+atk_mod vs DC, on success apply damage.

    Args:
        attacker: 攻击发起者名字
        defender: 防御者名字
        atk_mod: 攻击加值（如力量/技巧）
        dc: 防御难度（DC）
        dmg_expr: 伤害骰表达式（如 1d4, 1d6+1）
        advantage: 'none'|'advantage'|'disadvantage'
    """
    # Protection interception (treat as melee, reach 1 step)
    pre_logs: List[TextBlock] = []
    guard_meta: Optional[Dict[str, Any]] = None
    new_defender, meta_guard, pre = _resolve_guard_interception(attacker, defender, reach_steps=1)
    if new_defender != defender:
        defender = new_defender
    if pre:
        pre_logs.extend(pre)
    if meta_guard:
        guard_meta = dict(meta_guard)

    # Attack roll
    atk_res = skill_check(target=int(dc), modifier=int(atk_mod), advantage=advantage)
    success = bool(atk_res.metadata.get("success")) if atk_res.metadata else False
    parts: List[TextBlock] = list(pre_logs)
    # Describe the attack roll
    parts.append(TextBlock(type="text", text=f"攻击检定：{attacker} d20+{int(atk_mod)} vs DC {int(dc)} -> {'成功' if success else '失败'}"))
    if success:
        # Damage roll (reuse roll_dice)
        dmg_res = roll_dice(dmg_expr)
        total = int(dmg_res.metadata.get("total", 0)) if dmg_res.metadata else 0
        # Apply damage
        dmg_apply = damage(defender, total)
        # Aggregate logs
        parts.append(TextBlock(type="text", text=f"伤害掷骰 {dmg_expr} -> {total}"))
        # Append the damage text line
        if dmg_apply.content:
            for blk in dmg_apply.content:
                if blk.get("type") == "text":
                    parts.append(blk)
    out_meta = {
        "attacker": attacker,
        "defender": defender,
        "attack": atk_res.metadata,
        **({"guard": guard_meta} if guard_meta else {}),
    }
    return ToolResponse(content=parts, metadata=out_meta)


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
    """Replace the entire weapon definition table (backward compatible).

    Accepts legacy schema used by configs/weapons.json, e.g.:
      { reach_steps:int, ability:str, damage_expr:str, skill:str, label:str }

    Also tolerates extended fields if present. No schema enforcement here;
    validation happens during attack resolution.
    """
    try:
        cleaned: Dict[str, Dict[str, Any]] = {}
        for k, v in (defs or {}).items():
            d = dict(v or {})
            # Drop legacy noisy fields we never use
            d.pop("proficient_default", None)
            cleaned[str(k)] = d
        WORLD.weapon_defs = cleaned
    except Exception:
        WORLD.weapon_defs = {}
    return ToolResponse(content=[TextBlock(type="text", text=f"武器表载入：{len(WORLD.weapon_defs)} 项")], metadata={"count": len(WORLD.weapon_defs)})


def define_weapon(weapon_id: str, data: Dict[str, Any]):
    wid = str(weapon_id)
    WORLD.weapon_defs[wid] = dict(data or {})
    return ToolResponse(content=[TextBlock(type="text", text=f"武器登记：{wid}")], metadata={"id": wid, **WORLD.weapon_defs[wid]})


def attack_with_weapon(
    attacker: str,
    defender: str,
    weapon: str,
    advantage: str = "none",
) -> ToolResponse:
    """Attack using a named weapon from WORLD.weapon_defs.

    - No auto-move; if distance > reach_steps, fail early.
    - ability/damage_expr are sourced from weapon defs with safe defaults.
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

    # Choose schema: prefer extended when extended keys present
    is_extended = ("damage" in w) or ("defense_skill" in w) or ("damage_type" in w)
    # legacy if classic fields exist AND not extended
    is_legacy = ("damage_expr" in w) or ("ability" in w)
    if is_legacy and not is_extended:
        ability = str(w.get("ability", "STR")).upper()
        # damage_expr is now required for legacy weapons; no implicit default.
        if not str(w.get("damage_expr") or "").strip():
            return ToolResponse(
                content=[TextBlock(type="text", text=f"武器缺少伤害表达式 damage_expr: {weapon}")],
                metadata={"ok": False, "error_type": "weapon_damage_expr_missing", "weapon_id": weapon},
            )
        damage_expr = str(w.get("damage_expr"))
        base_mod = _coc_ability_mod_for(attacker, ability)
        # Distance string helper
        def _fmt_distance(steps: Optional[int]) -> str:
            if steps is None:
                return "未知"
            return format_distance_steps(int(steps))
        # Ownership gate
        bag = WORLD.inventory.get(str(attacker), {}) or {}
        if int(bag.get(str(weapon), 0)) <= 0:
            msg = TextBlock(type="text", text=f"{attacker} 未持有武器 {weapon}，攻击取消。")
            return ToolResponse(content=[msg], metadata={"ok": False, "error_type": "weapon_not_owned", "attacker": attacker, "defender": defender, "weapon_id": weapon})
        # Guard interception
        pre_logs: List[TextBlock] = []
        guard_meta: Optional[Dict[str, Any]] = None
        new_defender, meta_guard, pre = _resolve_guard_interception(attacker, defender, reach_steps)
        if new_defender != defender:
            defender = new_defender
        if pre:
            pre_logs.extend(pre)
        if meta_guard:
            guard_meta = dict(meta_guard)
        # Range gate
        dfd = WORLD.characters.get(defender, {})
        distance_before = get_distance_steps_between(attacker, defender)
        if distance_before is not None and distance_before > reach_steps:
            msg = TextBlock(type="text", text=f"距离不足：{attacker} 使用 {weapon} 攻击 {defender} 失败（距离 {_fmt_distance(distance_before)}，触及 {_fmt_distance(reach_steps)}）")
            return ToolResponse(content=pre_logs + [msg], metadata={"ok": False, "attacker": attacker, "defender": defender, "weapon_id": weapon, "hit": False, "reach_ok": False, "distance_before": distance_before, "distance_after": distance_before, "reach_steps": reach_steps, **({"guard": guard_meta} if guard_meta else {})})
        # Attack resolution
        skill_name = str(w.get("skill")) if w.get("skill") else _weapon_skill_for(weapon, reach_steps, ability)
        parts: List[TextBlock] = list(pre_logs)
        success = False
        oppose = None
        atk_res = None
        if _is_dying(defender):
            parts.append(TextBlock(type="text", text=f"对抗跳过：{defender} 濒死，本次仅进行命中检定"))
            atk_res = skill_check_coc(attacker, skill_name)
            if atk_res.content:
                for blk in atk_res.content:
                    if isinstance(blk, dict) and blk.get("type") == "text":
                        parts.append(blk)
            success = bool((atk_res.metadata or {}).get("success"))
        else:
            oppose = contest(attacker, skill_name, defender, "Dodge")
            if oppose.content:
                for blk in oppose.content:
                    if isinstance(blk, dict) and blk.get("type") == "text":
                        parts.append(blk)
            winner = (oppose.metadata or {}).get("winner")
            success = (winner == attacker)
        hp_before = int(WORLD.characters.get(defender, {}).get("hp", dfd.get("hp", 0)))
        dmg_total = 0
        if success:
            dmg_expr2 = _replace_ability_tokens(damage_expr, base_mod)
            # If any alpha token other than the dice 'd' remains, treat as invalid.
            # This allows forms like '1d6+1' while rejecting stray tokens (e.g., 'POW').
            import re as _re
            _chk = _re.sub(r"[dD]", "", str(dmg_expr2))
            if _re.search(r"[A-Za-z]", _chk):
                return ToolResponse(content=parts + [TextBlock(type="text", text=f"武器伤害表达式不被支持：{damage_expr}")], metadata={"ok": False, "error_type": "damage_expr_invalid", "weapon_id": weapon})
            dmg_res = roll_dice(dmg_expr2)
            total = int((dmg_res.metadata or {}).get("total", 0))
            dmg_total = total
            dmg_apply = damage(defender, total)
            parts.append(TextBlock(type="text", text=f"伤害：{dmg_expr2} -> {total}"))
            for blk in (dmg_apply.content or []):
                if isinstance(blk, dict) and blk.get("type") == "text":
                    parts.append(blk)
        hp_after = int(WORLD.characters.get(defender, {}).get("hp", dfd.get("hp", 0)))
        distance_after = distance_before
        WORLD._touch()
        return ToolResponse(
            content=parts,
            metadata={
                "ok": True,
                "attacker": attacker,
                "defender": defender,
                "weapon_id": weapon,
                "hit": success,
                "base_mod": int(base_mod),
                "damage_total": int(dmg_total),
                "hp_before": int(hp_before),
                "hp_after": int(hp_after),
                "reach_ok": True,
                "distance_before": distance_before,
                "distance_after": distance_after,
                "reach_steps": reach_steps,
                **({"guard": guard_meta} if guard_meta else {}),
                **(
                    {"opposed": False, "defender_dying": True, "attack_check": (atk_res.metadata if atk_res else None)}
                    if _is_dying(defender)
                    else ({"opposed": True, "opposed_meta": (oppose.metadata if oppose else None)})
                ),
            },
        )

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
    pre_logs: List[TextBlock] = []
    # Preview handled by main; keep pre_logs for guard messages only
    guard_meta: Optional[Dict[str, Any]] = None
    new_defender, meta_guard, pre = _resolve_guard_interception(attacker, defender, reach_steps)
    if new_defender != defender:
        defender = new_defender
    if pre:
        pre_logs.extend(pre)
    if meta_guard:
        guard_meta = dict(meta_guard)

    # Post-interception snapshot for defender stat and distance gate
    dfd = WORLD.characters.get(defender, {})
    distance_before = get_distance_steps_between(attacker, defender)
    if distance_before is not None and distance_before > reach_steps:
        msg = TextBlock(type="text", text=f"距离不足：{attacker} 使用 {weapon} 攻击 {defender} 失败（距离 {_fmt_distance(distance_before)}，触及 {_fmt_distance(reach_steps)}）")
        return ToolResponse(
            content=pre_logs + [msg],
            metadata={
                "ok": False,
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
    success = False
    oppose = None
    atk_res = None
    if _is_dying(defender):
        # Defender is dying: skip Dodge opposition; perform single-sided hit check
        parts.append(TextBlock(type="text", text=f"对抗跳过：{defender} 濒死，本次仅进行命中检定"))
        atk_res = skill_check_coc(attacker, skill_name)
        if atk_res.content:
            for blk in atk_res.content:
                if isinstance(blk, dict) and blk.get("type") == "text":
                    parts.append(blk)
        success = bool((atk_res.metadata or {}).get("success"))
    else:
        # Perform opposed check vs configured defense skill (default Dodge)
        oppose = contest(attacker, skill_name, defender, defense_skill_name)
        if oppose.content:
            for blk in oppose.content:
                if isinstance(blk, dict) and blk.get("type") == "text":
                    parts.append(blk)
        winner = (oppose.metadata or {}).get("winner")
        success = (winner == attacker)
    hp_before = int(WORLD.characters.get(defender, {}).get("hp", dfd.get("hp", 0)))
    dmg_total = 0
    if success:
        # Base damage only (no attribute bonus / DB / impale)
        dmg_res = roll_dice(damage_expr_base)
        total = int((dmg_res.metadata or {}).get("total", 0))
        # Fixed reduction by armor/barrier depending on damage_type
        reduced = 0
        final = total
        try:
            coc_d = dict(dfd.get("coc") or {})
            terra = dict(coc_d.get("terra") or {})
            prot = dict(terra.get("protection") or {})
            if damage_type == "arts":
                barrier = max(0, int(prot.get("arts_barrier", 0)))
                reduced = barrier
            else:
                armor = max(0, int(prot.get("physical_armor", 0)))
                reduced = armor
        except Exception:
            reduced = 0
        final = max(0, total - int(reduced))
        dmg_total = final
        dmg_apply = damage(defender, final)
        parts.append(TextBlock(type="text", text=f"伤害：{damage_expr_base} -> {total}{('（减伤 ' + str(reduced) + '）') if reduced else ''}"))
        for blk in (dmg_apply.content or []):
            if isinstance(blk, dict) and blk.get("type") == "text":
                parts.append(blk)
    hp_after = int(WORLD.characters.get(defender, {}).get("hp", dfd.get("hp", 0)))
    distance_after = distance_before
    # Any hit/miss still mutates state through damage(); touch once per attack
    WORLD._touch()
    return ToolResponse(
        content=parts,
        metadata={
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
            **(
                {"opposed": False, "defender_dying": True, "attack_check": (atk_res.metadata if atk_res else None)}
                if _is_dying(defender)
                else ({"opposed": True, "opposed_meta": (oppose.metadata if oppose else None)})
            ),
        },
    )


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
    allowed = {"label","cast_skill","resist","range_steps","damage_type","mp","damage","heal","control","tags"}
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

    # Range check
    dist = get_distance_steps_between(attacker, tgt)
    if dist is None or dist > rng:
        return ToolResponse(content=[TextBlock(type="text", text=f"距离不足：{attacker}->{tgt} {dist if dist is not None else '?'}步/触及{rng}步")], metadata={"ok": False, "error_type": "range"})

    # Line-of-sight check (simplified via cover)
    if "line-of-sight" in tags:
        try:
            if get_cover(tgt) == "total":
                return ToolResponse(content=[TextBlock(type="text", text=f"{tgt} 视线受阻，本术式需要视线")], metadata={"ok": False, "error_type": "no_los", "target": tgt})
        except Exception:
            pass

    # MP spending
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
        return spent_res

    # Contest / check
    parts: List[TextBlock] = []
    success = False
    oppose = None
    atk_res = None
    if _is_dying(tgt):
        parts.append(TextBlock(type="text", text=f"对抗跳过：{tgt} 濒死，本次仅进行命中检定"))
        atk_res = skill_check_coc(attacker, cast_skill)
        for blk in (atk_res.content or []):
            if isinstance(blk, dict) and blk.get("type") == "text":
                parts.append(blk)
        success = bool((atk_res.metadata or {}).get("success"))
    else:
        # Resist via skill only (POW removed)
        oppose = contest(attacker, cast_skill, tgt, resist)
        for blk in (oppose.content or []):
            if isinstance(blk, dict) and blk.get("type") == "text":
                parts.append(blk)
        winner = (oppose.metadata or {}).get("winner")
        success = (winner == attacker)

    # Success level only for narration; no multiplier in damage/heal
    level = (atk_res.metadata or {}).get("success_level") if atk_res else ((oppose.metadata or {}).get("a", {}) if oppose else {}).get("success_level")
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
        roll = roll_dice(expr)
        val = int((roll.metadata or {}).get("total", 0))
        # reduction
        reduced = 0
        try:
            coc_d = dict((WORLD.characters.get(tgt, {}) or {}).get("coc") or {})
            terra = dict(coc_d.get("terra") or {})
            prot = dict(terra.get("protection") or {})
            if dtype == "arts":
                reduced = max(0, int(prot.get("arts_barrier", 0)))
            else:
                reduced = max(0, int(prot.get("physical_armor", 0)))
        except Exception:
            reduced = 0
        final = max(0, val - reduced)
        dmg_total = final
        parts.append(TextBlock(type="text", text=f"术式伤害：{expr} -> {val}{('（减伤 ' + str(reduced) + '）') if reduced else ''}"))
        dmg_apply = damage(tgt, final)
        for blk in (dmg_apply.content or []):
            if isinstance(blk, dict) and blk.get("type") == "text":
                parts.append(blk)
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

    # 3.2) strict type for advance_position.target: must be array [x,y]
    if tool_name == "advance_position":
        tgt = p.get("target")
        # only accept list/tuple of length >= 2; explicitly reject dict/object
        if not (isinstance(tgt, (list, tuple)) and len(tgt) >= 2):
            return ToolResponse(
                content=[TextBlock(type="text", text="参数错误：advance_position.target 必须为 [x,y] 数组")],
                metadata={"ok": False, "error_type": "invalid_type", "param": "target"},
            )
        try:
            tx, ty = int(tgt[0]), int(tgt[1])
            p["target"] = (tx, ty)
        except Exception:
            return ToolResponse(
                content=[TextBlock(type="text", text="参数错误：target 元素必须为整数，如 [1, 1]")],
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
        "adjust_relation": lambda **p: _validated_call("adjust_relation", set_relation, p),
        "transfer_item": lambda **p: _validated_call("transfer_item", grant_item, p),
        "set_protection": lambda **p: _validated_call("set_protection", set_guard, p),
        "clear_protection": lambda **p: _validated_call("clear_protection", clear_guard, p),
        "first_aid": lambda **p: _validated_call("first_aid", first_aid, p),
        "cast_arts": lambda **p: _validated_call("cast_arts", cast_arts, p),
    }
