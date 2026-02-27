"""Dog Poop Tracker - Database Layer.

Uses SQLite stored at ~/.dpt/poop.db
Dogs = services/endpoints. Poops = health check results.
"""

import json
import sqlite3
from pathlib import Path

DB_PATH = Path.home() / ".dpt" / "poop.db"


def get_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS dogs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            url TEXT NOT NULL,
            method TEXT DEFAULT 'GET',
            headers TEXT DEFAULT '{}',
            expected_status INTEGER DEFAULT 200,
            timeout REAL DEFAULT 10.0,
            interval INTEGER DEFAULT 60,
            enabled INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS poops (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dog_id INTEGER NOT NULL,
            checked_at TEXT DEFAULT (datetime('now')),
            status_code INTEGER,
            latency_ms REAL,
            consistency TEXT NOT NULL,
            response_size INTEGER,
            healthy INTEGER DEFAULT 1,
            error TEXT,
            FOREIGN KEY (dog_id) REFERENCES dogs(id) ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_poops_dog_id ON poops(dog_id);
        CREATE INDEX IF NOT EXISTS idx_poops_checked_at ON poops(checked_at);
    """)
    conn.commit()
    conn.close()


def add_dog(name, url, method="GET", headers=None, expected_status=200, timeout=10.0, interval=60):
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO dogs (name, url, method, headers, expected_status, timeout, interval) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (name, url, method, json.dumps(headers or {}), expected_status, timeout, interval),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def remove_dog(name):
    conn = get_db()
    cur = conn.execute("DELETE FROM dogs WHERE name = ?", (name,))
    conn.commit()
    deleted = cur.rowcount > 0
    conn.close()
    return deleted


def get_dogs(enabled_only=False):
    conn = get_db()
    query = "SELECT * FROM dogs"
    if enabled_only:
        query += " WHERE enabled = 1"
    query += " ORDER BY name"
    dogs = conn.execute(query).fetchall()
    conn.close()
    return [dict(d) for d in dogs]


def get_dog(name):
    conn = get_db()
    dog = conn.execute("SELECT * FROM dogs WHERE name = ?", (name,)).fetchone()
    conn.close()
    return dict(dog) if dog else None


def toggle_dog(name):
    """Toggle enabled state. Returns new enabled state (True/False) or None if not found."""
    conn = get_db()
    dog = conn.execute("SELECT enabled FROM dogs WHERE name = ?", (name,)).fetchone()
    if not dog:
        conn.close()
        return None
    new_state = 0 if dog["enabled"] else 1
    conn.execute(
        'UPDATE dogs SET enabled = ?, updated_at = datetime("now") WHERE name = ?',
        (new_state, name),
    )
    conn.commit()
    conn.close()
    return bool(new_state)


def log_poop(dog_name, status_code, latency_ms, consistency, healthy, response_size=None, error=None):
    conn = get_db()
    dog = conn.execute("SELECT id FROM dogs WHERE name = ?", (dog_name,)).fetchone()
    if not dog:
        conn.close()
        return
    conn.execute(
        """INSERT INTO poops (dog_id, status_code, latency_ms, consistency, response_size, healthy, error)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (dog["id"], status_code, latency_ms, consistency, response_size, 1 if healthy else 0, error),
    )
    conn.commit()
    conn.close()


def get_poops(dog_name=None, limit=50, hours=None):
    conn = get_db()
    query = """SELECT p.*, d.name as dog_name, d.url as dog_url
               FROM poops p JOIN dogs d ON p.dog_id = d.id"""
    params = []
    conditions = []
    if dog_name:
        conditions.append("d.name = ?")
        params.append(dog_name)
    if hours:
        conditions.append("p.checked_at >= datetime('now', ?)")
        params.append(f"-{hours} hours")
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY p.checked_at DESC LIMIT ?"
    params.append(limit)
    poops = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(p) for p in poops]


def get_last_poop(dog_name):
    conn = get_db()
    poop = conn.execute(
        """SELECT p.*, d.name as dog_name FROM poops p
           JOIN dogs d ON p.dog_id = d.id
           WHERE d.name = ? ORDER BY p.checked_at DESC LIMIT 1""",
        (dog_name,),
    ).fetchone()
    conn.close()
    return dict(poop) if poop else None


def get_stats(dog_name=None, hours=24):
    conn = get_db()
    base = """FROM poops p JOIN dogs d ON p.dog_id = d.id
              WHERE p.checked_at >= datetime('now', ?)"""
    params = [f"-{hours} hours"]
    if dog_name:
        base += " AND d.name = ?"
        params.append(dog_name)

    total = conn.execute(f"SELECT COUNT(*) as cnt {base}", params).fetchone()["cnt"]
    healthy = conn.execute(f"SELECT COUNT(*) as cnt {base} AND p.healthy = 1", params).fetchone()["cnt"]

    lat_row = conn.execute(
        f"SELECT AVG(p.latency_ms) as avg_lat, MIN(p.latency_ms) as min_lat, MAX(p.latency_ms) as max_lat {base} AND p.latency_ms IS NOT NULL",
        params,
    ).fetchone()

    consistency_breakdown = conn.execute(
        f"SELECT p.consistency, COUNT(*) as cnt {base} GROUP BY p.consistency ORDER BY cnt DESC",
        params,
    ).fetchall()

    conn.close()
    return {
        "total_checks": total,
        "healthy_checks": healthy,
        "uptime_pct": round((healthy / total * 100), 2) if total > 0 else 100.0,
        "avg_latency": round(lat_row["avg_lat"], 1) if lat_row["avg_lat"] else 0,
        "min_latency": round(lat_row["min_lat"], 1) if lat_row["min_lat"] else 0,
        "max_latency": round(lat_row["max_lat"], 1) if lat_row["max_lat"] else 0,
        "consistency_breakdown": {r["consistency"]: r["cnt"] for r in consistency_breakdown},
    }
