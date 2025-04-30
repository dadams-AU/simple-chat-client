# Python Chat Application

A simple multi-threaded Python chat app with server and client components that lets multiple users connect and chat in real time.

## Features

- Multi-user support
- Nickname-based identification
- Real-time message broadcasting
- Graceful connection handling

## Requirements

- Python 3.6+
- Works on macOS, Linux, and Windows
- Clients and server must be on the same network

## Getting Started

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/python-chat
cd python-chat
```

### 2. Start the Server
```bash
python3 server.py
```

### 3. Start a Client
In a separate terminal or on another device:
```bash
python3 chat.py
```

You'll be prompted for:
- Server IP address (default: `192.168.0.103`)
- Port (default: `65432`)
- Nickname

## Client Commands

- `/quit` – Leave the chat
- `Ctrl+C` – Force quit

## Troubleshooting

**Server**
- Make sure the server is running and reachable
- Ensure the chosen port is open and not blocked by a firewall
- Check logs or run `ps aux | grep server.py`

**Client**
- Double-check the server’s IP and port
- Verify network access between client and server
- Ensure Python 3 is installed and functional

## Running the Server in the Background (Optional)

For Linux/macOS users wanting to run the server persistently (e.g. on a VPS or Raspberry Pi), see [`docs/background.md`](docs/background.md) for options like `screen`, `nohup`, `systemd`, and `launchctl`.

## Contributing

1. Fork the repository
2. Create your branch: `git checkout -b feature/AmazingFeature`
3. Commit your changes: `git commit -m 'Add some AmazingFeature'`
4. Push to the branch: `git push origin feature/AmazingFeature`
5. Open a Pull Request

## License

MIT — see the [LICENSE](LICENSE) file for details.
