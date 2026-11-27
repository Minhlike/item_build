from datetime import date
from pathlib import Path

import pytest
from pydantic import ValidationError

from item_build.compiler import active, compile_repo
from item_build.models import Basis, CanonicalEntity, Fact, Formula, Mechanic
from item_build.retrieval import HeroLookupError, Repository

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def repo():
    return Repository(ROOT)


def latest(repo, hero, key):
    return repo.get(f"heroes/{hero}", canonical=True)["facts"][key][-1]["value"]


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("Triệu Vân", "trieu-van"),
        ("trieu van", "trieu-van"),
        ("TV", "trieu-van"),
        ("Zanis", "trieu-van"),
        ("Y'bneth", "ybneth"),
        ("Boterfly", "butterfly"),
        ("BOLT BARON", "bolt-baron"),
        ("Flowborn pháp sư", "flowborn-2"),
        ("Flowborn ADC", "flowborn"),
    ],
)
def test_lookup(repo, name, expected):
    assert repo.identify(name) == expected


def test_alias_ambiguity(repo):
    with pytest.raises(HeroLookupError, match="nhiều bản"):
        repo.identify("Flowborn")
    with pytest.raises(HeroLookupError, match="Không tìm thấy"):
        repo.identify("xx")


def test_first_draft_mechanisms(repo):
    ctx = repo.context("Thane", "support", ["TV", "BB", "Allain", "Natalya", "Ryoma"], "fast_draft")
    assert ctx["supplied_enemy_count"] == 5
    bolt = next(e for e in ctx["enemies"] if e["id"] == "bolt-baron")
    assert bolt["live"]["passive.basic-magic"]["value"]["delivery"] == "basic_attack"
    assert bolt["live"]["skill-1.magic"]["value"]["delivery"] == "ability"
    assert {
        bolt["live"][key]["value"]["damage_type"]
        for key in ("passive.basic-magic", "skill-1.magic")
    } == {"magic"}
    assert latest(repo, "allain", "passive.hit-heal")["effect"] == "heal"
    assert latest(repo, "allain", "passive.magic-pen")["effect"] == "magic_pen"
    assert latest(repo, "allain", "skill-3.damage")["damage_type"] == "true"
    assert latest(repo, "thane", "passive.low-hp-heal")["basis"] == "caster_max_hp"
    assert latest(repo, "thane", "passive.low-hp-mitigation")["effect"] == "damage_reduction"
    assert (
        latest(repo, "thane", "skill-3.damage-heal")["formula"]["terms"][0]["basis"]
        == "damage_dealt"
    )
    assert latest(repo, "trieu-van", "passive.takedown-heal")["effect"] == "heal"
    assert latest(repo, "trieu-van", "skill-2.lifesteal")["effect"] == "lifesteal"
    assert latest(repo, "trieu-van", "skill-3.on-hit-true")["damage_type"] == "true"
    ra_live = ctx["related"]["items/ao-choang-than-ra"]["live"]
    assert ra_live["passive.anti-heal"]["value"]["effect"] == "heal_reduction"
    assert "passive.burn" not in ra_live
    ra = repo.get("items/ao-choang-than-ra", canonical=True)
    assert ra["facts"]["passive.burn"][0]["value"]["timing"]["interval_s"] == 1
    assert next(edge for edge in ra["relations"] if edge["id"] == "ra-allain")["condition"]


def test_second_draft_vision_and_damage(repo):
    ctx = repo.context(
        "Thane", "support", ["Richter", "Triệu Vân", "Hayate", "Raz", "Kaine"], "fast_draft"
    )
    foes = {pack["id"]: pack for pack in ctx["enemies"]}
    hayate = foes["hayate"]["live"]["passive.marked-true"]["value"]
    assert hayate["target"] == "same-marked-target"
    assert hayate["damage_type"] == "true" and hayate["stacks"] == 6
    assert hayate["timing"]["duration_s"] == 4
    assert foes["kaine"]["live"]["passive.stealth"]["value"]["effect"] == "stealth"
    assert "active.reveal" not in ctx["related"]["items/dai-dia-ma-nhan"]["live"]
    ma_nhan = repo.get("items/dai-dia-ma-nhan", canonical=True)
    assert ma_nhan["facts"]["active.reveal"][0]["value"]["effect"] == "reveal"
    assert ma_nhan["relations"][0]["object"] == "heroes/kaine#passive.stealth"
    assert latest(repo, "richter", "skill-2.cc-immunity")["effect"] == "cc_immunity"
    assert latest(repo, "richter", "skill-2.damage-immunity")["effect"] == "damage_immunity"
    assert "tactics.ambush" in foes["raz"]["review_properties"]
    assert "tactics.peel" in ctx["hero"]["live"]


def test_third_draft_fennik_timing_and_omen(repo):
    ctx = repo.context(
        "Thane", "support", ["Y'bneth", "Fennik", "TV", "Omen", "Preyta"], "fast_draft"
    )
    foe = {pack["id"]: pack for pack in ctx["enemies"]}
    fennik = foe["fennik"]["live"]["skill-1.detonation"]["value"]
    assert fennik["target"] == "marked-unit-or-structure"
    assert fennik["stacks"] == 4 and fennik["timing"]["duration_s"] == 4
    assert fennik["formula"]["base"] == 125
    assert foe["preyta"]["live"]["passive.mark-burst"]["value"]["formula"]["base"] == 180
    assert "tactics.split" in foe["omen"]["review_properties"]
    assert latest(repo, "omen", "passive.cooldown-reduction")["effect"] == "reduce_cooldown"
    assert latest(repo, "omen", "skill-2.mitigation")["timing"]["duration_s"] == 2
    assert "tactics.objective-trade" in ctx["battlefield"]["live"]


def test_fourth_draft_rework_and_forms(repo):
    ctx = repo.context(
        "Thane", "support", ["Butterfly", "Yue", "Arthur", "Hayate", "Edras"], "fast_draft"
    )
    foe = {pack["id"]: pack for pack in ctx["enemies"]}
    butterfly = foe["butterfly"]["live"]
    assert butterfly["skill-1.blade"]["value"]["damage_type"] == "physical"
    assert butterfly["skill-2.first-hit"]["value"]["damage_type"] == "magic"
    assert butterfly["skill-2.empowered-hit"]["value"]["charges"] == 3
    assert "Mỗi lần" in butterfly["skill-3.mark-heal"]["value"]["trigger"]
    assert "tactics.poke" in foe["yue"]["review_properties"]
    assert "skill-2.shield" in foe["arthur"]["live"]
    assert "light.skill-2.heal" in foe["edras"]["review_properties"]


@pytest.mark.parametrize(
    ("hero", "lane"),
    [
        ("Allain", "slayer"),
        ("Butterfly", "jungle"),
        ("Natalya", "mid"),
        ("Hayate", "dragon"),
        ("Thane", "support"),
        ("Rouie", "support"),
    ],
)
def test_role_paths(repo, hero, lane):
    ctx = repo.context(hero, lane, [], "hero_preparation")
    assert ctx["role"] == lane
    assert ctx["enemies"] == []
    assert "tactics.rotation" in ctx["tactical_role"]["live"]
    assert ctx["related"]
    assert "official-roster" in ctx["evidence"]
    assert repo.files_read <= 10


def test_packs_match_canonical(repo):
    assert compile_repo(ROOT, check=True)["changed"] == 0
    for group, index in repo.groups.items():
        for entity_id in index:
            key = f"{group}/{entity_id}"
            pack = repo.get(key)
            canonical = CanonicalEntity.model_validate(repo.get(key, canonical=True))
            assert pack["unknown"] == canonical.unknown
            for property_id, record in pack["live"].items():
                fact = Fact.model_validate(record)
                candidates = canonical.facts[property_id]
                assert any(
                    other.value == fact.value and other.evidence == fact.evidence
                    for other in candidates
                )


def test_formula_units_and_unknown_rank_origin():
    with pytest.raises(ValidationError, match="Đơn vị"):
        Formula.model_validate(
            {
                "base": 0,
                "unit": "second",
                "terms": [{"basis": "target_max_hp", "coefficient": 0.15}],
            }
        )
    with pytest.raises(ValidationError, match="đúng một loại"):
        Mechanic.model_validate({"effect": "damage", "target": "enemy", "trigger": "hit"})
    formula = Formula.model_validate(
        {"base": 9, "unit": "second", "terms": [{"basis": "skill_rank", "coefficient": -0.4}]}
    )
    with pytest.raises(ValueError, match="mốc cấp"):
        formula.calculate({Basis.SKILL_RANK: 2.0})
    formula.terms[0].origin = 1
    assert formula.calculate({Basis.SKILL_RANK: 2}) == pytest.approx(8.6)


def test_cooldowns_and_patch_predecessors(repo):
    day = date(2026, 11, 27)
    timeline = repo.get("heroes/fennik", canonical=True)["facts"]["skill-1.detonation"]
    previous, current = list(map(Fact.model_validate, timeline))
    assert previous.effective_from is None and not active(previous, day)
    assert active(current, day)
    assert (
        repo.cooldown("spells/dich-chuyen", "active.teleport", {}, None, None)["base_seconds"] == 90
    )
    assert repo.cooldown("spells/dich-chuyen", "active.teleport", {}, 0.5, 0.4)["seconds"] == 54
    with pytest.raises(ValueError, match="chưa được xác minh"):
        repo.cooldown("heroes/thane", "skill-1.cooldown", {}, None, None)
    with pytest.raises(ValueError, match="mốc cấp"):
        repo.cooldown("heroes/bolt-baron", "skill-1.cooldown", {"skill_rank": 2.0}, None, None)
