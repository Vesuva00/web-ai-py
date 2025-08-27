"""
文本分析工作流
演示工作流系统的可扩展性
"""

import asyncio
import re
from typing import Dict, Any
from datetime import datetime
import logging

from workflows.base import BaseWorkflow, WorkflowError

logger = logging.getLogger(__name__)

class TextAnalyzerWorkflow(BaseWorkflow):
    """文本分析工作流"""
    
    def __init__(self):
        super().__init__()
        self.description = "文本内容分析与统计"
        self.version = "1.0.0"
    
    def get_input_schema(self) -> Dict[str, Any]:
        """获取输入参数模式"""
        return {
            "type": "object",
            "description": "输入要分析的文本内容",
            "properties": {
                "text": {
                    "type": "string",
                    "format": "textarea",
                    "description": "待分析的文本内容",
                    "minLength": 1,
                    "maxLength": 10000,
                    "placeholder": "请输入要分析的文本内容..."
                },
                "analysis_type": {
                    "type": "string",
                    "description": "分析类型",
                    "enum": ["基础统计", "关键词提取", "情感分析", "语言检测", "全面分析"],
                    "default": "全面分析"
                },
                "include_details": {
                    "type": "boolean",
                    "description": "包含详细分析",
                    "default": True
                }
            },
            "required": ["text"],
            "additionalProperties": False
        }
    
    def get_output_schema(self) -> Dict[str, Any]:
        """获取输出结果模式"""
        return {
            "type": "object",
            "properties": {
                "basic_stats": {
                    "type": "object",
                    "description": "基础统计信息",
                    "properties": {
                        "char_count": {"type": "integer"},
                        "word_count": {"type": "integer"},
                        "sentence_count": {"type": "integer"},
                        "paragraph_count": {"type": "integer"}
                    }
                },
                "keywords": {
                    "type": "array",
                    "description": "提取的关键词",
                    "items": {"type": "string"}
                },
                "sentiment": {
                    "type": "string",
                    "description": "情感倾向"
                },
                "language": {
                    "type": "string",
                    "description": "检测到的语言"
                },
                "readability": {
                    "type": "object",
                    "description": "可读性分析"
                },
                "summary": {
                    "type": "string",
                    "description": "分析摘要"
                }
            },
            "required": ["basic_stats", "summary"],
            "additionalProperties": False
        }
    
    async def execute(self, inputs: Dict[str, Any], username: str) -> Dict[str, Any]:
        """执行文本分析"""
        try:
            text = inputs["text"]
            analysis_type = inputs.get("analysis_type", "全面分析")
            include_details = inputs.get("include_details", True)
            
            logger.info(f"开始文本分析，用户: {username}, 类型: {analysis_type}")
            
            result = {}
            
            # 基础统计
            if analysis_type in ["基础统计", "全面分析"]:
                result["basic_stats"] = await self._basic_statistics(text)
            
            # 关键词提取
            if analysis_type in ["关键词提取", "全面分析"]:
                result["keywords"] = await self._extract_keywords(text)
            
            # 情感分析
            if analysis_type in ["情感分析", "全面分析"]:
                result["sentiment"] = await self._sentiment_analysis(text)
            
            # 语言检测
            if analysis_type in ["语言检测", "全面分析"]:
                result["language"] = await self._language_detection(text)
            
            # 可读性分析
            if analysis_type == "全面分析" and include_details:
                result["readability"] = await self._readability_analysis(text)
            
            # 生成摘要
            result["summary"] = await self._generate_summary(result, analysis_type)
            
            logger.info(f"文本分析完成，用户: {username}")
            
            return result
            
        except Exception as e:
            logger.error(f"文本分析失败: {e}")
            raise WorkflowError(f"文本分析失败: {str(e)}", "text_analyzer")
    
    async def _basic_statistics(self, text: str) -> Dict[str, Any]:
        """基础统计分析"""
        # 字符统计
        char_count = len(text)
        char_count_no_spaces = len(text.replace(' ', '').replace('\n', '').replace('\t', ''))
        
        # 词语统计
        words = re.findall(r'\b\w+\b', text)
        word_count = len(words)
        
        # 句子统计
        sentences = re.split(r'[.!?。！？]', text)
        sentence_count = len([s for s in sentences if s.strip()])
        
        # 段落统计
        paragraphs = text.split('\n\n')
        paragraph_count = len([p for p in paragraphs if p.strip()])
        
        # 平均值计算
        avg_words_per_sentence = word_count / sentence_count if sentence_count > 0 else 0
        avg_chars_per_word = char_count_no_spaces / word_count if word_count > 0 else 0
        
        return {
            "char_count": char_count,
            "char_count_no_spaces": char_count_no_spaces,
            "word_count": word_count,
            "sentence_count": sentence_count,
            "paragraph_count": paragraph_count,
            "avg_words_per_sentence": round(avg_words_per_sentence, 2),
            "avg_chars_per_word": round(avg_chars_per_word, 2)
        }
    
    async def _extract_keywords(self, text: str) -> list:
        """提取关键词（简单实现）"""
        # 简单的关键词提取算法
        words = re.findall(r'\b\w+\b', text.lower())
        
        # 停用词列表
        stop_words = {
            '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '个', '上', '也', '很', '到', '说', '要', 
            '去', '你', '会', '着', '没有', '看', '好', '自己', '这', '那', '来', '他', '她', '它', '我们', '你们', '他们',
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'this', 'that',
            'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would'
        }
        
        # 过滤停用词和短词
        filtered_words = [word for word in words if len(word) > 2 and word not in stop_words]
        
        # 统计词频
        word_freq = {}
        for word in filtered_words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # 按频率排序，取前10个
        keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return [word for word, freq in keywords]
    
    async def _sentiment_analysis(self, text: str) -> str:
        """情感分析（简单实现）"""
        # 简单的情感词典
        positive_words = {
            '好', '棒', '优秀', '美好', '快乐', '开心', '喜欢', '爱', '赞', '完美', '成功', '胜利', '希望',
            'good', 'great', 'excellent', 'amazing', 'wonderful', 'happy', 'love', 'like', 'perfect', 'success'
        }
        
        negative_words = {
            '坏', '差', '糟糕', '失败', '痛苦', '悲伤', '讨厌', '恨', '困难', '问题', '错误', '危险',
            'bad', 'terrible', 'awful', 'hate', 'sad', 'angry', 'problem', 'error', 'fail', 'wrong'
        }
        
        words = re.findall(r'\b\w+\b', text.lower())
        
        positive_count = sum(1 for word in words if word in positive_words)
        negative_count = sum(1 for word in words if word in negative_words)
        
        if positive_count > negative_count:
            return "积极"
        elif negative_count > positive_count:
            return "消极"
        else:
            return "中性"
    
    async def _language_detection(self, text: str) -> str:
        """语言检测（简单实现）"""
        # 简单的语言检测
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        english_chars = len(re.findall(r'[a-zA-Z]', text))
        
        total_chars = chinese_chars + english_chars
        
        if total_chars == 0:
            return "未知"
        
        chinese_ratio = chinese_chars / total_chars
        
        if chinese_ratio > 0.5:
            return "中文"
        elif english_chars > chinese_chars:
            return "英文"
        else:
            return "混合语言"
    
    async def _readability_analysis(self, text: str) -> Dict[str, Any]:
        """可读性分析"""
        stats = await self._basic_statistics(text)
        
        # 可读性指标
        readability_score = 0
        difficulty_level = "简单"
        
        # 基于平均句子长度和词语长度的简单评估
        avg_sentence_length = stats.get("avg_words_per_sentence", 0)
        avg_word_length = stats.get("avg_chars_per_word", 0)
        
        if avg_sentence_length > 20 or avg_word_length > 6:
            difficulty_level = "困难"
            readability_score = 30
        elif avg_sentence_length > 15 or avg_word_length > 5:
            difficulty_level = "中等"
            readability_score = 60
        else:
            difficulty_level = "简单"
            readability_score = 90
        
        return {
            "score": readability_score,
            "level": difficulty_level,
            "avg_sentence_length": avg_sentence_length,
            "avg_word_length": avg_word_length
        }
    
    async def _generate_summary(self, analysis_result: Dict[str, Any], analysis_type: str) -> str:
        """生成分析摘要"""
        summary_parts = []
        
        if "basic_stats" in analysis_result:
            stats = analysis_result["basic_stats"]
            summary_parts.append(
                f"文本包含 {stats['char_count']} 个字符，{stats['word_count']} 个词语，"
                f"{stats['sentence_count']} 个句子，{stats['paragraph_count']} 个段落。"
            )
        
        if "sentiment" in analysis_result:
            sentiment = analysis_result["sentiment"]
            summary_parts.append(f"整体情感倾向：{sentiment}。")
        
        if "language" in analysis_result:
            language = analysis_result["language"]
            summary_parts.append(f"检测语言：{language}。")
        
        if "keywords" in analysis_result:
            keywords = analysis_result["keywords"][:5]  # 只显示前5个关键词
            if keywords:
                summary_parts.append(f"主要关键词：{', '.join(keywords)}。")
        
        if "readability" in analysis_result:
            readability = analysis_result["readability"]
            summary_parts.append(f"可读性评估：{readability['level']}（得分：{readability['score']}）。")
        
        if not summary_parts:
            summary_parts.append("文本分析完成。")
        
        return " ".join(summary_parts)
    
    async def preprocess(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """预处理输入"""
        processed = inputs.copy()
        
        # 清理文本
        if "text" in processed:
            text = processed["text"].strip()
            # 移除过多的空行
            text = re.sub(r'\n\s*\n', '\n\n', text)
            processed["text"] = text
        
        return processed
    
    async def postprocess(self, outputs: Dict[str, Any]) -> Dict[str, Any]:
        """后处理输出"""
        # 添加分析时间戳
        outputs["analyzed_at"] = datetime.now().isoformat()
        
        return outputs
