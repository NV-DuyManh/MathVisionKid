import io,json,tempfile,unittest,zipfile
from pathlib import Path
import math_data_drive_bootstrap as B
def archive(files):
    out=io.BytesIO()
    with zipfile.ZipFile(out,'w') as z:
        for n,v in files.items():z.writestr(n,v)
    return out.getvalue()
class FakeReader:
    def __init__(self,files):self.files=files;self.calls=[]
    def read(self,key,max_bytes):
        self.calls.append(key);b=self.files[key]
        if len(b)>max_bytes:raise ValueError('oversize')
        return b
class Tests(unittest.TestCase):
    def controls(self):
        rec=json.dumps(dict(artifacts={},chat_members=[],pending_discovery=[])).encode();ptr=dict(progress_id=B.PROGRESS_ID,member='run/recipe.json',sha256=B.sha(rec))
        state=json.dumps(dict(latest_all_data_union_recipe=ptr,training_started=False)).encode()
        return FakeReader({B.STATE_ID:state,B.PROGRESS_ID:archive({'run/recipe.json':rec})})
    def test_controls_resolve_fixed_ids_and_hash(self):
        f=self.controls();s,r,p=B.latest_controls(f);self.assertEqual(f.calls,[B.STATE_ID,B.PROGRESS_ID,B.STATE_ID]);self.assertEqual(p['sha256'],B.sha(json.dumps(r).encode()))
    def test_recipe_tamper_rejected(self):
        f=self.controls();f.files[B.PROGRESS_ID]=archive({'run/recipe.json':b'{}'})
        with self.assertRaisesRegex(ValueError,'hash'):B.latest_controls(f)
    def test_control_change_rejected(self):
        f=self.controls();old=f.read
        def read(k,n):
            if f.calls.count(B.STATE_ID)==1 and k==B.STATE_ID:return b'{}'
            return old(k,n)
        f.read=read
        with self.assertRaisesRegex(ValueError,'changed'):B.latest_controls(f)
    def test_bootstrap_only_pinned_code(self):
        files={'code/'+n:('# '+n).encode() for n in B.CODE_FILES};pins={n:dict(bytes=len(b),sha256=B.sha(b)) for n,b in files.items()};files['manifest.json']=json.dumps(dict(members=pins)).encode();files['data/never_read.jsonl']=b'not code'
        raw=archive(files);ref=dict(id='existing',bytes=len(raw),sha256=B.sha(raw));f=FakeReader({'existing':raw})
        with tempfile.TemporaryDirectory() as d:
            result=B.bootstrap_code(f,dict(sgk_finish_runs=[dict(bundle=ref)]),d)
            self.assertEqual(set(p.name for p in Path(d).iterdir()),set(B.CODE_FILES));self.assertEqual(len(result['code_members']),4)
    def test_one_payload_cache_preserves_checkpoint(self):
        a=b'first';b=b'second';refs={B.sha(v):dict(sha256=B.sha(v),bytes=len(v),file_ids=[i],file_names=[i+'.gz']) for i,v in [('a',a),('b',b)]}
        f=FakeReader({'a':a,'b':b})
        with tempfile.TemporaryDirectory() as root:
            cache=B.LazyDriveCache(f,dict(artifacts=refs),Path(root)/'payloads');db=Path(root)/'checkpoint.sqlite';db.write_bytes(b'keep')
            p1=cache['a'];self.assertEqual(cache[B.sha(a)],p1);p2=cache['b'];self.assertFalse(p1.exists());self.assertTrue(p2.exists());self.assertEqual(p2.suffix,'.gz');self.assertEqual(db.read_bytes(),b'keep')
    def test_payload_corruption_stops_before_path(self):
        raw=b'expected';f=FakeReader({'id':b'corrupt!'})
        with tempfile.TemporaryDirectory() as d:
            cache=B.LazyDriveCache(f,dict(artifacts={B.sha(raw):dict(sha256=B.sha(raw),bytes=len(raw),file_ids=['id'],file_names=['x.zip'])}),d)
            with self.assertRaisesRegex(ValueError,'mismatch'):cache['id']
            self.assertFalse(list(Path(d).iterdir()))
if __name__=='__main__':unittest.main()
