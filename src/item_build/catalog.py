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
DEFENSE_STAT_FIELDS = (
    "stat.price",
    "stat.hp",
    "stat.armor",
    "stat.magic-defense",
    "stat.cooldown-reduction",
)


def defense_purchase_matrix(items):
    def quantity(item, field):
        if field in item["live"]:
            return [item["live"][field]["amount"], "LIVE_VN"]
        candidate = item.get("academy_candidates", {}).get(field)
        return [candidate["amount"], "UNVERIFIED"] if candidate else None

    selected = [id for id in DEFENSE_CHECKPOINT_ITEMS if id in items]
    opening = [
        id
        for id, item in items.items()
        if item["shop_group"] == "boots" and item["live"].get("shop.tier", {}).get("amount") == 2
    ]
    support = [
        id
        for id, item in items.items()
        if item["shop_group"] == "support" and item["live"].get("shop.tier", {}).get("amount") == 3
    ]
    values = {id: [quantity(items[id], field) for field in DEFENSE_STAT_FIELDS] for id in selected}
    openings = {items[id]["live"].get("stat.price", {}).get("amount") for id in opening}
    supports = {items[id]["live"].get("stat.price", {}).get("amount") for id in support}
    base = (
        min(openings) + min(supports)
        if None not in openings | supports and len(openings) == len(supports) == 1
        else None
    )
    prices = {id: row[0] for id, row in values.items()}
    totals = {
        f"{a}+{b}": [
            base + prices[a][0] + prices[b][0],
            "LIVE_VN" if prices[a][1] == prices[b][1] == "LIVE_VN" else "UNVERIFIED",
        ]
        for a, b in combinations(selected, 2)
        if base is not None and prices[a] is not None and prices[b] is not None
    }
    groups = defaultdict(set)
    for id, entry in items.items():
        for layer in (entry["live"], entry.get("academy_candidates", {})):
            for mechanic in layer.values():
                if isinstance(mechanic, dict) and "unique_group" in mechanic:
                    groups[mechanic["unique_group"]].add(id)
    return {
        "columns": DEFENSE_STAT_FIELDS,
        "rows": values,
        "slot_1_2_full_price": base,
        "slot_3_full_price": {
            id: [base + value[0], value[1]]
            for id, value in prices.items()
            if base is not None and value is not None
        },
        "slot_4_full_price_pairs": totals,
        "shared_unique_groups": {
            group: sorted(ids) for group, ids in sorted(groups.items()) if len(ids) > 1
        },
        "scope": "Mốc nguyên món khi không tính bù thành phần hoặc bán đồ. Ô null là thiếu dữ kiện. "
        "Nhóm nội tại trùng cần đối chiếu trước khi cộng. Giữ CDR thô khi chưa xác minh trần.",
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
