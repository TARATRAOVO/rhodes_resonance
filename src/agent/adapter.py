from __future__ import annotations

"""
Thin adapter for building and invoking the underlying LLM agent.

Scope (by design, minimal):
- build_kimi_agent: construct a ReActAgent given a ready-made system prompt.
- ask_once: single-turn invocation wrapper.

Prompt assembly, context injection, JSON parsing and tool execution remain in
the main orchestrator.
"""

from typing import Any, Mapping, Optional, List, Union
from pathlib import Path
from datetime import datetime, timezone
import os

try:  # optional at import time; unit tests may not install agentscope
    from agentscope.agent import ReActAgent  # type: ignore
    from agentscope.formatter import OpenAIChatFormatter  # type: ignore
    from agentscope.memory import InMemoryMemory  # type: ignore
    from agentscope.model import OpenAIChatModel  # type: ignore
    from agentscope.tool import Toolkit  # type: ignore
except Exception:  # pragma: no cover - light stubs for dev/test without deps

    class ReActAgent:  # type: ignore
        pass

    class OpenAIChatFormatter:  # type: ignore
        pass

    class InMemoryMemory:  # type: ignore
        pass

    class OpenAIChatModel:  # type: ignore
        def __init__(self, *a, **k):
            pass

    class Toolkit:  # type: ignore
        def register_tool_function(self, *a, **k):
            pass


class _LoggingModelWrapper:
    """Proxy the model to capture the final payload sent to the LLM.

    We try to intercept common entrypoints (generate/agenerate/__call__). If the
    backend changes, keeping this wrapper here isolates the main loop from
    logging concerns.
    """

    def __init__(self, model: Any, *, actor: str, enabled: bool) -> None:
        self._model = model
        self._actor = str(actor)
        self._enabled = bool(enabled)

    # --- proxy helpers ---
    def __getattr__(self, item):  # delegate anything we don't override
        return getattr(self._model, item)

    def _root_dir(self) -> Path:
        # project root = parent of "src" directory
        p = Path(__file__).resolve()
        # src/agent/adapter.py -> .../src -> project root
        return p.parents[2]

    def _safe_name(self) -> str:
        s = "".join(ch if ch.isalnum() or ch in ("_", "-", ".") else "_" for ch in self._actor)
        return s or "actor"

    def _dump_payload(self, args, kwargs) -> None:
        if not self._enabled:
            return
        try:
            # Build a best-effort record; prefer kwargs["messages"], otherwise guess from args[0]
            messages = None
            if isinstance(kwargs, dict) and "messages" in kwargs:
                messages = kwargs.get("messages")
            elif args:
                a0 = args[0]
                if isinstance(a0, list):
                    # naive check: list of dicts with role/content
                    if a0 and isinstance(a0[0], dict) and "role" in a0[0]:
                        messages = a0
            meta = {
                "actor": self._actor,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            # model meta (best-effort)
            try:
                meta["model_name"] = getattr(self._model, "model_name", None)
            except Exception:
                pass
            try:
                meta["client_args"] = getattr(self._model, "client_args", None)
            except Exception:
                pass
            try:
                meta["generate_kwargs"] = getattr(self._model, "generate_kwargs", None)
            except Exception:
                pass
            record = {
                "meta": meta,
                "messages": messages,
                "kwargs": {k: (v if k != "messages" else "<omitted-dup>") for k, v in dict(kwargs or {}).items()},
            }
            root = self._root_dir()
            dump_dir = root / "logs" / "prompts"
            dump_dir.mkdir(parents=True, exist_ok=True)
            safe = self._safe_name()
            # Keep only latest per actor
            try:
                for p in dump_dir.glob(f"{safe}_payload.*"):
                    try:
                        p.unlink()
                    except Exception:
                        pass
            except Exception:
                pass
            path = dump_dir / f"{safe}_payload.json"
            try:
                import json
                with path.open("w", encoding="utf-8") as f:
                    json.dump(record, f, ensure_ascii=False, indent=2)
            except Exception:
                # never break the call if logging fails
                pass
        except Exception:
            # keep silent on logging errors
            pass

    # --- possible entrypoints used by agents ---
    def __call__(self, *args, **kwargs):
        self._dump_payload(args, kwargs)
        return self._model(*args, **kwargs)

    def generate(self, *args, **kwargs):  # sync entrypoint
        self._dump_payload(args, kwargs)
        return self._model.generate(*args, **kwargs)

    async def agenerate(self, *args, **kwargs):  # async entrypoint
        self._dump_payload(args, kwargs)
        return await self._model.agenerate(*args, **kwargs)


def build_kimi_agent(
    name: str,
    persona: str,
    model_cfg: Mapping[str, Any],
    *,
    sys_prompt: str,  # system prompt must be assembled by caller (main)
    debug_dump_prompts: bool = False,
    allowed_names: str = "",
    appearance: Optional[str] = None,
    quotes: Optional[Union[List[str], str]] = None,
    relation_brief: Optional[str] = None,
    weapon_brief: Optional[str] = None,
    arts_brief: Optional[str] = None,
    tools: Optional[List[object]] = None,
) -> ReActAgent:
    """Construct a Kimi(OpenAI-compatible) ReActAgent.

    Only model construction and tool registration happen here. The prompt is
    passed in via `sys_prompt` so the orchestrator keeps control of policy.
    """

    api_key = os.getenv("MOONSHOT_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError(
            "MOONSHOT_API_KEY is not set. Please export MOONSHOT_API_KEY to use the Kimi API."
        )

    base_url = str(
        model_cfg.get("base_url") or os.getenv("KIMI_BASE_URL", "https://api.moonshot.cn/v1")
    )
    sec = dict(model_cfg.get("npc") or {})
    model_name = sec.get("model") or os.getenv("KIMI_MODEL", "kimi-k2-turbo-preview")

    model = OpenAIChatModel(
        model_name=model_name,
        api_key=api_key,
        stream=bool(sec.get("stream", True)),
        client_args={"base_url": base_url},
        generate_kwargs={"temperature": float(sec.get("temperature", 0.7))},
    )
    # Wrap for prompt payload logging (when enabled)
    model = _LoggingModelWrapper(model, actor=name, enabled=debug_dump_prompts)

    toolkit = Toolkit()
    if tools:
        for fn in tools:
            try:
                toolkit.register_tool_function(fn)  # type: ignore[arg-type]
            except Exception:
                # Keep robust when individual tool registration fails
                pass

    return ReActAgent(
        name=name,
        sys_prompt=sys_prompt,
        model=model,
        formatter=OpenAIChatFormatter(),
        memory=InMemoryMemory(),
        toolkit=toolkit,
    )


async def ask_once(agent: "ReActAgent"):
    """Invoke the agent for a single turn. Encapsulated for future backends."""
    return await agent(None)
