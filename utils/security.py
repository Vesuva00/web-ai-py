"""
安全工具模块
提供加密、验证和安全相关的实用函数
"""

import hashlib
import secrets
import string
import hmac
import time
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import ipaddress
import re

def generate_secure_token(length: int = 32) -> str:
    """生成安全的随机令牌"""
    return secrets.token_urlsafe(length)

def generate_daily_code() -> str:
    """生成6位数字验证码"""
    return ''.join(secrets.choice(string.digits) for _ in range(6))

def hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
    """
    安全哈希密码
    
    Args:
        password: 明文密码
        salt: 盐值，如果为None则生成新的盐值
    
    Returns:
        (hashed_password, salt)
    """
    if salt is None:
        salt = secrets.token_hex(16)
    
    # 使用PBKDF2-SHA256
    hashed = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000  # 迭代次数
    )
    
    return hashed.hex(), salt

def verify_password(password: str, hashed_password: str, salt: str) -> bool:
    """验证密码"""
    hashed, _ = hash_password(password, salt)
    return hmac.compare_digest(hashed, hashed_password)

def validate_email(email: str) -> bool:
    """验证邮箱格式"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_username(username: str) -> bool:
    """验证用户名格式"""
    # 只允许字母、数字、下划线，长度3-20
    pattern = r'^[a-zA-Z0-9_]{3,20}$'
    return re.match(pattern, username) is not None

def validate_ip_address(ip: str) -> bool:
    """验证IP地址格式"""
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False

def is_safe_redirect_url(url: str, allowed_hosts: list[str]) -> bool:
    """检查重定向URL是否安全"""
    if not url:
        return False
    
    # 检查是否为相对URL
    if url.startswith('/') and not url.startswith('//'):
        return True
    
    # 检查是否为允许的主机
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return parsed.netloc in allowed_hosts
    except Exception:
        return False

def sanitize_input(input_str: str, max_length: int = 1000) -> str:
    """清理用户输入"""
    if not isinstance(input_str, str):
        return ""
    
    # 移除控制字符
    sanitized = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', input_str)
    
    # 限制长度
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    # 移除首尾空白
    return sanitized.strip()

def check_rate_limit(
    identifier: str,
    max_attempts: int = 5,
    window_minutes: int = 15,
    storage: Optional[Dict[str, Any]] = None
) -> tuple[bool, int]:
    """
    检查速率限制
    
    Args:
        identifier: 标识符（如IP地址、用户名）
        max_attempts: 最大尝试次数
        window_minutes: 时间窗口（分钟）
        storage: 存储字典（简单实现，生产环境应使用Redis）
    
    Returns:
        (is_allowed, remaining_attempts)
    """
    if storage is None:
        # 这里应该使用持久化存储，如Redis
        # 为了简单起见，使用内存存储
        if not hasattr(check_rate_limit, '_storage'):
            check_rate_limit._storage = {}
        storage = check_rate_limit._storage
    
    now = datetime.now()
    window_start = now - timedelta(minutes=window_minutes)
    
    # 清理过期记录
    expired_keys = []
    for key, timestamps in storage.items():
        storage[key] = [ts for ts in timestamps if ts > window_start]
        if not storage[key]:
            expired_keys.append(key)
    
    for key in expired_keys:
        del storage[key]
    
    # 检查当前标识符的尝试次数
    attempts = storage.get(identifier, [])
    recent_attempts = [ts for ts in attempts if ts > window_start]
    
    if len(recent_attempts) >= max_attempts:
        return False, 0
    
    return True, max_attempts - len(recent_attempts)

def record_attempt(identifier: str, storage: Optional[Dict[str, Any]] = None):
    """记录尝试"""
    if storage is None:
        if not hasattr(check_rate_limit, '_storage'):
            check_rate_limit._storage = {}
        storage = check_rate_limit._storage
    
    now = datetime.now()
    if identifier not in storage:
        storage[identifier] = []
    
    storage[identifier].append(now)

def generate_csrf_token() -> str:
    """生成CSRF令牌"""
    return secrets.token_urlsafe(32)

def verify_csrf_token(token: str, expected_token: str) -> bool:
    """验证CSRF令牌"""
    return hmac.compare_digest(token, expected_token)

def create_secure_headers() -> Dict[str, str]:
    """创建安全HTTP头"""
    return {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline' cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' cdn.jsdelivr.net; font-src 'self' cdn.jsdelivr.net; img-src 'self' data:",
        "Referrer-Policy": "strict-origin-when-cross-origin"
    }

def mask_sensitive_data(data: str, mask_char: str = "*", visible_chars: int = 4) -> str:
    """掩码敏感数据"""
    if len(data) <= visible_chars:
        return mask_char * len(data)
    
    return data[:visible_chars] + mask_char * (len(data) - visible_chars)

def is_suspicious_activity(
    user_agent: str,
    ip_address: str,
    previous_ips: list[str] = None
) -> bool:
    """检测可疑活动"""
    suspicious_patterns = [
        r'bot', r'crawler', r'spider', r'scraper',
        r'curl', r'wget', r'python', r'requests'
    ]
    
    # 检查User-Agent
    if any(re.search(pattern, user_agent.lower()) for pattern in suspicious_patterns):
        return True
    
    # 检查IP地址变化
    if previous_ips and len(set(previous_ips[-10:])) > 5:  # 最近10次访问中IP变化超过5次
        return True
    
    return False

class SecurityAuditor:
    """安全审计器"""
    
    def __init__(self):
        self.suspicious_events = []
    
    def log_suspicious_event(
        self,
        event_type: str,
        description: str,
        user_id: str = None,
        ip_address: str = None,
        metadata: Dict[str, Any] = None
    ):
        """记录可疑事件"""
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "description": description,
            "user_id": user_id,
            "ip_address": ip_address,
            "metadata": metadata or {}
        }
        
        self.suspicious_events.append(event)
        
        # 这里应该发送到安全监控系统
        print(f"[SECURITY ALERT] {event_type}: {description}")
    
    def check_login_pattern(self, user_id: str, success: bool, ip_address: str):
        """检查登录模式"""
        # 实现登录模式分析逻辑
        pass
    
    def analyze_api_usage(self, user_id: str, endpoint: str, frequency: int):
        """分析API使用模式"""
        # 实现API使用分析逻辑
        pass

# 全局安全审计器实例
security_auditor = SecurityAuditor()

# 导出主要函数
__all__ = [
    'generate_secure_token',
    'generate_daily_code',
    'hash_password',
    'verify_password',
    'validate_email',
    'validate_username',
    'validate_ip_address',
    'is_safe_redirect_url',
    'sanitize_input',
    'check_rate_limit',
    'record_attempt',
    'generate_csrf_token',
    'verify_csrf_token',
    'create_secure_headers',
    'mask_sensitive_data',
    'is_suspicious_activity',
    'SecurityAuditor',
    'security_auditor'
]
