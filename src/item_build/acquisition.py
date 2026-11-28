import hashlib
import json
import re
import subprocess
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser

import httpx

from .storage import encode, read, write

DATASETS = ("heroes", "items", "runes", "badges", "spells", "modes", "name-aliases", "crawl-info")
HERO_FIELDS = ("slug", "name", "classes", "lane", "stats", "balanceHistory", "sources")
USER_AGENT = "ItemBuildEvidenceMonitor/0.1"
MAX_RESPONSE = 2_000_000


def git(path: Path, *args: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(path), *args])


def snap(root: Path) -> tuple[dict, dict]:
    pin = read(root / "sources/upstream.json")
    if not re.fullmatch(r"[a-f0-9]{40}", pin["sha"]):
        raise ValueError("Upstream phải được pin bằng SHA đầy đủ.")
    checkout = root / ".local/upstream"
    if not (checkout / ".git").exists():
        checkout.mkdir(parents=True, exist_ok=True)
        git(checkout, "init", "-q")
    try:
        git(checkout, "cat-file", "-e", f"{pin['sha']}^{{commit}}")
    except subprocess.CalledProcessError:
        git(checkout, "fetch", "--depth=1", pin["repository"], pin["sha"])

    manifest_file = root / ".local/raw" / pin["sha"] / "manifest.json"
    previous = read(manifest_file) if manifest_file.exists() else {}
    manifest = {
        **pin,
        "source_committed_at": git(checkout, "show", "-s", "--format=%cI", pin["sha"])
        .decode()
        .strip(),
        "retrieved_at": previous.get("retrieved_at", datetime.now(UTC).isoformat()),
        "files": {},
    }
    datasets = {}
    for name in DATASETS:
        relative = f"data/{name}.json"
        content = git(checkout, "show", f"{pin['sha']}:{relative}")
        manifest["files"][relative] = {
            "sha256": hashlib.sha256(content).hexdigest(),
            "bytes": len(content),
        }
        datasets[name] = json.loads(content)
        write(manifest_file.parent / relative, content)
    write(manifest_file, encode(manifest))
    return manifest, datasets


def clean_for_review(root: Path, datasets: dict) -> None:
    heroes = []
    for hero in datasets["heroes"]:
        record = {key: hero[key] for key in HERO_FIELDS if key in hero}
        record["skills"] = [
            {key: value for key, value in skill.items() if key != "icon"}
            for skill in hero["skills"]
        ]
        heroes.append(record)
    write(root / ".local/clean/heroes.json", encode(heroes))

    def remove_media(value):
        if isinstance(value, dict):
            return {
                key: remove_media(inner)
                for key, inner in value.items()
                if key not in {"icon", "image", "background", "backgroundMobile", "searchKey"}
            }
        if isinstance(value, list):
            return [remove_media(inner) for inner in value]
        return value

    for name in ("items", "runes", "badges", "spells", "modes", "name-aliases"):
        write(root / f".local/clean/{name}.json", encode(remove_media(datasets[name])))


def audit(root: Path, manifest: dict, data: dict) -> dict:
    heroes = data["heroes"]
    skills = [(hero, skill) for hero in heroes for skill in hero["skills"]]
    duplicate_ids = {}
    for name in DATASETS:
        if isinstance(data[name], list):
            ids = Counter(record.get("slug") for record in data[name])
            duplicate_ids[name] = sorted(key for key, count in ids.items() if count > 1)
    roster = read(root / "sources/roster.json")
    upstream_by_id = {
        upstream: canonical
        for canonical, upstream in read(root / "sources/identity-map.json").items()
    }
    upstream_ids = {upstream_by_id.get(hero["slug"], hero["slug"]) for hero in heroes}
    report = {
        "snapshot": {key: value for key, value in manifest.items() if key != "retrieved_at"},
        "counts": {name: len(data[name]) for name in DATASETS},
        "duplicate_ids": duplicate_ids,
        "hero_coverage": {
            "base_stats_any": sum(bool(hero["stats"]) for hero in heroes),
            "base_stats_by_key": dict(
                sorted(Counter(stat["id"] for hero in heroes for stat in hero["stats"]).items())
            ),
            "base_stats_thane": len(
                next(hero["stats"] for hero in heroes if hero["slug"] == "thane")
            ),
            "balance_history_any": sum(bool(hero["balanceHistory"]) for hero in heroes),
            "source_by_key": dict(
                sorted(
                    Counter(
                        key for hero in heroes for key, value in hero["sources"].items() if value
                    ).items()
                )
            ),
            "skills": len(skills),
            "slots": dict(sorted(Counter(skill["slot"] for _, skill in skills).items())),
            "descriptions": sum(bool(skill.get("description", "").strip()) for _, skill in skills),
            "explicit_cooldown_fields": sum("cooldown" in skill for _, skill in skills),
            "true_damage_text_single_type_label": sorted(
                {
                    hero["slug"]
                    for hero, skill in skills
                    if "sát thương chuẩn" in skill["description"].casefold()
                    and hero.get("damageType") in {"Vật lý", "Phép"}
                }
            ),
            "identity_reconciliations": upstream_by_id,
            "only_upstream": sorted(upstream_ids - roster["heroes"].keys()),
            "only_official_roster": sorted(roster["heroes"].keys() - upstream_ids),
        },
        "item_coverage": {
            "stats_any": sum(bool(item["stats"]) for item in data["items"]),
            "passives_any": sum(bool(item["passives"]) for item in data["items"]),
            "recipes_explicit": sum(
                "recipe" in item or "components" in item for item in data["items"]
            ),
            "khiên_thánh_quang": any(item["slug"] == "khien-thanh-quang" for item in data["items"]),
        },
        "runes_with_stats": sum(bool(rune["stats"]) for rune in data["runes"]),
        "enchantment_nodes": sum(
            len(group["skills"]) for branch in data["badges"] for group in branch["groups"]
        ),
        "alias_counts": {key: len(data["name-aliases"][key]) for key in ("vi", "en", "buildNames")},
        "pipeline": "Garena: mô tả kỹ năng và hệ thống. Fandom EN: chỉ số. Fandom VI: nhãn và build. Các ô thiếu và nhãn suy ra cần kiểm chứng.",
    }
    write(root / "reports/upstream-audit.json", encode(report))
    return report


def request_limited(client: httpx.Client, url: str, headers: dict) -> tuple[int, dict, bytes]:
    with client.stream("GET", url, headers=headers) as response:
        if response.status_code == 304:
            return 304, dict(response.headers), b""
        response.raise_for_status()
        content = bytearray()
        for chunk in response.iter_bytes():
            content.extend(chunk)
            if len(content) > MAX_RESPONSE:
                raise ValueError("Nguồn vượt giới hạn dung lượng.")
        return response.status_code, dict(response.headers), bytes(content)


def monitor(root: Path) -> dict:
    registry = read(root / "knowledge/sources/registry.json")["sources"]
    checkpoint_file = root / ".local/update/monitor.json"
    checkpoint = read(checkpoint_file) if checkpoint_file.exists() else {}
    result = {}
    with httpx.Client(
        timeout=15, follow_redirects=False, headers={"User-Agent": USER_AGENT}
    ) as client:
        for source_id, source in registry.items():
            urls = source.get("monitor_urls", [])
            if not urls:
                continue
            if source["acquisition"] != "approved_http" or not source.get("permission_ref"):
                raise ValueError(f"Nguồn {source_id} thiếu quyền HTTP đã ghi nhận.")
            origin = urlsplit(source["url"])
            if (
                origin.scheme != "https"
                or not origin.hostname
                or origin.username
                or origin.password
            ):
                raise ValueError(f"Nguồn {source_id} cần URL HTTPS hợp lệ.")
            for url in urls:
                parsed = urlsplit(url)
                if (parsed.scheme, parsed.netloc) != (origin.scheme, origin.netloc):
                    raise ValueError(f"URL theo dõi ngoài phạm vi nguồn {source_id}.")
            _, _, raw = request_limited(client, f"https://{origin.netloc}/robots.txt", {})
            rules = RobotFileParser()
            rules.parse(raw.decode("utf-8").splitlines())
            for url in urls:
                if not rules.can_fetch(USER_AGENT, url):
                    result[url] = "blocked_by_robots"
                    continue
                previous = checkpoint.get(url, {})
                headers = {
                    header: previous[key]
                    for key, header in (
                        ("etag", "If-None-Match"),
                        ("last_modified", "If-Modified-Since"),
                    )
                    if previous.get(key)
                }
                status, response, content = request_limited(client, url, headers)
                if status == 304:
                    result[url] = "unchanged"
                    continue
                digest = hashlib.sha256(content).hexdigest()
                change = (
                    "new"
                    if not previous
                    else ("revised" if previous["sha256"] != digest else "unchanged")
                )
                checkpoint[url] = {
                    "sha256": digest,
                    "etag": response.get("etag"),
                    "last_modified": response.get("last-modified"),
                    "pending_review": change != "unchanged"
                    or previous.get("pending_review", False),
                }
                write(checkpoint_file, encode(checkpoint))
                result[url] = change
    return {
        "monitor": result,
        "pending_review": sorted(url for url, row in checkpoint.items() if row["pending_review"]),
    }
