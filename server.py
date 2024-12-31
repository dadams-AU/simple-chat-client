#!/usr/bin/env python3

import socket
import threading
import signal
import sys

class ChatServer:
    def __init__(self, host='0.0.0.0', port=65432):
        self.host = host
        self.port = port
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.clients = []
        self.nicknames = []
        
    def broadcast(self, message):
        for client in self.clients:
            try:
                client.send(message)
            except:
                self.remove_client(client)

    def handle_client(self, client):
        while True:
            try:
                message = client.recv(1024)
                if message:
                    self.broadcast(message)
                else:
                    self.remove_client(client)
                    break
            except:
                self.remove_client(client)
                break

    def remove_client(self, client):
        if client in self.clients:
            index = self.clients.index(client)
            self.clients.remove(client)
            client.close()
            nickname = self.nicknames[index]
            self.broadcast(f'{nickname} left the chat!'.encode('utf-8'))
            self.nicknames.remove(nickname)

    def start(self):
        self.server.bind((self.host, self.port))
        self.server.listen()
        print(f"Server running on {self.host}:{self.port}")
        
        def signal_handler(sig, frame):
            print("\nShutting down server...")
            for client in self.clients:
                client.close()
            self.server.close()
            sys.exit(0)
            
        signal.signal(signal.SIGINT, signal_handler)
        
        while True:
            try:
                client, address = self.server.accept()
                print(f"Connected with {str(address)}")
                
                client.send('NICK'.encode('utf-8'))
                nickname = client.recv(1024).decode('utf-8')
                self.nicknames.append(nickname)
                self.clients.append(client)
                
                print(f"Nickname of the client is {nickname}")
                self.broadcast(f"{nickname} joined the chat!".encode('utf-8'))
                client.send("Connected to the server!".encode('utf-8'))
                
                thread = threading.Thread(target=self.handle_client, args=(client,))
                thread.start()
            except Exception as e:
                print(f"Error: {e}")
                break

if __name__ == "__main__":
    server = ChatServer()
    server.start()