import sys
from pathlib import Path

import pytest

from world.core import WORLD

# Add tests/_stubs to sys.path so imports fallback to local stubs when Agentscope
# is not installed in the environment.
_STUBS = Path(__file__).resolve().parent / "_stubs"
sys.path.insert(0, str(_STUBS))


@pytest.fixture(autouse=True)
def reset_world_state():
    """Ensure WORLD state is cleaned between tests to avoid leakage."""

    WORLD.positions.clear()
    WORLD.objective_positions.clear()
    WORLD.hidden_enemies.clear()
    WORLD.characters.clear()
    WORLD.cover.clear()
    WORLD.conditions.clear()
    WORLD.triggers.clear()
    WORLD.turn_state.clear()
    WORLD.speeds.clear()
    # The core world no longer tracks initiative/combat lifecycle; no-op here.
    WORLD.participants.clear()
    yield
