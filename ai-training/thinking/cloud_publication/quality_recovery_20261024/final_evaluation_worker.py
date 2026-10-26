"""One-time post-selection locked evaluation. Importing has no model/network I/O.

Run only in the frozen recovery venv after training/run_complete.json exists.
No training, optimizer deserialization, best-pointer update, or model selection
is performed. A pre-inference exclusive marker prevents accidental test reruns.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import importlib.util
import json
import math
import os
from pathlib import Path, PurePosixPath
import random
import sys
import threading
import time
import traceback

MODEL = 'Qwen/Qwen3-1.7B'
REVISION = '70d244cc86ccca08cf5af4e1e306ecf908b1ad5e'
PRIMITIVES_SHA256 = 'd5f4f0bc2df2b9ff8b2999d607f7ab0b773a76e2ececd4cf48bada99ffcc787c'
LOCKED_SHA256 = '41413ac3e61e7180cee53d06ccec6186256f1cfdf845557a6a598822f6ca22d0'
DEV_SHA256 = '75eab78085830aa5bf0cf856eb6f70d2630e2407c8143409816dec94d849aaed'
SCHEMA = 'MathVisionKid.quality_recovery_locked_final_eval.v1'


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(4 * 1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def strict_json(raw):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('Duplicate JSON key: ' + key)
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=unique)


def read(path):
    return strict_json(Path(path).read_bytes())


def read_rows(path):
    return [strict_json(line) for line in Path(path).read_text('utf-8').splitlines() if line.strip()]


def atomic(path, value):
    path = Path(path)
    temp = path.with_name(path.name + '.pending')
    with temp.open('w', encoding='utf-8') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n')
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temp, path)


def inside(parent, relative):
    rel = PurePosixPath(relative)
    if not relative or rel.is_absolute() or '..' in rel.parts or '\\' in relative:
        raise ValueError('Unsafe evidence path')
    path = Path(parent).joinpath(*rel.parts)
    if path.is_symlink() or not path.resolve().is_relative_to(Path(parent).resolve()):
        raise ValueError('Evidence path escapes its run')
    return path


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def remaining(deadline, clock=time.time):
    value = deadline - clock()
    if value <= 0:
        raise TimeoutError('One-time final evaluation budget exhausted')
    return value


def reserve_attempt(final):
    Path(final).mkdir(exist_ok=False)


def check_environment(root):
    if Path(sys.prefix).resolve() != (root / 'venv').resolve():
        raise ValueError('Use this run\'s exact venv/bin/python')
    pinned = {'torch': '2.11.0', 'transformers': '5.16.1', 'unsloth': '2026.10.7',
              'unsloth_zoo': '2026.10.7', 'peft': '0.21.2',
              'accelerate': '1.15.0', 'bitsandbytes': '0.50.2'}
    actual = {name: importlib.metadata.version(name) for name in pinned}
    if any(actual[name].split('+')[0] != value for name, value in pinned.items()):
        raise ValueError('Inference environment differs from pinned recovery packages')
    installed = read(root / 'install_status.json')['versions']['packages']
    if any(actual[name] != installed[name] for name in pinned):
        raise ValueError('Inference packages differ from actual install receipt')
    return actual


def verify_generation(generation):
    manifest = read(generation / 'generation_manifest.json')
    if manifest.get('complete') is not True or not manifest.get('files'):
        raise ValueError('Incomplete checkpoint')
    for name, digest in manifest['files'].items():
        file = inside(generation, name)
        if sha(file) != digest or file.stat().st_size != manifest['file_bytes'][name]:
            raise ValueError('Checkpoint member hash/bytes mismatch')
    # resume_state.pt is integrity-hashed only, never loaded/deserialized.
    return manifest


def verify_selection(root, R, policy, fixtures, cfg, complete, best):
    """Revalidate selection solely from existing dev evidence, never locked results."""
    out = root / 'training'
    if complete.get('complete') is not True or complete.get('best') != best:
        raise ValueError('Run completion does not bind current best selection')
    if best.get('semantic_review_pending') is not False:
        raise ValueError('Selection semantic review is incomplete')
    if complete.get('budget_satisfied') is not True or complete.get('hard_deadline_unix') != cfg['hard_deadline_unix']:
        raise ValueError('Run completion budget binding differs')
    if not isinstance(complete.get('completed_unix'), (int, float)) or complete['completed_unix'] >= cfg['hard_deadline_unix']:
        raise ValueError('Training completion exceeds its authorized deadline')
    contract = read(out / 'evaluation_contract.json')
    csha = hashlib.sha256(canonical(contract).encode()).hexdigest()
    if cfg.get('contract_sha256') != csha or contract.get('fixture_sha256') != DEV_SHA256:
        raise ValueError('Development contract differs from configuration')
    base_dir = out / 'eval_step_000000'
    base_path = base_dir / 'base_generations.jsonl'
    base_rows = read_rows(base_path)
    baseline_binding = {'dev_sha256': DEV_SHA256, 'contract_sha256': csha,
        'source_plan_sha256': cfg['source_plan_sha256'], 'base_output_sha256': sha(base_path),
        'fixture_ids': [f['id'] for f in fixtures]}
    if read(base_dir / 'eval_bindings.json') != baseline_binding:
        raise ValueError('Development baseline evidence differs')
    validate_outputs(base_rows, fixtures, contract, csha, 'base_before_training')
    baseline = {'kind': 'untrained_base', 'model': MODEL, 'revision': REVISION,
                'validation_output_sha256': sha(base_path), 'production_approval': False}
    replay = dict(baseline)
    proofs = []
    gates = sorted(out.glob('gate_step_*.json'), key=lambda p: read(p)['step'])
    if not gates:
        raise ValueError('No reviewed development gate establishes final selection')
    profile = read(out / 'base_review_profile.json')
    for gate_path in gates:
        gate = read(gate_path)
        step = gate.get('step')
        if type(step) is not int or step < 0:
            raise ValueError('Invalid gate step')
        eval_dir = out / f'eval_step_{step:06d}'
        bindings = read(eval_dir / 'eval_bindings.json')
        for key, value in baseline_binding.items():
            if bindings.get(key) != value:
                raise ValueError('Gate does not bind the frozen development baseline')
        R.verify_eval_evidence(eval_dir, {k: v for k, v in bindings.items() if k != 'adapter_output_sha256'}, fixtures, contract)
        R.validate_review_metadata(gate['decisions'], fixtures)
        R.validate_review_completion(gate['decisions'], base_rows, read_rows(eval_dir / 'adapter_generations.jsonl'))
        policy.validate_gate(gate, step, bindings)
        expected_profile = {'base_output_sha256': baseline_binding['base_output_sha256'],
                            'dev_sha256': DEV_SHA256, 'profile': R.baseline_profile(gate['decisions'])}
        if profile != expected_profile:
            raise ValueError('Baseline judgments changed across gates')
        generations = [p for p in out.glob(f'generation_step_{step:06d}_rows_*')
                       if p.is_dir() and not p.name.endswith('.pending')]
        if len(generations) != 1:
            raise ValueError('Gate has missing/ambiguous checkpoint generation')
        generation = generations[0]
        manifest = verify_generation(generation)
        if manifest['step'] != step or sha(generation / 'generation_manifest.json') != bindings['generation_manifest_sha256']:
            raise ValueError('Gate checkpoint manifest differs')
        candidate = {'kind': 'trained_adapter', 'generation': generation.name,
                     'manifest_sha256': bindings['generation_manifest_sha256'],
                     'gate_file': gate_path.name, 'gate_sha256': sha(gate_path), 'step': step,
                     'bindings': bindings, 'production_approval': False}
        replay = R.choose_best(replay, policy.summarize_decisions(gate['decisions']), candidate, baseline)
        proofs.append({'step': step, 'gate_file': gate_path.name, 'gate_sha256': sha(gate_path),
                       'generation': generation.name, 'manifest_sha256': sha(generation / 'generation_manifest.json')})
    if replay != best:
        raise ValueError('Best pointer differs from replay of reviewed development selection')
    selected = complete.get('selected_artifact', {})
    if selected.get('kind') != best['kind'] or selected.get('selection_evidence') != best:
        raise ValueError('Selected artifact does not bind selected best evidence')
    if best['kind'] == 'trained_adapter':
        if selected.get('generation') != best['generation']:
            raise ValueError('Selected artifact generation differs')
        archive = inside(out, selected['path'])
        if sha(archive) != selected['sha256'] or archive.stat().st_size != selected['bytes']:
            raise ValueError('Selected adapter export bytes differ')
    elif best['kind'] != 'untrained_base' or selected.get('model') != MODEL or selected.get('revision') != REVISION or selected.get('adapter') is not None:
        raise ValueError('Unknown selected artifact kind/base identity')
    return {'gate_proofs': proofs, 'selected_kind': best['kind'], 'selected_best': best,
            'selected_artifact': selected, 'dev_base_output_sha256': sha(base_path)}


def validate_outputs(rows, fixtures, contract, contract_sha, stage):
    if [r.get('fixture_id') for r in rows] != [f['id'] for f in fixtures]:
        raise ValueError('Generated fixture count/order differs')
    for row, fixture in zip(rows, fixtures):
        if (row.get('grade') != fixture['grade'] or row.get('mode') != fixture['mode']
                or row.get('stage') != stage or row.get('contract_sha256') != contract_sha
                or row.get('prompt_token_sha256') != contract['prompt_token_sha256'][fixture['id']]
                or row.get('max_new_tokens') != 1024 or not isinstance(row.get('output'), str)):
            raise ValueError('Generated row does not match exact evaluation contract')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    scope = read(root / 'owner_run_scope.json')
    hard_deadline = float(scope['hard_deadline_unix'])
    if not math.isfinite(hard_deadline):
        raise ValueError('Nonfinite owner deadline')
    end = min(time.time() + 900, hard_deadline - 300)
    remaining(end)
    final = root / 'final_eval'
    # mkdir is exclusive; even partial/error attempts cannot silently be rerun.
    reserve_attempt(final)
    started = time.time()
    def watchdog():
        try:
            atomic(final / 'error.json', {'schema': SCHEMA, 'state': 'WATCHDOG_TIMEOUT',
                   'attempt_started_unix': started, 'deadline_unix': end, 'rerun_allowed': False})
        finally:
            os._exit(124)
    timer = threading.Timer(remaining(end), watchdog)
    timer.daemon = True
    timer.start()
    unchanged = {}
    try:
        atomic(final / 'attempt_started.json', {'schema': SCHEMA, 'started_unix': started,
               'deadline_unix': end, 'budget_seconds': end - started,
               'locked_test_sha256': LOCKED_SHA256, 'run_once': True, 'selection_change_allowed': False})
        for name in ('training/run_complete.json', 'training/best.json', 'training/run_config.json',
                     'owner_run_scope.json', 'locked_test_candidates.jsonl', 'new_validation_candidates.jsonl',
                     'derived_sampling_plan.json', 'recovery_worker.py', 'recovery_policy.py', 'frozen_training_primitives.py'):
            unchanged[name] = sha(root / name)
        complete, best, cfg = read(root / 'training/run_complete.json'), read(root / 'training/best.json'), read(root / 'training/run_config.json')
        if cfg.get('model') != MODEL or cfg.get('revision') != REVISION or cfg.get('dev_sha256') != DEV_SHA256:
            raise ValueError('Recovery configuration model/development pins differ')
        if cfg.get('hard_deadline_unix') != hard_deadline or scope.get('locked_test_sha256') != LOCKED_SHA256 or scope.get('dev_sha256') != DEV_SHA256:
            raise ValueError('Owner scope does not bind frozen locked/development fixtures')
        if unchanged['locked_test_candidates.jsonl'] != LOCKED_SHA256 or unchanged['new_validation_candidates.jsonl'] != DEV_SHA256:
            raise ValueError('Frozen fixture bytes differ')
        if unchanged['frozen_training_primitives.py'] != PRIMITIVES_SHA256 or cfg.get('worker_sha256') != unchanged['recovery_worker.py'] or cfg.get('policy_sha256') != unchanged['recovery_policy.py'] or cfg.get('source_plan_sha256') != unchanged['derived_sampling_plan.json']:
            raise ValueError('Recovery worker/policy/primitive/sampling-plan hash mismatch')
        packages = check_environment(root)
        sys.path.insert(0, str(root))
        policy = load(root / 'recovery_policy.py', 'recovery_policy')
        R = load(root / 'recovery_worker.py', 'final_eval_verified_recovery_worker')
        H = load(root / 'frozen_training_primitives.py', 'final_eval_frozen_primitives')
        fixtures, dev = read_rows(root / 'locked_test_candidates.jsonl'), read_rows(root / 'new_validation_candidates.jsonl')
        if len(fixtures) != 20 or len({f['id'] for f in fixtures}) != 20 or len(dev) != 30:
            raise ValueError('Frozen fixture count/IDs differ')
        selection = verify_selection(root, R, policy, dev, cfg, complete, best)
        raw_train = root / 'training_view.jsonl'
        if sha(raw_train) != H.VIEW_SHA256 or cfg['source_view_sha256'] != H.VIEW_SHA256:
            raise ValueError('Collision screening source differs from frozen selected training view')
        train = read_rows(raw_train)
        if len(train) != 16000:
            raise ValueError('Expected exactly 16000 preserved source training rows')
        train_screen = policy.screen_fixtures(fixtures, train)
        dev_keys = {policy.prompt_key(f['userproblem'], mask) for f in dev for mask in (False, True)}
        dev_collisions = [f['id'] for f in fixtures if any(policy.prompt_key(f['userproblem'], mask) in dev_keys for mask in (False, True))]
        if train_screen['collisions'] or dev_collisions:
            raise ValueError('Locked test collides with selected training/development text')
        atomic(final / 'collision_screening.json', {'selected_train_screen': train_screen,
               'development_exact_or_number_masked_collisions': dev_collisions,
               'full_6502344_row_independence': 'UNPROVEN', 'semantic_independence_claimed': False})
        atomic(final / 'selection_before_test.json', {**selection, 'input_hashes': unchanged,
               'selected_before_locked_inference': True, 'test_results_used_for_selection': False})
        remaining(end)
        from unsloth import FastLanguageModel
        import torch
        from transformers import BitsAndBytesConfig
        if not torch.cuda.is_available() or 't4' not in torch.cuda.get_device_name(0).lower():
            raise RuntimeError('Expected the authorized free T4 inference environment')
        random.seed(20261024)
        torch.manual_seed(20261024)
        torch.cuda.manual_seed_all(20261024)
        model, tokenizer = FastLanguageModel.from_pretrained(model_name=MODEL, revision=REVISION,
            use_exact_model_name=True, max_seq_length=2048, dtype=torch.float16, load_in_4bit=True,
            quantization_config=BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type='nf4',
                bnb_4bit_compute_dtype=torch.float16, bnb_4bit_use_double_quant=True), attn_implementation='sdpa')
        if getattr(model.config, '_commit_hash', None) != REVISION or tokenizer.eos_token_id != 151645 or tokenizer.convert_tokens_to_ids('<|im_end|>') != 151645:
            raise ValueError('Fresh base revision/tokenizer EOT differs')
        H.FIXTURES_SHA256, H.MAX_NEW_TOKENS = LOCKED_SHA256, 1024
        contract, contract_sha = H.eval_contract(fixtures, tokenizer)
        if contract['decoding']['do_sample'] is not False or contract.get('enable_thinking') is not False or contract['fixture_ids'] != [f['id'] for f in fixtures]:
            raise ValueError('Final evaluation contract must remain greedy/no-thinking/exact20')
        atomic(final / 'evaluation_contract.json', {**contract, 'contract_sha256': contract_sha})
        class InferenceOnlyMode:
            @staticmethod
            def for_inference(target):
                return FastLanguageModel.for_inference(target)
            @staticmethod
            def for_training(target):
                # Frozen helper's finally hook must never restore training mode.
                return FastLanguageModel.for_inference(target)
        base_rows = H.generate_fixtures(model, tokenizer, fixtures, final, 'base_before_training', contract, contract_sha, remaining(end), InferenceOnlyMode)
        validate_outputs(base_rows, fixtures, contract, contract_sha, 'base_before_training')
        base_path = final / 'base_generations.jsonl'
        atomic(final / 'base_generation_provenance.json', {'model': MODEL, 'revision': REVISION,
               'fresh_base': True, 'adapter_loaded': False, 'locked_test_sha256': LOCKED_SHA256,
               'contract_sha256': contract_sha, 'output_sha256': sha(base_path), 'output_rows': 20})
        if best['kind'] == 'trained_adapter':
            from peft import PeftModel, get_peft_model_state_dict
            from peft.utils.save_and_load import load_peft_weights
            generation = inside(root / 'training', best['generation'])
            model = PeftModel.from_pretrained(model, str(generation), is_trainable=False)
            expected = load_peft_weights(str(generation), device='cpu')
            actual = get_peft_model_state_dict(model)
            if set(actual) != set(expected):
                raise ValueError('Selected adapter key set differs after inference load')
            for key, tensor in actual.items():
                wanted = expected[key].to(device='cpu', dtype=tensor.dtype)
                if tensor.shape != wanted.shape or not torch.equal(tensor.detach().cpu(), wanted):
                    raise ValueError('Selected adapter tensor differs after inference load')
            del actual, expected
            selected_rows = H.generate_fixtures(model, tokenizer, fixtures, final, 'adapter_after_training', contract, contract_sha, remaining(end), InferenceOnlyMode)
            validate_outputs(selected_rows, fixtures, contract, contract_sha, 'adapter_after_training')
            selected_path = final / 'adapter_generations.jsonl'
            reused = False
        else:
            # Base won before the test. One generated file is both base and selected
            # evidence; do not rerun or manufacture a second adapter evaluation.
            selected_path, selected_rows, reused = base_path, base_rows, True
        atomic(final / 'selected_output_reference.json', {'selected_kind': best['kind'],
               'file': selected_path.name, 'sha256': sha(selected_path), 'output_rows': len(selected_rows),
               'reuses_exact_fresh_base_outputs': reused, 'duplicate_selected_generation_performed': False})
        for name, digest in unchanged.items():
            if sha(root / name) != digest:
                raise ValueError('Selection/config/input evidence changed during final test: ' + name)
        remaining(end)
        files = {p.name: {'sha256': sha(p), 'bytes': p.stat().st_size} for p in final.iterdir()
                 if p.is_file() and not p.name.endswith('.partial.jsonl')}
        atomic(final / 'final_eval_manifest.json', {'schema': SCHEMA, 'complete': True,
               'completed_unix': time.time(), 'deadline_unix': end, 'owner_hard_deadline_unix': hard_deadline,
               'locked_test_sha256': LOCKED_SHA256, 'fixture_count': 20, 'contract_sha256': contract_sha,
               'selected_kind': best['kind'], 'selected_best': best, 'input_hashes': unchanged, 'packages': packages,
               'base_outputs': 20, 'selected_outputs': 20, 'selected_file': selected_path.name,
               'selected_reuses_base_outputs': reused, 'files': files, 'test_run_count': 1,
               'selection_changed': False, 'training_performed': False, 'optimizer_loaded': False,
               'semantic_results_reviewed': False, 'production_approval': False,
               'full_corpus_test_independence': 'UNPROVEN'})
        print(canonical({'state': 'LOCKED_FINAL_EVAL_COMPLETE', 'selected_kind': best['kind'],
                         'base_outputs': 20, 'selected_outputs': 20, 'selected_reuses_base': reused,
                         'manifest_sha256': sha(final / 'final_eval_manifest.json')}), flush=True)
    except BaseException as exc:
        atomic(final / 'error.json', {'schema': SCHEMA, 'state': 'ERROR', 'complete': False,
               'type': type(exc).__name__, 'error': str(exc), 'traceback': traceback.format_exc(),
               'rerun_allowed': False, 'selection_changed': False, 'training_performed': False})
        raise
    finally:
        timer.cancel()


if __name__ == '__main__':
    main()
