#!/usr/bin/env python3


import socket
import threading

def handle_client(client_socket):
    while True:
        msg = client_socket.recv(1024)
        if msg:
            print(msg.decode('utf-8'))
        else:
            break
    client_socket.close()

def server():
    host = '192.168.0.74'
    port = 65432

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen()

    print(f"Server listening on {host}:{port}")

    while True:
        client, address = server.accept()
        print(f"Connection from {address} has been established.")
        client_thread = threading.Thread(target=handle_client, args=(client,))
        client_thread.start()

if __name__ == "__main__":
    server()
