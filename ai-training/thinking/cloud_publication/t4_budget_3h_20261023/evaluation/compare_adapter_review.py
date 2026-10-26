"""CLI wrapper for aggregating explicit base/adapter semantic review JSON."""
import argparse
import json
from pathlib import Path

from review_aggregation import compare_reviews, load_review

parser = argparse.ArgumentParser()
parser.add_argument("--base-review", type=Path, default=Path(__file__).with_name("base_semantic_review.json"))
parser.add_argument("--adapter-review", type=Path, required=True)
parser.add_argument("--fixtures", type=Path, default=Path(__file__).with_name("new_eval_candidates.jsonl"))
parser.add_argument("--base-generation-sha256", required=True,
                    help="SHA256 of uploaded raw base-generation file, not controller JSONL rendering")
parser.add_argument("--adapter-generation-sha256", required=True,
                    help="SHA256 of uploaded raw adapter-generation file")
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()

fixture_rows = [json.loads(line) for line in args.fixtures.read_text(encoding="utf-8").splitlines() if line.strip()]
if len(fixture_rows) != 28 or len({row["id"] for row in fixture_rows}) != 28:
    raise SystemExit("frozen fixture file must contain exactly 28 unique IDs")
fixture_ids = {row["id"] for row in fixture_rows}
import hashlib
fixture_sha = hashlib.sha256(args.fixtures.read_bytes()).hexdigest()
result = compare_reviews(load_review(args.base_review), load_review(args.adapter_review),
    expected_fixture_ids=fixture_ids, expected_fixture_sha256=fixture_sha,
    expected_base_source_sha256=args.base_generation_sha256,
    expected_adapter_source_sha256=args.adapter_generation_sha256)
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"wrote comparison for {result['fixture_count']} fixtures: {args.output}")
