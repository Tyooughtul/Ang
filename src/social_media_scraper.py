import logging
import requests
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class SocialMediaScraper:
    """社交媒体抓取器：获取一手资讯"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
    
    def fetch_reddit_hot(self, subreddit: str, limit: int = 5) -> List[Dict]:
        """
        获取 Reddit 热门帖子
        
        Args:
            subreddit: 子版块名称（如 'rust', 'programming', 'webdev'）
            limit: 获取数量
        
        Returns:
            帖子列表
        """
        try:
            logger.info(f"获取 Reddit r/{subreddit} 热门帖子...")
            
            url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit={limit}"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            posts = []
            
            for post in data['data']['children'][:limit]:
                post_data = post['data']
                
                posts.append({
                    'title': post_data.get('title', ''),
                    'content': post_data.get('selftext', '')[:500],
                    'url': f"https://reddit.com{post_data.get('permalink', '')}",
                    'author': post_data.get('author', ''),
                    'score': post_data.get('score', 0),
                    'num_comments': post_data.get('num_comments', 0),
                    'created_utc': post_data.get('created_utc', 0),
                    'subreddit': subreddit,
                    'platform': 'reddit',
                    'type': 'post'
                })
            
            logger.info(f"成功获取 {len(posts)} 条 Reddit 帖子")
            return posts
            
        except Exception as e:
            logger.error(f"获取 Reddit 帖子失败: {str(e)}")
            return []
    
    def fetch_reddit_new(self, subreddit: str, limit: int = 5) -> List[Dict]:
        """
        获取 Reddit 最新帖子
        
        Args:
            subreddit: 子版块名称
            limit: 获取数量
        
        Returns:
            帖子列表
        """
        try:
            logger.info(f"获取 Reddit r/{subreddit} 最新帖子...")
            
            url = f"https://www.reddit.com/r/{subreddit}/new.json?limit={limit}"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            posts = []
            
            for post in data['data']['children'][:limit]:
                post_data = post['data']
                
                posts.append({
                    'title': post_data.get('title', ''),
                    'content': post_data.get('selftext', '')[:500],
                    'url': f"https://reddit.com{post_data.get('permalink', '')}",
                    'author': post_data.get('author', ''),
                    'score': post_data.get('score', 0),
                    'num_comments': post_data.get('num_comments', 0),
                    'created_utc': post_data.get('created_utc', 0),
                    'subreddit': subreddit,
                    'platform': 'reddit',
                    'type': 'post'
                })
            
            logger.info(f"成功获取 {len(posts)} 条 Reddit 最新帖子")
            return posts
            
        except Exception as e:
            logger.error(f"获取 Reddit 最新帖子失败: {str(e)}")
            return []
    
    def fetch_github_trending(self, language: str = 'python', limit: int = 5) -> List[Dict]:
        """
        获取 GitHub 趋势仓库（通过 GitHub API）
        
        Args:
            language: 编程语言
            limit: 获取数量
        
        Returns:
            仓库列表
        """
        try:
            logger.info(f"获取 GitHub {language} 趋势仓库...")
            
            url = f"https://api.github.com/search/repositories?q=language:{language}&sort=stars&order=desc&per_page={limit}"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            repos = []
            
            for repo in data.get('items', [])[:limit]:
                repos.append({
                    'title': repo.get('name', ''),
                    'content': repo.get('description', '')[:300],
                    'url': repo.get('html_url', ''),
                    'author': repo.get('owner', {}).get('login', ''),
                    'stars': repo.get('stargazers_count', 0),
                    'forks': repo.get('forks_count', 0),
                    'language': repo.get('language', ''),
                    'created_at': repo.get('created_at', ''),
                    'platform': 'github',
                    'type': 'repository'
                })
            
            logger.info(f"成功获取 {len(repos)} 个 GitHub 仓库")
            return repos
            
        except Exception as e:
            logger.error(f"获取 GitHub 趋势失败: {str(e)}")
            return []
    
    def fetch_hacker_news(self, limit: int = 5) -> List[Dict]:
        """
        获取 Hacker News 热门帖子
        
        Args:
            limit: 获取数量
        
        Returns:
            帖子列表
        """
        try:
            logger.info("获取 Hacker News 热门帖子...")
            
            url = "https://hacker-news.firebaseio.com/v0/topstories.json"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            story_ids = response.json()[:limit]
            posts = []
            
            for story_id in story_ids:
                detail_url = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
                detail_response = self.session.get(detail_url, timeout=10)
                detail_response.raise_for_status()
                
                story_data = detail_response.json()
                
                if story_data:
                    posts.append({
                        'title': story_data.get('title', ''),
                        'content': story_data.get('text', '')[:300] if story_data.get('text') else '',
                        'url': story_data.get('url', ''),
                        'author': story_data.get('by', ''),
                        'score': story_data.get('score', 0),
                        'num_comments': story_data.get('descendants', 0),
                        'created_utc': story_data.get('time', 0),
                        'platform': 'hackernews',
                        'type': 'post'
                    })
            
            logger.info(f"成功获取 {len(posts)} 条 Hacker News 帖子")
            return posts
            
        except Exception as e:
            logger.error(f"获取 Hacker News 失败: {str(e)}")
            return []
    
    def fetch_dev_to(self, limit: int = 5) -> List[Dict]:
        """
        获取 Dev.to 热门帖子
        
        Args:
            limit: 获取数量
        
        Returns:
            帖子列表
        """
        try:
            logger.info("获取 Dev.to 热门帖子...")
            
            url = f"https://dev.to/api/articles?top=7&per_page={limit}"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            articles = response.json()
            posts = []
            
            for article in articles[:limit]:
                posts.append({
                    'title': article.get('title', ''),
                    'content': article.get('description', '')[:300],
                    'url': article.get('url', ''),
                    'author': article.get('user', {}).get('name', ''),
                    'score': article.get('positive_reactions_count', 0),
                    'num_comments': article.get('comments_count', 0),
                    'created_utc': article.get('published_timestamp', 0),
                    'platform': 'devto',
                    'type': 'article'
                })
            
            logger.info(f"成功获取 {len(posts)} 条 Dev.to 帖子")
            return posts
            
        except Exception as e:
            logger.error(f"获取 Dev.to 失败: {str(e)}")
            return []
    
    def fetch_from_multiple_sources(self, sources: List[Dict]) -> List[Dict]:
        """
        从多个来源获取内容
        
        Args:
            sources: 来源列表，格式 [{'platform': 'reddit', 'subreddit': 'rust', 'limit': 3}]
        
        Returns:
            所有内容的列表
        """
        all_posts = []
        
        for source in sources:
            platform = source.get('platform')
            
            if platform == 'reddit':
                subreddit = source.get('subreddit', 'programming')
                limit = source.get('limit', 3)
                posts = self.fetch_reddit_hot(subreddit, limit)
                all_posts.extend(posts)
            
            elif platform == 'github':
                language = source.get('language', 'python')
                limit = source.get('limit', 3)
                repos = self.fetch_github_trending(language, limit)
                all_posts.extend(repos)
            
            elif platform == 'hackernews':
                limit = source.get('limit', 3)
                posts = self.fetch_hacker_news(limit)
                all_posts.extend(posts)
            
            elif platform == 'devto':
                limit = source.get('limit', 3)
                posts = self.fetch_dev_to(limit)
                all_posts.extend(posts)
        
        logger.info(f"总共获取 {len(all_posts)} 条内容")
        return all_posts
    
    def format_posts(self, posts: List[Dict]) -> str:
        """
        格式化帖子为文本
        
        Args:
            posts: 帖子列表
        
        Returns:
            格式化后的文本
        """
        if not posts:
            return ""
        
        formatted_text = []
        for i, post in enumerate(posts, 1):
            platform_name = post.get('platform', '').upper()
            title = post.get('title', '')
            content = post.get('content', '')
            url = post.get('url', '')
            author = post.get('author', '')
            score = post.get('score', 0)
            
            formatted_text.append(f"{i}. [{platform_name}] {title}")
            formatted_text.append(f"   作者: {author} | 热度: {score}")
            formatted_text.append(f"   内容: {content}")
            formatted_text.append(f"   链接: {url}")
            formatted_text.append("")
        
        return "\n".join(formatted_text)
