import subprocess,json,time
if budget_preflight_process.poll() is None:
    budget_preflight_process.terminate()
    budget_preflight_process.wait(timeout=20)
old=(budget_root/'gpu_preflight.log').read_text()
(budget_root/'gpu_preflight_first_attempt.log').write_text(old)
source=(budget_root/'gpu_preflight.py').read_text().replace("max_seq_length=2048,dtype=", "use_exact_model_name=True,max_seq_length=2048,dtype=")
(budget_root/'gpu_preflight.py').write_text(source)
budget_preflight_log=(budget_root/'gpu_preflight.log').open('w')
budget_preflight_process=subprocess.Popen([str(budget_root/'venv/bin/python'),str(budget_root/'gpu_preflight.py')],stdout=budget_preflight_log,stderr=subprocess.STDOUT)
print(json.dumps({'state':'PREFLIGHT_EXACT_REPOSITORY_PIN_ENFORCED','previous_attempt_trained':False,'pid':budget_preflight_process.pid}))
