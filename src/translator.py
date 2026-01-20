import logging
from openai import OpenAI
from .config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL

logger = logging.getLogger(__name__)

def translate_to_chinese(text: str, api_key: str = None, base_url: str = None) -> str:
    """
    使用 DeepSeek 将英文翻译成中文
    
    Args:
        text: 待翻译的英文文本
        api_key: DeepSeek API Key，默认使用配置文件中的 Key
        base_url: DeepSeek API Base URL，默认使用配置文件中的 URL
    
    Returns:
        翻译后的中文文本
    """
    if api_key is None:
        api_key = DEEPSEEK_API_KEY
    if base_url is None:
        base_url = DEEPSEEK_BASE_URL
    
    if not api_key:
        raise ValueError("DeepSeek API Key 未配置，请在 .env 文件中设置 DEEPSEEK_API_KEY")
    
    try:
        logger.info("开始翻译文本...")
        
        client = OpenAI(api_key=api_key, base_url=base_url)
        
        response = client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "你是一个专业的科技翻译官，将英文科技新闻翻译成流畅的中文。保持技术术语的准确性，语言要自然流畅，符合中文表达习惯。"
                },
                {
                    "role": "user",
                    "content": text
                }
            ],
            temperature=0.3
        )
        
        translated_text = response.choices[0].message.content.strip()
        logger.info(f"翻译完成，原文长度: {len(text)} 字符，译文长度: {len(translated_text)} 字符")
        
        return translated_text
        
    except Exception as e:
        logger.error(f"翻译失败: {str(e)}")
        raise

def translate_news_list(news_list: list, api_key: str = None, base_url: str = None) -> list:
    """
    批量翻译新闻列表
    
    Args:
        news_list: 新闻列表，每个元素是包含 title 和 summary 的字典
        api_key: DeepSeek API Key
        base_url: DeepSeek API Base URL
    
    Returns:
        翻译后的新闻列表
    """
    if not news_list:
        return news_list
    
    logger.info(f"开始批量翻译 {len(news_list)} 条新闻...")
    
    translated_list = []
    for i, news in enumerate(news_list, 1):
        try:
            logger.info(f"正在翻译第 {i}/{len(news_list)} 条新闻: {news['title'][:50]}...")
            
            title = news.get('title', '')
            summary = news.get('summary', '')
            
            if not title and not summary:
                translated_list.append(news)
                continue
            
            combined_text = f"标题: {title}\n内容: {summary}"
            translated_text = translate_to_chinese(combined_text, api_key, base_url)
            
            translated_list.append({
                'title': news.get('title', ''),
                'summary': news.get('summary', ''),
                'link': news.get('link', ''),
                'published': news.get('published', ''),
                'source': news.get('source', ''),
                'translated_title': translated_text.split('\n')[0].replace('标题: ', '').strip(),
                'translated_summary': '\n'.join(translated_text.split('\n')[1:]).replace('内容: ', '').strip()
            })
            
        except Exception as e:
            logger.error(f"翻译第 {i} 条新闻失败: {str(e)}")
            translated_list.append(news)
    
    logger.info("批量翻译完成")
    return translated_list
