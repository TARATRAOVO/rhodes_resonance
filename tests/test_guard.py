import random

from world.core import (
    WORLD,
    set_character,
    set_position,
    set_weapon_defs,
    grant_item,
    attack_with_weapon,
    use_action,
    set_guard,
    clear_guard,
)


def setup_scene_basic():
    # Clear world bits that may interfere
    WORLD.characters.clear()
    WORLD.positions.clear()
    WORLD.inventory.clear()
    WORLD.guardians.clear()
    WORLD.turn_state.clear()
    WORLD.weapon_defs.clear()


def test_guard_redirects_target():
    random.seed(7)
    setup_scene_basic()
    # Protector A, Protectee B, Attacker C
    set_character(name="A", hp=12, max_hp=12)
    set_character(name="B", hp=10, max_hp=10)
    set_character(name="C", hp=10, max_hp=10)
    set_position("B", 0, 0)
    set_position("A", 1, 0)  # adjacent to B
    set_position("C", 1, 1)  # within 1 step to A and B
    set_guard("A", "B")

    set_weapon_defs({
        "longsword": {
            "label": "长剑",
            "reach_steps": 1,
            "skill": "Fighting_Blade",
            "defense_skill": "Dodge",
            "damage": "1d8",
            "damage_type": "physical",
        }
    })
    grant_item("C", "longsword", 1)
    res = attack_with_weapon("C", "B", weapon="longsword")
    # Defender should be redirected to A
    assert res.metadata.get("defender") == "A"
    guard = (res.metadata or {}).get("guard", {})
    assert guard.get("protector") == "A" and guard.get("protected") == "B"


def test_guard_requires_reaction():
    random.seed(8)
    setup_scene_basic()
    set_character(name="A", hp=12, max_hp=12)
    set_character(name="B", hp=10, max_hp=10)
    set_character(name="C", hp=10, max_hp=10)
    set_position("B", 0, 0)
    set_position("A", 1, 0)
    set_position("C", 1, 1)
    set_guard("A", "B")
    # Spend A's reaction beforehand
    use_action("A", "reaction")

    set_weapon_defs({
        "mace": {
            "label": "钉头锤",
            "reach_steps": 1,
            "skill": "Fighting_Blunt",
            "defense_skill": "Dodge",
            "damage": "1d6",
            "damage_type": "physical",
        }
    })
    grant_item("C", "mace", 1)
    res = attack_with_weapon("C", "B", weapon="mace")
    # No redirection due to lack of reaction
    assert res.metadata.get("defender") == "B"
    assert (res.metadata or {}).get("guard") is None


def test_guard_requires_proximity():
    random.seed(9)
    setup_scene_basic()
    set_character(name="A", hp=12, max_hp=12)
    set_character(name="B", hp=10, max_hp=10)
    set_character(name="C", hp=10, max_hp=10)
    set_position("B", 0, 0)
    set_position("A", 2, 0)  # not adjacent (distance=2)
    set_position("C", 1, 1)
    set_guard("A", "B")

    set_weapon_defs({
        "club": {
            "label": "木棒",
            "reach_steps": 1,
            "skill": "Fighting_Blunt",
            "defense_skill": "Dodge",
            "damage": "1d4",
            "damage_type": "physical",
        }
    })
    grant_item("C", "club", 1)
    res = attack_with_weapon("C", "B", weapon="club")
    # No redirection due to non-adjacency
    assert res.metadata.get("defender") == "B"
    assert (res.metadata or {}).get("guard") is None


def test_multiple_guardians_priority_nearest_to_attacker():
    random.seed(10)
    setup_scene_basic()
    set_character(name="A", hp=12, max_hp=12)
    set_character(name="D", hp=12, max_hp=12)
    set_character(name="B", hp=10, max_hp=10)
    set_character(name="C", hp=10, max_hp=10)
    set_position("B", 0, 0)
    set_position("A", 1, 0)  # adjacent
    set_position("D", 0, 1)  # adjacent
    set_position("C", 10, 0)
    set_guard("A", "B")
    set_guard("D", "B")

    set_weapon_defs({
        "bow": {
            "label": "弓",
            "reach_steps": 12,
            "skill": "Firearms_Rifle_Crossbow",
            "defense_skill": "Dodge",
            "damage": "1d8",
            "damage_type": "physical",
        }
    })
    grant_item("C", "bow", 1)
    res = attack_with_weapon("C", "B", weapon="bow")
    # C->A distance 9, C->D distance 10 -> choose A
    assert res.metadata.get("defender") == "A"
    assert (res.metadata or {}).get("guard", {}).get("protector") == "A"
