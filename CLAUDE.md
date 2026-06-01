# CLAUDE.md — AI Assistant Guide for simple-chat-client

## Project Overview

`simple-chat-client` is a lightweight, pure-Python TCP chat application with **TLS encryption**, **password-authenticated user accounts**, and **persistent message history**.

It consists of a `simplechat` package plus two backwards-compat shim scripts:

| File | Purpose |
|---|---|
| `simplechat/server.py` | Multi-threaded TLS chat server |
| `simplechat/client.py` | Interactive TLS chat client |
| `simplechat/db.py` | SQLite persistence (users + messages) |
| `simplechat/protocol.py` | Length-prefixed socket framing |
| `simplechat/validation.py` | Shared nickname/message validation |
| `simplechat/__init__.py` | Package version |
| `server.py` | Shim → `simplechat.server:main` |
| `chat.py` | Shim → `simplechat.client:main` |
| `generate_cert.py` | One-time self-signed cert generator |
| `packaging/systemd/` | User and system service unit files |
| `pyproject.toml` | pip install config |

**No external dependencies.** Only Python standard library modules are used.

**Python requirement:** 3.8+

---

## Repository Structure

```
simple-chat-client/
├── simplechat/
│   ├── __init__.py      # version = "0.2.0"
│   ├── server.py        # ChatServer class + main()
│   ├── client.py        # ChatClient class + main()
│   ├── db.py            # SQLite helpers
│   ├── protocol.py      # Length-prefixed socket framing
│   └── validation.py    # Shared input validation
├── server.py            # Shim (backwards compat)
├── chat.py              # Shim (backwards compat)
├── generate_cert.py     # Cert generator (uses subprocess + openssl)
├── packaging/
│   └── systemd/         # User and system service units
├── pyproject.toml       # pip install / console scripts
├── tests/               # unittest coverage
├── README.md
├── LICENSE              # MIT (David P. Adams, 2025)
└── docs/
    └── background.md    # Persistent server deployment guide
```

---

## Running the Application

### First-time server setup (one time)
```bash
python generate_cert.py       # creates cert.pem + key.pem
python generate_cert.py --san 192.168.0.103
```

### Start the server
```bash
python server.py              # direct
chat-server                   # after pip install .
chat-server --port 65432 --db chat.db --cert cert.pem --key key.pem
```

### Start the client
```bash
python chat.py                # direct (interactive prompts)
chat-client                   # after pip install .
chat-client --host 192.168.0.103 --nickname Alice --ca-cert cert.pem
```

First connect with a nickname = **registration** (choose a password).
Subsequent connects = **login** (enter password).

### Client commands
- `/quit` — Graceful disconnect
- `Ctrl+C` — Force exit

---

## Architecture & Design

### Protocol (v2)

```
S→C  NICK
C→S  <nickname>
S→C  PASSWORD:REGISTER   (new user)
  or PASSWORD:LOGIN       (returning user)
C→S  <password>
S→C  AUTH:OK
  or ERROR:<reason>       (closes connection on error)

-- auth succeeded --

S→C  HISTORY:<n>          (omitted if no history)
S→C  [HH:MM] nick: text   (n times)
S→C  HISTORY:END
S→C  OK:Welcome, <nickname>!
S→C  <nickname> joined the chat!   (broadcast to others)

-- chat loop --

C→S  <message text>
S→C  <nickname>: <message text>    (broadcast to all)

-- on disconnect --

S→C  <nickname> left the chat!    (broadcast to others)
```

Each protocol item is a UTF-8 string sent through `simplechat.protocol` as a 4-byte big-endian length followed by payload bytes. Frames are capped at 64 KiB. Chat messages are capped at 2,000 characters, and nicknames at 32 characters.

### Encryption
TLS via `ssl.SSLContext`. Server loads a certificate + private key and requires TLS 1.2+. Clients skip certificate verification by default for quick local/private testing. Pass `--ca-cert cert.pem` to verify the certificate and hostname. Use `--no-check-hostname` only when explicitly accepting certificate trust without hostname matching.

### Authentication & Passwords
- Passwords stored as PBKDF2-HMAC-SHA256 with a 16-byte random salt, 100,000 iterations.
- Implemented in `db.py:_hash_password` / `_verify_password`.
- Registration is automatic on first connect with a new nickname.

### Persistence
- SQLite database (`chat.db` by default) via a thread-safe `ChatDatabase` wrapper in `simplechat/db.py`.
- Two tables: `users` (nickname, password_hash, salt, created_at) and `messages` (id, nickname, content, timestamp).
- Last 50 messages are replayed to new clients on join.
- `SERVER` is used as the nickname for system messages (join/leave events).

### Threading Model
- **Server:** One daemon thread per connected client (`handle_client`). Client list protected by `threading.Lock()`.
- **Client:** Two daemon threads — `receive` and `write`. Main thread polls `self.running` every 0.1s.

### Key Classes

#### `ChatServer` (`simplechat/server.py`)
| Method | Purpose |
|---|---|
| `__init__(host, port, cert, key, db_path)` | Configure TLS socket, lock, database |
| `_send(client, message)` | Send one framed string to one client |
| `broadcast(message, exclude)` | Send to all clients except `exclude` |
| `_handshake(client)` | NICK + PASSWORD exchange; returns nickname or None |
| `_send_history(client)` | Replay recent messages from DB |
| `handle_client(client, address)` | Full per-client lifecycle (threaded) |
| `_remove_client(client, nickname)` | Thread-safe disconnect + broadcast |
| `start()` | Bind, listen, accept loop; SIGINT-safe |

#### `ChatClient` (`simplechat/client.py`)
| Method | Purpose |
|---|---|
| `__init__()` | Initialize state |
| `connect(host, port, ca_cert, check_hostname)` | Open TLS connection |
| `_handshake()` | Auth protocol; handles REGISTER vs LOGIN prompts |
| `receive()` | Daemon thread: reads server messages, handles HISTORY/OK/ERROR tags |
| `write()` | Daemon thread: reads stdin, sends messages |
| `stop()` | Shutdown socket + set running=False |
| `start(host, port, nickname, ca_cert, check_hostname)` | Prompt user, connect, authenticate, launch threads |

#### Database (`simplechat/db.py`)
| Function | Purpose |
|---|---|
| `init_db(path)` | Open/create SQLite DB, ensure tables exist |
| `user_exists(conn, nickname)` | Check if nickname is registered |
| `register_user(conn, nickname, password)` | Hash + store new user |
| `authenticate_user(conn, nickname, password)` | Verify credentials |
| `save_message(conn, nickname, content)` | Persist a message |
| `get_recent_messages(conn, limit)` | Fetch last N messages, oldest-first |

#### Protocol (`simplechat/protocol.py`)
| Function | Purpose |
|---|---|
| `send_frame(sock, message)` | Send one length-prefixed UTF-8 frame with `sendall()` |
| `recv_frame(sock)` | Receive exactly one frame or `None` on clean EOF |

---

## Code Conventions

### Naming
- **Classes:** PascalCase (`ChatServer`, `ChatClient`)
- **Methods and variables:** `snake_case`
- **"Private" helpers:** prefixed with `_` (`_handshake`, `_send`, `_remove_client`)
- **Constants:** Module-level uppercase (`HISTORY_LIMIT`, `MAX_FRAME_BYTES`)

### Error Handling
- Use `except Exception:` (never bare `except:`).
- Use specific exceptions (`ConnectionRefusedError`, `ssl.SSLError`, `socket.gaierror`) at system boundaries.
- Internal helpers that swallow errors (e.g. `_send`) should use `except Exception: pass` and be clearly scoped.

### Socket Configuration
- Server: `SO_REUSEADDR` for quick rebind after restart.
- Client: `socket.shutdown(socket.SHUT_RDWR)` before `close()` in `stop()`.
- Application messages must go through `send_frame()` and `recv_frame()`.

### Thread Safety
- `ChatServer.clients` (list of `(socket, nickname)` tuples) is always accessed under `self._lock`.
- `_remove_client` rebuilds the list rather than calling `.remove()` to avoid index drift.

### Signal Handling
Both `server.py` and `client.py` register `SIGINT` handlers for graceful shutdown.

---

## Development Workflow

### Install for development
```bash
pip install -e .
```

### No build step required
Plain Python — no compilation or transpilation.

### Tests
```bash
python -m unittest discover -v
python -m compileall -q .
```

Use stdlib `unittest`; keep the project dependency-free.

### Formatting
No linter configured. Follow PEP 8:
- 4 spaces for indentation (no tabs)
- Lines ≤ 79 characters
- Blank lines between methods and top-level definitions

### Branching
- Primary development branch: `master`
- Feature branches: `feature/<short-description>`
- Claude AI branches: `claude/<task-id>`

---

## Key Defaults & Configuration

| Setting | Value | Location |
|---|---|---|
| Server bind host | `0.0.0.0` | `simplechat/server.py:main` |
| Default port | `65432` | `simplechat/server.py:main`, `simplechat/client.py:start` |
| Default client IP | `127.0.0.1` | `simplechat/client.py:start` |
| TLS certificate | `cert.pem` | `simplechat/server.py:main` |
| TLS private key | `key.pem` | `simplechat/server.py:main` |
| SQLite database | `chat.db` | `simplechat/server.py:main` |
| Frame size limit | `64 KiB` | `MAX_FRAME_BYTES` in `simplechat/protocol.py` |
| Message length limit | `2,000` characters | `MAX_MESSAGE_CHARS` in `simplechat/validation.py` |
| Nickname length limit | `32` characters | `MAX_NICKNAME_CHARS` in `simplechat/validation.py` |
| Message encoding | `utf-8` | throughout |
| History replay limit | `50` messages | `HISTORY_LIMIT` in server.py |
| Password KDF | PBKDF2-HMAC-SHA256, 100k iterations | `simplechat/db.py` |
| Nickname protocol token | `NICK` | server + client handshake |

---

## What This Project Does NOT Have

- **No external dependencies** — do not add third-party libraries without discussion.
- **No end-to-end encryption** — server decrypts messages to broadcast; TLS is transport-layer only.
- **No message rooms/channels** — single global chat only.
- **No admin commands** — no kick/ban/mute.
- **No rate limiting or abuse protection**.
- **No CI/CD** — no GitHub Actions configured.

---

## Deployment

For running the server persistently in the background, see [`docs/background.md`](docs/background.md), which covers:
- `screen` (session management)
- `nohup` (background process with log file)
- `systemd` (Linux service with auto-restart)
- `launchctl` (macOS Launch Agent)

---

## License

MIT License — Copyright (c) 2025 David P. Adams.
