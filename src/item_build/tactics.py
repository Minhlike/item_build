from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field

from .models import Id, Model, Nonempty
from .storage import read

Lane = Literal["support", "mid", "jungle", "dragon", "slayer"]


class TeamThreat(Model):
    id: Id
    enemies: Annotated[list[Id], Field(min_length=2, max_length=5)]
    pattern: Literal["poke", "control", "burst", "cleanup", "reset"]
    condition: Nonempty
    chain: Nonempty
    response: Nonempty
    anchors: Annotated[list[Nonempty], Field(min_length=2)]


class MacroGoal(Model):
    id: Id
    roles: Annotated[list[Lane], Field(min_length=1)]
    hero: Id | None = None
    region: Literal["mid", "side-lane", "jungle", "river", "objective"]
    resource: Literal["gold", "experience", "wave", "turret", "buff", "boss"]
    tactic: Literal["engage", "peel", "pick", "counter-engage", "split-push", "retreat"]
    phase: Literal["early", "mid", "late"]
    condition: Nonempty
    action: Nonempty
    benefit: Nonempty
    risk: Nonempty
    anchors: Annotated[list[Nonempty], Field(min_length=1)]


class TacticalKnowledge(Model):
    team_threats: list[TeamThreat]
    macro_goals: list[MacroGoal]


def compile_tactics(root: Path, entities: dict, packs: dict) -> dict:
    source = TacticalKnowledge.model_validate(read(root / "sources/tactics.json"))
    rules = [*source.team_threats, *source.macro_goals]
    if len({rule.id for rule in rules}) != len(rules):
        raise ValueError("Mã chiến thuật phải duy nhất.")
    output = {"scope": "ranked_solo_vn", "team_threats": [], "macro_goals": []}
    for rule in rules:
        if isinstance(rule, TeamThreat):
            if len(set(rule.enemies)) != len(rule.enemies):
                raise ValueError(f"Trùng tướng trong {rule.id}.")
            for hero in rule.enemies:
                if not any(anchor.startswith(f"heroes/{hero}#") for anchor in rule.anchors):
                    raise ValueError(f"Thiếu cơ chế của {hero} trong {rule.id}.")
            group = "team_threats"
        else:
            if rule.hero and f"heroes/{rule.hero}" not in entities:
                raise ValueError(f"Tướng không hợp lệ trong {rule.id}.")
            group = "macro_goals"
        references = []
        for anchor in rule.anchors:
            entity, prop = anchor.split("#", 1)
            if prop not in entities[entity].facts:
                raise ValueError(f"Neo tri thức không hợp lệ: {anchor}.")
            references.append(packs[entity]["live"].get(prop))
        if all(references):
            output[group].append(
                rule.model_dump(exclude_none=True)
                | {
                    "kind": "tactical_heuristic",
                    "evidence": sorted({ev for fact in references for ev in fact["evidence"]}),
                }
            )
    return output


def select_tactics(pack: dict, hero: str, role: str | None, enemies: list[str]) -> dict:
    return {
        "scope": pack["scope"],
        "team_threats": [
            rule for rule in pack["team_threats"] if set(rule["enemies"]).issubset(enemies)
        ],
        "macro_goals": [
            rule
            for rule in pack["macro_goals"]
            if role in rule["roles"] and rule.get("hero", hero) == hero
        ],
    }
