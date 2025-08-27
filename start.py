#!/usr/bin/env python3
"""
启动脚本
快速启动AI工作流平台
"""

import os
import sys
import subprocess
import asyncio
from pathlib import Path

def check_python_version():
    """检查Python版本"""
    if sys.version_info < (3, 8):
        print("错误: 需要Python 3.8或更高版本")
        sys.exit(1)

def install_dependencies():
    """安装依赖包"""
    print("正在安装依赖包...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("依赖包安装完成")
    except subprocess.CalledProcessError as e:
        print(f"依赖包安装失败: {e}")
        sys.exit(1)

def check_env_file():
    """检查环境配置文件"""
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists():
        if env_example.exists():
            print("未找到.env文件，正在从.env.example创建...")
            env_file.write_text(env_example.read_text(encoding="utf-8"), encoding="utf-8")
            print("已创建.env文件，请根据需要修改配置")
        else:
            print("警告: 未找到环境配置文件")

def create_directories():
    """创建必要的目录"""
    directories = ["data", "logs", "config"]
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
    print("目录结构创建完成")

async def init_database():
    """初始化数据库"""
    print("正在初始化数据库...")
    try:
        from database.models import init_database
        await init_database()
        print("数据库初始化完成")
    except Exception as e:
        print(f"数据库初始化失败: {e}")
        sys.exit(1)

def start_server():
    """启动服务器"""
    print("正在启动服务器...")
    print("=" * 50)
    print("AI工作流平台正在启动...")
    print("访问地址: http://localhost:8000")
    print("按 Ctrl+C 停止服务器")
    print("=" * 50)
    
    try:
        import uvicorn
        uvicorn.run(
            "backend.app:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except ImportError:
        print("错误: uvicorn未安装，请运行 pip install uvicorn")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n服务器已停止")
    except Exception as e:
        print(f"服务器启动失败: {e}")
        sys.exit(1)

def main():
    """主函数"""
    print("AI工作流平台启动程序")
    print("=" * 30)
    
    # 检查Python版本
    check_python_version()
    
    # 创建目录结构
    create_directories()
    
    # 检查环境文件
    check_env_file()
    
    # 安装依赖
    if "--install-deps" in sys.argv or not Path("venv").exists():
        install_dependencies()
    
    # 初始化数据库
    try:
        asyncio.run(init_database())
    except Exception as e:
        print(f"数据库初始化失败: {e}")
        print("请检查配置并重试")
        sys.exit(1)
    
    # 启动服务器
    start_server()

if __name__ == "__main__":
    main()
