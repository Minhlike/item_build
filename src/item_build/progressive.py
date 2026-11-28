from pathlib import Path

from .catalog import defense_purchase_matrix, eligibility
from .storage import encode, read

DRAFT = "packs/l1"
THANE_SUPPORT_PACK = f"{DRAFT}/thane-support.json"
ICON_DOTS = {
    "xanh-ngoc": "🟢",
    "luc": "🟢",
    "lam": "🔵",
    "vang": "🟡",
    "cam": "🟠",
    "do": "🔴",
    "xam": "⚪",
}
ACADEMY_ITEM_DEFAULT = {
    "status": "UNVERIFIED",
    "evidence_layer": "official_undated_or_unresolved",
    "evidence": ["academy-items"],
}
COMMON_ITEM_GAPS = {
    "Màu icon",
    "Màu nhận diện icon",
    "Màu biểu tượng trong cửa hàng hiện hành",
    "Công thức ghép hiện hành",
    "Công thức ghép và giới hạn mua",
    "Đối chiếu cửa hàng trong game",
    "Đối chiếu số liệu trong cửa hàng phiên bản VN",
    "Giá vàng hiện hành",
    "Khả dụng cửa hàng và đường ghép hiện hành",
}


def official_icon(record: dict, evidence: dict) -> dict | None:
    images = {
        (claim["value"], ref)
        for claim in record["candidates"].get("identity.official-icon-color", [])
        for ref in claim["evidence"]
        if claim["evidence_layer"] != "conflict"
        and evidence[ref].source_type == "official"
        and evidence[ref].server == "VN"
        and evidence[ref].verification_status in {"verified_official", "cross_checked"}
    }
    if len({color for color, _ in images}) != 1:
        return None
    color, ref = min(images)
    if color not in ICON_DOTS:
        raise ValueError(f"Màu ảnh chưa có chấm tương ứng: {color}.")
    return {
        "color": color,
        "dot": ICON_DOTS[color],
        "scope": "official_artwork",
        "source": str(evidence[ref].source_url),
    }


def draft_entity(record: dict, *, exclude=()) -> dict:
    def relevant(prop):
        return prop not in exclude and (
            prop == "identity.icon-color"
            or not prop.startswith(("identity.", "stat.base.", "stat.growth."))
        )

    live = {}
    for prop, claim in record["live"].items():
        if not relevant(prop):
            continue
        value = claim["value"]
        terms = value.get("formula", {}).get("terms", []) if isinstance(value, dict) else []
        if any(term.get("multiply_by_target_max_hp") for term in terms):
            value = value | {
                "formula_basis": [
                    term["basis"]
                    + (" × target_max_hp" if term.get("multiply_by_target_max_hp") else "")
                    for term in terms
                ]
            }
        live[prop] = value
    candidates = {}
    for prop, claims in record["candidates"].items():
        if not relevant(prop):
            continue
        entries = [
            {
                field: claim[field]
                for field in ("value", "status", "evidence_layer", "evidence", "effective_from")
                if field in claim
            }
            for claim in claims
            if prop not in record["live"]
            or claim["value"] != record["live"][prop]["value"]
            or claim["evidence_layer"] == "conflict"
        ]
        if entries:
            candidates[prop] = entries
    review = [
        prop
        for prop in record["review_properties"]
        if prop not in candidates and prop not in live and prop != "identity.official-icon-color"
    ]
    return {
        "name": record["name"],
        "l2": record["canonical"].replace("knowledge/", "packs/", 1),
        "live": live,
        **({"candidates": candidates} if candidates else {}),
        **({"review": review} if review else {}),
        **({"unknown": record["unknown"]} if record["unknown"] else {}),
    }


def compile_draft(
    root: Path, packs: dict, paths: dict, tactics: dict, preferences: dict, release, evidence: dict
) -> dict:
    files = {}
    shortlists = read(root / "sources/draft-shortlists.json")
    if shortlists.keys() != paths["roles"].keys():
        raise ValueError("Cần danh sách trang bị draft cho mọi vai trò.")
    index = files[f"{DRAFT}/INDEX.json"] = {
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

    def item_draft(entry):
        art = official_icon(entry, evidence)
        return draft_entity(entry) | {
            "activation": entry["activation"],
            "shop_group": entry["shop_group"],
            **({"icon_reference": art} if art else {}),
        }

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
            choices[item_id] = item_draft(entry)
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
    if "thane/support" in preferences:
        index["thane_support"] = THANE_SUPPORT_PACK
        files[THANE_SUPPORT_PACK] = thane_support(
            packs, files, index, tactics, preferences["thane/support"], release, item_draft
        )
    return {path: encode(value, compact=True) for path, value in files.items()}


def thane_support(packs, files, index, tactics, preference, release, item_draft):
    all_items = {
        key.split("/")[1]: value for key, value in packs.items() if key.startswith("items/")
    }
    choices = {}
    components = {
        "bua-suc-manh",
        "dai-khang-phep",
        "day-chuyen-hong-ngoc",
        "gang-bach-kim",
        "gang-giac-dau",
        "giap-chan",
        "giap-hiep-si",
        "giap-nhe",
        "nhan-hong-ngoc",
        "tim-incubus",
        "giay-thep",
        "hoa-he-bao-thach",
        "nguyen-to-bao-thach",
        "tho-he-bao-thach",
    }
    for item_id, entry in all_items.items():
        if (
            entry["shop_group"] not in {"defense", "support", "boots"}
            and item_id != "chuy-bang-suong"
        ):
            continue
        decision = eligibility(item_id, entry, preference)
        if not decision.startswith("excluded"):
            if decision == "reviewable" and item_id in components:
                decision = "component"
            choices[item_id] = item_draft(entry) | {"eligibility": decision}
    # Recipe parts may live in another shop category or have their own recipes.
    pending_parts = list(choices.values())
    while pending_parts:
        entry = pending_parts.pop()
        for part in entry["live"].get("shop.recipe", []) + [
            part
            for claim in entry.get("candidates", {}).get("shop.recipe", [])
            for part in claim["value"]
        ]:
            part_id = part.split("/")[1]
            if part_id not in choices:
                choices[part_id] = item_draft(all_items[part_id]) | {"eligibility": "component"}
                pending_parts.append(choices[part_id])
    for entry in choices.values():
        # The same undated Academy citation applies to most shop properties.
        candidates = entry.get("candidates", {})
        academy = {}
        for prop, claims in list(candidates.items()):
            if len(claims) == 1 and all(
                field == "value" or ACADEMY_ITEM_DEFAULT.get(field) == value
                for field, value in claims[0].items()
            ):
                academy[prop] = candidates.pop(prop)[0]["value"]
        if academy:
            entry["academy_candidates"] = academy
        if not candidates:
            entry.pop("candidates", None)
        unknown = [gap for gap in entry.get("unknown", []) if gap not in COMMON_ITEM_GAPS]
        if unknown:
            entry["unknown"] = unknown
        else:
            entry.pop("unknown", None)
    support = files[f"{DRAFT}/roles/support.json"]
    return {
        "release": release.model_dump(mode="json"),
        "version_source": index["version"],
        "scope": tactics["scope"],
        "hero_lookup": index["heroes"],
        "hero_path": index["hero_path"],
        "player": files[f"{DRAFT}/heroes/thane.json"],
        "role_pack": {
            key: value
            for key, value in support.items()
            if key not in {"shortlist", "preferences", "macro_goals"}
        },
        "battlefield": files[f"{DRAFT}/battlefield.json"],
        "personal_preference": preference,
        "academy_candidate_defaults": ACADEMY_ITEM_DEFAULT,
        "shortlist": choices,
        "purchase_comparison": defense_purchase_matrix(choices),
        "macro_goals": [
            rule for rule in support["macro_goals"] if rule.get("hero", "thane") == "thane"
        ],
        "team_threats": tactics["team_threats"],
        "rules": [
            "Dùng purchase_comparison để so toàn lộ trình. Ở cùng ngân sách slot 3–4, thử đổi món hoặc đảo thứ tự, giữ phương án còn ổn định trước phép, vật lý/chuẩn và khống chế thực sự chạm ta hoặc chủ lực.",
            "So đợt dồn ngắn, đánh kéo dài và thời gian rút. Tách HP/giáp, chuẩn theo HP, lá chắn lúc kịp kích hoạt, hồi theo nhịp, giải khống và bảo kê. Ưu tiên sống sót sớm; bỏ phương án thua ở mọi tiêu chí đã biết, không cho điểm tùy ý.",
            "Hayate: Khiên thất truyền đáng so khi bị đánh thường, chưa biết số phi tiêu hoặc tốc đánh lấy ở mốc tung chiêu. Ra cần Hỏa diệm phủ đúng cửa sổ hồi của địch và đáng đánh đổi chỉ số. So Gaia/Troy với Khiên Thánh Quang nếu hai món vật lý làm hở sát thương phép.",
            "Chỉ cộng phần ghép có giá và công thức. Kiểm tra nội tại trùng, trần CDR và giá trị khi trận kết thúc sớm. Giữ ô thiếu là unknown; nếu thứ hạng đổi theo giả định, chốt một đường có điều kiện.",
            "live là LIVE_VN. academy_candidates kế thừa academy_candidate_defaults. Chỉ mở l2 nếu thiếu trường có thể đổi quyết định; L3 kiểm mâu thuẫn. Màu ưu tiên client có nguồn rồi ảnh Garena; thiếu dùng ⚪.",
            "Xuất đúng một build sáu món, chiến thuật mở bằng Mid đầu trận, tối đa 50 từ. Chỉ nêu giới hạn ảnh hưởng quyết định.",
        ],
    }


def draft_context(repo, hero: str, role: str | None, enemies: list[str], allies: list[str] | None):
    if hero == "thane" and role == "support" and "thane/support" in repo.preferences:
        shared = repo.read_file(THANE_SUPPORT_PACK)
        return {
            "layer": "L1",
            "patch": shared["release"]["patch_id"],
            "scope": shared["scope"],
            "hero": hero,
            "role": role,
            "enemies": enemies,
            **({"allies": allies} if allies is not None else {}),
            "heroes": {
                hero: shared["player"],
                **{
                    key: repo.read_file(shared["hero_path"].replace("<id>", key))
                    for key in dict.fromkeys([*enemies, *(allies or [])])
                    if key != hero
                },
            },
            **{
                key: shared[key]
                for key in (
                    "battlefield",
                    "role_pack",
                    "personal_preference",
                    "academy_candidate_defaults",
                    "shortlist",
                    "purchase_comparison",
                    "macro_goals",
                    "rules",
                )
            },
            "team_threats": [
                rule for rule in shared["team_threats"] if set(rule["enemies"]).issubset(enemies)
            ],
        }
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
