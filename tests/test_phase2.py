from pathlib import Path

import pytest

from item_build.local_review import classify_item_effect, observe
from item_build.retrieval import Repository
from item_build.storage import read

ROOT = Path(__file__).resolve().parents[1]
CASES = read(ROOT / "evaluations/phase2_cases.json")


@pytest.mark.parametrize("case", CASES, ids=lambda case: case["id"])
def test_match_case_context(case):
    repo = Repository(ROOT)
    ctx = repo.context(
        case["hero"], case["role"], case["enemies"], "fast_draft", include_candidates=True
    )
    assert case["feedback"]["type"] == "personal_experience"
    assert ctx["supplied_enemy_count"] == 5
    foes = {pack["id"]: pack for pack in ctx["enemies"]}
    for hero, props in case["review"].items():
        assert set(props) <= foes[hero]["live"].keys() | foes[hero].get("candidates", {}).keys()
    profile = ctx["personal_preference"]
    assert profile["checkpoints"] == [3, 4]
    assert profile["builds"] == 1 and profile["tactic_word_limit"] == 50
    assert "items/giap-thong-kho" not in ctx["related"]
    reviews = ctx["candidate_reviews"]
    assert reviews["items/giap-thong-kho"]["eligibility"] == "excluded_by_preference"
    assert reviews["items/nham-thuan"]["eligibility"] == "excluded_manual_activation"
    assert reviews["items/dai-dia-ma-nhan"]["eligibility"] == "reviewable"
    if case["id"] == "A":
        quillen = foes["quillen"]
        rear = quillen["candidates"]["passive.rear-critical"][0]
        assert "sau lưng" in rear["value"]["trigger"]
        conditional = next(
            edge for edge in quillen["candidate_relations"] if edge["id"] == "ma-nhan-quillen"
        )
        assert conditional["status"] == "UNVERIFIED"
        assert "đường vòng" in conditional["condition"] and "cửa sổ" in conditional["condition"]
        assert "hero-quillen" in ctx["evidence"]
    else:
        florentino = foes["florentino"]["candidates"]["skill-2.target-max-hp-true"][0]["value"]
        assert florentino["damage_type"] == "true" and florentino["basis"] == "target_max_hp"
        assert foes["raz"]["live"]["skill-2.magic-poke"]["value"]["damage_type"] == "magic"
        talisman = reviews["items/phu-chu-truong-sinh"]
        recharge = talisman["candidates"]["passive.out-of-combat-regen"][0]
        assert recharge["value"]["activation"] == "automatic"
        assert recharge["value"]["timing"]["interval_s"] == 2
        assert recharge["value"]["formula"]["terms"][0]["basis"] == "caster_max_hp"
        assert recharge["status"] == "UNVERIFIED" and "3 giây" in recharge["value"]["trigger"]
        shield = ctx["related"]["items/khien-thanh-quang"]["live"]["passive.shield-melee"]["value"]
        assert shield["activation"] == "automatic"
        assert "gây sát thương lên tướng" in shield["trigger"]
        assert shield["target"] == "self-and-lowest-health-nearby-ally"


def test_preferences_scope_and_candidates_opt_in():
    repo = Repository(ROOT)
    for name, position in (("Thane", "slayer"), ("Thane", None), ("Richter", "support")):
        result = repo.context(name, position, [], "fast_draft")
        assert result["personal_preference"] is None
        assert "candidates" not in result["hero"]
    candidate = repo.get("heroes/thane")["candidates"]["skill-3.base-type-conflict"]
    assert candidate[0]["evidence_layer"] == "conflict"


def test_every_public_item_in_exactly_one_group_and_mechanics_preserved():
    repo = Repository(ROOT)
    seen = set()
    for name in ("defense", "physical", "magic", "support", "boots", "jungle"):
        for key, entry in repo.read_file(repo.catalogs[name])["entries"].items():
            assert key not in seen
            seen.add(key)
            individual = repo.get(f"items/{key}")
            assert entry["shop_group"] == name == individual["shop_group"]
            assert entry["live"] == individual["live"]
            assert entry["candidates"] == individual.get("candidates", {})
            assert entry.get("candidate_relations", []) == individual.get("candidate_relations", [])
            for facts in [entry["live"].values(), *entry["candidates"].values()]:
                for fact in facts:
                    if isinstance(fact["value"], dict) and "effect" in fact["value"]:
                        assert fact["value"]["activation"] in {"manual", "automatic"}
    assert seen == repo.groups["items"].keys()


def test_observation_preserves_conditions_and_decimal():
    sentence = "Không thể chí mạng. Sau 0.5 giây gây sát thương chuẩn theo máu đã mất."
    result = observe(sentence)["paragraphs"][0]
    assert result["text"] == sentence
    assert result["quantity_literals"] == ["0.5 giây"]
    assert {mention["kind"] for mention in result["mentions"]} == {
        "crit",
        "true_damage",
        "missing_hp",
    }
    assert classify_item_effect("Nội tại duy nhất; hồi chiêu 5 giây") == "automatic_candidate"
    assert classify_item_effect("Kích hoạt duy nhất") == "manual_candidate"


def test_november_spell_patch_replaces_september_amount():
    repo = Repository(ROOT)
    key = "spells/ma-chung-hac-am"
    spell = repo.get(key)["live"]["active.shield"]
    assert spell["effective_from"] == "2026-11-17"
    assert spell["value"]["formula"]["base"] == 350
    previous = repo.get(key, canonical=True)["facts"]["active.shield"][0]
    assert previous["status"] == "SUPERSEDED"
    assert previous["value"]["formula"]["base"] == 280


def test_recipe_multiplicity_and_conflicting_ap():
    repo = Repository(ROOT)
    rhea = repo.get("items/quyen-truong-rhea")
    parts = rhea["live"]["shop.recipe"]["value"]
    assert parts.count("items/huyet-truong") == 2
    assert all(repo.get(part) for part in parts)
    orb = repo.get("items/qua-cau-bang-suong")
    assert "stat.ap" not in orb["live"]
    assert orb["candidates"]["stat.ap"][0]["evidence_layer"] == "conflict"
