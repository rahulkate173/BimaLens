"""SQLite-based RAG store for policy chunks.

The database lives at /tmp/bimalens_rag.db inside the Docker container.
That path is persisted via a named Docker volume (rag-data:/tmp).
"""

import sqlite3
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

DB_PATH = "/tmp/bimalens_rag.db"


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create the policy_chunks table if it does not exist."""
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS policy_chunks (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                policy_id     TEXT    NOT NULL,
                page          INTEGER NOT NULL DEFAULT 0,
                section       TEXT    NOT NULL DEFAULT '',
                quote         TEXT    NOT NULL DEFAULT '',
                category      TEXT    NOT NULL DEFAULT '',
                point_summary TEXT    NOT NULL DEFAULT '',
                created_at    TEXT    NOT NULL
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_policy_id ON policy_chunks (policy_id)"
        )
        conn.commit()
    logger.info("RAG SQLite store initialised at %s", DB_PATH)


def store_policy_chunks(policy_id: str, sources: list[dict]) -> None:
    """Upsert all chunks for a policy (DELETE then INSERT in a transaction)."""
    now = datetime.now(timezone.utc).isoformat()
    rows = [
        (
            policy_id,
            int(s.get("page", 0)),
            s.get("section", ""),
            s.get("quote", s.get("exact_quote", "")),
            s.get("category", ""),
            s.get("point_summary", ""),
            now,
        )
        for s in sources
    ]
    with _connect() as conn:
        conn.execute("DELETE FROM policy_chunks WHERE policy_id = ?", (policy_id,))
        conn.executemany(
            """
            INSERT INTO policy_chunks
                (policy_id, page, section, quote, category, point_summary, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
        conn.commit()
    logger.info("Stored %d chunks for policy %s", len(rows), policy_id)


def search_chunks(policy_id: str, query: str, limit: int = 8) -> list[dict]:
    """Keyword search across quote, section, and point_summary using LIKE."""
    keywords = [w.strip() for w in query.split() if len(w.strip()) > 1]
    if not keywords:
        return get_all_chunks(policy_id)[:limit]

    # Build a WHERE clause that ANDs all keywords across the three text columns
    conditions = " AND ".join(
        "(quote LIKE ? OR section LIKE ? OR point_summary LIKE ?)"
        for _ in keywords
    )
    params: list = []
    for kw in keywords:
        pattern = f"%{kw}%"
        params.extend([pattern, pattern, pattern])
    params.append(policy_id)
    params.append(limit)

    sql = f"""
        SELECT * FROM policy_chunks
        WHERE ({conditions}) AND policy_id = ?
        ORDER BY page ASC
        LIMIT ?
    """
    with _connect() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


def get_all_chunks(policy_id: str) -> list[dict]:
    """Return all stored chunks for a policy ordered by page."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM policy_chunks WHERE policy_id = ? ORDER BY page ASC",
            (policy_id,),
        ).fetchall()
    return [dict(r) for r in rows]
