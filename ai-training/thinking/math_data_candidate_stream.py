"""Unified bounded DATA-ONLY candidate reader; never invokes model training.

An explicit recipe unions declared candidate chat members, never every JSONL in
an archive. Runtime paths/connectors/accounts are outside recipe identity.
Source, history, sealed/pilot and selected diagnostic duplicates stay separate.
"""
from __future__ import annotations
from copy import deepcopy
from dataclasses import asdict,dataclass
import json
from pathlib import Path
import re
import sqlite3

import exhaustive_colab_loader as L
import math_data_archive_audit as A
from math_data_portable_resume import canonical,digest,save

SPLITS=('train','validation','test')
ROLES=('candidate_chat','candidate_source')


def content_identity(entry):
    return {k:entry.get(k) for k in ('sha256','bytes','member','member_sha256','member_bytes','role','rows')}


def member_key(entry):return digest(content_identity(entry))


def _check_entry(entry):
    for field in ('sha256',):
        if not re.fullmatch('[a-f0-9]{64}',entry.get(field,'')):raise ValueError('payload SHA256 required')
    if not isinstance(entry.get('bytes'),int) or entry['bytes']<0:raise ValueError('payload bytes required')
    if entry.get('member') and not re.fullmatch('[a-f0-9]{64}',entry.get('member_sha256') or ''):
        raise ValueError('inner member hash discovery required')
    if not isinstance(entry.get('rows'),int) or entry['rows']<0:raise ValueError('explicit row count required')
    name=(entry.get('member') or entry.get('file_name') or '').casefold()
    if any(x in name for x in ('sealed','pilot','concept_challenge')):raise ValueError('protected payload cannot enter candidate recipe')
    if entry.get('role') not in ROLES:raise ValueError('noncandidate role')


def discover_supplements(document):
    """Find every explicit chat_member descriptor, including unknown run labels.

    The caller supplies metadata obtained through authorized connectors. This
    performs no network access and never infers chat roles from filenames.
    """
    found=[]
    def walk(value):
        if isinstance(value,dict):
            if 'chat_member' in value:
                if 'source_member' not in value:raise ValueError('supplement missing source_member')
                ref=value.get('bundle',value)
                if not ref.get('sha256'):raise ValueError('supplement bundle hash missing')
                found.append(deepcopy(value))
                return
            for child in value.values():walk(child)
        elif isinstance(value,list):
            for child in value:walk(child)
    walk(document)
    # The same run appears in STATE and CHAT controls; exact member content is
    # idempotent. Conflicting metadata is rejected at recipe compilation.
    return found


def build_recipe(catalogs,append_runs=(),manifests=None):
    manifests=manifests or {};artifacts={};entries={};sources={};excluded=[];pending=[];dedup=[]
    def add_artifact(ref):
        sha=ref['sha256'];prior=artifacts.get(sha)
        if prior and prior['bytes']!=ref['bytes']:raise ValueError('artifact hash/size conflict')
        fid=ref.get('file_id',ref.get('id'))
        if fid:
            for item in artifacts.values():
                if fid in item['file_ids'] and item['sha256']!=sha:raise ValueError('existing file ID content changed')
        item=artifacts.setdefault(sha,{'sha256':sha,'bytes':ref['bytes'],'file_ids':[],'file_names':[]})
        if fid and fid not in item['file_ids']:item['file_ids'].append(fid)
        name=ref.get('file_name',ref.get('name'))
        if name and name not in item['file_names']:item['file_names'].append(name)
    def add(entry):
        _check_entry(entry);add_artifact(entry)
        target=entries if entry['role']=='candidate_chat' else sources
        key=member_key(entry)
        # Same inner chat bytes referenced by another archive are diagnostics
        # for the same data, not another authorized training contribution.
        identity=entry.get('member_sha256') or entry['sha256']
        for existing in target.values():
            if (existing.get('member_sha256') or existing['sha256'])==identity:
                if existing['rows']!=entry['rows']:raise ValueError('duplicate member row count conflict')
                dedup.append({'duplicate':content_identity(entry),'retained_member_key':member_key(existing)})
                return
        target[key]=deepcopy(entry)
    for catalog in catalogs:
        for ref in catalog.get('artifacts',{}).values():add_artifact(ref)
        for entry in catalog.get('members',[]):
            if entry.get('role') in ROLES:
                try:add(entry)
                except ValueError as error:
                    # Every candidate requiring missing discovery is surfaced;
                    # stream creation fails until resolved, never skips it.
                    if 'discovery required' not in str(error):raise
                    pending.append({'entry':content_identity(entry),'reason':str(error)})
            else:
                excluded.append({'sha256':entry.get('sha256'),'member':entry.get('member'),
                                 'role':entry.get('role'),'reason':'NOT_DECLARED_CURRENT_CANDIDATE_CHAT'})
    for run in append_runs:
        bundle=run.get('bundle',run);add_artifact(bundle)
        manifest=manifests.get(bundle['sha256'])
        if manifest is None:
            pending.append({'sha256':bundle['sha256'],'chat_member':run['chat_member'],
                            'reason':'EXACT_INNER_MANIFEST_REQUIRED_NO_SUPPLEMENT_SKIPPED'})
            continue
        for field in ('source_member','chat_member'):
            if field in manifest and manifest[field]!=run[field]:raise ValueError('append descriptor conflicts with declared manifest role')
        member_refs=manifest.get('members',{})
        if not member_refs and all(key in manifest for key in ('source','view')):
            # Numeric payload manifests keep source/view metadata directly;
            # do not skip later arithmetic ZIP supplements using that schema.
            member_refs={manifest['source']['name']:manifest['source'],manifest['view']['name']:manifest['view']}
            if run['source_member']!=manifest['source']['name'] or run['chat_member']!=manifest['view']['name']:
                raise ValueError('numeric source/view role mismatch')
        for role,path,count in [('candidate_source',run['source_member'],run.get('cases',manifest.get('accepted_cases'))),
                                ('candidate_chat',run['chat_member'],run.get('chat_rows',manifest.get('chat_rows')))]:
            ref=member_refs.get(path)
            if not ref:raise ValueError('declared supplement member absent from supplied manifest')
            if count is None:raise ValueError('append member row count missing')
            add({**bundle,'file_id':bundle.get('file_id',bundle.get('id')),'role':role,
                 'member':path,'member_sha256':ref['sha256'],'member_bytes':ref['bytes'],'rows':count,
                 'family':run.get('run_id','explicit_future_append')})
    recipe={'schema':'MathVisionKid.candidate_union_recipe.v1','artifacts':artifacts,
            'chat_members':list(entries.values()),'source_members':list(sources.values()),
            'excluded_members':excluded,'duplicate_member_references':dedup,'pending_discovery':pending,
            'raw_candidate_chat_rows_including_declared_current_splits':sum(x['rows'] for x in entries.values()),
            'future_training_selector':'row.split == train; never rewrite validation/test',
            'full_archive_audit_complete':False,'training_started':False}
    return recipe


def recipe_identity(recipe,split,overlay_sha256=None):
    return digest({'schema':recipe['schema'],'split':split,
                   'chat_members':[content_identity(x) for x in recipe['chat_members']],
                   'read_time_sourcehash_overlay_sha256':overlay_sha256})


@dataclass(frozen=True)
class Cursor:
    recipe_sha256:str
    split:str
    member_index:int=0
    next_line:int=0


class CandidateStream:
    def __init__(self,recipe,paths,split,overlay=None):
        if split not in SPLITS:raise ValueError('choose explicit split')
        if recipe.get('pending_discovery'):raise ValueError('unresolved candidate member discovery; refusing partial union')
        if not recipe.get('chat_members'):raise ValueError('empty candidate union')
        self.recipe=recipe;self.paths=paths;self.split=split;self.overlay=overlay
        self.identity=recipe_identity(recipe,split,overlay.overlay_sha256 if overlay else None)
        self.entries=recipe['chat_members']

    def path_for(self,entry):
        # Caller-supplied local mounts only. No filename search, fallback
        # download, path conversion or connector/account binding is inferred.
        path=self.paths.get(entry['sha256'])
        if path is None and entry.get('file_id'):path=self.paths.get(entry['file_id'])
        if path is None:raise ValueError('explicit mounted payload path missing: '+entry['sha256'])
        return Path(path)

    def events(self,cursor=None):
        cursor=Cursor(**cursor) if isinstance(cursor,dict) else cursor
        cursor=cursor or Cursor(self.identity,self.split)
        if cursor.recipe_sha256!=self.identity or cursor.split!=self.split:raise ValueError('recipe/split cursor changed')
        if cursor.member_index<0 or cursor.member_index>len(self.entries) or cursor.next_line<0:raise ValueError('invalid cursor')
        if cursor.member_index==len(self.entries) and cursor.next_line:raise ValueError('invalid terminal cursor')
        for index in range(cursor.member_index,len(self.entries)):
            entry=self.entries[index];start=cursor.next_line if index==cursor.member_index else 0;count=0
            _check_entry(entry)
            with A.payload(entry,self.path_for(entry)) as stream:
                for count,text in enumerate(stream,1):
                    if count<=start:continue
                    if not text.strip():raise ValueError('blank JSONL row')
                    raw=json.loads(text)
                    if not isinstance(raw,dict) or raw.get('split') not in SPLITS:
                        raise ValueError('explicit known split required; missing split never becomes train')
                    raw=L.validate_chat(raw);row_split=raw['split']
                    next_cursor=Cursor(self.identity,self.split,index,count)
                    if row_split!=self.split:
                        yield None,next_cursor,{'kind':'EXCLUDED_OTHER_SPLIT','original_split':row_split}
                        continue
                    row=raw;provenance={'kind':'CANDIDATE','member_key':member_key(entry),
                        'artifact_sha256':entry['sha256'],'chat_member_sha256':entry.get('member_sha256') or entry['sha256'],
                        'original_chat_canonical_sha256':digest(raw),'sourcehash_overlay_applied':False}
                    if self.overlay and raw['sample_id'] in self.overlay.chats:
                        source,link=self.overlay.chats[raw['sample_id']]
                        row=self.overlay.apply(raw,source['source_binding']['member_sha256'],provenance['chat_member_sha256'])
                        provenance.update(sourcehash_overlay_applied=True,sourcehash_origin=row['sourcehash_origin'])
                    elif raw.get('source_row_sha256'):
                        provenance['sourcehash_origin']='ORIGINAL_RAW_FIELD_NOT_REVERIFIED_BY_THIS_STREAM'
                    else:
                        provenance['sourcehash_origin']='NO_OVERLAY_FOR_THIS_ROW_SOURCE_LINKAGE_AUDIT_PENDING'
                    yield row,next_cursor,provenance
            if start>count:raise ValueError('cursor beyond member end')
            if count!=entry['rows']:raise ValueError('candidate member row count mismatch')
            # EOF is acknowledged separately only after expected count+gzip CRC
            # pass. It advances past a completely consumed member durably.
            yield None,Cursor(self.identity,self.split,index+1,0),{'kind':'MEMBER_COMPLETE','member_key':member_key(entry)}

    def iter_with_cursors(self,cursor=None):
        for row,next_cursor,evidence in self.events(cursor):
            if row is not None:yield row,next_cursor


class DataOnlyConsumer:
    """Disk-backed exact-ID dedup and successful-row acknowledgement.

    handler must be idempotent by sample/content hash if it has external side
    effects: local SQLite cannot transactionally roll back another system.
    No handler is called for other splits, repeats or audit/history members.
    """
    def __init__(self,path,stream):
        self.stream=stream;self.db=sqlite3.connect(path)
        self.db.executescript('''CREATE TABLE IF NOT EXISTS config(identity TEXT PRIMARY KEY);
        CREATE TABLE IF NOT EXISTS cursor(document TEXT);
        CREATE TABLE IF NOT EXISTS seen(sample TEXT PRIMARY KEY,hash TEXT,group_id TEXT,case_id TEXT,mode TEXT,split TEXT,
          UNIQUE(case_id,mode));
        CREATE TABLE IF NOT EXISTS counts(kind TEXT PRIMARY KEY,n INTEGER);
        CREATE TABLE IF NOT EXISTS member_done(id TEXT PRIMARY KEY);''')
        config=self.db.execute('SELECT identity FROM config').fetchone()
        if config and config[0]!=stream.identity:
            self.db.close();raise ValueError('consumer recipe or split changed; preserve DB and create new union revision')
        self.db.execute('INSERT OR IGNORE INTO config VALUES (?)',(stream.identity,));self.db.commit()

    def increment(self,kind):
        self.db.execute('INSERT INTO counts VALUES (?,1) ON CONFLICT(kind) DO UPDATE SET n=n+1',(kind,))

    @staticmethod
    def extend_recipe(path,previous_recipe,next_recipe,split,overlay_sha256=None):
        """Explicit append-only resume migration; never reinterpret old rows."""
        if next_recipe.get('pending_discovery'):raise ValueError('new recipe has unresolved supplement discovery')
        old=[content_identity(x) for x in previous_recipe['chat_members']]
        new=[content_identity(x) for x in next_recipe['chat_members']]
        if len(new)<len(old) or new[:len(old)]!=old:raise ValueError('resume requires unchanged old member prefix')
        before=recipe_identity(previous_recipe,split,overlay_sha256);after=recipe_identity(next_recipe,split,overlay_sha256)
        db=sqlite3.connect(path)
        try:
            with db:
                config=db.execute('SELECT identity FROM config').fetchone()
                if not config or config[0]!=before:raise ValueError('wrong prior consumer identity')
                saved=db.execute('SELECT document FROM cursor').fetchone()
                if saved:
                    cursor=json.loads(saved[0])
                    if cursor['recipe_sha256']!=before or cursor['split']!=split:raise ValueError('cursor/config mismatch')
                    cursor['recipe_sha256']=after
                    db.execute('UPDATE cursor SET document=?',(canonical(cursor),))
                db.execute('UPDATE config SET identity=?',(after,))
        finally:db.close()

    def consume(self,handler,max_rows=None):
        if max_rows is not None and max_rows<=0:raise ValueError('positive bound required')
        saved=self.db.execute('SELECT document FROM cursor').fetchone();cursor=json.loads(saved[0]) if saved else None
        accepted=0
        for row,next_cursor,evidence in self.stream.events(cursor):
            self.db.execute('BEGIN IMMEDIATE')
            try:
                if row is None:
                    self.increment(evidence['kind'])
                    if evidence['kind']=='MEMBER_COMPLETE':self.db.execute('INSERT OR IGNORE INTO member_done VALUES (?)',(evidence['member_key'],))
                else:
                    identity=evidence['original_chat_canonical_sha256'];prior=self.db.execute('SELECT hash FROM seen WHERE sample=?',(row['sample_id'],)).fetchone()
                    if prior:
                        if prior[0]!=identity:raise ValueError('conflicting duplicate sample content')
                        self.increment('EXACT_DUPLICATE_SAMPLE')
                    else:
                        # No renumber/rewrite to evade a collision.
                        try:
                            self.db.execute('INSERT INTO seen VALUES (?,?,?,?,?,?)',(row['sample_id'],identity,row['case_group_id'],L.case_id(row),row['mode'],row.get('split','train')))
                        except sqlite3.IntegrityError as error:raise ValueError('conflicting duplicate case/mode') from error
                        handler(row,evidence)
                        self.increment('ACKNOWLEDGED_CANDIDATE');accepted+=1
                self.db.execute('DELETE FROM cursor');self.db.execute('INSERT INTO cursor VALUES (?)',(canonical(asdict(next_cursor)),))
                self.db.commit()
            except Exception:
                self.db.rollback();raise
            if max_rows is not None and accepted>=max_rows:return self.report()
        return self.report()

    def report(self):
        saved=self.db.execute('SELECT document FROM cursor').fetchone()
        incomplete=self.db.execute('SELECT count(*) FROM (SELECT case_id FROM seen GROUP BY case_id HAVING count(*)!=4)').fetchone()[0]
        return {'schema':'MathVisionKid.candidate_consumer_progress.v1','recipe_sha256':self.stream.identity,
                'split':self.stream.split,'counts':dict(self.db.execute('SELECT kind,n FROM counts')),
                'acknowledged_rows':self.db.execute('SELECT count(*) FROM seen').fetchone()[0],
                'complete_members':self.db.execute('SELECT count(*) FROM member_done').fetchone()[0],
                'required_members':len(self.stream.entries),'incomplete_case_modes':incomplete,
                'cursor':json.loads(saved[0]) if saved else None,
                'stream_exhausted':bool(saved and json.loads(saved[0])['member_index']==len(self.stream.entries)),
                'all_data_training_ready':False,'training_started':False}

    def close(self):self.db.close()
