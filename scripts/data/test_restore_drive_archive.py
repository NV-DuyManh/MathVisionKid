import hashlib
import json
import os
from pathlib import Path
import stat
from types import SimpleNamespace
import zipfile

import pytest

from restore_drive_archive import MANIFEST, main, restore_archive


def make_archive(tmp_path, files=None, manifest_hash=None, extra=None):
    files = files or {'data/batch/a.jpg': b'image a', 'data/other/b.jpg': b'image b'}
    path = tmp_path / 'archive.zip'
    records = [{'path': name, 'bytes': len(raw),
                'sha256': manifest_hash or hashlib.sha256(raw).hexdigest(),
                'mtime_ns': 1700000000123456700} for name, raw in files.items()]
    with zipfile.ZipFile(path, 'w') as archive:
        for name, raw in files.items():
            archive.writestr(name, raw)
        if extra:
            archive.writestr(*extra)
        archive.writestr(MANIFEST, json.dumps({'version': 1, 'files': records}))
    return path, hashlib.sha256(path.read_bytes()).hexdigest()


def test_subset_round_trip_keeps_time_and_skips_identical_files(tmp_path):
    path, sha = make_archive(tmp_path)
    repo = tmp_path / 'repo'
    repo.mkdir()
    result = restore_archive(repo, path, sha, prefix='data/batch', expected_files=2)
    restored = repo / 'data/batch/a.jpg'
    assert result == {'restored': 1, 'skipped': 0}
    assert restored.read_bytes() == b'image a'
    assert restored.stat().st_mtime_ns == 1700000000123456700
    assert not (repo / 'data/other').exists()
    assert restore_archive(repo, path, sha, prefix='data/batch') == {'restored': 0, 'skipped': 1}
    assert not list(repo.glob('.drive-restore-*'))


def test_tampered_container_and_bad_entry_hash_write_nothing(tmp_path):
    repo = tmp_path / 'repo'
    repo.mkdir()
    path, sha = make_archive(tmp_path)
    with path.open('ab') as stream:
        stream.write(b'tampered')
    with pytest.raises(ValueError, match='Archive SHA-256'):
        restore_archive(repo, path, sha)
    path, sha = make_archive(tmp_path, manifest_hash='0' * 64)
    with pytest.raises(ValueError, match='Entry bytes'):
        restore_archive(repo, path, sha)
    assert list(repo.iterdir()) == []


@pytest.mark.parametrize('name', ['../outside.jpg', '/absolute.jpg', 'C:/outside.jpg',
                                  'data\\..\\outside.jpg', 'data/file.jpg:stream'])
def test_unsafe_archive_entries_are_rejected_before_restore(tmp_path, name):
    path, sha = make_archive(tmp_path, extra=(name, b'unsafe'))
    repo = tmp_path / 'repo'
    repo.mkdir()
    with pytest.raises(ValueError, match='Unsafe archive path'):
        restore_archive(repo, path, sha, prefix='data/batch')
    assert list(repo.iterdir()) == []


def test_conflicting_file_prevents_any_partial_restore(tmp_path):
    path, sha = make_archive(tmp_path)
    repo = tmp_path / 'repo'
    (repo / 'data/other').mkdir(parents=True)
    conflict = repo / 'data/other/b.jpg'
    conflict.write_bytes(b'local edit')
    with pytest.raises(ValueError, match='Local file conflicts'):
        restore_archive(repo, path, sha)
    assert conflict.read_bytes() == b'local edit'
    assert not (repo / 'data/batch').exists()
    assert not list(repo.glob('.drive-restore-*'))


def test_archive_symlink_and_destination_link_are_rejected(tmp_path):
    info = zipfile.ZipInfo('data/link')
    info.create_system = 3
    info.external_attr = (stat.S_IFLNK | 0o777) << 16
    path, sha = make_archive(tmp_path, extra=(info, '../outside'))
    repo = tmp_path / 'repo'
    repo.mkdir()
    with pytest.raises(ValueError, match='symbolic link'):
        restore_archive(repo, path, sha)
    path, sha = make_archive(tmp_path)
    outside = tmp_path / 'outside'
    outside.mkdir()
    try:
        os.symlink(outside, repo / 'data', target_is_directory=True)
    except OSError:
        pytest.skip('Creating symlinks requires a Windows privilege')
    with pytest.raises(ValueError, match='link or reparse point'):
        restore_archive(repo, path, sha)
    assert list(outside.iterdir()) == []


def test_destination_reparse_attribute_is_rejected_before_writing(tmp_path, monkeypatch):
    path, sha = make_archive(tmp_path)
    repo = tmp_path / 'repo'
    (repo / 'data').mkdir(parents=True)
    original_lstat = Path.lstat

    def lstat(candidate, *args, **kwargs):
        attributes = original_lstat(candidate, *args, **kwargs)
        if candidate == repo / 'data':
            return SimpleNamespace(st_mode=attributes.st_mode, st_file_attributes=1024)
        return attributes

    monkeypatch.setattr(Path, 'lstat', lstat)
    with pytest.raises(ValueError, match='link or reparse point'):
        restore_archive(repo, path, sha)
    assert list((repo / 'data').iterdir()) == []


def test_archive_file_cannot_also_be_a_parent_directory(tmp_path):
    path, sha = make_archive(tmp_path, files={'data': b'file', 'data/a.jpg': b'child'})
    repo = tmp_path / 'repo'
    repo.mkdir()
    with pytest.raises(ValueError, match='also a parent directory'):
        restore_archive(repo, path, sha)
    assert list(repo.iterdir()) == []


def test_list_does_not_need_mounted_drive(tmp_path, capsys):
    (tmp_path / 'docs').mkdir()
    (tmp_path / 'docs/drive-archives.json').write_text(json.dumps({
        'version': 1, 'drive_root': 'My Drive/project/archive', 'archives': [
            {'id': 'batch-preview', 'path': 'previews.zip', 'sha256': '0' * 64,
             'bytes': 1024, 'files': 2}]}), encoding='utf-8')
    assert main(['--list', '--repo-root', str(tmp_path),
                 '--drive-root', str(tmp_path / 'not-mounted')]) == 0
    assert 'batch-preview: 2 files' in capsys.readouterr().out
    assert not (tmp_path / 'not-mounted').exists()
