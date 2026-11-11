#!/usr/bin/env python3
"""
Milo Cognitive Core (Cortex) — Database & State Manager
Part of MiloOS. Built for Arch Linux & Hyprland.
"""

import sqlite3
from pathlib import Path
from typing import Optional, List, Dict, Any

CORTEX_DIR = Path.home() / ".local" / "share" / "milo" / "cortex"
DB_PATH = CORTEX_DIR / "cortex.db"


def get_db_connection() -> sqlite3.Connection:
    CORTEX_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cur = conn.cursor()

    # 1. Topic Centroids & Cognitive Status
    cur.execute("""
    CREATE TABLE IF NOT EXISTS topics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        embedding BLOB NOT NULL,
        encounter_count INTEGER DEFAULT 1,
        is_mastered BOOLEAN DEFAULT FALSE,
        is_dynamic BOOLEAN DEFAULT FALSE,
        ttl_days INTEGER DEFAULT 180,
        last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 2. Daily Episodic Buffer (Cleared during 24-hr consolidation)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS daily_staging (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        topic_id INTEGER,
        query TEXT NOT NULL,
        raw_snippet TEXT NOT NULL,
        source_url TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(topic_id) REFERENCES topics(id)
    );
    """)

    # 3. Permanent Atomic Facts (Synthesized by sleep consolidation)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS atomic_facts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        topic_id INTEGER NOT NULL,
        entity TEXT NOT NULL,
        attribute TEXT NOT NULL,
        fact_value TEXT NOT NULL,
        confidence REAL DEFAULT 1.0,
        verified_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(topic_id) REFERENCES topics(id)
    );
    """)

    # 4. Interaction Log & Satisfaction Tracker
    cur.execute("""
    CREATE TABLE IF NOT EXISTS query_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        query TEXT NOT NULL,
        topic_id INTEGER,
        mode TEXT NOT NULL, -- 'web', 'local', 'offline'
        user_satisfied BOOLEAN DEFAULT TRUE,
        latency_ms REAL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(topic_id) REFERENCES topics(id)
    );
    """)

    cur.execute("CREATE INDEX IF NOT EXISTS idx_topics_name ON topics(name);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_staging_topic ON daily_staging(topic_id);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_facts_topic ON atomic_facts(topic_id);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_facts_entity ON atomic_facts(entity);")

    conn.commit()
    conn.close()
    print(f"[milo-cortex] Initialized SQLite database at {DB_PATH}")


if __name__ == "__main__":
    init_db()
