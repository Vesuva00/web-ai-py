#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库初始化脚本
"""

import os
import sys
from datetime import datetime
from werkzeug.security import generate_password_hash

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import User, DailyCode, WorkflowCall, SystemLog
from auth import DailyCodeService

def init_database():
    """初始化数据库和基础数据"""
    with app.app_context():
        # 创建所有表
        db.create_all()
        print("数据库表创建完成")
        
        # 创建管理员用户（可选）
        admin_username = os.getenv('ADMIN_USERNAME', 'admin')
        admin_email = os.getenv('ADMIN_EMAIL', 'admin@example.com')
        admin_password = os.getenv('ADMIN_PASSWORD', 'admin123456')
        
        if not User.query.filter_by(username=admin_username).first():
            admin_user = User(
                username=admin_username,
                email=admin_email,
                password_hash=generate_password_hash(admin_password)
            )
            db.session.add(admin_user)
            db.session.commit()
            print(f"管理员用户创建完成: {admin_username}")
        
        # 生成当日验证码
        try:
            daily_code = DailyCodeService.get_or_create_daily_code()
            print(f"当日验证码: {daily_code.code}")
        except Exception as e:
            print(f"生成验证码失败: {e}")
        
        print("数据库初始化完成")

if __name__ == '__main__':
    init_database()
