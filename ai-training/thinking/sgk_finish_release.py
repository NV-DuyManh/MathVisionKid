"""Finite append acceptance, whole-new-chat audit and portable checkpoint export.

No training, model weights, production changes or Drive calls. Root must read
actual fields and bind peer review before this derivation. Old sources frozen.
"""
from pathlib import Path
from collections import Counter
from fractions import Fraction
from decimal import Decimal,localcontext
import argparse,json,hashlib,re,zipfile
from datetime import datetime,timezone
import exhaustive_colab_loader as L
from exhaustive_primary_math import chat_records
from sgk_gap_release import evaluate

HERE=Path(__file__).resolve().parent
OLD=HERE/'cloud_publication/sgk_page_audit_20261019'
RUN=HERE/'cloud_publication/sgk_finish_20261020'
OUT=RUN/'release'
DIRECTORIES=['g2_append','g3_reasoning','g1_text_append','g5_text_append','remaining_basic_text','g5_second_text','g34_network_text']
def sha(b):return hashlib.sha256(b).hexdigest()
def dump(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def read(p):return json.loads(p.read_text('utf-8'))
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8')
def rows(p):return [(json.loads(b),sha(b)) for b in p.read_bytes().splitlines() if b.strip()]
def jl(p,rs):p.write_text(''.join(dump(r)+'\n' for r in rs),encoding='utf-8',newline='\n')
def master(r):return r.get('coverage',{}).get('finite_master_id') or {'two_jug_transfer':'two_jug_state_transfer','operator_synthesis':'finite_operator_synthesis'}.get(r['topic'],r['topic'])

def audit():
    OUT.mkdir(exist_ok=True)
    old=rows(OLD/'current_sources.jsonl')+rows(OLD/'release/accepted_cases.jsonl')
    norm=lambda s:re.sub(r'\s+',' ',s).strip().casefold()
    oldids={r['sample_id'] for r,h in old};oldquestions={norm(r['problem']) for r,h in old}
    protected_path=OLD/'extensions/protected_numeric_signatures.json';protected=set(read(protected_path)['signatures'])
    accepted=[];chats=[];qa=[];oracles=[];eligibility=[];inputs=[];ids=set();questions=set();steps_count=0
    for directory in DIRECTORIES:
        source=RUN/directory/'cases.jsonl';peerpath=source.parent/'peer_review.json'
        if not peerpath.exists():raise ValueError('Cross review not complete: '+directory)
        peer=read(peerpath);raw=source.read_bytes();rws=rows(source)
        assert peer['source_file_sha256']==sha(raw) and peer['seven_criteria_pass_count']==len(rws)
        assert peer['chat_file_sha256']==sha((source.parent/'chat.jsonl').read_bytes())
        peerrows={x['sample_id']:x for x in peer['reviews']};assert len(peerrows)==len(rws)
        inputs.append(dict(directory=directory,source_file_sha256=sha(raw),peer_review_sha256=sha(peerpath.read_bytes()),cases=len(rws)))
        for r,parent in rws:
            sid=r['sample_id'];question=norm(r['problem']);assert sid not in oldids|ids and question not in oldquestions|questions
            ids.add(sid);questions.add(question);review=peerrows[sid];assert review['source_row_sha256']==parent and review['status'].startswith('PASS')
            assert not any(r.get(k) for k in ['human_verified','teacher_certified','owner_human_reviewed'])
            assert [h['level'] for h in r['hints']]==[1,2,3] and r['initial_guidance']
            numeric=[];previous={}
            for s in r['worked_steps']:
                assert s['reason'] and s['explanation'] and 'unit' in s
                if s.get('expression'):
                    expanded=re.sub(r'\{(s\d+)\}',lambda m:'('+str(Fraction(previous[m[1]]))+')',s['expression'])
                    f=evaluate(expanded,'fraction');assert f==Fraction(s['result'])
                    with localcontext() as ctx:
                        ctx.prec=90;d=evaluate(expanded,'decimal');assert abs(d-Decimal(f.numerator)/Decimal(f.denominator))<Decimal('1e-70')
                    numeric.append(dict(step_id=s['step_id'],expression=s['expression'],expanded_expression=expanded,exact=str(f),decimal_agrees=True));steps_count+=1
                previous[s['step_id']]=s['result']
            r['acceptance_status']='ACCEPTED_VALIDATED_OWNER_PREAUTHORIZED';r['quality_status']='CONTENT_QA_AND_CROSS_REVIEW_PASSED'
            r['provenance'].update(acceptance_basis='OWNER_PREAUTHORIZED_AFTER_FULL_CONTENT_QA_AND_CROSS_REVIEW',reviewed_draft_row_sha256=parent,content_human_review_completed=False)
            exported=sha(dump(r).encode());accepted.append(r)
            qa.append(dict(sample_id=sid,source_row_sha256=exported,reviewed_draft_row_sha256=parent,status='PASS',criteria=review['criteria'],actual_fields_read=review['actual_fields_read'],review_role=review.get('review_role',peer.get('reviewer','CONTENT_CROSS_REVIEW')),human_review_claimed=False))
            oracles.append(dict(sample_id=sid,source_row_sha256=exported,reviewed_draft_row_sha256=parent,numeric=numeric,independent_peer_oracle=review.get('structural_oracle',review.get('independent_oracle')),peer_review_file_sha256=sha(peerpath.read_bytes())))
            overlap=sorted((set(L.source_signatures(r))|set(r.get('canonical_signatures',[])))&protected)
            eligibility.append(dict(sample_id=sid,source_row_sha256=exported,training_eligible=True,basis='OWNER_HASH_SCOPED_NUMERIC_EXCEPTION_AFTER_QA' if overlap else 'CONTENT_QA_AND_CROSS_REVIEW',blind_numeric_overlap_hashes=overlap,numeric_benchmark_independence_claimed=False))
            for c in chat_records(r):
                c.update(source_row_sha256=exported,acceptance_status=r['acceptance_status'],quality_status=r['quality_status']);L.validate_chat(c)
                target=json.loads(c['messages'][2]['content'])
                if c['mode']=='worked_solution':assert target['steps']==r['worked_steps'] and target['answer']==r['expected_answer']
                else:
                    h=r['hints'][int(c['mode'][-1])-1];assert target==dict(hint=h['hint'],question=h['question'])
                chats.append(c)
    assert len(chats)==4*len(accepted) and len({r['sample_id'] for r in chats})==len(chats)
    jl(OUT/'accepted_cases.jsonl',accepted);jl(OUT/'accepted_chat.jsonl',chats);jl(OUT/'cross_reviews.jsonl',qa);jl(OUT/'independent_oracles.jsonl',oracles);jl(OUT/'training_eligibility_by_hash.jsonl',eligibility)
    tokenizer=Path.home()/'.cache/huggingface/hub/models--Qwen--Qwen3-1.7B/snapshots'/L.REVISION
    token=L.full_token_audit(chats,L.load_qwen_tokenizer(tokenizer));token['scope']='ALL_NEW_CHAT_NOT_FULL_ARCHIVE_NO_TRAINING';write(OUT/'token_audit.json',token)
    report=dict(cases=len(accepted),chat_rows=len(chats),by_grade=dict(Counter(str(r['grade']) for r in accepted)),by_topic=dict(Counter(r['topic'] for r in accepted)),master_branch_counts=dict(Counter(master(r) for r in accepted)),representation_master_count=len({master(r) for r in accepted}),numeric_steps=steps_count,hash_numeric_exception_cases=sum(bool(x['blind_numeric_overlap_hashes']) for x in eligibility),input_reviews=inputs,training_started=False,full_archive_token_split_audit_complete=False,all_sgk_forms_covered=False,preservation='No old source, 299 signoff, frozen benchmark or core495 edits. Exact author source bytes and pre-repair chats remain audit evidence.')
    queue=read(RUN/'crossgrade_mapping/resume_queue.json');by_master={}
    for r in accepted:by_master.setdefault(master(r),[]).append(r)
    resolutions=[]
    for m in queue['masters']:
        new=by_master.get(m['master_id'],[])
        rec=dict(master_id=m['master_id'],original_category=m['category'],candidate_ids=m['candidate_ids'],accepted_examples=[dict(sample_id=r['sample_id'],exported_row_sha256=sha(dump(r).encode()),grade=r['grade'],branch=r.get('coverage',{}).get('branch',r['topic'])) for r in new])
        covered_candidates=set()
        for r in new:
            explicit=r.get('coverage',{}).get('candidate_ids')
            if explicit:covered_candidates.update(explicit)
            elif m['master_id']=='finite_operator_synthesis':covered_candidates.add('g3_operator_synthesis')
            elif len(m['candidate_ids'])==1:covered_candidates.update(m['candidate_ids'])
        rec['covered_candidate_branches_in_this_append']=sorted(covered_candidates)
        rec['pending_candidate_alias_check']=[k for k in m['candidate_ids'] if k not in covered_candidates] if new else []
        rec['status']='EXACT_OLD_COVERAGE_RETAINED' if m['category']=='COVERED_EXACT_ID_HASH' else 'ASSET_LIMITATION_RETAINED' if m['category']=='ASSET_ONLY_LIMITATION' else 'NEW_TEXT_EXAMPLES_ACCEPTED_ALIAS_CHECK_PENDING' if new and rec['pending_candidate_alias_check'] else 'NEW_TEXT_REPRESENTATION_EXAMPLES_ACCEPTED' if new else 'FINITE_MASTER_NOT_YET_AUTHORED'
        resolutions.append(rec)
    write(OUT/'candidate_resolution_overlay.json',dict(schema='candidate_resolution_overlay.v1',parent_queue_sha256=sha((RUN/'crossgrade_mapping/resume_queue.json').read_bytes()),masters=resolutions,status_counts=dict(Counter(r['status'] for r in resolutions)),all_sgk_forms_covered=False,modality='Original explicit text reasoning only; visual or physical mastery not certified',g2_confirmed_masters_authored=14,g2_merged_or_asset_masters_still_open=37))
    write(OUT/'audit_report.json',report);print(dump(report))

def snapshot():
    report=read(OUT/'audit_report.json');members={}
    for directory in DIRECTORIES+['crossgrade_mapping','portable_resume','source_hash_overlay','root_evidence','remote_metadata','release']:
        for p in sorted((RUN/directory).rglob('*')):
            if p.is_file() and p.suffix in ('.json','.jsonl','.py','.sqlite') and not p.name.endswith('-wal'):
                members['data/'+p.relative_to(RUN).as_posix()]=p.read_bytes()
    for p in sorted(HERE.glob('sgk_finish*.py')):members['code/'+p.name]=p.read_bytes()
    for name in ['math_data_portable_resume.py','math_data_archive_audit.py','math_data_source_hash_overlay.py','test_math_data_portable_resume.py','exhaustive_colab_loader.py','exhaustive_primary_math.py','exhaustive_curriculum_scope.py','sgk_gap_release.py','sgk_g4extra_peer_oracle.py']:
        members['code/'+name]=(HERE/name).read_bytes()
    assert not any(re.search(r'\.blob\.core\.windows\.net|Bearer\s+[A-Za-z0-9]|[?&]sig=',b.decode('utf-8',errors='ignore'),re.I) for b in members.values())
    manifest=dict(schema='sgk_finish_append.v1',accepted_cases=report['cases'],chat_rows=report['chat_rows'],source_member='data/release/accepted_cases.jsonl',chat_member='data/release/accepted_chat.jsonl',portable_checkpoint_member='data/portable_resume/portable_checkpoint.json',training_started=False,full_archive_audit_complete=False,all_sgk_forms_covered=False,members={n:dict(bytes=len(b),sha256=sha(b)) for n,b in members.items()})
    members['manifest.json']=(dump(manifest)+'\n').encode();temp=RUN/'finish_append.partial.zip'
    with zipfile.ZipFile(temp,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for n,b in members.items():
            info=zipfile.ZipInfo(n,(2026,10,20,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,b)
    with zipfile.ZipFile(temp) as z:assert not z.testzip() and all(z.read(n)==b for n,b in members.items())
    h=sha(temp.read_bytes());target=RUN/f'MathVisionKid_SGK_FINISH_APPEND_20261020_{h[:16]}.zip';temp.replace(target)
    write(RUN/'bundle_local.json',dict(path=str(target),file_name=target.name,bytes=target.stat().st_size,sha256=h,member_count=len(members),cases=report['cases'],chat_rows=report['chat_rows']))
    print(dump(read(RUN/'bundle_local.json')))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['audit','snapshot']);a=ap.parse_args();{'audit':audit,'snapshot':snapshot}[a.action]()
