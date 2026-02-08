#!/usr/bin/env python3
"""LMS-Edge Simple HTTP Server"""

import http.server
import socketserver
import os
import json

PORT = 8080
PROJECT_DIR = '/home/raven/lms-edge/lms-edge/backend'
STATIC_DIR = os.path.join(PROJECT_DIR, 'static')

os.makedirs(STATIC_DIR, exist_ok=True)

class LMSHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
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
            info = {"status": "running", "version": "1.0.0", "port": PORT}
            self.wfile.write(json.dumps(info).encode())
            return
        
        return super().do_GET()
    
    def log_message(self, format, *args):
        pass

if __name__ == '__main__':
    print(f"LMS-Edge Server running on port {PORT}")
    with socketserver.TCPServer(("", PORT), LMSHandler) as httpd:
        httpd.serve_forever()
