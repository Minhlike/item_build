import hashlib
import json
from pathlib import Path
from platform import system
from statistics import quantiles
from time import perf_counter_ns

from .retrieval import Repository
from .storage import encode


def benchmark(root: Path) -> dict:
    import tiktoken

    tokenizer = tiktoken.get_encoding("o200k_base")
    cases = [
        ("thane", ["trieu van", "bolt baron", "allain", "natalya", "ryoma"]),
        ("thane", ["richter", "trieu van", "hayate", "raz", "kaine"]),
        ("thane", ["ybneth", "fennik", "trieu van", "omen", "preyta"]),
        ("thane", ["butterfly", "yue", "arthur", "hayate", "edras"]),
    ]
    measurements = []
    for hero, enemies in cases:
        start = perf_counter_ns()
        repo = Repository(root)
        index_ms = (perf_counter_ns() - start) / 1_000_000
        start = perf_counter_ns()
        context = repo.context(hero, "support", enemies, "fast_draft")
        first_ms = (perf_counter_ns() - start) / 1_000_000
        warm = []
        for _ in range(200):
            start = perf_counter_ns()
            repo.context(hero, "support", enemies, "fast_draft")
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
                "index_load_ms": round(index_ms, 3),
                "first_context_ms": round(first_ms, 3),
                "warm_context_p95_ms": round(quantiles(warm, n=100)[94], 3),
                "formats": sizes,
            }
        )
    return {
        "tokenizer": "o200k_base",
        "platform": system(),
        "runs_per_case": 200,
        "scope": "Local runtime. File reads include initial indexes. Model quality and connector latency remain unmeasured.",
        "cases": measurements,
    }
