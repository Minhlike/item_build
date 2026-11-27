import argparse
import subprocess
import sys
from pathlib import Path

import httpx

from .acquisition import audit, clean_for_review, monitor, snap
from .benchmark import benchmark, benchmark_catalogs
from .compiler import compile_repo
from .local_review import build_local_review
from .retrieval import LANES, Repository
from .storage import encode, read, write


def main() -> int:
    parser = argparse.ArgumentParser(prog="item-build")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("ingest", "audit", "enrich", "compile", "validate", "update"):
        commands.add_parser(name)
    commands.choices["enrich"].add_argument("--hero")
    query = commands.add_parser("query")
    query.add_argument("--hero", required=True)
    query.add_argument("--canonical", action="store_true")
    query.add_argument("--local-upstream", action="store_true")
    context = commands.add_parser("context")
    context.add_argument("--hero", required=True)
    context.add_argument("--role", choices=sorted(LANES))
    context.add_argument("--enemies", nargs="*", default=[])
    context.add_argument("--mode", choices=["hero_preparation", "fast_draft"], default="fast_draft")
    context.add_argument("--include-candidates", action="store_true")
    cooldown = commands.add_parser("cooldown")
    cooldown.add_argument("--entity", required=True)
    cooldown.add_argument("--property", required=True)
    cooldown.add_argument("--input", action="append", default=[])
    cooldown.add_argument("--cdr", type=float)
    cooldown.add_argument("--cap", type=float)
    perf = commands.add_parser("benchmark")
    perf.add_argument("--save", action="store_true")
    perf.add_argument("--catalogs", action="store_true")
    options = parser.parse_args()
    root = options.root.resolve()
    try:
        result = run(root, options)
    except (ValueError, KeyError, OSError, subprocess.SubprocessError, httpx.HTTPError) as error:
        sys.stderr.buffer.write(f"Lỗi: {error}\n".encode())
        return 2
    sys.stdout.buffer.write(encode(result))
    return 0


def run(root: Path, options) -> dict:
    match options.command:
        case "ingest" | "audit":
            manifest, datasets = snap(root)
            clean_for_review(root, datasets)
            build_local_review(root, manifest, datasets)
            return audit(root, manifest, datasets) if options.command == "audit" else manifest
        case "enrich":
            repo = Repository(root)
            if options.hero:
                key = f"heroes/{repo.identify(options.hero)}"
                pack = repo.get(key)
                name = pack["name"]
                return {
                    "canonical": pack["canonical"],
                    "unknown": pack["unknown"],
                    "review_properties": pack["review_properties"],
                    "search_candidates": [
                        f"site:lienquan.garena.vn {name} cập nhật nội tại hồi chiêu",
                        f"{name} Arena of Valor VN skill cooldown patch",
                        f"{name} 傳說對決 技能 冷卻 更新",
                        f"{name} RoV สกิล คูลดาวน์ แพตช์",
                    ],
                    "review_rule": "Nguồn ngoài VN chỉ dùng đối chiếu; cần xác minh tương thích và quyền nguồn.",
                }
            return {
                "coverage": repo.version["coverage"],
                "gaps": repo.version["gaps"],
                "review_queue": "reports/upstream-audit.json",
                "inputs": ["sources/entities", "patches", "overrides"],
            }
        case "compile" | "validate":
            return compile_repo(root, check=options.command == "validate")
        case "update":
            changes = monitor(root)
            pin = read(root / "sources/upstream.json")
            upstream_head = subprocess.check_output(
                ["git", "ls-remote", pin["repository"], "HEAD"], text=True, timeout=30
            ).split()
            if not upstream_head:
                raise ValueError("Upstream không trả về HEAD.")
            upstream_head = upstream_head[0]
            return {
                "upstream_candidate": upstream_head if upstream_head != pin["sha"] else None,
                **changes,
                "compile": compile_repo(root),
                "validate": compile_repo(root, check=True),
            }
        case "query":
            repo = Repository(root)
            hero_id = repo.identify(options.hero)
            result = repo.get(f"heroes/{hero_id}", canonical=options.canonical)
            if options.local_upstream:
                pin = read(root / "sources/upstream.json")["sha"]
                path = root / ".local/review" / pin / "heroes" / f"{hero_id}.json"
                result = {
                    **result,
                    "local_unverified": read(path),
                }
            return result
        case "context":
            return Repository(root).context(
                options.hero,
                options.role,
                options.enemies,
                options.mode,
                include_candidates=options.include_candidates,
            )
        case "cooldown":
            inputs = {}
            for entry in options.input:
                stat, value = entry.split("=", 1)
                inputs[stat] = float(value)
            return Repository(root).cooldown(
                options.entity, options.property, inputs, options.cdr, options.cap
            )
        case "benchmark":
            result = (benchmark_catalogs if options.catalogs else benchmark)(root)
            if options.save:
                name = "catalog-benchmark.json" if options.catalogs else "benchmark.json"
                write(root / "reports" / name, encode(result))
            return result
    raise ValueError("Lệnh không hợp lệ.")


if __name__ == "__main__":
    raise SystemExit(main())
