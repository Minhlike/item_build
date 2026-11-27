import argparse
import csv
import hashlib
import json
import random
import subprocess
import sys
import zipfile
from collections import Counter
from pathlib import Path, PurePosixPath
from statistics import mean

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PHASE2 = "b0146c96f82f2652ddb1184b27763b3ad5a7c2da"
ARMS = ("A", "B", "C")
DIMENSIONS = {
    "mechanics",
    "context",
    "quantitative",
    "legality",
    "purchase-order",
    "tactics",
    "uncertainty",
    "preference",
}
LANES = {"support", "mid", "jungle", "dragon", "slayer"}
CLASSES = {"tank", "mage", "assassin", "marksman", "warrior", "support"}
BUNDLE_PATHS = [
    "AGENTS.md",
    "README.md",
    "prompts",
    "knowledge",
    "packs",
    "schemas",
    "src",
    "pyproject.toml",
    "uv.lock",
]


def table(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def unique_index(rows, key):
    indexed = {row[key]: row for row in rows}
    if len(indexed) != len(rows):
        raise ValueError(f"Duplicate {key}")
    return indexed


def suite():
    questions = unique_index(table(HERE / "questions.tsv"), "id")
    rubric = unique_index(table(HERE / "rubric.tsv"), "id")
    if len(questions) < 50 or questions.keys() != rubric.keys():
        raise ValueError("Coverage or rubric IDs invalid")
    if len({row["question"] for row in questions.values()}) != len(questions):
        raise ValueError("Duplicate question text")
    if {row["lane"] for row in questions.values()} != LANES or {
        row["class"] for row in questions.values()
    } != CLASSES:
        raise ValueError("Lane or class coverage incomplete")
    if {row["dimension"] for row in rubric.values()} != DIMENSIONS:
        raise ValueError("Score dimensions invalid")
    if any(not all(row.values()) for row in (*questions.values(), *rubric.values())):
        raise ValueError("Empty question or rubric field")
    return questions, rubric


def fingerprint(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def revision(ref):
    return subprocess.check_output(
        ["git", "rev-parse", "--verify", "--end-of-options", f"{ref}^{{commit}}"],
        cwd=ROOT,
        text=True,
    ).strip()


def bundle(path, sha):
    if sha is None:
        with zipfile.ZipFile(path, "w"):
            return
    subprocess.run(
        ["git", "archive", "--format=zip", f"--output={path}", sha, *BUNDLE_PATHS],
        cwd=ROOT,
        check=True,
    )
    with zipfile.ZipFile(path) as archive:
        for name in archive.namelist():
            parts = PurePosixPath(name).parts
            if (
                not parts
                or parts[0] not in BUNDLE_PATHS
                or any(part in {".local", "evaluations", "reports"} for part in parts)
            ):
                raise ValueError("Unexpected bundle path")


def prepare(out, model, settings, phase3, seed):
    questions, _ = suite()
    phase3 = revision(phase3)
    if (
        phase3 == PHASE2
        or subprocess.run(
            ["git", "merge-base", "--is-ancestor", PHASE2, phase3], cwd=ROOT, check=False
        ).returncode
    ):
        raise ValueError("Phase 3 revision must descend from the Phase 2 checkpoint")
    if not isinstance(settings, dict) or not model.strip():
        raise ValueError("Specify a model ID and one shared settings object")
    out.mkdir(parents=True, exist_ok=False)
    (out / "packets").mkdir()
    (out / "responses").mkdir()
    common = (
        "Bạn đang làm bài kiểm định Liên Quân Mobile rank đơn Việt Nam, mốc 27/11/2026. "
        "Chỉ dùng ngữ cảnh được cấp và, nếu có, tệp trong bộ tri thức chỉ định. "
        "Khi được cấp bộ tri thức, bắt đầu từ AGENTS.md của bộ đó. "
        "Trả lời bằng tiếng Việt theo yêu cầu câu hỏi. Nêu điều kiện và phần thiếu có ảnh hưởng."
    )
    refs = {"A": None, "B": PHASE2, "C": phase3}
    entries = []
    for arm, sha in refs.items():
        bundle(out / f"{arm}.zip", sha)
        for key, row in questions.items():
            opaque = hashlib.sha256(f"{seed}|{arm}|{key}".encode()).hexdigest()[:16]
            packet = out / "packets" / f"{opaque}.json"
            write_json(packet, {"system": common, "user": row["question"]})
            entries.append({"trial": opaque, "arm": arm, "id": key})
    random.Random(seed).shuffle(entries)
    with (out / "grading.tsv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=["trial", "id"], delimiter="\t", extrasaction="ignore"
        )
        writer.writeheader()
        writer.writerows(entries)
    write_json(
        out / "manifest.json",
        {
            "model": model,
            "settings": settings,
            "revisions": refs,
            "seed": seed,
            "questions_sha256": fingerprint(HERE / "questions.tsv"),
            "rubric_sha256": fingerprint(HERE / "rubric.tsv"),
            "bundle_sha256": {arm: fingerprint(out / f"{arm}.zip") for arm in ARMS},
            "trials": entries,
        },
    )
    (out / "scores.tsv").write_text("trial\tscore\n", encoding="utf-8")


def score(out):
    questions, rubric = suite()
    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    for name in ("questions", "rubric"):
        if fingerprint(HERE / f"{name}.tsv") != manifest[f"{name}_sha256"]:
            raise ValueError(f"{name} changed since the trials were prepared")
    trials = unique_index(manifest["trials"], "trial")
    by_case = unique_index(
        [dict(row, pair=(row["id"], row["arm"])) for row in trials.values()], "pair"
    )
    if by_case.keys() != {(key, arm) for key in questions for arm in ARMS}:
        raise ValueError("Expected exactly one trial per case and arm")
    graded = unique_index(table(out / "scores.tsv"), "trial")
    for opaque, row in graded.items():
        if opaque not in trials or row["score"] not in {"0", "1", "2"}:
            raise ValueError("Invalid trial or score")
        if not (out / "responses" / f"{opaque}.txt").read_text(encoding="utf-8").strip():
            raise ValueError(f"Empty transcript for {opaque}")
    paired = [key for key in questions if all(by_case[key, arm]["trial"] in graded for arm in ARMS)]
    result = {
        "model": manifest["model"],
        "completed_triples": len(paired),
        "planned_triples": len(questions),
        "graded_trials": len(graded),
        "groups": {},
    }
    for group in (*sorted(DIMENSIONS), "all"):
        sample = [key for key in paired if group == "all" or rubric[key]["dimension"] == group]
        if sample:
            result["groups"][group] = {
                "paired_cases": len(sample),
                "mean_0_to_2": {
                    arm: mean(int(graded[by_case[key, arm]["trial"]]["score"]) for key in sample)
                    for arm in ARMS
                },
            }
    return result


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="action", required=True)
    commands.add_parser("validate")
    setup = commands.add_parser("prepare")
    setup.add_argument("--out", type=Path, required=True)
    setup.add_argument("--model", required=True)
    setup.add_argument(
        "--settings", required=True, help="JSON file with the actual shared model settings"
    )
    setup.add_argument("--phase3", required=True)
    setup.add_argument("--seed", type=int, default=20261127)
    scoring = commands.add_parser("score")
    scoring.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.action == "validate":
        questions, rubric = suite()
        print(
            json.dumps(
                {
                    "cases": len(questions),
                    "dimensions": Counter(row["dimension"] for row in rubric.values()),
                    "lanes": Counter(row["lane"] for row in questions.values()),
                },
                indent=2,
            )
        )
    elif args.action == "prepare":
        prepare(
            args.out.resolve(),
            args.model,
            json.loads(Path(args.settings).read_text(encoding="utf-8-sig")),
            args.phase3,
            args.seed,
        )
    else:
        print(json.dumps(score(args.out.resolve()), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
