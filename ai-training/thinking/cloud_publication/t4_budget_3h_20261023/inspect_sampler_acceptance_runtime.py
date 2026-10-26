import sys,json,time
scan=None
for f in sys._current_frames().values():
    while f:
        if f.f_code.co_name=='scan_and_sample':
            scan={'counts':dict(f.f_locals.get('counts',{})),'member_index':f.f_locals.get('mi'),'row_acceptance_status':f.f_locals.get('row',{}).get('acceptance_status')}
        f=f.f_back
print(json.dumps({'observed_unix':time.time(),'scan':scan,'worker_alive':budget_process.poll() is None,'worker_log_tail':(budget_root/'training.log').read_text()[-2000:]}))
