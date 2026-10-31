"""Private bounded SQLite catalog. No network, direct account IDs, or training effects."""
from contextlib import closing
from hashlib import sha256
import sqlite3
import time
import unicodedata
from pathlib import Path


def normalized_source(text):
    return ' '.join(unicodedata.normalize('NFC',text).split())


class CatalogStore:
    def __init__(self, path, *, ttl=30*86400, max_entries=500, max_audio_bytes=128*1024*1024):
        self.path=Path(path);self.ttl=ttl;self.max_entries=max_entries;self.max_audio_bytes=max_audio_bytes

    def connect(self):
        self.path.parent.mkdir(parents=True,exist_ok=True)
        db=sqlite3.connect(self.path,timeout=.15)
        try:
            db.execute('PRAGMA journal_mode=WAL')
            db.execute('PRAGMA journal_size_limit=1048576')
            db.execute('''CREATE TABLE IF NOT EXISTS entries (
                kind TEXT NOT NULL, scope TEXT NOT NULL, key TEXT NOT NULL, policy TEXT NOT NULL,
                payload BLOB NOT NULL, digest TEXT NOT NULL, created REAL NOT NULL, used REAL NOT NULL,
                expires REAL NOT NULL, hits INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY(kind,scope,key,policy))''')
            return db
        except BaseException:
            db.close();raise

    def get(self,kind,scope,key,policy):
        now=time.time()
        with closing(self.connect()) as db,db:
            row=db.execute('SELECT payload,digest,expires FROM entries WHERE kind=? AND scope=? AND key=? AND policy=?',
                           (kind,scope,key,policy)).fetchone()
            if row is None:return None
            if (not isinstance(row[0],bytes) or not isinstance(row[2],(int,float))
                    or row[2]<=now or sha256(row[0]).hexdigest()!=row[1]):
                db.execute('DELETE FROM entries WHERE kind=? AND scope=? AND key=? AND policy=?',(kind,scope,key,policy));return None
            db.execute('UPDATE entries SET used=?,hits=hits+1 WHERE kind=? AND scope=? AND key=? AND policy=?',
                       (now,kind,scope,key,policy))
            return bytes(row[0])

    def put(self,kind,scope,key,policy,payload):
        limit=65536 if kind=='plan' else 8*1024*1024
        if kind not in {'plan','audio'} or not isinstance(payload,bytes) or not 0<len(payload)<=limit:
            raise ValueError('Invalid catalog payload')
        if kind=='audio' and len(payload)>self.max_audio_bytes:return
        now=time.time()
        with closing(self.connect()) as db,db:
            db.execute('DELETE FROM entries WHERE expires<=?',(now,))
            db.execute('INSERT OR REPLACE INTO entries VALUES (?,?,?,?,?,?,?,?,?,0)',
                       (kind,scope,key,policy,payload,sha256(payload).hexdigest(),now,now,now+self.ttl))
            # ponytail: bounded LRU per kind; move to the existing database if multi-host replication is needed.
            db.execute('DELETE FROM entries WHERE kind=? AND rowid NOT IN (SELECT rowid FROM entries WHERE kind=? ORDER BY used DESC,rowid DESC LIMIT ?)',
                       (kind,kind,self.max_entries))
            if kind=='audio':
                total=db.execute("SELECT COALESCE(SUM(length(payload)),0) FROM entries WHERE kind='audio'").fetchone()[0]
                while total>self.max_audio_bytes:
                    oldest=db.execute("SELECT rowid,length(payload) FROM entries WHERE kind='audio' ORDER BY used,rowid LIMIT 1").fetchone()
                    db.execute('DELETE FROM entries WHERE rowid=?',(oldest[0],));total-=oldest[1]

    def remove(self,kind,scope,key,policy):
        with closing(self.connect()) as db,db:
            db.execute('DELETE FROM entries WHERE kind=? AND scope=? AND key=? AND policy=?',(kind,scope,key,policy))

    def audit(self,*,prune=False):
        if not self.path.is_file():return dict(expired=0,corrupt=0,pruned=prune,groups=[])
        now=time.time()
        # Inspecting the private inventory must not initialize/mutate a database.
        connection=self.connect() if prune else sqlite3.connect(self.path.resolve().as_uri()+'?mode=ro',uri=True,timeout=.15)
        with closing(connection) as db,db:
            expired=db.execute('SELECT count(*) FROM entries WHERE expires<=?',(now,)).fetchone()[0]
            corrupt=[row[0] for row in db.execute('SELECT rowid,payload,digest FROM entries')
                     if not isinstance(row[1],bytes) or sha256(row[1]).hexdigest()!=row[2]]
            if prune:
                db.execute('DELETE FROM entries WHERE expires<=?',(now,))
                db.executemany('DELETE FROM entries WHERE rowid=?',[(item,) for item in corrupt])
            rows=db.execute('SELECT kind,count(*),sum(length(payload)),sum(hits) FROM entries GROUP BY kind').fetchall()
            return dict(expired=expired,corrupt=len(corrupt),pruned=prune,
                        groups=[dict(kind=row[0],entries=row[1],bytes=row[2],hits=row[3]) for row in rows])
