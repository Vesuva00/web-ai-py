#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库模型定义
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Index

# 这里需要从app.py导入db实例，但为了避免循环导入，我们使用延迟初始化
db = SQLAlchemy()

def init_db(database):
    global db
    db = database

class User(db.Model):
    """用户模型"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_login = db.Column(db.DateTime)
    
    # 关联关系
    workflow_calls = db.relationship('WorkflowCall', backref='user', lazy=True)
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'last_login': self.last_login.isoformat() if self.last_login else None
        }

class DailyCode(db.Model):
    """每日验证码模型"""
    __tablename__ = 'daily_codes'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(10), unique=True, nullable=False, index=True)
    date = db.Column(db.Date, nullable=False, index=True)
    is_used = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    used_at = db.Column(db.DateTime)
    used_by_ip = db.Column(db.String(45))  # 支持IPv6
    
    # 创建复合索引以优化查询性能
    __table_args__ = (
        Index('idx_date_code', 'date', 'code'),
        Index('idx_date_used', 'date', 'is_used'),
    )
    
    def __repr__(self):
        return f'<DailyCode {self.code} for {self.date}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'date': self.date.isoformat(),
            'is_used': self.is_used,
            'created_at': self.created_at.isoformat(),
            'used_at': self.used_at.isoformat() if self.used_at else None,
            'used_by_ip': self.used_by_ip
        }

class WorkflowCall(db.Model):
    """工作流调用记录模型"""
    __tablename__ = 'workflow_calls'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    workflow_type = db.Column(db.String(50), nullable=False, index=True)
    input_data = db.Column(db.Text, nullable=False)  # JSON格式存储输入数据
    output_data = db.Column(db.Text)  # JSON格式存储输出数据
    status = db.Column(db.String(20), default='pending', nullable=False, index=True)  # pending, success, failed
    error_message = db.Column(db.Text)
    execution_time = db.Column(db.Float)  # 执行时间（秒）
    tokens_used = db.Column(db.Integer)  # 使用的token数量
    ip_address = db.Column(db.String(45), nullable=False)  # 客户端IP
    user_agent = db.Column(db.Text)  # 用户代理字符串
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    completed_at = db.Column(db.DateTime)
    
    # 创建复合索引以优化查询性能
    __table_args__ = (
        Index('idx_user_workflow', 'user_id', 'workflow_type'),
        Index('idx_status_created', 'status', 'created_at'),
        Index('idx_workflow_created', 'workflow_type', 'created_at'),
    )
    
    def __repr__(self):
        return f'<WorkflowCall {self.workflow_type} by User {self.user_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'workflow_type': self.workflow_type,
            'status': self.status,
            'execution_time': self.execution_time,
            'tokens_used': self.tokens_used,
            'ip_address': self.ip_address,
            'created_at': self.created_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'error_message': self.error_message
        }

class SystemLog(db.Model):
    """系统日志模型"""
    __tablename__ = 'system_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    level = db.Column(db.String(10), nullable=False, index=True)  # INFO, WARN, ERROR
    message = db.Column(db.Text, nullable=False)
    module = db.Column(db.String(50), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    ip_address = db.Column(db.String(45))
    extra_data = db.Column(db.Text)  # JSON格式存储额外数据
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # 创建复合索引以优化查询性能
    __table_args__ = (
        Index('idx_level_created', 'level', 'created_at'),
        Index('idx_module_created', 'module', 'created_at'),
    )
    
    def __repr__(self):
        return f'<SystemLog {self.level}: {self.message[:50]}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'level': self.level,
            'message': self.message,
            'module': self.module,
            'user_id': self.user_id,
            'ip_address': self.ip_address,
            'created_at': self.created_at.isoformat()
        }
