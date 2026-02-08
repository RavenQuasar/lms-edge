#!/usr/bin/env python3
"""
LMS-Edge Complete Server v3.0
Full-featured Classroom LAN Teaching Management System
"""

import http.server
import socketserver
import sqlite3
import json
import os
import hashlib
import time
import sys
from datetime import datetime
from urllib.parse import urlparse, parse_qs

def parse_args():
    port = 8080
    db_path = '/home/raven/lms-edge/backend/data/lms.db'
    static_dir = '/home/raven/lms-edge/backend/static'
    
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == '--port' and i + 1 < len(args):
            port = int(args[i + 1])
            i += 2
        elif args[i] == '--db' and i + 1 < len(args):
            db_path = args[i + 1]
            i += 2
        elif args[i] == '--static' and i + 1 < len(args):
            static_dir = args[i + 1]
            i += 2
        else:
            i += 1
    return port, db_path, static_dir

PORT, DB_PATH, STATIC_DIR = parse_args()

os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name TEXT,
    role TEXT DEFAULT 'student',
    avatar TEXT DEFAULT 'default.png',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    deleted INTEGER DEFAULT 0
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    content TEXT,
    assignment_type TEXT NOT NULL,
    options TEXT,
    correct_answer TEXT,
    points INTEGER DEFAULT 10,
    created_by INTEGER,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    deleted INTEGER DEFAULT 0
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS submissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    assignment_id INTEGER,
    student_answer TEXT,
    score REAL DEFAULT 0,
    is_correct INTEGER DEFAULT 0,
    submitted_at TEXT DEFAULT CURRENT_TIMESTAMP,
    deleted INTEGER DEFAULT 0)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS attendances (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    login_time TEXT DEFAULT CURRENT_TIMESTAMP,
    logout_time TEXT,
    activity_score REAL DEFAULT 0,
    session_duration INTEGER DEFAULT 0
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS operation_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    username TEXT,
    action TEXT,
    target TEXT,
    details TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
)
''')

default_users = [
    ('admin', hashlib.sha256('admin123'.encode()).hexdigest(), 'Administrator', 'admin'),
    ('teacher', hashlib.sha256('teacher123'.encode()).hexdigest(), 'Teacher', 'teacher'),
    ('student', hashlib.sha256('student123'.encode()).hexdigest(), 'Student', 'student'),
]

for username, pwd_hash, full_name, role in default_users:
    cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
    if not cursor.fetchone():
        cursor.execute('INSERT INTO users (username, password_hash, full_name, role) VALUES (?, ?, ?, ?)',
                      (username, pwd_hash, full_name, role))

conn.commit()

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def parse_json(body):
    try:
        return json.loads(body)
    except:
        return {}

def log_operation(cursor, user_id, username, action, target, details):
    cursor.execute('''INSERT INTO operation_logs (user_id, username, action, target, details) 
                     VALUES (?, ?, ?, ?, ?)''',
                     (user_id, username, action, target, details))

class LMSHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {args[0]}")
    
    def send_json(self, data, status=200):
        try:
            self.send_response(status)
            self.send_header('Content-Type', 'application/json')
            origin = self.headers.get('Origin', '*')
            self.send_header('Access-Control-Allow-Origin', origin)
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
            self.send_header('Access-Control-Max-Age', '86400')
            self.end_headers()
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode())
        except Exception as e:
            print(f"Error sending response: {e}")
    
    def do_OPTIONS(self):
        try:
            origin = self.headers.get('Origin', '*')
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', origin)
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
            self.send_header('Access-Control-Max-Age', '86400')
            self.end_headers()
        except Exception as e:
            print(f"Error in OPTIONS: {e}")
    
    def do_DELETE(self):
        path = urlparse(self.path).path
        parts = path.split('/')
        if len(parts) >= 4:
            resource = parts[2]
            resource_id = int(parts[3])
            if resource == 'users':
                self.delete_user(resource_id)
            elif resource == 'assignments':
                self.delete_assignment(resource_id)
            elif resource == 'submissions':
                self.delete_submission(resource_id)
            else:
                self.send_error(404, 'Not Found')
        else:
            self.send_error(404, 'Not Found')
    
    def do_PUT(self):
        try:
            path = urlparse(self.path).path
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length).decode() if length > 0 else '{}'
            data = parse_json(body)
            
            if path == '/api/users/':
                self.update_user(data)
            elif path == '/api/users/password':
                self.change_password(data)
            elif path.startswith('/api/assignments/') and len(path.split('/')) == 4:
                assignment_id = int(path.split('/')[3])
                self.update_assignment(assignment_id, data)
            else:
                self.send_error(404, 'Not Found')
        except Exception as e:
            print(f"Error in do_PUT: {e}")
            self.send_json({'error': str(e)}, status=500)
    
    def do_POST(self):
        try:
            path = urlparse(self.path).path
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length).decode() if length > 0 else '{}'
            data = parse_json(body)
            
            if path == '/api/auth/login':
                self.handle_login(data)
            elif path == '/api/users/create':
                self.create_user(data)
            elif path == '/api/assignments/create':
                self.handle_create_assignment(data)
            elif path == '/api/assignments/submit':
                self.handle_submit(data)
            elif path == '/api/attendance/auto':
                self.handle_auto_signin(data)
            elif path == '/api/logs':
                self.get_logs(data)
            else:
                self.send_error(404, 'Not Found')
        except Exception as e:
            print(f"Error in do_POST: {e}")
            self.send_json({'error': str(e)}, status=500)
    
    def do_GET(self):
        try:
            path = urlparse(self.path).path
            params = parse_qs(urlparse(path).query)
            
            if path == '/' or path == '/index.html':
                self.serve_index()
            elif path == '/api/health':
                self.send_json({'status': 'healthy', 'time': datetime.now().isoformat()})
            elif path == '/api/info':
                self.handle_info()
            elif path == '/api/users':
                self.handle_users()
            elif path.startswith('/api/users/') and len(path.split('/')) == 4:
                user_id = int(path.split('/')[3])
                self.get_user_detail(user_id)
            elif path == '/api/assignments':
                self.handle_assignments()
            elif path == '/api/assignments/all':
                self.handle_all_assignments()
            elif path.startswith('/api/assignments/') and len(path.split('/')) == 4:
                assignment_id = int(path.split('/')[3])
                self.get_assignment_detail(assignment_id)
            elif path == '/api/attendance/records':
                self.handle_attendance_records()
            elif path == '/api/stats/class':
                self.handle_class_stats()
            elif path == '/api/stats/my':
                self.handle_my_stats()
            elif path == '/api/submissions/my':
                self.handle_my_submissions()
            elif path == '/api/submissions/assignment':
                assignment_id = params.get('assignment_id', [0])[0]
                self.handle_submissions_by_assignment(int(assignment_id))
            elif path == '/api/logs':
                self.get_logs({})
            else:
                self.serve_static(path)
        except Exception as e:
            print(f"Error in do_GET: {e}")
            self.send_json({'error': str(e)}, status=500)
    
    def serve_index(self):
        index_file = os.path.join(STATIC_DIR, 'index.html')
        if os.path.exists(index_file):
            with open(index_file, 'rb') as f:
                content = f.read()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
        else:
            self.send_error(404, 'Not Found')
    
    def serve_static(self, path):
        if path.startswith('/static/') or path.startswith('/uploads/'):
            file_path = os.path.join(STATIC_DIR, path.replace('/static/', '').replace('/uploads/', ''))
            if os.path.exists(file_path) and os.path.isfile(file_path):
                with open(file_path, 'rb') as f:
                    content = f.read()
                self.send_response(200)
                self.end_headers()
                self.wfile.write(content)
                return
        self.send_error(404, 'Not Found')
    
    def handle_login(self, data):
        conn = get_db()
        user = conn.execute('SELECT * FROM users WHERE username = ? AND deleted = 0', (data.get('username',''),)).fetchone()
        
        if user:
            pwd_hash = hashlib.sha256(data.get('password','').encode()).hexdigest()
            if user['password_hash'] == pwd_hash:
                user_dict = dict(user)
                conn.close()
                
                conn = get_db()
                cursor = conn.cursor()
                log_operation(cursor, user['id'], user['username'], 'LOGIN', 'auth', '用户登录成功')
                conn.commit()
                conn.close()
                
                self.send_json({
                    'token': f'token_{user["id"]}_{int(time.time())}',
                    'user': {
                        'id': user_dict['id'],
                        'username': user_dict['username'],
                        'full_name': user_dict['full_name'],
                        'role': user_dict['role']
                    }
                })
                return
        self.send_json({'error': '用户名或密码错误'}, status=401)
    
    def handle_users(self):
        conn = get_db()
        users = conn.execute('SELECT id, username, full_name, role, created_at FROM users WHERE deleted = 0 ORDER BY id').fetchall()
        conn.close()
        self.send_json({'users': [dict(u) for u in users]})
    
    def get_user_detail(self, user_id):
        conn = get_db()
        user = conn.execute('SELECT id, username, full_name, role, created_at FROM users WHERE id = ? AND deleted = 0', (user_id,)).fetchone()
        
        submissions = conn.execute('''SELECT s.*, a.title as assignment_title 
                                      FROM submissions s 
                                      JOIN assignments a ON s.assignment_id = a.id 
                                      WHERE s.user_id = ? AND s.deleted = 0''', (user_id,)).fetchall()
        
        attendances = conn.execute('SELECT * FROM attendances WHERE user_id = ? ORDER BY login_time DESC LIMIT 10', (user_id,)).fetchall()
        
        conn.close()
        
        if user:
            self.send_json({
                'user': dict(user),
                'submissions': [dict(s) for s in submissions],
                'attendances': [dict(a) for a in attendances]
            })
        else:
            self.send_json({'error': '用户不存在'}, status=404)
    
    def create_user(self, data):
        if not data.get('username') or not data.get('password'):
            self.send_json({'error': '用户名和密码不能为空'}, status=400)
            return
        
        conn = get_db()
        cursor = conn.cursor()
        try:
            pwd_hash = hashlib.sha256(data.get('password').encode()).hexdigest()
            cursor.execute('''INSERT INTO users (username, password_hash, full_name, role) 
                             VALUES (?, ?, ?, ?)''',
                             (data.get('username'), pwd_hash, data.get('full_name'), data.get('role', 'student')))
            user_id = cursor.lastrowid
            log_operation(cursor, data.get('created_by', 1), 'CREATE', 'user', f'创建用户: {data.get("username")} (角色: {data.get("role")})')
            conn.commit()
            conn.close()
            self.send_json({'success': True, 'id': user_id})
        except sqlite3.IntegrityError:
            conn.close()
            self.send_json({'error': '用户名已存在'}, status=400)
    
    def update_user(self, data):
        conn = get_db()
        cursor = conn.cursor()
        
        updates = []
        values = []
        if data.get('full_name') is not None:
            updates.append('full_name = ?')
            values.append(data.get('full_name'))
        if data.get('role') is not None:
            updates.append('role = ?')
            values.append(data.get('role'))
        if data.get('password'):
            updates.append('password_hash = ?')
            values.append(hashlib.sha256(data.get('password').encode()).hexdigest())
        
        if updates:
            values.append(data.get('id'))
            cursor.execute(f'UPDATE users SET {", ".join(updates)} WHERE id = ? AND deleted = 0', values)
            log_operation(cursor, data.get('id'), 'UPDATE', 'user', f'更新用户ID: {data.get("id")}')
            conn.commit()
        
        conn.close()
        self.send_json({'success': True})
    
    def change_password(self, data):
        user_id = data.get('user_id')
        old_password = data.get('old_password', '')
        new_password = data.get('new_password', '')
        
        if not old_password or not new_password:
            self.send_json({'error': '原密码和新密码都不能为空'}, status=400)
            return
        
        conn = get_db()
        cursor = conn.cursor()
        user = cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        
        if user and user['password_hash'] == hashlib.sha256(old_password.encode()).hexdigest():
            cursor.execute('UPDATE users SET password_hash = ? WHERE id = ?', 
                          (hashlib.sha256(new_password.encode()).hexdigest(), user_id))
            log_operation(cursor, user_id, user['username'], 'PASSWORD', 'user', '修改密码')
            conn.commit()
            self.send_json({'success': True})
        else:
            self.send_json({'error': '原密码错误'}, status=400)
        
        conn.close()
    
    def delete_user(self, user_id):
        if user_id == 1:
            self.send_json({'error': '不能删除管理员账户'}, status=400)
            return
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET deleted = 1 WHERE id = ?', (user_id,))
        log_operation(cursor, user_id, 'DELETE', 'user', f'删除用户ID: {user_id}')
        conn.commit()
        conn.close()
        self.send_json({'success': True})
    
    def handle_assignments(self):
        conn = get_db()
        limit = 50
        assignments = conn.execute('SELECT * FROM assignments WHERE deleted = 0 ORDER BY created_at DESC LIMIT ?', (limit,)).fetchall()
        conn.close()
        self.send_json({'assignments': [dict(a) for a in assignments]})
    
    def handle_all_assignments(self):
        conn = get_db()
        limit = 50
        assignments = conn.execute('SELECT * FROM assignments WHERE deleted = 0 ORDER BY created_at DESC LIMIT ?', (limit,)).fetchall()
        
        result = []
        for a in assignments:
            submission_count = conn.execute('SELECT COUNT(*) FROM submissions WHERE assignment_id = ? AND deleted = 0', (a['id'],)).fetchone()[0]
            creator = conn.execute('SELECT username, full_name FROM users WHERE id = ?', (a['created_by'],)).fetchone()
            assignment = dict(a)
            assignment['submission_count'] = submission_count
            assignment['creator_name'] = creator['full_name'] if creator else '未知'
            result.append(assignment)
        
        conn.close()
        self.send_json({'assignments': result})
    
    def get_assignment_detail(self, assignment_id):
        conn = get_db()
        assignment = conn.execute('SELECT * FROM assignments WHERE id = ? AND deleted = 0', (assignment_id,)).fetchone()
        
        submissions = conn.execute('''SELECT s.*, u.username, u.full_name 
                                   FROM submissions s 
                                   JOIN users u ON s.user_id = u.id 
                                   WHERE s.assignment_id = ? AND s.deleted = 0''', (assignment_id,)).fetchall()
        
        conn.close()
        
        if assignment:
            self.send_json({
                'assignment': dict(assignment),
                'submissions': [dict(s) for s in submissions]
            })
        else:
            self.send_json({'error': '作业不存在'}, status=404)
    
    def handle_create_assignment(self, data):
        try:
            if not data.get('title'):
                self.send_json({'error': '作业标题不能为空'}, status=400)
                return
            
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('''INSERT INTO assignments (title, content, assignment_type, options, correct_answer, points, created_by)
                             VALUES (?, ?, ?, ?, ?, ?, ?)''',
                             (data.get('title'), data.get('content'), data.get('assignment_type'),
                              json.dumps(data.get('options', [])), data.get('correct_answer'),
                              data.get('points', 10), data.get('created_by')))
            assignment_id = cursor.lastrowid
            log_operation(cursor, data.get('created_by'), 'CREATE', 'assignment', f'创建作业: {data.get("title")}')
            conn.commit()
            conn.close()
            self.send_json({'success': True, 'id': assignment_id})
        except Exception as e:
            print(f"Error creating assignment: {e}")
            self.send_json({'error': str(e)}, status=500)
    
    def delete_assignment(self, assignment_id):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('UPDATE assignments SET deleted = 1 WHERE id = ?', (assignment_id,))
        cursor.execute('UPDATE submissions SET deleted = 1 WHERE assignment_id = ?', (assignment_id,))
        log_operation(cursor, 1, 'DELETE', 'assignment', f'删除作业ID: {assignment_id}')
        conn.commit()
        conn.close()
        self.send_json({'success': True})
    
    def update_assignment(self, assignment_id, data):
        conn = get_db()
        cursor = conn.cursor()
        
        assignment = conn.execute('SELECT * FROM assignments WHERE id = ? AND deleted = 0', (assignment_id,)).fetchone()
        if not assignment:
            conn.close()
            self.send_json({'error': '作业不存在'}, status=404)
            return
        
        updates = []
        values = []
        if data.get('title') is not None:
            updates.append('title = ?')
            values.append(data.get('title'))
        if data.get('content') is not None:
            updates.append('content = ?')
            values.append(data.get('content'))
        if data.get('assignment_type') is not None:
            updates.append('assignment_type = ?')
            values.append(data.get('assignment_type'))
        if data.get('options') is not None:
            updates.append('options = ?')
            values.append(json.dumps(data.get('options')))
        if data.get('correct_answer') is not None:
            updates.append('correct_answer = ?')
            values.append(data.get('correct_answer'))
        if data.get('points') is not None:
            updates.append('points = ?')
            values.append(data.get('points'))
        
        if updates:
            values.append(assignment_id)
            cursor.execute(f'UPDATE assignments SET {", ".join(updates)} WHERE id = ? AND deleted = 0', values)
            log_operation(cursor, assignment['created_by'], 'UPDATE', 'assignment', f'更新作业: {data.get("title", assignment["title"])}')
            conn.commit()
        
        conn.close()
        self.send_json({'success': True})
    
    def handle_submit(self, data):
        user_id = data.get('user_id')
        assignment_id = data.get('assignment_id')
        answer = data.get('answer', '')
        
        if not user_id or not assignment_id:
            self.send_json({'error': '参数不完整'}, status=400)
            return
        
        conn = get_db()
        cursor = conn.cursor()
        
        assignment = conn.execute('SELECT * FROM assignments WHERE id = ? AND deleted = 0', (assignment_id,)).fetchone()
        
        if not assignment:
            conn.close()
            self.send_json({'error': '作业不存在'}, status=404)
            return
        
        is_correct = 0
        score = 0
        if assignment['assignment_type'] in ['single_choice', 'true_false'] and answer == assignment['correct_answer']:
            is_correct = 1
            score = assignment['points']
        
        existing = conn.execute('SELECT * FROM submissions WHERE user_id = ? AND assignment_id = ? AND deleted = 0',
                              (user_id, assignment_id)).fetchone()
        
        if existing:
            cursor.execute('''UPDATE submissions SET student_answer = ?, score = ?, is_correct = ?, submitted_at = ?
                          WHERE id = ?''',
                          (answer, score, is_correct, datetime.now().isoformat(), existing['id']))
            log_operation(cursor, user_id, 'UPDATE', 'submission', f'更新作答: 作业{assignment_id}')
        else:
            cursor.execute('''INSERT INTO submissions (user_id, assignment_id, student_answer, score, is_correct)
                           VALUES (?, ?, ?, ?, ?)''',
                           (user_id, assignment_id, answer, score, is_correct))
            log_operation(cursor, user_id, 'CREATE', 'submission', f'提交作业: 作业{assignment_id}')
        
        conn.commit()
        conn.close()
        self.send_json({'success': True, 'is_correct': is_correct, 'score': score})
    
    def delete_submission(self, submission_id):
        conn = get_db()
        cursor = conn.cursor()
        submission = conn.execute('SELECT * FROM submissions WHERE id = ?', (submission_id,)).fetchone()
        if submission:
            cursor.execute('UPDATE submissions SET deleted = 1 WHERE id = ?', (submission_id,))
            log_operation(cursor, submission['user_id'], 'DELETE', 'submission', f'删除作答ID: {submission_id}')
            conn.commit()
        conn.close()
        self.send_json({'success': True})
    
    def handle_my_submissions(self):
        params = parse_qs(urlparse(self.path).query)
        user_id = int(params.get('user_id', [0])[0])
        conn = get_db()
        submissions = conn.execute('''SELECT s.*, a.title as assignment_title, a.content as assignment_content
                                   FROM submissions s 
                                   JOIN assignments a ON s.assignment_id = a.id 
                                   WHERE s.user_id = ? AND s.deleted = 0''', (user_id,)).fetchall()
        conn.close()
        self.send_json({'submissions': [dict(s) for s in submissions]})
    
    def handle_submissions_by_assignment(self, assignment_id):
        conn = get_db()
        submissions = conn.execute('''SELECT s.*, u.username, u.full_name 
                                    FROM submissions s 
                                    JOIN users u ON s.user_id = u.id 
                                    WHERE s.assignment_id = ? AND s.deleted = 0''', (assignment_id,)).fetchall()
        conn.close()
        self.send_json({'submissions': [dict(s) for s in submissions]})
    
    def handle_auto_signin(self, data):
        user_id = data.get('user_id')
        if not user_id:
            self.send_json({'error': '用户ID不能为空'}, status=400)
            return
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO attendances (user_id, activity_score) VALUES (?, ?)', (user_id, 100))
        
        user = cursor.execute('SELECT username, full_name FROM users WHERE id = ?', (user_id,)).fetchone()
        log_operation(cursor, user_id, user['username'] if user else 'unknown', 'ATTENDANCE', 'attendance', f'自动签到: {user["full_name"] if user else "未知用户"}')
        
        conn.commit()
        conn.close()
        self.send_json({'success': True, 'time': datetime.now().isoformat()})
    
    def handle_attendance_records(self):
        conn = get_db()
        limit = 100
        records = conn.execute('''SELECT a.*, u.username, u.full_name FROM attendances a
                                JOIN users u ON a.user_id = u.id 
                                WHERE u.deleted = 0
                                ORDER BY a.login_time DESC LIMIT ?''', (limit,)).fetchall()
        conn.close()
        self.send_json({'records': [dict(r) for r in records]})
    
    def handle_info(self):
        conn = get_db()
        self.send_json({
            'version': '3.0.0',
            'users': conn.execute('SELECT COUNT(*) FROM users WHERE deleted = 0').fetchone()[0],
            'assignments': conn.execute('SELECT COUNT(*) FROM assignments WHERE deleted = 0').fetchone()[0],
            'submissions': conn.execute('SELECT COUNT(*) FROM submissions WHERE deleted = 0').fetchone()[0],
            'students': conn.execute("SELECT COUNT(*) FROM users WHERE role='student' AND deleted=0").fetchone()[0],
            'teachers': conn.execute("SELECT COUNT(*) FROM users WHERE role='teacher' AND deleted=0").fetchone()[0]
        })
        conn.close()
    
    def handle_class_stats(self):
        conn = get_db()
        self.send_json({
            'total_students': conn.execute("SELECT COUNT(*) FROM users WHERE role='student' AND deleted=0").fetchone()[0],
            'total_teachers': conn.execute("SELECT COUNT(*) FROM users WHERE role='teacher' AND deleted=0").fetchone()[0],
            'total_assignments': conn.execute('SELECT COUNT(*) FROM assignments WHERE deleted=0').fetchone()[0],
            'total_sessions': conn.execute('SELECT COUNT(*) FROM attendances').fetchone()[0],
            'today_sessions': conn.execute("SELECT COUNT(*) FROM attendances WHERE date(login_time) = date('now')").fetchone()[0]
        })
        conn.close()
    
    def handle_my_stats(self):
        params = parse_qs(urlparse(self.path).query)
        user_id = int(params.get('user_id', [0])[0])
        conn = get_db()
        
        submissions = conn.execute('SELECT COUNT(*) FROM submissions WHERE user_id = ? AND deleted=0', (user_id,)).fetchone()[0]
        avg_score = conn.execute('SELECT AVG(score) FROM submissions WHERE user_id = ?', (user_id,)).fetchone()[0] or 0
        sessions = conn.execute('SELECT COUNT(*) FROM attendances WHERE user_id = ?', (user_id,)).fetchone()[0]
        total_time = conn.execute('SELECT SUM(session_duration) FROM attendances WHERE user_id = ?', (user_id,)).fetchone()[0] or 0
        
        conn.close()
        
        self.send_json({
            'total_assignments': submissions,
            'avg_score': round(avg_score, 1),
            'total_sessions': sessions,
            'total_duration': total_time
        })
    
    def get_logs(self, data):
        conn = get_db()
        limit = 200
        logs = conn.execute('''SELECT * FROM operation_logs ORDER BY created_at DESC LIMIT ?''', (limit,)).fetchall()
        conn.close()
        self.send_json({'logs': [dict(l) for l in logs]})

print(f"\n{'='*50}")
print(f"  LMS-Edge Server v3.0 Started!")
print(f"{'='*50}")
print(f"  URL: http://localhost:{PORT}")
print(f"\n  admin / admin123")
print(f"  teacher / teacher123")
print(f"  student / student123")
print(f"{'='*50}\n")

with socketserver.TCPServer(("", PORT), LMSHandler) as httpd:
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
        conn.close()
