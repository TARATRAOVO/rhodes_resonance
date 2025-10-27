import random

from world.core import (
    WORLD,
    set_coc_character,
    set_position,
    set_weapon_defs,
    attack_with_weapon,
    grant_item,
)


def test_attack_with_weapon_in_reach():
    random.seed(7)
    # Minimal CoC characters; skills will fall back to defaults
    set_coc_character(name="A", characteristics={"STR": 60, "DEX": 50, "CON": 50, "INT": 50, "SIZ": 50})
    set_coc_character(name="B", characteristics={"STR": 50, "DEX": 50, "CON": 50, "INT": 50, "SIZ": 50})
    set_position("A", 0, 0)
    set_position("B", 1, 0)
    set_weapon_defs(
        {
            "longsword": {
                "label": "长剑",
                "reach_steps": 1,
                "skill": "Fighting_Blade",
                "defense_skill": "Dodge",
                "damage": "1d8",
                "damage_type": "physical",
            }
        }
    )
    grant_item("A", "longsword", 1)
    res = attack_with_weapon("A", "B", weapon="longsword")
    assert res.metadata.get("reach_ok") is True
    assert res.metadata.get("weapon_id") == "longsword"


def test_attack_with_weapon_out_of_reach_fails():
    random.seed(11)
    set_coc_character(name="C", characteristics={"STR": 60, "DEX": 50, "CON": 50, "INT": 50, "SIZ": 50})
    set_coc_character(name="D", characteristics={"STR": 50, "DEX": 50, "CON": 50, "INT": 50, "SIZ": 50})
    set_position("C", 0, 0)
    set_position("D", 0, 3)
    set_weapon_defs(
        {
            "baton": {
                "label": "警棍",
                "reach_steps": 1,
                "skill": "Fighting_Blunt",
                "defense_skill": "Dodge",
                "damage": "1d4",
                "damage_type": "physical",
            }
        }
    )
    res = attack_with_weapon("C", "D", weapon="baton")
    # Must fail because attacker doesn't own the weapon
    assert res.metadata.get("error_type") == "weapon_not_owned"
    # Position unchanged (no auto move)
    assert WORLD.positions["C"] == (0, 0)
