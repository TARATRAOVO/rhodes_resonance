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


def build_kimi_agent(
    name: str,
    persona: str,
    model_cfg: Mapping[str, Any],
    *,
    sys_prompt: str,  # system prompt must be assembled by caller (main)
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

