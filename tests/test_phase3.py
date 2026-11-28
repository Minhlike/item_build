import runpy
from pathlib import Path

import pytest

from item_build.coverage import measure_coverage
from item_build.reasoning import Comparison, PurchaseScenario, compare_combat, plan_purchases
from item_build.retrieval import Repository
from item_build.storage import read

ROOT = Path(__file__).resolve().parents[1]


def test_ranked_context_uses_only_named_actors():
    repo = Repository(ROOT)
    first = repo.context("Thane", "support", ["Raz"], "fast_draft", include_reasoning=True)
    assert first["tactics"]["team_threats"] == []
    assert {rule["id"] for rule in first["tactics"]["macro_goals"]} >= {"thane-mid-start"}
    assert "allies" not in first
    second = repo.context(
        "Thane",
        "support",
        ["Raz", "Natalya"],
        "fast_draft",
        allies=["Yorn"],
        include_reasoning=True,
    )
    (threat,) = second["tactics"]["team_threats"]
    assert threat["id"] == "raz-natalya-poke-to-burst"
    assert threat["kind"] == "tactical_heuristic" and threat["condition"]
    assert set(threat["evidence"]) <= second["evidence"].keys()
    assert [ally["id"] for ally in second["allies"]] == ["yorn"]
    assert "tactics" not in repo.context("Thane", "support", [], "fast_draft")


def test_buy_components_checkpoint_order_and_filter():
    repo = Repository(ROOT)
    raw = read(ROOT / "examples/purchase-plan.json")
    steps = raw["paths"][0]["steps"]
    raw["paths"].extend(
        [
            {"id": "too-expensive", "steps": [dict(steps[0], cumulative_gold=1800), steps[1]]},
            {"id": "banned", "steps": [steps[0], dict(steps[1], item="giap-thong-kho")]},
            {"id": "unknown-cost", "steps": [steps[0], dict(steps[1], quoted_cost=None)]},
        ]
    )
    paths = plan_purchases(repo, PurchaseScenario.model_validate(raw))["paths"]
    shield = paths["shield-at-slot-3"]["steps"][-2]
    assert shield["final_slot"] == 3 and shield["preference_checkpoint"]
    assert paths["shield-at-slot-3"]["steps"][-1]["preference_checkpoint"]
    assert shield["cost_basis"] == "scenario_quote"
    assert shield["components_on_purchase"] == {"giap-nhe": 1}
    assert shield["gold_after"] == 0 and "giap-nhe" not in shield["held_after"]
    assert paths["too-expensive"]["steps"][0]["shortfall"] == 100
    assert paths["too-expensive"]["unreached_steps"] == 1
    assert paths["banned"]["steps"] == [] and paths["banned"]["status"] == "constraints_failed"
    assert paths["unknown-cost"]["steps"][-1]["status"] == "unknown_cost"


def test_purchase_rejects_consuming_same_component_twice():
    raw = read(ROOT / "examples/purchase-plan.json")
    raw["paths"][0]["steps"][-2]["quoted_consumption"].append("giap-nhe")
    with pytest.raises(ValueError, match="chưa sở hữu"):
        plan_purchases(Repository(ROOT), PurchaseScenario.model_validate(raw))


def test_what_if_penetration_reverses_order():
    case = Comparison.model_validate(read(ROOT / "examples/what-if.json"))
    branches = compare_combat(case)["cases"]
    assert branches["armor"]["remaining_hp"] == 4075
    assert branches["hp"]["remaining_hp"] == 3975
    assert branches["armor-penetrated"]["remaining_hp"] == 3700
    assert branches["hp-penetrated"]["remaining_hp"] == pytest.approx(3900)


def test_what_if_true_damage_shield_anti_heal_readiness_and_unknown():
    case = {
        "id": "base",
        "max_hp": 2000,
        "initial_hp": 2000,
        "assumptions": "synthetic",
        "events": [
            {"at_s": 0, "shield": {"duration_s": 1, "amount": 100, "absorbs": ["true"]}},
            {"at_s": 0.5, "damage": {"kind": "true", "target_max_hp_ratio": 0.25}},
            {"at_s": 1, "heal": {"amount": 500, "ready_at_s": 1, "condition_met": True}},
        ],
        "anti_heal": [{"start_s": 1, "end_s": 2, "reduction": 0.4}],
        "cooldown": {"base_s": 10, "started_at_s": 1, "cdr": 0.45, "cap": 0.4, "needed_at_s": 7.5},
    }
    variants = [
        dict(case, id="late-anti-heal", anti_heal=[{"start_s": 0, "end_s": 1, "reduction": 0.4}]),
        dict(case, id="unknown", events=[{"at_s": 0, "damage": {"kind": "magic", "flat": 100}}]),
        dict(
            case,
            id="unavailable",
            events=[
                *case["events"][:2],
                {"at_s": 1, "heal": {"amount": 500, "ready_at_s": 2, "condition_met": None}},
            ],
        ),
    ]
    result = compare_combat(
        Comparison.model_validate({"baseline": case, "alternatives": variants})
    )["cases"]
    assert result["base"]["ledger"][1]["damage_after_armor_layer"] == 500
    assert result["base"]["ledger"][1]["absorbed"] == 100
    assert result["base"]["remaining_hp"] == 1900
    assert result["late-anti-heal"]["remaining_hp"] == 2000
    assert result["unavailable"]["remaining_hp"] == 1600
    assert result["unknown"]["hp_delta_from_baseline"] is None
    assert result["base"]["cooldown_scenario"] == {"ready_at_s": 7, "ready_by_needed_at_s": True}


def test_confirmed_true_damage_formula_keeps_context_and_requires_target_hp():
    repo = Repository(ROOT)
    key, prop = "heroes/florentino", "skill-2.target-max-hp-true"
    value = repo.formula(key, prop, {"unspecified_ad": 700, "target_max_hp": 8000})
    assert value["value"] == pytest.approx(504)
    assert value["evidence"] == ["patch-2025-12-04"]
    with pytest.raises(ValueError, match="máu tối đa mục tiêu"):
        repo.formula(key, prop, {"unspecified_ad": 700})
    with pytest.raises(ValueError, match="mốc cấp"):
        repo.formula(
            "heroes/wiro", "skill-1.heal-on-hero", {"skill_rank": 1, "caster_bonus_hp": 2000}
        )


def test_coverage_counts_verified_fields_without_inflating_complete_heroes():
    coverage = measure_coverage(Repository(ROOT))
    assert coverage["hero_count"] == 130
    heroes = {row["id"]: row for row in coverage["heroes"]}
    assert heroes["dirak"]["ability_inventory_verified"]
    assert heroes["dirak"]["slots"]["skill-4"]["cooldown"] == "live"
    assert heroes["edras"]["slots"]["dark.skill-2"]["quantity"] == "live"
    assert not heroes["edras"]["complete"]
    assert coverage["complete_heroes"] == sum(hero["complete"] for hero in heroes.values())


def test_eval_questions_and_rubric_are_separate_and_cover_requested_groups():
    runner = runpy.run_path(str(ROOT / "evaluations/phase3/run.py"))
    questions, rubric = runner["suite"]()
    assert len(questions) == len(rubric) == 56
    assert all(set(row) == {"id", "lane", "class", "question"} for row in questions.values())


def test_chilling_smite_keeps_three_hero_damage_types_and_separate_recharge():
    repo = Repository(ROOT)
    live = repo.get("spells/te-cong")["live"]
    charges = live["active.charges"]["value"]
    assert charges["charges"] == 2
    assert charges["timing"] == {"cooldown_s": 10, "recharge_s": 45}
    for kind in ("physical", "magic", "true"):
        value = live[f"active.hero-{kind}"]["value"]
        assert value["damage_type"] == kind and "Mang " in value["trigger"]
