"""Independent recomputation of saved evidence, coverage and checkpoint selection."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
from real_math_data import validate,write_json
from real_math_training import scores,summary

def rows(path):return [json.loads(x) for x in Path(path).read_text(encoding='utf-8').splitlines() if x.strip()]

def audit(root):
    root=Path(root);run=root/'runs'/'qwen3_06b_real_mcq_2epoch_seed20261012'
    config=json.loads((run/'config.json').read_text(encoding='utf-8'))
    report=json.loads((run/'completed_run.json').read_text(encoding='utf-8'))
    selection=json.loads((run/'selection.json').read_text(encoding='utf-8'))
    split={s:rows(root/'data'/'clean'/(s+'.jsonl')) for s in ('train','val','test')};validate(split)
    for s in split:assert hashlib.sha256((root/'data'/'clean'/(s+'.jsonl')).read_bytes()).hexdigest()==config['dataset_fingerprints'][s]
    for name,sha in config['source_hashes'].items():assert hashlib.sha256((root/'src'/name).read_bytes()).hexdigest()==sha
    token=json.loads((run/'token_audit.json').read_text(encoding='utf-8'))
    log=rows(run/'training_log.jsonl')
    assert [r['step'] for r in log]==list(range(1,config['steps']+1))
    for epoch in (1,2):
        ids=[i for r in log if r['epoch']==epoch for i in r['sample_ids']]
        assert Counter(ids)==Counter(token['training_ids']), 'Dropped or repeated training rows'
    summaries={}
    relaxed={}
    reasoning_audit={}
    for name,s,shift in (('baseline_val','val',0),('epoch1_val','val',0),('epoch2_val','val',0),
                         ('selected_test','test',0),('selected_rotated_test','test',1)):
        predictions=rows(run/(name+'.jsonl'));references={r['sample_id']:r for r in split[s]}
        assert [p['sample_id'] for p in predictions]==[r['sample_id'] for r in split[s]]
        for p in predictions:assert scores(references[p['sample_id']],p['prediction'],p['scores']['truncated'],shift)==p['scores']
        result=summary(predictions);assert result==json.loads((run/(name+'.summary.json')).read_text(encoding='utf-8'))
        summaries[name]=result
        reasoning_audit[name]={'correct_choice_with_arithmetic_flags':sum(p['scores']['correct'] and p['scores']['arithmetic_flagged']>0 for p in predictions),
                              'flagged_output_samples':sum(p['scores']['arithmetic_flagged']>0 for p in predictions),
                              'partial_check_not_semantic_or_pedagogical_certification':True}
        # Advisory semantic answer extraction; never used for checkpoint selection.
        count=0
        for p in predictions:
            if p['scores']['truncated'] or '</think>' not in p['prediction']:continue
            final=p['prediction'].split('</think>',1)[1].strip()
            candidate=p['scores']['predicted_answer']
            if candidate is None:
                cleaned=final.replace('**','').replace('`','')
                patterns=[r'"answer"\s*:\s*"([ABCD])"',
                    r'(?:[Đđ]áp án|[Cc]họn)\s*(?:đúng\s*)?(?:là\s*)?[:：]?\s*([ABCD])\b',r'\\boxed\{([ABCD])\}']
                matches={m for pat in patterns for m in re.findall(pat,cleaned)}
                bare=re.fullmatch(r'\s*([ABCD])\s*[.]?',cleaned)
                if bare:matches.add(bare[1])
                if len(matches)==1:candidate=matches.pop()
            count+=candidate==p['scores']['target_answer']
        relaxed[name]={'advisory_only':True,'correct':count,'samples':len(predictions)}
    candidates=selection['candidates']
    assert len(candidates)==3
    for c in candidates:
        assert c['validation']==summaries['baseline_val' if c['name']=='base' else c['name']+'_val']
    winner=max(candidates,key=lambda c:(c['validation']['accuracy'],c['validation']['macro_grade_accuracy']))
    assert winner['name']==selection['selected']==report['selected']
    assert not selection['test_used_for_selection'] and report['reload_verified']
    assert report['baseline_validation']==summaries['baseline_val']
    assert report['selected_test']==summaries['selected_test'] and report['rotated_test']==summaries['selected_rotated_test']
    original=rows(run/'selected_test.jsonl');rotated=rows(run/'selected_rotated_test.jsonl')
    consistency=sum(a['scores']['predicted_answer'] is not None and b['scores']['predicted_answer'] is not None and
        (ord(a['scores']['predicted_answer'])-65)==(ord(b['scores']['predicted_answer'])-65+1)%4 for a,b in zip(original,rotated))/len(original)
    assert consistency==report['choice_rotation_consistency']
    assert not report['production_approved']
    if report['selected_adapter_path']:
        weight=Path(report['selected_adapter_path'])/'adapter_model.safetensors'
        assert hashlib.sha256(weight.read_bytes()).hexdigest()==report['selected_adapter_sha256']
    result={'status':'PASSED','training_steps':len(log),'training_samples_each_epoch':token['accepted'],
            'epochs':2,'source_and_data_hashes_verified':True,'split_invariants_verified':True,
            'all_scores_recomputed':True,'all_eval_ids_once':True,'selected_by_validation_only':True,
            'selected':winner['name'],'advisory_answer_metrics':relaxed,
            'reasoning_audit':reasoning_audit,
            'does_not_certify_source_semantics_or_pedagogy':True}
    write_json(run/'reviewer_audit.json',result);return result

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);a=p.parse_args();print(json.dumps(audit(a.root),ensure_ascii=False))
