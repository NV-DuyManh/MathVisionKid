"""Restore verified, optionally selected files from a private Drive archive.

Use --list without Drive mounted. Restoration never replaces local files.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import stat
import tempfile
import zipfile


MANIFEST = '_ARCHIVE_MANIFEST.json'
REPO = Path(__file__).resolve().parents[2]


def _relative_path(name):
    if not isinstance(name, str) or not name or '\\' in name:
        raise ValueError(f'Unsafe archive path: {name!r}')
    parts = name.split('/')
    reserved = {'CON', 'PRN', 'AUX', 'NUL', *(f'COM{i}' for i in range(1, 10)),
                *(f'LPT{i}' for i in range(1, 10))}
    if (PurePosixPath(name).is_absolute() or PureWindowsPath(name).drive or
            any(part in ('', '.', '..') or part.rstrip(' .') != part or
                part.split('.')[0].upper() in reserved or
                any(char in '<>:"|?*' or ord(char) < 32 for char in part)
                for part in parts)):
        raise ValueError(f'Unsafe archive path: {name!r}')
    return Path(*parts)


def _hash_file(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def _check_destination(path):
    """Reject symlinks, junctions and other reparse points, even above repo root."""
    for ancestor in (*reversed(path.parents), path):
        try:
            attributes = ancestor.lstat()
        except FileNotFoundError:
            continue
        if (stat.S_ISLNK(attributes.st_mode) or
                getattr(attributes, 'st_file_attributes', 0) &
                getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 1024)):
            raise ValueError(f'Destination contains a link or reparse point: {ancestor}')
        if ancestor != path and not stat.S_ISDIR(attributes.st_mode):
            raise ValueError(f'Destination parent is not a directory: {ancestor}')


def restore_archive(repo_root, archive_path, sha256, *, prefix=None,
                    expected_bytes=None, expected_files=None):
    """Validate everything before staging; install each file without overwriting."""
    root = Path(os.path.abspath(repo_root))
    _check_destination(root)
    if not root.is_dir():
        raise ValueError('Repository root must be an existing directory')
    if prefix is not None:
        prefix = _relative_path(prefix).as_posix()
    if not isinstance(sha256, str) or not re.fullmatch('[0-9a-f]{64}', sha256):
        raise ValueError('Archive SHA-256 must contain 64 lowercase hex characters')
    with Path(archive_path).open('rb') as stream:
        if expected_bytes is not None and os.fstat(stream.fileno()).st_size != expected_bytes:
            raise ValueError('Archive size differs from the catalog')
        if hashlib.file_digest(stream, 'sha256').hexdigest() != sha256:
            raise ValueError('Archive SHA-256 differs from the catalog')
        stream.seek(0)
        with zipfile.ZipFile(stream) as archive:
            members = {}
            normalized = set()
            for info in archive.infolist():
                name = info.filename.rstrip('/') if info.is_dir() else info.filename
                _relative_path(name)
                if stat.S_ISLNK(info.external_attr >> 16):
                    raise ValueError(f'Archive contains a symbolic link: {name}')
                if name.casefold() in normalized:
                    raise ValueError(f'Duplicate archive path: {name}')
                normalized.add(name.casefold())
                if not info.is_dir():
                    members[name] = info
            if MANIFEST not in members:
                raise ValueError('Archive has no verification manifest')
            file_names = {name.casefold() for name in members}
            for name in members:
                if any(parent.as_posix().casefold() in file_names
                       for parent in PurePosixPath(name).parents):
                    raise ValueError(f'Archive file is also a parent directory: {name}')
            manifest = json.loads(archive.read(MANIFEST))
            if manifest.get('version') != 1 or not isinstance(manifest.get('files'), list):
                raise ValueError('Unsupported archive manifest')
            records = {}
            for item in manifest['files']:
                name = item['path']
                _relative_path(name)
                if name == MANIFEST or name in records:
                    raise ValueError(f'Duplicate or reserved manifest path: {name}')
                if (type(item['bytes']) is not int or item['bytes'] < 0 or
                        type(item['mtime_ns']) is not int or item['mtime_ns'] < 0 or
                        not re.fullmatch('[0-9a-f]{64}', item['sha256'])):
                    raise ValueError(f'Invalid verification metadata: {name}')
                records[name] = item
            if set(records) != set(members) - {MANIFEST}:
                raise ValueError('Manifest does not match all archive files')
            if expected_files is not None and len(records) != expected_files:
                raise ValueError('Archive file count differs from the catalog')
            pending, skipped = [], 0
            for name, item in records.items():
                if prefix is not None and name != prefix and not name.startswith(prefix + '/'):
                    continue
                destination = root / _relative_path(name)
                _check_destination(destination)
                if members[name].file_size != item['bytes']:
                    raise ValueError(f'Entry size differs from the manifest: {name}')
                if destination.exists():
                    if (not destination.is_file() or destination.stat().st_size != item['bytes'] or
                            _hash_file(destination) != item['sha256']):
                        raise ValueError(f'Local file conflicts with archive: {name}')
                    skipped += 1
                else:
                    pending.append((name, item, destination))
            if not pending and not skipped:
                raise ValueError('No archive files match the requested prefix')
            # Stage all selected bytes first so bad data cannot cause a partial restore.
            with tempfile.TemporaryDirectory(prefix='.drive-restore-', dir=root) as staging:
                prepared = []
                for number, (name, item, destination) in enumerate(pending):
                    temporary = Path(staging) / str(number)
                    digest, size = hashlib.sha256(), 0
                    with archive.open(members[name]) as source, temporary.open('xb') as target:
                        while chunk := source.read(1024 * 1024):
                            size += len(chunk)
                            digest.update(chunk)
                            target.write(chunk)
                    if size != item['bytes'] or digest.hexdigest() != item['sha256']:
                        raise ValueError(f'Entry bytes differ from the manifest: {name}')
                    os.utime(temporary, ns=(item['mtime_ns'], item['mtime_ns']))
                    prepared.append((temporary, destination))
                for temporary, destination in prepared:
                    _check_destination(destination)
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    _check_destination(destination)
                    # Both paths are on the repository volume; link creates atomically
                    # and fails if a destination appeared since preflight.
                    os.link(temporary, destination)
            return {'restored': len(pending), 'skipped': skipped}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--list', action='store_true', help='List catalog without reading Drive')
    action.add_argument('--id', help='Archive ID from docs/drive-archives.json')
    parser.add_argument('--prefix', help='Restore only this repository-relative path or folder')
    parser.add_argument('--drive-root', type=Path, help='Override the mounted archive folder')
    parser.add_argument('--repo-root', type=Path, default=REPO)
    args = parser.parse_args(argv)
    try:
        catalog = json.loads((args.repo_root / 'docs/drive-archives.json').read_text(encoding='utf-8'))
        if catalog.get('version') != 1:
            raise ValueError('Unsupported archive catalog')
        if args.list:
            for item in catalog['archives']:
                print(f"{item['id']}: {item['files']} files, {item['bytes'] / 1048576:.1f} MiB — {item['path']}")
            return 0
        matches = [item for item in catalog['archives'] if item['id'] == args.id]
        if len(matches) != 1:
            raise ValueError('Choose one archive ID shown by --list')
        item = matches[0]
        drive_root = args.drive_root or Path('G:/') / _relative_path(catalog['drive_root'])
        result = restore_archive(args.repo_root, drive_root / _relative_path(item['path']),
                                 item['sha256'], prefix=args.prefix,
                                 expected_bytes=item['bytes'], expected_files=item['files'])
        print(f"Restored {result['restored']} files; {result['skipped']} identical local files skipped.")
        return 0
    except (OSError, ValueError, KeyError, TypeError, zipfile.BadZipFile) as exc:
        parser.exit(1, f'Restore stopped: {exc}\n')


if __name__ == '__main__':
    raise SystemExit(main())
