"""One-time diagnostic of immutable update-one weights on existing dev30.

No locked-test access, optimizer loading, training, gate/selection mutation, or
fresh baseline generation. Reuses verified shared evaluation primitives.
"""
import argparse
import importlib.util
import json
import math
import os
from pathlib import Path
import random
import sys
import threading
import time
import traceback

FINAL_HELPER_SHA256 = '5d8d7e89e0a31615db2820c99f4074038ea827b0303c94a3685c9517f2380b3e'
PRIMITIVES_SHA256 = 'd5f4f0bc2df2b9ff8b2999d607f7ab0b773a76e2ececd4cf48bada99ffcc787c'
DEV_SHA256 = '75eab78085830aa5bf0cf856eb6f70d2630e2407c8143409816dec94d849aaed'


def sha(path):
    import hashlib
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for data in iter(lambda: stream.read(4 * 1024 * 1024), b''):
            h.update(data)
    return h.hexdigest()


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def assert_training_exited(root, proc_root=Path('/proc'), own_pid=None):
    """Fail closed while any worker for this exact root still exists."""
    own_pid = os.getpid() if own_pid is None else own_pid
    if not proc_root.is_dir():
        raise RuntimeError('Linux process evidence is required before probing')
    for item in proc_root.iterdir():
        if not item.name.isdecimal() or int(item.name) == own_pid:
            continue
        try:
            args = [x.decode('utf-8', errors='replace') for x in (item / 'cmdline').read_bytes().split(b'\0') if x]
        except FileNotFoundError:
            continue
        if any(Path(arg).name == 'recovery_worker.py' for arg in args):
            if '--root' in args and args.index('--root') + 1 < len(args) and Path(args[args.index('--root') + 1]).resolve() == root.resolve():
                raise RuntimeError('Training worker still exists for this root')


def choose_step1(out, verify):
    generations = [p for p in out.glob('generation_step_000001_rows_*') if p.is_dir() and not p.name.endswith('.pending')]
    if len(generations) != 1:
        raise ValueError('Step-one checkpoint is missing or ambiguous')
    generation = generations[0]
    manifest = verify(generation)
    if manifest.get('step') != 1 or manifest.get('rows_done') != 16:
        raise ValueError('Expected the immutable first complete sixteen-row update')
    return generation, manifest


def probe_bindings(base_binding, manifest_sha, adapter_output_sha):
    required = {'dev_sha256', 'contract_sha256', 'source_plan_sha256', 'base_output_sha256', 'fixture_ids'}
    if set(base_binding) != required or len(base_binding['fixture_ids']) != 30 or len(set(base_binding['fixture_ids'])) != 30:
        raise ValueError('Baseline bindings must name exactly30 unique development fixtures')
    return {**base_binding, 'generation_manifest_sha256': manifest_sha,
            'final_stage': True, 'adapter_output_sha256': adapter_output_sha}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    helper_path = root / 'final_evaluation_worker.py'
    if sha(helper_path) != FINAL_HELPER_SHA256:
        raise ValueError('Shared evaluation helper hash mismatch')
    F = load(helper_path, 'probe_verified_final_helpers')
    scope = F.read(root / 'owner_run_scope.json')
    deadline = min(time.time() + 900, float(scope['hard_deadline_unix']) - 600)
    F.remaining(deadline)
    assert_training_exited(root)
    out = root / 'training'
    evaldir = out / 'eval_step_000001'
    F.reserve_attempt(evaldir)
    started = time.time()
    def watchdog():
        try:
            F.atomic(evaldir / 'probe_error.json', {'state': 'WATCHDOG_TIMEOUT', 'deadline_unix': deadline,
                     'rerun_allowed': False, 'training_performed': False})
        finally:
            os._exit(124)
    timer = threading.Timer(F.remaining(deadline), watchdog)
    timer.daemon = True
    timer.start()
    try:
        cfg = F.read(out / 'run_config.json')
        if cfg.get('model') != F.MODEL or cfg.get('revision') != F.REVISION or cfg.get('dev_sha256') != DEV_SHA256:
            raise ValueError('Probe model/development pins differ from this run')
        if cfg['hard_deadline_unix'] != scope['hard_deadline_unix'] or scope['dev_sha256'] != DEV_SHA256:
            raise ValueError('Probe owner deadline/development scope differs')
        for name, expected in [('frozen_training_primitives.py', PRIMITIVES_SHA256),
                               ('recovery_worker.py', cfg['worker_sha256']),
                               ('recovery_policy.py', cfg['policy_sha256']),
                               ('derived_sampling_plan.json', cfg['source_plan_sha256']),
                               ('new_validation_candidates.jsonl', DEV_SHA256)]:
            if sha(root / name) != expected:
                raise ValueError('Probe frozen source binding differs: ' + name)
        packages = F.check_environment(root)
        sys.path.insert(0, str(root))
        policy = load(root / 'recovery_policy.py', 'recovery_policy')
        R = load(root / 'recovery_worker.py', 'probe_verified_recovery_worker')
        H = load(root / 'frozen_training_primitives.py', 'probe_frozen_primitives')
        generation, manifest = choose_step1(out, F.verify_generation)
        cp_cfg = F.read(generation / 'run_config.json')
        for key in ('model', 'revision', 'dev_sha256', 'source_plan_sha256', 'worker_sha256', 'policy_sha256', 'contract_sha256'):
            if cp_cfg.get(key) != cfg.get(key):
                raise ValueError('Step-one checkpoint config differs: ' + key)
        fixtures = F.read_rows(root / 'new_validation_candidates.jsonl')
        if len(fixtures) != 30 or len({f['id'] for f in fixtures}) != 30:
            raise ValueError('Probe requires the same30 development fixtures')
        contract = F.read(out / 'evaluation_contract.json')
        contract_sha = policy.digest(policy.canonical(contract).encode())
        if contract_sha != cfg['contract_sha256'] or contract['fixture_sha256'] != DEV_SHA256 or contract['decoding']['max_new_tokens'] != 1024 or contract['decoding']['do_sample'] is not False or contract['enable_thinking'] is not False:
            raise ValueError('Probe must preserve exact existing greedy/no-thinking dev contract')
        basepath = out / 'eval_step_000000/base_generations.jsonl'
        base_rows = F.read_rows(basepath)
        F.validate_outputs(base_rows, fixtures, contract, contract_sha, 'base_before_training')
        base_binding = {'dev_sha256': DEV_SHA256, 'contract_sha256': contract_sha,
                        'source_plan_sha256': cfg['source_plan_sha256'], 'base_output_sha256': sha(basepath),
                        'fixture_ids': [f['id'] for f in fixtures]}
        if F.read(basepath.parent / 'eval_bindings.json') != base_binding:
            raise ValueError('Original baseline outputs are not exactly bound')
        # Preserve the whole completed selection/gate state, including any STOP gate.
        protected = [out / 'best.json', out / 'run_complete.json', out / 'run_config.json',
                     basepath, basepath.parent / 'eval_bindings.json'] + sorted(out.glob('gate_step_*.json'))
        unchanged = {str(p.relative_to(root)): sha(p) for p in protected if p.exists()}
        absent = [p for p in protected if not p.exists()]
        manifest_sha = sha(generation / 'generation_manifest.json')
        F.atomic(evaldir / 'probe_started.json', {'purpose': 'diagnostic_first_update_vs_later_drift',
                 'step': 1, 'started_unix': started, 'deadline_unix': deadline,
                 'generation': generation.name, 'generation_manifest_sha256': manifest_sha,
                 'base_binding': base_binding, 'selection_state_before_probe': unchanged,
                 'selection_mutation_allowed': False, 'locked_test_access': False})
        from unsloth import FastLanguageModel
        import torch
        from transformers import BitsAndBytesConfig
        from peft import PeftModel, get_peft_model_state_dict
        from peft.utils.save_and_load import load_peft_weights
        if not torch.cuda.is_available() or 't4' not in torch.cuda.get_device_name(0).lower():
            raise RuntimeError('Expected the authorized free T4')
        random.seed(20261024)
        torch.manual_seed(20261024)
        torch.cuda.manual_seed_all(20261024)
        model, tokenizer = FastLanguageModel.from_pretrained(model_name=F.MODEL, revision=F.REVISION,
            use_exact_model_name=True, max_seq_length=2048, dtype=torch.float16, load_in_4bit=True,
            quantization_config=BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type='nf4',
                bnb_4bit_compute_dtype=torch.float16, bnb_4bit_use_double_quant=True), attn_implementation='sdpa')
        if getattr(model.config, '_commit_hash', None) != F.REVISION or tokenizer.eos_token_id != 151645 or tokenizer.convert_tokens_to_ids('<|im_end|>') != 151645:
            raise ValueError('Probe fresh base identity/tokenizer differs')
        H.FIXTURES_SHA256, H.MAX_NEW_TOKENS = DEV_SHA256, 1024
        actual_contract, actual_sha = H.eval_contract(fixtures, tokenizer)
        if actual_contract != contract or actual_sha != contract_sha:
            raise ValueError('Actual probe tokenized prompts differ from existing dev contract')
        model = PeftModel.from_pretrained(model, str(generation), is_trainable=False)
        expected = load_peft_weights(str(generation), device='cpu')
        actual = get_peft_model_state_dict(model)
        if set(actual) != set(expected):
            raise ValueError('Loaded step-one adapter key set differs')
        for key, tensor in actual.items():
            wanted = expected[key].to(device='cpu', dtype=tensor.dtype)
            if tensor.shape != wanted.shape or not torch.equal(tensor.detach().cpu(), wanted):
                raise ValueError('Loaded step-one adapter tensor differs')
        del actual, expected
        class InferenceOnly:
            @staticmethod
            def for_inference(target):
                return FastLanguageModel.for_inference(target)
            @staticmethod
            def for_training(target):
                return FastLanguageModel.for_inference(target)
        outputs = H.generate_fixtures(model, tokenizer, fixtures, evaldir, 'adapter_after_training',
                                     contract, contract_sha, F.remaining(deadline), InferenceOnly)
        F.validate_outputs(outputs, fixtures, contract, contract_sha, 'adapter_after_training')
        for relative, digest in unchanged.items():
            if sha(root / relative) != digest:
                raise ValueError('Selection/gate/baseline evidence changed during probe')
        if any(path.exists() for path in absent):
            raise ValueError('Probe requires exclusive stopped-worker selection state')
        if sha(generation / 'generation_manifest.json') != manifest_sha:
            raise ValueError('Immutable step-one checkpoint changed during probe')
        proof = probe_bindings(base_binding, manifest_sha, sha(evaldir / 'adapter_generations.jsonl'))
        F.atomic(evaldir / 'eval_bindings.json', proof)
        R.verify_eval_evidence(evaldir, {k: v for k, v in proof.items() if k != 'adapter_output_sha256'}, fixtures, contract)
        F.remaining(deadline)
        F.atomic(evaldir / 'probe_complete.json', {'complete': True, 'diagnostic_only': True, 'step': 1,
                 'generation': generation.name, 'checkpoint_metrics_sha256': sha(generation / 'metrics.json'),
                 'bindings': proof, 'adapter_outputs': 30, 'base_reused_without_generation': True,
                 'packages': packages, 'completed_unix': time.time(), 'deadline_unix': deadline,
                 'selection_changed': False, 'gate_written': False, 'locked_test_access': False,
                 'optimizer_loaded': False, 'training_performed': False, 'semantic_review_pending': True})
        print(policy.canonical({'state': 'STEP1_DEV_PROBE_COMPLETE', 'adapter_outputs': 30,
                               'bindings_sha256': sha(evaldir / 'eval_bindings.json'),
                               'semantic_review_pending': True}), flush=True)
    except BaseException as exc:
        F.atomic(evaldir / 'probe_error.json', {'complete': False, 'type': type(exc).__name__,
                 'error': str(exc), 'traceback': traceback.format_exc(), 'rerun_allowed': False,
                 'selection_changed': False, 'training_performed': False, 'locked_test_access': False})
        raise
    finally:
        timer.cancel()


if __name__ == '__main__':
    main()
