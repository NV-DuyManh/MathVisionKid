import json,sys,traceback,pathlib
from datetime import datetime,timezone
s=dict(full_text_training_status);t=full_text_training_thread
s.update(observed_utc=datetime.now(timezone.utc).isoformat(),worker_alive=t.is_alive())
f=sys._current_frames().get(t.ident)
s['worker_stack']=[dict(function=x.name,line=x.lineno,file=pathlib.Path(x.filename).name) for x in traceback.extract_stack(f)[-20:]] if f else []
s['checkpoint_io_files']=[dict(name=q.name,bytes=q.stat().st_size,mtime=q.stat().st_mtime) for q in pathlib.Path('/content/mathvisionkid_full_text_training/run_artifacts').glob('*') if q.name.startswith(('readback_checkpoint','existing_checkpoint'))]
print(json.dumps(s,ensure_ascii=False))
