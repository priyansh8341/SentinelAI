"""Local snapshot history with an optimistic revision check."""
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
from contextlib import closing

class RevisionConflict(Exception):
    pass

class SnapshotStore:
    def __init__(self, path):
        self.path=Path(path)

    def connect(self):
        self.path.parent.mkdir(parents=True,exist_ok=True)
        db=sqlite3.connect(self.path,timeout=15)
        db.row_factory=sqlite3.Row
        db.execute('''CREATE TABLE IF NOT EXISTS runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT, previous_id INTEGER,
            snapshot TEXT NOT NULL, insight TEXT NOT NULL, diff TEXT NOT NULL,
            mode TEXT NOT NULL, model TEXT NOT NULL, created TEXT NOT NULL)''')
        db.commit()
        return db

    def latest(self):
        with closing(self.connect()) as db:
            row=db.execute('SELECT * FROM runs ORDER BY id DESC LIMIT 1').fetchone()
            return dict(row) if row else None

    def history(self):
        with closing(self.connect()) as db:
            rows=db.execute('SELECT * FROM runs ORDER BY id DESC LIMIT 10').fetchall()
            return [dict(id=r['id'],when=r['created'],tag='Baseline' if r['mode']=='baseline' else 'Comparison',note=r['snapshot'].splitlines()[0][:100]) for r in rows]

    def save(self,expected_id,snapshot,insight,diff,mode,model):
        with closing(self.connect()) as db:
            db.execute('BEGIN IMMEDIATE')
            latest=db.execute('SELECT id FROM runs ORDER BY id DESC LIMIT 1').fetchone()
            if (latest['id'] if latest else None)!=expected_id:
                raise RevisionConflict('Snapshot changed while the model was working.')
            stamp=datetime.now(timezone.utc).isoformat(timespec='seconds')
            cursor=db.execute('INSERT INTO runs(previous_id,snapshot,insight,diff,mode,model,created) VALUES(?,?,?,?,?,?,?)',(expected_id,snapshot,insight,diff,mode,model,stamp))
            db.commit()
            return cursor.lastrowid
