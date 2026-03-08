#!/usr/bin/env python3
"""Encrypted chat client with TLS, user authentication, and history display."""

import argparse
import getpass
import signal
import socket
import ssl
import sys
import threading
import time

BUFFER_SIZE = 4096


class ChatClient:
    def __init__(self):
        self.running = True
        self.nickname = ''
        self.client = None

    # ------------------------------------------------------------------
    # Connection
    # ------------------------------------------------------------------

    def connect(self, host, port, ca_cert=None):
        """
        Open a TLS connection to the server.

        ca_cert: path to the server's certificate for verification.
                 Omit to skip verification (self-signed certs without
                 distributing the cert file).
        """
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ctx.check_hostname = False
        if ca_cert:
            ctx.verify_mode = ssl.CERT_REQUIRED
            ctx.load_verify_locations(ca_cert)
        else:
            ctx.verify_mode = ssl.CERT_NONE

        raw = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.client = ctx.wrap_socket(raw, server_hostname=host)
            self.client.connect((host, port))
            return True
        except ConnectionRefusedError:
            print('Could not connect — is the server running?')
            return False
        except ssl.SSLError as e:
            print(f'TLS error: {e}')
            return False
        except socket.gaierror:
            print('Invalid host address.')
            return False

    # ------------------------------------------------------------------
    # Handshake
    # ------------------------------------------------------------------

    def _handshake(self):
        """
        Perform the authentication handshake matching the server protocol:
          S→C  NICK
          C→S  <nickname>
          S→C  PASSWORD:REGISTER  or  PASSWORD:LOGIN
          C→S  <password>
          S→C  AUTH:OK            or  ERROR:<reason>

        Returns True on success.
        """
        try:
            msg = self.client.recv(BUFFER_SIZE).decode('utf-8')
            if msg != 'NICK':
                print('Unexpected server response during handshake.')
                return False

            self.client.send(self.nickname.encode('utf-8'))

            prompt = self.client.recv(BUFFER_SIZE).decode('utf-8')
            if prompt == 'PASSWORD:REGISTER':
                print('New account — please choose a password.')
                while True:
                    password = getpass.getpass('Password: ')
                    confirm = getpass.getpass('Confirm password: ')
                    if password == confirm:
                        break
                    print('Passwords do not match. Try again.')
            elif prompt == 'PASSWORD:LOGIN':
                password = getpass.getpass('Password: ')
            else:
                print(f'Unexpected prompt from server: {prompt}')
                return False

            self.client.send(password.encode('utf-8'))

            response = self.client.recv(BUFFER_SIZE).decode('utf-8')
            if response.startswith('ERROR:'):
                print(f'Authentication failed: {response[6:]}')
                return False
            if response == 'AUTH:OK':
                return True

            print(f'Unexpected server response: {response}')
            return False

        except Exception as e:
            print(f'Handshake error: {e}')
            return False

    # ------------------------------------------------------------------
    # Threads
    # ------------------------------------------------------------------

    def receive(self):
        in_history = False
        while self.running:
            try:
                message = self.client.recv(BUFFER_SIZE).decode('utf-8')
                if not message:
                    print('\nLost connection to server.')
                    self.stop()
                    break

                if message.startswith('HISTORY:'):
                    tag = message[8:]
                    if tag == 'END':
                        in_history = False
                        print('--- end of history ---\n')
                    elif tag.isdigit():
                        in_history = True
                        print(f'\n--- last {tag} messages ---')
                    else:
                        # individual history line
                        print(message)
                elif message.startswith('OK:'):
                    print(message[3:])
                elif message.startswith('ERROR:'):
                    print(f'Server error: {message[6:]}')
                else:
                    print(message)

            except ConnectionResetError:
                print('\nServer closed the connection.')
                self.stop()
                break
            except Exception as e:
                if self.running:
                    print(f'\nReceive error: {e}')
                self.stop()
                break

    def write(self):
        while self.running:
            try:
                message = input()
                if message.lower() == '/quit':
                    self.stop()
                    break
                if message:
                    self.client.send(message.encode('utf-8'))
            except (EOFError, KeyboardInterrupt):
                self.stop()
                break
            except Exception as e:
                if self.running:
                    print(f'\nSend error: {e}')
                self.stop()
                break

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def stop(self):
        self.running = False
        try:
            self.client.shutdown(socket.SHUT_RDWR)
            self.client.close()
        except Exception:
            pass

    def start(self, host=None, port=None, nickname=None, ca_cert=None):
        print('Welcome to SimpleChat!')
        print('Commands: /quit\n')

        def signal_handler(sig, frame):
            print('\nDisconnecting...')
            self.stop()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)

        if host is None:
            host = input('Server IP (default: 127.0.0.1): ').strip() \
                   or '127.0.0.1'
        if port is None:
            while True:
                try:
                    port = int(
                        input('Port (default: 65432): ').strip() or '65432'
                    )
                    break
                except ValueError:
                    print('Invalid port. Try again.')
        if nickname is None:
            while True:
                nickname = input('Nickname: ').strip()
                if nickname:
                    break
                print('Nickname cannot be empty.')

        self.nickname = nickname

        print(f'\nConnecting to {host}:{port} (TLS)...')
        if not self.connect(host, port, ca_cert):
            return

        print('Connected. Authenticating...')
        if not self._handshake():
            self.stop()
            return

        threading.Thread(target=self.receive, daemon=True).start()
        threading.Thread(target=self.write, daemon=True).start()

        while self.running:
            time.sleep(0.1)


def main():
    parser = argparse.ArgumentParser(description='Encrypted chat client')
    parser.add_argument('--host', default=None,
                        help='Server IP address')
    parser.add_argument('--port', type=int, default=None,
                        help='Server port (default: 65432)')
    parser.add_argument('--nickname', default=None,
                        help='Your chat nickname')
    parser.add_argument('--ca-cert', default=None,
                        help='Server CA certificate for verification')
    args = parser.parse_args()

    ChatClient().start(args.host, args.port, args.nickname, args.ca_cert)


if __name__ == '__main__':
    main()
