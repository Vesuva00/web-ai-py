"""
日志配置模块
统一的日志格式和配置
"""

import logging
import os
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from typing import Optional

def setup_logger(
    name: str,
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> logging.Logger:
    """
    设置日志记录器
    
    Args:
        name: 日志记录器名称
        level: 日志级别
        log_file: 日志文件路径
        max_bytes: 日志文件最大大小
        backup_count: 备份文件数量
    
    Returns:
        配置好的日志记录器
    """
    
    # 创建日志记录器
    logger = logging.getLogger(name)
    
    # 避免重复添加处理器
    if logger.handlers:
        return logger
    
    logger.setLevel(level)
    
    # 创建格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 文件处理器
    if log_file:
        # 确保日志目录存在
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        
        # 使用轮转文件处理器
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def setup_application_logging():
    """设置应用程序的日志配置"""
    
    # 确保日志目录存在
    os.makedirs("logs", exist_ok=True)
    
    # 应用主日志
    app_logger = setup_logger(
        "app",
        level=logging.INFO,
        log_file="logs/app.log"
    )
    
    # API访问日志
    api_logger = setup_logger(
        "api",
        level=logging.INFO,
        log_file="logs/api.log"
    )
    
    # 工作流执行日志
    workflow_logger = setup_logger(
        "workflows",
        level=logging.INFO,
        log_file="logs/workflows.log"
    )
    
    # 安全日志
    security_logger = setup_logger(
        "security",
        level=logging.WARNING,
        log_file="logs/security.log"
    )
    
    # 错误日志
    error_logger = setup_logger(
        "errors",
        level=logging.ERROR,
        log_file="logs/errors.log"
    )
    
    return {
        "app": app_logger,
        "api": api_logger,
        "workflows": workflow_logger,
        "security": security_logger,
        "errors": error_logger
    }

class SecurityLogger:
    """安全日志记录器"""
    
    def __init__(self):
        self.logger = setup_logger(
            "security",
            level=logging.WARNING,
            log_file="logs/security.log"
        )
    
    def log_login_attempt(self, username: str, success: bool, ip_address: str = None):
        """记录登录尝试"""
        status = "成功" if success else "失败"
        message = f"登录尝试 - 用户: {username}, 状态: {status}"
        if ip_address:
            message += f", IP: {ip_address}"
        
        if success:
            self.logger.info(message)
        else:
            self.logger.warning(message)
    
    def log_invalid_token(self, token_prefix: str, ip_address: str = None):
        """记录无效token访问"""
        message = f"无效token访问 - Token前缀: {token_prefix[:8]}..."
        if ip_address:
            message += f", IP: {ip_address}"
        self.logger.warning(message)
    
    def log_rate_limit_exceeded(self, username: str, endpoint: str, ip_address: str = None):
        """记录速率限制超出"""
        message = f"速率限制超出 - 用户: {username}, 端点: {endpoint}"
        if ip_address:
            message += f", IP: {ip_address}"
        self.logger.warning(message)
    
    def log_suspicious_activity(self, description: str, username: str = None, ip_address: str = None):
        """记录可疑活动"""
        message = f"可疑活动 - {description}"
        if username:
            message += f", 用户: {username}"
        if ip_address:
            message += f", IP: {ip_address}"
        self.logger.warning(message)

class APILogger:
    """API访问日志记录器"""
    
    def __init__(self):
        self.logger = setup_logger(
            "api",
            level=logging.INFO,
            log_file="logs/api.log"
        )
    
    def log_request(
        self,
        method: str,
        path: str,
        status_code: int,
        response_time_ms: float,
        username: str = None,
        ip_address: str = None
    ):
        """记录API请求"""
        message = f"{method} {path} - {status_code} - {response_time_ms:.1f}ms"
        if username:
            message += f" - 用户: {username}"
        if ip_address:
            message += f" - IP: {ip_address}"
        
        if status_code < 400:
            self.logger.info(message)
        elif status_code < 500:
            self.logger.warning(message)
        else:
            self.logger.error(message)
    
    def log_workflow_execution(
        self,
        workflow_name: str,
        username: str,
        success: bool,
        execution_time_ms: float,
        error_message: str = None
    ):
        """记录工作流执行"""
        status = "成功" if success else "失败"
        message = f"工作流执行 - {workflow_name} - 用户: {username} - 状态: {status} - {execution_time_ms:.1f}ms"
        
        if error_message:
            message += f" - 错误: {error_message}"
        
        if success:
            self.logger.info(message)
        else:
            self.logger.error(message)

class PerformanceLogger:
    """性能监控日志记录器"""
    
    def __init__(self):
        self.logger = setup_logger(
            "performance",
            level=logging.INFO,
            log_file="logs/performance.log"
        )
    
    def log_slow_query(self, query: str, execution_time_ms: float, threshold_ms: float = 1000):
        """记录慢查询"""
        if execution_time_ms > threshold_ms:
            self.logger.warning(f"慢查询 - {execution_time_ms:.1f}ms - {query[:100]}...")
    
    def log_memory_usage(self, usage_mb: float, threshold_mb: float = 500):
        """记录内存使用"""
        if usage_mb > threshold_mb:
            self.logger.warning(f"高内存使用 - {usage_mb:.1f}MB")
    
    def log_api_performance(self, endpoint: str, avg_response_time_ms: float, request_count: int):
        """记录API性能统计"""
        self.logger.info(f"API性能 - {endpoint} - 平均响应时间: {avg_response_time_ms:.1f}ms - 请求数: {request_count}")

# 全局日志记录器实例
security_logger = SecurityLogger()
api_logger = APILogger()
performance_logger = PerformanceLogger()

# 导出主要类和函数
__all__ = [
    'setup_logger',
    'setup_application_logging',
    'SecurityLogger',
    'APILogger', 
    'PerformanceLogger',
    'security_logger',
    'api_logger',
    'performance_logger'
]
