import sys,json,time,pathlib,subprocess
out={'observed_unix':time.time()}
for frame in sys._current_frames().values():
 while frame:
  if frame.f_code.co_name=='scan_and_sample':
   loc=frame.f_locals;out.update(line=frame.f_lineno,current_case=str(loc.get('case',{})),current_label=loc.get('label'),selected=len(loc.get('chosen',[])),found=len(loc.get('found_row_hashes',[])),elapsed=time.monotonic()-loc['started'])
  frame=frame.f_back
out['db_files']={p.name:p.stat().st_size for p in (budget_root/'sampling/run').glob('*.sqlite3*')}
out['resources']=subprocess.run(['df','-h','/content'],capture_output=True,text=True).stdout
print(json.dumps(out,ensure_ascii=False))
