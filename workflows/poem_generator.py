"""
诗歌生成工作流
基于Qwen API生成主题诗歌
"""

import asyncio
import httpx
import json
import logging
from typing import Dict, Any
from datetime import datetime

from workflows.base import BaseWorkflow, WorkflowError
from config.settings import settings

logger = logging.getLogger(__name__)

class PoemWorkflow(BaseWorkflow):
    """诗歌生成工作流"""
    
    def __init__(self):
        super().__init__()
        self.description = "基于给定主题生成诗歌"
        self.version = "1.0.0"
    
    def get_input_schema(self) -> Dict[str, Any]:
        """获取输入参数模式"""
        return {
            "type": "object",
            "properties": {
                "theme": {
                    "type": "string",
                    "description": "诗歌主题",
                    "minLength": 1,
                    "maxLength": 100
                },
                "style": {
                    "type": "string",
                    "description": "诗歌风格",
                    "enum": ["古典", "现代", "自由诗", "律诗", "绝句"],
                    "default": "现代"
                },
                "length": {
                    "type": "string",
                    "description": "诗歌长度",
                    "enum": ["短诗", "中等", "长诗"],
                    "default": "中等"
                }
            },
            "required": ["theme"],
            "additionalProperties": False
        }
    
    def get_output_schema(self) -> Dict[str, Any]:
        """获取输出结果模式"""
        return {
            "type": "object",
            "properties": {
                "poem": {
                    "type": "string",
                    "description": "生成的诗歌内容"
                },
                "title": {
                    "type": "string", 
                    "description": "诗歌标题"
                },
                "analysis": {
                    "type": "string",
                    "description": "诗歌创作说明"
                },
                "metadata": {
                    "type": "object",
                    "properties": {
                        "theme": {"type": "string"},
                        "style": {"type": "string"},
                        "length": {"type": "string"},
                        "word_count": {"type": "integer"},
                        "line_count": {"type": "integer"}
                    }
                }
            },
            "required": ["poem", "title"],
            "additionalProperties": False
        }
    
    async def execute(self, inputs: Dict[str, Any], username: str) -> Dict[str, Any]:
        """执行诗歌生成"""
        try:
            theme = inputs["theme"]
            style = inputs.get("style", "现代")
            length = inputs.get("length", "中等")
            
            logger.info(f"开始生成诗歌，用户: {username}, 主题: {theme}, 风格: {style}")
            
            # 构建提示词
            prompt = self._build_prompt(theme, style, length)
            
            # 调用Qwen API
            poem_result = await self._call_qwen_api(prompt)
            
            # 解析结果
            parsed_result = await self._parse_poem_result(poem_result, theme, style, length)
            
            logger.info(f"诗歌生成成功，用户: {username}, 主题: {theme}")
            
            return parsed_result
            
        except Exception as e:
            logger.error(f"诗歌生成失败: {e}")
            raise WorkflowError(f"诗歌生成失败: {str(e)}", "poem_generator")
    
    def _build_prompt(self, theme: str, style: str, length: str) -> str:
        """构建提示词"""
        length_guide = {
            "短诗": "4-8行",
            "中等": "12-20行", 
            "长诗": "24-40行"
        }
        
        style_guide = {
            "古典": "使用古典诗词的韵律和意象，注重平仄和对仗",
            "现代": "使用现代诗歌的自由表达方式，注重情感和意境",
            "自由诗": "不拘格律，自由表达情感和思想",
            "律诗": "遵循律诗格律，八句四联，讲究平仄对仗",
            "绝句": "四句诗，注重意境和韵律"
        }
        
        prompt = f"""请以"{theme}"为主题创作一首{style}风格的诗歌。

要求：
1. 风格特点：{style_guide.get(style, "自然流畅的表达")}
2. 长度：{length_guide.get(length, "适中长度")}
3. 内容要求：围绕主题"{theme}"展开，情感真挚，意境优美
4. 语言要求：用词精准，富有诗意

请按以下JSON格式返回结果：
{{
    "title": "诗歌标题",
    "poem": "诗歌正文\\n每行用\\n分隔",
    "analysis": "简要的创作说明，包括主题表达和艺术特色"
}}

请确保返回的是有效的JSON格式。"""

        return prompt
    
    async def _call_qwen_api(self, prompt: str) -> str:
        """调用Qwen API"""
        if not settings.QWEN_API_KEY:
            raise WorkflowError("Qwen API密钥未配置", "poem_generator")
        
        headers = {
            "Authorization": f"Bearer {settings.QWEN_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "qwen-turbo",
            "messages": [
                {
                    "role": "system",
                    "content": "你是一位优秀的诗人，擅长创作各种风格的诗歌。请根据用户的要求创作诗歌，并确保返回的是有效的JSON格式。"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.8,
            "max_tokens": 1000
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    f"{settings.QWEN_BASE_URL}/chat/completions",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                
                result = response.json()
                
                if "choices" not in result or not result["choices"]:
                    raise WorkflowError("API返回格式错误", "poem_generator")
                
                content = result["choices"][0]["message"]["content"]
                return content
                
            except httpx.RequestError as e:
                raise WorkflowError(f"API请求失败: {str(e)}", "poem_generator")
            except httpx.HTTPStatusError as e:
                raise WorkflowError(f"API返回错误 {e.response.status_code}: {e.response.text}", "poem_generator")
    
    async def _parse_poem_result(self, api_result: str, theme: str, style: str, length: str) -> Dict[str, Any]:
        """解析API返回的诗歌结果"""
        try:
            # 尝试解析JSON
            try:
                # 清理可能的markdown格式
                clean_result = api_result.strip()
                if clean_result.startswith("```json"):
                    clean_result = clean_result[7:]
                if clean_result.endswith("```"):
                    clean_result = clean_result[:-3]
                clean_result = clean_result.strip()
                
                poem_data = json.loads(clean_result)
            except json.JSONDecodeError:
                # 如果JSON解析失败，尝试简单的文本解析
                poem_data = self._fallback_parse(api_result, theme)
            
            # 确保必需字段存在
            poem_content = poem_data.get("poem", api_result)
            title = poem_data.get("title", f"《{theme}》")
            analysis = poem_data.get("analysis", "基于主题创作的诗歌作品")
            
            # 计算诗歌统计信息
            lines = poem_content.split('\n')
            line_count = len([line for line in lines if line.strip()])
            word_count = len(poem_content.replace('\n', '').replace(' ', ''))
            
            return {
                "poem": poem_content,
                "title": title,
                "analysis": analysis,
                "metadata": {
                    "theme": theme,
                    "style": style,
                    "length": length,
                    "word_count": word_count,
                    "line_count": line_count,
                    "generated_at": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"解析诗歌结果失败: {e}")
            # 返回基础格式
            return {
                "poem": api_result,
                "title": f"《{theme}》",
                "analysis": "生成的诗歌作品",
                "metadata": {
                    "theme": theme,
                    "style": style,
                    "length": length,
                    "word_count": len(api_result),
                    "line_count": len(api_result.split('\n')),
                    "generated_at": datetime.now().isoformat()
                }
            }
    
    def _fallback_parse(self, text: str, theme: str) -> Dict[str, Any]:
        """文本解析的后备方案"""
        lines = text.strip().split('\n')
        
        # 简单的启发式解析
        title = f"《{theme}》"
        poem_lines = []
        analysis = "基于主题创作的诗歌作品"
        
        # 寻找可能的标题
        for i, line in enumerate(lines):
            if any(marker in line for marker in ["标题", "题目", "《", "》"]):
                title = line.strip()
                lines = lines[i+1:]
                break
        
        # 过滤空行和非诗歌内容
        for line in lines:
            clean_line = line.strip()
            if clean_line and not any(skip in clean_line.lower() for skip in ["json", "```", "分析", "说明"]):
                poem_lines.append(clean_line)
        
        poem_content = '\n'.join(poem_lines[:20])  # 限制最大行数
        
        return {
            "title": title,
            "poem": poem_content,
            "analysis": analysis
        }
    
    async def preprocess(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """预处理输入"""
        # 清理和标准化输入
        processed = inputs.copy()
        
        # 清理主题
        if "theme" in processed:
            processed["theme"] = processed["theme"].strip()
        
        # 设置默认值
        if "style" not in processed:
            processed["style"] = "现代"
        if "length" not in processed:
            processed["length"] = "中等"
        
        return processed
    
    async def postprocess(self, outputs: Dict[str, Any]) -> Dict[str, Any]:
        """后处理输出"""
        # 确保诗歌格式正确
        if "poem" in outputs:
            # 清理诗歌内容
            poem = outputs["poem"]
            lines = [line.strip() for line in poem.split('\n') if line.strip()]
            outputs["poem"] = '\n'.join(lines)
        
        return outputs
