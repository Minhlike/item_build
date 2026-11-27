from collections import Counter, defaultdict
from datetime import date
from graphlib import TopologicalSorter
from pathlib import Path
from urllib.parse import urlsplit

from pydantic import TypeAdapter

from .catalog import activation_review, candidate_layer, group_packs, load_preferences
from .models import (
    CanonicalEntity,
    Entity,
    Evidence,
    Fact,
    Mechanic,
    Patch,
    Relation,
    Release,
    Status,
)
from .storage import encode, read, write
from .tactics import compile_tactics

GROUPS = ("heroes", "items", "runes", "enchantments", "spells", "battlefield", "roles")
SCHEMA_VERSION = 2


def payload(model):
    return model.model_dump(mode="json", exclude_none=True, exclude_defaults=True)


def load_inputs(root: Path):
    registry = read(root / "knowledge/sources/registry.json")["sources"]
    evidence = TypeAdapter(dict[str, Evidence]).validate_python(
        read(root / "sources/evidence.json")
    )
    for key, reference in evidence.items():
        source = registry[reference.source_id]
        if source["redistribution"] not in {"independent_facts_only", "approved_facts"}:
            raise ValueError(f"Nguồn {reference.source_id} chưa có quyền công bố tri thức.")
        origin = urlsplit(source["url"] or str(reference.source_url))
        if source["type"] != reference.source_type or source["server"] != reference.server:
            raise ValueError(f"Metadata nguồn không khớp: {key}.")
        if origin.hostname != reference.source_url.host:
            raise ValueError(f"URL bằng chứng ngoài phạm vi nguồn: {key}.")

    roster = read(root / "sources/roster.json")
    entities = {}
    for hero_id, name in roster["heroes"].items():
        hero = Entity.model_validate(
            {
                "id": hero_id,
                "kind": "heroes",
                "name": name,
                "facts": {"identity.roster": [{"value": True, "evidence": [roster["evidence"]]}]},
                "unknown": [
                    "Chỉ số gốc",
                    "Bộ chiêu đầy đủ và biến thể",
                    "Hồi chiêu theo cấp",
                    "Tương tác và ngưỡng sức mạnh",
                ],
            }
        )
        entities[f"heroes/{hero.id}"] = hero
    seen = set()
    for path in sorted((root / "sources/entities").glob("*.json")):
        for entity in TypeAdapter(list[Entity]).validate_python(read(path)):
            key = f"{entity.kind}/{entity.id}"
            if key in seen:
                raise ValueError(f"Trùng ID {key}.")
            seen.add(key)
            if entity.kind == "heroes":
                base = entities[key]
                if entity.name != base.name or base.facts.keys() & entity.facts.keys():
                    raise ValueError(f"Hồ sơ trùng thuộc tính gốc hoặc sai tên: {key}.")
                entity.facts = {**base.facts, **entity.facts}
            entities[key] = entity

    patch_files = sorted((root / "patches").glob("*.json"))
    override_files = sorted((root / "overrides").glob("*.json"))
    patches = [Patch.model_validate(read(path)) for path in patch_files]
    overrides = [Patch.model_validate(read(path)) for path in override_files]
    patch_map = {patch.id: patch for patch in patches}
    if len(patch_map) != len(patches) or len({p.id for p in patches + overrides}) != len(
        patches + overrides
    ):
        raise ValueError("Mã patch hoặc override trùng nhau.")
    release = Release.model_validate(read(root / "sources/release.json"))
    live_patch = patch_map[release.patch_id]
    if (
        live_patch.status != Status.LIVE_VN
        or live_patch.server != "VN"
        or live_patch.effective_from > release.as_of
    ):
        raise ValueError("Mốc phát hành không phù hợp với bản VN.")
    if any(
        patch.status == Status.LIVE_VN
        and live_patch.effective_from < patch.effective_from <= release.as_of
        for patch in patches
    ):
        raise ValueError("Mốc phát hành bỏ qua patch VN mới hơn.")

    override_ids = {patch.id for patch in overrides}
    for patch in sorted(
        patches + overrides,
        key=lambda patch: (patch.effective_from, patch.id in override_ids, patch.id),
    ):
        source = evidence[patch.evidence]
        if patch.server != source.server:
            raise ValueError(f"Patch {patch.id} sai máy chủ so với nguồn.")
        if patch.status == Status.LIVE_VN and (
            patch.server != "VN"
            or source.effective_from is None
            or source.effective_from > patch.effective_from
        ):
            raise ValueError(f"Patch {patch.id} thiếu ngày hiệu lực VN có bằng chứng.")
        fields = set()
        for change in patch.changes:
            key = (change.entity, change.property)
            if key in fields:
                raise ValueError(f"Patch {patch.id} sửa một thuộc tính nhiều lần.")
            fields.add(key)
            apply_change(entities[change.entity], patch, change)

    relations = TypeAdapter(list[Relation]).validate_python(read(root / "sources/relations.json"))
    return entities, evidence, relations, release, live_patch


def apply_change(entity, patch, change):
    new = change.replacement
    if new.status != patch.status or new.effective_from != patch.effective_from:
        raise ValueError(f"Ngày hoặc trạng thái của thay đổi {patch.id} không khớp patch.")
    timeline = entity.facts.setdefault(change.property, [])
    if patch.status != Status.LIVE_VN:
        if change.previous:
            raise ValueError(f"Patch {patch.id} chưa đủ điều kiện sửa lịch sử VN.")
        timeline.append(new)
        return

    old = next((fact for fact in timeline if fact.live_at(patch.effective_from)), None)
    if old and change.previous:
        if old.value != change.previous.value:
            raise ValueError(f"Giá trị trước của {patch.id} không khớp lịch sử {change.property}.")
    if old:
        if old.effective_from == new.effective_from:
            raise ValueError(f"Hai thay đổi cùng ngày cho {change.property}. Sửa bản ghi gốc.")
        index = timeline.index(old)
        timeline[index] = Fact.model_validate(
            {**old.model_dump(), "status": Status.SUPERSEDED, "effective_until": new.effective_from}
        )
    elif change.previous:
        if (
            change.previous.status != Status.SUPERSEDED
            or change.previous.effective_until != new.effective_from
        ):
            raise ValueError(f"Lịch sử trước {patch.id} không có mốc kết thúc hợp lệ.")
        timeline.append(change.previous)
    timeline.append(new)


def validate_claim(claim, evidence: dict[str, Evidence]) -> None:
    refs = [evidence[key] for key in claim.evidence]
    if claim.status == Status.LIVE_VN and not any(
        ref.server == "VN"
        and ref.verification_status in {"verified_official", "cross_checked", "experiment"}
        and ref.effective_from is not None
        and ref.effective_from <= claim.effective_from
        and (
            ref.effective_until is None
            or (claim.effective_until is not None and claim.effective_until <= ref.effective_until)
        )
        for ref in refs
    ):
        raise ValueError(f"Thuộc tính LIVE_VN thiếu bằng chứng VN còn hiệu lực: {claim.evidence}.")


def owning_entity(node: str) -> str:
    return node.split("#", 1)[0]


def validate_graph(entities, evidence, relations) -> None:
    for key, entity in entities.items():
        for prop, timeline in entity.facts.items():
            if not timeline:
                raise ValueError(f"Thuộc tính trống: {key}#{prop}.")
            for fact in timeline:
                validate_claim(fact, evidence)
                if (
                    entity.kind == "items"
                    and isinstance(fact.value, Mechanic)
                    and fact.value.activation is None
                ):
                    raise ValueError(f"Cơ chế trang bị thiếu loại kích hoạt: {key}#{prop}.")
                if prop == "catalog.entries" and (
                    not isinstance(fact.value, list)
                    or any(entry not in entities for entry in fact.value)
                ):
                    raise ValueError(f"Danh mục {key} chứa đích không hợp lệ.")
                if prop == "shop.recipe" and (
                    entity.kind != "items"
                    or not isinstance(fact.value, list)
                    or not fact.value
                    or any(
                        part == key or not part.startswith("items/") or part not in entities
                        for part in fact.value
                    )
                ):
                    raise ValueError(f"Công thức của {key} thiếu thành phần hợp lệ.")
            dated = sorted(
                (
                    fact
                    for fact in timeline
                    if fact.status in {Status.LIVE_VN, Status.SUPERSEDED} and fact.effective_from
                ),
                key=lambda fact: fact.effective_from,
            )
            if any(
                (left.effective_until or date.max) > right.effective_from
                for left, right in zip(dated, dated[1:], strict=False)
            ):
                raise ValueError(f"Phiên bản chồng lấn: {key}#{prop}.")
    ids = set()
    for relation in relations:
        if relation.id in ids:
            raise ValueError(f"Trùng ID quan hệ: {relation.id}.")
        ids.add(relation.id)
        validate_claim(relation, evidence)
        for endpoint in (relation.subject, relation.object):
            key, _, prop = endpoint.partition("#")
            entity = entities[key]
            if prop and prop not in entity.facts:
                raise ValueError(f"Quan hệ trỏ tới thuộc tính không tồn tại: {endpoint}.")


def active(fact: Fact, day: date) -> bool:
    return fact.live_at(day) or (
        fact.status == Status.SUPERSEDED
        and fact.effective_from is not None
        and fact.effective_from <= day < fact.effective_until
    )


def relation_is_live(relation, entities, day):
    if not relation.live_at(day):
        return False
    for node in (relation.subject, relation.object):
        key, _, prop = node.partition("#")
        if prop and not any(
            active(fact, day) and fact.effective_from <= relation.effective_from
            for fact in entities[key].facts[prop]
        ):
            return False
    return True


def artifacts(root: Path) -> dict[str, bytes]:
    entities, evidence, relations, release, patch = load_inputs(root)
    validate_graph(entities, evidence, relations)
    day = release.as_of
    recipes = {
        key: fact.value
        for key, entity in entities.items()
        for fact in entity.facts.get("shop.recipe", [])
        if active(fact, day)
    }
    tuple(TopologicalSorter(recipes).static_order())
    files = {}
    packed = {}
    paths = {group: {} for group in GROUPS}
    coverage = {group: Counter() for group in GROUPS}
    edges = defaultdict(list)
    for relation in relations:
        for key in {owning_entity(relation.subject), owning_entity(relation.object)}:
            edges[key].append(relation)
    for key, entity in sorted(entities.items()):
        canonical = f"knowledge/{key}.json"
        pack = f"packs/{key}.json"
        live = {}
        review = {}
        for prop, timeline in entity.facts.items():
            for fact in timeline:
                if active(fact, day):
                    if fact.status == Status.SUPERSEDED:
                        fact = fact.model_copy(update={"status": Status.LIVE_VN})
                    live[prop] = payload(fact) | {"status": fact.status.value}
                elif fact.status == Status.UNVERIFIED and prop != "identity.roster":
                    review.setdefault(prop, []).append(
                        payload(fact)
                        | {
                            "status": fact.status.value,
                            "evidence_layer": candidate_layer(fact, evidence),
                        }
                    )

        live_relations = [
            payload(edge) for edge in edges[key] if relation_is_live(edge, entities, day)
        ]
        candidate_relations = [
            payload(edge)
            | {"status": edge.status.value, "evidence_layer": candidate_layer(edge, evidence)}
            for edge in edges[key]
            if edge.status == Status.UNVERIFIED
        ]
        counts = coverage[entity.kind]
        counts["entities"] += 1
        counts["entities_with_live_facts"] += bool(live)
        counts["live_properties"] += len(live)
        counts["review_claims"] += sum(map(len, review.values()))
        counts["live_mechanics"] += sum(
            "effect" in fact["value"] for fact in live.values() if isinstance(fact["value"], dict)
        )
        counts["mechanical_properties_any"] += sum(
            any(isinstance(fact.value, Mechanic) for fact in timeline)
            for timeline in entity.facts.values()
        )
        files[canonical] = encode(
            payload(entity) | {"relations": [payload(edge) for edge in edges[key]]}
        )
        record = {
            "id": entity.id,
            "name": entity.name,
            "canonical": canonical,
            "identity_sources": [
                ref for fact in entity.facts.get("identity.roster", []) for ref in fact.evidence
            ],
            "live": live,
            "review_properties": sorted(review),
            "review_relations": [
                edge.id for edge in edges[key] if not relation_is_live(edge, entities, day)
            ],
            "unknown": entity.unknown,
            "relations": live_relations,
        }
        if review:
            record["candidates"] = review
        if candidate_relations:
            record["candidate_relations"] = candidate_relations
        if entity.shop_group:
            record["shop_group"] = entity.shop_group
            record["activation"] = activation_review(record | {"candidates": review})
        packed[key] = record | {"candidates": review}
        files[pack] = encode(record, compact=True)
        paths[entity.kind][entity.id] = [entity.name, pack, canonical, entity.aliases]
    catalog_paths = {}
    for group, entries in group_packs(packed).items():
        path = f"packs/catalogs/{group}.json"
        files[path] = encode({"group": group, "entries": entries}, compact=True)
        catalog_paths[group] = path
    preferences = load_preferences(root, entities)
    preference_paths = {}
    for key, preference in preferences.items():
        path = f"packs/preferences/{key.replace('/', '-')}.json"
        files[path] = encode(preference, compact=True)
        preference_paths[key] = path
    tactics_path = "packs/tactics.json"
    files[tactics_path] = encode(compile_tactics(root, entities, packed), compact=True)
    files["packs/INDEX.json"] = encode(
        {
            "schema": SCHEMA_VERSION,
            "version": "knowledge/VERSION.json",
            "groups": paths,
            "entry_fields": ["name", "pack", "canonical", "aliases"],
            "evidence": "knowledge/sources/INDEX.json",
            "roles": "packs/roles/",
            "catalogs": catalog_paths,
            "preferences": preference_paths,
            "tactics": tactics_path,
        },
        compact=True,
    )
    files["knowledge/INDEX.json"] = encode(
        {
            "packs": "packs/INDEX.json",
            "version": "knowledge/VERSION.json",
            "sources": "knowledge/sources/INDEX.json",
            "graph": "knowledge/interactions/graph.json",
            "schema": "schemas/entity.schema.json",
            "directories": {group: f"knowledge/{group}/" for group in GROUPS},
        }
    )
    files["knowledge/VERSION.json"] = encode(
        {
            **payload(release),
            "patch_title": patch.title,
            "server": "VN",
            "patch_source": str(evidence[patch.evidence].source_url),
            "effective_from": patch.effective_from.isoformat(),
            "schema": SCHEMA_VERSION,
            "coverage": {group: dict(counts) for group, counts in coverage.items()},
        }
    )
    files["knowledge/sources/INDEX.json"] = encode(
        {key: model.model_dump(mode="json") for key, model in evidence.items()}, compact=True
    )
    files["knowledge/interactions/graph.json"] = encode([payload(edge) for edge in relations])
    for name, model in {
        "entity": CanonicalEntity,
        "patch": Patch,
        "evidence": Evidence,
        "relation": Relation,
    }.items():
        files[f"schemas/{name}.schema.json"] = encode(model.model_json_schema())
    return files


def compile_repo(root: Path, *, check: bool = False) -> dict:
    files = artifacts(root)
    outdated = [
        name
        for name, raw in files.items()
        if not (root / name).exists() or (root / name).read_bytes() != raw
    ]
    obsolete = [
        str(path.relative_to(root).as_posix())
        for group in GROUPS
        for base in ("knowledge", "packs")
        for path in (root / base / group).glob("*.json")
        if path.relative_to(root).as_posix() not in files
    ]
    obsolete.extend(
        path.relative_to(root).as_posix()
        for directory in ("packs/catalogs", "packs/preferences")
        for path in (root / directory).glob("*.json")
        if path.relative_to(root).as_posix() not in files
    )
    if check and (outdated or obsolete):
        raise ValueError(
            f"Tệp biên dịch lệch nguồn ({len(outdated)} cũ, {len(obsolete)} thừa): {(outdated + obsolete)[:8]}."
        )
    for name in outdated:
        write(root / name, files[name])
    for name in obsolete:
        (root / name).unlink()
    return {"files": len(files), "changed": len(outdated), "removed": len(obsolete)}
