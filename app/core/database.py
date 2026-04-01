# app/core/database.py
import sqlite3
import json
from datetime import datetime
from app.core.config import settings


def get_connection():
    conn = sqlite3.connect(settings.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create all tables if they don't exist"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS signals (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            thread_id        TEXT UNIQUE,
            pair             TEXT,
            direction        TEXT,
            entry_low        REAL,
            entry_high       REAL,
            stop_loss        REAL,
            tp1              REAL,
            tp2              REAL,
            tp3              REAL,
            confidence       INTEGER,
            risk_score       INTEGER,
            setup_type       TEXT,
            timeframe        TEXT,
            research_summary TEXT,
            whatsapp_message TEXT,
            human_approved   INTEGER,
            human_feedback   TEXT,
            compliance_passed INTEGER,
            delivery_status  TEXT,
            performance_log  TEXT,
            created_at       TEXT,
            updated_at       TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subscribers (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            phone      TEXT UNIQUE,
            plan       TEXT DEFAULT 'free',
            active     INTEGER DEFAULT 1,
            joined_at  TEXT,
            updated_at TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS performance (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            signal_id INTEGER,
            result    TEXT,
            pnl       REAL,
            tp1_hit   INTEGER DEFAULT 0,
            tp2_hit   INTEGER DEFAULT 0,
            tp3_hit   INTEGER DEFAULT 0,
            sl_hit    INTEGER DEFAULT 0,
            closed_at TEXT,
            FOREIGN KEY (signal_id) REFERENCES signals(id)
        )
    """)

    conn.commit()
    conn.close()
    print("✅ Database initialized")


def save_signal(thread_id: str, state: dict) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    signal = state.get("candidate_signal", {})
    now = datetime.now().isoformat()

    cursor.execute("""
        INSERT OR REPLACE INTO signals (
            thread_id, pair, direction,
            entry_low, entry_high, stop_loss,
            tp1, tp2, tp3,
            confidence, risk_score, setup_type, timeframe,
            research_summary, whatsapp_message,
            human_approved, human_feedback,
            compliance_passed, delivery_status,
            performance_log, created_at, updated_at
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        thread_id,
        signal.get("pair"),
        signal.get("direction"),
        signal.get("entry_low"),
        signal.get("entry_high"),
        signal.get("stop_loss"),
        signal.get("tp1"),
        signal.get("tp2"),
        signal.get("tp3"),
        signal.get("confidence"),
        signal.get("risk_score"),
        signal.get("setup_type"),
        signal.get("timeframe"),
        state.get("research_summary"),
        state.get("final_whatsapp_message"),
        1 if state.get("human_approved") else 0,
        state.get("human_feedback"),
        1 if state.get("compliance_passed") else 0,
        state.get("delivery_status"),
        json.dumps(state.get("performance_log", {})),
        now, now
    ))

    signal_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return signal_id


def get_all_signals():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM signals ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_signal_by_thread(thread_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM signals WHERE thread_id = ?",
        (thread_id,)
    )
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def add_subscriber(phone: str, plan: str = "free"):
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute("""
        INSERT OR IGNORE INTO subscribers
        (phone, plan, active, joined_at, updated_at)
        VALUES (?, ?, 1, ?, ?)
    """, (phone, plan, now, now))
    conn.commit()
    conn.close()


def get_subscribers(plan: str = None, active: bool = True):
    conn = get_connection()
    cursor = conn.cursor()
    if plan:
        cursor.execute(
            "SELECT * FROM subscribers WHERE active=? AND plan=?",
            (1 if active else 0, plan)
        )
    else:
        cursor.execute(
            "SELECT * FROM subscribers WHERE active=?",
            (1 if active else 0,)
        )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]
    
def save_pending_signal(thread_id: str, state: dict, signal_data: dict):
    """Save a pending signal to database"""
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pending_signals (
            thread_id  TEXT PRIMARY KEY,
            state      TEXT,
            signal_data TEXT,
            created_at TEXT
        )
    """)

    cursor.execute("""
        INSERT OR REPLACE INTO pending_signals
        (thread_id, state, signal_data, created_at)
        VALUES (?, ?, ?, ?)
    """, (
        thread_id,
        json.dumps(state),
        json.dumps(signal_data),
        now
    ))
    conn.commit()
    conn.close()


def get_pending_signal(thread_id: str):
    """Get a pending signal from database"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT * FROM pending_signals WHERE thread_id = ?",
            (thread_id,)
        )
        row = cursor.fetchone()
        conn.close()
        if row:
            return {
                "thread_id":   row["thread_id"],
                "state":       json.loads(row["state"]),
                "signal_data": json.loads(row["signal_data"]),
                "created_at":  row["created_at"]
            }
        return None
    except Exception:
        conn.close()
        return None


def get_all_pending_signals():
    """Get all pending signals from database"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pending_signals (
                thread_id   TEXT PRIMARY KEY,
                state       TEXT,
                signal_data TEXT,
                created_at  TEXT
            )
        """)
        cursor.execute(
            "SELECT * FROM pending_signals ORDER BY created_at DESC"
        )
        rows = cursor.fetchall()
        conn.close()
        return [
            {
                "thread_id":   r["thread_id"],
                "state":       json.loads(r["state"]),
                "signal_data": json.loads(r["signal_data"]),
                "created_at":  r["created_at"]
            }
            for r in rows
        ]
    except Exception:
        conn.close()
        return []


def delete_pending_signal(thread_id: str):
    """Remove a pending signal after approval/rejection"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "DELETE FROM pending_signals WHERE thread_id = ?",
            (thread_id,)
        )
        conn.commit()
    except Exception:
        pass
    conn.close()

# ── Quick test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    init_db()
    print("✅ Core database working")