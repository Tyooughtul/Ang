import logging
import json
import re
from typing import Dict, List
from .config import GLM_API_KEY, GLM_BASE_URL, GLM_MODEL
import requests

logger = logging.getLogger(__name__)

def clean_json_response(text: str) -> str:
    """
    清理 GLM-4.7 返回的 JSON 响应，移除 markdown 代码块标记
    
    Args:
        text: 原始文本
    
    Returns:
        清理后的 JSON 字符串
    """
    if not text:
        return text
    
    # 移除 markdown 代码块标记
    patterns = [
        r'```json\s*\n?([\s\S]*?)\n?```',
        r'```\s*\n?([\s\S]*?)\n?```',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
    
    return text.strip()

class ContentImprover:
    """内容改进器：根据验证结果改进内容质量（使用 GLM-4.7）"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or GLM_API_KEY
        self.base_url = GLM_BASE_URL
        self.model = GLM_MODEL
        
        if not self.api_key:
            logger.warning("GLM API Key 未配置，内容改进功能将不可用")
    
    def _make_glm_request(self, prompt: str, system_prompt: str = None, enable_web_search: bool = True, max_tokens: int = 3000) -> str:
        """
        使用 GLM-4.7 发送请求
        
        Args:
            prompt: 用户提示词
            system_prompt: 系统提示词
            enable_web_search: 是否启用联网搜索
            max_tokens: 最大 token 数
        
        Returns:
            响应内容
        """
        if not self.api_key:
            raise ValueError("GLM API Key 未配置")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # 构建输入
        input_messages = []
        
        if system_prompt:
            input_messages.append({
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": f"系统设定：{system_prompt}\n\n{prompt}"
                    }
                ]
            })
        else:
            input_messages.append({
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": prompt
                    }
                ]
            })
        
        # 构建请求
        payload = {
            "model": self.model,
            "stream": False,
            "input": input_messages
        }
        
        # 如果启用联网搜索，添加工具
        if enable_web_search:
            payload["tools"] = [
                {
                    "type": "web_search",
                    "max_keyword": 3
                }
            ]
        
        try:
            logger.info(f"发送 GLM-4.7 请求...")
            logger.debug(f"联网搜索: {'启用' if enable_web_search else '禁用'}")
            
            response = requests.post(
                self.base_url,
                headers=headers,
                json=payload,
                timeout=60
            )
            
            logger.info(f"GLM-4.7 响应状态码: {response.status_code}")
            
            if response.status_code != 200:
                raise Exception(f"HTTP 错误: {response.status_code} - {response.text[:500]}")
            
            result = response.json()
            
            if 'error' in result:
                error_code = result['error'].get('code', 'unknown')
                error_message = result['error'].get('message', 'unknown')
                raise Exception(f"API 错误 [{error_code}]: {error_message}")
            
            if 'output' not in result:
                raise Exception("响应中没有 output 字段")
            
            output_items = result['output']
            collected_text = []
            
            for idx, item in enumerate(output_items):
                item_type = item.get('type', 'unknown')
                logger.debug(f"Output 项目 {idx}: type={item_type}")
                
                if item_type == 'message' and item.get('role') == 'assistant':
                    for content_item in item.get('content', []):
                        if content_item.get('type') == 'output_text':
                            text = content_item.get('text', '')
                            if text:
                                collected_text.append(text)
                                logger.debug(f"收集到文本: {text[:100]}")
                
                elif item_type == 'web_search_call':
                    action = item.get('action', {})
                    logger.debug(f"检测到 Web Search 调用: {action.get('query', 'N/A')}")
            
            if not collected_text:
                raise Exception("GLM-4.7 响应中未找到有效文本内容")
            
            content = '\n'.join(collected_text)
            
            logger.info(f"GLM-4.7 成功返回内容，长度: {len(content)}")
            
            if 'usage' in result:
                usage = result['usage']
                logger.info(f"使用的 Token: {usage.get('total_tokens', 0)}")
            
            return content
            
        except Exception as e:
            logger.error(f"GLM-4.7 请求失败: {str(e)}")
            raise
    
    def improve_content(self, topic: str, content: str, check_result: Dict) -> Dict:
        """
        根据验证结果改进内容（使用 GLM-4.7）
        
        Args:
            topic: 话题
            content: 原始内容
            check_result: 验证结果
        
        Returns:
            改进结果字典
        """
        if not self.api_key:
            return {
                'success': False,
                'improved_content': content,
                'improvements': [],
                'reasoning': '未配置 API Key，无法改进内容'
            }
        
        try:
            logger.info("开始改进内容...")
            
            truth_score = check_result['score_breakdown']['truth_score']
            freshness_score = check_result['score_breakdown']['freshness_score']
            consistency_score = check_result['score_breakdown']['consistency_score']
            overall_score = check_result['overall_score']
            
            improvement_needs = []
            
            if truth_score < 70:
                improvement_needs.append(f"真实性评分 {truth_score:.1f} 分过低，需要核实事实，添加可靠来源")
            if freshness_score < 70:
                improvement_needs.append(f"时效性评分 {freshness_score:.1f} 分过低，需要更新内容，添加最新信息")
            if consistency_score < 70:
                improvement_needs.append(f"一致性评分 {consistency_score:.1f} 分过低，需要检查内容逻辑，确保信息一致")
            
            if check_result.get('improvement_suggestions'):
                improvement_needs.extend(check_result['improvement_suggestions'])
            
            improvement_prompt = f"""你是一个专业的内容编辑，擅长根据质量反馈改进科技新闻内容。

任务：根据以下反馈改进内容，提高质量评分

话题：{topic}

当前内容：
{content}

当前评分：
- 总体评分：{overall_score:.1f}/100
- 真实性：{truth_score:.1f}/100
- 时效性：{freshness_score:.1f}/100
- 一致性：{consistency_score:.1f}/100

需要改进的问题：
{chr(10).join([f"{i+1}. {item}" for i, item in enumerate(improvement_needs)])}

改进要求：
1. 保持核心信息和观点不变
2. 针对上述问题逐一改进
3. 提高真实性：核实事实，添加可靠来源，避免夸大或误导
4. 提高时效性：更新过时信息，添加最新动态，使用新鲜关键词
5. 提高一致性：检查逻辑矛盾，统一术语和表述
6. 降低 AI 味：使用更自然的语言，避免机械化的表达
7. 保持文章的可读性和吸引力
8. 可以使用联网搜索获取最新信息来改进内容

返回格式（必须是有效的 JSON）：
{{
    "improved_content": "改进后的完整内容",
    "improvements": [
        {{
            "issue": "问题描述",
            "action": "采取了什么改进措施",
            "before": "改进前的片段",
            "after": "改进后的片段"
        }}
    ],
    "reasoning": "改进理由和预期效果"
}}"""
            
            system_prompt = "你是一个专业的内容编辑，擅长根据质量反馈改进科技新闻内容，目标是提高真实性、时效性和一致性。"
            
            result_text = self._make_glm_request(improvement_prompt, system_prompt, enable_web_search=True, max_tokens=3000)
            
            cleaned_result = clean_json_response(result_text)
            
            try:
                result = json.loads(cleaned_result)
                
                improved_content = result.get('improved_content', content)
                improvements = result.get('improvements', [])
                reasoning = result.get('reasoning', '')
                
                logger.info(f"内容改进完成，共 {len(improvements)} 项改进")
                for i, imp in enumerate(improvements, 1):
                    logger.info(f"  {i}. {imp.get('issue', '')}")
                
                return {
                    'success': True,
                    'improved_content': improved_content,
                    'improvements': improvements,
                    'reasoning': reasoning
                }
                
            except json.JSONDecodeError as e:
                logger.error(f"解析改进结果失败: {e}")
                logger.error(f"原始结果: {result_text[:500]}")
                logger.error(f"清理后结果: {cleaned_result[:500]}")
                return {
                    'success': False,
                    'improved_content': content,
                    'improvements': [],
                    'reasoning': f'解析失败: {str(e)}'
                }
            
        except Exception as e:
            logger.error(f"改进内容失败: {str(e)}")
            return {
                'success': False,
                'improved_content': content,
                'improvements': [],
                'reasoning': f'改进失败: {str(e)}'
            }
    
    def analyze_improvement_needs(self, check_result: Dict) -> List[str]:
        """
        分析需要改进的具体问题
        
        Args:
            check_result: 验证结果
        
        Returns:
            需要改进的问题列表
        """
        needs = []
        
        truth_score = check_result['score_breakdown']['truth_score']
        freshness_score = check_result['score_breakdown']['freshness_score']
        consistency_score = check_result['score_breakdown']['consistency_score']
        
        if truth_score < 50:
            needs.append("严重问题：内容可能包含虚假信息，必须彻底核查所有事实")
        elif truth_score < 70:
            needs.append("中等问题：部分信息可能不准确，需要核实并添加可靠来源")
        
        if freshness_score < 50:
            needs.append("严重问题：内容可能严重过时，建议重新获取最新资讯")
        elif freshness_score < 70:
            needs.append("中等问题：部分信息可能不够新鲜，需要更新最新动态")
        
        if consistency_score < 50:
            needs.append("严重问题：内容存在明显矛盾，需要全面检查逻辑")
        elif consistency_score < 70:
            needs.append("中等问题：部分信息可能不一致，需要统一表述")
        
        if check_result.get('improvement_suggestions'):
            needs.extend(check_result['improvement_suggestions'])
        
        return needs