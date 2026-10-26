"""Freeze a reviewed source/data payload for the original Colab notebook."""
import json
from pathlib import Path
from teacher_math_colab_ops_v3 import build_payload

HERE=Path(__file__).resolve().parent
FILES=['teacher_math_data_v3.py','test_teacher_math_data_v3.py','train_teacher_math_v3.py',
       'test_train_teacher_math_v3.py','audit_teacher_math_v3.py','test_audit_teacher_math_v3.py',
       'teacher_math_verifier_v3.py','test_teacher_math_verifier_v3.py',
       'teacher_math_runtime_v3.py','test_teacher_math_runtime_v3.py']
DATA=HERE/'data'/'teacher_math_v3'
CONFIG={'model_id':'Qwen/Qwen3-1.7B','revision':'70d244cc86ccca08cf5af4e1e306ecf908b1ad5e',
        'run_id':'qwen3_17b_teacher_math_v3_epoch1_seed20261013','seed':20261013,'epochs':1,
        'batch_size':1,'accumulation':4,'lr':1e-4,'max_length':2048,'max_new_tokens':1536,
        'eval_batch_size':4,'val_limit':0,'thinking_probe_limit':8,'thinking_max_new_tokens':2048,
        'lora_r':16,'lora_alpha':32,'lora_dropout':.05,'checkpoint_interval':50,'train_limit':0,
        'data_module':'teacher_math_data_v3'}

if __name__=='__main__':
    files={f'data/{split}.jsonl':DATA/'generated'/(split+'.jsonl') for split in ('train','val','challenge')}
    files['data/dataset_report.json']=DATA/'generated'/'dataset_report.json'
    files['evidence/curriculum_sources.json']=DATA/'curriculum_sources.json'
    files['posthoc_data/independent_anchor.jsonl']=DATA/'independent_anchor.jsonl'
    for name in ('semantic_template_review.json','trainer_peer_review.json'):
        if (DATA/name).exists():files['evidence/'+name]=DATA/name
    build_payload([HERE/name for name in FILES],files,{'inspection':CONFIG},index=53)
