#!/usr/bin/env python3
"""
动态工作流系统测试脚本
演示前端如何根据后端配置自动渲染工作流界面
"""

import asyncio
import aiohttp
import json
import sys
import time
from typing import Dict, Any

# 配置
BASE_URL = "http://localhost:8000"
DEMO_USER = "admin"
DEMO_CODE = "123456"

class DynamicWorkflowDemo:
    """动态工作流演示类"""
    
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
        try:
            async with self.session.post(
                f"{self.base_url}/api/auth/login",
                json={"username": username, "daily_code": daily_code},
                headers={"Content-Type": "application/json"}
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    self.access_token = result["access_token"]
                    return True
                else:
                    return False
                    
        except Exception as e:
            print(f"❌ 登录失败: {e}")
            return False
    
    async def get_workflows(self) -> list:
        """获取工作流列表"""
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            async with self.session.get(
                f"{self.base_url}/api/workflows",
                headers=headers
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    return result["workflows"]
                else:
                    return []
                    
        except Exception as e:
            print(f"❌ 获取工作流失败: {e}")
            return []
    
    async def execute_workflow(self, workflow_name: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """执行工作流"""
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "workflow_type": workflow_name,
                "inputs": inputs
            }
            
            async with self.session.post(
                f"{self.base_url}/api/workflows/execute",
                json=payload,
                headers=headers
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    return result
                else:
                    error = await response.json()
                    print(f"❌ 工作流执行失败: {error.get('detail', '未知错误')}")
                    return {}
                    
        except Exception as e:
            print(f"❌ 工作流执行请求失败: {e}")
            return {}

def print_workflow_info(workflow):
    """打印工作流信息"""
    print(f"\n📋 工作流: {workflow['name']}")
    print(f"   描述: {workflow['description']}")
    print(f"   版本: {workflow['version']}")
    
    # 显示输入参数结构
    input_schema = workflow.get('input_schema', {})
    properties = input_schema.get('properties', {})
    required = input_schema.get('required', [])
    
    if properties:
        print("   📥 输入参数:")
        for field_name, field_schema in properties.items():
            required_mark = " *" if field_name in required else ""
            field_type = field_schema.get('type', 'unknown')
            field_desc = field_schema.get('description', field_name)
            print(f"      - {field_desc} ({field_type}){required_mark}")
            
            # 显示枚举值
            if 'enum' in field_schema:
                print(f"        选项: {', '.join(field_schema['enum'])}")
            
            # 显示默认值
            if 'default' in field_schema:
                print(f"        默认值: {field_schema['default']}")
    else:
        print("   📥 无需输入参数")
    
    # 显示输出结构
    output_schema = workflow.get('output_schema', {})
    output_properties = output_schema.get('properties', {})
    
    if output_properties:
        print("   📤 输出结果:")
        for field_name, field_schema in output_properties.items():
            field_type = field_schema.get('type', 'unknown')
            field_desc = field_schema.get('description', field_name)
            print(f"      - {field_desc} ({field_type})")
    
    # 显示统计信息
    stats = workflow.get('stats', {})
    if stats and stats.get('total_executions', 0) > 0:
        print(f"   📊 使用统计:")
        print(f"      - 总执行次数: {stats['total_executions']}")
        print(f"      - 成功次数: {stats['successful_executions']}")
        print(f"      - 平均执行时间: {stats.get('average_execution_time', 0):.2f}秒")

def create_test_inputs(workflow):
    """为工作流创建测试输入"""
    input_schema = workflow.get('input_schema', {})
    properties = input_schema.get('properties', {})
    
    if not properties:
        return {}
    
    inputs = {}
    
    for field_name, field_schema in properties.items():
        field_type = field_schema.get('type', 'string')
        
        # 根据字段类型和名称创建测试数据
        if field_name == 'theme' and workflow['name'] == 'poem':
            inputs[field_name] = "春天的花朵"
        elif field_name == 'style' and workflow['name'] == 'poem':
            inputs[field_name] = "现代"
        elif field_name == 'length' and workflow['name'] == 'poem':
            inputs[field_name] = "短诗"
        elif field_name == 'text' and workflow['name'] == 'text_analyzer':
            inputs[field_name] = """人工智能技术正在快速发展，深刻改变着我们的生活方式。
从智能手机到自动驾驶汽车，从语音助手到医疗诊断，AI的应用无处不在。
这项技术带来了巨大的便利，但同时也引发了一些担忧。
我们需要在享受AI带来的好处的同时，谨慎应对可能的风险。
未来，人工智能将继续发展，我们期待看到更多积极的变化。"""
        elif field_name == 'analysis_type' and workflow['name'] == 'text_analyzer':
            inputs[field_name] = "全面分析"
        elif field_name == 'include_details' and workflow['name'] == 'text_analyzer':
            inputs[field_name] = True
        elif field_type == 'string' and 'enum' in field_schema:
            inputs[field_name] = field_schema['enum'][0]
        elif field_type == 'string':
            inputs[field_name] = field_schema.get('default', f"测试{field_name}")
        elif field_type in ['integer', 'number']:
            inputs[field_name] = field_schema.get('default', 1)
        elif field_type == 'boolean':
            inputs[field_name] = field_schema.get('default', True)
        elif field_type == 'array':
            inputs[field_name] = field_schema.get('default', [f"测试项目{i+1}" for i in range(3)])
    
    return inputs

async def run_demo():
    """运行动态工作流演示"""
    print("🚀 动态工作流系统演示")
    print("=" * 60)
    print("本演示展示前端如何根据后端工作流配置自动渲染界面")
    print()
    
    # 检查服务是否可用
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BASE_URL}/") as response:
                if response.status != 200:
                    print("❌ 服务不可用，请确保服务器已启动")
                    return
    except Exception as e:
        print(f"❌ 无法连接到服务器: {e}")
        return
    
    print("✅ 服务器连接正常")
    print()
    
    async with DynamicWorkflowDemo(BASE_URL) as demo:
        # 1. 登录
        print("🔐 正在登录...")
        if not await demo.login(DEMO_USER, DEMO_CODE):
            print("❌ 登录失败")
            return
        print("✅ 登录成功")
        
        # 2. 获取工作流列表
        print("\n📋 获取动态工作流配置...")
        workflows = await demo.get_workflows()
        
        if not workflows:
            print("❌ 未找到可用工作流")
            return
        
        print(f"✅ 发现 {len(workflows)} 个工作流\n")
        
        # 3. 展示工作流配置信息
        print("🔍 工作流配置详情:")
        print("=" * 50)
        
        for i, workflow in enumerate(workflows, 1):
            print(f"\n{i}. ", end="")
            print_workflow_info(workflow)
        
        print("\n" + "=" * 50)
        
        # 4. 演示动态表单生成和执行
        print("\n🎯 动态工作流执行演示:")
        print("-" * 40)
        
        for workflow in workflows:
            print(f"\n🔧 正在测试工作流: {workflow['name']}")
            
            # 创建测试输入
            test_inputs = create_test_inputs(workflow)
            
            if test_inputs:
                print(f"📝 自动生成的测试输入:")
                for key, value in test_inputs.items():
                    if isinstance(value, str) and len(value) > 50:
                        print(f"   {key}: {value[:50]}...")
                    else:
                        print(f"   {key}: {value}")
            else:
                print("📝 无需输入参数")
            
            # 执行工作流
            print("⚡ 执行中...")
            start_time = time.time()
            
            result = await demo.execute_workflow(workflow['name'], test_inputs)
            
            execution_time = time.time() - start_time
            
            if result and result.get('success'):
                print(f"✅ 执行成功 (耗时: {execution_time:.2f}秒)")
                
                outputs = result.get('result', {}).get('outputs', {})
                
                # 显示结果摘要
                if isinstance(outputs, dict):
                    print("📊 结果摘要:")
                    for key, value in outputs.items():
                        if key == 'summary':
                            print(f"   📝 {key}: {value}")
                        elif key in ['title', 'sentiment', 'language']:
                            print(f"   🔖 {key}: {value}")
                        elif key == 'basic_stats' and isinstance(value, dict):
                            print(f"   📈 基础统计: {value.get('word_count', 0)}词, {value.get('sentence_count', 0)}句")
                        elif key == 'keywords' and isinstance(value, list):
                            print(f"   🔍 关键词: {', '.join(value[:5])}")
                else:
                    print(f"   📄 结果: {outputs}")
            else:
                print("❌ 执行失败")
            
            await asyncio.sleep(0.5)  # 短暂延迟
        
        print("\n" + "=" * 60)
        print("✨ 动态工作流演示完成！")
        print()
        print("💡 关键特性:")
        print("   🔹 前端根据JSON Schema自动生成表单")
        print("   🔹 支持多种字段类型：文本、选择、布尔、数组等")
        print("   🔹 动态结果显示，适配不同工作流输出")
        print("   🔹 可扩展架构，添加新工作流无需修改前端")
        print()
        print("🚀 接下来你可以:")
        print("   1. 访问 http://localhost:8000 体验Web界面")
        print("   2. 在 workflows/ 目录添加新的工作流类")
        print("   3. 在 backend/app.py 中注册新工作流")
        print("   4. 前端将自动识别并渲染新工作流")

if __name__ == "__main__":
    print("🎯 动态工作流系统演示程序")
    print()
    
    # 检查参数
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("用法:")
        print("  python test_dynamic_workflows.py        # 运行演示")
        print("  python test_dynamic_workflows.py --help # 显示帮助")
        sys.exit(0)
    
    print("💡 演示说明:")
    print("   本程序将展示前端如何根据后端工作流配置自动渲染界面")
    print("   包括动态表单生成、参数验证、结果显示等功能")
    print()
    
    # 询问是否继续
    try:
        input("按 Enter 键开始演示，或 Ctrl+C 退出...")
    except KeyboardInterrupt:
        print("\n演示已取消")
        sys.exit(0)
    
    print()
    asyncio.run(run_demo())
