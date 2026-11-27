from pathlib import Path

import pytest

from item_build.reasoning import Combat, evaluate_combat
from item_build.retrieval import Repository

ROOT = Path(__file__).resolve().parents[1]


def test_progressive_packs_keep_decision_conditions_and_expand_history():
    repo = Repository(ROOT)
    draft = repo.context(
        "Thane", "support", ["Raz", "Natalya", "Florentino"], "fast_draft", layer="l1"
    )
    assert {rule["id"] for rule in draft["team_threats"]} == {"raz-natalya-poke-to-burst"}
    true_damage = draft["heroes"]["florentino"]["live"]["skill-2.target-max-hp-true"]
    assert true_damage["damage_type"] == "true"
    assert any("target_max_hp" in term for term in true_damage["formula_basis"])
    assert draft["personal_preference"]["checkpoints"] == [3, 4]
    assert draft["shortlist"]["phu-chu-truong-sinh"]["live"] == {}
    assert draft["shortlist"]["dai-dia-hoi-huyet"]["live"]["active.independent-recharge"][
        "exceptions"
    ]
    deep = repo.context("Thane", "support", ["Violet"], "fast_draft", layer="l3")
    cooldown = deep["canonical"]["knowledge/heroes/violet.json"]["facts"]["skill-1.cooldown"]
    assert [fact["status"] for fact in cooldown] == ["SUPERSEDED", "LIVE_VN"]
    assert repo.cooldown("heroes/violet", "skill-1.cooldown", {}, None, None)["base_seconds"] == 5


def test_what_if_uses_actual_heal_and_anti_heal_parameters():
    repo = Repository(ROOT)
    source = "heroes/thane#skill-3.damage-heal"
    scenario = Combat.model_validate(
        {
            "id": "thane",
            "assumptions": "Quan sát chiêu 3 gây 480 sát thương và Thane đang dính Hỏa diệm.",
            "max_hp": 8000,
            "initial_hp": 4200,
            "anti_heal": [{"start_s": 1, "fact": "items/ao-choang-than-ra#passive.anti-heal"}],
            "events": [
                {
                    "at_s": 2,
                    "heal": {
                        "ready_at_s": 2,
                        "condition_met": True,
                        "fact": source,
                        "inputs": {"damage_dealt": 480},
                    },
                }
            ],
        }
    )
    result = evaluate_combat(scenario, repo)
    assert result["sourced_heal_windows"][0]["end_s"] == 4
    assert result["ledger"][0]["source"]["value"] == 120
    assert result["ledger"][0]["effective_heal"] == 72
    scenario.events[0].heal.fact = "items/phu-chu-truong-sinh#passive.in-combat-regen"
    with pytest.raises(ValueError, match="LIVE_VN"):
        evaluate_combat(scenario, repo)
