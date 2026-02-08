#!/usr/bin/env python3
"""Simple Web Server"""
import socket

HOST = ''  # 所有接口
PORT = 9999

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind((HOST, PORT))
sock.listen(1)
print(f"Server started on port {PORT}")

while True:
    conn, addr = sock.accept()
    print(f'Connection from {addr}')
    data = conn.recv(1024)
    if not data:
        break
    
    response = b'HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n<h1>LMS-Edge Server</h1><p>Port 9999 working!</p>'
    conn.sendall(response)
    conn.close()
