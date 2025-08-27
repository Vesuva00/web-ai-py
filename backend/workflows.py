#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流模块 - 可扩展的大模型工作流框架
"""

import os
import json
import time
import logging
from datetime import datetime
from abc import ABC, abstractmethod
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import requests

from models import db, User, WorkflowCall, SystemLog

logger = logging.getLogger(__name__)
workflows_bp = Blueprint('workflows', __name__)

class BaseWorkflow(ABC):
    """工作流基类"""
    
    def __init__(self):
        self.name = self.__class__.__name__
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.api_base = os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1')
    
    @abstractmethod
    def validate_input(self, input_data):
        """验证输入数据"""
        pass
    
    @abstractmethod
    def process(self, input_data):
        """处理工作流逻辑"""
        pass
    
    def execute(self, input_data, user_id, ip_address, user_agent):
        """执行工作流"""
        start_time = time.time()
        
        # 创建工作流调用记录
        workflow_call = WorkflowCall(
            user_id=user_id,
            workflow_type=self.name,
            input_data=json.dumps(input_data),
            status='pending',
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        db.session.add(workflow_call)
        db.session.commit()
        
        try:
            # 验证输入
            validation_result = self.validate_input(input_data)
            if not validation_result['valid']:
                raise ValueError(validation_result['error'])
            
            # 处理工作流
            result = self.process(input_data)
            
            # 计算执行时间
            execution_time = time.time() - start_time
            
            # 更新记录
            workflow_call.status = 'success'
            workflow_call.output_data = json.dumps(result)
            workflow_call.execution_time = execution_time
            workflow_call.tokens_used = result.get('tokens_used', 0)
            workflow_call.completed_at = datetime.utcnow()
            
            db.session.commit()
            
            logger.info(f'工作流 {self.name} 执行成功，用户: {user_id}，耗时: {execution_time:.2f}s')
            
            return {
                'success': True,
                'result': result,
                'execution_time': execution_time,
                'call_id': workflow_call.id
            }
            
        except Exception as e:
            # 计算执行时间
            execution_time = time.time() - start_time
            
            # 更新错误记录
            workflow_call.status = 'failed'
            workflow_call.error_message = str(e)
            workflow_call.execution_time = execution_time
            workflow_call.completed_at = datetime.utcnow()
            
            db.session.commit()
            
            # 记录错误日志
            SystemLog.log_error(
                message=f'工作流 {self.name} 执行失败: {str(e)}',
                module='workflows',
                user_id=user_id,
                ip_address=ip_address,
                extra_data={'input_data': input_data}
            )
            
            logger.error(f'工作流 {self.name} 执行失败: {str(e)}')
            
            return {
                'success': False,
                'error': str(e),
                'execution_time': execution_time,
                'call_id': workflow_call.id
            }

class PoetryGeneratorWorkflow(BaseWorkflow):
    """诗歌生成工作流"""
    
    def validate_input(self, input_data):
        """验证输入数据"""
        if not isinstance(input_data, dict):
            return {'valid': False, 'error': '输入数据必须是字典格式'}
        
        theme = input_data.get('theme', '').strip()
        if not theme:
            return {'valid': False, 'error': '请提供诗歌主题'}
        
        if len(theme) > 100:
            return {'valid': False, 'error': '主题长度不能超过100个字符'}
        
        return {'valid': True}
    
    def process(self, input_data):
        """处理诗歌生成"""
        theme = input_data.get('theme')
        style = input_data.get('style', '现代诗')  # 默认现代诗
        
        # 构建提示词
        prompt = f"""请根据主题"{theme}"创作一首{style}。要求：
1. 紧扣主题，意境优美
2. 语言流畅，朗朗上口
3. 富有诗意和想象力
4. 长度适中（8-16行）

主题：{theme}
诗歌风格：{style}

请直接输出诗歌内容，不要包含其他说明文字。"""
        
        # 调用大模型API
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'model': 'gpt-3.5-turbo',
                'messages': [
                    {'role': 'system', 'content': '你是一位富有才华的诗人，擅长创作各种风格的诗歌。'},
                    {'role': 'user', 'content': prompt}
                ],
                'max_tokens': 500,
                'temperature': 0.8
            }
            
            response = requests.post(
                f'{self.api_base}/chat/completions',
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code != 200:
                raise Exception(f'API调用失败: {response.status_code} - {response.text}')
            
            result = response.json()
            
            if 'choices' not in result or not result['choices']:
                raise Exception('API返回数据格式错误')
            
            poetry = result['choices'][0]['message']['content'].strip()
            tokens_used = result.get('usage', {}).get('total_tokens', 0)
            
            return {
                'poetry': poetry,
                'theme': theme,
                'style': style,
                'tokens_used': tokens_used,
                'model': 'gpt-3.5-turbo'
            }
            
        except requests.exceptions.Timeout:
            raise Exception('API请求超时，请稍后重试')
        except requests.exceptions.RequestException as e:
            raise Exception(f'网络请求失败: {str(e)}')
        except Exception as e:
            raise Exception(f'诗歌生成失败: {str(e)}')

class TextSummaryWorkflow(BaseWorkflow):
    """文本摘要工作流"""
    
    def validate_input(self, input_data):
        """验证输入数据"""
        if not isinstance(input_data, dict):
            return {'valid': False, 'error': '输入数据必须是字典格式'}
        
        text = input_data.get('text', '').strip()
        if not text:
            return {'valid': False, 'error': '请提供要摘要的文本'}
        
        if len(text) > 10000:
            return {'valid': False, 'error': '文本长度不能超过10000个字符'}
        
        return {'valid': True}
    
    def process(self, input_data):
        """处理文本摘要"""
        text = input_data.get('text')
        max_length = input_data.get('max_length', 200)  # 默认摘要长度
        
        # 构建提示词
        prompt = f"""请为以下文本生成一个简洁的摘要，长度控制在{max_length}字以内：

原文：
{text}

要求：
1. 保留主要信息和核心观点
2. 语言简洁明了
3. 逻辑清晰连贯
4. 长度控制在{max_length}字以内

请直接输出摘要内容："""
        
        # 调用大模型API
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'model': 'gpt-3.5-turbo',
                'messages': [
                    {'role': 'system', 'content': '你是一个专业的文本摘要助手，擅长提取文本的核心信息。'},
                    {'role': 'user', 'content': prompt}
                ],
                'max_tokens': max_length * 2,  # 给一些余量
                'temperature': 0.3
            }
            
            response = requests.post(
                f'{self.api_base}/chat/completions',
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code != 200:
                raise Exception(f'API调用失败: {response.status_code} - {response.text}')
            
            result = response.json()
            
            if 'choices' not in result or not result['choices']:
                raise Exception('API返回数据格式错误')
            
            summary = result['choices'][0]['message']['content'].strip()
            tokens_used = result.get('usage', {}).get('total_tokens', 0)
            
            return {
                'summary': summary,
                'original_length': len(text),
                'summary_length': len(summary),
                'max_length': max_length,
                'tokens_used': tokens_used,
                'model': 'gpt-3.5-turbo'
            }
            
        except requests.exceptions.Timeout:
            raise Exception('API请求超时，请稍后重试')
        except requests.exceptions.RequestException as e:
            raise Exception(f'网络请求失败: {str(e)}')
        except Exception as e:
            raise Exception(f'文本摘要失败: {str(e)}')

# 工作流注册表
WORKFLOW_REGISTRY = {
    'poetry_generator': PoetryGeneratorWorkflow,
    'text_summary': TextSummaryWorkflow,
}

def get_workflow(workflow_type):
    """获取工作流实例"""
    if workflow_type not in WORKFLOW_REGISTRY:
        raise ValueError(f'不支持的工作流类型: {workflow_type}')
    
    return WORKFLOW_REGISTRY[workflow_type]()

@workflows_bp.route('/list', methods=['GET'])
@jwt_required()
def list_workflows():
    """获取可用工作流列表"""
    workflows = []
    
    for workflow_type, workflow_class in WORKFLOW_REGISTRY.items():
        workflows.append({
            'type': workflow_type,
            'name': workflow_class.__name__,
            'description': workflow_class.__doc__ or ''
        })
    
    return jsonify({
        'workflows': workflows,
        'total': len(workflows)
    })

@workflows_bp.route('/execute', methods=['POST'])
@jwt_required()
def execute_workflow():
    """执行工作流"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or not user.is_active:
            return jsonify({'error': '用户不存在或已禁用'}), 401
        
        data = request.get_json()
        if not data:
            return jsonify({'error': '请提供请求数据'}), 400
        
        workflow_type = data.get('workflow_type')
        input_data = data.get('input_data', {})
        
        if not workflow_type:
            return jsonify({'error': '请指定工作流类型'}), 400
        
        # 获取工作流实例
        try:
            workflow = get_workflow(workflow_type)
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        
        # 执行工作流
        result = workflow.execute(
            input_data=input_data,
            user_id=user_id,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', '')
        )
        
        if result['success']:
            return jsonify({
                'success': True,
                'result': result['result'],
                'execution_time': result['execution_time'],
                'call_id': result['call_id']
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error'],
                'execution_time': result['execution_time'],
                'call_id': result['call_id']
            }), 500
            
    except Exception as e:
        logger.error(f'工作流执行接口错误: {str(e)}')
        return jsonify({'error': '服务器内部错误'}), 500

@workflows_bp.route('/history', methods=['GET'])
@jwt_required()
def get_workflow_history():
    """获取用户工作流调用历史"""
    try:
        user_id = get_jwt_identity()
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        
        # 查询用户的工作流调用记录
        query = WorkflowCall.query.filter_by(user_id=user_id)
        
        # 按创建时间倒序排列
        query = query.order_by(WorkflowCall.created_at.desc())
        
        # 分页
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        calls = [call.to_dict() for call in pagination.items]
        
        return jsonify({
            'calls': calls,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        })
        
    except Exception as e:
        logger.error(f'获取工作流历史失败: {str(e)}')
        return jsonify({'error': '获取历史记录失败'}), 500
