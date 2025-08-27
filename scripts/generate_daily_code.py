#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日验证码生成脚本
建议配置为每日凌晨自动执行的定时任务
"""

import os
import sys
from datetime import datetime, date

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app import app
from auth import DailyCodeService

def generate_daily_code():
    """生成并发送每日验证码"""
    with app.app_context():
        try:
            today = date.today()
            daily_code = DailyCodeService.get_or_create_daily_code(today)
            
            print(f"[{datetime.now()}] 每日验证码生成成功")
            print(f"日期: {today}")
            print(f"验证码: {daily_code.code}")
            
            return True
            
        except Exception as e:
            print(f"[{datetime.now()}] 每日验证码生成失败: {e}")
            return False

if __name__ == '__main__':
    success = generate_daily_code()
    sys.exit(0 if success else 1)
