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

from .protocol import ProtocolError, recv_frame, send_frame
from .validation import message_error, nickname_error


class ChatClient:
    def __init__(self):
        self.running = True
        self.nickname = ''
        self.client = None

    # ------------------------------------------------------------------
    # Connection
    # ------------------------------------------------------------------

    def connect(self, host, port, ca_cert=None, check_hostname=True):
        """
        Open a TLS connection to the server.

        ca_cert: path to the server's certificate for verification.
                 Omit to skip verification (self-signed certs without
                 distributing the cert file).
        """
        if ca_cert:
            ctx = ssl.create_default_context(
                ssl.Purpose.SERVER_AUTH,
                cafile=ca_cert,
            )
            ctx.check_hostname = check_hostname
        else:
            ctx = ssl._create_unverified_context()
        ctx.minimum_version = ssl.TLSVersion.TLSv1_2

        raw = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.client = ctx.wrap_socket(raw, server_hostname=host)
            self.client.connect((host, port))
            return True
        except ConnectionRefusedError:
            print('Could not connect — is the server running?')
        except ssl.SSLError as e:
            print(f'TLS error: {e}')
        except socket.gaierror:
            print('Invalid host address.')
        except OSError as e:
            print(f'Connection error: {e}')
        try:
            if self.client is not None:
                self.client.close()
            else:
                raw.close()
        except Exception:
            pass
        self.client = None
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
            msg = recv_frame(self.client)
            if msg != 'NICK':
                print('Unexpected server response during handshake.')
                return False

            send_frame(self.client, self.nickname)

            prompt = recv_frame(self.client)
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
            elif prompt and prompt.startswith('ERROR:'):
                print(f'Authentication failed: {prompt[6:]}')
                return False
            else:
                print(f'Unexpected prompt from server: {prompt}')
                return False

            send_frame(self.client, password)

            response = recv_frame(self.client)
            if response is None:
                print('Server closed the connection during authentication.')
                return False
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
        while self.running:
            try:
                message = recv_frame(self.client)
                if message is None:
                    print('\nLost connection to server.')
                    self.stop()
                    break

                if message.startswith('HISTORY:'):
                    tag = message[8:]
                    if tag == 'END':
                        print('--- end of history ---\n')
                    elif tag.isdigit():
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
            except ProtocolError as e:
                print(f'\nProtocol error: {e}')
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
                    error = message_error(message)
                    if error:
                        print(error)
                        continue
                    send_frame(self.client, message)
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

    def start(self, host=None, port=None, nickname=None, ca_cert=None,
              check_hostname=True):
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
                error = nickname_error(nickname)
                if not error:
                    break
                print(error)
        else:
            error = nickname_error(nickname)
            if error:
                print(f'Invalid nickname: {error}')
                return

        self.nickname = nickname

        print(f'\nConnecting to {host}:{port} (TLS)...')
        if not self.connect(host, port, ca_cert, check_hostname):
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
    parser.add_argument('--no-check-hostname', action='store_true',
                        help='Disable hostname verification with --ca-cert')
    args = parser.parse_args()

    if args.no_check_hostname and not args.ca_cert:
        parser.error('--no-check-hostname requires --ca-cert')

    ChatClient().start(
        args.host,
        args.port,
        args.nickname,
        args.ca_cert,
        not args.no_check_hostname,
    )


if __name__ == '__main__':
    main()
