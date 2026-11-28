from collections import Counter

from .catalog import eligibility
from .retrieval import Repository

REQUIRED_STATS = (
    "hp",
    "armor",
    "magic-defense",
    "attack-damage",
    "attack-speed",
    "move-speed",
    "mana",
    "hp-regen",
)
VARIANTS_BY_HERO = {
    "edras": [
        "light.skill-1",
        "light.skill-2",
        "light.skill-3",
        "dark.skill-1",
        "dark.skill-2",
        "dark.skill-3",
    ],
    "yena": [
        "crescent.skill-1",
        "crescent.skill-2",
        "crescent.skill-3",
        "dual.skill-1",
        "dual.skill-2",
        "dual.skill-3",
    ],
    "sinestrea": ["melee.skill-2", "ranged.skill-2", "ranged.skill-3"],
}
SLOT_FIELDS = (
    "effect",
    "quantity",
    "cooldown",
    "cooldown_resolved",
    "duration",
    "trigger",
    "exceptions",
    "interactions",
)


def slot_presence(slot, facts):
    mechanics = [
        v
        for key, v in facts.items()
        if key.startswith(f"{slot}.") and isinstance(v, dict) and "effect" in v
    ]
    cooldowns = [
        m["timing"]["cooldown_s"] for m in mechanics if "cooldown_s" in m.get("timing", {})
    ]
    return {
        "effect": bool(mechanics),
        "quantity": any("formula" in m or "amount" in m for m in mechanics),
        "cooldown": bool(cooldowns),
        "cooldown_resolved": bool(cooldowns)
        and all(
            not isinstance(cooldown, dict)
            or all(
                "origin" in term
                for term in cooldown.get("terms", [])
                if term["basis"] in {"skill_rank", "hero_level"}
            )
            for cooldown in cooldowns
        ),
        "duration": any("duration_s" in m.get("timing", {}) for m in mechanics),
        "trigger": any(
            m.get("trigger") and not m["trigger"].startswith("Hồi chiêu") for m in mechanics
        ),
        "exceptions": any(m.get("exceptions") for m in mechanics),
        "interactions": any(m.get("interactions") for m in mechanics),
    }


def assess_hero(pack):
    live = {key: fact["value"] for key, fact in pack["live"].items()}
    candidates = pack.get("candidates", {})
    inventory = live.get("identity.ability-inventory")
    has_inventory = isinstance(inventory, list) and bool(inventory)
    slots = ["passive", "skill-1", "skill-2", "skill-3", *VARIANTS_BY_HERO.get(pack["id"], [])]
    # A reviewed inventory may name more forms, including an extra skill.
    if has_inventory:
        slots = list(dict.fromkeys(["passive", *inventory, *VARIANTS_BY_HERO.get(pack["id"], [])]))
    stats = {
        f"{kind}.{name}": "live"
        if f"stat.{kind}.{name}" in live
        else "reviewed_na"
        if live.get(f"stat.{kind}.{name}.review.na") is True
        else "candidate"
        if f"stat.{kind}.{name}" in candidates
        else "unknown"
        for kind in ("base", "growth")
        for name in REQUIRED_STATS
    }
    slot_states = {}
    for slot in slots:
        live_fields = slot_presence(slot, live)
        reviewed_fields = {
            field for field in SLOT_FIELDS if live.get(f"{slot}.review.{field}-na") is True
        }
        candidate_fields = {
            field
            for key, variants in candidates.items()
            for fact in variants
            for field, present in slot_presence(slot, {key: fact["value"]}).items()
            if present
        }
        slot_states[slot] = {
            field: "live"
            if live_fields[field]
            else "reviewed_na"
            if field in reviewed_fields
            else "candidate"
            if field in candidate_fields
            else "unknown"
            for field in SLOT_FIELDS
        }
    # A slot having one instance per column says nothing about missing effects within it.
    reviewed_slots = [slot for slot in slots if live.get(f"{slot}.review.complete") is True]
    required_complete = all(state in {"live", "reviewed_na"} for state in stats.values()) and all(
        state in {"live", "reviewed_na"}
        for fields in slot_states.values()
        for state in fields.values()
    )
    complete = has_inventory and len(reviewed_slots) == len(slots) and required_complete
    return {
        "id": pack["id"],
        "name": pack["name"],
        "complete": complete,
        "quantitative_components": [
            key
            for key, value in live.items()
            if isinstance(value, dict)
            and "effect" in value
            and (
                "amount" in value
                or isinstance(value.get("timing", {}).get("cooldown_s"), (int, float, list))
                or (
                    "formula" in value
                    and all(
                        term["basis"] != "unspecified_ad"
                        and (term["basis"] not in {"hero_level", "skill_rank"} or "origin" in term)
                        for term in value["formula"].get("terms", [])
                    )
                )
            )
        ],
        "ability_inventory_verified": has_inventory,
        "fully_reviewed_slots": reviewed_slots,
        "stats": stats,
        "slots": slot_states,
        "candidate_layers": dict(
            Counter(fact["evidence_layer"] for variants in candidates.values() for fact in variants)
        ),
    }


def assess_readiness(
    repo: Repository,
    hero: str,
    role: str | None,
    items: list[str],
    enemies: list[str],
    anchors: list[str],
) -> dict:
    hero_id = repo.identify(hero)
    key = f"heroes/{hero_id}"
    pack = repo.get(key)
    coverage = assess_hero(pack)
    threats = [f"heroes/{repo.identify(enemy)}" for enemy in enemies]
    checked = {}
    for anchor in anchors:
        entity, _, prop = anchor.partition("#")
        if not prop:
            raise ValueError("Mỗi neo cần dạng nhóm/id#thuộc.tính.")
        checked[anchor] = prop in repo.get(entity)["live"]
    confirmed_entities = {anchor.partition("#")[0] for anchor, ok in checked.items() if ok}
    preference_path = repo.preferences.get(f"{hero_id}/{role}")
    preference = repo.read_file(preference_path) if preference_path else None
    gaps = [anchor for anchor, ok in checked.items() if not ok]
    fast_gaps = list(gaps)
    if not role:
        fast_gaps.append("Vị trí")
    if len(items) != 6 or len(set(items)) != 6:
        fast_gaps.append("Sáu ID trang bị khác nhau")
    for entity in [key, *threats]:
        if not any(
            anchor.startswith(f"{entity}#") and not anchor.split("#", 1)[1].startswith("identity.")
            for anchor, ok in checked.items()
            if ok
        ):
            fast_gaps.append(f"Neo cơ chế ảnh hưởng quyết định của {entity}")
    for item in items:
        entry = repo.get(f"items/{item}")
        if "stat.price" not in entry["live"] or eligibility(item, entry, preference) not in {
            "no_personal_filter",
            "reviewable",
        }:
            fast_gaps.append(f"Giá hoặc điều kiện chọn items/{item}")
        if f"items/{item}" not in confirmed_entities:
            fast_gaps.append(f"Neo cơ chế hoặc chỉ số đầu ra của items/{item}")
    prep_gaps = list(gaps)
    if not role or not any(
        anchor.startswith(f"{key}#") and not anchor.split("#", 1)[1].startswith("identity.")
        for anchor, ok in checked.items()
        if ok
    ):
        prep_gaps.append("Vị trí và neo cơ chế chủ đạo")
    # When the data exists these properties describe the validation of a specific selection.
    # Guides with example loadouts do not establish global selection legality.
    for rule, label in {
        "preparation.rune-selection-rules": "Giới hạn ô, màu và số lượng ngọc",
        "preparation.enchantment-selection-rules": "Luật nhánh chính/phụ và tầng phù hiệu",
    }.items():
        if rule not in repo.get("battlefield/ranked-vn")["live"]:
            prep_gaps.append(label)
    for group, label in (("runes", "ngọc"), ("enchantments", "phù hiệu"), ("spells", "phép")):
        if not any(entity.startswith(f"{group}/") for entity in confirmed_entities):
            prep_gaps.append(f"Neo cho cấu hình {label} đã chọn")
    return {
        "id": hero_id,
        "role": role,
        "checked_anchors": checked,
        "FAST_DRAFT_READY": {"ready": not fast_gaps, "gaps": fast_gaps},
        "HERO_PREPARATION_READY": {"ready": not prep_gaps, "gaps": prep_gaps},
        "QUANTITATIVE_REASONING_READY": {
            "ready": bool(coverage["quantitative_components"]),
            "components": coverage["quantitative_components"],
            "scope": "Thành phần riêng lẻ, cần nhập đủ biến và kiểm tra điều kiện trước khi tính.",
        },
        "FULL_KNOWLEDGE_READY": {
            "ready": coverage["complete"],
            "ability_inventory_verified": coverage["ability_inventory_verified"],
            "stats": coverage["stats"],
            "slots": coverage["slots"],
        },
    }


def measure_coverage(repo: Repository) -> dict:
    heroes = [assess_hero(repo.get(f"heroes/{key}")) for key in sorted(repo.groups["heroes"])]
    return {
        "version": repo.version["patch_id"],
        "stats_fields": dict(Counter(state for hero in heroes for state in hero["stats"].values())),
        "skill_fields": {
            field: dict(Counter(slot[field] for hero in heroes for slot in hero["slots"].values()))
            for field in SLOT_FIELDS
        },
        "complete_heroes": sum(hero["complete"] for hero in heroes),
        "hero_count": len(heroes),
        "counts_by_group": repo.version["coverage"],
        "heroes": heroes,
    }
