"""Paired full-validation thinking-mode development evaluation; no training.

Preserves the frozen original greedy selection, datasets and adapter. No challenge
is loaded. A positive numeric result still needs AI review of actual guidance.
"""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import sys

RUN_ID='qwen3_17b_teacher_math_v3_epoch1_seed20261013'


def nonregression(base,candidate):
    keys=('numeric_correct','answer_unit_correct')
    return all(candidate[key]>=base[key] for key in keys) and all(
        all(candidate['per_grade'][grade][key]>=values[key] for key in keys)
        for grade,values in base['per_grade'].items())


def main(root):
    root=Path(root).resolve();run=root/'runs'/RUN_ID
    sys.path.insert(0,str(root/'src'));sys.path.insert(0,str(root/'posthoc_src'))
    import train_teacher_math_v3 as trainer
    import teacher_math_numeric_diagnostic_v3 as diagnostic_module
    import audit_teacher_math_v3 as audit_module
    diagnostic=diagnostic_module.diagnostic
    check_evaluation=audit_module.check_evaluation
    import torch
    from peft import PeftModel
    config=json.loads((run/'config.json').read_text())
    data_source=trainer.bind_data_system(config)
    actual_sources={Path(trainer.__file__).name:Path(trainer.__file__).resolve(),
                    data_source.name:data_source.resolve()}
    for name,digest in config['source_hashes'].items():
        if actual_sources[name]!=(root/'src'/name).resolve() or trainer.sha(actual_sources[name])!=digest:
            raise ValueError('Actual imported frozen V3 source differs: '+name)
    dependency_paths={**actual_sources,Path(audit_module.__file__).name:Path(audit_module.__file__).resolve(),
        Path(diagnostic_module.__file__).name:Path(diagnostic_module.__file__).resolve()}
    manifest=json.loads((root/'bundle_manifest.json').read_text())['files']
    if trainer.sha(audit_module.__file__)!=manifest['src/audit_teacher_math_v3.py']:
        raise ValueError('Auditor differs from the original verified deployment')
    if trainer.sha(diagnostic_module.__file__)!='170ec0a5ec64cb5b7bca02bbc9f38dd3b3d6797bb769bf4c6e90e23d90aa594a':
        raise ValueError('Direct numeric diagnostic differs from the reviewed source')
    if trainer.sha(root/'data'/'val.jsonl')!=config['dataset_fingerprints']['val']:
        raise ValueError('Frozen validation data differs')
    audit=json.loads((run/'reviewer_audit.json').read_text())
    if audit.get('status')!='PASSED' or audit.get('run_id')!=RUN_ID or not audit['all_passed']:
        raise ValueError('Matching successful core V3 integrity audit required')
    complete=json.loads((run/'training_complete.json').read_text())
    actual=trainer.sha(run/'adapter'/'adapter_model.safetensors')
    if actual!=complete['adapter_sha256']:raise ValueError('Saved adapter file changed')
    destination=run/'full_thinking_validation_seed20261013';destination.mkdir(parents=True,exist_ok=True)
    examples=trainer.rows(root/'data'/'val.jsonl')
    environment={'gpu':torch.cuda.get_device_name(0),'cuda_build':torch.version.cuda,
        'compute_capability':list(torch.cuda.get_device_capability(0)),
        'packages':{key:importlib.metadata.version(key) for key in ('torch','transformers','peft','accelerate','torchao')}}
    protocol={'run_id':RUN_ID,'model_id':config['model_id'],'revision':config['revision'],
        'adapter_sha256':actual,'validation_sha256':trainer.sha(root/'data'/'val.jsonl'),
        'dependency_sha256':{name:trainer.sha(path) for name,path in dependency_paths.items()},
        'generation_environment':environment,
        'source_sha256':trainer.sha(__file__),'samples':len(examples),'seed':20261013,
        'thinking':True,'temperature':.6,'top_p':.95,'top_k':20,'max_new_tokens':2048,'batch_size':4,
        'role':'posthoc paired reasoning-mode development validation after an eight-case exploratory probe',
        'primary_greedy_selection_unchanged':True,'challenge_loaded':False,
        'optimizer_steps':0,'production_approved':False,'teacher_certified':False,
        'provisional_gate':'strict solution improvement and all original paired strict/per-grade axes non-regression, plus directly generated numeric/unit overall/per-grade retention; then AI semantic guidance review required'}
    file=destination/'protocol.json'
    if file.exists() and json.loads(file.read_text())!=protocol:raise ValueError('Changed full-thinking protocol: use a new evaluation ID')
    if not file.exists():trainer.save(file,protocol)
    def state(phase,**kwargs):trainer.save(destination/'state.json',{'phase':phase,**kwargs})
    state('loading_fresh_base_and_adapter',model_loaded=False)
    trainer.save(destination/'environment.json',environment)
    with (destination/'environment_sessions.jsonl').open('a',encoding='utf-8') as stream:
        stream.write(json.dumps({'generation_environment':environment,'free_total_vram_bytes':list(torch.cuda.mem_get_info())})+'\n')
    tokenizer=trainer.get_tokenizer(config)
    base=trainer.load_model(config)
    model=PeftModel.from_pretrained(base,run/'adapter',is_trainable=False)
    if trainer.adapter_hashes(model)!=complete['adapter_tensor_hashes']:raise ValueError('Fresh adapter tensor reload differs')
    trainer.save(destination/'reload_verification.json',{'passed':True,'adapter_sha256':actual,'revision':config['revision']})
    base_key='base:'+config['model_id']+':'+config['revision'];adapter_key='adapter:'+actual
    state('baseline_full_thinking_validation',model_loaded=True)
    with model.disable_adapter():
        baseline=trainer.evaluate(model,tokenizer,examples,destination/'baseline.jsonl',base_key,
            2048,4,thinking=True,seed=20261013)
    state('candidate_full_thinking_validation',model_loaded=True)
    candidate=trainer.evaluate(model,tokenizer,examples,destination/'candidate.jsonl',adapter_key,
        2048,4,thinking=True,seed=20261013)
    by_id={row['sample_id']:row for row in examples}
    validations={name:check_evaluation(destination/(name+'.jsonl'),by_id,tokenizer) for name in ('baseline','candidate')}
    raw={name:diagnostic(examples,trainer.rows(destination/(name+'.jsonl'))) for name in ('baseline','candidate')}
    for name,report in raw.items():trainer.save(destination/(name+'_direct_numeric.json'),report)
    strict=trainer.select_candidate(baseline,candidate)
    raw_ok=nonregression(raw['baseline']['summary'],raw['candidate']['summary'])
    provisional=strict['selected']=='adapter' and raw_ok
    report={'status':'AWAITING_ACTUAL_GUIDANCE_SEMANTIC_REVIEW' if provisional else 'THINKING_ADAPTER_REJECTED_VALIDATION_RETENTION',
        'provisional_selected':'adapter' if provisional else 'base','provisional_strict_decision':strict,
        'direct_numeric_retention_non_regression':raw_ok,'baseline_direct_numeric':raw['baseline']['summary'],
        'candidate_direct_numeric':raw['candidate']['summary'],'technical_evaluation_audit':validations,
        'actual_guidance_review_required':True,'single_sampling_seed_only':True,
        'original_primary_selection_unchanged':True,'challenge_loaded':False,'production_approved':False,
        'near_assistant_intelligence_demonstrated':False}
    trainer.save(destination/'evaluation_review.json',report)
    state('completed_numeric_comparison',model_loaded=False,status=report['status'],production_approved=False)
    print('FULL_THINKING_VALIDATION_COMPLETE',json.dumps(report,ensure_ascii=False),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--root',required=True);args=parser.parse_args()
    try:main(args.root)
    except Exception as error:
        destination=Path(args.root)/'runs'/RUN_ID/'full_thinking_validation_seed20261013'
        destination.mkdir(parents=True,exist_ok=True)
        (destination/'state.json').write_text(json.dumps({'phase':'failed','error_type':type(error).__name__,'error':str(error),
            'optimizer_steps':0,'production_approved':False}),encoding='utf-8')
        raise
