import hashlib
import json
from pathlib import Path
from platform import system
from statistics import quantiles
from time import perf_counter_ns

from .catalog import group_packs
from .progressive import THANE_SUPPORT_PACK
from .retrieval import Repository
from .storage import encode, read

DRAFT_CASES = [
    ["trieu van", "bolt baron", "allain", "natalya", "ryoma"],
    ["richter", "trieu van", "hayate", "raz", "kaine"],
    ["ybneth", "fennik", "trieu van", "omen", "preyta"],
    ["butterfly", "yue", "arthur", "hayate", "edras"],
    ["raz", "natalya", "butterfly", "preyta", "darcy"],
]
THANE_CLOUD_CASE = ["Alice", "Hayate", "Arthur", "Triệu Vân", "Lauriel"]


def benchmark_progressive(root: Path) -> dict:
    import tiktoken

    tokenizer = tiktoken.get_encoding("o200k_base")

    def tokens(data):
        return len(tokenizer.encode(encode(data, compact=True).decode()))

    def raw_tokens(paths):
        return sum(len(tokenizer.encode((root / p).read_text(encoding="utf-8"))) for p in paths)

    regressions = read(root / "evaluations/phase2_cases.json")
    lineups = [
        (f"phase3-{i}", "thane", "support", enemies) for i, enemies in enumerate(DRAFT_CASES, 1)
    ]
    lineups += [(case["id"], case["hero"], case["role"], case["enemies"]) for case in regressions]
    lineups.append(("cloud-67s", "thane", "support", THANE_CLOUD_CASE))
    measurements = []
    for label, hero, role, enemies in lineups:
        layers = {}
        for layer in ("l1", "l2"):
            repo = Repository(root)
            context = repo.context(
                hero, role, enemies, "fast_draft", layer=layer, include_reasoning=True
            )
            paths = ["knowledge/VERSION.json", *repo.cached]
            prompts = ["prompts/cloud_bootstrap.md", "prompts/fast_draft.md"]
            warm_path = {}
            if layer == "l1" and THANE_SUPPORT_PACK in repo.cached:
                paths = list(repo.cached)
                prompts = ["prompts/cloud_bootstrap.md"]
                added = [path for path in paths if path != THANE_SUPPORT_PACK]
                warm_path = {
                    "preload_knowledge_tokens": raw_tokens([THANE_SUPPORT_PACK]),
                    "post_form_reads": len(added),
                    "post_form_tokens": raw_tokens(added),
                }
            elif layer == "l2":
                paths.append("packs/INDEX.json")
                prompts.append("prompts/reasoning_protocol.md")
            layers[layer] = {
                "assembled_tokens": tokens(context),
                "github_knowledge_file_count": len(paths),
                "github_knowledge_tokens": raw_tokens(paths),
                "github_tokens_with_prompts": raw_tokens(paths + prompts),
                **warm_path,
            }
        measurements.append(
            {"case": label, "hero": hero, "role": role, "enemies": enemies, **layers}
        )
    return {
        "tokenizer": "o200k_base",
        "scope": "JSON dựng cục bộ và tổng token file thô mô phỏng đọc GitHub. Chưa đo connector, chất lượng đầu ra hoặc win rate.",
        "cases": measurements,
    }


def benchmark_catalogs(root: Path) -> dict:
    import tiktoken

    tokenizer = tiktoken.get_encoding("o200k_base")
    repo = Repository(root)
    strategies = {
        "thane_support_draft": ("defense", "support", "boots"),
        "mage_preparation": ("magic", "boots", "runes", "enchantments", "spells", "battlefield"),
        "whole_catalog": tuple(repo.catalogs),
    }
    measurements = {}
    for label, groups in strategies.items():
        bundled = [repo.read_file(repo.catalogs[group]) for group in groups]
        individual = {}
        for record in bundled:
            group = record["group"]
            for entry_id, entry in record["entries"].items():
                kind = "items" if "shop_group" in entry else group
                key = f"{kind}/{entry_id}"
                individual[key] = repo.get(key)

        same_fields = group_packs(
            {key: {"candidates": {}, **entry} for key, entry in individual.items()}
        ) == {record["group"]: record["entries"] for record in bundled}

        def measure(documents):
            raw = [encode(doc, compact=True) for doc in documents]
            return {
                "file_reads": len(raw),
                "bytes": sum(map(len, raw)),
                "tokens": sum(len(tokenizer.encode(blob.decode())) for blob in raw),
            }

        measurements[label] = {
            "entity_count": len(individual),
            "live_facts": sum(len(entry["live"]) for entry in individual.values()),
            "candidate_facts": sum(
                len(facts)
                for entry in individual.values()
                for facts in entry.get("candidates", {}).values()
            ),
            "same_claims_conditions_and_unknowns": same_fields,
            "individual": measure(list(individual.values())),
            "grouped": measure(bundled),
        }
        if not same_fields:
            raise ValueError(f"Phát hiện mất dữ liệu khi gộp {label}.")
    return {
        "tokenizer": "o200k_base",
        "scope": "Same compiled records; individual versus grouped file reads. One file per call is an estimate. Connector latency was not measured.",
        "cases": measurements,
    }


def benchmark(root: Path, *, reasoning: bool = False) -> dict:
    import tiktoken

    tokenizer = tiktoken.get_encoding("o200k_base")
    cases = [("thane", enemies) for enemies in DRAFT_CASES]
    measurements = []
    for hero, enemies in cases:
        start = perf_counter_ns()
        repo = Repository(root)
        index_ms = (perf_counter_ns() - start) / 1_000_000
        start = perf_counter_ns()
        context = repo.context(hero, "support", enemies, "fast_draft", include_reasoning=reasoning)
        first_ms = (perf_counter_ns() - start) / 1_000_000
        knowledge_paths = ["knowledge/VERSION.json", "packs/INDEX.json", *repo.cached]
        prompt_paths = ["prompts/cloud_bootstrap.md", "prompts/fast_draft.md"]
        if reasoning and repo.tactics:
            prompt_paths.append("prompts/reasoning_protocol.md")
        raw_tokens = {
            "knowledge": sum(
                len(tokenizer.encode((root / path).read_text(encoding="utf-8")))
                for path in knowledge_paths
            ),
            "prompts": sum(
                len(tokenizer.encode((root / path).read_text(encoding="utf-8")))
                for path in prompt_paths
            ),
            "prompt_reads": len(prompt_paths),
        }
        warm = []
        for _ in range(200):
            start = perf_counter_ns()
            repo.context(hero, "support", enemies, "fast_draft", include_reasoning=reasoning)
            warm.append((perf_counter_ns() - start) / 1_000_000)
        formats = {
            "json": encode(context),
            "json_compact": encode(context, compact=True),
            "markdown_sections_with_json": "\n\n".join(
                f"## {key}\n\n```json\n{encode(value, compact=True).decode()}```"
                for key, value in context.items()
            ).encode(),
        }
        sizes = {}
        for fmt, raw in formats.items():
            lines = raw.decode()
            read_times = []
            for _ in range(200):
                start = perf_counter_ns()
                if fmt.startswith("markdown"):
                    values = [value.split("```", 1)[0] for value in lines.split("```json\n")[1:]]
                    decoded = dict(zip(context, map(json.loads, values), strict=True))
                else:
                    decoded = json.loads(raw)
                read_times.append((perf_counter_ns() - start) / 1_000_000)
            sizes[fmt] = {
                "bytes": len(raw),
                "tokens": len(tokenizer.encode(lines)),
                "round_trip": decoded == context,
                "decode_p95_ms": round(quantiles(read_times, n=100)[94], 3),
                "sha256": hashlib.sha256(raw).hexdigest(),
            }
        measurements.append(
            {
                "hero": hero,
                "enemies": enemies,
                "file_reads": repo.files_read,
                "raw_file_tokens": raw_tokens,
                "index_load_ms": round(index_ms, 3),
                "first_context_ms": round(first_ms, 3),
                "warm_context_p95_ms": round(quantiles(warm, n=100)[94], 3),
                "formats": sizes,
            }
        )
    return {
        "tokenizer": "o200k_base",
        "platform": system(),
        "reasoning_pack_enabled": reasoning and repo.tactics is not None,
        "runs_per_case": 200,
        "scope": "Local runtime. File reads include initial indexes. Model quality and connector latency remain unmeasured.",
        "cases": measurements,
    }
