# Python Chat Application

A simple multi-threaded chat application with server and client components, allowing multiple users to connect and chat in real-time.

## Features

- Multi-threaded server supporting multiple simultaneous connections
- Nickname-based user identification
- Real-time message broadcasting
- Graceful connection handling and error recovery
- Background server operation support
- Clean shutdown handling

## Requirements

- Python 3.6 or higher
- macOS, Linux, or Windows operating system
- Network connectivity between server and clients

## Server Setup

### Running the Server

1. Clone the repository and navigate to the project directory
2. Run the server:
```bash
python3 server.py
```

### Running the Server in Background

#### Linux (systemd)

1. Create a system service file:
```bash
sudo nano /etc/systemd/system/chatserver.service
```

2. Add this configuration (adjust paths accordingly):
```ini
[Unit]
Description=Python Chat Server
After=network.target

[Service]
Type=simple
User=yourusername
ExecStart=/usr/bin/python3 /path/to/your/server.py
Restart=always
RestartSec=3
StandardOutput=append:/var/log/chatserver.log
StandardError=append:/var/log/chatserver.error.log

[Install]
WantedBy=multi-user.target
```

3. Enable and start the service:
```bash
# Reload systemd to recognize the new service
sudo systemctl daemon-reload

# Enable the service to start on boot
sudo systemctl enable chatserver

# Start the service
sudo systemctl start chatserver

# Check status
sudo systemctl status chatserver

# View logs
journalctl -u chatserver
```

4. Common systemd commands:
```bash
# Stop the service
sudo systemctl stop chatserver

# Restart the service
sudo systemctl restart chatserver

# Disable autostart
sudo systemctl disable chatserver
```

#### macOS (Launch Agent)

#### Using Screen (Available on both Linux and macOS)
```bash
# Install screen if needed
# For Arch Linux:
sudo pacman -S screen

# Start a new screen session
screen -S chat_server

# Run the server
python3 server.py

# Detach from screen (press Ctrl-A, then D)

# To reattach later:
screen -r chat_server
```

#### Using nohup
```bash
nohup python3 server.py > chat_server.log 2>&1 &
```

#### Using Launch Agent (Recommended for production)

1. Create a Launch Agent configuration:
```bash
nano ~/Library/LaunchAgents/com.user.chatserver.plist
```

2. Add this configuration (adjust paths accordingly):
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.user.chatserver</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/path/to/your/server.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/chatserver.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/chatserver.error.log</string>
</dict>
</plist>
```

3. Load the Launch Agent:
```bash
launchctl load ~/Library/LaunchAgents/com.user.chatserver.plist
```

## Client Setup

1. Run the client:
```bash
python3 client.py
```

2. Enter the requested information:
   - Server IP address (defaults to 192.168.0.74)
   - Port number (defaults to 65432)
   - Your nickname

## Client Commands

- `/quit` - Exit the chat
- Ctrl+C - Force quit the application

## Troubleshooting

### Server Issues
- Ensure the server IP address is correct and accessible
- Check if the port is available and not blocked by firewall
- Verify the server is running using `ps aux | grep server.py`
- Check server logs for errors

### Client Issues
- Confirm the server is running and accessible
- Verify the correct IP address and port
- Check network connectivity between client and server
- Ensure Python 3 is installed and working correctly

## Development

### Server Architecture
- Multi-threaded design using Python's threading module
- Socket-based communication
- Broadcast message handling
- Client connection management
- Signal handling for clean shutdown

### Client Architecture
- Separate threads for sending and receiving messages
- Error handling and recovery
- Clean shutdown support
- User-friendly interface

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.