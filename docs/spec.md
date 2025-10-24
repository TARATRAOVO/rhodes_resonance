World Ownership And Orchestrator Contract (Simplified)
=====================================================

Goal
- Move all “world settings” file I/O (configs/story.json, configs/characters.json, configs/weapons.json, configs/arts.json) into the world component.
- Expose a minimal, stable interface from the world to main/orchestrator.
- Keep main focused on orchestration, logging, server endpoints, and model config only.

Ownership Split
- World component (src/world/tools.py)
  - Owns reading, parsing, and applying world settings into in‑memory WORLD.
  - Single source of truth for runtime state: positions, participants, relations, scene, weapons/arts, and character sheets/meta.
  - Minimal public API for selection:
    - list_world_ids() -> list[str]
    - select_world(world_id: Optional[str]) -> dict (returns WORLD snapshot)
  - Optional utilities used internally:
    - init_world_from_configs(selected_story_id, reset=True)
    - project_root() (used by main to avoid duplicate path logic)

- Main/orchestrator (src/main.py)
  - Does NOT read story/characters/weapons/arts directly.
  - Reads only model.json (LLM config) and handles the settings editor endpoints (/api/config/*) for the web UI.
  - Uses world.list_world_ids() to present choices; calls world.select_world(id) to initialize a run.
  - Builds tools and NPC agents, then runs the loop using WORLD.snapshot() only.

World.select_world() Semantics
- Resets WORLD (clean start) and loads the following from configs:
  - story.json (single story or container: { stories: { id: {...} } })
  - characters.json
  - weapons.json (weapon_defs)
  - arts.json (arts_defs; optional, tolerated empty)
- Applies into WORLD:
  - Weapons/Arts definitions
  - Characters
    - persona/appearance/quotes (prompt meta)
    - type (npc|player) used by orchestrator to skip player agents
    - CoC sheet (characteristics, skills, derived caps); movement derived from DEX
    - inventory (items/weapons)
  - Positions/Participants: from story.initial_positions, story.positions, or story.initial.positions
  - Relations: from characters.relations (name -> name -> int)
  - Scene: location, objectives, details, weather, time
    - Accepts legacy scene.description/opening; merged into details
- Returns WORLD.snapshot() for convenience.

Main Flow (CLI)
- Load model config (configs/model.json).
- Bootstrap logging/runtime shell.
- List world ids via world.list_world_ids(); choose one (default: first if present).
- Initialize world via world.select_world(id).
- Build tools and NPC agents; enter run_demo (uses only WORLD.snapshot()).

Main Flow (Server)
- /api/stories: return world.list_world_ids() and current selection.
- /api/select_story: remember the chosen id (per session).
- /api/preview_state?id=...: world.select_world(id) into a fresh WORLD and return snapshot (no run).
- /api/start: select_world(current-selection) then run background loop.

What Main Still Reads/Writes
- Reads: configs/model.json only (LLM config for agent factory).
- Reads/Writes (editor only): /api/config/story|characters|weapons — file I/O for the web editor; not used by runtime.

Invariants And Notes
- No fallback JSON reading in main for world settings; all through world API.
- No implicit auto-move; reach/steps enforced by world rules.
- Player entries (type == "player") do not create NPC agents; they are driven by user input.
- Main does not inject defaults; if scene has no details, no opening line is added by orchestrator.
- Main does not write character meta/sheets/inventory; all are populated during world selection.
- JSON-only agent output is supported (strict mode in main).

Optional Future
- Add a CLI flag --world-id to pick a world explicitly for CLI runs.
- Move editor read/write (/api/config/*) behind world if we want main to avoid touching settings files altogether.

Quick Reference
- World API: src/world/tools.py
  - list_world_ids(), select_world()
- Orchestrator usage: src/main.py
  - CLI boot: _bootstrap_runtime() -> select_world() -> make_npc_actions() -> run_demo()
  - Server: /api/stories, /api/select_story, /api/preview_state, /api/start
