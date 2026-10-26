"""Exact two-phrase G1 wording derivative; mathematical choices and frozen parent preserved."""
from pathlib import Path
import json,hashlib,sys,shutil,importlib.util
HERE=Path(__file__).resolve().parent
OUT=HERE/'g1_turn_wording_corrected'
def sha(b):return hashlib.sha256(b).hexdigest()
def dump(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def jl(p,rs):p.write_text(''.join(dump(r)+'\n' for r in rs),encoding='utf-8',newline='\n')
def main():
    assert not (OUT/'derivation_delta.json').exists(),'Completed derivative already exists: do not overwrite frozen evidence'
    parentpins={n:sha((HERE/n).read_bytes()) for n in ['cases.jsonl','chat.jsonl','manifest.json','selfqa7.jsonl']}
    OUT.mkdir(exist_ok=True)
    for p in HERE.iterdir():
        if p.name in ('g1_turn_wording_corrected','__pycache__') or p.name.startswith('peer'):continue
        if p.is_file():shutil.copy2(p,OUT/p.name)
        elif p.name in ('assets','visual_qa'):shutil.copytree(p,OUT/p.name,dirs_exist_ok=True)
    lines=(HERE/'cases.jsonl').read_bytes().splitlines();records=[json.loads(b)for b in lines]
    i=next(i for i,r in enumerate(records)if r['topic']=='notched_piece_rotation_without_reflection');r=records[i];oldhash=sha(lines[i]);before=json.loads(dump(r))
    assert r['worked_steps'][2]['result']=='Chỉ Q xoay 180 độ'
    assert r['expected_answer'][0]['result']=='Q xoay nửa vòng (180 độ); R không đạt'
    r['worked_steps'][2]['result']='Chỉ Q xoay nửa vòng'
    r['expected_answer'][0]['result']='Q xoay nửa vòng; R không đạt'
    lines[i]=dump(r).encode();newhash=sha(lines[i])
    (OUT/'cases.jsonl').write_bytes(b'\n'.join(lines)+b'\n')
    # Preserve all other serialized chat bytes; regenerate only the affected case.
    sys.path.insert(0,str(HERE.parents[2]))
    from exhaustive_primary_math import chat_records
    from math_data_archive_audit import source_projection,linkage_errors
    rawchats=(HERE/'chat.jsonl').read_bytes().splitlines();replacement={c['sample_id']:c for c in chat_records(r)}
    newchats=[]
    for b in rawchats:
        c=json.loads(b)
        if c['source_sample_id']==r['sample_id']:
            new=replacement[c['sample_id']];new.update(source_row_sha256=newhash,quality_status=r['quality_status'],acceptance_status=r['acceptance_status']);b=dump(new).encode()
        newchats.append(b)
    (OUT/'chat.jsonl').write_bytes(b'\n'.join(newchats)+b'\n')
    # Hash-bound evidence updated to the exact derived row; all mathematical model fields remain unchanged.
    for n in ['selfqa7.jsonl','independent_oracles.jsonl','numeric_fraction_decimal.jsonl','adversarial_mutations.jsonl']:
        bs=[]
        for b in (HERE/n).read_bytes().splitlines():
            v=json.loads(b)
            if v.get('sample_id')==r['sample_id']:
                assert v['source_row_sha256']==oldhash;v['source_row_sha256']=newhash;b=dump(v).encode()
            bs.append(b)
        (OUT/n).write_bytes(b'\n'.join(bs)+b'\n')
    spec=importlib.util.spec_from_file_location('g1_derivative_oracle',OUT/'independent_geometry_oracle.py');O=importlib.util.module_from_spec(spec);spec.loader.exec_module(O)
    byid={json.loads(b)['sample_id']:(json.loads(b),sha(b))for b in lines}
    for v,h in byid.values():O.check(v)
    for b in newchats:
        c=json.loads(b);v,h=byid[c['source_sample_id']];assert c['source_row_sha256']==h and not linkage_errors(c,source_projection(v))
    delta=dict(parent_source_sha256=parentpins['cases.jsonl'],derived_source_sha256=sha((OUT/'cases.jsonl').read_bytes()),sample_id=r['sample_id'],parent_raw_row_sha256=oldhash,derived_raw_row_sha256=newhash,fields=[dict(path='worked_steps[2].result',before=before['worked_steps'][2]['result'],after=r['worked_steps'][2]['result']),dict(path='expected_answer[0].result',before=before['expected_answer'][0]['result'],after=r['expected_answer'][0]['result'])],reason='Root semantic grade1 review: use half-turn wording rather than formal degree notation; chosen piece, legal turns and all mathematics unchanged.',other_source_rows_byte_identical=23,other_chat_rows_byte_identical=sum(a==b for a,b in zip(rawchats,newchats)),source_oracle_model_unchanged=before['independent_model']==r['independent_model'],parent_preserved=parentpins)
    (OUT/'derivation_delta.json').write_text(json.dumps(delta,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    manifest=json.loads((HERE/'manifest.json').read_text('utf-8'))
    for pin in manifest['files']:
        p=OUT/pin['path'];pin['sha256']=sha(p.read_bytes());pin['bytes']=p.stat().st_size
    manifest['derivation']=delta;manifest['status']='24_DERIVED_DRAFTS_AUTHOR_QA_ROOT_CROSS_REVIEW_PENDING'
    (OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    receipt=dict(cases=24,chats=96,source_sha256=sha((OUT/'cases.jsonl').read_bytes()),chat_sha256=sha((OUT/'chat.jsonl').read_bytes()),manifest_sha256=sha((OUT/'manifest.json').read_bytes()),other_rows_byte_identical=23,other_chat_rows_byte_identical=delta['other_chat_rows_byte_identical'],all24_oracles_pass=True,all96_source_chat_links=True,parent_hashes_preserved=all(sha((HERE/n).read_bytes())==h for n,h in parentpins.items()),training_started=False,drive_mutated=False)
    (OUT/'validation_receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(dump(receipt))
if __name__=='__main__':main()

