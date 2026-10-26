"""Check saved run evidence against source rows; never tune on dev-test errors."""
import argparse
import hashlib
import json
from pathlib import Path
from planner_metrics import score_prediction,aggregate

def read_rows(path):
    return [json.loads(s) for s in Path(path).read_text(encoding='utf-8').splitlines() if s.strip()]

def audit(root):
    root=Path(root); run=root/'runs'/'qwen3_06b_grounded_sft_epoch1_seed20261012'
    report=json.loads((run/'completed_run.json').read_text(encoding='utf-8'))
    config=json.loads((run/'config.json').read_text(encoding='utf-8'))
    log=read_rows(run/'training_log.jsonl')
    assert [r['step'] for r in log]==list(range(1,report['steps']+1))
    assert report['steps']==463 and report['train_examples_seen']==1852
    assert log[-1]['examples_seen']==1852
    for split,digest in config['dataset_fingerprints'].items():
        assert hashlib.sha256((root/'data'/(split+'.jsonl')).read_bytes()).hexdigest()==digest
    checks={}
    for name,split,report_key in [('baseline_val','val','baseline_validation'),
                                 ('candidate_val','val','candidate_validation'),
                                 ('selected_dev_test','test','selected_development_test')]:
        source={r['sample_id']:r for r in read_rows(root/'data'/(split+'.jsonl'))}
        predictions=read_rows(run/(name+'.jsonl'))
        assert len(predictions)==len(source) and {r['sample_id'] for r in predictions}==set(source)
        for record in predictions:
            row=source[record['sample_id']]
            assert record['reference_status']==row['target']['status']
            scores=score_prediction(row,record['prediction'],record['scores']['truncated'])
            assert scores==record['scores'],record['sample_id']
        expected=aggregate(predictions)
        assert all(report[report_key][k]==v for k,v in expected.items())
        checks[name]={'all_ids_once':True,'scores_recomputed':True,'rows':len(predictions)}
    selection=json.loads((run/'selection.json').read_text(encoding='utf-8'))
    winner='adapter' if report['candidate_validation']['raw_plan_accuracy']>report['baseline_validation']['raw_plan_accuracy'] else 'base'
    assert selection['selected']==winner==report['selected']
    assert selection['test_used_for_selection'] is False
    assert json.loads((run/'reload_verification.json').read_text(encoding='utf-8'))['passed']
    assert hashlib.sha256((run/'adapter'/'adapter_model.safetensors').read_bytes()).hexdigest()==report['adapter_sha256']
    result={'status':'PASSED','checks':checks,'full_epoch_once':True,'selection_validation_only':True,
            'adapter_file_sha256_verified':True,'reload_record_verified':True,
            'quality_scope':'synthetic planner task; not real-student benchmark or free-text math accuracy',
            'training_loss_first':log[0]['loss'],'training_loss_last':log[-1]['loss'],
            'peak_vram_gib':max(r['peak_vram_gib'] for r in log),'training_seconds':log[-1]['seconds']}
    (run/'reviewer_audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',required=True)
    print(json.dumps(audit(p.parse_args().root),ensure_ascii=False,indent=2))
