"""Build the separate self-contained derived worker; original source is untouched."""
from pathlib import Path

root = Path(__file__).parent
source = (root / 'corrective_worker.py').read_text(encoding='utf-8')


def replace(old, new):
    global source
    if source.count(old) != 1:
        raise ValueError(f'expected exact unique source anchor: {old[:100]}')
    source = source.replace(old, new)


additions = r'''

HARD_DEADLINE_UNIX = 1792819703.0
TRAIN_STOP_UNIX = 1792818803.0
RESERVE_SECONDS = 900
BUDGET_SCOPE = "OWNER_REVISED_REMAINING_COLAB_WINDOW_V2"


def optimizer_coherence(optimizer_state, acknowledged_step):
    """Reject interrupted AdamW updates, partial initialization and mixed steps."""
    expected_ids = [pid for group in optimizer_state["param_groups"] for pid in group["params"]]
    states = optimizer_state["state"]
    if len(set(expected_ids)) != len(expected_ids) or set(states) != set(expected_ids):
        raise ValueError("optimizer parameter state set is incomplete or ambiguous")
    steps = []
    for pid in expected_ids:
        value = states[pid].get("step")
        if hasattr(value, "item"):
            value = value.item()
        if value is None or int(value) != value or int(value) != acknowledged_step:
            raise ValueError(f"incoherent AdamW step for parameter {pid}: {value} vs {acknowledged_step}")
        steps.append(int(value))
    if not steps:
        raise ValueError("empty optimizer state")
    return {"parameter_states": len(steps), "all_parameter_steps": acknowledged_step, "coherent": True}


def validate_resume_files(generation):
    manifest = strict_json((generation / "generation_manifest.json").read_text(encoding="utf-8"))
    if manifest.get("complete") is not True:
        raise ValueError("resume generation is not complete")
    for name, expected_sha in manifest["files"].items():
        if Path(name).name != name or sha_file(generation / name) != expected_sha:
            raise ValueError(f"resume file/hash mismatch: {name}")
        if (generation / name).stat().st_size != manifest["file_bytes"][name]:
            raise ValueError(f"resume file size mismatch: {name}")
    metrics = strict_json((generation / "metrics.json").read_text(encoding="utf-8"))
    cfg = strict_json((generation / "run_config.json").read_text(encoding="utf-8"))
    pins = {"model": MODEL, "revision": REVISION, "train_view_sha256": VIEW_SHA256,
            "train_view_manifest_sha256": MANIFEST_SHA256, "fixture_sha256": FIXTURES_SHA256,
            "tokenizer_helper_sha256": TOKENIZER_HELPER_SHA256, "seed": SEED,
            "effective_batch": EFFECTIVE_BATCH, "lora_r": 16, "lora_alpha": 16,
            "lora_dropout": 0.0, "target_modules": TARGET_MODULES}
    if any(cfg.get(k) != v for k, v in pins.items()):
        raise ValueError("resume configuration differs from pinned training contract")
    if manifest["step"] != metrics["step"] or manifest["rows_done"] != metrics["rows_done"]:
        raise ValueError("checkpoint metrics/manifest step disagreement")
    if metrics["rows_done"] != metrics["step"] * EFFECTIVE_BATCH:
        raise ValueError("checkpoint exposures are not full optimizer groups")
    return manifest, metrics, cfg


def rebuild_acknowledged_state(log_path, prefix_bytes, metrics, rows, cursor):
    """Copy only the CP-bound log prefix; verify exact original same16 sequence."""
    raw = Path(log_path).read_bytes()[:prefix_bytes]
    if len(raw) != prefix_bytes or (raw and not raw.endswith(b"\n")):
        raise ValueError("successful-ID log checkpoint prefix is missing or partial")
    entries = [strict_json(line) for line in raw.decode("utf-8").splitlines()]
    if len(entries) != metrics["rows_done"]:
        raise ValueError("acknowledged log length differs from checkpoint exposures")
    by_id = {row["sample_id"]: row for row in rows}
    expected_epoch, expected_cursor, order = 0, 0, make_length_batches(rows, 0)
    sup = nonpad = 0
    unique, cases = set(), set()
    counts = {key: Counter() for key in ("mode", "grade", "family")}
    for offset in range(0, len(entries), EFFECTIVE_BATCH):
        if expected_cursor >= len(order):
            expected_epoch += 1
            expected_cursor = 0
            order = make_length_batches(rows, expected_epoch)
        ids = [rows[i]["sample_id"] for batch in order[expected_cursor:expected_cursor + ACCUMULATION] for i in batch]
        actual = entries[offset:offset + EFFECTIVE_BATCH]
        if [entry.get("sample_id") for entry in actual] != ids:
            raise ValueError("acknowledged log differs from deterministic original optimizer order")
        if any(entry.get("step") != offset // EFFECTIVE_BATCH + 1 or entry.get("epoch") != expected_epoch for entry in actual):
            raise ValueError("acknowledged log step/epoch disagreement")
        expected_cursor += ACCUMULATION
        for entry in actual:
            row = by_id[entry["sample_id"]]
            unique.add(row["sample_id"])
            cases.add(row["source_case_id"])
            sup += sum(label != -100 for label in row["encoded"]["labels"])
            nonpad += len(row["encoded"]["input_ids"])
            for key in counts:
                counts[key][str(row[key])] += 1
    if (cursor.get("epoch"), cursor.get("next_microbatch")) != (expected_epoch, expected_cursor):
        raise ValueError("checkpoint cursor disagrees with acknowledged log")
    if sup != metrics["supervised_tokens"] or nonpad != metrics["nonpadding_tokens"]:
        raise ValueError("checkpoint token counters disagree with acknowledged IDs")
    if len(unique) != metrics["unique_examples"] or len(cases) != metrics["unique_source_cases"]:
        raise ValueError("checkpoint unique counts disagree with acknowledged IDs")
    for key in counts:
        if dict(counts[key]) != metrics[f"exposures_by_{key}"]:
            raise ValueError(f"checkpoint exposure distribution disagreement: {key}")
    state = {k: v for k, v in metrics.items() if k not in (
        "unique_examples", "unique_source_cases", "exposures_by_mode", "exposures_by_grade", "exposures_by_family")}
    state.update(unique_ids=unique, unique_cases=cases, exposures_by_mode=counts["mode"],
                 exposures_by_grade=counts["grade"], exposures_by_family=counts["family"])
    return state, raw


def replan_lr(elapsed, prior_elapsed, remaining, prior_lr):
    """Continue warmup once if needed; then cosine to floor by revised cutoff."""
    active = max(0.0, elapsed - prior_elapsed)
    warmup_left = max(0.0, TRAIN_SECONDS * WARMUP_FRACTION - prior_elapsed)
    warmup_left = min(warmup_left, max(0.0, remaining * 0.2))
    if warmup_left and active < warmup_left:
        return prior_lr + (PEAK_LR - prior_lr) * active / warmup_left
    start_lr = PEAK_LR if warmup_left else max(MIN_LR, prior_lr)
    fraction = min(1.0, max(0.0, (active - warmup_left) / max(remaining - warmup_left, 1e-6)))
    return MIN_LR + (start_lr - MIN_LR) * (1 + math.cos(math.pi * fraction)) / 2


def regroup_same16(group_ids, rows, physical):
    if physical not in (2, 4, 8) or len(group_ids) != EFFECTIVE_BATCH:
        raise ValueError("physical grouping requires same16 and micro2/4/8")
    # Retain micro2 baseline pairing/order; larger shapes sort within this same group.
    ordered = list(group_ids) if physical == 2 else sorted(group_ids, key=lambda i: len(rows[i]["encoded"]["input_ids"]))
    return [ordered[i:i + physical] for i in range(0, len(ordered), physical)]


def measure_physical_batches(model, tokenizer, rows, group_ids, optimizer, scaler, cutoff_unix):
    """No optimizer/scaler step. Restore RNG, scaler and gradients on every exit."""
    import copy
    import torch
    parameters = [p for p in model.parameters() if p.requires_grad]
    cpu_rng, cuda_rng, python_rng = torch.get_rng_state(), torch.cuda.get_rng_state_all(), random.getstate()
    scale_state = copy.deepcopy(scaler.state_dict())
    budget_end = min(time.monotonic() + 150, time.monotonic() + max(0, cutoff_unix - time.time() - 90))
    stress_ids = sorted(range(len(rows)), key=lambda i: len(rows[i]["encoded"]["input_ids"]), reverse=True)[:16]
    results = []
    def run(ids, micro):
        optimizer.zero_grad(set_to_none=True)
        torch.cuda.reset_peak_memory_stats()
        torch.cuda.synchronize()
        started = time.monotonic()
        for indices in regroup_same16(ids, rows, micro):
            batch = collate([rows[i] for i in indices], tokenizer, "cuda")
            with torch.autocast("cuda", dtype=torch.float16):
                loss = model(**batch).loss * (len(indices) / EFFECTIVE_BATCH)
            if not bool(torch.isfinite(loss).item()):
                raise FloatingPointError("nonfinite benchmark loss")
            scaler.scale(loss).backward()
        grads = [p.grad for p in parameters if p.grad is not None]
        if not grads or not all(bool(torch.isfinite(g).all().item()) for g in grads):
            raise FloatingPointError("nonfinite benchmark gradients")
        torch.cuda.synchronize()
        return time.monotonic() - started, torch.cuda.max_memory_allocated()
    try:
        for micro in (2, 4, 8):
            if time.monotonic() >= budget_end:
                break
            result = {"microbatch": micro, "optimizer_updates": 0, "gradient_checkpointing": "unsloth_retained"}
            try:
                torch.set_rng_state(cpu_rng)
                torch.cuda.set_rng_state_all(cuda_rng)
                run(group_ids, micro)  # untimed graph/kernel warmup, no update
                reps = []
                for _ in range(2):
                    torch.set_rng_state(cpu_rng)
                    torch.cuda.set_rng_state_all(cuda_rng)
                    seconds, peak = run(group_ids, micro)
                    reps.append(seconds)
                _, stress_peak = run(stress_ids, micro)
                memory_margin = torch.cuda.get_device_properties(0).total_memory - max(peak, stress_peak)
                result.update(state="PASS" if memory_margin >= 1024 ** 3 else "REJECT_MEMORY_MARGIN",
                              repeat_seconds=reps, mean_group_seconds=sum(reps) / len(reps),
                              peak_vram_bytes=max(peak, stress_peak), memory_margin_bytes=memory_margin,
                              worst16_length_stress=True)
            except (torch.cuda.OutOfMemoryError, FloatingPointError) as error:
                result.update(state="REJECT", error=type(error).__name__)
            finally:
                optimizer.zero_grad(set_to_none=True)
                torch.cuda.empty_cache()
            results.append(result)
        passing = [result for result in results if result.get("state") == "PASS"]
        if not passing:
            raise RuntimeError("no finite physical batch with 1GiB worst-length memory margin")
        baseline = next((r for r in passing if r["microbatch"] == 2), None)
        chosen = min(passing, key=lambda r: r["mean_group_seconds"])
        if baseline and chosen["mean_group_seconds"] > baseline["mean_group_seconds"] * 0.97:
            chosen = baseline
        return chosen["microbatch"], {"selected_microbatch": chosen["microbatch"], "candidates": results,
                "same16_sample_ids": [rows[i]["sample_id"] for i in group_ids],
                "optimizer_updates": 0, "rng_scaler_gradients_restored": True,
                "checkpointing_off": "Not tested; retain proven Unsloth activation checkpointing within bounded tuning time.",
                "loss_limitation": "Physical token-mean grouping can change example weighting when target lengths differ; effective examples remain16."}
    finally:
        optimizer.zero_grad(set_to_none=True)
        scaler.load_state_dict(scale_state)
        torch.set_rng_state(cpu_rng)
        torch.cuda.set_rng_state_all(cuda_rng)
        random.setstate(python_rng)

'''

replace('\ndef main():', additions + '\ndef main():')
replace('    parser.add_argument("--eval-timeout-seconds", type=int, default=600)', '''    parser.add_argument("--eval-timeout-seconds", type=int, default=600)
    parser.add_argument("--resume-generation", type=Path, required=True)
    parser.add_argument("--resume-successful-ids", type=Path, required=True)
    parser.add_argument("--resume-base-dir", type=Path, required=True)''')
replace('    state = None\n    train_start = None', '''    manifest_before, prior_metrics, prior_config = validate_resume_files(args.resume_generation)
    if time.time() >= TRAIN_STOP_UNIX - 120:
        raise TimeoutError("insufficient revised owner budget to load and resume")
    prior_consumed = float(prior_metrics["training_wall_seconds"])
    state = None
    train_start = None''')
replace('"schema": "MathVisionKid.corrective5h.run.v1"', '"schema": "MathVisionKid.corrective_optimized_v2.run.v1"')
replace('    atomic_json(out / "run_config.json", cfg)\n    atomic_json(out / "progress.json", {"state": "INITIALIZING_FRESH_BASE"', '''    cfg.update(budget_scope=BUDGET_SCOPE, hard_deadline_unix=HARD_DEADLINE_UNIX,
               hard_deadline_utc="2026-10-24T05:28:23Z", train_stop_unix=TRAIN_STOP_UNIX,
               train_stop_utc="2026-10-24T05:13:23Z", reserve_seconds=RESERVE_SECONDS,
               prior_training_consumed_seconds=prior_consumed, fresh_base=False,
               automatic_resume_implemented=True, resume_generation=str(args.resume_generation),
               resume_generation_manifest_sha256=sha_file(args.resume_generation / "generation_manifest.json"),
               resume_note="Explicit coherent optimizer/scaler/RNG/cursor/log-prefix resume of current corrective branch.")
    atomic_json(out / "run_config.json", cfg)
    atomic_json(out / "progress.json", {"state": "INITIALIZING_EXPLICIT_RESUME"''')
replace('        base = cached_base(out, contract, contract_sha)', '''        import shutil
        for name in ("base_generations.jsonl", "base_generation_provenance.json"):
            shutil.copyfile(args.resume_base_dir / name, out / name)
        base = cached_base(out, contract, contract_sha)''')
replace('        FastLanguageModel.for_training(model)\n        parameters =', '''        from peft import set_peft_model_state_dict
        from peft.utils.save_and_load import load_peft_weights
        adapter_state = load_peft_weights(str(args.resume_generation), device="cpu")
        loaded = set_peft_model_state_dict(model, adapter_state)
        if getattr(loaded, "unexpected_keys", []):
            raise ValueError("unexpected adapter weight keys on resume")
        FastLanguageModel.for_training(model)
        parameters =''')
start = source.index('        state = {"step": 0, "rows_done": 0')
end = source.index('        last_checkpoint = train_start', start)
source = source[:start] + '''        resume = torch.load(args.resume_generation / "resume_state.pt", map_location="cpu", weights_only=False)
        if resume["step"] != prior_metrics["step"] or resume["rows_done"] != prior_metrics["rows_done"]:
            raise ValueError("resume tensor state/metrics disagreement")
        coherent = optimizer_coherence(resume["optimizer"], prior_metrics["step"])
        state, prefix = rebuild_acknowledged_state(args.resume_successful_ids,
            resume["successful_ids_log_bytes"], prior_metrics, rows, resume["cursor"])
        optimizer.load_state_dict(resume["optimizer"])
        scaler.load_state_dict(resume["scaler"])
        atomic_bytes(out / "successful_ids.jsonl", prefix)
        ids_path = out / "successful_ids.jsonl"
        atomic_json(out / "resume_validation.json", {"coherence": coherent,
            "source_generation_manifest_sha256": cfg["resume_generation_manifest_sha256"],
            "acknowledged_log_prefix_sha256": digest(prefix), "acknowledged_log_prefix_bytes": len(prefix),
            "step": state["step"], "rows_done": state["rows_done"], "prior_training_consumed_seconds": prior_consumed})
        epoch, batch_cursor = resume["cursor"]["epoch"], resume["cursor"]["next_microbatch"]
        batches = make_length_batches(rows, epoch)
        if batch_cursor == len(batches):
            epoch += 1
            batch_cursor = 0
            batches = make_length_batches(rows, epoch)
        torch.set_rng_state(resume["torch_cpu_rng"])
        torch.cuda.set_rng_state_all(resume["torch_cuda_rng"])
        random.setstate(resume["python_rng"])
        next_ids = [i for batch in batches[batch_cursor:batch_cursor + ACCUMULATION] for i in batch]
        physical, tuning = measure_physical_batches(model, tokenizer, rows, next_ids, optimizer, scaler, TRAIN_STOP_UNIX)
        atomic_json(out / "physical_batch_tuning.json", tuning)
        cfg.update(microbatch=physical, grad_accumulation=EFFECTIVE_BATCH // physical,
                   physical_batch_tuning=tuning, ordering="Original micro2 shuffled groups-of16 retained")
        # Offline/setup/benchmark time is excluded from consumed train seconds.
        segment_start = time.monotonic()
        segment_start_unix = time.time()
        train_start = segment_start - prior_consumed
        replanned_remaining = max(0.0, TRAIN_STOP_UNIX - segment_start_unix)
        prior_lr = float(prior_metrics["last_lr"])
        clock = {"segment_begin_unix": segment_start_unix, "segment_begin_monotonic": segment_start,
                 "prior_training_consumed_seconds": prior_consumed, "budget_scope": BUDGET_SCOPE,
                 "deadline_unix": TRAIN_STOP_UNIX, "hard_deadline_unix": HARD_DEADLINE_UNIX,
                 "deadline_monotonic": segment_start + replanned_remaining,
                 "offline_time_excluded": True}
        cfg["clock"] = clock
        cfg["scheduler"] = {"type": "continue_remaining_warmup_then_replanned_cosine",
            "prior_elapsed_seconds": prior_consumed, "prior_lr": prior_lr,
            "segment_remaining_seconds": replanned_remaining, "floor_lr": MIN_LR,
            "warmup_restarted": False}
        atomic_json(out / "run_config.json", cfg)
        atomic_json(out / "progress.json", {"state": "RESUMED_OPTIMIZER_GROUP_BEGIN", "step": state["step"],
            "rows_done": state["rows_done"], "training_started": True, "clock": clock, "config": cfg})
''' + source[end:]
replace('            while group_may_start(time.monotonic(), train_start):', '            while time.time() < TRAIN_STOP_UNIX and time.monotonic() < clock["deadline_monotonic"]:')
replace('                group_rows = len(group_ids)', '''                group_rows = len(group_ids)
                physical_group = regroup_same16(group_ids, rows, physical)''')
replace('                if elapsed_at_entry >= TRAIN_SECONDS:\n                    break\n                lr = lr_at_elapsed(elapsed_at_entry)', '''                if time.time() >= TRAIN_STOP_UNIX or time.monotonic() >= clock["deadline_monotonic"]:
                    break
                lr = replan_lr(elapsed_at_entry, prior_consumed, replanned_remaining, prior_lr)''')
replace('                        for indices in group:', '                        for indices in physical_group:')
replace('                if not group_may_start(time.monotonic(), train_start):', '                if time.time() >= TRAIN_STOP_UNIX or time.monotonic() >= clock["deadline_monotonic"]:')
replace('            try:\n                save_generation(model, tokenizer, optimizer, scaler, out, cfg, metrics,', '''            try:
                optimizer_coherence(optimizer.state_dict(), state["step"])
                save_generation(model, tokenizer, optimizer, scaler, out, cfg, metrics,''')
replace('        metrics["stop_reason"] = "FIVE_HOUR_WALL_DEADLINE_AT_GROUP_BOUNDARY"', '''        metrics["stop_reason"] = "OWNER_REVISED_ABSOLUTE_TRAIN_CUTOFF_AT_GROUP_BOUNDARY"
        metrics["budget_scope"] = BUDGET_SCOPE
        metrics["prior_training_consumed_seconds"] = prior_consumed
        metrics["current_segment_training_wall_seconds"] = train_stop - segment_start
        metrics["hard_deadline_unix"] = HARD_DEADLINE_UNIX
        metrics["train_stop_unix"] = TRAIN_STOP_UNIX
        metrics["deadline_boundary_overrun_seconds"] = max(0.0, time.time() - TRAIN_STOP_UNIX)''')
replace('        metrics["full_requested_training_window_reached"] = metrics["training_wall_seconds"] >= TRAIN_SECONDS', '''        metrics["full_requested_training_window_reached"] = False
        metrics["revised_training_cutoff_reached"] = time.time() >= TRAIN_STOP_UNIX
        optimizer_coherence(optimizer.state_dict(), state["step"])''')
replace('        after = generate_fixtures(model, tokenizer, fixtures, out, "adapter_after_training",\n                     contract, contract_sha, args.eval_timeout_seconds, FastLanguageModel)', '''        remaining_eval = min(args.eval_timeout_seconds, HARD_DEADLINE_UNIX - time.time() - 45)
        if remaining_eval <= 0:
            raise TimeoutError("hard deadline reserve exhausted after safe adapter export")
        after = generate_fixtures(model, tokenizer, fixtures, out, "adapter_after_training",
                     contract, contract_sha, remaining_eval, FastLanguageModel)
        if time.time() >= HARD_DEADLINE_UNIX:
            raise TimeoutError("revised owner hard deadline exceeded; adapter preserved")''')
replace('"schema": "MathVisionKid.corrective5h.complete.v1"', '"schema": "MathVisionKid.corrective_optimized_v2.complete.v1"')
replace('                    "requested_training_wall_seconds": TRAIN_SECONDS,', '''                    "requested_training_wall_seconds": None,
                    "budget_scope": BUDGET_SCOPE, "hard_deadline_unix": HARD_DEADLINE_UNIX,
                    "hard_deadline_utc": "2026-10-24T05:28:23Z", "train_stop_unix": TRAIN_STOP_UNIX,
                    "train_stop_utc": "2026-10-24T05:13:23Z", "reserve_seconds": RESERVE_SECONDS,
                    "budget_satisfied": time.time() < HARD_DEADLINE_UNIX,
                    "revised_training_cutoff_reached": metrics["revised_training_cutoff_reached"],
                    "prior_training_consumed_seconds": prior_consumed,
                    "current_segment_training_wall_seconds": metrics["current_segment_training_wall_seconds"],''')
replace('                       "adapter_generations.jsonl", "adapter_export.zip"]', '                       "adapter_generations.jsonl", "adapter_export.zip", "resume_validation.json", "physical_batch_tuning.json"]')
replace('              "automatic_resume_implemented": False,', '              "automatic_resume_implemented": True,')
replace('              "resume_note": "Checkpoint contains optimizer/scaler/RNG/cursor, but automatic resume is not implemented.",', '              "resume_note": "Explicit v2 resume requires coherent optimizer state, hash-bound generation and acknowledged log prefix.",')
replace('    """Time scheduler sampled at group entry, with a fixed 900-second warmup."""', '    """Original scheduler retained for provenance; production v2 uses replan_lr."""')
(root / 'corrective_worker_optimized_v2.py').write_text(source, encoding='utf-8')
print('Built corrective_worker_optimized_v2.py without modifying original worker.')
