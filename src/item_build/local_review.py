"""Candidate observations derived from the pinned snapshot for local use."""

import re
from pathlib import Path

from .storage import encode, read, write

MENTIONS = {
    "physical_damage": r"sát thương vật lý|\bstvl\b",
    "magic_damage": r"sát thương phép|\bstp\b",
    "true_damage": r"sát thương chuẩn|\bst chuẩn\b",
    "healing": r"hồi (?:lại |phục |thêm )?(?:\d[\d,.]*%? )?máu|hồi phục|trị liệu",
    "lifesteal": r"hút máu",
    "heal_reduction": r"giảm.{0,20}(?:hồi máu|hồi phục|trị liệu)",
    "cooldown": r"hồi chiêu|làm mới (?:kỹ năng|chiêu)|thời gian hồi",
    "stacks": r"cộng dồn|tích (?:lũy|điểm|trữ)",
    "armor_pen": r"xuyên giáp",
    "crit": r"chí mạng",
    "damage_reduction": r"miễn thương|giảm sát thương",
    "control": r"làm chậm|hất tung|hất văng|choáng|đẩy lùi|áp chế|câm lặng|miễn khống",
    "stealth": r"tàng hình|ẩn thân|lộ diện",
    "basic_attack": r"đánh thường|đòn đánh",
    "max_hp": r"máu tối đa",
    "missing_hp": r"máu (?:đã |bị )mất",
    "current_hp": r"máu hiện tại",
}
QUANTITY = re.compile(r"(?<![.\d])\d+(?:[.,]\d+)?\s*(?:%|giây\b|phút\b|giây/cấp|s\b)", re.I)
PATTERNS = {key: re.compile(pattern, re.I) for key, pattern in MENTIONS.items()}


def observe(text: str) -> dict:
    # Keep original scope because negative clauses and target conditions are meaningful.
    paragraphs = re.split(r"\n+", text.strip()) if text.strip() else []
    return {
        "paragraphs": [
            {
                "text": paragraph,
                "mentions": [
                    {"kind": kind, "span": list(match.span())}
                    for kind, pattern in PATTERNS.items()
                    for match in pattern.finditer(paragraph)
                ],
                "quantity_literals": [
                    match.group().strip() for match in QUANTITY.finditer(paragraph)
                ],
            }
            for paragraph in paragraphs
        ]
    }


def classify_item_effect(text: str) -> str:
    folded = text.casefold()
    if re.search(r"kích hoạt (?:chủ động|duy nhất)|chủ động sử dụng", folded):
        return "manual_candidate"
    if "nội tại" in folded:
        return "automatic_candidate"
    return "unknown"


def build_local_review(root: Path, manifest: dict, datasets: dict) -> dict:
    folder = root / ".local/review" / manifest["sha"]
    identity_map = {
        upstream: hero for hero, upstream in read(root / "sources/identity-map.json").items()
    }
    provenance = {
        "status": "UNVERIFIED",
        "evidence_layer": "community_or_unverified",
        "publication": "local_only",
    }
    heroes = datasets["heroes"]
    hero_ids = [identity_map.get(hero["slug"], hero["slug"]) for hero in heroes]
    if len(set(hero_ids)) != len(hero_ids) or any(
        not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", hero_id) for hero_id in hero_ids
    ):
        raise ValueError("Snapshot có ID tướng trùng hoặc không an toàn.")
    counts = {"heroes": len(heroes), "skills": 0, "base_stats": 0, "clauses": 0}
    for hero, hero_id in zip(heroes, hero_ids, strict=True):
        skills = []
        for skill in hero["skills"]:
            observations = observe(skill.get("description", ""))
            counts["clauses"] += len(observations["paragraphs"])
            skills.append({**skill, **observations})
        counts["skills"] += len(skills)
        counts["base_stats"] += len(hero["stats"])
        write(
            folder / "heroes" / f"{hero_id}.json",
            encode(
                {
                    **provenance,
                    "source": manifest["repository"],
                    "upstream_sha": manifest["sha"],
                    "hero": hero_id,
                    "roles": hero["classes"],
                    "lane": hero["lane"],
                    "base_stats": hero["stats"],
                    "sources": hero["sources"],
                    "skills": skills,
                    "balance_history": hero["balanceHistory"],
                }
            ),
        )
    clean = root / ".local/clean"
    items = []
    for item in read(clean / "items.json"):
        effects = [
            {"activation": classify_item_effect(text), **observe(text)} for text in item["passives"]
        ]
        items.append(item | {"observed_effects": effects})
    write(folder / "items.json", encode(provenance | {"entries": items}))
    for name in ("runes", "badges", "spells", "modes"):
        write(
            folder / f"{name}.json", encode(provenance | {"entries": read(clean / f"{name}.json")})
        )
    for name in ("items", "runes", "badges", "spells", "modes"):
        counts[name] = len(datasets[name])
    write(
        folder / "manifest.json",
        encode(provenance | {"upstream_sha": manifest["sha"], "counts": counts}),
    )
    return counts
