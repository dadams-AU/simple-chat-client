#!/usr/bin/env python3
"""Encrypted multi-user chat server with TLS, authentication, and persistence."""

import argparse
import os
import signal
import socket
import ssl
import sys
import threading
import time

from .db import (
    authenticate_user,
    get_recent_messages,
    init_db,
    register_user,
    save_message,
    user_exists,
)

BUFFER_SIZE = 4096
HISTORY_LIMIT = 50


class ChatServer:
    def __init__(self, host='0.0.0.0', port=65432,
                 cert='cert.pem', key='key.pem', db_path='chat.db'):
        self.host = host
        self.port = port

        # Thread-safe client list: [(ssl_socket, nickname), ...]
        self._lock = threading.Lock()
        self.clients = []

        # Persistence
        self.db = init_db(db_path)

        # TLS
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.load_cert_chain(cert, key)

        raw = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        raw.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server = ctx.wrap_socket(raw, server_side=True)

    # ------------------------------------------------------------------
    # Messaging helpers
    # ------------------------------------------------------------------

    def _send(self, client, message):
        try:
            client.send(message.encode('utf-8'))
        except Exception:
            pass

    def broadcast(self, message, exclude=None):
        with self._lock:
            targets = list(self.clients)
        for client, _ in targets:
            if client is not exclude:
                self._send(client, message)

    # ------------------------------------------------------------------
    # Connection handshake
    # ------------------------------------------------------------------

    def _handshake(self, client):
        """
        Authenticate or register an incoming client.
        Protocol:
          S→C  NICK
          C→S  <nickname>
          S→C  PASSWORD:REGISTER  or  PASSWORD:LOGIN
          C→S  <password>
          S→C  AUTH:OK            or  ERROR:<reason>

        Returns the authenticated nickname on success, None on failure.
        """
        try:
            self._send(client, 'NICK')
            nickname = client.recv(BUFFER_SIZE).decode('utf-8').strip()
            if not nickname:
                return None

            exists = user_exists(self.db, nickname)
            self._send(client, 'PASSWORD:LOGIN' if exists else 'PASSWORD:REGISTER')
            password = client.recv(BUFFER_SIZE).decode('utf-8').strip()
            if not password:
                return None

            if exists:
                if not authenticate_user(self.db, nickname, password):
                    self._send(client, 'ERROR:Invalid password')
                    return None
            else:
                if not register_user(self.db, nickname, password):
                    self._send(client, 'ERROR:Nickname already taken')
                    return None

            self._send(client, 'AUTH:OK')
            return nickname

        except Exception:
            return None

    # ------------------------------------------------------------------
    # Per-client thread
    # ------------------------------------------------------------------

    def _send_history(self, client):
        messages = get_recent_messages(self.db, HISTORY_LIMIT)
        if not messages:
            return
        self._send(client, f'HISTORY:{len(messages)}')
        for nick, content, ts in messages:
            stamp = time.strftime('%H:%M', time.localtime(ts))
            self._send(client, f'[{stamp}] {nick}: {content}')
        self._send(client, 'HISTORY:END')

    def handle_client(self, client, address):
        nickname = self._handshake(client)
        if not nickname:
            client.close()
            return

        with self._lock:
            self.clients.append((client, nickname))

        print(f'[+] {nickname} connected from {address}')
        self._send_history(client)
        self._send(client, f'OK:Welcome, {nickname}!')
        self.broadcast(f'{nickname} joined the chat!', exclude=client)
        save_message(self.db, 'SERVER', f'{nickname} joined the chat!')

        while True:
            try:
                data = client.recv(BUFFER_SIZE)
                if not data:
                    break
                message = data.decode('utf-8').strip()
                if message:
                    formatted = f'{nickname}: {message}'
                    self.broadcast(formatted)
                    save_message(self.db, nickname, message)
            except Exception:
                break

        self._remove_client(client, nickname)

    def _remove_client(self, client, nickname):
        with self._lock:
            self.clients = [(c, n) for c, n in self.clients if c is not client]
        try:
            client.close()
        except Exception:
            pass
        msg = f'{nickname} left the chat!'
        print(f'[-] {msg}')
        self.broadcast(msg)
        save_message(self.db, 'SERVER', msg)

    # ------------------------------------------------------------------
    # Main accept loop
    # ------------------------------------------------------------------

    def start(self):
        self.server.bind((self.host, self.port))
        self.server.listen()
        print(f'Server listening on {self.host}:{self.port} (TLS)')

        def signal_handler(sig, frame):
            print('\nShutting down server...')
            with self._lock:
                for client, _ in self.clients:
                    try:
                        client.close()
                    except Exception:
                        pass
            self.server.close()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)

        while True:
            try:
                client, address = self.server.accept()
                thread = threading.Thread(
                    target=self.handle_client,
                    args=(client, address),
                    daemon=True,
                )
                thread.start()
            except Exception as e:
                print(f'Accept error: {e}')
                break


def main():
    parser = argparse.ArgumentParser(description='Encrypted chat server')
    parser.add_argument('--host', default='0.0.0.0',
                        help='Bind address (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=65432,
                        help='Port (default: 65432)')
    parser.add_argument('--cert', default='cert.pem',
                        help='TLS certificate file (default: cert.pem)')
    parser.add_argument('--key', default='key.pem',
                        help='TLS private key file (default: key.pem)')
    parser.add_argument('--db', default='chat.db',
                        help='SQLite database path (default: chat.db)')
    args = parser.parse_args()

    for path in (args.cert, args.key):
        if not os.path.exists(path):
            print(f"Missing TLS file: {path}")
            print("Run:  python generate_cert.py")
            sys.exit(1)

    ChatServer(args.host, args.port, args.cert, args.key, args.db).start()


if __name__ == '__main__':
    main()
