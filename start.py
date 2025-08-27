#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
开发环境启动脚本
"""

import os
import sys

# 设置项目路径
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

# 切换到backend目录
os.chdir(backend_path)

if __name__ == '__main__':
    from app import app
    
    # 开发环境配置
    app.config['DEBUG'] = True
    
    print("启动开发服务器...")
    print("前端地址: 请使用浏览器打开 frontend/index.html")
    print("后端地址: http://127.0.0.1:5000")
    print("API文档: http://127.0.0.1:5000/health")
    
    app.run(host='127.0.0.1', port=5000, debug=True)
