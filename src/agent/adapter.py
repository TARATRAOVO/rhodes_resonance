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
import json

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
                with path.open("w", encoding="utf-8") as f:
                    json.dump(record, f, ensure_ascii=False, indent=2)
            except Exception:
                # never break the call if logging fails
                pass

            # Additionally write a human-friendly .txt alongside the JSON.
            # This file must not add or omit information; it only re-formats
            # what is already present in `record` for easier reading.
            try:
                self._dump_payload_pretty(record, dump_dir / f"{safe}_payload.txt")
            except Exception:
                # pretty log failure must not affect runtime
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

    # --- helpers for human-readable payload log ---
    def _dump_payload_pretty(self, record: dict, out_path: Path) -> None:
        """Write a strictly re-formatted, human-readable view of the payload.

        No fields are added or removed. Strings are shown verbatim; compound
        values are pretty-printed JSON. This is intended only as a companion
        to the JSON payload file for quick inspection.
        """

        def _w(fp, s: str = "") -> None:
            fp.write((s or "") + "\n")

        def _indent_lines(text: Any, pad: str) -> str:
            """Indent a possibly multi-line string.

            Additionally, improve readability by treating literal "\\n" (and
            common variants) as visual line breaks. This does not change the
            underlying JSON record (which is emitted verbatim below).
            """
            s = "" if text is None else str(text)
            if not s:
                return ""
            try:
                # Normalize common escaped line breaks for display only
                s = s.replace("\r\n", "\n")
                s = s.replace("\\n", "\n")  # literal backslash-n -> newline
                s = s.replace("/n", "\n")     # tolerate accidental "/n"
            except Exception:
                pass
            return "\n".join(pad + ln for ln in s.splitlines())

        def _pjson(obj: Any, indent: int = 2) -> str:
            return json.dumps(obj, ensure_ascii=False, indent=indent)

        meta = record.get("meta", {}) or {}
        messages = record.get("messages", None)
        kwargs = record.get("kwargs", {}) or {}

        with out_path.open("w", encoding="utf-8") as f:
            # meta
            _w(f, f"actor: {meta.get('actor', '')}")
            _w(f, f"timestamp: {meta.get('timestamp', '')}")
            if meta.get("model_name") is not None:
                _w(f, f"model_name: {meta.get('model_name')}")
            if meta.get("client_args") is not None:
                _w(f, "client_args:")
                _w(f, _indent_lines(_pjson(meta.get("client_args")), "  "))
            if meta.get("generate_kwargs") is not None:
                _w(f, "generate_kwargs:")
                _w(f, _indent_lines(_pjson(meta.get("generate_kwargs")), "  "))

            # messages
            _w(f)
            _w(f, "messages:")
            if messages is None:
                _w(f, "  <none>")
            else:
                for i, m in enumerate(messages, start=1):
                    if not isinstance(m, dict):
                        _w(f, f"- [{i}] <non-dict>:")
                        _w(f, _indent_lines(_pjson(m), "    "))
                        continue
                    role = m.get("role", "")
                    name = m.get("name", "")
                    _w(f, f"- [{i}] role: {role}  name: {name}")
                    if "content" in m:
                        c = m.get("content")
                        if isinstance(c, str):
                            _w(f, "    content:")
                            _w(f, _indent_lines(c, "      "))
                        else:
                            _w(f, "    content(json):")
                            _w(f, _indent_lines(_pjson(c), "      "))
                    for k, v in m.items():
                        if k in ("role", "name", "content"):
                            continue
                        _w(f, f"    {k}:")
                        if isinstance(v, (dict, list)):
                            _w(f, _indent_lines(_pjson(v), "      "))
                        elif v is None:
                            _w(f, "      null")
                        else:
                            _w(f, _indent_lines(v, "      "))

            # kwargs
            _w(f)
            _w(f, "kwargs:")
            if not kwargs:
                _w(f, "  <none>")
            else:
                for k, v in kwargs.items():
                    _w(f, f"- {k}:")
                    if isinstance(v, (dict, list)):
                        _w(f, _indent_lines(_pjson(v), "    "))
                    elif v is None:
                        _w(f, "    null")
                    else:
                        _w(f, _indent_lines(v, "    "))

            # raw JSON (verbatim)
            _w(f)
            _w(f, "--- raw (verbatim record) ---")
            _w(f, _pjson(record))


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
