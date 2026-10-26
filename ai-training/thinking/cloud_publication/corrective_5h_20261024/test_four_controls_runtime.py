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


class ControlsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.parent = self.root/"parent"; self.parent.mkdir()
        docs = {"state":{"accepted_cases":1629922,"training_chat_rows":6502344},
                "chat":{"chat_rows":6502344,"count_reconciliation":{"declared_candidate_chat_rows":6502344,"historical_accepted_case_counter_preserved":1629922}}}
        for kind, doc in docs.items():
            doc.update(training_started=False, TRAINING_DATASET_READY=False, preserved_source={"x":"unchanged"})
            (self.parent/(kind+".json")).write_bytes(prepare.json_bytes(doc))
        (self.parent/"context.md").write_bytes(b"canonical history\n")
        with zipfile.ZipFile(self.parent/"progress.zip","w") as z:
            z.writestr("prior/source.txt",b"never change source")
        self.parents = {k:{**prepare.pin(self.parent/(k+prepare.EXT[k]),prepare.IDS[k]),"fresh_raw_readback_verified":True} for k in prepare.KINDS}
        self.observation = {"observed_utc":"2026-10-24T01:00:00Z", "worker_alive":True,"training_started":True,"test_fixture":True}
        self.prepared = prepare.prepare_controls(self.parents,b"canonical history\nnew run\n",self.observation,{},self.root/"prepared")
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
            self.assertIs(doc["latest_corrective5h_branch"]["training_started"],True)
            self.assertEqual(doc["preserved_source"],{"x":"unchanged"})
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
