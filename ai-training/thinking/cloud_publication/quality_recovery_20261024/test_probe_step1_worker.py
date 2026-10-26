"""CPU-only first-update probe safety tests; no model/network/locked content."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('step1_probe', Path(__file__).with_name('probe_step1_worker.py'))
P = importlib.util.module_from_spec(spec)
spec.loader.exec_module(P)


class StepOneProbeTests(unittest.TestCase):
    def test_exact_worker_compatible_bindings(self):
        base = {'dev_sha256': 'a' * 64, 'contract_sha256': 'b' * 64,
                'source_plan_sha256': 'c' * 64, 'base_output_sha256': 'd' * 64,
                'fixture_ids': [str(i) for i in range(30)]}
        proof = P.probe_bindings(base, 'e' * 64, 'f' * 64)
        self.assertEqual(set(proof), set(base) | {'generation_manifest_sha256', 'final_stage', 'adapter_output_sha256'})
        self.assertTrue(proof['final_stage'])
        with self.assertRaises(ValueError):
            P.probe_bindings({**base, 'fixture_ids': ['same'] * 30}, 'e' * 64, 'f' * 64)

    def test_live_training_process_blocks_probe(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            proc = root / 'proc'
            pid = proc / '123'
            pid.mkdir(parents=True)
            (pid / 'cmdline').write_bytes(b'python\0/recovery_worker.py\0--root\0' + str(root).encode() + b'\0')
            with self.assertRaises(RuntimeError):
                P.assert_training_exited(root, proc, own_pid=999)
            P.assert_training_exited(root, proc, own_pid=123)
            (pid / 'cmdline').write_bytes(b'python\0/unrelated.py\0')
            P.assert_training_exited(root, proc, own_pid=999)

    def test_step_one_checkpoint_is_unique_complete_group(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            generation = root / 'generation_step_000001_rows_00000016'
            generation.mkdir()
            path, manifest = P.choose_step1(root, lambda g: {'step': 1, 'rows_done': 16})
            self.assertEqual(path, generation)
            with self.assertRaises(ValueError):
                P.choose_step1(root, lambda g: {'step': 1, 'rows_done': 15})
            (root / 'generation_step_000001_rows_00000032').mkdir()
            with self.assertRaises(ValueError):
                P.choose_step1(root, lambda g: {'step': 1, 'rows_done': 16})


if __name__ == '__main__':
    unittest.main()
