# CLAUDE.md — AI Assistant Guide for simple-chat-client

## Project Overview

`simple-chat-client` is a lightweight, pure-Python TCP chat application. It consists of two standalone scripts:

- **`server.py`** — Multi-threaded chat server that accepts connections and broadcasts messages to all clients.
- **`chat.py`** — Interactive chat client that connects to the server and enables real-time messaging.

**No external dependencies.** Only Python standard library modules are used (`socket`, `threading`, `signal`, `sys`, `time`).

**Python requirement:** 3.6+

---

## Repository Structure

```
simple-chat-client/
├── chat.py          # Chat client (118 lines)
├── server.py        # Chat server (81 lines)
├── README.md        # User-facing documentation
├── LICENSE          # MIT License (David P. Adams, 2025)
└── docs/
    └── background.md  # Guide for running server persistently (screen, nohup, systemd, launchctl)
```

---

## Running the Application

### Start the server
```bash
python server.py
```
Listens on `0.0.0.0:65432` by default.

### Start the client
```bash
python chat.py
```
Prompts for:
1. Server IP (default: `192.168.0.103`)
2. Port (default: `65432`)
3. Nickname

### Client commands
- `/quit` — Gracefully disconnect
- `Ctrl+C` — Force exit

---

## Architecture & Design

### Protocol
A simple, text-based TCP protocol:

1. Client connects.
2. Server sends the literal string `NICK`.
3. Client responds with its chosen nickname.
4. Server broadcasts `"<nickname> joined the chat!"`.
5. All subsequent messages from the client are broadcast as-is to all connected clients.
6. On disconnect, server broadcasts `"<nickname> left the chat!"`.

### Message Format
Messages are sent and received as UTF-8 encoded strings, up to 1024 bytes per message:
```
"nickname: message text"
```
The client formats messages before sending; the server broadcasts them verbatim.

### Threading Model
- **Server:** One thread per connected client (`handle_client` method).
- **Client:** Two daemon threads — `receive` (listens for server messages) and `write` (reads stdin and sends).

### Key Classes

#### `ChatServer` (`server.py`)
| Method | Purpose |
|---|---|
| `__init__(host, port)` | Configure socket and data structures |
| `broadcast(message)` | Send UTF-8 message to all clients |
| `handle_client(client)` | Per-client receive/broadcast loop (threaded) |
| `remove_client(client)` | Disconnect a client, notify others |
| `start()` | Accept connections; SIGINT-safe shutdown |

#### `ChatClient` (`chat.py`)
| Method | Purpose |
|---|---|
| `__init__()` | Initialize socket and state |
| `connect(host, port)` | Establish TCP connection |
| `receive()` | Daemon thread: reads from server, handles NICK handshake |
| `write()` | Daemon thread: reads stdin, sends messages |
| `stop()` | Shut down socket and threads |
| `start()` | Prompt user, launch threads |

---

## Code Conventions

### Naming
- **Classes:** PascalCase (`ChatServer`, `ChatClient`)
- **Methods and variables:** `snake_case`
- **Constants:** Inline hardcoded values (no separate constants file)

### Socket Configuration
- Server enables `SO_REUSEADDR` to allow quick rebinding after restart.
- Client uses `socket.shutdown(socket.SHUT_RDWR)` before `close()` for a proper TCP FIN sequence.

### Signal Handling
Both `server.py` and `chat.py` register a `SIGINT` handler to enable graceful shutdown on `Ctrl+C`.

### Error Handling (Known Limitations)
The codebase uses broad `except:` clauses in several places, which catch all exceptions including `SystemExit` and `KeyboardInterrupt`. This is a known Python anti-pattern. Prefer `except Exception:` or specific exception types when making changes.

---

## Development Workflow

### No build step required
The project is two plain Python scripts. There is no compilation, packaging, or dependency installation needed.

### No test suite
There are currently no automated tests. When adding tests, use `pytest` and follow the standard naming convention:
- Test files: `test_<module>.py`
- Test functions: `test_<description>()`

### Formatting
No linter or formatter is configured. Follow PEP 8:
- 4 spaces for indentation (no tabs)
- Lines ≤ 79 characters
- Blank lines between methods and between top-level definitions

### Branching
- Primary development branch: `master`
- Feature branches should follow: `feature/<short-description>`
- Claude AI branches follow: `claude/<task-id>`

---

## Key Defaults & Configuration

| Setting | Value | Location |
|---|---|---|
| Server bind host | `0.0.0.0` | `server.py:__init__` |
| Default port | `65432` | `server.py:__init__`, `chat.py:start` |
| Default client IP | `192.168.0.103` | `chat.py:start` |
| Message buffer size | `1024` bytes | `chat.py:receive`, `server.py:handle_client` |
| Message encoding | `utf-8` | throughout |
| Nickname protocol token | `NICK` | `server.py:handle_client`, `chat.py:receive` |

---

## What This Project Does NOT Have

Be aware of these absent features before suggesting or adding them:

- **No external dependencies** — do not add third-party libraries without discussion.
- **No authentication or encryption** — the protocol is plaintext over TCP.
- **No message persistence** — messages exist only in-memory during the session.
- **No message history** — new clients see no prior messages.
- **No tests** — adding `pytest` tests is welcome but not yet set up.
- **No CI/CD** — no GitHub Actions or other pipelines configured.
- **No packaging** — no `setup.py`, `pyproject.toml`, or `requirements.txt`.

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
