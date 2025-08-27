"""
应用配置模块
管理系统配置、用户配置、邮件配置等
"""

import os
import json
import yaml
from typing import Dict, Any, List
from pydantic_settings import BaseSettings
from pydantic import EmailStr

class Settings(BaseSettings):
    """应用配置类"""
    
    # 基础配置
    APP_NAME: str = "AI工作流平台"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # 安全配置
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:8000", 
        "http://127.0.0.1:8000",
        "http://localhost:3000", 
        "http://127.0.0.1:3000"
    ]
    
    # 邮件配置
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    
    # Qwen API配置
    QWEN_API_KEY: str = ""
    QWEN_BASE_URL: str = "https://dashscope.aliyuncs.com/api/v1"
    
    # 数据库配置
    DATABASE_URL: str = "sqlite:///data/app.db"
    
    # 文件路径配置
    DATA_DIR: str = "data"
    CONFIG_DIR: str = "config"
    LOGS_DIR: str = "logs"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._ensure_directories()
        self._load_user_config()
    
    def _ensure_directories(self):
        """确保必要的目录存在"""
        for directory in [self.DATA_DIR, self.CONFIG_DIR, self.LOGS_DIR]:
            os.makedirs(directory, exist_ok=True)
    
    def _load_user_config(self):
        """加载用户配置"""
        user_config_path = os.path.join(self.CONFIG_DIR, "users.yaml")
        if not os.path.exists(user_config_path):
            # 创建默认用户配置文件
            self._create_default_user_config(user_config_path)
        
        try:
            with open(user_config_path, 'r', encoding='utf-8') as f:
                self._users_config = yaml.safe_load(f) or {}
        except Exception as e:
            print(f"加载用户配置失败: {e}")
            self._users_config = {}
    
    def _create_default_user_config(self, config_path: str):
        """创建默认用户配置文件"""
        default_config = {
            "users": {
                "admin": {
                    "email": "admin@example.com",
                    "role": "admin",
                    "enabled": True
                },
                "user1": {
                    "email": "user1@example.com", 
                    "role": "user",
                    "enabled": True
                }
            }
        }
        
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(default_config, f, default_flow_style=False, allow_unicode=True)
            print(f"已创建默认用户配置文件: {config_path}")
        except Exception as e:
            print(f"创建默认配置文件失败: {e}")
    
    def get_users(self) -> Dict[str, Dict[str, Any]]:
        """获取用户配置"""
        return self._users_config.get("users", {})
    
    def reload_user_config(self):
        """重新加载用户配置"""
        self._load_user_config()
    
    def validate_user(self, username: str) -> bool:
        """验证用户是否存在且启用"""
        users = self.get_users()
        if username not in users:
            return False
        return users[username].get("enabled", False)
    
    def get_user_email(self, username: str) -> str:
        """获取用户邮箱"""
        users = self.get_users()
        if username in users:
            return users[username].get("email", "")
        return ""

# 全局配置实例
settings = Settings()
