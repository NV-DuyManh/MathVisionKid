"""CPU-only contract/evidence tests. No model, locked content, network or GPU."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import recovery_policy as policy
import recovery_worker as R
spec = importlib.util.spec_from_file_location('locked_final_worker', HERE / 'final_evaluation_worker.py')
F = importlib.util.module_from_spec(spec)
spec.loader.exec_module(F)


class FinalEvaluationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='final_eval_contract_cpu_')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.out = self.root / 'training'
        self.out.mkdir()

    def write(self, path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        F.atomic(path, value)

    def rows(self, path, records):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(''.join(F.canonical(r) + '\n' for r in records), encoding='utf-8')

    def scaffold(self, trained):
        fixtures = [{'id': f'synthetic_{i}', 'grade': i // 6 + 1,
                     'mode': 'answer' if i % 6 < 3 else ('hint_no_answer' if i % 6 == 3 else ('student_error' if i % 6 == 4 else 'missing_or_contradictory_info'))} for i in range(30)]
        contract = {'fixture_sha256': F.DEV_SHA256, 'fixture_ids': [x['id'] for x in fixtures],
                    'prompt_token_sha256': {x['id']: 'c' * 64 for x in fixtures},
                    'decoding': {'max_new_tokens': 1024}}
        csha = hashlib.sha256(F.canonical(contract).encode()).hexdigest()
        self.write(self.out / 'evaluation_contract.json', contract)
        def output(f, stage):
            return {'fixture_id': f['id'], 'grade': f['grade'], 'mode': f['mode'], 'stage': stage,
                    'contract_sha256': csha, 'prompt_token_sha256': 'c' * 64,
                    'max_new_tokens': 1024, 'output': 'synthetic fixture output',
                    'ended_eos': True, 'possibly_truncated': False, 'timed_out': False}
        base_dir, eval_dir = self.out / 'eval_step_000000', self.out / 'eval_step_000050'
        base_rows = [output(f, 'base_before_training') for f in fixtures]
        candidate_rows = [output(f, 'adapter_after_training') for f in fixtures]
        self.rows(base_dir / 'base_generations.jsonl', base_rows)
        self.rows(eval_dir / 'adapter_generations.jsonl', candidate_rows)
        baseline_binding = {'dev_sha256': F.DEV_SHA256, 'contract_sha256': csha,
            'source_plan_sha256': 'b' * 64, 'base_output_sha256': F.sha(base_dir / 'base_generations.jsonl'),
            'fixture_ids': [x['id'] for x in fixtures]}
        self.write(base_dir / 'eval_bindings.json', baseline_binding)
        generation = self.out / 'generation_step_000050_rows_00000800'
        generation.mkdir()
        (generation / 'adapter.bin').write_bytes(b'synthetic weights')
        self.write(generation / 'generation_manifest.json', {'complete': True, 'step': 50, 'rows_done': 800,
            'files': {'adapter.bin': F.sha(generation / 'adapter.bin')}, 'file_bytes': {'adapter.bin': (generation / 'adapter.bin').stat().st_size}})
        bindings = {**baseline_binding, 'generation_manifest_sha256': F.sha(generation / 'generation_manifest.json'),
                    'adapter_output_sha256': F.sha(eval_dir / 'adapter_generations.jsonl'), 'final_stage': False}
        self.write(eval_dir / 'eval_bindings.json', bindings)
        decisions = [{'fixture_id': f['id'], 'grade': f['grade'], 'mode': f['mode'],
                      'base_pass': not trained, 'adapter_pass': not trained or i == 0,
                      'base_hint_leak': False, 'adapter_hint_leak': False, 'critical_new_error': False}
                     for i, f in enumerate(fixtures)]
        gate = {**bindings, 'step': 50, 'all_actual_outputs_reviewed': True, 'human_review_claimed': False,
                'decision': 'STOP', 'decisions': decisions}
        gate_path = self.out / 'gate_step_000050.json'
        self.write(gate_path, gate)
        self.write(self.out / 'base_review_profile.json', {'base_output_sha256': baseline_binding['base_output_sha256'],
            'dev_sha256': F.DEV_SHA256, 'profile': R.baseline_profile(decisions)})
        baseline = {'kind': 'untrained_base', 'model': F.MODEL, 'revision': F.REVISION,
                    'validation_output_sha256': baseline_binding['base_output_sha256'], 'production_approval': False}
        candidate = {'kind': 'trained_adapter', 'generation': generation.name,
                     'manifest_sha256': bindings['generation_manifest_sha256'],
                     'gate_file': gate_path.name, 'gate_sha256': F.sha(gate_path), 'step': 50,
                     'bindings': bindings, 'production_approval': False}
        best = R.choose_best(baseline, policy.summarize_decisions(decisions), candidate, baseline)
        selected = {'kind': best['kind'], 'selection_evidence': best}
        if trained:
            archive = self.out / 'selected_adapter_export.zip'
            archive.write_bytes(b'synthetic archive')
            selected.update(generation=generation.name, path=archive.name, sha256=F.sha(archive), bytes=archive.stat().st_size)
        else:
            selected.update(model=F.MODEL, revision=F.REVISION, adapter=None)
        cfg = {'contract_sha256': csha, 'source_plan_sha256': 'b' * 64, 'hard_deadline_unix': 2000}
        complete = {'complete': True, 'best': best, 'selected_artifact': selected,
                    'completed_unix': 1900, 'hard_deadline_unix': 2000, 'budget_satisfied': True}
        return fixtures, cfg, complete, best

    def test_trained_selection_replays_exact_bound_dev_evidence(self):
        fixtures, cfg, complete, best = self.scaffold(True)
        proof = F.verify_selection(self.root, R, policy, fixtures, cfg, complete, best)
        self.assertEqual(proof['selected_kind'], 'trained_adapter')
        self.assertEqual(len(proof['gate_proofs']), 1)

    def test_base_wins_ties_and_remains_selected(self):
        fixtures, cfg, complete, best = self.scaffold(False)
        proof = F.verify_selection(self.root, R, policy, fixtures, cfg, complete, best)
        self.assertEqual(proof['selected_kind'], 'untrained_base')

    def test_selected_archive_corruption_rejected(self):
        fixtures, cfg, complete, best = self.scaffold(True)
        (self.out / 'selected_adapter_export.zip').write_bytes(b'changed')
        with self.assertRaises(ValueError):
            F.verify_selection(self.root, R, policy, fixtures, cfg, complete, best)

    def test_changed_gate_binding_or_baseline_profile_rejected(self):
        fixtures, cfg, complete, best = self.scaffold(True)
        path = self.out / 'gate_step_000050.json'
        gate = F.read(path)
        gate['dev_sha256'] = '0' * 64
        self.write(path, gate)
        with self.assertRaises(ValueError):
            F.verify_selection(self.root, R, policy, fixtures, cfg, complete, best)

    def test_checkpoint_corruption_rejected_without_deserialization(self):
        fixtures, cfg, complete, best = self.scaffold(True)
        (self.out / best['generation'] / 'adapter.bin').write_bytes(b'corrupt')
        with self.assertRaises(ValueError):
            F.verify_selection(self.root, R, policy, fixtures, cfg, complete, best)

    def test_complete_best_mismatch_fails_before_selection(self):
        with self.assertRaises(ValueError):
            F.verify_selection(self.root, R, policy, [], {}, {'complete': True, 'best': {}}, {'kind': 'other'})

    def test_once_marker_and_deadline_fail_closed(self):
        final = self.root / 'final_eval'
        F.reserve_attempt(final)
        with self.assertRaises(FileExistsError):
            F.reserve_attempt(final)
        self.assertEqual(F.remaining(20, lambda: 12), 8)
        with self.assertRaises(TimeoutError):
            F.remaining(20, lambda: 20)

    def test_unsafe_paths_and_duplicate_json_keys_rejected(self):
        for relative in ('../other', '/absolute', 'a\\b'):
            with self.assertRaises(ValueError):
                F.inside(self.root, relative)
        with self.assertRaises(ValueError):
            F.strict_json('{"best":1,"best":2}')


if __name__ == '__main__':
    unittest.main()
