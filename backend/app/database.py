from __future__ import annotations
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import psycopg2
from psycopg2.extras import RealDictCursor

from .config import DATABASE_URL, DEV_USERS, LOCAL_SQLITE_PATH


def _use_sqlite() -> bool:
    return DATABASE_URL.startswith('sqlite') or os.getenv('USE_SQLITE_FOR_TESTS', '').lower() in {'1', 'true', 'yes'}


def _sqlite_path() -> str:
    if DATABASE_URL.startswith('sqlite:///'):
        return DATABASE_URL.replace('sqlite:///', '', 1)
    return LOCAL_SQLITE_PATH


def _translate_sql(query: str) -> str:
    if _use_sqlite():
        return query.replace('%s', '?')
    return query


@contextmanager
def db(commit: bool = False):
    if _use_sqlite():
        path = Path(_sqlite_path())
        path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        try:
            yield conn, cur
            if commit:
                conn.commit()
        finally:
            conn.close()
        return

    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    cur = conn.cursor()
    try:
        yield conn, cur
        if commit:
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def fetchone(query: str, params: tuple[Any, ...] = ()):
    with db(False) as (_, cur):
        cur.execute(_translate_sql(query), params)
        row = cur.fetchone()
    return normalize_row(row)


def fetchall(query: str, params: tuple[Any, ...] = ()):
    with db(False) as (_, cur):
        cur.execute(_translate_sql(query), params)
        rows = cur.fetchall()
    return [normalize_row(item) for item in rows]


def execute(query: str, params: tuple[Any, ...] = (), *, fetch: str | None = None):
    with db(True) as (_, cur):
        cur.execute(_translate_sql(query), params)
        if fetch == 'one':
            return normalize_row(cur.fetchone())
        if fetch == 'all':
            return [normalize_row(item) for item in cur.fetchall()]
    return None


def normalize_row(row):
    if row is None:
        return None
    if isinstance(row, sqlite3.Row):
        return dict(row)
    if isinstance(row, dict):
        return dict(row)
    return row


def init_db() -> None:
    if not _use_sqlite():
        return

    execute(
        '''
        CREATE TABLE IF NOT EXISTS branches (
            branch_id INTEGER PRIMARY KEY,
            branch_name TEXT NOT NULL,
            location TEXT NOT NULL,
            status TEXT DEFAULT 'Active'
        )
        '''
    )
    execute(
        '''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            role TEXT NOT NULL,
            branch_id INTEGER,
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        '''
    )
    execute(
        '''
        CREATE TABLE IF NOT EXISTS model_versions (
            version_id INTEGER PRIMARY KEY AUTOINCREMENT,
            model_name TEXT NOT NULL,
            version_number TEXT NOT NULL,
            artifact_signature TEXT NOT NULL,
            is_active INTEGER DEFAULT 0,
            deployed_by INTEGER,
            deployed_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        '''
    )
    execute(
        '''
        CREATE TABLE IF NOT EXISTS samples (
            sample_id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_name TEXT NOT NULL,
            project_reference TEXT,
            material_type TEXT NOT NULL,
            current_state TEXT DEFAULT 'Registered',
            branch_id INTEGER,
            registered_by INTEGER,
            image_path TEXT NOT NULL,
            is_immutable INTEGER DEFAULT 0,
            intake_timestamp TEXT DEFAULT CURRENT_TIMESTAMP
        )
        '''
    )
    execute(
        '''
        CREATE TABLE IF NOT EXISTS ai_inferences (
            inference_id INTEGER PRIMARY KEY AUTOINCREMENT,
            sample_id INTEGER UNIQUE,
            predicted_label TEXT NOT NULL,
            confidence_score REAL NOT NULL,
            decision TEXT NOT NULL,
            version_id INTEGER,
            device_metadata TEXT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP
        )
        '''
    )
    execute(
        '''
        CREATE TABLE IF NOT EXISTS manual_validations (
            validation_id INTEGER PRIMARY KEY AUTOINCREMENT,
            sample_id INTEGER UNIQUE,
            original_ai_label TEXT NOT NULL,
            corrected_label TEXT NOT NULL,
            justification TEXT NOT NULL,
            reviewed_by INTEGER,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP
        )
        '''
    )
    execute(
        '''
        CREATE TABLE IF NOT EXISTS lifecycle_history (
            transition_id INTEGER PRIMARY KEY AUTOINCREMENT,
            sample_id INTEGER,
            from_state TEXT NOT NULL,
            to_state TEXT NOT NULL,
            changed_by INTEGER,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP
        )
        '''
    )
    execute(
        '''
        CREATE TABLE IF NOT EXISTS audit_logs (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            sample_id INTEGER,
            action TEXT NOT NULL,
            endpoint_accessed TEXT,
            old_value TEXT,
            new_value TEXT,
            ip_address TEXT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP
        )
        '''
    )

    if not fetchone('SELECT branch_id FROM branches WHERE branch_id = %s', (1,)):
        execute('INSERT INTO branches (branch_id, branch_name, location, status) VALUES (%s, %s, %s, %s)', (1, 'Main Laboratory - Marikina', 'Marikina', 'Active'))


    from .config import MODEL_REGISTRY_PATH
    import json
    registry = json.loads(Path(MODEL_REGISTRY_PATH).read_text(encoding="utf-8"))
    active = registry[0] if isinstance(registry, list) else next(item for item in registry["versions"] if item.get("is_active"))
    existing_model = fetchone('SELECT version_id FROM model_versions WHERE version_number = %s', (active["version_number"],))
    if not existing_model:
        execute(
            """
            INSERT INTO model_versions (model_name, version_number, artifact_signature, is_active, deployed_by, deployed_at)
            VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
            """,
            (active["model_name"], active["version_number"], active["artifact_signature"], 1, None),
        )

    for user in DEV_USERS:
        execute(
            '''
            INSERT OR REPLACE INTO users (user_id, username, password_hash, full_name, role, branch_id, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ''',
            (user['user_id'], user['username'], user['password'], user['full_name'], user['role'], user['branch_id'], 1),
        )
