from collections import defaultdict
from itertools import combinations
from pathlib import Path

from pydantic import Field

from .models import Id, Model, Nonempty
from .storage import read

ITEM_GROUPS = ("defense", "physical", "magic", "support", "boots", "jungle")


class Preference(Model):
    hero: Id
    role: Id
    excluded_items: list[Id]
    manual_activation: dict[Id, bool]
    checkpoints: list[int]
    review_items: list[Id]
    priorities: list[Nonempty]
    rotation: Nonempty
    builds: int = Field(gt=0)
    tactic_word_limit: int = Field(gt=0)


def load_preferences(root: Path, entities: dict) -> dict:
    preferences = {}
    for path in sorted((root / "sources/preferences").glob("*.json")):
        preference = Preference.model_validate(read(path))
        key = f"{preference.hero}/{preference.role}"
        if (
            key in preferences
            or not {f"heroes/{preference.hero}", f"roles/{preference.role}"} <= entities.keys()
        ):
            raise ValueError(f"Hồ sơ sở thích trùng hoặc tham chiếu sai: {key}.")
        if any(
            f"items/{item}" not in entities
            for item in preference.excluded_items + preference.review_items
        ):
            raise ValueError(f"Hồ sơ sở thích có trang bị không tồn tại: {key}.")
        if not preference.manual_activation.keys() <= set(ITEM_GROUPS):
            raise ValueError(f"Hồ sơ sở thích có nhóm trang bị không tồn tại: {key}.")
        preferences[key] = preference.model_dump(mode="json")
    return preferences


def candidate_layer(record, evidence):
    refs = [evidence[key] for key in record.evidence]
    if any(ref.verification_status == "conflict" for ref in refs):
        return "conflict"
    if record.kind != "mechanical_fact":
        return "inference"
    if any(ref.source_type == "official" for ref in refs):
        return "official_undated_or_unresolved"
    return "community_or_unverified"


def activation_review(pack: dict) -> str:
    """Infer the input requirement only from explicit mechanics or a sourced declaration."""
    live, candidates = pack["live"], pack["candidates"]
    modes = set()
    for key in live.keys() | candidates.keys():
        timeline = [live[key]] if key in live else candidates[key]
        for fact in timeline:
            value = fact["value"]
            if key == "shop.activation" and isinstance(value, str):
                if value == "mixed":
                    modes.update(("manual", "automatic"))
                elif value in {"manual", "automatic", "stats_only"}:
                    modes.add(value)
            elif isinstance(value, dict) and value.get("activation"):
                modes.add(value["activation"])
    if "manual" in modes:
        return "mixed" if "automatic" in modes else "manual"
    if "automatic" in modes:
        return "automatic"
    if "stats_only" in modes:
        return "stats_only"
    return "unknown"


def eligibility(item_id: str, entry: dict, preferences: dict | None) -> str:
    if preferences is None:
        return "no_personal_filter"
    if item_id in preferences["excluded_items"]:
        return "excluded_by_preference"
    manual_ok = preferences["manual_activation"].get(entry["shop_group"], False)
    if entry["activation"] in {"manual", "mixed"} and not manual_ok:
        return "excluded_manual_activation"
    if entry["activation"] == "unknown" and not manual_ok:
        return "activation_needs_confirmation"
    return "reviewable"


def pareto_front(vectors):
    """Return undominated IDs for maximized, comparable coordinates.

    Unknown coordinates prevent elimination. A tie leaves both options available.
    """
    survivors = []
    for key, values in vectors.items():
        if not any(
            key != other
            and len(values) == len(alternative)
            and all(
                a is not None and b is not None and b >= a
                for a, b in zip(values, alternative, strict=True)
            )
            and any(b > a for a, b in zip(values, alternative, strict=True))
            for other, alternative in vectors.items()
        ):
            survivors.append(key)
    return survivors


DEFENSE_CHECKPOINT_ITEMS = (
    "khien-that-truyen",
    "ao-choang-than-ra",
    "khien-thanh-quang",
    "giap-gaia",
    "huan-chuong-troy",
    "phu-chu-truong-sinh",
)
COMPARISON_UNITS = {
    "stat.price": "gold",
    "stat.hp": "hp",
    "stat.armor": "armor",
    "stat.magic-defense": "magic_defense",
    "stat.cooldown-reduction": "ratio",
}
COMPARISON_CONFIDENCE = {
    ("UNVERIFIED", "community_or_unverified"): 0,
    ("UNVERIFIED", "official_undated_or_unresolved"): 1,
    ("LIVE_VN",): 2,
}


def comparison_quantity(item, field):
    """Use LIVE first, or an agreed candidate quantity with source confidence."""
    unit = COMPARISON_UNITS[field]

    def amount(claim):
        value = claim.get("value")
        if not isinstance(value, dict) or value.get("unit") != unit:
            return None
        number = value["amount"]
        if number < 0 or (unit == "gold" and int(number) != number):
            return None
        return number

    live = item["live"].get(field)
    if live is not None and (value := amount(live)) is not None:
        return [value, "LIVE_VN"]
    values = defaultdict(set)
    for claim in item.get("candidates", {}).get(field, []):
        confidence = (claim["status"], claim["evidence_layer"])
        if confidence in COMPARISON_CONFIDENCE and (value := amount(claim)) is not None:
            values[value].add(confidence)
    if len(values) != 1:
        return None
    ((value, levels),) = values.items()
    return [value, *max(levels, key=COMPARISON_CONFIDENCE.__getitem__)]


def defense_purchase_matrix(items):
    def sum_prices(*rows):
        confidence = min((tuple(row[1:]) for row in rows), key=COMPARISON_CONFIDENCE.__getitem__)
        return [sum(row[0] for row in rows), *confidence]

    def common_group_price(group, tier):
        prices = [
            comparison_quantity(item, "stat.price")
            for item in items.values()
            if item["shop_group"] == group
            and item["live"].get("shop.tier", {}).get("value", {}).get("amount") == tier
        ]
        if not prices or None in prices or len({row[0] for row in prices}) != 1:
            return None
        return min(prices, key=lambda row: COMPARISON_CONFIDENCE[tuple(row[1:])])

    selected = [id for id in DEFENSE_CHECKPOINT_ITEMS if id in items]
    values = {
        id: [comparison_quantity(items[id], field) for field in COMPARISON_UNITS] for id in selected
    }
    boots = common_group_price("boots", 2)
    support = common_group_price("support", 3)
    base = sum_prices(boots, support) if boots and support else None
    prices = {id: row[0] for id, row in values.items()}
    totals = {
        f"{a}+{b}": sum_prices(base, prices[a], prices[b])
        for a, b in combinations(selected, 2)
        if base is not None and prices[a] is not None and prices[b] is not None
    }
    groups = defaultdict(set)
    for id, entry in items.items():
        for prop in entry["live"].keys() | entry["candidates"].keys():
            claims = [entry["live"][prop]] if prop in entry["live"] else entry["candidates"][prop]
            for claim in claims:
                mechanic = claim["value"]
                if (
                    isinstance(mechanic, dict)
                    and "unique_group" in mechanic
                    and claim.get("evidence_layer") != "conflict"
                ):
                    groups[mechanic["unique_group"]].add(id)
    return {
        "columns": list(COMPARISON_UNITS),
        "rows": values,
        "slot_1_2_full_price": base[0] if base else None,
        **({"slot_1_2_price_basis": base[1:]} if base and base[1] != "LIVE_VN" else {}),
        "slot_3_full_price": {
            id: sum_prices(base, value)
            for id, value in prices.items()
            if base is not None and value is not None
        },
        "slot_4_full_price_pairs": totals,
        "shared_unique_groups": {
            group: sorted(ids) for group, ids in sorted(groups.items()) if len(ids) > 1
        },
        "scope": "Giá nguyên món. Ô null là thiếu hoặc chưa có giá trị duy nhất. "
        "Các tổng giữ mức bằng chứng thấp nhất trong các giá thành phần. "
        "Kiểm tra bù thành phần, nội tại trùng và trần CDR trước khi tính hiệu lực.",
    }


def group_packs(packs: dict) -> dict:
    groups = defaultdict(dict)
    for key, pack in packs.items():
        kind, item_id = key.split("/", 1)
        if kind not in {"items", "runes", "enchantments", "spells", "battlefield"}:
            continue
        group = pack["shop_group"] if kind == "items" else kind
        groups[group][item_id] = {
            field: pack[field]
            for field in (
                "name",
                "live",
                "candidates",
                "relations",
                "candidate_relations",
                "review_relations",
                "unknown",
                "shop_group",
                "activation",
            )
            if field in pack and (pack[field] or field in {"live", "candidates"})
        }
    return dict(groups)
