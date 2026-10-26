"""Read-time additive provenance for already verified legacy chat/source links.

Raw old payloads are never rewritten. This proves a derived association with a
hash-pinned source member; it never claims the legacy raw chat had that field.
"""
from copy import deepcopy
import json
from pathlib import Path

from math_data_portable_resume import digest,file_hash
from math_data_archive_audit import linkage_errors


class VerifiedSourceHashOverlay:
    def __init__(self,manifest_path,expected_manifest_sha256):
        manifest_path=Path(manifest_path)
        if file_hash(manifest_path)!=expected_manifest_sha256:
            raise ValueError('externally pinned overlay manifest SHA256 mismatch')
        self.manifest=json.loads(manifest_path.read_text('utf8'))
        ref=self.manifest['overlay'];path=(manifest_path.parent/ref['file_name']).resolve()
        if not path.is_relative_to(manifest_path.parent.resolve()):raise ValueError('overlay path escapes root')
        if path.stat().st_size!=ref['bytes'] or file_hash(path)!=ref['sha256']:
            raise ValueError('overlay file byte/hash mismatch')
        self.overlay_sha256=ref['sha256']
        self.sources={};self.chats={}
        for line in path.read_text('utf8').splitlines():
            source=json.loads(line);sid=source['source_sample_id']
            if sid in self.sources:raise ValueError('duplicate overlay source ID')
            if source['source_projection_sha256']!=digest(source['source_projection']):
                raise ValueError('source fingerprint integrity mismatch')
            self.sources[sid]=source
            for chat in source['chat_memberships']:
                key=chat['sample_id']
                if key in self.chats:raise ValueError('ambiguous chat/source overlay membership')
                self.chats[key]=(source,chat)

    def apply(self,row,source_member_sha256,chat_member_sha256):
        """Input must be an original validated raw chat row, before decoration."""
        key=row['sample_id']
        if key not in self.chats:raise ValueError('chat outside explicitly audited overlay')
        source,chat=self.chats[key]
        if source_member_sha256!=source['source_binding']['member_sha256'] or chat_member_sha256!=chat['chat_binding']['member_sha256']:
            raise ValueError('source/chat member identity mismatch')
        expected=source['source_raw_row_sha256']
        if row.get('source_row_sha256') is not None and row['source_row_sha256']!=expected:
            raise ValueError('existing source row hash conflicts with verified source')
        if digest(row)!=chat['original_chat_canonical_sha256']:
            raise ValueError('chat row content hash mismatch')
        errors=linkage_errors(row,source['source_projection'])
        if errors:raise ValueError('source/chat field mismatch: '+','.join(errors))
        result=deepcopy(row)
        originally_present='source_row_sha256' in row
        result['source_row_sha256']=expected
        result['sourcehash_origin']='ORIGINAL_FIELD_VERIFIED_AGAINST_PINNED_SOURCE_MEMBER' if originally_present else 'DERIVED_FROM_VERIFIED_PINNED_SOURCE_MEMBER'
        result['sourcehash_original_field_present']=originally_present
        result['sourcehash_overlay_sha256']=self.overlay_sha256
        return result
