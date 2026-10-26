"""Read-only CPU collector for small final-run metadata and 28 eval outputs.

Reads named JSON/JSONL metadata files only. It does not open the selected
training JSONL, checkpoints, weights, or the adapter ZIP payload.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
from typing import Any

MODEL = "Qwen/Qwen3-1.7B"
REVISION = "70d244cc86ccca08cf5af4e1e306ecf908b1ad5e"
RECIPE_SHA256 = "1bb69c394c7eaaea7034125c6b3361eebbbe0d77e0715a8454331fbe7cee3ff8"
FIXTURE_SHA256 = "81ddf4261063b5832b6f55168ca160bf5cec26a5cabd83b7fedaa00ddecec100"


def _json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _jsonl(path: Path) -> list[dict[str, Any]]:
    out = []
    with path.open("r", encoding="utf-8") as stream:
        for n, line in enumerate(stream, 1):
            if not line.strip():
                raise ValueError(f"blank record at {path.name}:{n}")
            row = json.loads(line)
            if not isinstance(row, dict):
                raise ValueError(f"non-object record at {path.name}:{n}")
            out.append(row)
    return out


def _file_record(path: Path, *, include_records: bool = False) -> dict[str, Any]:
    raw = path.read_bytes()
    record = {"name": path.name, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
    if include_records:
        record["records"] = [json.loads(line) for line in raw.decode("utf-8").splitlines() if line.strip()]
    return record


def collect(runtime_root: str | Path) -> dict[str, Any]:
    root = Path(runtime_root)
    training = root / "training"
    sampling_candidates = [root / "sampling" / "run" / "training_view_manifest.json",
                           root / "sampling" / "training_view_manifest.json"]
    manifest_path = next((p for p in sampling_candidates if p.is_file()), None)
    if manifest_path is None:
        raise FileNotFoundError("selected-view training_view_manifest.json not found")
    paths = {
        "budget_control": root / "budget_control.json",
        "manifest": manifest_path,
        "run_complete": training / "run_complete.json",
        "run_config": training / "run_config.json",
        "successful_ids": training / "successful_ids.jsonl",
        "checkpoint_timing": training / "checkpoint_timing.jsonl",
        "base_generations": training / "base_generations.jsonl",
        "adapter_generations": training / "adapter_generations.jsonl",
    }
    for label, path in paths.items():
        if not path.is_file():
            raise FileNotFoundError(f"required final evidence missing ({label}): {path}")
    budget = _json(paths["budget_control"])
    budget = budget.get("budget", budget)
    manifest = _json(paths["manifest"])
    run_complete = _json(paths["run_complete"])
    run_config_file = _json(paths["run_config"])
    cfg = run_complete.get("config") or run_config_file
    metrics = run_complete.get("metrics")
    if not isinstance(metrics, dict):
        raise ValueError("run_complete metrics missing; no counters inferred")
    if run_complete.get("complete") is not True:
        raise ValueError("run_complete does not declare complete=true")
    if cfg.get("model") != MODEL or cfg.get("revision") != REVISION:
        raise ValueError("run config model/revision differs from pinned experiment")
    if manifest.get("all_four_modes_preserved") is not True or manifest.get("selected_chat_rows") != 16000 or manifest.get("selected_cases") != 4000:
        raise ValueError("selected-view manifest is not the expected complete 4000-case/16000-row view")
    if manifest.get("raw_train_rows_scanned") != 6502344 or manifest.get("recipe_sha256") != RECIPE_SHA256:
        raise ValueError("sampling manifest does not bind the full pinned train release")

    successful = _jsonl(paths["successful_ids"])
    sample_ids = [row.get("sample_id") for row in successful]
    if any(not isinstance(s, str) or not s for s in sample_ids):
        raise ValueError("successful_ids contains missing sample_id")
    unique_ids = set(sample_ids)
    steps = [row.get("step") for row in successful]
    if any(not isinstance(step, int) or step <= 0 for step in steps):
        raise ValueError("successful_ids contains invalid step")
    step_counts = {}
    for step in steps:
        step_counts[step] = step_counts.get(step, 0) + 1
    expected_ids = {info.get("sample_id") for case in manifest.get("selected_cases_manifest", [])
                    for info in case.get("rows", {}).values()}
    if len(expected_ids) != manifest["selected_chat_rows"] or None in expected_ids:
        raise ValueError("selected-view manifest row-ID binding is malformed")
    unknown = sorted(unique_ids - expected_ids)
    if unknown:
        raise ValueError(f"successful_ids includes IDs outside selected train view: {unknown[:3]}")
    rows_done = run_complete.get("rows_done")
    if rows_done != len(successful) or metrics.get("rows_done") != len(successful):
        raise ValueError("successful_ids exposure count disagrees with run_complete/metrics")
    if metrics.get("unique_examples") != len(unique_ids):
        raise ValueError("unique successful IDs disagree with metrics.unique_examples")
    if metrics.get("step") != run_complete.get("step"):
        raise ValueError("run_complete step disagrees with final metrics")
    if len(step_counts) != run_complete["step"] or any(step_counts.get(i, 0) == 0 for i in range(1, run_complete["step"] + 1)):
        raise ValueError("successful_ids does not show one or more optimizer steps")

    base = _jsonl(paths["base_generations"])
    adapter = _jsonl(paths["adapter_generations"])
    eval_candidates = root / "sampling" / "new_eval_candidates.jsonl"
    if not eval_candidates.is_file():
        raise FileNotFoundError("pinned 28-row new_eval_candidates.jsonl missing from runtime sampling folder")
    fixture_rows = _jsonl(eval_candidates)
    fixture_sha256 = hashlib.sha256(eval_candidates.read_bytes()).hexdigest()
    if fixture_sha256 != FIXTURE_SHA256:
        raise ValueError("runtime eval fixture raw SHA256 differs from frozen 28-fixture release")
    fixture_ids = {case.get("id") for case in fixture_rows}
    if len(fixture_rows) != 28 or len(fixture_ids) != 28:
        raise ValueError("runtime frozen fixture file must contain 28 unique fixture IDs")
    if {case["fixture_id"] for case in base} != fixture_ids:
        raise ValueError("base generations do not cover the frozen fixture IDs")
    if len(base) != 28 or len(adapter) != 28 or len(fixture_ids) != 28 or {x.get("fixture_id") for x in adapter} != fixture_ids:
        raise ValueError("base and adapter generation outputs must each cover the exact same 28 fixtures")
    if any(row.get("stage") != "base_before_training" for row in base):
        raise ValueError("base generation stage labels do not match pretraining snapshot")
    if any(row.get("stage") != "adapter_after_training" for row in adapter):
        raise ValueError("adapter generation stage labels do not match post-training snapshot")
    if run_complete.get("base_outputs") != 28 or run_complete.get("adapter_outputs") != 28 or run_complete.get("eval_fixture_count") != 28:
        raise ValueError("run_complete eval counts disagree with actual generation JSONL files")

    timings = _jsonl(paths["checkpoint_timing"])
    timing_steps = [x.get("step") for x in timings]
    if any(not isinstance(x, int) for x in timing_steps) or timing_steps != sorted(timing_steps):
        raise ValueError("checkpoint timing records have missing or unordered step values")
    stat = paths["run_complete"].stat()
    finish_unix = stat.st_mtime
    finish_utc = datetime.fromtimestamp(finish_unix, timezone.utc).isoformat()
    elapsed = metrics.get("elapsed_seconds")
    if not isinstance(elapsed, (int, float)) or elapsed <= 0:
        raise ValueError("metrics.elapsed_seconds missing/invalid")
    if not isinstance(metrics.get("supervised_tokens"), int) or not isinstance(metrics.get("nonpadding_tokens"), int):
        raise ValueError("actual supervised/nonpadding token metrics are absent")
    if metrics.get("completed_view_epochs") is None or metrics.get("peak_vram_bytes") is None or metrics.get("mean_loss") is None:
        raise ValueError("required final progress metrics are absent; none will be reconstructed")

    runtime_versions_path = root / "runtime_versions.json"
    runtime_versions = _json(runtime_versions_path) if runtime_versions_path.is_file() else None
    runtime_record = runtime_versions.get("record", runtime_versions) if isinstance(runtime_versions, dict) else None
    runtime_packages = runtime_record.get("packages") if isinstance(runtime_record, dict) else None
    benchmark_ids = cfg.get("benchmark_sample_ids")
    if benchmark_ids is None:
        benchmark_ids = cfg.get("bench_sample_ids")
    torch_bench_candidates = [training / "torch_baseline_benchmark.json", root / "torch_baseline_benchmark.json"]
    torch_bench_path = next((p for p in torch_bench_candidates if p.is_file()), None)
    torch_bench = _json(torch_bench_path) if torch_bench_path else None
    if benchmark_ids is None and isinstance(torch_bench, dict):
        benchmark_ids = torch_bench.get("unique_sample_ids")
    framework_versions = runtime_packages or cfg.get("framework_versions")
    if framework_versions is None and isinstance(torch_bench, dict):
        framework_versions = torch_bench.get("framework_versions")
    actual_microbatch = cfg.get("selected_microbatch", run_config_file.get("selected_microbatch", run_config_file.get("microbatch")))
    actual_grad_accum = cfg.get("grad_accumulation", run_config_file.get("grad_accumulation"))
    normalized = {
        "state": "COMPLETE",
        "model": cfg["model"], "revision": cfg["revision"],
        "framework_versions": framework_versions,
        "gpu": runtime_record.get("nvidia_smi") if isinstance(runtime_record, dict) else None,
        "view_cases": manifest["selected_cases"], "view_chat_rows": manifest["selected_chat_rows"],
        "successful_optimizer_steps": run_complete["step"],
        "example_exposures": len(successful), "unique_examples": len(unique_ids),
        "supervised_tokens": metrics["supervised_tokens"], "nonpad_tokens": metrics["nonpadding_tokens"],
        "completed_view_epochs": metrics.get("completed_view_epochs"),
        "peak_vram_bytes": metrics.get("peak_vram_bytes"),
        "adapter_zip_sha256": run_complete.get("adapter_zip_sha256"),
        "base_fixture_count": len(base), "adapter_fixture_count": len(adapter),
        "base_review": "base_semantic_review.json", "adapter_review": "adapter_semantic_review.json",
        "training_configuration": cfg,
        "training_runtime_settings": {"actual_physical_microbatch": actual_microbatch,
                                      "actual_gradient_accumulation": actual_grad_accum,
                                      "effective_batch": cfg.get("effective_batch", run_config_file.get("effective_batch")),
                                      "selected_setting_source": "run_complete.config selected_microbatch / grad_accumulation, fallback run_config selected fields",
                                      "original_run_config_file_microbatch": run_config_file.get("microbatch")},
        "finish_utc": finish_utc, "finish_unix": finish_unix,
        "finish_time_source": "run_complete.json filesystem mtime (atomic final record write); capture timestamp is not substituted",
        "elapsed_seconds": elapsed, "mean_loss": metrics.get("mean_loss"),
        "base_truncation_count": sum(bool(x.get("possibly_truncated")) for x in base),
        "adapter_truncation_count": sum(bool(x.get("possibly_truncated")) for x in adapter),
        "benchmark_sample_ids": benchmark_ids,
    }
    raw = {label: _file_record(path, include_records=(label in {"successful_ids", "checkpoint_timing", "base_generations", "adapter_generations"}))
           for label, path in paths.items()}
    raw["evaluation_fixtures"] = _file_record(eval_candidates)
    raw["run_config_file"] = _file_record(paths["run_config"])
    if runtime_versions_path.is_file():
        raw["runtime_versions"] = _file_record(runtime_versions_path)
    if torch_bench_path:
        raw["torch_baseline_benchmark"] = _file_record(torch_bench_path)
    if framework_versions is None:
        normalized.pop("framework_versions")
    if benchmark_ids is None:
        normalized.pop("benchmark_sample_ids")
    return {
        "schema": "MathVisionKid.final_runtime_evidence.v1",
        "collected_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "small metadata and exact 28 generation outputs only; no training-view JSONL, corpus, checkpoint, weights, or adapter ZIP payload opened",
        "raw_file_records": raw,
        "run_complete_raw": run_complete,
        "run_config_raw": cfg,
        "run_config_file_raw": run_config_file,
        "budget_control": budget,
        "runtime_versions_raw": runtime_versions,
        "sampling_manifest": manifest,
        "successful_id_exposure_count": len(successful),
        "successful_id_unique_count": len(unique_ids),
        "successful_step_exposure_counts": {str(k): step_counts[k] for k in sorted(step_counts)},
        "checkpoint_timing_records": timings,
        "base_generations": base,
        "adapter_generations": adapter,
        "evaluation_fixture_ids": sorted(fixture_ids),
        "evaluation_fixture_sha256": fixture_sha256,
        "torch_baseline_benchmark": torch_bench,
        "normalized_run_complete_candidate": normalized,
        "completeness": {"run_complete": True, "successful_ids_match_rows_done": True,
                         "unique_ids_match_metrics": True, "all_ids_in_selected_train_view": True,
                         "both_generation_sets_match_28_fixture_ids": True,
                         "checkpoint_timings_steps": timing_steps,
                         "actual_finish_timestamp_uses_file_mtime": True},
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runtime-root", type=Path, default=Path("/content/mathvisionkid_t4_budget_3h_20261023"))
    ap.add_argument("--output", type=Path, default=None)
    args = ap.parse_args()
    result = collect(args.runtime_root)
    target = args.output or (args.runtime_root / "training" / "final_runtime_evidence.json")
    tmp = target.with_suffix(target.suffix + ".pending")
    tmp.write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, target)
    print(json.dumps({"state": "EVIDENCE_COLLECTED", "output": str(target),
                      "steps": result["normalized_run_complete_candidate"]["successful_optimizer_steps"],
                      "exposures": result["successful_id_exposure_count"],
                      "unique_examples": result["successful_id_unique_count"],
                      "base_generations": len(result["base_generations"]),
                      "adapter_generations": len(result["adapter_generations"])}, ensure_ascii=False))


if __name__ == "__main__":
    main()
