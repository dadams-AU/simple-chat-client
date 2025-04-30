# Running the Chat Server in the Background

This guide provides optional methods to run `server.py` in the background on various systems.

---

## Linux / macOS

### **Option 1: `screen`**
```bash
# Install screen if needed
sudo apt install screen         # Debian/Ubuntu
sudo pacman -S screen           # Arch
brew install screen             # macOS

# Start a new screen session
screen -S chat_server

# Run the server
python3 server.py

# Detach (Ctrl+A, then D), reattach with:
screen -r chat_server
```

---

### **Option 2: `nohup`**
```bash
nohup python3 server.py > chat_server.log 2>&1 &
```
Logs output to `chat_server.log`.

---

### **Option 3: `systemd`** (Linux)

1. Create a service file:
```bash
sudo nano /etc/systemd/system/chatserver.service
```

2. Add:
```ini
[Unit]
Description=Python Chat Server
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /path/to/server.py
Restart=always
RestartSec=3
StandardOutput=append:/var/log/chatserver.log
StandardError=append:/var/log/chatserver.err

[Install]
WantedBy=multi-user.target
```

3. Reload and enable:
```bash
sudo systemctl daemon-reload
sudo systemctl enable chatserver
sudo systemctl start chatserver
```

4. View logs:
```bash
journalctl -u chatserver
```

---

## macOS

### **Option: Launch Agent**

1. Create:
```bash
nano ~/Library/LaunchAgents/com.user.chatserver.plist
```

2. Paste:
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
    <string>/path/to/server.py</string>
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

3. Load it:
```bash
launchctl load ~/Library/LaunchAgents/com.user.chatserver.plist
```

---

These methods are for advanced users. For basic use, just run:
```bash
python3 server.py
```
