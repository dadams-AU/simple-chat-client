# Python Chat Application

A simple multi-threaded Python chat app with server and client components, featuring **TLS encryption**, **user accounts with password authentication**, and **persistent message history**.

## Features

- End-to-end TLS encryption (stdlib `ssl` module, no external dependencies)
- User accounts with password hashing (PBKDF2-HMAC-SHA256 via `hashlib`)
- Message history replayed on join (SQLite via `sqlite3`)
- Multi-user support with nicknames
- Real-time message broadcasting
- Graceful connection and shutdown handling

## Requirements

- Python 3.8+
- OpenSSL (for generating the server certificate — usually pre-installed)
- Works on macOS, Linux, and Windows
- Clients and server must be reachable over the network

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/simple-chat-client
cd simple-chat-client
```

### 2. (Optional) Install as a package

```bash
pip install .
```

This installs `chat-server` and `chat-client` console scripts.

### 3. Generate a TLS certificate (server side, one time)

```bash
python generate_cert.py
```

This creates `cert.pem` and `key.pem` in the current directory.
**Keep `key.pem` private.** Distribute `cert.pem` to clients only if you want them to verify the server identity with `--ca-cert`.

### 4. Start the server

```bash
# Direct
python server.py

# After pip install
chat-server

# With options
chat-server --host 0.0.0.0 --port 65432 --cert cert.pem --key key.pem --db chat.db
```

### 5. Start a client

```bash
# Direct (interactive prompts)
python chat.py

# After pip install
chat-client

# With flags (skips prompts)
chat-client --host 192.168.0.103 --port 65432 --nickname Alice
```

On first connect, a new nickname triggers **registration** (choose a password).
On subsequent connects, the same nickname triggers **login** (enter your password).

## Client Commands

| Command | Action |
|---------|--------|
| `/quit` | Disconnect gracefully |
| `Ctrl+C` | Force quit |

## Server Options

| Flag | Default | Description |
|------|---------|-------------|
| `--host` | `0.0.0.0` | Bind address |
| `--port` | `65432` | TCP port |
| `--cert` | `cert.pem` | TLS certificate |
| `--key` | `key.pem` | TLS private key |
| `--db` | `chat.db` | SQLite database path |

## Client Options

| Flag | Default | Description |
|------|---------|-------------|
| `--host` | *(prompted)* | Server IP address |
| `--port` | *(prompted)* | Server port |
| `--nickname` | *(prompted)* | Your chat nickname |
| `--ca-cert` | *(none)* | Server cert for verification |

## Security Notes

- All traffic is TLS-encrypted.
- Passwords are never stored in plaintext — PBKDF2-HMAC-SHA256 with a random salt and 100,000 iterations.
- The default TLS configuration skips certificate verification on the client side (suitable for private networks with self-signed certs). Pass `--ca-cert cert.pem` to enforce server identity verification.
- This is **not** end-to-end encrypted — the server decrypts messages to broadcast them.

## File Overview

```
simple-chat-client/
├── simplechat/
│   ├── __init__.py    # Package metadata
│   ├── server.py      # ChatServer class + main()
│   ├── client.py      # ChatClient class + main()
│   └── db.py          # SQLite helpers (users, messages)
├── server.py          # Shim: python server.py still works
├── chat.py            # Shim: python chat.py still works
├── generate_cert.py   # One-time TLS cert generator
├── pyproject.toml     # pip install configuration
└── docs/
    └── background.md  # Running the server persistently
```

## Running the Server in the Background

For persistent deployment (VPS, Raspberry Pi, etc.) see [`docs/background.md`](docs/background.md), which covers `screen`, `nohup`, `systemd`, and `launchctl`.

## Contributing

1. Fork the repository
2. Create your branch: `git checkout -b feature/AmazingFeature`
3. Commit your changes: `git commit -m 'Add some AmazingFeature'`
4. Push to the branch: `git push origin feature/AmazingFeature`
5. Open a Pull Request

## License

MIT — see the [LICENSE](LICENSE) file for details.
