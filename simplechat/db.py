"""SQLite persistence layer — user accounts and message history."""

import hashlib
import os
import sqlite3
import time


def init_db(db_path):
    """Open (or create) the database and ensure tables exist."""
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            nickname    TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL,
            salt        TEXT NOT NULL,
            created_at  REAL NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            nickname    TEXT NOT NULL,
            content     TEXT NOT NULL,
            timestamp   REAL NOT NULL
        )
    """)
    conn.commit()
    return conn


# ---------------------------------------------------------------------------
# Password helpers
# ---------------------------------------------------------------------------

def _hash_password(password, salt=None):
    if salt is None:
        salt = os.urandom(16)
    h = hashlib.pbkdf2_hmac(
        'sha256', password.encode('utf-8'), salt, 100_000
    )
    return h.hex(), salt.hex()


def _verify_password(password, stored_hash, stored_salt):
    salt = bytes.fromhex(stored_salt)
    h, _ = _hash_password(password, salt)
    return h == stored_hash


# ---------------------------------------------------------------------------
# User account operations
# ---------------------------------------------------------------------------

def user_exists(conn, nickname):
    row = conn.execute(
        "SELECT 1 FROM users WHERE nickname = ?", (nickname,)
    ).fetchone()
    return row is not None


def register_user(conn, nickname, password):
    """Register a new user. Returns True on success, False if nickname taken."""
    try:
        h, salt = _hash_password(password)
        conn.execute(
            "INSERT INTO users (nickname, password_hash, salt, created_at)"
            " VALUES (?, ?, ?, ?)",
            (nickname, h, salt, time.time()),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False


def authenticate_user(conn, nickname, password):
    """Return True if nickname + password are correct."""
    row = conn.execute(
        "SELECT password_hash, salt FROM users WHERE nickname = ?",
        (nickname,),
    ).fetchone()
    if row is None:
        return False
    return _verify_password(password, row[0], row[1])


# ---------------------------------------------------------------------------
# Message history operations
# ---------------------------------------------------------------------------

def save_message(conn, nickname, content):
    conn.execute(
        "INSERT INTO messages (nickname, content, timestamp) VALUES (?, ?, ?)",
        (nickname, content, time.time()),
    )
    conn.commit()


def get_recent_messages(conn, limit=50):
    """Return up to *limit* most recent messages, oldest first."""
    rows = conn.execute(
        "SELECT nickname, content, timestamp FROM messages"
        " ORDER BY id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    return list(reversed(rows))
