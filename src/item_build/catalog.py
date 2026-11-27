from collections import defaultdict
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
