import subprocess,json,time
assert budget_process.poll() is not None
assert not (budget_root/'training/successful_ids.jsonl').exists()
budget_orchestration_log=(budget_root/'orchestrator.log').open('a')
budget_process=subprocess.Popen(['/usr/bin/python3',str(budget_root/'budget_gpu_orchestrator.py')],stdout=budget_orchestration_log,stderr=subprocess.STDOUT)
budget_status.update(state='FULL_SCAN_REUSED_FAST_SELECTION_THEN_BENCHMARK_AND_TRAIN',worker_pid=budget_process.pid)
(budget_root/'budget_control.json').write_text(json.dumps(budget_status,indent=2))
print(json.dumps({'state':budget_status['state'],'pid':budget_process.pid,'optimizer_updates':0,'all_32_member_scan_preserved':True}))
