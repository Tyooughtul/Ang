import feedparser
import logging
from typing import List, Dict
from .config import RSS_SOURCES, NEWS_LIMIT

logger = logging.getLogger(__name__)

def fetch_news(rss_urls: List[str] = None, limit: int = None) -> List[Dict]:
    """
    从多个 RSS 源获取最新新闻
    
    Args:
        rss_urls: RSS 源列表，默认使用配置文件中的源
        limit: 每个 RSS 源获取的新闻数量，默认使用配置文件中的限制
    
    Returns:
        新闻列表，格式: [{'title': str, 'summary': str, 'link': str, 'published': str}]
    """
    if rss_urls is None:
        rss_urls = RSS_SOURCES
    if limit is None:
        limit = NEWS_LIMIT
    
    all_news = []
    
    for url in rss_urls:
        try:
            logger.info(f"正在获取 RSS 源: {url}")
            feed = feedparser.parse(url)
            
            if feed.bozo:
                logger.warning(f"RSS 源解析失败: {url}, 错误: {feed.bozo_exception}")
                continue
            
            for entry in feed.entries[:limit]:
                title = entry.get('title', '').strip()
                summary = entry.get('summary', '').strip()
                
                if not title or not summary:
                    continue
                
                all_news.append({
                    'title': title,
                    'summary': summary,
                    'link': entry.get('link', ''),
                    'published': entry.get('published', ''),
                    'source': feed.feed.get('title', url)
                })
            
            logger.info(f"从 {url} 获取了 {len(feed.entries[:limit])} 条新闻")
            
        except Exception as e:
            logger.error(f"获取 RSS 源失败: {url}, 错误: {str(e)}")
            continue
    
    logger.info(f"总共获取了 {len(all_news)} 条新闻")
    return all_news

def format_news(news_list: List[Dict]) -> str:
    """
    将新闻列表格式化为文本
    
    Args:
        news_list: 新闻列表
    
    Returns:
        格式化后的文本
    """
    if not news_list:
        return ""
    
    formatted_text = []
    for i, item in enumerate(news_list, 1):
        formatted_text.append(f"{i}. {item['title']}\n{item['summary']}\n")
    
    return "\n".join(formatted_text)

def get_mock_data() -> List[Dict]:
    """
    返回固定的测试数据，用于开发测试
    
    Returns:
        模拟新闻列表
    """
    return [
        {
            'title': 'OpenAI 发布 GPT-5，性能提升 300%',
            'summary': 'OpenAI 今日正式发布 GPT-5 模型，相比 GPT-4 性能提升 300%，支持多模态输入输出，推理能力大幅增强。新模型在代码生成、数学推理和创意写作方面表现出色。',
            'link': 'https://example.com/news/1',
            'published': '2025-01-17',
            'source': 'Mock Data'
        },
        {
            'title': '苹果发布 Vision Pro 2，价格降低 50%',
            'summary': '苹果今日发布 Vision Pro 2，新设备重量减轻 40%，电池续航提升至 8 小时，价格从 3499 美元降至 1749 美元。新设备支持更多原生应用和手势交互。',
            'link': 'https://example.com/news/2',
            'published': '2025-01-17',
            'source': 'Mock Data'
        },
        {
            'title': '特斯拉 Optimus 机器人开始量产',
            'summary': '特斯拉宣布 Optimus 机器人开始量产，预计年产量 10 万台。机器人能够执行家务、搬运等任务，售价 2 万美元。马斯克表示未来将推出更便宜的版本。',
            'link': 'https://example.com/news/3',
            'published': '2025-01-17',
            'source': 'Mock Data'
        }
    ]
