import pathlib,json,hashlib,sys
from googleapiclient.discovery import build
from google_auth_httplib2 import AuthorizedHttp
import httplib2
root=pathlib.Path('/content/mathvisionkid_recovery_20261026');pubpath=root/'publication/publication_status.json'
state=json.loads(pubpath.read_bytes());assert state['state']=='ERROR'
assert state['last_error']['error']=='Fresh Drive raw readback bytes/SHA mismatch'
assert not conditional_publisher.publisher_thread.is_alive()
proof=state['artifacts']['dev_train_screening.json']
api=build('drive','v3',http=AuthorizedHttp(recovery_credentials,http=httplib2.Http(timeout=60)),cache_discovery=False)
remote=api.files().get_media(fileId=proof['id']).execute();api.close()
assert len(remote)==proof['bytes'] and hashlib.sha256(remote).hexdigest()==proof['sha256']
current=(root/'dev_train_screening.json').read_bytes();before=json.loads(remote);after=json.loads(current)
assert 'against_prior_used_development' in before and 'against_prior_used_development' not in after
assert {k:v for k,v in before.items() if k!='against_prior_used_development'}==after
assert not before['collisions'] and not before['against_prior_used_development']['collisions']
history=root/'error_history/screening_serialization';history.mkdir(parents=True,exist_ok=False)
(history/'publication_error.json').write_bytes(pubpath.read_bytes())
(history/'worker_screening_source_only.json').write_bytes(current)
(root/'dev_train_screening.json').write_bytes(remote)
repair={'reason':'Worker rewrote source-only screening while publisher treated the preflight source+prior screening as immutable. Both source-screen objects are identical and have zero collisions; restore original published complete screening bytes, preserve worker version and original error.',
 'canonical_sha256':hashlib.sha256(remote).hexdigest(),'worker_source_only_sha256':hashlib.sha256(current).hexdigest(),
 'fresh_drive_raw_verified':True,'training_data_targets_config_or_evaluation_changed':False,'training_worker_restarted':False}
(root/'screening_publication_repair.json').write_text(json.dumps(repair,indent=2)+'\n')
result=conditional_publisher.start(recovery_credentials,root)
print(json.dumps({'repair':repair,'publisher':result,'training_worker_pid':conditional_training_process.pid,'worker_exit':conditional_training_process.poll()}))
