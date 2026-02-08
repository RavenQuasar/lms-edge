#!/usr/bin/env python3
"""Initialize game database with default users"""
import sqlite3
import os

DB_PATH = '/home/raven/lms-edge/backend/data/lms.db'
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Create users table (matching app_api.py schema)
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    full_name TEXT,
    role TEXT DEFAULT 'student',
    avatar TEXT
)
''')

# Create assignments table
cursor.execute('''
CREATE TABLE IF NOT EXISTS assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    content TEXT,
    assignment_type TEXT DEFAULT 'normal',
    options TEXT,
    correct_answer TEXT,
    points INTEGER DEFAULT 10,
    attachment TEXT,
    created_by INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

# Create submissions table
cursor.execute('''
CREATE TABLE IF NOT EXISTS submissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    assignment_id INTEGER,
    student_answer TEXT,
    score INTEGER,
    is_correct INTEGER,
    submitted_at TIMESTAMP,
    attachment TEXT
)
''')

# Create attendance table
cursor.execute('''
CREATE TABLE IF NOT EXISTS attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    date DATE,
    status TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

# Insert default users if they don't exist
users = [
    (1, 'admin', 'admin123', '系统管理员', 'admin', None),
    (2, 'teacher', 'teacher123', '教师', 'teacher', None),
    (3, 'student', 'student123', '学生', 'student', None),
    (8, 'U1', '123456', '王五', 'student', None),
    (9, 'U2', '123456', '马六', 'student', None),
]

for user in users:
    try:
        cursor.execute('INSERT OR IGNORE INTO users (id, username, password, full_name, role, avatar) VALUES (?, ?, ?, ?, ?, ?)', user)
    except:
        pass

conn.commit()
print('Database initialized!')
print('Users created:')
cursor.execute('SELECT id, username, full_name, role FROM users')
for row in cursor.fetchall():
    print(f'  ID:{row[0]} {row[1]} ({row[2]}) - {row[3]}')

conn.close()
