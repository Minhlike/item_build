import re
import unicodedata
from pathlib import Path

from pydantic import TypeAdapter
from rapidfuzz import fuzz, process

from .models import Basis, Formula, Nonnegative
from .storage import read

LANES = {"support", "mid", "jungle", "dragon", "slayer"}


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
        self.groups = read(root / "packs/INDEX.json")["groups"]
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
        if path not in self.cached:
            self.cached[path] = read(self.root / path)
            self.files_read += 1
        return self.cached[path]

    def context(self, hero: str, role: str | None, enemies: list[str], mode: str) -> dict:
        if role not in LANES | {None} or len(enemies) > 5:
            raise ValueError("Cần vị trí hợp lệ và tối đa năm tướng địch.")
        hero_id = self.identify(hero)
        enemy_ids = list(dict.fromkeys(self.identify(enemy) for enemy in enemies))
        team = [self.get(f"heroes/{entity_id}") for entity_id in enemy_ids]
        player = self.get(f"heroes/{hero_id}")
        role_pack = self.get(f"roles/{role or 'general'}")
        battlefield = self.get("battlefield/ranked-vn")
        related = {}
        for key in role_pack["live"].get("catalog.entries", {}).get("value", []):
            entry = self.get(key)
            if entry["live"]:
                related[key] = entry
        for pack in [player, *team, role_pack, battlefield]:
            for edge in pack["relations"]:
                for endpoint in (edge["subject"], edge["object"]):
                    key = endpoint.split("#", 1)[0]
                    if key.split("/")[0] in {"items", "runes", "enchantments", "spells"}:
                        item = self.get(key)
                        if item["live"]:
                            related[key] = item
        pack_list = [player, *team, role_pack, battlefield, *related.values()]
        references = {
            key
            for pack in pack_list
            for entry in [*pack["live"].values(), *pack["relations"]]
            for key in entry["evidence"]
        }
        references.update(key for pack in pack_list for key in pack["identity_sources"])
        evidence_path = "knowledge/sources/INDEX.json"
        if evidence_path not in self.cached:
            self.cached[evidence_path] = read(self.root / evidence_path)
            self.files_read += 1
        return {
            "version": self.version,
            "mode": mode,
            "queue": "ranked_solo_vn",
            "role": role,
            "hero": player,
            "enemies": team,
            "supplied_enemy_count": len(enemy_ids),
            "battlefield": battlefield,
            "tactical_role": role_pack,
            "related": related,
            "evidence": {key: self.cached[evidence_path][key] for key in sorted(references)},
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
