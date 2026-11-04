"""Validate the SQL chain on an explicitly disposable empty PostgreSQL DB.

This checks actual PostgreSQL SQL, not Flyway history/checksum or an upgrade
from existing production data. It never creates/drops a database or reads .env.
"""
import os
from pathlib import Path
import re
import subprocess


def migration_files(directory):
    files = list(directory.glob('V*__*.sql'))
    versions = [int(re.fullmatch(r'V(\d+)__.+\.sql', file.name)[1]) for file in files]
    if not versions or len(versions) != len(set(versions)):
        raise ValueError('Migration versions must be nonempty and unique')
    return [file for _, file in sorted(zip(versions, files))]


def main():
    database = os.environ.get('PGDATABASE', '')
    if not database.endswith('_test') or os.environ.get('GITHUB_ACTIONS') != 'true':
        raise SystemExit('Run only in CI with an explicit disposable *_test database')
    command = ['psql', '-X', '-v', 'ON_ERROR_STOP=1']
    count = subprocess.check_output(command + ['-Atc', "SELECT count(*) FROM information_schema.tables WHERE table_schema='public'"], text=True).strip()
    if count != '0':
        raise SystemExit('Refusing to run migrations on a nonempty database')
    directory = Path(__file__).resolve().parents[2] / 'backend/business-api/src/main/resources/db/migration'
    files = migration_files(directory)
    subprocess.run(command + ['--single-transaction'] + [arg for file in files for arg in ('-f', str(file))], check=True)
    print(f'PASS: {len(files)} migrations executed on disposable PostgreSQL')


if __name__ == '__main__':
    main()
