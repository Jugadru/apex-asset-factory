"""Local durable session registry; never replays interrupted work."""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import stat
import sys
import uuid

SCHEMA = 1
IDENT = re.compile(r"[0-9a-f]{32}\Z")
MAX_SNAPSHOT = 2_000_000
TERMINAL = {"PASS", "FAIL", "BLOCKED"}
DDL = """
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY, created TEXT NOT NULL, updated TEXT NOT NULL,
    phase TEXT NOT NULL CHECK(phase IN ('RUNNING','FINISHED','INTERRUPTED')),
    outcome TEXT NOT NULL CHECK(outcome IN ('PASS','FAIL','BLOCKED')),
    report TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS history (
    session_id TEXT NOT NULL REFERENCES sessions(id),
    seq INTEGER NOT NULL, at TEXT NOT NULL, kind TEXT NOT NULL,
    report TEXT NOT NULL, PRIMARY KEY(session_id, seq)
);
"""


def now():
    return datetime.now(timezone.utc).isoformat()


def encode(report):
    value = json.dumps(report, sort_keys=True, ensure_ascii=True, separators=(",", ":"))
    if len(value) > MAX_SNAPSHOT:
        raise ValueError("Registry snapshot exceeds limit")
    return value


def require(condition, message):
    if not condition:
        raise ValueError(message)


def ident(value):
    require(isinstance(value, str) and IDENT.fullmatch(value), "Invalid session ID")
    return value


class Registry:
    """Trusted local Linux directory; SQLite transaction + per-session flock."""
    def __init__(self, root):
        root = Path(root).expanduser()
        require(not root.is_symlink(), "Registry directory cannot be a symlink")
        root.mkdir(mode=0o700, parents=True, exist_ok=True)
        self.root = root.resolve()
        st = self.root.stat()
        require(st.st_uid == os.getuid() and stat.S_IMODE(st.st_mode) & 0o077 == 0,
                "Registry must be owned by operator and private (chmod 700)")
        self.db = self.root / "registry.sqlite3"
        fd = os.open(self.db, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
        try:
            st = os.fstat(fd)
            require(stat.S_ISREG(st.st_mode) and st.st_uid == os.getuid()
                    and stat.S_IMODE(st.st_mode) & 0o077 == 0, "Unsafe registry database")
        finally:
            os.close(fd)
        with self.connect() as db:
            version = db.execute("PRAGMA user_version").fetchone()[0]
            require(version in (0, SCHEMA), "Unsupported registry schema")
            if version == 0:
                db.executescript("BEGIN IMMEDIATE;\n" + DDL +
                                 "\nPRAGMA user_version=1;\nCOMMIT;")

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.db, timeout=5)
        db.row_factory = sqlite3.Row
        try:
            db.execute("PRAGMA foreign_keys=ON")
            db.execute("PRAGMA synchronous=FULL")
            with db:
                yield db
        finally:
            db.close()

    @contextmanager
    def lock(self, session_id):
        fd = os.open(self.root / (ident(session_id) + ".lock"),
                     os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
        try:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise ValueError("Session is locked by an active process") from exc
            yield
        finally:
            os.close(fd)

    @contextmanager
    def session(self, report):
        sid = uuid.uuid4().hex
        report["session_id"] = sid
        with self.lock(sid):
            stamp, payload = now(), encode(report)
            with self.connect() as db:
                db.execute("INSERT INTO sessions VALUES (?,?,?,?,?,?)",
                           (sid, stamp, stamp, "RUNNING", "BLOCKED", payload))
                db.execute("INSERT INTO history VALUES (?,?,?,?,?)",
                           (sid, 1, stamp, "START", payload))
            yield Session(self, sid)
            # No implicit completion: caller must explicitly finish after all tasks.
            # On crash/exception, the last committed snapshot remains RUNNING.

    def _append(self, sid, report, kind, phase):
        ident(sid)
        require(report.get("session_id") == sid, "Snapshot session mismatch")
        require(phase in {"RUNNING", "FINISHED", "INTERRUPTED"}, "Invalid lifecycle")
        require(report.get("status") in TERMINAL, "Invalid outcome")
        stamp, payload = now(), encode(report)
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT phase,report FROM sessions WHERE id=?", (sid,)).fetchone()
            require(row is not None and row["phase"] == "RUNNING", "Session is not running")
            if kind == "CHECKPOINT" and row["report"] == payload:
                return
            seq = db.execute("SELECT MAX(seq)+1 FROM history WHERE session_id=?", (sid,)).fetchone()[0]
            db.execute("UPDATE sessions SET updated=?,phase=?,outcome=?,report=? WHERE id=?",
                       (stamp, phase, report["status"], payload, sid))
            db.execute("INSERT INTO history VALUES (?,?,?,?,?)",
                       (sid, seq, stamp, kind, payload))

    def list(self, limit=50, phase=None):
        require(type(limit) is int and 1 <= limit <= 100, "Limit must be 1..100")
        require(phase in (None, "RUNNING", "FINISHED", "INTERRUPTED"), "Invalid phase")
        with self.connect() as db:
            query = "SELECT id,created,updated,phase,outcome FROM sessions"
            args = []
            if phase:
                query += " WHERE phase=?"
                args.append(phase)
            return [dict(row) for row in db.execute(query + " ORDER BY created DESC,id DESC LIMIT ?", (*args, limit))]

    def show(self, sid):
        with self.connect() as db:
            row = db.execute("SELECT * FROM sessions WHERE id=?", (ident(sid),)).fetchone()
            require(row is not None, "Unknown session")
            result = dict(row)
            result["report"] = json.loads(result["report"])
            return result

    def history(self, sid):
        self.show(sid)
        with self.connect() as db:
            return [{**dict(row), "report": json.loads(row["report"])}
                    for row in db.execute("SELECT seq,at,kind,report FROM history WHERE session_id=? ORDER BY seq", (sid,))]

    def recover(self, sid):
        # Lock proves no cooperating Hub process currently owns this session;
        # it cannot prove external descendants are gone. Never replay or delete.
        self.show(sid)
        with self.lock(sid):
            row = self.show(sid)
            require(row["phase"] == "RUNNING", "Only interrupted RUNNING sessions can be recovered")
            report = row["report"]
            report["status"] = "BLOCKED"
            report["recovery"] = "Interrupted; no jobs replayed. Inspect evidence and start a new explicit session."
            self._append(sid, report, "RECOVER", "INTERRUPTED")
            return self.show(sid)


class Session:
    def __init__(self, registry, sid):
        self.registry, self.sid = registry, sid

    def checkpoint(self, report):
        self.registry._append(self.sid, report, "CHECKPOINT", "RUNNING")

    def finish(self, report):
        require(all(t["status"] in TERMINAL for t in report["tasks"]), "Unfinished tasks")
        self.registry._append(self.sid, report, "FINISH", "FINISHED")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--registry", required=True, type=Path)
    sub = p.add_subparsers(dest="mode", required=True)
    listing = sub.add_parser("list")
    listing.add_argument("--limit", type=int, default=50)
    listing.add_argument("--phase", choices=["RUNNING", "FINISHED", "INTERRUPTED"])
    for mode in ("show", "history", "recover"):
        sub.add_parser(mode).add_argument("session_id")
    args = p.parse_args()
    try:
        registry = Registry(args.registry)
        result = registry.list(args.limit, args.phase) if args.mode == "list" else getattr(registry, args.mode)(args.session_id)
        print(json.dumps(result, indent=2, ensure_ascii=True))
        return 0
    except (OSError, ValueError, sqlite3.Error) as exc:
        print("APEX_REGISTRY_BLOCKED: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
