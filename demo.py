#!/usr/bin/env python3
"""
AI工作流平台演示脚本
展示系统的主要功能和API使用方法
"""

import asyncio
import aiohttp
import json
import sys
from datetime import datetime
from typing import Dict, Any

# 配置
BASE_URL = "http://localhost:8000"
DEMO_USER = "admin"
DEMO_CODE = "123456"  # 在实际环境中，这将是每日生成的验证码

class APIDemo:
    """API演示类"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = None
        self.access_token = None
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()
    
    async def login(self, username: str, daily_code: str) -> bool:
        """用户登录"""
        print(f"🔐 正在登录用户: {username}")
        
        try:
            async with self.session.post(
                f"{self.base_url}/api/auth/login",
                json={"username": username, "daily_code": daily_code},
                headers={"Content-Type": "application/json"}
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    self.access_token = result["access_token"]
                    print(f"✅ 登录成功！用户: {result['username']}")
                    return True
                else:
                    error = await response.json()
                    print(f"❌ 登录失败: {error.get('detail', '未知错误')}")
                    return False
                    
        except Exception as e:
            print(f"❌ 登录请求失败: {e}")
            return False
    
    async def get_user_info(self) -> Dict[str, Any]:
        """获取用户信息"""
        print("👤 获取用户信息...")
        
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            async with self.session.get(
                f"{self.base_url}/api/auth/me",
                headers=headers
            ) as response:
                
                if response.status == 200:
                    user_info = await response.json()
                    print(f"✅ 用户信息: {user_info}")
                    return user_info
                else:
                    print(f"❌ 获取用户信息失败: {response.status}")
                    return {}
                    
        except Exception as e:
            print(f"❌ 请求失败: {e}")
            return {}
    
    async def get_workflows(self) -> list:
        """获取可用工作流"""
        print("📋 获取可用工作流列表...")
        
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            async with self.session.get(
                f"{self.base_url}/api/workflows",
                headers=headers
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    workflows = result["workflows"]
                    print(f"✅ 发现 {len(workflows)} 个可用工作流:")
                    
                    for workflow in workflows:
                        print(f"  📝 {workflow['name']}: {workflow['description']}")
                    
                    return workflows
                else:
                    print(f"❌ 获取工作流失败: {response.status}")
                    return []
                    
        except Exception as e:
            print(f"❌ 请求失败: {e}")
            return []
    
    async def execute_poem_workflow(self, theme: str, style: str = "现代", length: str = "中等") -> Dict[str, Any]:
        """执行诗歌生成工作流"""
        print(f"🎨 正在生成诗歌...")
        print(f"   主题: {theme}")
        print(f"   风格: {style}")
        print(f"   长度: {length}")
        
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "workflow_type": "poem",
                "inputs": {
                    "theme": theme,
                    "style": style,
                    "length": length
                }
            }
            
            async with self.session.post(
                f"{self.base_url}/api/workflows/execute",
                json=payload,
                headers=headers
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    if result["success"]:
                        outputs = result["result"]["outputs"]
                        print("✅ 诗歌生成成功！")
                        print("=" * 50)
                        print(f"📖 {outputs['title']}")
                        print("-" * 30)
                        print(outputs['poem'])
                        print("-" * 30)
                        print(f"💭 创作说明: {outputs['analysis']}")
                        
                        metadata = outputs['metadata']
                        print(f"📊 统计: {metadata['line_count']}行, {metadata['word_count']}字, {metadata['style']}风格")
                        print("=" * 50)
                        
                        return outputs
                    else:
                        print(f"❌ 工作流执行失败")
                        return {}
                else:
                    error = await response.json()
                    print(f"❌ 请求失败: {error.get('detail', '未知错误')}")
                    return {}
                    
        except Exception as e:
            print(f"❌ 请求失败: {e}")
            return {}
    
    async def get_logs(self, limit: int = 10) -> list:
        """获取活动日志"""
        print(f"📊 获取最近 {limit} 条活动日志...")
        
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            async with self.session.get(
                f"{self.base_url}/api/admin/logs?limit={limit}",
                headers=headers
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    logs = result["logs"]
                    print(f"✅ 获取到 {len(logs)} 条日志:")
                    
                    for log in logs[:5]:  # 只显示前5条
                        print(f"  🕒 {log['timestamp'][:19]} | {log['username']} | {log['activity_type']}")
                    
                    return logs
                else:
                    print(f"❌ 获取日志失败: {response.status}")
                    return []
                    
        except Exception as e:
            print(f"❌ 请求失败: {e}")
            return []

async def run_demo():
    """运行演示"""
    print("🚀 AI工作流平台演示程序")
    print("=" * 60)
    
    # 检查服务是否可用
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BASE_URL}/") as response:
                if response.status != 200:
                    print("❌ 服务不可用，请确保服务器已启动")
                    print(f"   访问地址: {BASE_URL}")
                    return
    except Exception as e:
        print(f"❌ 无法连接到服务器: {e}")
        print(f"   请确保服务器在 {BASE_URL} 上运行")
        return
    
    print("✅ 服务器连接正常")
    print()
    
    async with APIDemo(BASE_URL) as demo:
        # 1. 用户登录
        if not await demo.login(DEMO_USER, DEMO_CODE):
            print("💡 提示: 在实际环境中，验证码会每日通过邮件发送")
            return
        
        print()
        
        # 2. 获取用户信息
        await demo.get_user_info()
        print()
        
        # 3. 获取工作流列表
        workflows = await demo.get_workflows()
        print()
        
        # 4. 演示诗歌生成工作流
        if workflows:
            themes = [
                ("春天", "古典", "短诗"),
                ("友情", "现代", "中等"),
                ("月夜", "自由诗", "短诗")
            ]
            
            for theme, style, length in themes:
                await demo.execute_poem_workflow(theme, style, length)
                print()
                await asyncio.sleep(1)  # 避免请求过快
        
        # 5. 获取活动日志
        await demo.get_logs()
        print()
    
    print("✨ 演示完成！")
    print()
    print("📌 接下来你可以:")
    print("   1. 访问 http://localhost:8000 使用Web界面")
    print("   2. 修改 config/users.yaml 添加更多用户")
    print("   3. 在 workflows/ 目录下添加新的工作流")
    print("   4. 查看 logs/ 目录下的详细日志")

def create_test_data():
    """创建测试数据"""
    import os
    import json
    from datetime import datetime
    
    # 确保data目录存在
    os.makedirs("data", exist_ok=True)
    
    # 创建测试用的每日验证码
    daily_codes = {
        DEMO_USER: {
            "code": DEMO_CODE,
            "generated_at": datetime.now().isoformat(),
            "email": "admin@example.com"
        }
    }
    
    with open("data/daily_codes.json", "w", encoding="utf-8") as f:
        json.dump(daily_codes, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 已创建测试验证码: {DEMO_CODE}")

async def main():
    """主函数"""
    print("🎯 AI工作流平台演示")
    print()
    
    # 检查参数
    if len(sys.argv) > 1:
        if sys.argv[1] == "--create-test-data":
            create_test_data()
            return
        elif sys.argv[1] == "--help":
            print("用法:")
            print("  python demo.py                  # 运行演示")
            print("  python demo.py --create-test-data  # 创建测试数据")
            print("  python demo.py --help           # 显示帮助")
            return
    
    # 提示用户
    print("💡 演示说明:")
    print("   1. 请确保服务器已启动 (python start.py)")
    print("   2. 如果是首次运行，请先创建测试数据:")
    print("      python demo.py --create-test-data")
    print()
    
    # 询问是否继续
    try:
        input("按 Enter 键开始演示，或 Ctrl+C 退出...")
    except KeyboardInterrupt:
        print("\n演示已取消")
        return
    
    print()
    await run_demo()

if __name__ == "__main__":
    asyncio.run(main())
