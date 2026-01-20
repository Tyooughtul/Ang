import logging
import json
import os
from typing import Dict, List, Optional
# from tavily import TavilyClient  <-- 移除不兼容的 SDK
from .simple_tavily import SimpleTavilyClient as TavilyClient
from .config import TAVILY_API_KEY

logger = logging.getLogger(__name__)

class WebSearcher:
    """Web 搜索器：使用 Tavily (推荐) 进行智能搜索"""
    
    def __init__(self, api_key: str = None):
        # 1. 优先初始化 Tavily
        self.tavily_api_key = TAVILY_API_KEY
        self.tavily_client = None
        
        if self.tavily_api_key:
            try:
                self.tavily_client = TavilyClient(api_key=self.tavily_api_key)
                logger.info("Tavily 搜索客户端初始化成功")
            except Exception as e:
                logger.error(f"Tavily 客户端初始化失败: {e}")
        else:
            logger.warning("未检测到 TAVILY_API_KEY，搜索功能将受限")

        # 2. 保留原有的 GLM Key 仅为了兼容接口调用，不再初始化复杂配置
        self.legacy_api_key = api_key
    
    def search_topic(self, topic: str, max_results: int = 5) -> List[Dict]:
        """
        搜索话题相关信息
        """
        if self.tavily_client:
            return self._search_with_tavily(topic, max_results)
        
        logger.warning("没有可用的搜索客户端 (Tavily 未配置)")
        return []

    def _search_with_tavily(self, topic: str, max_results: int) -> List[Dict]:
        """使用 Tavily 进行搜索"""
        try:
            logger.info(f"使用 Tavily 搜索话题: {topic}...")
            response = self.tavily_client.search(
                query=topic, 
                search_depth="advanced", 
                max_results=max_results
            )
            
            results = []
            for result in response.get('results', []):
                results.append({
                    'title': result.get('title', '无标题'),
                    'summary': result.get('content', '')[:800],
                    'link': result.get('url', ''),
                    'published': result.get('published_date', ''), 
                    'source': 'Tavily API'
                })
            
            if response.get('answer'):
                logger.info(f"Tavily Answer: {response.get('answer')[:100]}...")
                
            return results
        except Exception as e:
            logger.error(f"Tavily 搜索失败: {e}")
            return []

    def verify_fact(self, claim: str) -> Dict:
        """[DEPRECATED] 简化的事实验证（仅搜索相关信息）"""
        return {
            "is_true": None,
            "confidence": 0,
            "reasoning": "Function deprecated to save tokens",
            "sources": [],
            "search_results": []
        }
    
    def check_freshness_with_search(self, topic: str, content: str) -> Dict:
        """[DEPRECATED] 简化的新鲜度检查"""
        return {
            "is_fresh": None,
            "freshness_level": "未知",
            "score": 0,
            "reasoning": "Function deprecated to save tokens",
            "latest_info": "",
            "search_results": []
        }
