from pathlib import Path

import pytest

from item_build.benchmark import THANE_CLOUD_CASE, THANE_EVITA_CASE
from item_build.catalog import pareto_front
from item_build.progressive import THANE_SUPPORT_PACK
from item_build.reasoning import Combat, PurchaseScenario, evaluate_combat, plan_purchases
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


def test_thane_warm_draft_preserves_evidence_and_reads_only_new_heroes():
    repo = Repository(ROOT)
    shared = repo.read_file(THANE_SUPPORT_PACK)
    before = set(repo.cached)
    draft = repo.context("Thane", "support", THANE_CLOUD_CASE, "fast_draft", layer="l1")
    assert set(repo.cached) - before == {
        f"packs/l1/heroes/{id}.json" for id in ("alice", "hayate", "arthur", "trieu-van", "lauriel")
    }
    assert {rule["id"] for rule in draft["team_threats"]} == {"alice-hayate-shielded-entry"}
    before = set(repo.cached)
    repo.context("Thane", "support", ["Alice", "Toro"], "fast_draft", layer="l1")
    assert set(repo.cached) - before == {"packs/l1/heroes/toro.json"}

    items = draft["shortlist"]
    assert not {"giap-thong-kho", "nham-thuan", "vo-anh-tien"} & items.keys()
    assert shared["academy_candidate_defaults"]["status"] == "UNVERIFIED"
    assert items["phu-chu-truong-sinh"]["academy_candidates"]["stat.hp"]["amount"] == 1500
    assert items["giap-gaia"]["live"]["passive.proc-amount"]["formula"]["terms"][0] == {
        "basis": "caster_max_hp",
        "coefficient": 0.04,
    }
    for item in (
        "dai-dia-mo-troi",
        "giay-kien-cuong",
        "khien-thanh-quang",
        "giap-gaia",
        "ao-choang-than-ra",
        "phu-chu-truong-sinh",
    ):
        assert items[item]["icon_reference"]["scope"] == "official_artwork"
        assert items[item]["icon_reference"]["dot"] != "⚪"
        assert "identity.icon-color" not in items[item]["live"]

    heroes = draft["heroes"]
    hayate = heroes["hayate"]["live"]["passive.marked-true"]
    assert hayate["damage_type"] == "true" and hayate["formula"]["base"] == 45
    assert {term["basis"] for term in hayate["formula"]["terms"]} == {"unspecified_ad"}
    arthur = heroes["arthur"]["candidates"]["skill-1.mark-max-hp-magic"][0]["value"]
    assert (
        arthur["damage_type"] == "magic"
        and arthur["formula"]["terms"][0]["basis"] == "target_max_hp"
    )
    assert (
        heroes["lauriel"]["candidates"]["passive.damage-type-conflict"][0]["evidence_layer"]
        == "conflict"
    )


def test_thane_compares_same_budget_and_retains_unresolved_options():
    repo = Repository(ROOT)
    draft = repo.context("Thane", "support", THANE_EVITA_CASE, "fast_draft", layer="l1")
    assert {rule["id"] for rule in draft["team_threats"]} == {"evita-toro-persistent-magic"}
    matrix = draft["purchase_comparison"]
    for item in ("giap-nhe", "dai-khang-phep", "giay-thep", "tho-he-bao-thach"):
        assert draft["shortlist"][item]["eligibility"] == "component"
    assert matrix["slot_3_full_price"]["ao-choang-than-ra"] == [4660, "LIVE_VN"]
    assert matrix["slot_3_full_price"]["khien-that-truyen"] == [4700, "UNVERIFIED"]
    assert "khien-thanh-quang" not in matrix["slot_3_full_price"]
    assert matrix["slot_4_full_price_pairs"]["ao-choang-than-ra+giap-gaia"] == [6840, "LIVE_VN"]
    assert matrix["slot_4_full_price_pairs"]["khien-that-truyen+giap-gaia"] == [6880, "UNVERIFIED"]
    assert matrix["shared_unique_groups"]["linh-gac"] == ["giap-hiep-si", "khien-that-truyen"]

    def path(first_item, second_item, gold, *, quoted=False):
        steps = [
            {
                "item": item,
                "cumulative_gold": budget,
                "final_slot": slot,
                "phase": "mid",
                "purpose": "So hai nhánh tại cùng ngân sách",
            }
            for slot, (item, budget) in enumerate(
                [
                    ("dai-dia-mo-troi", 1900),
                    ("giay-ho-ve", 2600),
                    (first_item, 4700),
                    (second_item, gold),
                ],
                1,
            )
        ]
        if quoted:
            steps[2]["quoted_cost"] = 2100
        return {"id": first_item, "steps": steps}

    for gold in (6840, 6880):
        case = PurchaseScenario.model_validate(
            {
                "hero": "Thane",
                "role": "support",
                "retain_completed_items": True,
                "paths": [
                    path("ao-choang-than-ra", "giap-gaia", gold),
                    path("khien-that-truyen", "giap-gaia", gold, quoted=True),
                ],
            }
        )
        result = plan_purchases(repo, case)["paths"]
        assert result["ao-choang-than-ra"]["steps"][-1]["gold_after"] == gold - 6840
        shield = result["khien-that-truyen"]["steps"]
        assert shield[2]["cost_basis"] == "scenario_quote"
        if gold == 6840:
            assert shield[3]["shortfall"] == 40
        else:
            assert shield[3]["gold_after"] == 0
        assert result["khien-that-truyen"]["purchased_totals"]["unresolved_stat_fields"]["stat.hp"]

    # Each coordinate is measured independently. Unknown ally cover precludes elimination.
    assert pareto_front(
        {"baseline": (100, 150, 0), "improved": (125, 150, 0), "unknown": (80, 100, None)}
    ) == ["improved", "unknown"]


def test_gaia_heals_only_after_proc_and_during_actual_antiheal_window():
    repo = Repository(ROOT)
    for ready, anti_heal, expected in (
        (False, [], 0),
        (True, [], 240),
        (True, [{"start_s": 1, "fact": "items/ao-choang-than-ra#passive.anti-heal"}], 144),
    ):
        result = evaluate_combat(
            Combat.model_validate(
                {
                    "id": "gaia",
                    "assumptions": "Giả định 6.000 máu tối đa và Hồi phục phát sinh ở giây 2.",
                    "max_hp": 6000,
                    "initial_hp": 4000,
                    "anti_heal": anti_heal,
                    "events": [
                        {
                            "at_s": 2,
                            "heal": {
                                "fact": "items/giap-gaia#passive.proc-amount",
                                "condition_met": ready,
                                "ready_at_s": 2,
                            },
                        }
                    ],
                }
            ),
            repo,
        )
        assert result["ledger"][0]["effective_heal"] == expected
