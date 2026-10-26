"""Read-only original eight-batch intake checks; no tokenization or training."""
from pathlib import Path
from datetime import datetime,timezone
from collections import Counter,defaultdict
import hashlib,json,zipfile,sys,io

HERE=Path(__file__).resolve().parent
WORK=HERE.parents[2]
sys.path.insert(0,str(WORK/'thinking'))
import math_data_archive_audit as A
import math_data_full_audit_v3 as V3
import exhaustive_colab_loader as L

def sha(b):return hashlib.sha256(b).hexdigest()
def canonical(v):return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def jlines(b):
    return [(n,line,V3.rawhash(line),json.loads(line)) for n,line in enumerate(io.TextIOWrapper(io.BytesIO(b),encoding='utf8'),1) if line.strip()]
def load(b):return json.loads(b.decode('utf8'))

def main():
    index_path=WORK/'handoff/ANTIGRAVITY_G2_FINAL_HANDOFF_MANIFEST.json'
    queue_path=WORK/'thinking/cloud_publication/data_resume_20261022/next_uncovered_tasks.json'
    index=load(index_path.read_bytes());queue=load(queue_path.read_bytes())
    task_map={r['task_id']:r for r in queue['g2_pending_specific_tasks']}
    candidate_map={r['candidate_id']:r for r in queue['external_g2_remaining_separate']}
    report=dict(schema='MathVisionKid.AntigravityOriginalStructuralIntake.v1',
        observed_utc=datetime.now(timezone.utc).isoformat(),
        skills_applied=[],scope='Original eight ZIPs only; no semantic certification, tokenization, Drive/Colab or source mutations.',
        audit_code_sha256=sha(Path(__file__).read_bytes()),
        final_manifest_sha256=sha(index_path.read_bytes()),
        final_manifest_hash_matches_user_report=sha(index_path.read_bytes())=='6848d7a7a73be7f6a91944bc2997e3c01783b88973d0c4284c884fc59e365423',
        actual_queue_sha256=sha(queue_path.read_bytes()),declared_queue_sha256=index['parent_queue']['sha256'],
        queue_parent_hash_matches=sha(queue_path.read_bytes())==index['parent_queue']['sha256'],
        batches=[],findings=[],per_case=[],per_chat=[],task_bindings=[],
        raw_readback_scope='LOCAL_EXISTING_BYTES_ONLY_NOT_CLOUD_SERVER_READBACK',
        cloud_server_IDs_verified=False,training_started=False)
    original_hashes={};all_cases={};case_counts=Counter();chat_counts=Counter();all_chats={};closed_tasks={};member_maxima=[]
    for release in index['releases']:
        path=WORK/'handoff'/release['release_zip']
        if not path.exists():path=Path(r'G:\.shortcut-targets-by-id\19ZxkfKVIggdcbSfsAdCtG1ibfJ0CRN3n\primary_math_teacher_20261016')/release['release_zip']
        raw=path.read_bytes();original_hashes[str(path)]=sha(raw)
        batch=dict(batch=release['batch_number'],path=str(path),bytes=len(raw),sha256=sha(raw),
            expected_sha256=release['zip_sha256'],zip_sha256_matches=sha(raw)==release['zip_sha256'],
            zip_bytes_match=len(raw)==release['zip_bytes'],declared_drive_item_id=release['drive_item_id'],
            declared_drive_id_is_placeholder=release['drive_item_id'].startswith('drive_item_'))
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            names=z.namelist();batch['duplicate_member_names']=len(names)!=len(set(names))
            manifest=load(z.read('manifest.json'));entries=manifest['entries'];member_checks=[]
            for member,ref in entries.items():
                blob=z.read(member)
                member_checks.append(dict(member=member,sha256=sha(blob),bytes=len(blob),hash_match=sha(blob)==ref['sha256'],bytes_match=len(blob)==ref['bytes']))
            batch['manifest_member_checks']=member_checks
            sources=jlines(z.read('accepted_cases.jsonl'));chats=jlines(z.read('accepted_chat.jsonl'))
            batch['source_newline_counts']={k:z.read('accepted_cases.jsonl').count(v) for k,v in {'lf':b'\n','crlf':b'\r\n','crcrlf':b'\r\r\n'}.items()}
            batch['cases']=len(sources);batch['chats']=len(chats)
            qa={r['sample_id']:r for _,_,_,r in jlines(z.read('qa7.jsonl'))}
            bindings={r['sample_id']:r for r in load(z.read('source_draft_export_hashes.json'))}
            token=load(z.read('token_audit.json'));batch['declared_token_audit']=dict(total=token.get('total_chats_audited'),maximum=token.get('max_token_length_observed'),revision=token.get('snapshot_revision'),records=len(token.get('records',[])))
            member_maxima.append(token.get('max_token_length_observed',0))
            source_by_id={r['sample_id']:(h,r) for _,_,h,r in sources}
            for line_number,line,h,row in sources:
                sid=row['sample_id'];case_counts[sid]+=1;all_cases[sid]=(h,row)
                review=qa.get(sid,{});binding=bindings.get(sid,{})
                criteria=review.get('criteria',{})
                flags={k:row.get(k) for k in ['human_verified','teacher_certified','owner_human_reviewed']}
                record=dict(batch=release['batch_number'],line=line_number,sample_id=sid,raw_sha256=h,
                    source_role=row.get('source_role'),split=row.get('split'),human_flags=flags,
                    human_review_claim=row.get('provenance',{}).get('human_content_review_completed'),
                    qa7_criteria_count=len(criteria),qa7_criteria_all_pass=bool(criteria) and all(v=='PASS' for v in criteria.values()),
                    qa_export_hash_matches=review.get('exported_row_sha256')==h,
                    qa_source_hash_is_reviewed_draft=(review.get('source_row_sha256')==review.get('reviewed_draft_row_sha256')),
                    reviewed_draft_content_in_zip=False,
                    source_hash_binding_matches=binding.get('exported_row_sha256')==h,
                    reviewed_draft_binding_matches=binding.get('reviewed_draft_row_sha256')==row.get('provenance',{}).get('reviewed_draft_row_sha256'),
                    coverage_task=row.get('coverage',{}).get('planning_task_id'),coverage_candidates=row.get('coverage',{}).get('candidate_ids',[]))
                record['claim_flags_truthful']=all(v is False for v in flags.values()) and record['human_review_claim'] is False and record['source_role']=='AI_GENERATED'
                report['per_case'].append(record)
            for line_number,line,h,row in chats:
                sid=row['sample_id'];chat_counts[sid]+=1;all_chats[sid]=row
                source=source_by_id.get(L.case_id(row));validation_error=None
                try:L.validate_chat(row)
                except Exception as error:validation_error=type(error).__name__+': '+str(error)
                try:errors=A.linkage_errors(row,A.source_projection(source[1])) if source else ['source_missing']
                except Exception as error:errors=[type(error).__name__+': '+str(error)]
                prompt=json.loads(row['messages'][1]['content'])
                report['per_chat'].append(dict(batch=release['batch_number'],line=line_number,sample_id=sid,
                    raw_sha256=h,source_raw_sha256=source[0] if source else None,
                    source_row_sha256_matches=bool(source and row.get('source_row_sha256')==source[0]),
                    schema_validation_error=validation_error,linkage_errors=errors,
                    explicit_human_flags={key:row.get(key) for key in ['human_verified','teacher_certified','owner_human_reviewed'] if key in row},
                    human_review_claim=row.get('provenance',{}).get('human_content_review_completed'),
                    prompt_keys=sorted(prompt),student_work_in_source=bool(source and source[1].get('student_work')),
                    student_work_in_prompt=bool(prompt.get('student_work'))))
            delta=load(z.read('coverage_delta.json'))
            for task in delta['closed_tasks']:
                task_id=task['task_id'];closed_tasks[task_id]=task
                expected=task_map.get(task_id);evidence_ids=task.get('evidence_sample_ids',[]);evidence_hashes=task.get('evidence_exported_hashes',[])
                mapped=[dict(sample_id=sid,hash_matches=(sid in source_by_id and source_by_id[sid][0]==h)) for sid,h in zip(evidence_ids,evidence_hashes)]
                expected_candidates=expected.get('candidate_ids',[]) if expected else []
                report['task_bindings'].append(dict(task_id=task_id,exists_in_actual_queue=expected is not None,
                    declared_candidates=task.get('candidate_ids',[]),actual_queue_candidates=expected_candidates,
                    candidate_sets_match=set(task.get('candidate_ids',[]))==set(expected_candidates),
                    all_candidates_in_remaining_queue=all(c in candidate_map for c in task.get('candidate_ids',[])),
                    evidence_lengths_match=len(evidence_ids)==len(evidence_hashes),evidence_bindings=mapped,
                    branch_scope_remains_subject_to_semantic_review=True))
        report['batches'].append(batch)
    report['counts']=dict(case_occurrences=sum(case_counts.values()),unique_case_ids=len(case_counts),
        duplicate_case_ids=[k for k,v in case_counts.items() if v!=1],chat_occurrences=sum(chat_counts.values()),unique_chat_ids=len(chat_counts),
        duplicate_chat_ids=[k for k,v in chat_counts.items() if v!=1],
        declared_closed_task_ids=len(closed_tasks),actual_queue_tasks=len(task_map),
        covered_task_IDs=set(closed_tasks)==set(task_map),
        candidate_IDs_declared=len(set(c for t in closed_tasks.values() for c in t['candidate_ids'])),
        missing_candidate_IDs=sorted(set(candidate_map)-set(c for t in closed_tasks.values() for c in t['candidate_ids'])),
        expected_remaining_candidates=len(candidate_map),
        exact_candidate_ID_set_matches=set(c for t in closed_tasks.values() for c in t['candidate_ids'])==set(candidate_map),
        chat_source_hash_mismatches=sum(not c['source_row_sha256_matches'] for c in report['per_chat']),
        chats_with_linkage_errors=sum(bool(c['linkage_errors']) for c in report['per_chat']),
        chat_schema_errors=sum(c['schema_validation_error'] is not None for c in report['per_chat']),
        case_human_flag_or_source_role_issues=sum(not r['claim_flags_truthful'] for r in report['per_case']))
    report['missing_candidate_constraint_evidence']=[dict(candidate_id=cid,
        original_candidate= candidate_map[cid],
        task_id=next((task['task_id'] for task in task_map.values() if cid in task.get('candidate_ids',[])),None),
        note='Task ID exists but this exact candidate binding is not in original delta. Root semantic adjudication of actual constraints is required before adding a derived binding; no automatic alias closure.')
        for cid in report['counts']['missing_candidate_IDs']]
    report['counts']['unique_case_group_ids']=len({row['case_group_id'] for _,row in all_cases.values()})
    report['counts']['chat_human_claim_issues']=sum(any(value is True for value in row['explicit_human_flags'].values()) or row['human_review_claim'] is True for row in report['per_chat'])
    report['four_modes_per_case']={sid:sorted(r['mode'] for r in all_chats.values() if L.case_id(r)==sid) for sid in all_cases}
    report['four_mode_sets_valid']=all(set(m)==set(L.MODES) and len(m)==4 for m in report['four_modes_per_case'].values())
    report['token_count_claims']=dict(user_report_maximum=782,final_handoff_maximum=index['summary_metrics']['max_tokens_across_corpus'],
        member_declared_maximum=max(member_maxima),claim_conflict=782!=max(member_maxima),actual_tokenizer_rerun_by_this_audit=False)
    report['findings']=[
        dict(kind='CLOUD_PROOF_NOT_ESTABLISHED',detail='drive_item_* identifiers are placeholders; original verification calls DriveFS queued sync a raw readback. No cloud-server ID/readback established by these originals.'),
        dict(kind='PARENT_QUEUE_HASH_MISMATCH',actual=report['actual_queue_sha256'],declared=report['declared_queue_sha256'],detail='Exact ID and candidate-set comparisons below preserve usable mapping, but do not establish semantic closure.'),
        dict(kind='TOKEN_MAXIMUM_REPORT_CONFLICT',detail='Narrative maximum782 conflicts with final manifest/member audit maximum909; root actual pinned tokenizer audit required.'),
        dict(kind='DRAFT_HASH_CONTENT_NOT_PRESENT',detail='QA source_row_sha256 binds reviewed draft, not accepted exported raw row. Export hash binding can be checked, but original draft content is absent from ZIP; do not claim re-read draft from QA declarations.'),
    ]
    if report['counts']['chats_with_linkage_errors']:
        report['findings'].append(dict(kind='SOURCE_CHAT_LINKAGE_ERRORS',count=report['counts']['chats_with_linkage_errors'],
            kinds=dict(Counter(e for c in report['per_chat'] for e in c['linkage_errors'])),
            required_repair='Regenerate all four modes from full repaired source fields including actual student_work; keep old chats audit-only.'))
    report['original_hashes_unchanged_at_end']={path:sha(Path(path).read_bytes())==h for path,h in original_hashes.items()}
    report['status']='ORIGINALS_PRESERVED_REPAIRS_AND_CLOUD_PUBLICATION_REQUIRED'
    report['TRAINING_DATASET_READY']=False
    output=HERE/'structural_intake.json';output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps(dict(path=str(output),sha256=sha(output.read_bytes()),counts=report['counts'],four_mode_sets_valid=report['four_mode_sets_valid'],all_zip_hashes_match=all(b['zip_sha256_matches'] for b in report['batches']),all_member_hashes_match=all(m['hash_match'] for b in report['batches'] for m in b['manifest_member_checks'])),ensure_ascii=False))

if __name__=='__main__':main()
