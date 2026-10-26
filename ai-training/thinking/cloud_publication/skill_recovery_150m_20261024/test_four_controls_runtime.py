"""Offline fake-API coverage for additive scoped control publication."""
import hashlib, importlib.util, json, sys, tempfile, types, unittest, zipfile, threading
from pathlib import Path


def load(name):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(name+".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


prepare = load("prepare_four_controls_runtime")
transaction = load("four_controls_transaction")
stage_builder = load("prepare_control_stage")


class ControlsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.parent = self.root/"parent"; self.parent.mkdir()
        docs = {"state":{"accepted_cases":1629922,"training_chat_rows":6502344},
                "chat":{"chat_rows":6502344,"count_reconciliation":{"declared_candidate_chat_rows":6502344,"historical_accepted_case_counter_preserved":1629922}}}
        for kind, doc in docs.items():
            doc.update(training_started=False, TRAINING_DATASET_READY=False, preserved_source={"x":"unchanged"})
            doc["latest_corrective5h_branch"]={"branch":"corrective_5h_20261024","decision":"REGRESSION_DO_NOT_PROMOTE"}
            doc["corrective5h_control_publications"]=[{"prior":"corrective history"}]
            doc["skill_recovery_control_publications"]=[{"prior":"recovery history"}]
            doc["latest_skill_recovery_branch"]={"prior":"recovery latest"}
            (self.parent/(kind+".json")).write_bytes(prepare.json_bytes(doc))
        (self.parent/"context.md").write_bytes(b"canonical history\n")
        with zipfile.ZipFile(self.parent/"progress.zip","w") as z:
            z.writestr("prior/source.txt",b"never change source")
        self.parents = {k:{**prepare.pin(self.parent/(k+prepare.EXT[k]),prepare.IDS[k]),"fresh_raw_readback_verified":True} for k in prepare.KINDS}
        self.observation = {"observed_utc":"2026-10-24T01:00:00Z", "worker_alive":True,"training_started":True,"test_fixture":True}
        self.run_metadata={"run":"skill_recovery_150m_20261024","phase":"test fixture only","quality_guaranteed":False}
        self.prepared = prepare.prepare_controls(self.parents,b"canonical history\nnew run\n",self.observation,{},self.root/"prepared",run_metadata=self.run_metadata)
        self.store = {prepare.IDS[k]:Path(self.parents[k]["path"]).read_bytes() for k in prepare.KINDS}
        self.downloads, self.writes = [], []
        owner = self

        class API:
            def files(self): return self
            def update(self,fileId,media_body,**kwargs):
                def execute():
                    owner.store[fileId]=Path(media_body.filename).read_bytes()
                    owner.writes.append(fileId)
                    return {"id":fileId}
                return types.SimpleNamespace(execute=execute)
        self.api=API()
        self.old_download=transaction._download

        def download(api,file_id,dest,expected_size):
            data=self.store[file_id]; dest.write_bytes(data); self.downloads.append(file_id)
            return len(data),hashlib.sha256(data).hexdigest()
        transaction._download=download
        self.old_modules={k:sys.modules.get(k) for k in ("googleapiclient","googleapiclient.http")}
        package=types.ModuleType("googleapiclient"); http=types.ModuleType("googleapiclient.http")
        http.MediaFileUpload=lambda filename,**kwargs:types.SimpleNamespace(filename=filename)
        package.http=http;sys.modules["googleapiclient"]=package;sys.modules["googleapiclient.http"]=http

    def tearDown(self):
        transaction._download=self.old_download
        for key,value in self.old_modules.items():
            if value is None:sys.modules.pop(key,None)
            else:sys.modules[key]=value
        self.temp.cleanup()

    def test_additive_branch_keeps_legacy_flags_and_source(self):
        for kind in ("state","chat"):
            doc=json.loads(Path(self.prepared["controls"][kind]["path"]).read_bytes())
            self.assertIs(doc["training_started"],False)
            self.assertIs(doc["latest_skill_recovery_branch"]["training_started"],True)
            self.assertEqual(doc["preserved_source"],{"x":"unchanged"})
            self.assertEqual(doc["latest_corrective5h_branch"],{"branch":"corrective_5h_20261024","decision":"REGRESSION_DO_NOT_PROMOTE"})
            self.assertEqual(doc["corrective5h_control_publications"],[{"prior":"corrective history"}])
            self.assertEqual(doc["skill_recovery_control_publications"],[{"prior":"recovery history"},{"prior":"recovery latest"}])
            self.assertEqual(doc["latest_skill_recovery_branch"]["run_metadata"],self.run_metadata)
        with zipfile.ZipFile(self.prepared["controls"]["progress"]["path"]) as z:
            self.assertEqual(z.read("prior/source.txt"),b"never change source")

    def test_state_last_every_control_readback_and_idempotent_retry(self):
        result=transaction.publish_controls(self.api,self.prepared["parents"],self.prepared["controls"],self.root/"runtime")
        self.assertEqual(self.writes,[prepare.IDS[k] for k in prepare.KINDS])
        self.assertEqual([x["kind"] for x in result["verified_writes"]],list(prepare.KINDS))
        self.assertTrue(all(x["fresh_raw_readback_verified"] for x in result["verified_writes"]))
        self.assertNotIn("training_started",result)
        self.assertEqual(len(self.downloads),12)
        transaction.publish_controls(self.api,self.prepared["parents"],self.prepared["controls"],self.root/"runtime")
        self.assertEqual(len(self.writes),4)

    def test_changed_remote_parent_stops_before_write(self):
        self.store[prepare.IDS["chat"]]=b"changed concurrently"
        with self.assertRaisesRegex(RuntimeError,"changed from both"):
            transaction.publish_controls(self.api,self.prepared["parents"],self.prepared["controls"],self.root/"runtime")
        self.assertEqual(self.writes,[])

    def test_removed_recovery_history_rejected_before_any_remote_write(self):
        ref=self.prepared['controls']['chat'];path=Path(ref['path'])
        changed=json.loads(path.read_bytes());changed['skill_recovery_control_publications']=[]
        path.write_bytes(prepare.json_bytes(changed))
        self.prepared['controls']['chat']=prepare.pin(path,prepare.IDS['chat'])
        with self.assertRaisesRegex(ValueError,'prior recovery history'):
            transaction.publish_controls(self.api,self.prepared['parents'],self.prepared['controls'],self.root/'bad-history')
        self.assertEqual(self.writes,[])

    def test_transaction_rejects_other_existing_id_even_if_distinct(self):
        parents={kind:dict(ref) for kind,ref in self.prepared['parents'].items()}
        parents['state']['id']='another-distinct-existing-ID'
        with self.assertRaisesRegex(ValueError,'exact existing control IDs'):
            transaction.publish_controls(self.api,parents,self.prepared['controls'],self.root/'bad-ID')
        self.assertEqual(self.writes,[])

    def test_builder_only_writes_fresh_stage_and_accepts_context_bytes_metadata(self):
        context=b'canonical history\nnew quality phase\n'
        context_path=self.root/'canonical.md';context_path.write_bytes(context)
        metadata={'run':'skill_recovery_150m_20261024','stage':'bounded fake test','human_certification':False}
        output=self.root/'stage_controls_runtime.py'
        result=stage_builder.build_stage(context_path.read_bytes(),metadata,{},output)
        self.assertFalse(result['stage_executed']);self.assertFalse(result['drive_calls_made'])
        self.assertEqual(result['canonical_context_sha256'],hashlib.sha256(context).hexdigest())
        self.assertEqual(context_path.read_bytes(),context)
        code=output.read_text(encoding='utf-8');compile(code,str(output),'exec')
        self.assertIn("recovery_credentials",code);self.assertIn("recovery_process",code)
        self.assertIn("recovery_controls_thread=threading.Thread",code)
        self.assertEqual(self.writes,[])
        with self.assertRaises(FileExistsError):stage_builder.build_stage(context,metadata,{},output)

    def test_builder_rejects_payload_path_traversal_and_bad_metadata(self):
        evidence=self.root/'evidence.json';evidence.write_text('{}',encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'unsafe archive-relative'):
            stage_builder.build_stage(b'context',{}, {'../escape.json':evidence},self.root/'badstage.py')
        with self.assertRaisesRegex(ValueError,'run metadata object'):
            stage_builder.build_stage(b'context',[],{},self.root/'badstage2.py')

    def test_capture_reads_branch_metadata_without_opening_payloads_or_logs(self):
        (self.root/'training').mkdir();(self.root/'publication').mkdir()
        (self.root/'training'/'progress.json').write_text('{"training_started": true, "step": 50}',encoding='utf-8')
        (self.root/'training'/'best.json').write_text('{"kind": "untrained_base"}',encoding='utf-8')
        (self.root/'publication'/'publication_status.json').write_text('{"checkpoints": {}}',encoding='utf-8')
        (self.root/'training'/'successful_ids.jsonl').write_bytes(b'not JSON metadata and must never be read')
        captured=prepare.capture_branch_metadata(self.root,worker_observation=self.observation)
        self.assertTrue(captured['training_started'])
        self.assertIn('training/best.json',captured['metadata_files'])
        self.assertIn('publication/publication_status.json',captured['metadata_files'])
        self.assertNotIn('training/successful_ids.jsonl',captured['metadata_files'])

    def test_context_replacement_and_invented_id_rejected(self):
        with self.assertRaisesRegex(ValueError,"exact fresh parent prefix"):
            prepare.prepare_controls(self.parents,b"replacement",self.observation,{},self.root/"bad1")
        changed={k:dict(v) for k,v in self.parents.items()};changed["state"]["id"]="new ID"
        with self.assertRaisesRegex(ValueError,"ID/fresh-parent"):
            prepare.prepare_controls(changed,b"canonical history\n",self.observation,{},self.root/"bad2")

    def test_retained_parent_mutation_stops_before_write(self):
        Path(self.prepared["parents"]["chat"]["path"]).write_bytes(b"mutated locally")
        with self.assertRaisesRegex(ValueError,"retained parent"):
            transaction.publish_controls(self.api,self.prepared["parents"],self.prepared["controls"],self.root/"runtime")
        self.assertEqual(self.writes,[])

    def test_authorized_http_recursive_refresh_does_not_deadlock(self):
        """AuthorizedHttp uses self.request on a refresh retry; fake that shape."""
        class HTTP:
            def request(self, uri, method="GET", body=None, headers=None, **kwargs):
                if not kwargs.get("_credential_refresh_attempt"):
                    return self.request(uri, method, body=body, headers=headers,
                                        _credential_refresh_attempt=1)
                return types.SimpleNamespace(status=200), b"ok"
        api=types.SimpleNamespace(_http=HTTP(),close=lambda:None)
        discovery=types.ModuleType("googleapiclient.discovery")
        discovery.build=lambda *a,**kw:api
        prior=sys.modules.get("googleapiclient.discovery")
        sys.modules["googleapiclient.discovery"]=discovery
        results=[]
        def run():
            with transaction.own_throttled_client(object(),min_request_interval=0) as client:
                results.append(client._http.request("https://example.invalid"))
        thread=threading.Thread(target=run,daemon=True)
        try:
            thread.start();thread.join(timeout=2)
            self.assertFalse(thread.is_alive(),"recursive auth-refresh wrapper deadlocked")
            self.assertEqual(results[0][1],b"ok")
        finally:
            if prior is None:sys.modules.pop("googleapiclient.discovery",None)
            else:sys.modules["googleapiclient.discovery"]=prior


if __name__=="__main__":unittest.main()
