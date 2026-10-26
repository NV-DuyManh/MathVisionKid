import pathlib,json,hashlib
r=pathlib.Path('/content/mathvisionkid_skill_recovery_150m_20261024');s=json.loads((r/'publication/publication_status.json').read_bytes());dif=[]
for n,pin in s['artifacts'].items():
 q=r/n
 if q.is_file():
  h=hashlib.sha256(q.read_bytes()).hexdigest()
  if h!=pin['sha256']:dif.append({'name':n,'actual_local_sha256':h,'published_sha256':pin['sha256'],'bytes':q.stat().st_size,'published_bytes':pin['bytes']})
print(json.dumps({'differences':dif,'training_worker_alive':skill_training_process.poll() is None,'publisher_thread_alive':skill_publisher.publisher_thread.is_alive()}))
