"""Assistant-only tokenization, padding and deterministic full-epoch batches."""
import json
import random
from scope_dataset import SYSTEM, prompt

def serialize(row,tokenizer,max_length=1024):
    prefix=tokenizer.apply_chat_template([{'role':'system','content':SYSTEM},
        {'role':'user','content':prompt(row)}],tokenize=False,add_generation_prompt=True,enable_thinking=True)
    opening='' if prefix.rstrip().endswith('<think>') else '<think>\n'
    completion=opening+row['worked_solution']+'\n</think>\n'+json.dumps(row['target'],ensure_ascii=False,separators=(',',':'))+tokenizer.eos_token
    a=tokenizer(prefix,add_special_tokens=False)['input_ids']
    b=tokenizer(completion,add_special_tokens=False)['input_ids']
    if not a or not b or len(a)+len(b)>max_length: raise ValueError('Empty or long example; no silent truncation')
    return {'input_ids':a+b,'labels':[-100]*len(a)+b,'attention_mask':[1]*(len(a)+len(b))}

def collate(rows,pad_token_id):
    length=max(len(r['input_ids']) for r in rows)
    return {k:[r[k]+[pad_token_id if k=='input_ids' else -100 if k=='labels' else 0]*(length-len(r[k])) for r in rows]
            for k in ('input_ids','labels','attention_mask')}

def epoch_batches(size,batch_size=2,seed=20261012):
    order=list(range(size)); random.Random(seed).shuffle(order)
    return [order[i:i+batch_size] for i in range(0,size,batch_size)]
