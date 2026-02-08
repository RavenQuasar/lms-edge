#!/usr/bin/env python3
"""LMS-Edge Server"""

import http.server
import socketserver
import threading
import os
import json
import sqlite3
import time

PORT = 8080
PROJECT_DIR = '/home/raven/lms-edge/lms-edge/backend'
DATA_DIR = os.path.join(PROJECT_DIR, 'data')
STATIC_DIR = os.path.join(PROJECT_DIR, 'static')

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

DB_PATH = os.path.join(DATA_DIR, 'lms.db')
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name TEXT,
    role TEXT DEFAULT 'student',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
)
''')

users = [('admin', 'admin123', 'Administrator', 'admin'),
         ('teacher', 'teacher123', 'Teacher', 'teacher'),
         ('student', 'student123', 'Student', 'student')]

for username, password, full_name, role in users:
    cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
    if not cursor.fetchone():
        import hashlib
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        cursor.execute('INSERT INTO users VALUES (?, ?, ?, ?)', 
                     (username, password_hash, full_name, role))
        print(f"Created user: {username}")

conn.commit()

class LMSHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path in ['/', '/index.html']:
            self.path = '/index.html'
        
        if self.path == '/api/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"status": "healthy"}')
            return
        
        if self.path == '/api/info':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            users_count = cursor.execute('SELECT COUNT(*) FROM users').fetchone()[0]
            info = {"status": "running", "version": "1.0.0", "users": users_count, "port": PORT}
            self.wfile.write(json.dumps(info).encode())
            return
        
        if self.path == '/api/users':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            users = cursor.execute('SELECT username, full_name, role FROM users').fetchall()
            data = [{"username": u[0], "full_name": u[1], "role": u[2]} for u in users]
            self.wfile.write(json.dumps(data).encode())
            return
        
        return super().do_GET()

print(f"\n{'='*50}")
print(f"  LMS-Edge Server Started!")
print(f"{'='*50}")
print(f"  URL: http://localhost:{PORT}")
print(f"  API: http://localhost:{PORT}/api/info")
print(f"\n  Users:")
print(f"    admin / admin123")
print(f"    teacher / teacher123")
print(f"    student / student123")
print(f"{'='*50}\n")

httpd = socketserver.TCPServer(("", PORT), LMSHandler)
thread = threading.Thread(target=httpd.serve_forever)
thread.daemon = True
thread.start()

try:
    time.sleep(86400)
except KeyboardInterrupt:
    print("\nStopping server...")
    conn.close()
    httpd.shutdown()
    print("Server stopped")
