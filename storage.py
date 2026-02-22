"""SQLite storage layer for tasks."""
import sqlite3
from pathlib import Path
from typing import Optional
from models import Task


DB_PATH = Path.home() / ".task_manager" / "tasks.db"


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create the tasks table if it doesn't exist."""
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                title       TEXT    NOT NULL,
                description TEXT    NOT NULL DEFAULT '',
                status      TEXT    NOT NULL DEFAULT 'pending',
                priority    TEXT    NOT NULL DEFAULT 'medium',
                created_at  TEXT    NOT NULL,
                due_date    TEXT,
                tags        TEXT    NOT NULL DEFAULT ''
            )
        """)
        conn.commit()


# ── CRUD ──────────────────────────────────────────────────────────────────────

def add_task(
    title: str,
    description: str = "",
    priority: str = "medium",
    due_date: Optional[str] = None,
    tags: Optional[list[str]] = None,
) -> Task:
    tags_str = ",".join(tags) if tags else ""
    created_at = Task.now()
    with _connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO tasks (title, description, status, priority, created_at, due_date, tags)
            VALUES (?, ?, 'pending', ?, ?, ?, ?)
            """,
            (title, description, priority, created_at, due_date, tags_str),
        )
        conn.commit()
        task_id = cur.lastrowid
    return get_task(task_id)


def get_task(task_id: int) -> Optional[Task]:
    with _connect() as conn:
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    return Task.from_row(tuple(row)) if row else None


def list_tasks(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    tag: Optional[str] = None,
) -> list[Task]:
    query = "SELECT * FROM tasks WHERE 1=1"
    params: list = []
    if status:
        query += " AND status = ?"
        params.append(status)
    if priority:
        query += " AND priority = ?"
        params.append(priority)
    if tag:
        query += " AND (',' || tags || ',' LIKE ?)"
        params.append(f"%,{tag},%")
    query += " ORDER BY CASE priority WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END, created_at"
    with _connect() as conn:
        rows = conn.execute(query, params).fetchall()
    return [Task.from_row(tuple(r)) for r in rows]


def update_task(
    task_id: int,
    title: Optional[str] = None,
    description: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    due_date: Optional[str] = None,
    tags: Optional[list[str]] = None,
) -> Optional[Task]:
    task = get_task(task_id)
    if task is None:
        return None
    updates = {
        "title": title if title is not None else task.title,
        "description": description if description is not None else task.description,
        "status": status if status is not None else task.status,
        "priority": priority if priority is not None else task.priority,
        "due_date": due_date if due_date is not None else task.due_date,
        "tags": ",".join(tags) if tags is not None else ",".join(task.tags),
    }
    with _connect() as conn:
        conn.execute(
            """
            UPDATE tasks SET title=?, description=?, status=?, priority=?, due_date=?, tags=?
            WHERE id=?
            """,
            (*updates.values(), task_id),
        )
        conn.commit()
    return get_task(task_id)


def delete_task(task_id: int) -> bool:
    with _connect() as conn:
        cur = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
    return cur.rowcount > 0


def search_tasks(query: str) -> list[Task]:
    pattern = f"%{query}%"
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM tasks WHERE title LIKE ? OR description LIKE ? OR tags LIKE ?",
            (pattern, pattern, pattern),
        ).fetchall()
    return [Task.from_row(tuple(r)) for r in rows]


def get_stats() -> dict:
    with _connect() as conn:
        total = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
        by_status = dict(
            conn.execute(
                "SELECT status, COUNT(*) FROM tasks GROUP BY status"
            ).fetchall()
        )
        by_priority = dict(
            conn.execute(
                "SELECT priority, COUNT(*) FROM tasks GROUP BY priority"
            ).fetchall()
        )
        overdue = conn.execute(
            "SELECT COUNT(*) FROM tasks WHERE due_date < date('now') AND status != 'done'"
        ).fetchone()[0]
    return {
        "total": total,
        "by_status": by_status,
        "by_priority": by_priority,
        "overdue": overdue,
    }
