import json
from pathlib import Path

from collect_final_evidence import collect


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def test_collects_counts_from_logs_and_preserves_only_named_outputs(tmp_path):
    root = tmp_path
    tr = root / "training"
    (root / "sampling" / "run").mkdir(parents=True)
    fixtures = [json.loads(line) for line in (Path(__file__).parents[1] / "evaluation" / "new_eval_candidates.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    (root / "sampling" / "new_eval_candidates.jsonl").write_bytes(
        (Path(__file__).parents[1] / "evaluation" / "new_eval_candidates.jsonl").read_bytes())
    selected = []
    for c in range(4000):
        rows = {mode: {"sample_id": f"s{c}-{mode}", "row_sha256": f"{c:064x}"}
                for mode in ("worked_solution", "hint_level_1", "hint_level_2", "hint_level_3")}
        selected.append({"rows": rows})
    write_json(root / "sampling" / "run" / "training_view_manifest.json", {
        "selected_cases": 4000, "selected_chat_rows": 16000, "all_four_modes_preserved": True,
        "raw_train_rows_scanned": 6502344,
        "recipe_sha256": "1bb69c394c7eaaea7034125c6b3361eebbbe0d77e0715a8454331fbe7cee3ff8",
        "selected_cases_manifest": selected,
    })
    write_json(root / "budget_control.json", {"deadline_unix": 9999999999})
    write_json(tr / "run_config.json", {"model": "Qwen/Qwen3-1.7B", "revision": "70d244cc86ccca08cf5af4e1e306ecf908b1ad5e", "microbatch": 1})
    write_json(root / "runtime_versions.json", {"record": {"packages": {"torch": "test-version"},
                 "nvidia_smi": "Tesla T4 test", "evidence_scope": "package metadata and nvidia-smi only"}})
    success = [{"step": step, "sample_id": f"s{i}-worked_solution"}
               for step in (1, 2) for i in range(16)]
    (tr / "successful_ids.jsonl").write_text("".join(json.dumps(x) + "\n" for x in success), encoding="utf-8")
    (tr / "checkpoint_timing.jsonl").write_text(json.dumps({"step": 2}) + "\n", encoding="utf-8")
    generation = [{"fixture_id": x["id"], "stage": "base_before_training"} for x in fixtures]
    (tr / "base_generations.jsonl").write_text("".join(json.dumps(x) + "\n" for x in generation), encoding="utf-8")
    after = [{**x, "stage": "adapter_after_training"} for x in generation]
    (tr / "adapter_generations.jsonl").write_text("".join(json.dumps(x) + "\n" for x in after), encoding="utf-8")
    write_json(tr / "run_complete.json", {
        "complete": True, "step": 2, "rows_done": 32, "eval_fixture_count": 28,
        "base_outputs": 28, "adapter_outputs": 28, "adapter_zip_sha256": "a" * 64,
        "config": {"model": "Qwen/Qwen3-1.7B", "revision": "70d244cc86ccca08cf5af4e1e306ecf908b1ad5e",
                   "microbatch": 1, "selected_microbatch": 2, "grad_accumulation": 8, "effective_batch": 16},
        "metrics": {"step": 2, "rows_done": 32, "unique_examples": 16,
                    "supervised_tokens": 1000, "nonpadding_tokens": 2000,
                    "completed_view_epochs": 0.002, "peak_vram_bytes": 123,
                    "mean_loss": 2.4, "elapsed_seconds": 20.0},
    })
    result = collect(root)
    normalized = result["normalized_run_complete_candidate"]
    assert normalized["example_exposures"] == 32
    assert normalized["unique_examples"] == 16
    assert normalized["successful_optimizer_steps"] == 2
    assert normalized["framework_versions"] == {"torch": "test-version"}
    assert normalized["gpu"] == "Tesla T4 test"
    assert normalized["training_runtime_settings"]["actual_physical_microbatch"] == 2
    assert normalized["training_runtime_settings"]["original_run_config_file_microbatch"] == 1
    assert normalized["supervised_tokens"] == 1000
    assert len(result["base_generations"]) == len(result["adapter_generations"]) == 28
    assert "training_view.jsonl" not in str(result["raw_file_records"])
