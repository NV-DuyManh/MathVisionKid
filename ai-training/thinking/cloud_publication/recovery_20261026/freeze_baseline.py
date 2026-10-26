from pathlib import Path
import json,hashlib
from datetime import datetime,timezone
P=Path(__file__).parent;R=P/'review_baseline';OLD=P.parent/'conditional_grounding_20261025'
comparison=json.loads((P/'baseline_content_comparison.json').read_bytes());assert comparison['identical_actual_output_count']==30 and not comparison['changed_outputs']
frozen=json.loads((OLD/'baseline_semantic_review_frozen.json').read_bytes())
current=[json.loads(x) for x in (R/'training__eval_step_000000__base_generations.jsonl').read_bytes().splitlines()]
for record,row in zip(frozen['records'],current):
 assert record['fixture_id']==row['fixture_id'] and record['actual_output_sha256']==hashlib.sha256(row['output'].encode()).hexdigest()
 assert row['ended_eos'] and not row['possibly_truncated'] and not row['timed_out']
frozen.update({'reviewed_utc':datetime.now(timezone.utc).isoformat(),
 'base_output_raw_sha256':comparison['current_base_raw_sha256'],
 'review_nature':'Reuse root semantic judgments of exactly identical full response content, original question/rubric and per-output SHA from prior root reading. All30current outputs, prompt tokens, fixtures, contract and per-fixture seeds were byte/hash re-bound before candidate outputs. Generation timestamps/timing differ; no new human review claimed.',
 'current_rebind_proof_sha256':hashlib.sha256((P/'baseline_content_comparison.json').read_bytes()).hexdigest(),
 'prior_root_review_sha256':hashlib.sha256((OLD/'baseline_semantic_review_frozen.json').read_bytes()).hexdigest(),
 'development_was_previously_used':True,'judgments_fixed_before_adapter_outputs_read':True})
dest=P/'baseline_semantic_review_frozen.json';assert not dest.exists();dest.write_text(json.dumps(frozen,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
(P/'paired_review_policy_pre_candidate.json').write_bytes((OLD/'paired_review_policy_pre_candidate.json').read_bytes())
print({'baseline_full_task_pass':frozen['fulltask_pass'],'identical_actual_outputs':30,'current_frozen_sha256':hashlib.sha256(dest.read_bytes()).hexdigest()})
