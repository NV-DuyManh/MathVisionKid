import gzip
import hashlib
import json
import zipfile

import pytest

from source_storage import read_source_bytes


@pytest.mark.parametrize('kind', ['file', 'zip', 'parquet'])
def test_mounted_sources_keep_exact_bytes_and_reject_changes(tmp_path, kind):
    raw = b'original image bytes'
    cloud = tmp_path / 'mounted-drive'
    cloud.mkdir()
    path = cloud / ('source.' + kind)
    source = {'kind': kind, 'path': str(path), 'sha256': hashlib.sha256(raw).hexdigest()}
    if kind == 'zip':
        with zipfile.ZipFile(path, 'w') as archive:
            archive.writestr('crop.png', raw)
        source['entry'] = 'crop.png'
    elif kind == 'parquet':
        import pyarrow as pa
        import pyarrow.parquet as pq
        pq.write_table(pa.Table.from_pylist([
            {'image': {'bytes': b'wrong row', 'path': 'other.png'}},
            {'image': {'bytes': raw, 'path': 'crop.png'}}]), path, row_group_size=1)
        source.update(row_group=1, group_row=0)
    else:
        path.write_bytes(raw)
    source['container_sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
    data = tmp_path / 'data'
    folder = data / 'batch/shards/1'
    folder.mkdir(parents=True)
    with gzip.open(data / 'storage_sources.json.gz', 'wt') as stream:
        json.dump({'sources': {'a': source}}, stream)
    assert read_source_bytes(folder, {'drive_id': 'a'}) == raw
    path.write_bytes(b'changed source')
    with pytest.raises(ValueError):
        read_source_bytes(folder, {'drive_id': 'a'})
    path.unlink()
    with pytest.raises(OSError):
        read_source_bytes(folder, {'drive_id': 'a'})


def test_unmigrated_local_source_remains_readable(tmp_path):
    folder = tmp_path / 'batch'
    (folder / 'images').mkdir(parents=True)
    (folder / 'images/a.jpg').write_bytes(b'local image')
    assert read_source_bytes(folder, {'drive_id': 'a'}) == b'local image'


def test_nested_audit_reads_retained_original_without_creating_another_copy(tmp_path):
    original = tmp_path / 'old-batch/images'
    original.mkdir(parents=True)
    (original / 'a.jpg').write_bytes(b'retained original')
    with gzip.open(tmp_path / 'storage_sources.json.gz', 'wt') as stream:
        json.dump({'sources': {}}, stream)
    item = {'drive_id': 'a', 'audit_source_batch': 'old-batch'}
    assert read_source_bytes(tmp_path / 'audit/shards/1', item) == b'retained original'
    item['audit_source_batch'] = '../../outside'
    with pytest.raises(ValueError):
        read_source_bytes(tmp_path / 'audit/shards/1', item)


def test_mounted_selection_skips_tested_content_and_reads_without_batch_copy(tmp_path):
    import sqlite3
    from drive_line_batch import select_mounted
    cloud = tmp_path / 'drive'
    cloud.mkdir()
    (cloud / 'old.jpg').write_bytes(b'tested bytes')
    (cloud / 'new.jpg').write_bytes(b'new bytes')
    db = sqlite3.connect(':memory:')
    db.execute('CREATE TABLE images (sha256 TEXT)')
    db.execute('INSERT INTO images VALUES (?)', (hashlib.sha256(b'tested bytes').hexdigest(),))
    selected = select_mounted(cloud, db, 10)
    assert len(selected) == 1 and selected[0]['name'] == 'new.jpg'
    assert read_source_bytes(tmp_path / 'batch', selected[0]) == b'new bytes'
    (cloud / 'new.jpg').write_bytes(b'changed bytes')
    with pytest.raises(ValueError):
        read_source_bytes(tmp_path / 'batch', selected[0])
    db.close()
