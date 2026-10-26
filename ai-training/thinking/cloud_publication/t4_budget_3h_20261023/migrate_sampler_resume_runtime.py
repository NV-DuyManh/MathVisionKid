import sqlite3,json,hashlib,collections
assert not sampling_worker_thread.is_alive()
db=sqlite3.connect(budget_root/'sampling/run/stratified_sampling.sqlite3')
db.execute('CREATE TABLE IF NOT EXISTS member_scan_state(member_key TEXT PRIMARY KEY,rows_seen INTEGER NOT NULL,train_rows INTEGER NOT NULL,validation_rows INTEGER NOT NULL,test_rows INTEGER NOT NULL,member_complete INTEGER NOT NULL)')
inventory=json.loads((budget_root/'sampling_metadata_inventory.json').read_text())
members=inventory['chat_member_metadata'];counts=collections.Counter(m['sha256'] for m in members)
migrated=[]
for sha,seen,train,complete in db.execute('SELECT * FROM scan_state').fetchall():
    matched=[m for m in members if m['sha256']==sha]
    if complete==1 and counts[sha]==1 and matched[0]['rows']==seen==train:
        m=matched[0];key=hashlib.sha256(json.dumps({k:m[k] for k in ('sha256','file_name','file_id','bytes','rows')},sort_keys=True,separators=(',',':')).encode()).hexdigest()
        db.execute('INSERT OR REPLACE INTO member_scan_state VALUES (?,?,?,?,?,1)',(key,seen,train,0,0));migrated.append({'member':m['file_name'],'rows':seen,'member_key':key,'archive_hash_was_verified_before_prior_completed_marker':True})
db.commit();db.close()
(budget_root/'sampling/legacy_completed_member_migration.json').write_text(json.dumps(migrated,indent=2))
INVENTORY_PATH=budget_root/'sampling_metadata_inventory.json'
print(json.dumps({'migrated':migrated,'new_scan':launch_t4_sampler()}))
