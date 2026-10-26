"""Consolidate audited paired thinking evidence; never retrain or change selection."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import zipfile

import train_teacher_math_v3 as trainer
import teacher_math_numeric_diagnostic_v3 as direct
from validation_sensitivity_v3 import EXCLUDED_ID, summary, raw_gate

ROOT = Path(__file__).resolve().parent
EVIDENCE = ROOT / 'evidence' / 'teacher_math_v3_20261013'
EVAL = EVIDENCE / 'full_thinking_readback'
REVIEW = EVIDENCE / 'full_thinking_semantic_review'
VAL = ROOT / 'data' / 'teacher_math_v3' / 'generated' / 'val.jsonl'

def read(path):
    return json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=trainer.unique_object)

def report_numeric():
    paths = [VAL, EVAL/'protocol.json', EVAL/'state.json', EVAL/'evaluation_review.json',
             EVAL/'reload_verification.json', ROOT/'run_teacher_thinking_validation_v3.py',
             ROOT/'train_teacher_math_v3.py', ROOT/'teacher_math_data_v3.py',
             ROOT/'audit_teacher_math_v3.py', ROOT/'teacher_math_numeric_diagnostic_v3.py']
    for name in ('baseline','candidate'):
        paths += [EVAL/(name+suffix) for suffix in ('.jsonl','.metadata.json','.summary.json')]
    before = {str(path.relative_to(ROOT)): trainer.sha(path) for path in paths}
    protocol = read(EVAL/'protocol.json')
    assert protocol['source_sha256'] == trainer.sha(ROOT/'run_teacher_thinking_validation_v3.py')
    assert protocol['source_sha256'] == 'd4547e3cab2edf9fce90dfdd07d6937e383c5d25788841df9142d06e90ccb1bd'
    assert protocol['adapter_sha256'] == '20e99388093c5f7caa1aacaac2a6014cdc0bfd4b4b1bb6f25b5a593ea8beae8d'
    assert trainer.sha(VAL) == protocol['validation_sha256']
    reload = read(EVAL/'reload_verification.json')
    assert reload == {'passed':True,'adapter_sha256':protocol['adapter_sha256'],'revision':protocol['revision']}
    packet = read(REVIEW/'review_packet_evidence.json')
    refs = trainer.rows(VAL)
    by_id = {r['sample_id']:r for r in refs}
    full, reduced, omitted, differences = {}, {}, {}, []
    for name in ('baseline','candidate'):
        rows = trainer.rows(EVAL/(name+'.jsonl'))
        assert len(rows) == 262 and [r['sample_id'] for r in rows] == [r['sample_id'] for r in refs]
        assert packet['model_evidence'][name]['predictions_sha256'] == trainer.sha(EVAL/(name+'.jsonl'))
        full[name] = {'strict':summary(rows),'direct':direct.diagnostic(refs,rows)['summary']}
        assert full[name]['direct'] == packet['model_evidence'][name]['direct_numeric_summary']
        kept = [r for r in rows if r['sample_id'] != EXCLUDED_ID]
        kept_refs = [r for r in refs if r['sample_id'] != EXCLUDED_ID]
        reduced[name] = {'strict':summary(kept),'direct':direct.diagnostic(kept_refs,kept)['summary']}
        removed = next(r for r in rows if r['sample_id'] == EXCLUDED_ID)
        omitted[name] = {'sample_id':EXCLUDED_ID,'scores':removed['scores'],
                         'direct':direct.diagnostic([by_id[EXCLUDED_ID]],[removed])['records'][0]}
        assert reduced[name]['strict']['samples'] == 261 and reduced[name]['direct']['solution_samples'] == 172
    base_d = {r['sample_id']:r for r in read(EVAL/'baseline_direct_numeric.json')['records']}
    cand_d = {r['sample_id']:r for r in read(EVAL/'candidate_direct_numeric.json')['records']}
    for sample_id in base_d:
        a,b = base_d[sample_id],cand_d[sample_id]
        if any(a[key] != b[key] for key in ('numeric_correct','answer_unit_correct')):
            differences.append({'sample_id':sample_id,'grade':by_id[sample_id]['grade'],
                'topic':by_id[sample_id]['topic'],
                'baseline':{key:a[key] for key in ('answer_extracted','numeric_correct','answer_unit_correct')},
                'candidate':{key:b[key] for key in ('answer_extracted','numeric_correct','answer_unit_correct')}})
    gates = {key:raw_gate(value['baseline']['direct'],value['candidate']['direct'])
             for key,value in (('primary262',full),('supplemental261',reduced))}
    strict = {key:trainer.select_candidate(value['baseline']['strict'],value['candidate']['strict'])
              for key,value in (('primary262',full),('supplemental261',reduced))}
    expected = read(EVAL/'evaluation_review.json')
    assert strict['primary262'] == expected['provisional_strict_decision']
    assert not gates['primary262']['per_grade_non_regression']
    assert expected['provisional_selected'] == 'base'
    assert not gates['supplemental261']['per_grade_non_regression']
    assert before == {str(p.relative_to(ROOT)):trainer.sha(p) for p in paths}
    report = {'run_id':protocol['run_id'],'evaluation_id':'full_thinking_validation_seed20261013',
        'created_at_utc':datetime.now(timezone.utc).isoformat(),
        'status':'AUDITED_NUMERIC_COMPARISON_SEMANTIC_REVIEW_PENDING',
        'primary262':full,'supplemental261':reduced,'excluded_sample_id':EXCLUDED_ID,
        'excluded_observations':omitted,'raw_retention_gates':gates,'strict_decisions':strict,
        'paired_numeric_transitions':dict(Counter((
            'both_correct' if base_d[s]['numeric_correct'] and cand_d[s]['numeric_correct'] else
            'candidate_only_correct' if cand_d[s]['numeric_correct'] else
            'baseline_only_correct' if base_d[s]['numeric_correct'] else 'neither_correct') for s in base_d)),
        'paired_differences':differences,'technical_audit':packet['model_evidence'],
        'source_and_artifact_sha256':before,'primary_greedy_selection_changed':False,
        'provisional_thinking_recommended_weights':'base','production_approved':False,
        'human_verified':False,'single_seed_development_evaluation':True,
        'new_training_or_inference_performed':False,'frozen_files_unchanged':True}
    trainer.save(REVIEW/'numeric_and_sensitivity_report.json',report)
    print(json.dumps({'status':report['status'],'numeric262':{k:v['direct'] for k,v in full.items()},
        'numeric261':{k:v['direct'] for k,v in reduced.items()},'paired':report['paired_numeric_transitions']},ensure_ascii=False))
    return report

def finalize_semantic():
    numeric = read(REVIEW/'numeric_and_sensitivity_report.json')
    for name,digest in numeric['source_and_artifact_sha256'].items():
        assert trainer.sha(ROOT/name) == digest, 'Frozen numeric evidence changed: '+name
    evidence = read(REVIEW/'review_packet_evidence.json')
    packets, file_by_key = {}, {}
    for model in ('baseline','candidate'):
        for kind in ('worked_solution','hint','guard'):
            name = f'{model}_{kind}_review_packets.jsonl'
            path = REVIEW/name
            assert trainer.sha(path) == evidence['packet_files'][name]['sha256']
            for packet in trainer.rows(path):
                key = (model,packet['sample_id'])
                assert key not in packets and packet['kind'] == kind
                packets[key], file_by_key[key] = packet, path
    sources = ['baseline_worked_semantic_decisions.jsonl',
               'candidate_worked_semantic_decisions.jsonl','hint_guard_semantic_decisions.jsonl']
    source_hashes = {name:trainer.sha(REVIEW/name) for name in sources}
    decisions = {}
    common = ('semantic_correct','instruction_followed','grade_appropriate',
              'invented_data_or_image','severe_error')
    for name in sources:
        for decision in trainer.rows(REVIEW/name):
            key = (decision['model'],decision['sample_id'])
            assert key in packets and key not in decisions
            packet,path = packets[key],file_by_key[key]
            review = decision.get('review',decision)
            assert decision['grade'] == packet['grade'] and decision['kind'] == packet['kind']
            assert all(type(review.get(field)) is bool for field in common)
            assert review.get('human_verified') is False and review.get('teacher_certified') is False
            assert isinstance(review.get('reason'),str) and review['reason'].strip()
            bound = next(decision[field] for field in ('packet_source_sha256',
                'source_packet_file_sha256','packet_file_sha256') if field in decision)
            assert bound == trainer.sha(path)
            payload = (json.dumps(packet['visible_output'],ensure_ascii=False,sort_keys=True)
                if packet['kind'] == 'worked_solution' else packet['visible_output']['text'] or '')
            assert decision['visible_output_sha256'] == hashlib.sha256(payload.encode()).hexdigest()
            if packet['kind'] == 'worked_solution':
                for field in ('explanation_operation_consistent','data_roles_correct',
                              'displayed_method_valid','step_by_step_guidance_useful'):
                    assert type(review.get(field)) is bool
                accepted = all(review[f] for f in ('semantic_correct','instruction_followed','grade_appropriate',
                    'explanation_operation_consistent','data_roles_correct','displayed_method_valid',
                    'step_by_step_guidance_useful')) and not review['invented_data_or_image'] and not review['severe_error']
            else:
                accepted = decision['acceptable_for_intended_role']
                assert type(accepted) is bool
                if accepted:
                    assert all(review[f] for f in ('semantic_correct','instruction_followed','grade_appropriate'))
                    assert not review['invented_data_or_image'] and not review['severe_error']
                    if packet['kind'] == 'hint':assert decision['answer_leakage'] is False
            decisions[key] = {'model':key[0],'sample_id':key[1],'grade':packet['grade'],
                'kind':packet['kind'],'topic':packet['topic'],'review':review,
                'acceptable_for_intended_role':accepted,'source_decision_file':name,
                'source_decision_file_sha256':source_hashes[name]}
    assert set(decisions) == set(packets) and len(decisions) == 524
    def aggregate(items):
        counts = {'samples':len(items),**{field:sum(r['review'][field] for r in items) for field in common},
                  'acceptable_for_intended_role':sum(r['acceptable_for_intended_role'] for r in items)}
        for field in ('step_by_step_guidance_useful','answer_leakage'):
            values = [r['review'].get(field) for r in items]
            if all(type(x) is bool for x in values):counts[field] = sum(values)
        return counts
    models = {}
    for model in ('baseline','candidate'):
        models[model] = {}
        for kind,expected in (('worked_solution',173),('hint',59),('guard',30)):
            rows = [r for (m,_),r in decisions.items() if m == model and r['kind'] == kind]
            assert len(rows) == expected
            models[model][kind] = {'counts':aggregate(rows),
                'per_grade':{str(g):aggregate([r for r in rows if r['grade']==g]) for g in range(1,6)}}
    assert models['baseline']['worked_solution']['counts']['semantic_correct'] == 150
    assert models['candidate']['worked_solution']['counts']['semantic_correct'] == 149
    assert models['candidate']['hint']['counts']['acceptable_for_intended_role'] == 15
    assert models['candidate']['guard']['counts']['acceptable_for_intended_role'] == 20
    combined_path = REVIEW/'all_524_semantic_decisions.jsonl'
    combined_path.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in decisions.values()),
                            encoding='utf-8',newline='\n')
    final = {'run_id':numeric['run_id'],'evaluation_id':numeric['evaluation_id'],
        'created_at_utc':datetime.now(timezone.utc).isoformat(),
        'status':'FULL_THINKING_EVALUATED_RESEARCH_ONLY_UNSUITABLE_FOR_STUDENT_TUTOR',
        'technical_audit_passed':True,'visible_outputs_reviewed':524,'semantic_review_complete':True,
        'review_kind':'AI_SEMANTIC_RESEARCH_REVIEW','human_verified':False,'teacher_certified':False,
        'numeric_and_sensitivity_report_sha256':trainer.sha(REVIEW/'numeric_and_sensitivity_report.json'),
        'review_packet_evidence_sha256':trainer.sha(REVIEW/'review_packet_evidence.json'),
        'decision_files_sha256':source_hashes,'all_decisions_sha256':trainer.sha(combined_path),
        'models':models,
        'primary262_direct':{m:v['direct'] for m,v in numeric['primary262'].items()},
        'supplemental261_direct':{m:v['direct'] for m,v in numeric['supplemental261'].items()},
        'strict_numeric':{m:{k:v['strict'][k] for k in ('answer_and_unit_correct','solution_verified',
            'hint_safe','hint_reference_match','guard_correct','truncated')} for m,v in numeric['primary262'].items()},
        'paired_numeric_transitions':numeric['paired_numeric_transitions'],
        'provisional_strict_selected':'adapter','direct_numeric_per_grade_retention_passed':False,
        'thinking_adapter_rejected_by_frozen_gate':True,'original_primary_greedy_selection':'base',
        'original_selection_changed':False,'recommended_weights_for_current_research_comparison':'base',
        'standalone_student_tutor_approved':False,'production_approved':False,
        'near_assistant_intelligence_demonstrated':False,'hidden_thinking_in_report':False,
        'parent_adjudication':[{'model':'candidate','packet_indices':[123,125],
            'decision':'Keep semantic failure, nonsevere wording/data-role issue.',
            'reason':'Alternative divide-first trapezoid computation is correct, but final explanation calls a half-sum the sum and says divide by two again.'}],
        'next_phase':[
            'Audit fresh training grade assignments/ranges and old/current curriculum labels; frozen evaluation remains unchanged.',
            'Repair or author new teacher examples for operations/data roles, column carry/borrow and child-friendly explanations, avoiding these exact held-out questions/numbers.',
            'Strengthen one-question hint mode, no answer leakage, and missing-information/scope guards.',
            'Review mixedV4 replay/concept curriculum and smaller learning-rate plan before freezing and launching; no V4 training performed in this monitoring phase.',
            'Evaluate visible concise solving separately from thinking generation token budget; use arithmetic verification without replacing raw model scores.',
            'Obtain independent teacher-reviewed school problems for quality measurement; keep unseen concept challenge unread until declared selection.'
        ],
        'limits':[
            'One sampling seed on AI-authored development validation after pilot; not human gold or a guarantee for arbitrary school problems.',
            'Manual math-intent/semantic unit interpretations are supplemental; canonical raw number/unit scores remain untouched.',
            'Reviewer severity/usefulness/grade judgments are AI research judgments, with per-case reasons; not teacher certification.',
            'Some problem-grade assignments/ranges need correction in future data; grade-appropriate flags include this shared data limitation.',
            'Strict solution_verified measures the required schema/reference path, not unrestricted mathematical reasoning.',
            'Current text-only evaluation does not certify OCR, image geometry or all current/legacy curriculum outcomes.'
        ]}
    trainer.save(REVIEW/'final_thinking_review.json',final)
    assert all(trainer.sha(REVIEW/name)==digest for name,digest in source_hashes.items())
    print(json.dumps({'status':final['status'],'reviewed':524,'models':models},ensure_ascii=False))
    return final

def package_review():
    members = {}
    names = ['final_thinking_review.json','numeric_and_sensitivity_report.json',
             'all_524_semantic_decisions.jsonl','review_packet_evidence.json','review_plan.json']
    for model in ('baseline','candidate'):
        names += [f'{model}_{kind}_review_packets.jsonl' for kind in ('worked_solution','hint','guard')]
        names += [f'{model}_worked_semantic_decisions.jsonl',f'{model}_worked_semantic_summary.json']
    names += ['hint_guard_semantic_decisions.jsonl','hint_guard_semantic_summary.json']
    for name in names:members['review/'+name] = (REVIEW/name).read_bytes()
    for name in ('protocol.json','reload_verification.json','environment.json','state.json',
                 'evaluation_review.json','baseline.metadata.json','candidate.metadata.json'):
        members['technical/'+name] = (EVAL/name).read_bytes()
    members['reproduce/review_full_thinking_results_v3.py'] = Path(__file__).read_bytes()
    manifest = {'status':'RESEARCH_EVALUATION_ARCHIVE_NOT_DEPLOYABLE_MODEL',
        'production_approved':False,'human_verified':False,'hidden_thinking_included':False,
        'weights_included':False,'files':{name:hashlib.sha256(data).hexdigest() for name,data in members.items()}}
    members['EXPORT_MANIFEST.json'] = json.dumps(manifest,ensure_ascii=False,indent=2).encode()
    archive_path = EVIDENCE/'MathVisionKid_Full_Thinking_Review_20261013.zip'
    with zipfile.ZipFile(archive_path,'w',zipfile.ZIP_DEFLATED) as archive:
        for name,data in sorted(members.items()):archive.writestr(name,data)
    with zipfile.ZipFile(archive_path) as archive:
        assert archive.testzip() is None
        assert all(hashlib.sha256(archive.read(name)).hexdigest()==digest for name,digest in manifest['files'].items())
    trainer.save(REVIEW/'review_export_receipt.json',{'archive_path':str(archive_path),
        'sha256':trainer.sha(archive_path),'bytes':archive_path.stat().st_size,'members':len(members),
        'archive_members_hash_verified':True,'hidden_thinking_included':False})
    print(json.dumps({'archive':str(archive_path),'sha256':trainer.sha(archive_path),'bytes':archive_path.stat().st_size}))

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser();parser.add_argument('--finalize',action='store_true');args=parser.parse_args()
    if args.finalize:
        finalize_semantic();package_review()
    else:
        report_numeric()
