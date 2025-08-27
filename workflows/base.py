"""
工作流基础架构
提供可扩展的工作流管理系统
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Type
import asyncio
import time
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class BaseWorkflow(ABC):
    """工作流基类"""
    
    def __init__(self):
        self.name = self.__class__.__name__
        self.description = ""
        self.version = "1.0.0"
        self.input_schema = {}
        self.output_schema = {}
    
    @abstractmethod
    async def execute(self, inputs: Dict[str, Any], username: str) -> Dict[str, Any]:
        """
        执行工作流
        
        Args:
            inputs: 输入参数
            username: 执行用户
            
        Returns:
            执行结果
        """
        pass
    
    @abstractmethod
    def get_input_schema(self) -> Dict[str, Any]:
        """获取输入参数模式"""
        pass
    
    @abstractmethod
    def get_output_schema(self) -> Dict[str, Any]:
        """获取输出结果模式"""
        pass
    
    def validate_inputs(self, inputs: Dict[str, Any]) -> bool:
        """验证输入参数"""
        try:
            schema = self.get_input_schema()
            required_fields = schema.get("required", [])
            
            # 检查必需字段
            for field in required_fields:
                if field not in inputs:
                    raise ValueError(f"缺少必需参数: {field}")
            
            # 检查字段类型
            properties = schema.get("properties", {})
            for field, value in inputs.items():
                if field in properties:
                    expected_type = properties[field].get("type")
                    if expected_type and not self._check_type(value, expected_type):
                        raise ValueError(f"参数 {field} 类型错误，期望 {expected_type}")
            
            return True
            
        except Exception as e:
            logger.error(f"输入验证失败: {e}")
            return False
    
    def _check_type(self, value: Any, expected_type: str) -> bool:
        """检查值类型"""
        type_mapping = {
            "string": str,
            "integer": int,
            "number": (int, float),
            "boolean": bool,
            "array": list,
            "object": dict
        }
        
        expected_python_type = type_mapping.get(expected_type)
        if expected_python_type:
            return isinstance(value, expected_python_type)
        
        return True
    
    async def preprocess(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """预处理输入数据"""
        return inputs
    
    async def postprocess(self, outputs: Dict[str, Any]) -> Dict[str, Any]:
        """后处理输出数据"""
        return outputs

class WorkflowManager:
    """工作流管理器"""
    
    def __init__(self):
        self._workflows: Dict[str, BaseWorkflow] = {}
        self._execution_stats: Dict[str, Dict[str, Any]] = {}
    
    def register_workflow(self, name: str, workflow: BaseWorkflow):
        """注册工作流"""
        if not isinstance(workflow, BaseWorkflow):
            raise ValueError("工作流必须继承自 BaseWorkflow")
        
        self._workflows[name] = workflow
        self._execution_stats[name] = {
            "total_executions": 0,
            "successful_executions": 0,
            "total_execution_time": 0.0,
            "average_execution_time": 0.0
        }
        
        logger.info(f"工作流已注册: {name}")
    
    def unregister_workflow(self, name: str):
        """注销工作流"""
        if name in self._workflows:
            del self._workflows[name]
            del self._execution_stats[name]
            logger.info(f"工作流已注销: {name}")
    
    def get_available_workflows(self) -> List[Dict[str, Any]]:
        """获取可用工作流列表"""
        workflows = []
        for name, workflow in self._workflows.items():
            workflows.append({
                "name": name,
                "description": workflow.description,
                "version": workflow.version,
                "input_schema": workflow.get_input_schema(),
                "output_schema": workflow.get_output_schema(),
                "stats": self._execution_stats.get(name, {})
            })
        return workflows
    
    async def execute_workflow(
        self, 
        workflow_name: str, 
        inputs: Dict[str, Any], 
        username: str
    ) -> Dict[str, Any]:
        """执行指定工作流"""
        if workflow_name not in self._workflows:
            raise ValueError(f"工作流不存在: {workflow_name}")
        
        workflow = self._workflows[workflow_name]
        
        # 验证输入
        if not workflow.validate_inputs(inputs):
            raise ValueError("输入参数验证失败")
        
        # 记录开始时间
        start_time = time.time()
        execution_id = f"{workflow_name}_{username}_{int(start_time)}"
        
        try:
            logger.info(f"开始执行工作流: {workflow_name}, 用户: {username}, ID: {execution_id}")
            
            # 预处理
            processed_inputs = await workflow.preprocess(inputs)
            
            # 执行工作流
            outputs = await workflow.execute(processed_inputs, username)
            
            # 后处理
            final_outputs = await workflow.postprocess(outputs)
            
            # 计算执行时间
            execution_time = time.time() - start_time
            
            # 更新统计信息
            await self._update_stats(workflow_name, execution_time, True)
            
            # 记录成功日志
            from database.models import WorkflowLogger
            await WorkflowLogger.log_execution(
                username=username,
                workflow_type=workflow_name,
                inputs=inputs,
                outputs=final_outputs,
                status="success",
                execution_time_ms=int(execution_time * 1000)
            )
            
            logger.info(f"工作流执行成功: {execution_id}, 耗时: {execution_time:.2f}秒")
            
            return {
                "execution_id": execution_id,
                "workflow_name": workflow_name,
                "execution_time": execution_time,
                "timestamp": datetime.now().isoformat(),
                "outputs": final_outputs
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            # 更新统计信息
            await self._update_stats(workflow_name, execution_time, False)
            
            # 记录错误日志
            from database.models import WorkflowLogger
            await WorkflowLogger.log_execution(
                username=username,
                workflow_type=workflow_name,
                inputs=inputs,
                status="error",
                execution_time_ms=int(execution_time * 1000),
                error_message=str(e)
            )
            
            logger.error(f"工作流执行失败: {execution_id}, 错误: {e}")
            raise e
    
    async def _update_stats(self, workflow_name: str, execution_time: float, success: bool):
        """更新工作流统计信息"""
        if workflow_name not in self._execution_stats:
            return
        
        stats = self._execution_stats[workflow_name]
        stats["total_executions"] += 1
        stats["total_execution_time"] += execution_time
        
        if success:
            stats["successful_executions"] += 1
        
        if stats["total_executions"] > 0:
            stats["average_execution_time"] = stats["total_execution_time"] / stats["total_executions"]
    
    def get_workflow_stats(self, workflow_name: str = None) -> Dict[str, Any]:
        """获取工作流统计信息"""
        if workflow_name:
            return self._execution_stats.get(workflow_name, {})
        return self._execution_stats.copy()
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        return {
            "total_workflows": len(self._workflows),
            "workflow_names": list(self._workflows.keys()),
            "total_executions": sum(stats["total_executions"] for stats in self._execution_stats.values()),
            "total_successful": sum(stats["successful_executions"] for stats in self._execution_stats.values()),
            "status": "healthy"
        }

class WorkflowError(Exception):
    """工作流执行错误"""
    
    def __init__(self, message: str, workflow_name: str = None, error_code: str = None):
        super().__init__(message)
        self.workflow_name = workflow_name
        self.error_code = error_code
        self.timestamp = datetime.now()

class ValidationError(WorkflowError):
    """输入验证错误"""
    pass

class ExecutionError(WorkflowError):
    """工作流执行错误"""
    pass

class ConfigurationError(WorkflowError):
    """工作流配置错误"""
    pass

# 导出主要类
__all__ = [
    'BaseWorkflow',
    'WorkflowManager',
    'WorkflowError',
    'ValidationError', 
    'ExecutionError',
    'ConfigurationError'
]
