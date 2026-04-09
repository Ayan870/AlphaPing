# app/database.py
import os
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# We use SQLite locally for now (no setup needed)
# Will switch to Postgres when we deploy to VPS
import sqlite3

DB_PATH = "alphaping.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # return dict-like rows
    return conn

def init_db():
    """Create all tables if they don't exist"""
    conn = get_connection()
    cursor = conn.cursor()

    # Signals table — stores every signal generated
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS signals (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            thread_id       TEXT UNIQUE,
            pair            TEXT,
            direction       TEXT,
            entry_low       REAL,
            entry_high      REAL,
            stop_loss       REAL,
            tp1             REAL,
            tp2             REAL,
            tp3             REAL,
            confidence      INTEGER,
            risk_score      INTEGER,
            setup_type      TEXT,
            timeframe       TEXT,
            research_summary TEXT,
            whatsapp_message TEXT,
            human_approved  INTEGER,
            human_feedback  TEXT,
            compliance_passed INTEGER,
            delivery_status TEXT,
            performance_log TEXT,
            created_at      TEXT,
            updated_at      TEXT
        )
    """)

    # Subscribers table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subscribers (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            phone        TEXT UNIQUE,
            plan         TEXT DEFAULT 'free',
            active       INTEGER DEFAULT 1,
            joined_at    TEXT,
            updated_at   TEXT
        )
    """)

    # Performance table — tracks TP/SL hits
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS performance (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            signal_id   INTEGER,
            result      TEXT,
            pnl         REAL,
            tp1_hit     INTEGER DEFAULT 0,
            tp2_hit     INTEGER DEFAULT 0,
            tp3_hit     INTEGER DEFAULT 0,
            sl_hit      INTEGER DEFAULT 0,
            closed_at   TEXT,
            FOREIGN KEY (signal_id) REFERENCES signals(id)
        )
    """)

    conn.commit()
    conn.close()
    print("✅ Database initialized")


def save_signal(thread_id: str, state: dict) -> int:
    """Save a signal state to database. Returns signal ID."""
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
    """Get all signals from database"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM signals ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_signal_by_thread(thread_id: str):
    """Get a single signal by thread_id"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM signals WHERE thread_id = ?", (thread_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def add_subscriber(phone: str, plan: str = "free"):
    """Add or update a subscriber"""
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute("""
        INSERT OR IGNORE INTO subscribers (phone, plan, active, joined_at, updated_at)
        VALUES (?, ?, 1, ?, ?)
    """, (phone, plan, now, now))
    conn.commit()
    conn.close()


def get_subscribers(plan: str = None, active: bool = True):
    """Get all subscribers, optionally filtered by plan"""
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


# ── Quick test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    init_db()

    # Test save signal
    test_state = {
        "candidate_signal": {
            "pair": "BTCUSDT",
            "direction": "LONG",
            "entry_low": 66000.0,
            "entry_high": 66300.0,
            "stop_loss": 65000.0,
            "tp1": 67500.0,
            "tp2": 68500.0,
            "tp3": 70000.0,
            "confidence": 78,
            "risk_score": 2,
            "setup_type": "breakout",
            "timeframe": "1h"
        },
        "research_summary": "BTC strong breakout",
        "final_whatsapp_message": "Test message",
        "human_approved": True,
        "human_feedback": "Looks good",
        "compliance_passed": True,
        "delivery_status": "sent",
        "performance_log": {}
    }

    signal_id = save_signal("test-thread-001", test_state)
    print(f"✅ Signal saved with ID: {signal_id}")

    signals = get_all_signals()
    print(f"✅ Total signals in DB: {len(signals)}")

    # Test subscriber
    add_subscriber("+923001234567", "free")
    subs = get_subscribers()
    print(f"✅ Total subscribers: {len(subs)}")