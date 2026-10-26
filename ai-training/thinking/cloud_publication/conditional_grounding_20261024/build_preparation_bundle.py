"""Bounded code and evidence bundle; no corpus, model or protected tests."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import subprocess
import sys
import unittest
import zipfile

P = Path(__file__).resolve().parent
OLD = P.parent / 'skill_recovery_150m_20261024'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    suite = unittest.defaultTestLoader.discover(str(P), pattern='test_*.py')
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    if not result.wasSuccessful() or result.testsRun != 19:
        raise ValueError('All 19 bounded CPU tests must pass')
    subprocess.run([sys.executable, '-X', 'utf8', str(P/'prepare_conditional_samples.py')], check=True)
    preflight = json.loads((P/'conditional_sample_preflight.json').read_bytes())
    audit = json.loads((P/'archived_dev_claim_audit.json').read_bytes())
    if audit['checker_sha256'] != sha((P/'exact_math_audit.py').read_bytes()):
        raise ValueError('Archived audit checker pin differs')
    from collections import Counter
    counts = Counter()
    for row in audit['records']:
        counts.update(row['claim_counts'])
    report = {
        'schema': 'MathVisionKid.conditional_grounding_preparation.v1',
        'phase': 'CPU_PREPARATION_COMPLETE_COLAB_CONNECTION_REQUIRED',
        'observed_utc': datetime.now(timezone.utc).isoformat(),
        'requested_chrome_profile': 'Duy Mạnh 1 / Profile 7',
        'notebook_id': '1TeCoP57miKmhESZVKWFqD-XqZmQd5u4l',
        'colab_mcp_connected_at_last_check': False,
        'kernel_or_gpu_live_status': 'unknown_since_MCP_disconnected',
        'new_model_calls': 0, 'new_optimizer_updates': 0,
        'previous_run_workers_last_verified_exited_utc': '2026-10-24T14:24:40Z',
        'previous_run_checkpoint_and_adapter_promoted': False,
        'cpu_tests_run': result.testsRun, 'cpu_tests_passed': True,
        'sanity_projection_samples': preflight['sample_count'],
        'worked_prompt_suffix_changes': preflight['worked_prompt_suffix_changes'],
        'hint_prompts_and_all_targets_unchanged': True,
        'raw_source_hashes_inherited_not_reverified': True,
        'full_16000_training_projection_built': False,
        'archived_development_responses_audited': len(audit['records']),
        'explicit_relation_counts': dict(counts),
        'relation_counts_are_answer_accuracy': False,
        'arithmetic_checker_rewrites_outputs': False,
        'model_improvement_established': False,
        'corpus_labels_history_and_checkpoints_preserved': True,
        'new_human_review_claimed': False,
        'production_changes': False, 'paid_resources': False,
        'drive_folder_id': '1f5CrIUPOYjmyhKJpOcNkXi0Ap-nzXuYK',
        'connection_blockers': ['Chrome launch rejected by automatic approval; no detailed reason supplied',
                                'Computer-use reports Local browser use is disabled in Work settings'],
        'next_steps': ['User opens the notebook in requested profile and connects MCP',
                       'Verify actual runtime/account/T4 before executing any model call',
                       'Use archived development only to compare the conditional prompt against pinned base',
                       'Keep final tests sealed until a candidate passes the predeclared quality gate',
                       'Only consider another SFT run after validating inputs, target masks and source quality'],
        'skills_applied': ['computer-use', 'google-drive:google-drive'],
    }
    (P/'phase_report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
    names = ['conditional_behavior_renderer.py', 'conditional_inference_contract.py',
             'exact_math_audit.py', 'prepare_conditional_samples.py',
             'test_conditional_behavior_renderer.py', 'test_conditional_inference_contract.py',
             'test_exact_math_audit.py', 'archived_dev_claim_audit.json',
             'conditional_sample_preflight.json', 'conditional_samples.jsonl',
             'phase_report.json', 'build_preparation_bundle.py']
    files = {P.name+'/'+name: P/name for name in names}
    for name in ['behavior_renderer.py', 'projection_preflight.json', 'source_behavior_samples.json']:
        files[OLD.name+'/'+name] = OLD/name
    target = P.parent/'verbal_recovery_20261024/verbal_training_renderer_v3.py'
    files['verbal_recovery_20261024/verbal_training_renderer_v3.py'] = target
    contents = {}
    for name, path in files.items():
        data = path.read_bytes()
        if len(data) > 2*1024*1024:
            raise ValueError('Only explicitly bounded code/evidence allowed')
        contents[name] = data
    manifest = {name: {'bytes': len(data), 'sha256': sha(data)} for name, data in contents.items()}
    manifest_data = (json.dumps({'schema': 'MathVisionKid.code_evidence_manifest.v1',
        'files': manifest, 'corpus_or_weights_included': False}, ensure_ascii=False, indent=2)+'\n').encode()
    (P/'bundle_manifest.json').write_bytes(manifest_data)
    contents[P.name+'/bundle_manifest.json'] = manifest_data
    path = P/'MathVisionKid_conditional_grounding_PREPARATION.zip'
    if path.exists():
        raise FileExistsError('Keep immutable bundle; do not rebuild an existing publication')
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as output:
        for name, data in sorted(contents.items()):
            info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            output.writestr(info, data)
    with zipfile.ZipFile(path) as check:
        if check.testzip() is not None or any(check.read(n) != d for n, d in contents.items()):
            raise ValueError('Archive readback failed')
    proof = {'path': str(path), 'bytes': path.stat().st_size, 'sha256': sha(path.read_bytes()),
             'members': len(contents), 'local_archive_readback_verified': True}
    (P/'bundle_local_proof.json').write_text(json.dumps(proof, indent=2)+'\n', encoding='utf8')
    print(json.dumps(proof))


if __name__ == '__main__':
    main()
