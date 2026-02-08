#!/usr/bin/env python3
"""
LMS-Edge Simple Password Hash - 不需要 bcrypt
"""

import hashlib

def hash_password(password):
    """简单哈希密码"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, password_hash):
    """验证密码"""
    return hash_password(password) == password_hash

if __name__ == '__main__':
    # 测试
    pwd = "admin123"
    hashed = hash_password(pwd)
    print(f"Original: {pwd}")
    print(f"Hashed: {hashed}")
    print(f"Verified: {verify_password(pwd, hashed)}")
