import threading,sys,functools,json,pathlib,time
# Coordinate whole immutable put/find/create/readback transactions across the
# separate authenticated publisher clients. Does not alter frozen store bytes.
if 'skill_drive_write_lock' not in globals():skill_drive_write_lock=threading.RLock()
classes={id(m.DriveStore):m.DriveStore for m in list(sys.modules.values()) if m and hasattr(m,'DriveStore') and isinstance(m.DriveStore,type) and getattr(m.DriveStore,'__module__','').endswith(('store','lib'))}
wrapped=[]
for cls in classes.values():
 if cls.__dict__.get('_skill_write_lock_applied'):continue
 old=cls.put
 def make_serial(original):
  @functools.wraps(original)
  def serial(self,*args,**kwargs):
   with skill_drive_write_lock:return original(self,*args,**kwargs)
  return serial
 cls.put=make_serial(old);cls._skill_write_lock_applied=True;wrapped.append(cls.__module__)
proof={'shared_put_lock_applied_to_loaded_stores':wrapped,'observed_unix':time.time(),'frozen_store_bytes_changed':False,'model_or_training_changed':False,'purpose':'Serialize complete immutable Drive put transactions across publisher clients to avoid concurrent find/create races.'}
pathlib.Path('/content/mathvisionkid_skill_recovery_150m_20261024/drive_write_coordination.json').write_text(json.dumps(proof,indent=2)+'\n')
print(json.dumps(proof))
