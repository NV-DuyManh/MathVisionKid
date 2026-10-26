from pathlib import Path
import json,ast
RUN=Path(__file__).resolve().parent/'cloud_publication/mcp_prepare_20261022'
source=(RUN.parent/'data_resume_20261022/restore_existing_v3_readonly.py').read_text('utf8')
header='''# Load the already published, exact V3 auditor. CPU data only.
import io,zipfile,importlib,hashlib,os
assert os.environ.get('COLAB_GPU','0') in ('0','')
progress_code=reader.read('1D5RvQ5-V3DtYZfGxmlmvvPlVz9I-SxeX',128*1024*1024)
module_pins={
'data_resume_20261022/code/math_data_full_audit_v3.py':'02431da433060a6574127f9a8e14d90cabffe85d8d0150c3b2a331dc15b4be1f',
'data_resume_20261022/code/math_data_primary782_bindings_v3.py':'4d75e90c07eecccf7571d68015dda16e85a690e7ee2379b28d517d201472580b'}
with zipfile.ZipFile(io.BytesIO(progress_code)) as code_zip:
    assert hashlib.sha256(code_zip.read(recipe_pointer['member'])).hexdigest()==recipe_pointer['sha256']
    for member,pin in module_pins.items():
        module_bytes=code_zip.read(member)
        assert hashlib.sha256(module_bytes).hexdigest()==pin
        (ROOT/'code'/member.rsplit('/',1)[-1]).write_bytes(module_bytes)
importlib.invalidate_caches()
import math_data_full_audit_v3 as audit_v3
assert audit_v3.plan_identity(recipe)=='06339a42b0a4b8d2c8ce7b1031a41a6ca1fc936dd361dd4055e17f8796f5b8e2'
'''
source=source.replace('while not done:_,done=download.next_chunk(num_retries=3)', '''while not done:
        _,done=download.next_chunk(num_retries=3)
        if sink.size%(256*1024*1024)==0 or done:
            print({'checkpoint_download_bytes':sink.size,'expected_bytes':size,'training_started':False},flush=True)''')
code=header+source
ast.parse(code)
(RUN/'hoai_restore_existing_v3.py').write_bytes(code.encode('utf8'))
(RUN/'hoai_restore_args.json').write_text(json.dumps({'cellIndex':17,'language':'python','code':code}),encoding='utf8')
print('Prepared existing-checkpoint restore cell; not executed here.')
