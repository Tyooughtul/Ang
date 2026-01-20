import logging
import json
import re
from openai import OpenAI
from .config import (
    DEEPSEEK_API_KEY,
    DEEPSEEK_BASE_URL,
    DEEPSEEK_MODEL,
    GLM_API_KEY,
    GLM_BASE_URL,
    GLM_MODEL
)

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

def generate_with_glm(prompt: str, system_prompt: str = None, enable_web_search: bool = True, max_tokens: int = 2000) -> str:
    """
    使用 GLM-4.7 生成内容（支持联网搜索）
    
    Args:
        prompt: 用户提示词
        system_prompt: 系统提示词
        enable_web_search: 是否启用联网搜索
        max_tokens: 最大 token 数
    
    Returns:
        生成的内容
    """
    if not GLM_API_KEY:
        raise ValueError("GLM API Key 未配置，请在 .env 文件中设置 DOUBAO_API_KEY")
    
    try:
        logger.info("开始使用 GLM-4.7 生成内容...")
        logger.info(f"输入文本长度: {len(prompt)} 字符")
        logger.info(f"联网搜索: {'启用' if enable_web_search else '禁用'}")
        
        import requests
        
        headers = {
            "Authorization": f"Bearer {GLM_API_KEY}",
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
            "model": GLM_MODEL,
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
        
        logger.debug(f"发送请求到: {GLM_BASE_URL}")
        
        response = requests.post(
            GLM_BASE_URL,
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
        
        logger.info(f"GLM-4.7 生成完成，长度: {len(content)} 字符")
        
        if 'usage' in result:
            usage = result['usage']
            logger.info(f"使用的 Token: {usage.get('total_tokens', 0)}")
            logger.info(f"  输入 Token: {usage.get('input_tokens', 0)}")
            logger.info(f"  输出 Token: {usage.get('output_tokens', 0)}")
        
        return content
        
    except Exception as e:
        logger.error(f"GLM-4.7 生成失败: {str(e)}")
        raise

def generate_script(news_text: str, api_key: str = None, base_url: str = None, system_prompt: str = None) -> str:
    """
    使用 DeepSeek 将新闻改写为文案
    
    Args:
        news_text: 原始新闻文本
        api_key: DeepSeek API Key，默认使用配置文件中的 Key
        base_url: DeepSeek API Base URL，默认使用配置文件中的 URL
        system_prompt: 自定义系统提示词，默认使用配置文件中的提示词
    
    Returns:
        改写后的文案
    """
    if api_key is None:
        api_key = DEEPSEEK_API_KEY
    if base_url is None:
        base_url = DEEPSEEK_BASE_URL
    if system_prompt is None:
        from .config import PODCAST_SYSTEM_PROMPT
        system_prompt = PODCAST_SYSTEM_PROMPT
    
    if not api_key:
        raise ValueError("DeepSeek API Key 未配置，请在 .env 文件中设置 DEEPSEEK_API_KEY")
    
    try:
        logger.info("开始生成文案...")
        logger.info(f"输入文本长度: {len(news_text)} 字符")
        
        client = OpenAI(api_key=api_key, base_url=base_url)
        
        response = client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": news_text
                }
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        script = response.choices[0].message.content.strip()
        
        logger.info(f"文案生成完成，长度: {len(script)} 字符")
        logger.info(f"使用的 Token: {response.usage.total_tokens}")
        
        return script
        
    except Exception as e:
        logger.error(f"生成文案失败: {str(e)}")
        raise

def generate_script_with_glm(news_text: str, system_prompt: str = None, enable_web_search: bool = True, max_tokens: int = 2000) -> str:
    """
    使用 GLM-4.7 生成文案（支持联网搜索）
    
    Args:
        news_text: 原始新闻文本
        system_prompt: 自定义系统提示词
        enable_web_search: 是否启用联网搜索
        max_tokens: 最大 token 数
    
    Returns:
        改写后的文案
    """
    if system_prompt is None:
        from .config import PODCAST_SYSTEM_PROMPT
        system_prompt = PODCAST_SYSTEM_PROMPT
    
    return generate_with_glm(news_text, system_prompt, enable_web_search, max_tokens)

def generate_script_with_retry(news_text: str, max_retries: int = 3, api_key: str = None, base_url: str = None, system_prompt: str = None) -> str:
    """
    带重试机制的文案生成（使用 DeepSeek）
    
    Args:
        news_text: 原始新闻文本
        max_retries: 最大重试次数
        api_key: DeepSeek API Key
        base_url: DeepSeek API Base URL
        system_prompt: 自定义系统提示词
    
    Returns:
        改写后的文案
    """
    for attempt in range(max_retries):
        try:
            logger.info(f"尝试生成文案 (第 {attempt + 1}/{max_retries} 次)...")
            return generate_script(news_text, api_key, base_url, system_prompt)
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"第 {attempt + 1} 次尝试失败，正在重试... 错误: {str(e)}")
            else:
                logger.error(f"已达到最大重试次数 {max_retries}，生成失败")
                raise

def generate_script_with_glm_retry(news_text: str, max_retries: int = 3, system_prompt: str = None, enable_web_search: bool = True, max_tokens: int = 2000) -> str:
    """
    带重试机制的文案生成（使用 GLM-4.7）
    
    Args:
        news_text: 原始新闻文本
        max_retries: 最大重试次数
        system_prompt: 自定义系统提示词
        enable_web_search: 是否启用联网搜索
        max_tokens: 最大 token 数
    
    Returns:
        改写后的文案
    """
    for attempt in range(max_retries):
        try:
            logger.info(f"尝试生成文案 (第 {attempt + 1}/{max_retries} 次)...")
            return generate_script_with_glm(news_text, system_prompt, enable_web_search, max_tokens)
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"第 {attempt + 1} 次尝试失败，正在重试... 错误: {str(e)}")
            else:
                logger.error(f"已达到最大重试次数 {max_retries}，生成失败")
                raise

def validate_script(script: str) -> bool:
    """
    验证生成的口播文案是否有效
    
    Args:
        script: 待验证的口播文案
    
    Returns:
        是否有效
    """
    if not script or len(script.strip()) < 50:
        logger.warning("口播文案过短，可能无效")
        return False
    
    if len(script) > 2000:
        logger.warning("口播文案过长，可能超过 60 秒")
        return False
    
    return True
