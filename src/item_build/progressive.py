from pathlib import Path

from .catalog import eligibility
from .storage import encode, read

DRAFT = "packs/l1"


def draft_entity(record: dict, *, exclude=()) -> dict:
    live = {}
    for prop, claim in record["live"].items():
        if prop in exclude or prop.startswith(("identity.", "stat.base.", "stat.growth.")):
            continue
        value = claim["value"]
        if isinstance(value, dict) and "formula" in value:
            # Keep the typed basis and full trigger. Numerical evaluation expands this property.
            formula = value["formula"]
            value = {key: val for key, val in value.items() if key != "formula"} | {
                "formula_basis": [
                    term["basis"]
                    + (" × target_max_hp" if term.get("multiply_by_target_max_hp") else "")
                    for term in formula.get("terms", [])
                ]
            }
        live[prop] = value
    return {
        "name": record["name"],
        "l2": record["canonical"].replace("knowledge/", "packs/", 1),
        "live": live,
        **({"review": record["review_properties"]} if record["review_properties"] else {}),
        **({"unknown": record["unknown"]} if record["unknown"] else {}),
    }


def compile_draft(root: Path, packs: dict, paths: dict, tactics: dict, preferences: dict) -> dict:
    files = {}
    shortlists = read(root / "sources/draft-shortlists.json")
    if shortlists.keys() != paths["roles"].keys():
        raise ValueError("Cần danh sách trang bị draft cho mọi vai trò.")
    files[f"{DRAFT}/INDEX.json"] = {
        "heroes": {key: [name, *aliases] for key, (name, _, _, aliases) in paths["heroes"].items()},
        "hero_path": f"{DRAFT}/heroes/<id>.json",
        "role_path": f"{DRAFT}/roles/<role>.json",
        "battlefield": f"{DRAFT}/battlefield.json",
        "team_threats": {rule["id"]: rule["enemies"] for rule in tactics["team_threats"]},
        "team_path": f"{DRAFT}/team/<rule-id>.json",
        "version": "knowledge/VERSION.json",
        "evidence": "knowledge/sources/INDEX.json",
    }
    for key, pack in packs.items():
        if key.startswith("heroes/"):
            files[f"{DRAFT}/{key}.json"] = draft_entity(pack)
    battlefield = packs["battlefield/ranked-vn"]
    core = ("items.", "support.", "draft.", "tactics.", "jungle.early-")
    files[f"{DRAFT}/battlefield.json"] = draft_entity(
        battlefield, exclude={prop for prop in battlefield["live"] if not prop.startswith(core)}
    )
    for role, ids in shortlists.items():
        if len(set(ids)) != len(ids):
            raise ValueError(f"Danh sách trang bị draft trùng ID ở {role}.")
        role_preferences = {
            key.split("/")[0]: preference
            for key, preference in preferences.items()
            if key.endswith(f"/{role}")
        }
        choices = {}
        for item_id in ids:
            entry = packs[f"items/{item_id}"]
            choices[item_id] = draft_entity(entry) | {
                "activation": entry["activation"],
                "shop_group": entry["shop_group"],
            }
            if role_preferences:
                choices[item_id]["personal_filter"] = {
                    hero: eligibility(item_id, entry, pref)
                    for hero, pref in role_preferences.items()
                }
        files[f"{DRAFT}/roles/{role}.json"] = draft_entity(packs[f"roles/{role}"]) | {
            "shortlist": choices,
            "preferences": role_preferences,
            "macro_goals": [rule for rule in tactics["macro_goals"] if role in rule["roles"]],
        }
    for rule in tactics["team_threats"]:
        files[f"{DRAFT}/team/{rule['id']}.json"] = rule
    return {path: encode(value, compact=True) for path, value in files.items()}


def draft_context(repo, hero: str, role: str | None, enemies: list[str], allies: list[str] | None):
    index = repo.read_file(f"{DRAFT}/INDEX.json")
    battlefield = repo.read_file(index["battlefield"])
    role_data = repo.read_file(index["role_path"].replace("<role>", role or "general"))
    selected = {
        key: {prop: value for prop, value in entry.items() if prop != "personal_filter"}
        | {"eligibility": entry.get("personal_filter", {}).get(hero, "no_personal_filter")}
        for key, entry in role_data["shortlist"].items()
    }
    roster = {
        key: repo.read_file(index["hero_path"].replace("<id>", key))
        for key in dict.fromkeys([hero, *enemies, *(allies or [])])
    }
    return {
        "layer": "L1",
        "patch": repo.version["patch_id"],
        "scope": "ranked_solo_vn",
        "hero": hero,
        "role": role,
        "enemies": enemies,
        **({"allies": allies} if allies is not None else {}),
        "heroes": roster,
        "battlefield": battlefield,
        "role_pack": {
            key: value
            for key, value in role_data.items()
            if key not in {"shortlist", "preferences", "macro_goals"}
        },
        "personal_preference": role_data["preferences"].get(hero),
        "shortlist": selected,
        "macro_goals": [
            rule for rule in role_data["macro_goals"] if rule.get("hero", hero) == hero
        ],
        "team_threats": [
            repo.read_file(index["team_path"].replace("<rule-id>", key))
            for key, members in index["team_threats"].items()
            if set(members).issubset(enemies)
        ],
    }
