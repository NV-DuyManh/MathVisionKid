import io
import unittest
import zipfile
import sgk_finish_zip_metadata as M


class ZipMetadataTests(unittest.TestCase):
    def build(self):
        stream=io.BytesIO()
        with zipfile.ZipFile(stream,'w',zipfile.ZIP_DEFLATED) as archive:
            archive.writestr('manifest.json','{"members":{"source.jsonl.gz":{"sha256":"test"}}}')
            archive.writestr('source.jsonl.gz',b'never consumed as metadata')
            archive.writestr('sealed/manifest.json','{"never":"read"}')
        return stream.getvalue()

    def test_range_roundtrip_reads_only_manifest(self):
        raw=self.build();end=M.eocd(raw,0,len(raw))
        entries=M.central_directory(raw[end['directory_offset']:end['directory_offset']+end['directory_bytes']],3)
        allowed=[x for x in entries if M.metadata_permitted(x['name'])]
        self.assertEqual([x['name'] for x in allowed],['manifest.json'])
        entry=allowed[0];offset=entry['local_header_offset'];payload=M.local_payload_range(raw[offset:offset+30],entry)
        result=M.decode_metadata(raw[payload['offset']:payload['offset']+payload['bytes']],entry)
        self.assertIn('source.jsonl.gz',result['document']['members'])
        self.assertFalse(result['full_archive_hash_verified_by_range'])

    def test_protected_and_jsonl_payloads_never_decoded(self):
        for name in ['sealed/manifest.json','pilot/index.json','evaluation/manifest.json','chat.jsonl','source.jsonl.gz']:
            entry={'name':name,'uncompressed_bytes':0,'compressed_bytes':0,'method':0,'crc32':0}
            self.assertFalse(M.metadata_permitted(name))
            with self.assertRaises(ValueError):M.decode_metadata(b'',entry)

    def test_crc_and_bounds_detect_tamper(self):
        entry={'name':'manifest.json','uncompressed_bytes':2,'compressed_bytes':2,'method':0,'crc32':0}
        with self.assertRaisesRegex(ValueError,'CRC'):M.decode_metadata(b'{}',entry)
        entry['uncompressed_bytes']=100
        with self.assertRaisesRegex(ValueError,'bound'):M.decode_metadata(b'{}',entry,limit=50)

    def test_truncated_directory_and_wrong_count_rejected(self):
        raw=self.build();end=M.eocd(raw,0,len(raw));directory=raw[end['directory_offset']:end['directory_offset']+end['directory_bytes']]
        with self.assertRaises(ValueError):M.central_directory(directory[:-1])
        with self.assertRaises(ValueError):M.central_directory(directory,4)
        with self.assertRaises(ValueError):M.eocd(raw[:-1],0,len(raw)-1)


if __name__=='__main__':unittest.main(verbosity=2)
