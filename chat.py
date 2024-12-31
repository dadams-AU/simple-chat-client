#!/usr/bin/env python3

import socket
import threading
import signal
import sys
import time

class ChatClient:
    def __init__(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.running = True
        
    def connect(self, host, port):
        try:
            self.client.connect((host, port))
            return True
        except ConnectionRefusedError:
            print("Could not connect to server. Is it running?")
            return False
        except socket.gaierror:
            print("Invalid host address")
            return False
    
    def receive(self):
        while self.running:
            try:
                message = self.client.recv(1024).decode('utf-8')
                if message == 'NICK':
                    self.client.send(self.nickname.encode('utf-8'))
                elif message:
                    print(message)
                else:
                    print("\nLost connection to server")
                    self.stop()
                    break
            except ConnectionResetError:
                print("\nServer closed the connection")
                self.stop()
                break
            except Exception as e:
                if self.running:
                    print(f"\nError receiving message: {e}")
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
                    self.client.send(f"{self.nickname}: {message}".encode('utf-8'))
            except (EOFError, KeyboardInterrupt):
                self.stop()
                break
            except Exception as e:
                if self.running:
                    print(f"\nError sending message: {e}")
                self.stop()
                break

    def stop(self):
        self.running = False
        try:
            self.client.shutdown(socket.SHUT_RDWR)
            self.client.close()
        except:
            pass
        
    def start(self):
        print("Welcome to the Chat Client!")
        print("Available commands:")
        print("  /quit - Exit the chat")
        
        # Setup signal handler for graceful shutdown
        def signal_handler(sig, frame):
            print("\nDisconnecting...")
            self.stop()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        
        while True:
            host = input("Enter server IP (default: 192.168.0.74): ").strip() or "192.168.0.74"
            try:
                port = int(input("Enter port (default: 65432): ").strip() or "65432")
                break
            except ValueError:
                print("Invalid port number. Please try again.")
        
        self.nickname = input("Choose your nickname: ").strip()
        while not self.nickname:
            print("Nickname cannot be empty!")
            self.nickname = input("Choose your nickname: ").strip()
            
        print(f"\nConnecting to {host}:{port}...")
        if not self.connect(host, port):
            return
        
        print("Connected to server!")
        
        receive_thread = threading.Thread(target=self.receive)
        receive_thread.daemon = True
        receive_thread.start()
        
        write_thread = threading.Thread(target=self.write)
        write_thread.daemon = True
        write_thread.start()
        
        # Keep main thread alive until client stops
        while self.running:
            time.sleep(0.1)

if __name__ == "__main__":
    client = ChatClient()
    client.start()