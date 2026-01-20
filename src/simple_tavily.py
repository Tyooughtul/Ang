from typing import Dict, List, Optional
import requests
import logging

logger = logging.getLogger(__name__)

class SimpleTavilyClient:
    """简单的 Tavily 客户端，使用 request 直接调用，兼容 Python 3.8"""
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.tavily.com/search"

    def search(self, query: str, search_depth: str = "basic", max_results: int = 5, **kwargs) -> Dict:
        payload = {
            "api_key": self.api_key,
            "query": query,
            "search_depth": search_depth,
            "max_results": max_results,
            **kwargs
        }
        
        try:
             response = requests.post(self.base_url, json=payload, timeout=30)
             response.raise_for_status()
             return response.json()
        except Exception as e:
             logger.error(f"Tavily request failed: {e}")
             raise
