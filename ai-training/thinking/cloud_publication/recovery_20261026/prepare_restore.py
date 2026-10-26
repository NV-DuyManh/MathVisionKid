from pathlib import Path
import json
P=Path(__file__).parent
old=(P.parent/'conditional_grounding_20261025/restore_native_runtime.py').read_text(encoding='utf8')
start=old.index('scope={');end=old.index("(r/'owner_run_scope.json')",start)
code=old[:start]+'scope='+repr(json.loads((P/'owner_run_scope.json').read_bytes()))+'\n'+old[end:]
code=code.replace('1611698ac255','fb7636900c84').replace('/content/mathvisionkid_conditional_grounding_20261025','/content/mathvisionkid_recovery_20261026')
code=code.replace('auth.authenticate_user()',"assert 'recovery_credentials' in globals(), 'Authenticate Drive before restore'")
code=code.replace('recovery_credentials,_=google.auth.default()','# reuse notebook-authorized Drive credentials')
compile(code,'restore26','exec');(P/'restore_runtime.py').write_bytes(code.encode())
print('Prepared cloud-only source restore and isolated missing-bnb installation')
