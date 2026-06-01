"""SQLite persistence layer — user accounts and message history."""

import hashlib
import hmac
import os
import sqlite3
import threading
import time


PBKDF2_ITERATIONS = 100_000


class ChatDatabase:
    """Thread-safe wrapper around the app's SQLite connection."""

    def __init__(self, db_path):
        self.path = db_path
        self.lock = threading.RLock()
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        with self.lock:
            self.conn.execute("PRAGMA foreign_keys = ON")
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    nickname    TEXT PRIMARY KEY,
                    password_hash TEXT NOT NULL,
                    salt        TEXT NOT NULL,
                    created_at  REAL NOT NULL
                )
            """)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    nickname    TEXT NOT NULL,
                    content     TEXT NOT NULL,
                    timestamp   REAL NOT NULL
                )
            """)
            self.conn.commit()

    def close(self):
        with self.lock:
            self.conn.close()


def init_db(db_path):
    """Open (or create) the database and ensure tables exist."""
    return ChatDatabase(db_path)


# ---------------------------------------------------------------------------
# Password helpers
# ---------------------------------------------------------------------------

def _hash_password(password, salt=None):
    if salt is None:
        salt = os.urandom(16)
    h = hashlib.pbkdf2_hmac(
        'sha256', password.encode('utf-8'), salt, PBKDF2_ITERATIONS
    )
    return h.hex(), salt.hex()


def _verify_password(password, stored_hash, stored_salt):
    salt = bytes.fromhex(stored_salt)
    h, _ = _hash_password(password, salt)
    return hmac.compare_digest(h, stored_hash)


# ---------------------------------------------------------------------------
# User account operations
# ---------------------------------------------------------------------------

def user_exists(conn, nickname):
    with conn.lock:
        row = conn.conn.execute(
            "SELECT 1 FROM users WHERE nickname = ?", (nickname,)
        ).fetchone()
    return row is not None


def register_user(conn, nickname, password):
    """Register a new user. Returns True on success, False if nickname taken."""
    with conn.lock:
        try:
            h, salt = _hash_password(password)
            conn.conn.execute(
                "INSERT INTO users (nickname, password_hash, salt, created_at)"
                " VALUES (?, ?, ?, ?)",
                (nickname, h, salt, time.time()),
            )
            conn.conn.commit()
            return True
        except sqlite3.IntegrityError:
            conn.conn.rollback()
            return False


def authenticate_user(conn, nickname, password):
    """Return True if nickname + password are correct."""
    with conn.lock:
        row = conn.conn.execute(
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
    with conn.lock:
        conn.conn.execute(
            "INSERT INTO messages (nickname, content, timestamp)"
            " VALUES (?, ?, ?)",
            (nickname, content, time.time()),
        )
        conn.conn.commit()


def get_recent_messages(conn, limit=50):
    """Return up to *limit* most recent messages, oldest first."""
    with conn.lock:
        rows = conn.conn.execute(
            "SELECT nickname, content, timestamp FROM messages"
            " ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return list(reversed(rows))
