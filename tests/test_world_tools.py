import random

from world.core import (
    WORLD,
    get_position,
    roll_dice,
    set_position,
    set_character,
    set_weapon_defs,
    grant_item,
    attack_with_weapon,
)


def test_set_and_get_position():
    res1 = set_position("Tester", 2, 3)
    meta = res1.metadata or {}
    assert meta.get("position") == [2, 3]
    res2 = get_position("Tester")
    assert res2.metadata.get("position") == [2, 3]


def test_stat_block_and_attack():
    # Deterministic randomness
    random.seed(42)
    set_character(name="A", hp=10, max_hp=10)
    set_character(name="B", hp=10, max_hp=10)
    set_position("A", 0, 0)
    set_position("B", 0, 1)
    # Define a simple melee weapon and grant to A
    set_weapon_defs(
        {
            "training_blade": {
                "label": "训练短刃",
                "reach_steps": 1,
                "skill": "Fighting_Brawl",
                "defense_skill": "Dodge",
                "damage": "1d4",
                "damage_type": "physical",
            }
        }
    )
    grant_item("A", "training_blade", 1)
    res = attack_with_weapon("A", "B", weapon="training_blade")
    # hp should be <= max after damage applied
    hp_after = WORLD.characters["B"]["hp"]
    assert 0 <= hp_after <= WORLD.characters["B"]["max_hp"]
    assert res.metadata.get("reach_ok") is True


def test_roll_dice_parse_and_total():
    random.seed(123)
    out = roll_dice("2d6+1")
    total = out.metadata.get("total")
    assert isinstance(total, int)
    assert 3 <= total <= 13


def test_attack_respects_reach_without_auto_move():
    random.seed(1)
    set_character(name="A", hp=10, max_hp=10)
    set_character(name="B", hp=10, max_hp=10)
    set_position("A", 0, 0)
    set_position("B", 0, 4)
    set_weapon_defs(
        {
            "training_blade": {
                "label": "训练短刃",
                "reach_steps": 1,
                "skill": "Fighting_Brawl",
                "defense_skill": "Dodge",
                "damage": "1d4",
                "damage_type": "physical",
            }
        }
    )
    grant_item("A", "training_blade", 1)
    res = attack_with_weapon("A", "B", weapon="training_blade")
    assert res.metadata.get("reach_ok") is False
    assert WORLD.positions["A"] == (0, 0)


# 自动靠近攻击已移除：不再测试 auto_move 行为
