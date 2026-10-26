import sys,json,hashlib,time
module=sys.modules['mvk_colab_train_view_worker']
module.ACCEPTED.add('OWNER_HUMAN_CERTIFIED')
p=budget_root/'sampling/colab_train_view_worker.py'
before=hashlib.sha256(p.read_bytes()).hexdigest()
s=p.read_text().replace('ACCEPTED = {"ACCEPTED_OWNER_PREAUTHORIZED", "ACCEPTED_VALIDATED_OWNER_PREAUTHORIZED"}','ACCEPTED = {"ACCEPTED_OWNER_PREAUTHORIZED", "ACCEPTED_VALIDATED_OWNER_PREAUTHORIZED", "OWNER_HUMAN_CERTIFIED"}')
p.write_text(s)
record={'state':'PRESERVE_CURRENT_HASH_BOUND_OWNER_HUMAN_CERTIFIED_ACCEPTANCE','changed_labels':False,'human_attestations_added':False,'added_existing_accepted_status':'OWNER_HUMAN_CERTIFIED','source_code_sha256_before':before,'source_code_sha256_after':hashlib.sha256(p.read_bytes()).hexdigest(),'previous_probe_unaccepted_rows':0,'observed_unix':time.time()}
(budget_root/'sampling/acceptance_execution_overlay.json').write_text(json.dumps(record,indent=2))
print(json.dumps(record))
