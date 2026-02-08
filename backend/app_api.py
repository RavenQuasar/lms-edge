#!/usr/bin/env python3
"""
LMS-Edge Flask API Server v3.1
Full-featured Classroom LAN Teaching Management System
"""

from flask import Flask, request, jsonify, send_from_directory, send_file
import sqlite3
import json
import os
import hashlib
import time
import uuid
import shutil
from datetime import datetime, timedelta
from functools import wraps

app = Flask(__name__)

DB_PATH = os.environ.get('DB_PATH', '/home/raven/lms-edge/backend/data/lms.db')
STATIC_DIR = os.environ.get('STATIC_DIR', '/home/raven/lms-edge/backend/static')
UPLOAD_DIR = os.environ.get('UPLOAD_DIR', '/home/raven/lms-edge/backend/uploads')
ATTACHMENTS_DIR = os.environ.get('ATTACHMENTS_DIR', '/home/raven/lms-edge/backend/attachments')
SUBMISSIONS_DIR = os.environ.get('SUBMISSIONS_DIR', '/home/raven/lms-edge/backend/submissions')

os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(ATTACHMENTS_DIR, exist_ok=True)
os.makedirs(SUBMISSIONS_DIR, exist_ok=True)

ALLOWED_ATTACHMENT_EXTENSIONS = {'xlsx', 'xls', 'doc', 'docx', 'zip', 'rar', 'jpg', 'jpeg', 'png', 'gif', 'pdf'}
ALLOWED_SUBMISSION_EXTENSIONS = {'zip', 'rar', 'jpg', 'jpeg', 'png', 'gif', 'pdf', 'doc', 'docx'}

def get_db():
    conn = sqlite3.connect(DB_PATH, isolation_level=None, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn

def allowed_file(filename, allowed_set):
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    return ext in allowed_set

def init_db():
    conn = sqlite3.connect(DB_PATH, isolation_level=None)
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        full_name TEXT,
        role TEXT DEFAULT 'student',
        avatar TEXT DEFAULT 'default.png',
        last_active TEXT,
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
        attachment TEXT,
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
        attachment TEXT,
        feedback TEXT,
        submitted_at TEXT DEFAULT CURRENT_TIMESTAMP,
        deleted INTEGER DEFAULT 0
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS attendances (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        login_time TEXT DEFAULT CURRENT_TIMESTAMP,
        logout_time TEXT,
        activity_score REAL DEFAULT 0,
        session_duration INTEGER DEFAULT 0,
        last_active TEXT DEFAULT CURRENT_TIMESTAMP
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
    conn.close()

def log_operation(user_id, username, action, target, details):
    try:
        conn = get_db()
        conn.execute('''INSERT INTO operation_logs (user_id, username, action, target, details) 
                       VALUES (?, ?, ?, ?, ?)''',
                      (user_id, username, action, target, details))
        conn.commit()
        conn.close()
    except Exception:
        pass

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS')
    return response

@app.route('/')
def index():
    return send_from_directory(STATIC_DIR, 'index.html')

@app.route('/<path:filename>')
def static_files(filename):
    return send_from_directory(STATIC_DIR, filename)

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'time': datetime.now().isoformat()})

@app.route('/api/info', methods=['GET'])
def info():
    conn = get_db()
    role = request.args.get('role', '')
    if role == 'student':
        data = {'version': '3.1.0', 'assignments': conn.execute('SELECT COUNT(*) FROM assignments WHERE deleted=0').fetchone()[0]}
    else:
        data = {
            'version': '3.1.0',
            'users': conn.execute('SELECT COUNT(*) FROM users WHERE deleted=0').fetchone()[0],
            'students': conn.execute("SELECT COUNT(*) FROM users WHERE role='student' AND deleted=0").fetchone()[0],
            'teachers': conn.execute("SELECT COUNT(*) FROM users WHERE role='teacher' AND deleted=0").fetchone()[0],
            'assignments': conn.execute('SELECT COUNT(*) FROM assignments WHERE deleted=0').fetchone()[0],
            'submissions': conn.execute('SELECT COUNT(*) FROM submissions WHERE deleted=0').fetchone()[0]
        }
    conn.close()
    return jsonify(data)

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username', '')
    password = data.get('password', '')
    
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE username = ? AND deleted = 0', (username,)).fetchone()
    conn.close()
    
    if user:
        pwd_hash = hashlib.sha256(password.encode()).hexdigest()
        if user['password_hash'] == pwd_hash:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('UPDATE users SET last_active = ? WHERE id = ?', (datetime.now().isoformat(), user['id']))
            
            last_att = conn.execute('SELECT * FROM attendances WHERE user_id = ? ORDER BY login_time DESC LIMIT 1', (user['id'],)).fetchone()
            if last_att and not last_att['logout_time']:
                pass
            else:
                cursor.execute('INSERT INTO attendances (user_id, activity_score) VALUES (?, ?)', (user['id'], 100))
                cursor.execute('UPDATE attendances SET last_active = ? WHERE id = ?', (datetime.now().isoformat(), cursor.lastrowid))
            
            conn.commit()
            conn.close()
            
            log_operation(user['id'], user['username'], 'LOGIN', 'auth', '用户登录成功')
            return jsonify({
                'token': f'token_{user["id"]}_{int(time.time())}',
                'user': {
                    'id': user['id'],
                    'username': user['username'],
                    'full_name': user['full_name'],
                    'role': user['role']
                }
            })
    
    return jsonify({'error': '用户名或密码错误'}), 401

@app.route('/api/users', methods=['GET'])
def get_users():
    conn = get_db()
    users = conn.execute('SELECT id, username, full_name, role, last_active, created_at FROM users WHERE deleted = 0 ORDER BY id').fetchall()
    conn.close()
    return jsonify({'users': [dict(u) for u in users]})

@app.route('/api/users/create', methods=['POST'])
def create_user():
    data = request.get_json()
    if not data.get('username') or not data.get('password'):
        return jsonify({'error': '用户名和密码不能为空'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    try:
        pwd_hash = hashlib.sha256(data.get('password').encode()).hexdigest()
        cursor.execute('''INSERT INTO users (username, password_hash, full_name, role) 
                         VALUES (?, ?, ?, ?)''',
                         (data.get('username'), pwd_hash, data.get('full_name'), data.get('role', 'student')))
        user_id = cursor.lastrowid
        log_operation(user_id, data.get('username'), 'CREATE', 'user', f'创建用户: {data.get("username")}')
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'id': user_id})
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'error': '用户名已存在'}), 400

@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user_detail(user_id):
    conn = get_db()
    user = conn.execute('SELECT id, username, full_name, role, last_active, created_at FROM users WHERE id = ? AND deleted = 0', (user_id,)).fetchone()
    conn.close()
    if user:
        return jsonify({'user': dict(user)})
    return jsonify({'error': '用户不存在'}), 404

@app.route('/api/users/', methods=['PUT'])
def update_user():
    data = request.get_json()
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
        user = conn.execute('SELECT username FROM users WHERE id = ?', (data.get('id'),)).fetchone()
        log_operation(data.get('id'), user['username'] if user else 'unknown', 'UPDATE', 'user', f'更新用户ID: {data.get("id")}')
        conn.commit()
    
    conn.close()
    return jsonify({'success': True})

@app.route('/api/users/password', methods=['PUT'])
def change_password():
    data = request.get_json()
    user_id = data.get('user_id')
    old_password = data.get('old_password', '')
    new_password = data.get('new_password', '')
    
    if not old_password or not new_password:
        return jsonify({'error': '原密码和新密码都不能为空'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    user = cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    
    if user and user['password_hash'] == hashlib.sha256(old_password.encode()).hexdigest():
        cursor.execute('UPDATE users SET password_hash = ? WHERE id = ?', 
                      (hashlib.sha256(new_password.encode()).hexdigest(), user_id))
        log_operation(user_id, user['username'], 'PASSWORD', 'user', '修改密码')
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    
    conn.close()
    return jsonify({'error': '原密码错误'}), 400

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    if user_id == 1:
        return jsonify({'error': '不能删除管理员账户'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET deleted = 1 WHERE id = ?', (user_id,))
    user = conn.execute('SELECT username FROM users WHERE id = ?', (user_id,)).fetchone()
    log_operation(user_id, user['username'] if user else 'unknown', 'DELETE', 'user', f'删除用户ID: {user_id}')
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/assignments', methods=['GET'])
def get_assignments():
    user_id = request.args.get('user_id', type=int)
    conn = get_db()
    limit = 100
    assignments = conn.execute('SELECT * FROM assignments WHERE deleted = 0 ORDER BY created_at DESC LIMIT ?', (limit,)).fetchall()
    result = []
    for a in assignments:
        assignment = dict(a)
        if user_id:
            submission = conn.execute('SELECT id, score, feedback FROM submissions WHERE user_id = ? AND assignment_id = ? AND deleted = 0',
                                      (user_id, a['id'])).fetchone()
            assignment['my_submission'] = dict(submission) if submission else None
        result.append(assignment)
    conn.close()
    return jsonify({'assignments': result})

@app.route('/api/assignments/all', methods=['GET'])
def get_all_assignments():
    conn = get_db()
    limit = 100
    assignments = conn.execute('''
        SELECT a.*, u.full_name as creator_name,
               (SELECT COUNT(*) FROM submissions s WHERE s.assignment_id = a.id AND s.deleted = 0) as submission_count
        FROM assignments a
        LEFT JOIN users u ON a.created_by = u.id
        WHERE a.deleted = 0
        ORDER BY a.created_at DESC
        LIMIT ?
    ''', (limit,)).fetchall()
    conn.close()
    return jsonify({'assignments': [dict(a) for a in assignments]})

@app.route('/api/assignments/<int:assignment_id>', methods=['GET'])
def get_assignment_detail(assignment_id):
    conn = get_db()
    assignment = conn.execute('SELECT * FROM assignments WHERE id = ? AND deleted = 0', (assignment_id,)).fetchone()
    submissions = conn.execute('''SELECT s.*, u.username, u.full_name 
                               FROM submissions s 
                               JOIN users u ON s.user_id = u.id 
                               WHERE s.assignment_id = ? AND s.deleted = 0''', (assignment_id,)).fetchall()
    conn.close()
    if assignment:
        result = dict(assignment)
        result['submissions'] = [dict(s) for s in submissions]
        return jsonify({'assignment': result})
    return jsonify({'error': '作业不存在'}), 404

@app.route('/api/assignments/create', methods=['POST'])
def create_assignment():
    data = request.get_json()
    if not data.get('title'):
        return jsonify({'error': '作业标题不能为空'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO assignments (title, content, assignment_type, options, correct_answer, points, attachment, created_by)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                     (data.get('title'), data.get('content'), data.get('assignment_type'),
                      json.dumps(data.get('options', [])), data.get('correct_answer'),
                      data.get('points', 10), data.get('attachment'), data.get('created_by')))
    assignment_id = cursor.lastrowid
    creator = conn.execute('SELECT username FROM users WHERE id = ?', (data.get('created_by'),)).fetchone()
    log_operation(data.get('created_by'), creator['username'] if creator else 'unknown', 'CREATE', 'assignment', f'创建作业: {data.get("title")}')
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'id': assignment_id})

@app.route('/api/assignments/<int:assignment_id>', methods=['PUT'])
def update_assignment(assignment_id):
    data = request.get_json()
    conn = get_db()
    cursor = conn.cursor()
    
    assignment = conn.execute('SELECT * FROM assignments WHERE id = ? AND deleted = 0', (assignment_id,)).fetchone()
    if not assignment:
        conn.close()
        return jsonify({'error': '作业不存在'}), 404
    
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
    if data.get('attachment') is not None:
        updates.append('attachment = ?')
        values.append(data.get('attachment'))
    
    if updates:
        values.append(assignment_id)
        cursor.execute(f'UPDATE assignments SET {", ".join(updates)} WHERE id = ? AND deleted = 0', values)
        creator = conn.execute('SELECT username FROM users WHERE id = ?', (assignment['created_by'],)).fetchone()
        log_operation(assignment['created_by'], creator['username'] if creator else 'unknown', 'UPDATE', 'assignment', f'更新作业: {data.get("title", assignment["title"])}')
        conn.commit()
    
    conn.close()
    return jsonify({'success': True})

@app.route('/api/assignments/<int:assignment_id>', methods=['DELETE'])
def delete_assignment(assignment_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('UPDATE assignments SET deleted = 1 WHERE id = ?', (assignment_id,))
    cursor.execute('UPDATE submissions SET deleted = 1 WHERE assignment_id = ?', (assignment_id,))
    admin = conn.execute('SELECT username FROM users WHERE id = 1').fetchone()
    log_operation(1, admin['username'] if admin else 'admin', 'DELETE', 'assignment', f'删除作业ID: {assignment_id}')
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/attachments/<int:assignment_id>', methods=['POST'])
def upload_attachment(assignment_id):
    if 'file' not in request.files:
        return jsonify({'error': '没有文件'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400
    
    filename = file.filename
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    if ext not in ALLOWED_ATTACHMENT_EXTENSIONS:
        return jsonify({'error': f'不支持的文件格式，允许格式: {", ".join(ALLOWED_ATTACHMENT_EXTENSIONS)}'}), 400
    
    safe_filename = f'{assignment_id}_{uuid.uuid4().hex[:8]}_{filename}'
    filepath = os.path.join(ATTACHMENTS_DIR, safe_filename)
    file.save(filepath)
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('UPDATE assignments SET attachment = ? WHERE id = ?', (safe_filename, assignment_id))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'filename': safe_filename})

@app.route('/api/attachments/<int:assignment_id>/<path:filename>', methods=['GET'])
def download_attachment(assignment_id, filename):
    filepath = os.path.join(ATTACHMENTS_DIR, filename)
    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=True, download_name=filename)
    return jsonify({'error': '文件不存在'}), 404

@app.route('/api/submissions/file/<int:submission_id>', methods=['POST'])
def upload_submission_file(submission_id):
    if 'file' not in request.files:
        return jsonify({'error': '没有文件'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400
    
    filename = file.filename
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    if ext not in ALLOWED_SUBMISSION_EXTENSIONS:
        return jsonify({'error': f'不支持的文件格式，允许格式: {", ".join(ALLOWED_SUBMISSION_EXTENSIONS)}'}), 400
    
    safe_filename = f'{submission_id}_{uuid.uuid4().hex[:8]}_{filename}'
    filepath = os.path.join(SUBMISSIONS_DIR, safe_filename)
    file.save(filepath)
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('UPDATE submissions SET attachment = ? WHERE id = ?', (safe_filename, submission_id))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'filename': safe_filename})

@app.route('/api/submissions/file/<int:submission_id>/<path:filename>', methods=['GET'])
def download_submission_file(submission_id, filename):
    filepath = os.path.join(SUBMISSIONS_DIR, filename)
    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=True, download_name=filename)
    return jsonify({'error': '文件不存在'}), 404

@app.route('/api/assignments/submit', methods=['POST'])
def submit_assignment():
    data = request.get_json()
    user_id = data.get('user_id')
    assignment_id = data.get('assignment_id')
    answer = data.get('answer', '')
    
    if not user_id or not assignment_id:
        return jsonify({'error': '参数不完整'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    
    assignment = conn.execute('SELECT * FROM assignments WHERE id = ? AND deleted = 0', (assignment_id,)).fetchone()
    if not assignment:
        conn.close()
        return jsonify({'error': '作业不存在'}), 404
    
    assignment_type = assignment['assignment_type']
    existing = conn.execute('SELECT * FROM submissions WHERE user_id = ? AND assignment_id = ? AND deleted = 0',
                          (user_id, assignment_id)).fetchone()
    
    if existing:
        if assignment_type in ['single_choice', 'multiple_choice']:
            conn.close()
            return jsonify({'error': '选择题作答后不可修改', 'submitted': True, 'answer': existing['student_answer'], 'is_correct': existing['is_correct']}), 400
        else:
            cursor.execute('''UPDATE submissions SET student_answer = ?, submitted_at = ?
                          WHERE id = ?''', (answer, datetime.now().isoformat(), existing['id']))
            log_msg = 'UPDATE'
            score = existing['score']
            is_correct = existing['is_correct']
    else:
        if assignment_type in ['single_choice', 'multiple_choice']:
            is_correct = 0
            score = 0
            correct_answer = assignment['correct_answer'] or ''
            if assignment_type == 'multiple_choice':
                student_answers = set((answer or '').split(','))
                correct_answers = set(correct_answer.split(','))
                if student_answers == correct_answers:
                    is_correct = 1
                    score = assignment['points']
            else:
                if answer == correct_answer:
                    is_correct = 1
                    score = assignment['points']
        else:
            is_correct = 0
            score = 0
        
        cursor.execute('''INSERT INTO submissions (user_id, assignment_id, student_answer, score, is_correct)
                       VALUES (?, ?, ?, ?, ?)''',
                       (user_id, assignment_id, answer, score, is_correct))
        log_msg = 'CREATE'
    
    conn.commit()
    conn.close()
    if log_msg:
        conn2 = get_db()
        user = conn2.execute('SELECT username FROM users WHERE id = ?', (user_id,)).fetchone()
        conn2.close()
        log_operation(user_id, user['username'] if user else 'unknown', log_msg, 'submission', f'作答作业ID: {assignment_id}')
    
    result = {'success': True, 'submitted': True}
    if assignment_type in ['single_choice', 'multiple_choice']:
        result['is_correct'] = is_correct
        result['score'] = score
    else:
        result['message'] = '提交成功！等待老师批改作业'
    return jsonify(result)

@app.route('/api/submissions/<int:submission_id>', methods=['GET', 'DELETE'])
def handle_submission(submission_id):
    conn = get_db()
    
    if request.method == 'DELETE':
        cursor = conn.cursor()
        submission = conn.execute('SELECT * FROM submissions WHERE id = ?', (submission_id,)).fetchone()
        if submission:
            cursor.execute('UPDATE submissions SET deleted = 1 WHERE id = ?', (submission_id,))
            conn.commit()
            user = conn.execute('SELECT username FROM users WHERE id = ?', (submission['user_id'],)).fetchone()
            log_operation(submission['user_id'], user['username'] if user else 'unknown', 'DELETE', 'submission', f'删除作答ID: {submission_id}')
        conn.close()
        return jsonify({'success': True})
    
    submission = conn.execute('''SELECT s.*, a.title as assignment_title, a.content as assignment_content, a.attachment as assignment_attachment,
                                   a.assignment_type, a.points, u.username, u.full_name
                                   FROM submissions s
                                   JOIN assignments a ON s.assignment_id = a.id
                                   JOIN users u ON s.user_id = u.id
                                   WHERE s.id = ?''', (submission_id,)).fetchone()
    conn.close()
    if submission:
        return jsonify({'submission': dict(submission)})
    return jsonify({'error': '作答不存在'}), 404

@app.route('/api/submissions/<int:submission_id>/grade', methods=['POST'])
def grade_submission(submission_id):
    data = request.get_json()
    score = data.get('score', 0)
    feedback = data.get('feedback', '')
    teacher_id = data.get('teacher_id')
    
    if not teacher_id:
        return jsonify({'error': '缺少教师ID'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    submission = conn.execute('SELECT * FROM submissions WHERE id = ? AND deleted = 0', (submission_id,)).fetchone()
    
    if not submission:
        conn.close()
        return jsonify({'error': '作答不存在'}), 404
    
    cursor.execute('UPDATE submissions SET score = ?, feedback = ?, is_correct = ? WHERE id = ?',
                  (score, feedback, 1 if score > 0 else 0, submission_id))
    
    assignment = conn.execute('SELECT * FROM assignments WHERE id = ?', (submission['assignment_id'],)).fetchone()
    teacher = conn.execute('SELECT username FROM users WHERE id = ?', (teacher_id,)).fetchone()
    
    log_operation(teacher_id, teacher['username'] if teacher else 'unknown', 'GRADE', 'submission', 
                  f'批改作业ID:{submission["assignment_id"]} 作答ID:{submission_id} 得分:{score}')
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/submissions/my', methods=['GET'])
def get_my_submissions():
    user_id = request.args.get('user_id', 0, type=int)
    conn = get_db()
    submissions = conn.execute('''SELECT s.*, a.title as assignment_title, a.content as assignment_content, a.attachment as assignment_attachment,
                               a.assignment_type, a.options, a.correct_answer
                               FROM submissions s 
                               JOIN assignments a ON s.assignment_id = a.id 
                               WHERE s.user_id = ? AND s.deleted = 0''', (user_id,)).fetchall()
    conn.close()
    return jsonify({'submissions': [dict(s) for s in submissions]})

@app.route('/api/attendance/records', methods=['GET'])
def get_attendance_records():
    conn = get_db()
    limit = 200
    records = conn.execute('''SELECT a.*, u.username, u.full_name, u.role FROM attendances a
                            JOIN users u ON a.user_id = u.id 
                            WHERE u.deleted = 0
                            ORDER BY a.login_time DESC LIMIT ?''', (limit,)).fetchall()
    conn.close()
    return jsonify({'records': [dict(r) for r in records]})

@app.route('/api/attendance/online', methods=['GET'])
def get_online_users():
    conn = get_db()
    threshold = (datetime.now() - timedelta(minutes=5)).strftime('%Y-%m-%d %H:%M:%S')
    online = conn.execute('''SELECT id, username, full_name, role, last_active FROM users 
                            WHERE deleted = 0 AND last_active > ? 
                            ORDER BY last_active DESC''', (threshold,)).fetchall()
    conn.close()
    return jsonify({'online': [dict(u) for u in online], 'threshold': threshold})

@app.route('/api/attendance/auto', methods=['POST'])
def auto_signin():
    data = request.get_json()
    user_id = data.get('user_id')
    
    if not user_id:
        return jsonify({'error': '用户ID不能为空'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET last_active = ? WHERE id = ?', (datetime.now().isoformat(), user_id))
    
    last_att = conn.execute('SELECT * FROM attendances WHERE user_id = ? ORDER BY login_time DESC LIMIT 1', (user_id,)).fetchone()
    if last_att and not last_att['logout_time']:
        cursor.execute('UPDATE attendances SET last_active = ? WHERE id = ?', (datetime.now().isoformat(), last_att['id']))
    else:
        cursor.execute('INSERT INTO attendances (user_id, activity_score) VALUES (?, ?)', (user_id, 100))
    
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/stats/class', methods=['GET'])
def get_class_stats():
    conn = get_db()
    data = {
        'total_students': conn.execute("SELECT COUNT(*) FROM users WHERE role='student' AND deleted=0").fetchone()[0],
        'total_teachers': conn.execute("SELECT COUNT(*) FROM users WHERE role='teacher' AND deleted=0").fetchone()[0],
        'total_assignments': conn.execute('SELECT COUNT(*) FROM assignments WHERE deleted=0').fetchone()[0],
        'total_sessions': conn.execute('SELECT COUNT(*) FROM attendances').fetchone()[0],
        'today_sessions': conn.execute("SELECT COUNT(*) FROM attendances WHERE date(login_time) = date('now')").fetchone()[0]
    }
    conn.close()
    return jsonify(data)

@app.route('/api/stats/my', methods=['GET'])
def get_my_stats():
    user_id = request.args.get('user_id', 0, type=int)
    conn = get_db()
    
    submissions = conn.execute('SELECT COUNT(*) FROM submissions WHERE user_id = ? AND deleted=0', (user_id,)).fetchone()[0]
    avg_score = conn.execute('SELECT AVG(score) FROM submissions WHERE user_id = ?', (user_id,)).fetchone()[0] or 0
    total_score = conn.execute('SELECT COALESCE(SUM(score), 0) FROM submissions WHERE user_id = ? AND deleted=0', (user_id,)).fetchone()[0] or 0
    sessions = conn.execute('SELECT COUNT(*) FROM attendances WHERE user_id = ?', (user_id,)).fetchone()[0]
    total_time = conn.execute('SELECT SUM(session_duration) FROM attendances WHERE user_id = ?', (user_id,)).fetchone()[0] or 0
    
    conn.close()
    return jsonify({
        'total_assignments': submissions,
        'avg_score': round(avg_score, 1),
        'total_score': round(total_score, 1),
        'total_sessions': sessions,
        'total_duration': total_time
    })

@app.route('/api/logs', methods=['GET'])
def get_logs():
    conn = get_db()
    limit = 200
    logs = conn.execute('''SELECT * FROM operation_logs ORDER BY created_at DESC LIMIT ?''', (limit,)).fetchall()
    conn.close()
    return jsonify({'logs': [dict(l) for l in logs]})

import threading
import time

whiteboard_lock = threading.Lock()

@app.route('/api/whiteboard', methods=['POST'])
def save_whiteboard():
    data = request.get_json()
    user_id = data.get('user_id')
    content = data.get('content', '')
    drawings = data.get('drawings', [])
    
    whiteboard_file = os.path.join(STATIC_DIR, 'whiteboard.json')
    try:
        with whiteboard_lock:
            if os.path.exists(whiteboard_file):
                with open(whiteboard_file, 'r') as f:
                    whiteboard = json.load(f)
            else:
                whiteboard = {'updates': [], 'drawings': [], 'allowed': False, 'online': {}}
            
            whiteboard['content'] = content
            whiteboard['updated_at'] = datetime.now().isoformat()
            
            if drawings:
                existing_drawings = whiteboard.get('drawings', [])
                existing_drawings.extend(drawings)
                whiteboard['drawings'] = existing_drawings[-500:]
            
            online_users = whiteboard.get('online', {})
            online_users[str(user_id)] = datetime.now().isoformat()
            for uid in list(online_users.keys()):
                last_time = datetime.fromisoformat(online_users[uid])
                if (datetime.now() - last_time).seconds > 30:
                    del online_users[uid]
            whiteboard['online'] = online_users
            whiteboard['online_count'] = len(online_users)
            
            with open(whiteboard_file, 'w') as f:
                json.dump(whiteboard, f)
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/whiteboard/settings', methods=['GET', 'POST'])
def whiteboard_settings():
    whiteboard_file = os.path.join(STATIC_DIR, 'whiteboard.json')
    
    if request.method == 'POST':
        data = request.get_json()
        allowed = data.get('allowed', False)
        try:
            if os.path.exists(whiteboard_file):
                with open(whiteboard_file, 'r') as f:
                    whiteboard = json.load(f)
            else:
                whiteboard = {'updates': [], 'allowed': False}
            whiteboard['allowed'] = allowed
            whiteboard['updated_at'] = datetime.now().isoformat()
            with open(whiteboard_file, 'w') as f:
                json.dump(whiteboard, f)
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    try:
        if os.path.exists(whiteboard_file):
            with open(whiteboard_file, 'r') as f:
                whiteboard = json.load(f)
            return jsonify({'allowed': whiteboard.get('allowed', False)})
        return jsonify({'allowed': False})
    except:
        return jsonify({'allowed': False})

@app.route('/api/whiteboard', methods=['GET'])
def get_whiteboard():
    whiteboard_file = os.path.join(STATIC_DIR, 'whiteboard.json')
    if os.path.exists(whiteboard_file):
        try:
            with open(whiteboard_file, 'r') as f:
                return jsonify(json.load(f))
        except:
            pass
    return jsonify({'drawings': [], 'content': '', 'allowed': False, 'online_count': 0})

@app.route('/api/whiteboard/heartbeat', methods=['POST'])
def whiteboard_heartbeat():
    data = request.get_json()
    user_id = data.get('user_id')
    
    whiteboard_file = os.path.join(STATIC_DIR, 'whiteboard.json')
    try:
        with whiteboard_lock:
            if os.path.exists(whiteboard_file):
                with open(whiteboard_file, 'r') as f:
                    whiteboard = json.load(f)
            else:
                whiteboard = {'updates': [], 'drawings': [], 'allowed': False, 'online': {}}
            
            online_users = whiteboard.get('online', {})
            online_users[str(user_id)] = datetime.now().isoformat()
            
            for uid in list(online_users.keys()):
                last_time = datetime.fromisoformat(online_users[uid])
                if (datetime.now() - last_time).seconds > 30:
                    del online_users[uid]
            
            whiteboard['online'] = online_users
            whiteboard['online_count'] = len(online_users)
            
            with open(whiteboard_file, 'w') as f:
                json.dump(whiteboard, f)
        
        return jsonify({'success': True, 'online_count': len(online_users)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/whiteboard/clear', methods=['POST'])
def clear_whiteboard():
    data = request.get_json()
    user_id = data.get('user_id')
    
    conn = get_db()
    user = conn.execute('SELECT role FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    
    if not user or user['role'] != 'teacher':
        return jsonify({'error': '只有老师可以清空白板'}), 403
    
    whiteboard_file = os.path.join(STATIC_DIR, 'whiteboard.json')
    try:
        with whiteboard_lock:
            whiteboard = {
                'drawings': [],
                'content': '',
                'allowed': False,
                'online': {},
                'online_count': 0,
                'updated_at': datetime.now().isoformat()
            }
            with open(whiteboard_file, 'w') as f:
                json.dump(whiteboard, f)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

GAME_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'game')
os.makedirs(GAME_DIR, exist_ok=True)
game_lock = threading.Lock()
MATCHES_FILE = os.path.join(GAME_DIR, 'matches.json')
PENDING_FILE = os.path.join(GAME_DIR, 'pending.json')
PLAYERS_FILE = os.path.join(GAME_DIR, 'players.json')

def load_json(filepath, default):
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except:
            pass
    return default

def save_json(filepath, data):
    with open(filepath, 'w') as f:
        json.dump(data, f, ensure_ascii=False)

def get_questions():
    q_file = os.path.join(GAME_DIR, 'questions.json')
    if os.path.exists(q_file):
        return load_json(q_file, [])
    questions = [
        {'q': '1+1=', 'options': ['1', '2', '3', '4'], 'answer': 'B', 'is_multi': False},
        {'q': '2+2=', 'options': ['3', '4', '5', '6'], 'answer': 'B', 'is_multi': False},
        {'q': '3+3=', 'options': ['5', '6', '7', '8'], 'answer': 'B', 'is_multi': False},
        {'q': '中国的首都是？', 'options': ['上海', '北京', '广州', '深圳'], 'answer': 'B', 'is_multi': False},
        {'q': '太阳从哪边升起？', 'options': ['西', '东', '南', '北'], 'answer': 'B', 'is_multi': False},
        {'q': '水有几个氢原子？', 'options': ['1', '2', '3', '4'], 'answer': 'B', 'is_multi': False},
        {'q': '下列哪个是水果？', 'options': ['汽车', '苹果', '桌子', '电视'], 'answer': 'B', 'is_multi': False},
        {'q': '1小时有多少分钟？', 'options': ['30', '60', '90', '120'], 'answer': 'B', 'is_multi': False},
        {'q': '兔子的耳朵有几个？', 'options': ['1', '2', '3', '4'], 'answer': 'B', 'is_multi': False},
        {'q': '天空是什么颜色？', 'options': ['红色', '蓝色', '绿色', '黄色'], 'answer': 'B', 'is_multi': False},
        {'q': '下面哪个是动物？', 'options': ['石头', '狗', '椅子', '书本'], 'answer': 'B', 'is_multi': False},
        {'q': '2x3等于多少？', 'options': ['5', '6', '7', '8'], 'answer': 'B', 'is_multi': False},
        {'q': '一年有几个季节？', 'options': ['2', '3', '4', '5'], 'answer': 'C', 'is_multi': False},
        {'q': '下列哪个是蔬菜？', 'options': ['香蕉', '苹果', '胡萝卜', '葡萄'], 'answer': 'C', 'is_multi': False},
        {'q': '人有多少根手指？', 'options': ['5', '10', '15', '20'], 'answer': 'B', 'is_multi': False},
        {'q': '下列哪些是水果？', 'options': ['苹果', '香蕉', '胡萝卜', '葡萄'], 'answer': 'A,B,D', 'is_multi': True},
        {'q': '下列哪些是动物？', 'options': ['狗', '猫', '桌子', '鸟'], 'answer': 'A,B,D', 'is_multi': True},
    ]
    save_json(q_file, questions)
    return questions

@app.route('/api/game/player', methods=['GET'])
def get_player_game_data():
    user_id = request.args.get('user_id', type=int)
    conn = get_db()
    user = conn.execute('SELECT id, username, full_name, role FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    players = load_json(PLAYERS_FILE, [])
    player = next((p for p in players if p['user_id'] == user_id), None)
    
    if not player:
        player = {
            'user_id': user_id,
            'username': user['username'],
            'full_name': user['full_name'] or user['username'],
            'gold': 10,
            'medals': 0,
            'wins': 0,
            'inventory': [{'e': '🍎', 't': 'heal', 'name': '苹果'}]
        }
        players.append(player)
        save_json(PLAYERS_FILE, players)
    
    return jsonify({'player': player})

@app.route('/api/game/match', methods=['POST'])
def game_match():
    data = request.get_json()
    user_id = data.get('user_id')
    conn = get_db()
    user = conn.execute('SELECT username, full_name FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    
    if not user:
        return jsonify({'success': False, 'message': '用户不存在'})
    
    pending = load_json(PENDING_FILE, [])
    matches = load_json(MATCHES_FILE, [])
    
    pending = [p for p in pending if p['expires'] > datetime.now().timestamp()]
    
    print(f"[MATCH] User {user_id} joining, pending before={[p['user_id'] for p in pending]}")
    
    for i, p in enumerate(pending):
        if p['user_id'] != user_id:
            match_id = str(int(datetime.now().timestamp())) + str(user_id)
            opponent = p['user_data']
            questions = get_questions()
            
            match = {
                'match_id': match_id,
                'player1': p['user_id'],
                'player2': user_id,
                'player1_data': opponent,
                'player2_data': {'user_id': user_id, 'username': user['username'], 'full_name': user['full_name'] or user['username']},
                'player1_hp': 100,
                'player2_hp': 100,
                'player1_answered': False,
                'player2_answered': False,
                'player1_answer': None,
                'player2_answer': None,
                'player1_correct': None,
                'player2_correct': None,
                'current_question_idx': 0,
                'questions': questions,
                'my_turn': 1,
                'created_at': datetime.now().isoformat(),
                'game_over': False,
                'winner': None
            }
            
            pending.pop(i)
            matches.append(match)
            save_json(PENDING_FILE, pending)
            save_json(MATCHES_FILE, matches)
            
            print(f"[MATCH] Match created: {match_id}, P1={p['user_id']}, P2={user_id}")
            return jsonify({'success': True, 'match_id': match_id, 'opponent': opponent, 'is_player1': False, 'player1_id': p['user_id']})
    
    pending.append({
        'user_id': user_id,
        'user_data': {'user_id': user_id, 'username': user['username'], 'full_name': user['full_name'] or user['username']},
        'expires': datetime.now().timestamp() + 60
    })
    save_json(PENDING_FILE, pending)
    
    print(f"[MATCH] User {user_id} added to pending")
    return jsonify({'success': False, 'message': '等待匹配中...'})

@app.route('/api/game/check', methods=['GET'])
def check_game_match():
    user_id = request.args.get('user_id', type=int)
    
    matches = load_json(MATCHES_FILE, [])
    pending = load_json(PENDING_FILE, [])
    
    print(f"[CHECK] User {user_id}: matches={len(matches)}, pending={len(pending)}")
    
    for m in matches:
        if not m['game_over'] and (m['player1'] == user_id or m['player2'] == user_id):
            print(f"[CHECK] User {user_id}: found in match {m['match_id']}")
            return jsonify({'in_match': True, 'match': m})
    
    for p in pending:
        if p['user_id'] == user_id:
            print(f"[CHECK] User {user_id}: found in pending")
            return jsonify({'in_match': False, 'matching': True})
    
    print(f"[CHECK] User {user_id}: not found, pending users={[p['user_id'] for p in pending]}")
    return jsonify({'in_match': False, 'matching': False})

@app.route('/api/game/students', methods=['GET'])
def get_students_game_status():
    conn = get_db()
    students = conn.execute("SELECT id, username, full_name FROM users WHERE role = 'student'").fetchall()
    conn.close()
    
    matches = load_json(MATCHES_FILE, [])
    pending = load_json(PENDING_FILE, [])
    
    results = []
    for s in students:
        status = 'offline'
        for p in pending:
            if p['user_id'] == s['id']:
                status = 'matching'
                break
        if status == 'offline':
            for m in matches:
                if not m['game_over'] and (m['player1'] == s['id'] or m['player2'] == s['id']):
                    status = 'playing'
                    break
        
        players = load_json(PLAYERS_FILE, [])
        player = next((p for p in players if p['user_id'] == s['id']), None)
        medals = player['medals'] if player else 0
        
        results.append({
            'id': s['id'],
            'username': s['username'],
            'full_name': s['full_name'] or s['username'],
            'status': status,
            'medals': medals
        })
    
    return jsonify({'students': results})

@app.route('/api/game/state', methods=['GET'])
def get_game_state():
    match_id = request.args.get('match_id')
    user_id = request.args.get('user_id', type=int)
    
    matches = load_json(MATCHES_FILE, [])
    match = None
    match_idx = -1
    for i, m in enumerate(matches):
        if m['match_id'] == match_id:
            match = m
            match_idx = i
            break
    
    if not match:
        return jsonify({'success': False, 'message': '比赛不存在'})
    
    if match['game_over']:
        return jsonify({'success': True, 'game_over': True, 'winner': match['winner']})
    
    is_p1 = match['player1'] == user_id
    opponent_id = match['player2'] if is_p1 else match['player1']
    
    # 检查对手是否离开（超时或其他原因）
    now = datetime.now()
    timeout_seconds = 90
    
    # 检查对手的最后活跃时间
    opponent_last_active_key = 'player2_last_active' if is_p1 else 'player1_last_active'
    opponent_last_active = match.get(opponent_last_active_key)
    player_last_active_key = 'player1_last_active' if is_p1 else 'player2_last_active'
    player_last_active = match.get(player_last_active_key)
    
    opponent_left = False
    if opponent_last_active:
        try:
            last_time = datetime.fromisoformat(opponent_last_active)
            if (now - last_time).total_seconds() > timeout_seconds:
                # 对手超时离开
                matches[match_idx]['game_over'] = True
                matches[match_idx]['winner'] = user_id
                save_json(MATCHES_FILE, matches)
                return jsonify({'success': True, 'game_over': True, 'winner': user_id, 'timeout': True, 'opponent_left': True})
        except:
            pass
    else:
        # 对手还没有发送过心跳
        # 如果是刚创建的游戏（双方都没有心跳），不视为离开
        if player_last_active is None:
            # 游戏刚创建，双方都没有心跳，这是正常的
            pass
        else:
            # 对手从来没有发送过心跳，但自己发送过
            # 这可能是对手在匹配后立即退出了
            # 不直接判定对手离开，而是继续游戏（让对手超时）
            pass
    
    # 获取当前题目的状态
    current_idx = match['current_question_idx']
    has_question = current_idx < len(match['questions'])
    
    current_q = None
    if has_question:
        q = match['questions'][current_idx]
        current_q = {
            'question': q['q'],
            'options': q['options'],
            'is_multi': q['is_multi']
        }
    
    hp = match['player1_hp'] if is_p1 else match['player2_hp']
    opponent_hp = match['player2_hp'] if is_p1 else match['player1_hp']
    
    # 检查双方是否都答题了
    both_answered = match['player1_answered'] and match['player2_answered']
    
    # 判断当前玩家是否已经答题
    player_answered = match['player1_answered'] if is_p1 else match['player2_answered']
    
    # 检查是否需要返回上一回合的结果
    last_round_result = match.get('last_round_result')
    
    if last_round_result:
        # 检查当前玩家是否已处理过上一回合结果
        processed_by = last_round_result.get('processed_by', [])
        if not isinstance(processed_by, list):
            processed_by = [processed_by] if processed_by else []
        
        # 如果当前玩家还没处理过，添加他到列表
        if user_id not in processed_by:
            processed_by.append(user_id)
            match['last_round_result']['processed_by'] = processed_by
            save_json(MATCHES_FILE, matches)
        
        # 返回上一回合结果（both_answered设为True，因为确实双方都答了）
        lrr = last_round_result
        is_p1 = match['player1'] == user_id
        return jsonify({
            'success': True,
            'game_over': False,
            'round_result': {
                'p1_correct': lrr['p1_correct'],
                'p2_correct': lrr['p2_correct'],
                'p1_dmg': lrr['p1_dmg'],
                'p2_dmg': lrr['p2_dmg'],
                'p1_hp': lrr['p1_hp'],
                'p2_hp': lrr['p2_hp']
            },
            'hp': lrr['p1_hp'] if is_p1 else lrr['p2_hp'],
            'opponent_hp': lrr['p2_hp'] if is_p1 else lrr['p1_hp'],
            'current_question': current_q,
            'current_question_idx': current_idx,
            'both_answered': True,  # 上一回合双方都答了
            'player_answered': True,  # 当前玩家已答上一题
            'total_questions': len(match['questions'])
        })
    
    return jsonify({
        'success': True,
        'game_over': False,
        'opponent_left': opponent_left,
        'hp': hp,
        'opponent_hp': opponent_hp,
        'current_question': current_q,
        'current_question_idx': current_idx,
        'both_answered': both_answered,
        'player_answered': player_answered,
        'total_questions': len(match['questions'])
    })

@app.route('/api/game/answer', methods=['POST'])
def submit_game_answer():
    data = request.get_json()
    match_id = data.get('match_id')
    user_id = data.get('user_id')
    answer = data.get('answer')
    is_correct = data.get('is_correct')
    
    matches = load_json(MATCHES_FILE, [])
    match = None
    match_idx = -1
    for i, m in enumerate(matches):
        if m['match_id'] == match_id:
            match = m
            match_idx = i
            break
    
    if not match or match['game_over']:
        return jsonify({'success': False, 'message': '比赛不存在或已结束'})
    
    is_p1 = match['player1'] == user_id
    
    # 更新答案状态
    if is_p1:
        match['player1_answer'] = answer
        match['player1_correct'] = is_correct
        match['player1_answered'] = True
    else:
        match['player2_answer'] = answer
        match['player2_correct'] = is_correct
        match['player2_answered'] = True
    
    # 检查双方是否都答题了
    round_result = None
    if match['player1_answered'] and match['player2_answered']:
        p1_correct = match['player1_correct']
        p2_correct = match['player2_correct']
        
        # 计算伤害
        dmg_p1 = 0
        dmg_p2 = 0
        
        if p1_correct and p2_correct:
            # 双方都对 - 都不掉血
            dmg_p1 = 0
            dmg_p2 = 0
        elif p1_correct and not p2_correct:
            # P1对P2错 - P2掉血
            dmg_p2 = 20
        elif not p1_correct and p2_correct:
            # P1错P2对 - P1掉血
            dmg_p1 = 20
        else:
            # 双方都错 - 各掉10血
            dmg_p1 = 10
            dmg_p2 = 10
        
        match['player1_hp'] = max(0, match['player1_hp'] - dmg_p1)
        match['player2_hp'] = max(0, match['player2_hp'] - dmg_p2)
        
        # 记录回合结果供双方查看
        match['last_round_result'] = {
            'p1_correct': p1_correct,
            'p2_correct': p2_correct,
            'p1_dmg': dmg_p1,
            'p2_dmg': dmg_p2,
            'p1_hp': match['player1_hp'],
            'p2_hp': match['player2_hp'],
            'question_idx': match['current_question_idx'],
            'processed_by': []
        }
        
        # 记录回合结果供前端显示
        round_result = {
            'p1_correct': p1_correct,
            'p2_correct': p2_correct,
            'p1_dmg': dmg_p1,
            'p2_dmg': dmg_p2,
            'p1_hp': match['player1_hp'],
            'p2_hp': match['player2_hp'],
            'question_idx': match['current_question_idx']
        }
        
        # 重置答题状态
        match['player1_answered'] = False
        match['player2_answered'] = False
        match['player1_answer'] = None
        match['player2_answer'] = None
        match['player1_correct'] = None
        match['player2_correct'] = None
        
        # 进入下一题
        match['current_question_idx'] += 1
        
        # 检查游戏是否结束
        if match['player1_hp'] <= 0 or match['player2_hp'] <= 0 or match['current_question_idx'] >= len(match['questions']):
            match['game_over'] = True
            if match['player1_hp'] > match['player2_hp']:
                match['winner'] = match['player1']
            elif match['player2_hp'] > match['player1_hp']:
                match['winner'] = match['player2']
            else:
                match['winner'] = 'draw'
            
            # 更新玩家统计
            if match['winner'] == match['player1']:
                update_player_stats(match['player1'], True)
                update_player_stats(match['player2'], False)
            elif match['winner'] == match['player2']:
                update_player_stats(match['player2'], True)
                update_player_stats(match['player1'], False)
    
    save_json(MATCHES_FILE, matches)
    
    response = {'success': True, 'player_answered': True}
    if round_result:
        response['round_result'] = round_result
    
    return jsonify(response)

def update_player_stats(user_id, won):
    import random
    players = load_json(PLAYERS_FILE, [])
    for p in players:
        if p['user_id'] == user_id:
            if won:
                p['wins'] = p.get('wins', 0) + 1
                p['medals'] = p.get('medals', 0) + 1
                p['gold'] = p.get('gold', 10) + random.randint(10, 20)
            break
    save_json(PLAYERS_FILE, players)

@app.route('/api/game/quit', methods=['POST'])
def quit_game():
    data = request.get_json()
    match_id = data.get('match_id')
    user_id = data.get('user_id')
    
    matches = load_json(MATCHES_FILE, [])
    for i, m in enumerate(matches):
        if m['match_id'] == match_id and not m['game_over']:
            matches[i]['game_over'] = True
            matches[i]['winner'] = m['player2'] if m['player1'] == user_id else m['player1']
            update_player_stats(matches[i]['winner'], True)
            save_json(MATCHES_FILE, matches)
            return jsonify({'success': True})
    
    return jsonify({'success': False, 'message': '比赛不存在'})

@app.route('/api/game/heartbeat', methods=['POST'])
def game_heartbeat():
    data = request.get_json()
    match_id = data.get('match_id')
    user_id = data.get('user_id')
    
    matches = load_json(MATCHES_FILE, [])
    for i, m in enumerate(matches):
        if m['match_id'] == match_id and not m['game_over']:
            if m['player1'] == user_id:
                matches[i]['player1_last_active'] = datetime.now().isoformat()
            elif m['player2'] == user_id:
                matches[i]['player2_last_active'] = datetime.now().isoformat()
            save_json(MATCHES_FILE, matches)
            return jsonify({'success': True})
    
    return jsonify({'success': False})

@app.route('/api/game/inventory', methods=['POST'])
def update_inventory():
    data = request.get_json()
    user_id = data.get('user_id')
    inventory = data.get('inventory', [])
    
    players = load_json(PLAYERS_FILE, [])
    for p in players:
        if p['user_id'] == user_id:
            p['inventory'] = inventory
            break
    save_json(PLAYERS_FILE, players)
    return jsonify({'success': True})

@app.route('/api/game/leaderboard', methods=['GET'])
def get_game_leaderboard():
    players = load_json(PLAYERS_FILE, [])
    sorted_players = sorted(players, key=lambda x: x.get('medals', 0), reverse=True)[:20]
    return jsonify({'leaderboard': sorted_players})

if __name__ == '__main__':
    init_db()
    print(f"\n{'='*50}")
    print(f"  LMS-Edge Flask API v3.1 Started!")
    print(f"{'='*50}")
    print(f"  Database: {DB_PATH}")
    print(f"  Static: {STATIC_DIR}")
    print(f"{'='*50}\n")
    app.run(host='0.0.0.0', port=8080, debug=False)
