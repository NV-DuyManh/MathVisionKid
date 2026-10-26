"""Derived v3 current-candidate CPU audit. No training, weights, network or deletions.

Use only in a cloud/runtime directory for the corpus. Account and mounted paths
are outside content identity. Every declared source member is indexed before
chats; all explicit splits are checked together. Original bytes never change.
"""
from pathlib import Path
from collections import Counter
import json,sqlite3,hashlib
import math_data_archive_audit as A
import exhaustive_colab_loader as L
from math_data_candidate_stream import member_key,content_identity,SPLITS,_check_entry
from math_data_portable_resume import canonical,digest
import math_data_primary782_bindings_v3 as PRIMARY

PRIMARY_BINDINGS_CODE_SHA256='4d75e90c07eecccf7571d68015dda16e85a690e7ee2379b28d517d201472580b'
PRIMARY_MEMBER_SHA256='99aefab7a58177e3b3222f7bf269c02e991fafeaf2fed79e83b5b5b39ebc5a02'
PRIMARY_ADAPTER_KIND='EXACT_PRIMARY782_NEUTRAL_EXPORT_V3'

def verify_primary_bindings():
    if hashlib.sha256(Path(PRIMARY.__file__).read_bytes()).hexdigest()!=PRIMARY_BINDINGS_CODE_SHA256:
        raise ValueError('Primary782 adapter code hash differs')
    if digest(PRIMARY.BINDINGS)!=PRIMARY.PROVENANCE['binding_table_sha256']:
        raise ValueError('Primary782 binding table hash differs')

def primary_binding(row,source_raw_sha):
    binding=PRIMARY.BINDINGS.get(source_raw_sha)
    if not binding or binding['sample_id']!=row.get('sample_id') or binding['exported_canonical_sha256']!=digest(row):
        raise ValueError('Primary782 exact exported row raw/canonical hash not in pinned binding table')
    if digest(row.get('verification'))!=binding['source_verification_digest']:
        raise ValueError('Primary782 original/derived source verification differs')
    return binding

def primary_projection(row,source_raw_sha):
    binding=primary_binding(row,source_raw_sha)
    # A read-time projection only. The original row is not mutated or relabeled.
    projected=dict(row,can_solve=binding['can_solve'],case_group_id=binding['chat_group_id'])
    result=A.source_projection(projected)
    if digest(result)!=binding['projection_sha256']:
        raise ValueError('Primary782 projected fingerprint differs')
    return result,binding

DERIVATION_PROVENANCE = {
    'parent_file': 'math_data_full_audit_v2.py',
    'parent_sha256': '81b1e3f04c5886f78282386ecb34d47ba4ba9da63edfec8856bab82034a093ee',
    'source_label_evidence_file': 'exhaustive_primary_math.py',
    'source_label_evidence_sha256': 'd0af1e4adf73a55b8416757ee43de900474f378af7ff8290fffdd0b015acb8b2',
    'source_label_evidence': 'make_row returns train_candidate; chat_records explicitly returns train.',
    'raw_source_rewritten': False,
    'candidate_pool_promoted_to_train': False,
    'v1_checkpoint_and_issues_preserved': True,
    'v2_checkpoint_and_issues_preserved': True,
    'primary782_binding_code_sha256':PRIMARY_BINDINGS_CODE_SHA256,
    'original_source_and_exported_row_hashes_distinct':True,
}
SOURCE_LABELS = frozenset(SPLITS) | {'train_candidate'}

def source_chat_split_compatible(source_label, chat_split):
    # This is a builder-backed compatibility check, not a source split rewrite.
    # Unknown/missing source labels stay unverified; chats still require SPLITS.
    return (source_label == 'train_candidate' and chat_split == 'train') or (
        source_label in SPLITS and source_label == chat_split)

def rawhash(line):return hashlib.sha256(line.removesuffix('\n').removesuffix('\r').encode('utf8')).hexdigest()
def plan_identity(recipe):
    return digest(dict(schema='full_current_archive_audit.v3',source_members=[content_identity(x) for x in recipe['source_members']],chat_members=[content_identity(x) for x in recipe['chat_members']],tokenizer_revision=L.REVISION,source_label_policy='builder_pinned_candidate_pool_to_train_chat_only.v1',primary782_adapter_code_sha256=PRIMARY_BINDINGS_CODE_SHA256))
class FullArchiveAudit:
    def __init__(self,database,recipe,tokenizer,sequence_limit=40960):
        if recipe.get('pending_discovery'):raise ValueError('Unresolved member discovery')
        if tokenizer is None:raise ValueError('Actual tokenizer required, no full token audit without it')
        verify_primary_bindings()
        self.recipe=recipe;self.tokenizer=tokenizer;self.limit=sequence_limit
        self.entries=recipe['source_members']+recipe['chat_members']
        for e in self.entries:_check_entry(e)
        self.keys=[member_key(e) for e in self.entries]
        self.primary_source_keys={member_key(e) for e in recipe['source_members'] if e.get('member_sha256',e['sha256'])==PRIMARY_MEMBER_SHA256}
        if len(set(self.keys))!=len(self.keys):raise ValueError('Duplicate exact member key')
        self.identity=plan_identity(recipe);self.db=sqlite3.connect(database)
        # Refuse an old identity before any schema write, preserving its issue log.
        if self.db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='config'").fetchone():
            prior=self.db.execute('SELECT identity,sequence_limit FROM config').fetchone()
            if prior and prior!=(self.identity,self.limit):
                self.db.close();raise ValueError('Different immutable audit identity; preserve prior checkpoint')
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS config(identity TEXT PRIMARY KEY, sequence_limit INTEGER);
        CREATE TABLE IF NOT EXISTS members(id TEXT PRIMARY KEY, role TEXT, next_line INTEGER, complete INTEGER, expected_rows INTEGER);
        CREATE TABLE IF NOT EXISTS source_versions(id TEXT,raw_sha TEXT,canonical_sha TEXT,projection TEXT,signatures TEXT,source_split TEXT,original_source_sha TEXT,adapter_kind TEXT,verification_digest TEXT,PRIMARY KEY(id,raw_sha));
        CREATE TABLE IF NOT EXISTS samples(id TEXT PRIMARY KEY,canonical_sha TEXT,case_id TEXT,mode TEXT,split TEXT,source_raw_sha TEXT,linkage INTEGER,raw_hash_origin TEXT,sequence_tokens INTEGER,completion_tokens INTEGER, UNIQUE(case_id,mode));
        CREATE TABLE IF NOT EXISTS occurrences(member TEXT,line INTEGER,sample_id TEXT,raw_sha TEXT,kind TEXT,PRIMARY KEY(member,line));
        CREATE TABLE IF NOT EXISTS split_keys(kind TEXT,key TEXT,split TEXT,PRIMARY KEY(kind,key));
        CREATE TABLE IF NOT EXISTS issues(member TEXT,line INTEGER,kind TEXT,detail TEXT,PRIMARY KEY(member,line,kind,detail));
        """)
        prior=self.db.execute('SELECT identity,sequence_limit FROM config').fetchone()
        if prior and prior!=(self.identity,self.limit):self.db.close();raise ValueError('Different immutable audit identity; preserve prior checkpoint')
        self.db.execute('INSERT OR IGNORE INTO config VALUES (?,?)',(self.identity,self.limit));self.db.commit()
    def issue(self,key,line,kind,detail):
        self.db.execute('INSERT OR IGNORE INTO issues VALUES (?,?,?,?)',(key,line,kind,str(detail)))
    def _source(self,row,key,line,text):
        if row.get('split') not in SOURCE_LABELS:self.issue(key,line,'SOURCE_SPLIT_MISSING_OR_UNKNOWN',row.get('sample_id'))
        h=rawhash(text);original_sha=kind=verification_digest=None
        try:
            if key in self.primary_source_keys:
                projection,binding=primary_projection(row,h)
                original_sha=binding['original_or_derived_source_sha256'];kind=PRIMARY_ADAPTER_KIND
                verification_digest=binding['source_verification_digest']
            else:
                projection=A.source_projection(row)
        except (KeyError,TypeError,ValueError) as error:
            self.issue(key,line,'SOURCE_SCHEMA_UNSUPPORTED_OR_HASH_MISMATCH',str(row.get('sample_id'))+':'+str(error))
            return
        self.db.execute('INSERT OR IGNORE INTO source_versions VALUES (?,?,?,?,?,?,?,?,?)',(row['sample_id'],h,digest(row),canonical(projection),canonical(L.source_signatures(row)),row.get('split'),original_sha,kind,verification_digest))
    def _chat(self,row,key,line,text):
        if row.get('split') not in SPLITS:raise ValueError('Explicit known chat split required; no default train')
        L.validate_chat(row);sid=L.case_id(row);h=digest(row)
        prior=self.db.execute('SELECT canonical_sha FROM samples WHERE id=?',(row['sample_id'],)).fetchone()
        if prior:
            kind='EXACT_DUPLICATE_REFERENCE' if prior[0]==h else 'CONFLICTING_SAMPLE_ID'
            self.db.execute('INSERT INTO occurrences VALUES (?,?,?,?,?)',(key,line,row['sample_id'],rawhash(text),kind))
            if kind!='EXACT_DUPLICATE_REFERENCE':self.issue(key,line,kind,row['sample_id'])
            return
        candidates=self.db.execute('SELECT raw_sha,projection,signatures,source_split,original_source_sha,adapter_kind,canonical_sha,verification_digest FROM source_versions WHERE id=?',(sid,)).fetchall()
        original=row.get('source_row_sha256')
        def bound_hashes(source):
            if source[5]==PRIMARY_ADAPTER_KIND:
                # Primary chat's source_row_sha256 binds pre-overlay AI/derived
                # source. row_sha256 independently binds the exported canonical
                # row. Neither is the raw JSONL export hash kept in source[0].
                return (original==source[4] and row.get('row_sha256')==source[6]
                        and digest(row.get('verification'))==source[7])
            return not original or source[0]==original
        before_hash=candidates
        candidates=[s for s in candidates if bound_hashes(s)]
        if before_hash and not candidates:
            self.issue(key,line,'SOURCE_HASH_CHAIN_MISMATCH' if any(s[5]==PRIMARY_ADAPTER_KIND for s in before_hash) else 'SOURCE_RAW_HASH_NOT_FOUND',sid)
        elif original and not candidates:self.issue(key,line,'SOURCE_RAW_HASH_NOT_FOUND',sid)
        target_matches=[s for s in candidates if not A.linkage_errors(row,json.loads(s[1]))]
        matches=[s for s in target_matches if source_chat_split_compatible(s[3],row['split'])]
        if target_matches and not matches:
            self.issue(key,line,'SOURCE_CHAT_SPLIT_MISMATCH',canonical(dict(case_id=sid,source_labels=sorted({str(s[3]) for s in target_matches}),chat_split=row['split'])))
        if len(matches)==1:
            source=matches[0];origin=('PRIMARY_ORIGINAL_AND_EXPORTED_HASH_VERIFIED' if source[5]==PRIMARY_ADAPTER_KIND else 'ORIGINAL_RAW_HASH_VERIFIED' if original else 'READ_TIME_DERIVED_BY_FULL_PROMPT_TARGET_LINKAGE')
        elif len(matches)>1:
            self.issue(key,line,'AMBIGUOUS_SOURCE_RAW_HASH',sid);source=None;origin='UNVERIFIED'
        else:
            self.issue(key,line,'SOURCE_CHAT_LINKAGE_UNVERIFIED',sid);source=None;origin='UNVERIFIED'
        encoded=L.tokenize_assistant_only(row,self.tokenizer,self.limit)
        raw_sha=source[0] if source else None;signatures=json.loads(source[2]) if source else row.get('canonical_signatures',[])
        try:
            self.db.execute('INSERT INTO samples VALUES (?,?,?,?,?,?,?,?,?,?)',(row['sample_id'],h,sid,row['mode'],row['split'],raw_sha,int(source is not None),origin,len(encoded['input_ids']),encoded['completion_tokens']))
        except sqlite3.IntegrityError:
            self.issue(key,line,'CONFLICTING_CASE_MODE',sid+':'+row['mode']);return
        self.db.execute('INSERT INTO occurrences VALUES (?,?,?,?,?)',(key,line,row['sample_id'],rawhash(text),'CURRENT_CANDIDATE'))
        keys=[('group',row['case_group_id']),('question',L.question_key(row))]
        keys.extend(('canonical',s) for s in signatures)
        for kind,value in keys:
            p=self.db.execute('SELECT split FROM split_keys WHERE kind=? AND key=?',(kind,value)).fetchone()
            if p and p[0]!=row['split']:self.issue(key,line,'CROSS_SPLIT_'+kind.upper(),value)
            self.db.execute('INSERT OR IGNORE INTO split_keys VALUES (?,?,?)',(kind,value,row['split']))
    def consume(self,entry,path,max_rows=20000,commit_every=256):
        if max_rows is not None and max_rows<=0 or commit_every<=0:raise ValueError('Positive work bounds required')
        key=member_key(entry)
        if key not in self.keys:raise ValueError('Member not declared by exact recipe')
        if entry['role']=='candidate_chat':
            missing=[member_key(e) for e in self.recipe['source_members'] if not self.db.execute('SELECT complete FROM members WHERE id=?',(member_key(e),)).fetchone() or not self.db.execute('SELECT complete FROM members WHERE id=?',(member_key(e),)).fetchone()[0]]
            if missing:raise ValueError('Index every declared source member before any chats')
        cursor=self.db.execute('SELECT next_line,complete FROM members WHERE id=?',(key,)).fetchone()
        if cursor and cursor[1]:return dict(already_complete=True,rows=cursor[0],member_key=key)
        start=cursor[0] if cursor else 0;processed=0;count=0
        self.db.execute('INSERT OR IGNORE INTO members VALUES (?,?,0,0,?)',(key,entry['role'],entry['rows']));self.db.commit()
        try:
            with A.payload(entry,path) as stream:
                for count,text in enumerate(stream,1):
                    if count<=start:continue
                    if not text.strip():raise ValueError('Blank JSONL row')
                    row=json.loads(text)
                    if not isinstance(row,dict):raise ValueError('JSONL object required')
                    if entry['role']=='candidate_source':self._source(row,key,count,text)
                    else:self._chat(row,key,count,text)
                    self.db.execute('UPDATE members SET next_line=? WHERE id=?',(count,key));processed+=1
                    if processed%commit_every==0:self.db.commit()
                    if max_rows is not None and processed>=max_rows:
                        self.db.commit();return dict(member_key=key,rows=count,processed=processed,bounded_pause=True)
            if count!=entry['rows'] or start>count:raise ValueError('Exact declared member row count differs')
            self.db.execute('UPDATE members SET next_line=?,complete=1 WHERE id=?',(count,key));self.db.commit()
            return dict(member_key=key,rows=count,processed=processed,complete=True)
        except Exception:
            self.db.rollback();raise
    def next_entry(self):
        for e in self.entries:
            done=self.db.execute('SELECT complete FROM members WHERE id=?',(member_key(e),)).fetchone()
            if not done or not done[0]:return e
        return None
    @staticmethod
    def extend_recipe(database,previous_recipe,next_recipe):
        """Explicit append-only migration; retain all prior source/chat evidence."""
        if next_recipe.get('pending_discovery'):raise ValueError('Unresolved new member discovery')
        for field in ('source_members','chat_members'):
            old=[content_identity(e) for e in previous_recipe[field]]
            new=[content_identity(e) for e in next_recipe[field]]
            if len(new)<len(old) or new[:len(old)]!=old:raise ValueError('Old source/chat prefixes must remain immutable')
        before,after=plan_identity(previous_recipe),plan_identity(next_recipe)
        db=sqlite3.connect(database)
        try:
            with db:
                prior=db.execute('SELECT identity FROM config').fetchone()
                if not prior or prior[0]!=before:raise ValueError('Wrong prior audit identity')
                db.execute('CREATE TABLE IF NOT EXISTS recipe_history(previous_identity TEXT,next_identity TEXT,PRIMARY KEY(previous_identity,next_identity))')
                db.execute('INSERT OR IGNORE INTO recipe_history VALUES (?,?)',(before,after))
                db.execute('UPDATE config SET identity=?',(after,))
        finally:db.close()
        return dict(previous_identity=before,next_identity=after,prior_evidence_preserved=True,training_started=False)
    def report(self):
        n,maxseq,maxcomp,unlinked=self.db.execute('SELECT count(*),max(sequence_tokens),max(completion_tokens),coalesce(sum(linkage=0),0) FROM samples').fetchone()
        completed=self.db.execute('SELECT count(*) FROM members WHERE complete=1').fetchone()[0]
        issues=dict(self.db.execute('SELECT kind,count(*) FROM issues GROUP BY kind'))
        missing_modes=self.db.execute('SELECT count(*) FROM (SELECT case_id FROM samples GROUP BY case_id HAVING count(*)!=4)').fetchone()[0]
        sources=self.db.execute('SELECT count(*) FROM source_versions').fetchone()[0]
        all_done=completed==len(self.entries)
        # Canonical overlaps need an exact-hash policy adjudication, never a
        # blanket bypass. This scanner does not invent owner exceptions.
        clean=not issues and not unlinked and not missing_modes
        return dict(schema='MathVisionKid.full_current_archive_audit.v3',identity=self.identity,derivation_provenance=DERIVATION_PROVENANCE,source_versions_indexed=sources,source_labels_indexed=dict(self.db.execute('SELECT coalesce(source_split,\'<missing>\'),count(*) FROM source_versions GROUP BY source_split')),candidate_source_train_chat_links=self.db.execute("SELECT count(*) FROM samples s JOIN source_versions v ON s.case_id=v.id AND s.source_raw_sha=v.raw_sha WHERE s.linkage=1 AND v.source_split='train_candidate' AND s.split='train'").fetchone()[0],unique_chat_rows_processed=n,actual_rows_by_split=dict(self.db.execute('SELECT split,count(*) FROM samples GROUP BY split')),source_hash_origins=dict(self.db.execute('SELECT raw_hash_origin,count(*) FROM samples GROUP BY raw_hash_origin')),physical_chat_occurrences_processed=self.db.execute('SELECT count(*) FROM occurrences').fetchone()[0],exact_duplicate_references=self.db.execute("SELECT count(*) FROM occurrences WHERE kind='EXACT_DUPLICATE_REFERENCE'").fetchone()[0],members_complete=completed,members_expected=len(self.entries),all_declared_members_scanned=all_done,max_sequence_tokens=maxseq,max_completion_tokens=maxcomp,source_linkage_unverified_rows=unlinked,incomplete_four_mode_cases=missing_modes,issues=issues,full_archive_token_linkage_split_audit_complete=bool(all_done and clean),all_rows_semantically_human_reviewed=False,whole_curriculum_certified=False,TRAINING_DATASET_READY=False,training_started=False,gpu_used=False,model_weights_loaded=False)
    def close(self):self.db.close()

def migrate_v2_snapshot(parent_database,destination_database,recipe,expected_parent_sha256,
                        sequence_limit=40960,expected_source_versions=None,
                        expected_members_complete=None,expected_primary_rows=None):
    """Create an explicit separate v3 backup; never reset/relabel the v2 DB.

    Restricted to source-indexing checkpoints with zero chat/occurrence rows.
    Original cursors, issues, canonical source hashes and signatures survive.
    Only exact table-bound primary782 projection/group and alias metadata change.
    No source raw data or owner attestation is created or rewritten.
    """
    from math_data_full_audit_v2 import plan_identity as v2_identity
    verify_primary_bindings()
    def file_sha(path):
        h=hashlib.sha256()
        with Path(path).open('rb') as f:
            for block in iter(lambda:f.read(1048576),b''):h.update(block)
        return h.hexdigest()
    parent=Path(parent_database).resolve();dest=Path(destination_database).resolve()
    if parent==dest or dest.exists():raise ValueError('Migration needs a new separate destination; preserve old DB')
    if len(expected_parent_sha256)!=64 or file_sha(parent)!=expected_parent_sha256:
        raise ValueError('Explicit parent checkpoint SHA256 differs')
    for suffix in ('-wal','-journal'):
        side=Path(str(parent)+suffix)
        if side.exists() and side.stat().st_size:raise ValueError('Standalone committed checkpoint required before migration')
    old=sqlite3.connect(parent.as_uri()+'?mode=ro',uri=True);new=None
    try:
        if old.execute('SELECT identity,sequence_limit FROM config').fetchone()!=(v2_identity(recipe),sequence_limit):
            raise ValueError('Wrong exact v2 recipe/checkpoint identity')
        if old.execute('SELECT count(*) FROM samples').fetchone()[0] or old.execute('SELECT count(*) FROM occurrences').fetchone()[0]:
            raise ValueError('Migration restricted to source-only zero-chat checkpoints')
        count=old.execute('SELECT count(*) FROM source_versions').fetchone()[0]
        completed=old.execute('SELECT count(*) FROM members WHERE complete=1').fetchone()[0]
        if expected_source_versions is not None and count!=expected_source_versions:raise ValueError('Source checkpoint count differs')
        if expected_members_complete is not None and completed!=expected_members_complete:raise ValueError('Complete member count differs')
        cursors=old.execute('SELECT * FROM members ORDER BY id').fetchall()
        issues=old.execute('SELECT * FROM issues ORDER BY member,line,kind,detail').fetchall()
        new=sqlite3.connect(dest);old.backup(new)
        if new.execute('PRAGMA integrity_check').fetchone()!=('ok',):raise ValueError('Backup integrity failed')
        changed=[]
        with new:
            for name in ('original_source_sha','adapter_kind','verification_digest'):
                new.execute('ALTER TABLE source_versions ADD COLUMN '+name+' TEXT')
            source_cursor=new.execute('SELECT id,raw_sha,canonical_sha,projection FROM source_versions')
            for sid,raw_sha,canonical_sha,projection in source_cursor:
                binding=PRIMARY.BINDINGS.get(raw_sha)
                if not binding:continue
                if (sid,canonical_sha)!=(binding['sample_id'],binding['exported_canonical_sha256']):
                    raise ValueError('Already-indexed primary exact hash binding differs')
                obj=json.loads(projection);obj['case_group_id']=binding['chat_group_id']
                if digest(obj)!=binding['projection_sha256']:
                    raise ValueError('Primary source projection cannot be reconstructed exactly from committed v2 fingerprint')
                new.execute('UPDATE source_versions SET projection=?,original_source_sha=?,adapter_kind=?,verification_digest=? WHERE id=? AND raw_sha=?',
                    (canonical(obj),binding['original_or_derived_source_sha256'],PRIMARY_ADAPTER_KIND,binding['source_verification_digest'],sid,raw_sha))
                changed.append((sid,raw_sha))
            if expected_primary_rows is not None and len(changed)!=expected_primary_rows:
                raise ValueError('Already-indexed primary row count differs')
            # Exact comparison proves all identity/hash/signature/label data kept.
            fields='id,raw_sha,canonical_sha,signatures,source_split'
            if old.execute('SELECT '+fields+' FROM source_versions ORDER BY id,raw_sha').fetchall()!=new.execute('SELECT '+fields+' FROM source_versions ORDER BY id,raw_sha').fetchall():
                raise ValueError('Source identity/signatures/labels changed during migration')
            if cursors!=new.execute('SELECT * FROM members ORDER BY id').fetchall():raise ValueError('Resume cursor changed')
            if issues!=new.execute('SELECT * FROM issues ORDER BY member,line,kind,detail').fetchall():raise ValueError('Prior issues changed')
            after=plan_identity(recipe)
            receipt=dict(parent_sha256=expected_parent_sha256,parent_identity=v2_identity(recipe),next_identity=after,
                source_versions_preserved=count,members_complete_preserved=completed,primary_projections_adapted=len(changed),
                primary_raw_row_bindings_sha256=digest(sorted(changed)),issues_preserved=len(issues),chat_rows=0,
                prior_unknown_regression_issue='PRESERVED_PENDING_NOT_TRAIN_ELIGIBLE',raw_source_mutated=False,
                source_canonical_hashes_signatures_labels_preserved=True,training_started=False)
            new.execute('CREATE TABLE v3_derivation_history(parent_sha256 TEXT PRIMARY KEY,receipt TEXT)')
            new.execute('INSERT INTO v3_derivation_history VALUES (?,?)',(expected_parent_sha256,canonical(receipt)))
            new.execute('UPDATE config SET identity=?',(after,))
        if file_sha(parent)!=expected_parent_sha256:raise ValueError('Parent checkpoint changed during backup')
        return receipt
    finally:
        old.close()
        if new is not None:new.close()

