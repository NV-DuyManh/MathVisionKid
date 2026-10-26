import json,threading,sys,traceback,pathlib
from datetime import datetime,timezone
_status=dict(globals().get('full_text_training_status',{}))
_thread=globals().get('full_text_training_thread')
_status.update(observed_utc=datetime.now(timezone.utc).isoformat(),worker_alive=bool(_thread and _thread.is_alive()))
if _thread and _thread.is_alive():
    _frame=sys._current_frames().get(_thread.ident)
    _status['worker_stack']=[dict(function=f.name,line=f.lineno,file=pathlib.Path(f.filename).name) for f in traceback.extract_stack(_frame)[-8:]] if _frame else []
if _status.get('state')=='SETUP_OR_TRAINING_STOPPED':
    _log=pathlib.Path('/content/mathvisionkid_full_text_training/dependency_install.log')
    if _log.exists():_status['dependency_log_tail']=_log.read_text()[-2500:]
print(json.dumps(_status,ensure_ascii=False))
