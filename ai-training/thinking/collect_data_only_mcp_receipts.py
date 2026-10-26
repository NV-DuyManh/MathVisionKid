from pathlib import Path
import json,ast,hashlib
r=Path('thinking/cloud_publication/colab_data_audit_20261021')
(r/'mcp_evidence').mkdir(parents=True,exist_ok=True)
base=Path.home()/'.codex/integrations/colab-mcp'
source={'token_checkpoint':'data_only_checkpoint_save.json','first_full_audit':'data_only_full_audit_first_run.json','full_audit_checkpoint':'data_only_full_audit_checkpoint_save.json','full_audit_v2_checkpoint':'data_only_v2_run.json','finite_worker_started':'data_only_worker_started.json','finite_worker_observation':'data_only_worker_status_readback.json'}
pins={}
for name,fn in source.items():
 p=base/fn;d=json.loads(p.read_text('utf8'));assert not d['is_error']
 outputs=d['structured_content']['outputs']
 stdout=''.join(''.join(o.get('text',[])) for o in outputs if o.get('name')=='stdout')
 data=ast.literal_eval(stdout.strip())
 (r/'mcp_evidence'/f'{name}.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 pins[fn]=hashlib.sha256(p.read_bytes()).hexdigest()
(r/'mcp_evidence/response_pins.json').write_text(json.dumps(pins,indent=2)+'\n',encoding='utf8')
print('Saved3 exact MCP execution receipts, no auth material')

