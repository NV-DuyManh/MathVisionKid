"""Data-only reviewed finite append. No Drive, training or old-source edits."""
from pathlib import Path
from collections import Counter
from decimal import Decimal, localcontext
from fractions import Fraction
import argparse, hashlib, json, re, zipfile
import exhaustive_colab_loader as L
from exhaustive_primary_math import chat_records
from sgk_gap_release import evaluate

HERE=Path(__file__).resolve().parent
RUN=HERE/'cloud_publication/sgk_remaining_20261020'
PRIOR=HERE/'cloud_publication/sgk_finish_20261020'
OLD=HERE/'cloud_publication/sgk_page_audit_20261019'
DIRS=['g5_applied_text','g5_geometry_text','g34_structure_polished']
FIELDS=['problem','givens','requested_quantity','student_work','worked_steps','expected_answer','initial_guidance','hints']
def sha(b): return hashlib.sha256(b).hexdigest()
def dump(x): return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def read(p): return json.loads(p.read_text('utf-8'))
def rows(p): return [(json.loads(b),sha(b)) for b in p.read_bytes().splitlines() if b.strip()]
def write(p,x): p.write_text(json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8')
def jl(p,x): p.write_text(''.join(dump(r)+'\n' for r in x),encoding='utf-8',newline='\n')

def audit():
    out=RUN/'release';out.mkdir(exist_ok=True)
    root=read(RUN/'root_evidence/content_review.json')
    protected=set(read(OLD/'extensions/protected_numeric_signatures.json')['signatures'])
    prior=rows(OLD/'current_sources.jsonl')+rows(OLD/'release/accepted_cases.jsonl')+rows(PRIOR/'release/accepted_cases.jsonl')
    norm=lambda x:re.sub(r'\s+',' ',x).strip().casefold()
    ids={r['sample_id'] for r,h in prior};qs={norm(r['problem']) for r,h in prior}
    accepted=[];chats=[];reviews=[];checks=[];eligibility=[];inputs=[]
    for name in DIRS:
        folder=RUN/name;src=folder/'cases.jsonl';source=rows(src)
        rr=root['batches'][name]
        assert rr['cases_sha256']==sha(src.read_bytes())
        assert rr['chat_sha256']==sha((folder/'chat.jsonl').read_bytes())
        assert rr['actual_content_read'] and rr['status']=='PASS' and len(rr['reviews'])==len(source)
        per={r['sample_id']:r for r in rr['reviews']}
        for ref in rr['peer_evidence']:
            assert sha((folder/ref['file']).read_bytes())==ref['sha256']
        inputs.append(dict(directory=name,cases=len(source),source_sha256=rr['cases_sha256'],peer_evidence=rr['peer_evidence']))
        for r,parent in source:
            sid=r['sample_id'];q=norm(r['problem']);review=per[sid]
            assert sid not in ids and q not in qs
            ids.add(sid);qs.add(q)
            assert review['source_row_sha256']==parent and len(review['criteria'])==7 and all(v['passed'] for v in review['criteria'])
            assert review['actual_fields']=={k:r[k] for k in FIELDS}
            assert not any(r.get(k) for k in ['human_verified','teacher_certified','owner_human_reviewed'])
            assert [h['level'] for h in r['hints']]==[1,2,3]
            prev={};numeric=[]
            for s in r['worked_steps']:
                assert s['reason'] and s['explanation'] and 'unit' in s
                if s.get('expression'):
                    expr=re.sub(r'\{(s\d+)\}',lambda m:'('+str(Fraction(prev[m[1]]))+')',s['expression'])
                    f=evaluate(expr,'fraction');assert f==Fraction(s['result'])
                    with localcontext() as ctx:
                        ctx.prec=90;d=evaluate(expr,'decimal');assert abs(d-Decimal(f.numerator)/Decimal(f.denominator))<Decimal('1e-70')
                    numeric.append(dict(step_id=s['step_id'],expression=expr,exact=str(f),decimal_agrees=True))
                prev[s['step_id']]=s['result']
            r['acceptance_status']='ACCEPTED_VALIDATED_OWNER_PREAUTHORIZED'
            r['quality_status']='CONTENT_QA_AND_CROSS_REVIEW_PASSED'
            r['provenance'].update(acceptance_basis='OWNER_PREAUTHORIZED_AFTER_FULL_CONTENT_QA_AND_CROSS_REVIEW',reviewed_draft_row_sha256=parent,human_content_review_completed=False)
            h=sha(dump(r).encode());accepted.append(r)
            reviews.append(dict(sample_id=sid,reviewed_draft_row_sha256=parent,exported_row_sha256=h,criteria=review['criteria'],actual_fields_read=FIELDS,semantic_decision=review['semantic_decision'],human_review_claimed=False))
            checks.append(dict(sample_id=sid,source_row_sha256=h,reviewed_draft_row_sha256=parent,numeric=numeric,peer_evidence=rr['peer_evidence']))
            overlap=sorted((set(L.source_signatures(r))|set(r.get('canonical_signatures',[])))&protected)
            eligibility.append(dict(sample_id=sid,source_row_sha256=h,training_eligible=True,basis='OWNER_HASH_SCOPED_NUMERIC_EXCEPTION_AFTER_QA' if overlap else 'CONTENT_QA_AND_CROSS_REVIEW',blind_numeric_overlap_hashes=overlap,numeric_benchmark_independence_claimed=False))
            for c in chat_records(r):
                c.update(source_row_sha256=h,acceptance_status=r['acceptance_status'],quality_status=r['quality_status']);L.validate_chat(c)
                target=json.loads(c['messages'][2]['content'])
                if c['mode']=='worked_solution':assert target['steps']==r['worked_steps'] and target['answer']==r['expected_answer']
                else:
                    hint=r['hints'][int(c['mode'][-1])-1];assert target==dict(hint=hint['hint'],question=hint['question'])
                chats.append(c)
    assert len(accepted)==36 and len(chats)==144 and len({r['sample_id'] for r in chats})==144
    for n,data in [('accepted_cases',accepted),('accepted_chat',chats),('cross_reviews',reviews),('independent_oracles',checks),('training_eligibility_by_hash',eligibility)]:jl(out/(n+'.jsonl'),data)
    tokenizer=Path.home()/'.cache/huggingface/hub/models--Qwen--Qwen3-1.7B/snapshots'/L.REVISION
    token=L.full_token_audit(chats,L.load_qwen_tokenizer(tokenizer));token['scope']='ALL_144_NEW_CHAT_ONLY_NO_TRAINING';write(out/'token_audit.json',token)
    report=dict(cases=36,chat_rows=144,by_grade=dict(Counter(str(r['grade']) for r in accepted)),by_topic=dict(Counter(r['topic'] for r in accepted)),master_counts=dict(Counter(r['coverage']['finite_master_id'] for r in accepted)),numeric_steps=sum(len(r['numeric']) for r in checks),hash_numeric_exception_cases=sum(bool(r['blind_numeric_overlap_hashes']) for r in eligibility),input_reviews=inputs,training_started=False,all_sgk_forms_covered=False,full_archive_audit_complete=False,core_unchanged=495,old_sources_unchanged=True)
    write(out/'audit_report.json',report);print(dump(report))

def snapshot():
    report=read(RUN/'release/audit_report.json');members={}
    for p in sorted(RUN.rglob('*')):
        if p.is_file() and p.suffix in ('.json','.jsonl','.py','.sqlite','.txt') and not p.name.startswith(('bundle_','publish_','prewrite_')):
            members['data/'+p.relative_to(RUN).as_posix()]=p.read_bytes()
    code=['sgk_remaining_release.py','sgk_remaining_publish_controls.py','sgk_remaining_g5_applied.py','sgk_remaining_geometry.py','sgk_remaining_structure.py','math_data_candidate_stream.py','test_math_data_candidate_stream.py','math_data_archive_audit.py','math_data_portable_resume.py','math_data_source_hash_overlay.py','exhaustive_colab_loader.py','exhaustive_primary_math.py','exhaustive_curriculum_scope.py','sgk_gap_release.py']
    for n in code:
        p=HERE/n
        if p.exists():members['code/'+n]=p.read_bytes()
    for n in ['sgk_remaining_root_review.py','sgk_remaining_union_recipe.py','sgk_finish_g5_text_append.py','sgk_finish_g1_text_append.py','sgk_finish_g3_reasoning.py','sgk_g4extra_peer_oracle.py']:
        p=HERE/n
        if p.exists():members['code/'+n]=p.read_bytes()
    assert not any(re.search(r'\.blob\.core\.windows\.net|Bearer\s+[A-Za-z0-9]|[?&]sig=',b.decode('utf-8',errors='ignore'),re.I) for b in members.values())
    manifest=dict(schema='sgk_remaining_append.v1',accepted_cases=36,chat_rows=144,source_member='data/release/accepted_cases.jsonl',chat_member='data/release/accepted_chat.jsonl',training_started=False,full_archive_audit_complete=False,all_sgk_forms_covered=False,members={n:dict(bytes=len(b),sha256=sha(b)) for n,b in members.items()})
    members['manifest.json']=(dump(manifest)+'\n').encode();tmp=RUN/'remaining_append.partial.zip'
    with zipfile.ZipFile(tmp,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for n,b in members.items():
            info=zipfile.ZipInfo(n,(2026,10,20,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,b)
    with zipfile.ZipFile(tmp) as z:assert not z.testzip() and all(z.read(n)==b for n,b in members.items())
    h=sha(tmp.read_bytes());target=RUN/f'MathVisionKid_SGK_REMAINING_APPEND_20261020_{h[:16]}.zip';tmp.replace(target)
    write(RUN/'bundle_local.json',dict(path=str(target),file_name=target.name,bytes=target.stat().st_size,sha256=h,member_count=len(members),cases=36,chat_rows=144));print(dump(read(RUN/'bundle_local.json')))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['audit','snapshot']);a=p.parse_args();globals()[a.action]()
