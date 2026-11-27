from collections import Counter

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
        "ability_inventory_verified": has_inventory,
        "fully_reviewed_slots": reviewed_slots,
        "stats": stats,
        "slots": slot_states,
        "candidate_layers": dict(
            Counter(fact["evidence_layer"] for variants in candidates.values() for fact in variants)
        ),
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
