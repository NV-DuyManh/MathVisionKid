import pathlib, json, subprocess, os
root=pathlib.Path('/content/mathvisionkid_t4_budget_3h_20261023')
if globals().get('final_collector_process') and final_collector_process.poll() is None:
    print(json.dumps({'started':False,'reason':'existing collector waiter alive'}))
else:
    code="""import pathlib,time,json,subprocess,sys
root=pathlib.Path('/content/mathvisionkid_t4_budget_3h_20261023')
deadline=json.loads((root/'budget_control.json').read_bytes())['deadline_unix']
while time.time()<deadline+120:
 p=root/'training/run_complete.json'
 if p.is_file() and json.loads(p.read_bytes()).get('complete') is True:break
 time.sleep(30)
else:raise TimeoutError('No complete training record before budget deadline')
subprocess.run([sys.executable,str(root/'training/collect_final_evidence.py'),'--runtime-root',str(root)],check=True)
"""
    p=root/'wait_for_final_collector.py';p.write_text(code,encoding='utf-8')
    env=dict(os.environ);env['CUDA_VISIBLE_DEVICES']='';env['HF_HUB_OFFLINE']='1'
    log=(root/'final_collector.log').open('ab')
    final_collector_process=subprocess.Popen([str(root/'venv/bin/python'),str(p)],stdout=log,stderr=subprocess.STDOUT,env=env)
    print(json.dumps({'started':True,'pid':final_collector_process.pid,'scope':'CPU read-only final-record collector after run_complete; no training action'}))
