"""Research inference CLI: selected weights + exact supported-pattern tutor.

Default gives one authored hint. Full worked output requires explicit mode and
confirmed text. This CLI does not authenticate teacher roles or perform OCR;
the application must enforce those requirements before classroom integration.
"""
import argparse
import json
from pathlib import Path
import sys

def main(root,run_id,question,grade,mode,confirmed):
    root=Path(root);run=root/'runs'/run_id
    import train_teacher_math_v3 as trainer
    from teacher_math_runtime_v3 import tutor
    cfg=json.loads((run/'config.json').read_text(encoding='utf-8'))
    trainer.bind_data_system(cfg)
    row={'grade':grade,'problem':question,'mode':mode}
    if not confirmed:
        print(json.dumps(tutor(question,'',grade=grade,mode=mode,input_confirmed=False),ensure_ascii=False,indent=2));return
    tokenizer=trainer.get_tokenizer(cfg);base=trainer.load_model(cfg)
    role=json.loads((run/'role_review.json').read_text(encoding='utf-8'))
    if role['final_recommended_weights']=='adapter':
        from peft import PeftModel
        model=PeftModel.from_pretrained(base,run/'adapter',is_trainable=False)
    else:model=base
    import torch
    text=tokenizer.apply_chat_template(trainer.messages(row),tokenize=False,
                                      add_generation_prompt=True,enable_thinking=False)
    inputs=tokenizer(text,return_tensors='pt',add_special_tokens=False).to('cuda')
    with torch.inference_mode():
        ids=model.generate(**inputs,max_new_tokens=512,do_sample=False,
                           pad_token_id=tokenizer.pad_token_id,eos_token_id=tokenizer.eos_token_id)
    new_ids=ids[0,inputs['input_ids'].shape[-1]:].tolist()
    truncated=tokenizer.eos_token_id not in new_ids and len(new_ids)>=512
    prediction=tokenizer.decode(new_ids,skip_special_tokens=True)
    result=tutor(question,prediction if not truncated else '',grade=grade,mode=mode,input_confirmed=True)
    result['research_generation']={'selected_weights':role['final_recommended_weights'],
        'model_id':cfg['model_id'],'revision':cfg['revision'],'generated_tokens':len(new_ids),'truncated':truncated,
        'free_model_text_released_to_student':False}
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--run-id',required=True)
    p.add_argument('--question',required=True);p.add_argument('--grade',type=int,required=True,choices=range(1,6))
    p.add_argument('--mode',choices=('hint','worked_solution'),default='hint');p.add_argument('--text-confirmed',action='store_true')
    a=p.parse_args();main(a.root,a.run_id,a.question,a.grade,a.mode,a.text_confirmed)
