#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
认证模块 - 处理用户认证、每日验证码生成和验证
"""

import os
import secrets
import string
import smtplib
import json
import logging
from datetime import datetime, date, timedelta
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from email_validator import validate_email, EmailNotValidError

from models import db, User, DailyCode, SystemLog

logger = logging.getLogger(__name__)
auth_bp = Blueprint('auth', __name__)

class EmailService:
    """邮件服务类"""
    
    @staticmethod
    def send_daily_code(code, target_date):
        """发送每日验证码到管理员邮箱"""
        try:
            # 邮件配置
            smtp_server = os.getenv('MAIL_SERVER')
            smtp_port = int(os.getenv('MAIL_PORT', 587))
            use_tls = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
            username = os.getenv('MAIL_USERNAME')
            password = os.getenv('MAIL_PASSWORD')
            admin_email = os.getenv('ADMIN_EMAIL')
            
            if not all([smtp_server, username, password, admin_email]):
                logger.error('邮件配置不完整')
                return False
            
            # 创建邮件内容
            msg = MimeMultipart()
            msg['From'] = username
            msg['To'] = admin_email
            msg['Subject'] = f'每日访问验证码 - {target_date}'
            
            body = f"""
            <html>
            <body>
                <h2>AI工作流系统 - 每日访问验证码</h2>
                <p><strong>日期：</strong>{target_date}</p>
                <p><strong>验证码：</strong><span style="font-size: 20px; font-weight: bold; color: #007bff;">{code}</span></p>
                <p><strong>有效期：</strong>当日24小时内有效</p>
                <hr>
                <p style="color: #666; font-size: 12px;">
                    此验证码用于访问AI工作流系统，请妥善保管。
                    <br>系统时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                </p>
            </body>
            </html>
            """
            
            msg.attach(MimeText(body, 'html', 'utf-8'))
            
            # 发送邮件
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                if use_tls:
                    server.starttls()
                server.login(username, password)
                server.send_message(msg)
            
            logger.info(f'每日验证码已发送到 {admin_email}')
            return True
            
        except Exception as e:
            logger.error(f'发送邮件失败: {str(e)}')
            return False

class DailyCodeService:
    """每日验证码服务类"""
    
    @staticmethod
    def generate_code(length=8):
        """生成随机验证码"""
        # 使用数字和大写字母，避免易混淆字符
        characters = string.ascii_uppercase + string.digits
        characters = characters.replace('0', '').replace('O', '').replace('1', '').replace('I', '')
        return ''.join(secrets.choice(characters) for _ in range(length))
    
    @staticmethod
    def get_or_create_daily_code(target_date=None):
        """获取或创建指定日期的验证码"""
        if target_date is None:
            target_date = date.today()
        
        # 查找当日验证码
        daily_code = DailyCode.query.filter_by(date=target_date).first()
        
        if daily_code:
            return daily_code
        
        # 生成新的验证码
        while True:
            code = DailyCodeService.generate_code()
            # 确保验证码唯一
            if not DailyCode.query.filter_by(code=code).first():
                break
        
        # 创建新记录
        daily_code = DailyCode(
            code=code,
            date=target_date
        )
        
        db.session.add(daily_code)
        db.session.commit()
        
        # 发送邮件
        EmailService.send_daily_code(code, target_date.strftime('%Y-%m-%d'))
        
        logger.info(f'生成新的每日验证码: {code} for {target_date}')
        return daily_code
    
    @staticmethod
    def verify_code(code, ip_address):
        """验证当日验证码"""
        today = date.today()
        daily_code = DailyCode.query.filter_by(
            code=code.upper(),
            date=today,
            is_used=False
        ).first()
        
        if not daily_code:
            return False
        
        # 标记为已使用
        daily_code.is_used = True
        daily_code.used_at = datetime.utcnow()
        daily_code.used_by_ip = ip_address
        
        db.session.commit()
        
        logger.info(f'验证码 {code} 验证成功，IP: {ip_address}')
        return True

@auth_bp.route('/register', methods=['POST'])
def register():
    """用户注册"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': '请提供注册信息'}), 400
        
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        # 验证输入
        if not username or len(username) < 3:
            return jsonify({'error': '用户名至少需要3个字符'}), 400
        
        if not email:
            return jsonify({'error': '请提供邮箱地址'}), 400
        
        if not password or len(password) < 6:
            return jsonify({'error': '密码至少需要6个字符'}), 400
        
        # 验证邮箱格式
        try:
            valid = validate_email(email)
            email = valid.email
        except EmailNotValidError:
            return jsonify({'error': '邮箱格式不正确'}), 400
        
        # 检查用户名和邮箱是否已存在
        if User.query.filter_by(username=username).first():
            return jsonify({'error': '用户名已存在'}), 400
        
        if User.query.filter_by(email=email).first():
            return jsonify({'error': '邮箱已注册'}), 400
        
        # 创建用户
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        
        db.session.add(user)
        db.session.commit()
        
        # 记录日志
        SystemLog.log_info(
            message=f'新用户注册: {username}',
            module='auth',
            user_id=user.id,
            ip_address=request.remote_addr
        )
        
        logger.info(f'新用户注册成功: {username} ({email})')
        
        return jsonify({
            'message': '注册成功',
            'user': user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'用户注册失败: {str(e)}')
        return jsonify({'error': '注册失败，请稍后重试'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """用户登录"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': '请提供登录信息'}), 400
        
        username = data.get('username', '').strip()
        password = data.get('password', '')
        daily_code = data.get('daily_code', '').strip()
        
        if not all([username, password, daily_code]):
            return jsonify({'error': '请提供用户名、密码和每日验证码'}), 400
        
        # 查找用户
        user = User.query.filter_by(username=username, is_active=True).first()
        
        if not user or not check_password_hash(user.password_hash, password):
            SystemLog.log_warn(
                message=f'登录失败: 用户名或密码错误 - {username}',
                module='auth',
                ip_address=request.remote_addr
            )
            return jsonify({'error': '用户名或密码错误'}), 401
        
        # 验证每日验证码
        if not DailyCodeService.verify_code(daily_code, request.remote_addr):
            SystemLog.log_warn(
                message=f'登录失败: 验证码错误 - {username}',
                module='auth',
                user_id=user.id,
                ip_address=request.remote_addr
            )
            return jsonify({'error': '验证码错误或已使用'}), 401
        
        # 更新最后登录时间
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        # 创建访问令牌
        access_token = create_access_token(
            identity=user.id,
            additional_claims={'username': user.username}
        )
        
        # 记录成功登录日志
        SystemLog.log_info(
            message=f'用户登录成功: {username}',
            module='auth',
            user_id=user.id,
            ip_address=request.remote_addr
        )
        
        logger.info(f'用户登录成功: {username}')
        
        return jsonify({
            'message': '登录成功',
            'access_token': access_token,
            'user': user.to_dict()
        })
        
    except Exception as e:
        logger.error(f'用户登录失败: {str(e)}')
        return jsonify({'error': '登录失败，请稍后重试'}), 500

@auth_bp.route('/verify-token', methods=['POST'])
@jwt_required()
def verify_token():
    """验证访问令牌"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or not user.is_active:
            return jsonify({'error': '用户不存在或已禁用'}), 401
        
        return jsonify({
            'valid': True,
            'user': user.to_dict()
        })
        
    except Exception as e:
        logger.error(f'令牌验证失败: {str(e)}')
        return jsonify({'error': '令牌验证失败'}), 401

@auth_bp.route('/daily-code/generate', methods=['POST'])
def generate_daily_code():
    """生成当日验证码（管理员接口）"""
    try:
        # 这里可以添加管理员验证逻辑
        daily_code = DailyCodeService.get_or_create_daily_code()
        
        return jsonify({
            'message': '验证码生成成功',
            'code': daily_code.code,
            'date': daily_code.date.isoformat()
        })
        
    except Exception as e:
        logger.error(f'生成验证码失败: {str(e)}')
        return jsonify({'error': '生成验证码失败'}), 500

# 扩展SystemLog模型以添加便捷的日志方法
def log_info(message, module, user_id=None, ip_address=None, extra_data=None):
    """记录信息日志"""
    log = SystemLog(
        level='INFO',
        message=message,
        module=module,
        user_id=user_id,
        ip_address=ip_address,
        extra_data=json.dumps(extra_data) if extra_data else None
    )
    db.session.add(log)
    db.session.commit()

def log_warn(message, module, user_id=None, ip_address=None, extra_data=None):
    """记录警告日志"""
    log = SystemLog(
        level='WARN',
        message=message,
        module=module,
        user_id=user_id,
        ip_address=ip_address,
        extra_data=json.dumps(extra_data) if extra_data else None
    )
    db.session.add(log)
    db.session.commit()

def log_error(message, module, user_id=None, ip_address=None, extra_data=None):
    """记录错误日志"""
    log = SystemLog(
        level='ERROR',
        message=message,
        module=module,
        user_id=user_id,
        ip_address=ip_address,
        extra_data=json.dumps(extra_data) if extra_data else None
    )
    db.session.add(log)
    db.session.commit()

# 将日志方法添加到SystemLog类
SystemLog.log_info = staticmethod(log_info)
SystemLog.log_warn = staticmethod(log_warn)
SystemLog.log_error = staticmethod(log_error)
