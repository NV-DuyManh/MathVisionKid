"""Account-neutral authoring task ledger. Runs after accepted append audit."""
from pathlib import Path
from collections import Counter
import json,hashlib
import math_data_portable_resume as P
from sgk_finish_release import master
HERE=Path(__file__).resolve().parent
RUN=HERE/'cloud_publication/sgk_finish_20261020'
def read(p):return json.loads(p.read_text('utf-8'))
def main():
    root=read(RUN/'portable_resume/portable_checkpoint.json')
    ledger=P.new_checkpoint(root['artifacts'],root.get('data_owner_history',[]))
    ledger['control_pointers']=root.get('control_pointers',{})
    ledger['pinned_input_state_sha256']='063e95ed756b2824a30d9a76b3bc99da16b93beaea94d1864a9e6325e5e80411'
    queue_path=RUN/'crossgrade_mapping/resume_queue.json';queue=read(queue_path);queuehash=P.file_hash(queue_path)
    accepted=[json.loads(b) for b in (RUN/'release/accepted_cases.jsonl').read_bytes().splitlines()]
    groups={}
    for row in accepted:groups.setdefault(master(row),[]).append(row)
    initial_old_covered=asset_limited=new_examples=0
    for m in queue['masters']:
        key=P.add_task(ledger,P.task_spec('FINITE_MASTER_TEXT_AUTHORING_AND_EXACT_CANDIDATE_ADJUDICATION',[dict(sha256=queuehash,member='data/crossgrade_mapping/resume_queue.json')],dict(master_id=m['master_id'],candidate_ids=m['candidate_ids'],scope_limit='Original text examples; all candidate aliases require explicit content mapping; no visual/physical certification'),'semantic_mapping'))
        examples=groups.get(m['master_id'],[])
        if m['category']=='COVERED_EXACT_ID_HASH':
            token=P.claim(ledger,key,'portable_coordinator',now=0,ttl=10);P.acknowledge(ledger,key,token,result=dict(disposition='REUSE_OLD_EXACT_SOURCE_IDS_HASHES',nearest_refs=m['nearest_refs']),now=1);initial_old_covered+=1
        elif m['category']=='ASSET_ONLY_LIMITATION':
            ledger['tasks'][key]['progress']=dict(disposition='ASSET_LIMITATION_DOCUMENTED_NOT_COMPLETED',next_action=m['next_action']);asset_limited+=1
        elif examples:
            ledger['tasks'][key]['progress']=dict(disposition='NEW_EXAMPLES_ACCEPTED_CANDIDATE_ALIAS_RECONCILIATION_REQUIRED',accepted_examples=[dict(sample_id=r['sample_id'],exported_row_sha256=hashlib.sha256(P.canonical(r).encode()).hexdigest()) for r in examples],resolution_member='data/release/candidate_resolution_overlay.json');new_examples+=1
    g2=HERE/'cloud_publication/sgk_page_audit_20261019/g2v2_audit/g2_combined_candidate_adjudication.json';g2h=P.file_hash(g2)
    for m in read(g2)['finite_master_resume_queue']:
        if m['status']=='COVERED':continue
        key=P.add_task(ledger,P.task_spec('FINITE_G2_MASTER_BRANCH_RECONCILIATION',[dict(sha256=g2h,member='prior_sgk_page_bundle:data/g2v2_audit/g2_combined_candidate_adjudication.json')],dict(master_id=m['finite_master_id'],candidate_refs=m['candidate_refs'],scope_limit='No duplicate authoring across related global masters'),'semantic_mapping'))
        if m['finite_master_id'] in groups:ledger['tasks'][key]['progress']=dict(disposition='CONFIRMED_BRANCH_EXAMPLES_ACCEPTED_RECHECK_RELATED_ALIASES',accepted_ids=[r['sample_id'] for r in groups[m['finite_master_id']]])
    ledger['next_wave_assignments']=dict(g5_applied_text=dict(output_scope='sgk_remaining_20261020/g5_applied_text',masters=['frequency_table_weighted_mean','one_swap_parity_extremum','whole_units_from_decimal_quotient','whole_package_area_procurement','piece_pack_unit_role_choice','circular_rim_capacity_feasibility'],status='DRAFTING_NOT_ACCEPTED'),stream_loader=dict(output_scope='sgk_remaining_20261020/stream_loader',status='DATA_ONLY_LOADER_IMPLEMENTATION_NOT_TRAINING'))
    ledger['binding_note']='Output members resolve relative to enclosing verified bundle manifest; connector link IDs and Codex account/session are runtime only. Lease and progress are exported, never inferred from chat history.'
    P.safe_metadata(ledger);P.save(RUN/'release/authoring_portable_checkpoint.json',ledger)
    print(json.dumps(dict(finite_tasks=len(ledger['tasks']),old_covered=initial_old_covered,asset_limited=asset_limited,masters_with_new_examples=new_examples,g2_added_pending=51,completed_tasks=len(ledger['completed']),training_started=False)))
if __name__=='__main__':main()
