"""Read verified source images from a mounted Drive without copying batches."""
import gzip
import hashlib
import json
from functools import lru_cache
from pathlib import Path
import zipfile


@lru_cache(maxsize=4)
def _index(path, modified):
    with gzip.open(path, 'rt', encoding='utf-8') as stream:
        return json.load(stream)['sources']


@lru_cache(maxsize=1)
def _row_group(path, size, modified, group):
    import pyarrow.parquet as pq
    return pq.ParquetFile(path).read_row_group(group, columns=['image']).to_pylist()


def read_source_bytes(folder, item):
    """Cloud mappings take priority; unmigrated sources remain local."""
    folder = Path(folder)
    if item.get('mounted_source_path'):
        return read_mapped_bytes({'kind': 'file', 'path': item['mounted_source_path'],
                                  'sha256': item['sha256']})
    for parent in (folder, *folder.parents):
        index = parent / 'storage_sources.json.gz'
        if index.is_file():
            source = _index(str(index), index.stat().st_mtime_ns).get(item['drive_id'])
            if source:
                return read_mapped_bytes(source)
            if item.get('audit_source_batch'):
                original = (parent / item['audit_source_batch'] / 'images' /
                            f"{item['drive_id']}.jpg").resolve()
                if not original.is_relative_to(parent.resolve()):
                    raise ValueError('Unmigrated source must stay inside the dataset')
                return original.read_bytes()
            break
    return (folder / 'images' / f"{item['drive_id']}.jpg").read_bytes()


def read_mapped_bytes(source):
    path = Path(source['path'])
    stat = path.stat()  # Missing/unmounted Drive must fail rather than invent data.
    if source['kind'] == 'file':
        raw = path.read_bytes()
    else:
        if source['kind'] == 'zip':
            try:
                with zipfile.ZipFile(path) as archive:
                    raw = archive.read(source['entry'])
            except (zipfile.BadZipFile, KeyError) as exc:
                raise ValueError('Mapped ZIP image is unavailable or corrupt') from exc
        elif source['kind'] == 'parquet':
            rows = _row_group(str(path), stat.st_size, stat.st_mtime_ns, source['row_group'])
            raw = rows[source['group_row']]['image']['bytes']
        else:
            raise ValueError('Unknown source storage kind')
    if hashlib.sha256(raw).hexdigest() != source['sha256']:
        raise ValueError('Image bytes differ from verified migration source')
    return raw
