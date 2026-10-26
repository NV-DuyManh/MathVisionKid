"""Prepare small evidence only; full corpus/checkpoints stay in Colab/Drive."""
from pathlib import Path
from datetime import datetime,timezone
import base64,hashlib,json

HERE=Path(__file__).resolve().parent
RUN=HERE/'cloud_publication/audit_finish_20261022'
def sha(b):return hashlib.sha256(b).hexdigest()
def write(name,value):
    (RUN/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
validation=json.loads((RUN/'batch_adapter_validation_root.json').read_text('utf8'))
assert validation['success'] and validation['tests_run']==21
for name,h in validation['files_sha256'].items():assert sha((HERE/name).read_bytes())==h
review=dict(schema='MathVisionKid.root_performance_review.v1',reviewed_utc=datetime.now(timezone.utc).isoformat(),
    reviewer='Codex root AI review; no human attestation',
    review_type='ROOT_INTEGRATION_AND_DIFFERENTIAL_TEST_REVIEW',
    adapter_sha256=sha((HERE/'math_data_batch_token_audit.py').read_bytes()),
    resume_sha256=sha((RUN/'performance_resume_existing_v3.py').read_bytes()),
    validation_sha256=sha((RUN/'batch_adapter_validation_root.json').read_bytes()),
    tests_passed=21,
    peer_findings_resolved=[
        'Read-ahead stream/CRC/UTF8/IO failures flush previously read rows via unchanged original scalar validation before surfacing error.',
        'Batch-only backend/preparation failures discard speculative cache; original row path remains authoritative.',
        'Cached batch row-gate failure retries exact scalar tokenizer at actual row; root added differential regression.',
        'Pause compares full committed member cursors with raw-verified snapshot as well as report; joined thread required.',
        'Explicit adapter.consume integration uses original auditor method; no recursive method replacement.',
        'Final code/test hashes checked against new successful validation, rather than transient author version.'
    ],
    runtime_revision_resolution='First attempt refused unlabelled in-memory tokenizer. Corrected path loads explicit pinned cached snapshot, compares Rust tokenizer serialization and chat_template with prior tokenizer, then constructs adapter. Refusal preserved in notebook/evidence; no token gate weakened.',
    limitation='Independent reviewers supplied failure findings and reviewed plan; root completed final scalar retry/test/integration. Final exact implementation is root reviewed, not falsely labelled independent peer-approved.',
    original_auditor_changed=False,source_rows_changed=False,
    checkpoint_interval_seconds=1800,checkpoint_finish_and_error_save=True,
    local_pc_corpus_downloaded=False,training_started=False)
write('root_performance_review.json',review)
diagnostic=dict(schema='MathVisionKid.diagnostic_exact_hash_evidence.v1',
    sample_id='exhaustive_v1_div_1563_43',source_label='regression_only',
    source_raw_row_sha256='1729ed713dfedcc0205b130c6573313dcc5784c7eaf5618d0cf32fdc728cf26b',
    source_canonical_sha256='1729ed713dfedcc0205b130c6573313dcc5784c7eaf5618d0cf32fdc728cf26b',
    evidence_file='diagnostic_metadata_observed.json',
    evidence_sha256=sha((RUN/'diagnostic_metadata_observed.json').read_bytes()),
    same_id_source_versions=1,chat_links_so_far=0,
    status='PRESERVED_DIAGNOSTIC_EXCLUSION_PENDING_FINAL_FULL_SCAN_PROOF',
    raw_scanner_finding_preserved=True,train_eligible=False,
    zero_links_is_final_proof=False,training_started=False)
write('diagnostic_exact_hash_evidence.json',diagnostic)
files={}
for p in RUN.iterdir():
    if p.is_file() and p.suffix in ('.json','.py') and not p.name.startswith(('publication_payload','publish_remote')):
        files[p.name]=p.read_bytes()
for name in ['math_data_batch_token_audit.py','test_math_data_batch_token_audit.py','build_batch_performance_resume.py',Path(__file__).name]:
    files[name]=(HERE/name).read_bytes()
payload={'files':{name:base64.b64encode(b).decode() for name,b in files.items()},
    'sha256':{name:sha(b) for name,b in files.items()},
    'expected_controls':{
        'progress':dict(id='1D5RvQ5-V3DtYZfGxmlmvvPlVz9I-SxeX',sha256='aae86d259f840f2461c6bd8230757ec74f839d9a2342f4b2f06835f9795b4e38'),
        'chat':dict(id='1tkSQoAlxXXRUg2AwYfvqsFKVEmM_LmR6',sha256='34aef6fe1c12d3534ea6c46ce38f01e70318f74bc961d5c3297bdd7a5c0bb76b'),
        'context':dict(id='13gdIPQTFKcekoQQtgo0TXc7RgeadzIN9',sha256='222d3efeb1494f99c40d30c6d3ab1d8b2b5063980b59ecf51a7293e9dbc73a82'),
        'state':dict(id='1TLoQIbrRVmgsg-2uiUujCfM3HrK62Yme',sha256='61ea0622980dfa8bac3a7717119b5084af4536f7ba8a4e6c05a7f3fcfd04686a')},
    'training_started':False}
write('publication_payload.json',payload)
print(json.dumps({'evidence_files':len(files),'payload_bytes':(RUN/'publication_payload.json').stat().st_size,'adapter_sha256':review['adapter_sha256'],'training_started':False}))
