import pathlib,json,subprocess,os
root=pathlib.Path('/content/mathvisionkid_t4_budget_3h_20261023')
out={'pid':os.getpid(),'prior_runtime_directory_exists':root.exists()}
if root.exists():
 for n in ['training/run_complete.json','training/final_runtime_evidence.json','drive_publication/publication_status.json','benchmark_id_binding.json']:
  p=root/n;out[n]=json.loads(p.read_bytes()) if p.exists() and p.stat().st_size<100000 else {'exists':p.exists(),'bytes':p.stat().st_size if p.exists() else None}
try:out['gpu']=subprocess.check_output(['nvidia-smi','--query-gpu=name,memory.total,memory.used,utilization.gpu','--format=csv,noheader'],text=True,timeout=10)
except Exception as e:out['gpu_error']=str(e)
print(json.dumps(out,ensure_ascii=False))
