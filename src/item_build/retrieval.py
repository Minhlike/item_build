import re
import unicodedata
from pathlib import Path

from pydantic import TypeAdapter
from rapidfuzz import fuzz, process

from .catalog import eligibility
from .models import Basis, Formula, Nonnegative
from .storage import read
from .tactics import select_tactics

LANES = {"support", "mid", "jungle", "dragon", "slayer"}
ROLE_GROUPS = {
    "support": ("defense", "support", "boots"),
    "mid": ("magic", "boots", "defense"),
    "jungle": ("jungle", "physical", "magic", "spells"),
    "dragon": ("physical", "boots", "defense"),
    "slayer": ("physical", "defense", "boots"),
    "general": ("defense", "physical", "magic", "support", "boots", "jungle"),
}


def normalize(name: str) -> str:
    folded = unicodedata.normalize("NFKD", name.casefold().replace("đ", "d"))
    ascii_letters = "".join(char for char in folded if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]+", "", ascii_letters)


class HeroLookupError(ValueError):
    pass


class Repository:
    def __init__(self, root: Path):
        self.root = root
        self.version = read(root / "knowledge/VERSION.json")
        index = read(root / "packs/INDEX.json")
        self.groups = index["groups"]
        self.catalogs = index["catalogs"]
        self.preferences = index["preferences"]
        self.tactics = index.get("tactics")
        aliases = {}
        for hero_id, (name, _, _, labels) in self.groups["heroes"].items():
            for label in (hero_id, name, *labels):
                aliases.setdefault(normalize(label), set()).add(hero_id)
        self.aliases = aliases
        self.cached = {}
        self.files_read = 2

    def identify(self, name: str) -> str:
        cleaned = normalize(name)
        if name in self.groups["heroes"] and name != "flowborn":
            return name
        exact = self.aliases.get(cleaned)
        if exact:
            if len(exact) == 1:
                return next(iter(exact))
            raise HeroLookupError(f"Tên {name!r} có nhiều bản: {', '.join(sorted(exact))}.")
        if len(cleaned) >= 4:
            matches = process.extract(
                cleaned, self.aliases.keys(), scorer=fuzz.ratio, limit=None, score_cutoff=75
            )
            scores = {}
            for alias, score, _ in matches:
                for hero_id in self.aliases[alias]:
                    scores.setdefault(hero_id, score)
            ranked = sorted(scores, key=scores.get, reverse=True)
            if (
                ranked
                and scores[ranked[0]] >= 82
                and (len(ranked) == 1 or scores[ranked[0]] - scores[ranked[1]] >= 8)
            ):
                return ranked[0]
            if ranked:
                raise HeroLookupError(f"Tên {name!r} chưa rõ: {', '.join(ranked[:3])}.")
        raise HeroLookupError(f"Không tìm thấy tướng {name!r}.")

    def get(self, key: str, *, canonical: bool = False) -> dict:
        group, entity_id = key.split("/", 1)
        path = self.groups[group][entity_id][2 if canonical else 1]
        return self.read_file(path)

    def read_file(self, path: str) -> dict:
        if path not in self.cached:
            self.cached[path] = read(self.root / path)
            self.files_read += 1
        return self.cached[path]

    def context(
        self,
        hero: str,
        role: str | None,
        enemies: list[str],
        mode: str,
        *,
        include_candidates: bool = False,
        include_reasoning: bool = False,
        allies: list[str] | None = None,
    ) -> dict:
        if role not in LANES | {None} or len(enemies) > 5 or len(allies or []) > 4:
            raise ValueError("Cần vị trí hợp lệ, tối đa năm tướng địch và bốn đồng minh.")
        hero_id = self.identify(hero)
        enemy_ids = list(dict.fromkeys(self.identify(enemy) for enemy in enemies))
        ally_ids = list(dict.fromkeys(self.identify(ally) for ally in allies or []))

        def match_pack(key: str) -> dict:
            pack = self.get(key)
            return (
                pack
                if include_candidates
                else {
                    k: v for k, v in pack.items() if k not in {"candidates", "candidate_relations"}
                }
            )

        team = [match_pack(f"heroes/{entity_id}") for entity_id in enemy_ids]
        ally_packs = [match_pack(f"heroes/{entity_id}") for entity_id in ally_ids]
        player = match_pack(f"heroes/{hero_id}")
        role_pack = self.get(f"roles/{role or 'general'}")
        battlefield = match_pack("battlefield/ranked-vn")
        preference_path = self.preferences.get(f"{hero_id}/{role}")
        preference = self.read_file(preference_path) if preference_path else None
        groups = list(ROLE_GROUPS[role or "general"])
        if mode == "hero_preparation" and include_candidates:
            groups.extend(("runes", "enchantments", "spells"))
        groups = list(dict.fromkeys(groups))
        related = {}
        candidate_reviews = {}
        for group in groups:
            path = self.catalogs.get(group)
            if path is None:
                continue
            for item_id, entry in self.read_file(path)["entries"].items():
                is_item = "shop_group" in entry
                key = f"{'items' if is_item else group}/{item_id}"
                choice = eligibility(item_id, entry, preference) if is_item else "reviewable"
                canonical = self.groups[key.split("/")[0]][item_id][2]
                if include_candidates and (entry["candidates"] or choice.startswith("excluded")):
                    candidate_reviews[key] = {
                        **entry,
                        "eligibility": choice,
                        "canonical": canonical,
                    }
                if entry["live"] and choice in {"no_personal_filter", "reviewable"}:
                    related[key] = {
                        "id": item_id,
                        "canonical": canonical,
                        "identity_sources": [],
                        "review_properties": sorted(entry["candidates"]),
                        "relations": [],
                        "review_relations": [],
                        "unknown": [],
                        **{
                            k: v
                            for k, v in entry.items()
                            if k not in {"candidates", "candidate_relations"}
                        },
                    }
        pack_list = [
            player,
            *team,
            *ally_packs,
            role_pack,
            battlefield,
            *related.values(),
            *candidate_reviews.values(),
        ]
        references = {key for pack in pack_list for key in pack.get("identity_sources", [])}
        for pack in pack_list:
            claims = [
                *pack["live"].values(),
                *pack.get("relations", []),
                *pack.get("candidate_relations", []),
            ]
            claims.extend(fact for facts in pack.get("candidates", {}).values() for fact in facts)
            references.update(key for fact in claims for key in fact["evidence"])
        tactics = None
        if include_reasoning and self.tactics:
            tactics = select_tactics(self.read_file(self.tactics), hero_id, role, enemy_ids)
            for rule in tactics["team_threats"] + tactics["macro_goals"]:
                references.update(rule["evidence"])
        evidence_path = "knowledge/sources/INDEX.json"
        sources = self.read_file(evidence_path)
        return {
            "version": self.version,
            "mode": mode,
            "queue": "ranked_solo_vn",
            "role": role,
            "hero": player,
            "enemies": team,
            "supplied_enemy_count": len(enemy_ids),
            **({"allies": ally_packs} if allies is not None else {}),
            "battlefield": battlefield,
            "tactical_role": role_pack,
            "related": related,
            "catalog_paths": self.catalogs,
            "personal_preference": preference,
            **({"tactics": tactics} if tactics is not None else {}),
            **({"candidate_reviews": candidate_reviews} if include_candidates else {}),
            "evidence": {key: sources[key] for key in sorted(references)},
        }

    def formula(self, key: str, prop: str, raw_inputs: dict[str, float]):
        fact = self.get(key)["live"].get(prop)
        value = fact["value"] if fact else None
        if not isinstance(value, dict) or "formula" not in value:
            raise ValueError("Thuộc tính thiếu công thức đã xác minh cho phiên bản.")
        formula = Formula.model_validate(value["formula"])
        inputs = TypeAdapter(dict[Basis, Nonnegative]).validate_python(raw_inputs)
        return {
            "value": formula.calculate(inputs),
            "unit": formula.unit.value,
            "trigger": value["trigger"],
            "evidence": fact["evidence"],
        }

    def cooldown(
        self,
        key: str,
        prop: str,
        raw_inputs: dict[str, float],
        reduction: float | None,
        cap: float | None,
    ):
        fact = self.get(key)["live"].get(prop)
        if fact is None:
            raise ValueError("Thuộc tính hồi chiêu chưa được xác minh cho phiên bản.")
        value = fact["value"]
        cooldown = value.get("timing", {}).get("cooldown_s") if isinstance(value, dict) else None
        inputs = TypeAdapter(dict[Basis, Nonnegative]).validate_python(raw_inputs)
        if isinstance(cooldown, dict):
            seconds = Formula.model_validate(cooldown).calculate(inputs)
        elif isinstance(cooldown, list):
            rank = inputs.get(Basis.SKILL_RANK, 0.0)
            if not rank.is_integer() or not 1 <= rank <= len(cooldown):
                raise ValueError("Cần cấp chiêu hợp lệ cho bảng hồi chiêu.")
            seconds = cooldown[int(rank) - 1]
        elif isinstance(cooldown, (int, float)):
            seconds = cooldown
        else:
            raise ValueError("Thuộc tính không có giá trị hồi chiêu cơ bản.")
        if reduction is None and cap is None:
            return {"base_seconds": seconds, "evidence": fact["evidence"]}
        if reduction is None or cap is None or not (0 <= reduction <= 1 and 0 <= cap <= 1):
            raise ValueError("Cần cả giảm hồi chiêu và giới hạn trong khoảng [0, 1].")
        return {
            "base_seconds": seconds,
            "seconds": seconds * (1 - min(reduction, cap)),
            "model": "standard_capped_cdr_scenario",
            "scenario_inputs": {"reduction": reduction, "cap": cap},
            "evidence": fact["evidence"],
        }
