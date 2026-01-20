import logging
import random
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class TopicSelector:
    """话题选择器：选择并聚焦具体话题"""
    
    def __init__(self):
        self.topic_categories = {
            'programming_languages': {
                'name': '编程语言',
                'topics': [
                    'Rust 新版本发布',
                    'Zig 社区动态',
                    'WebAssembly 更新',
                    'Python 新特性',
                    'Go 语言进展',
                    'TypeScript 新版本',
                    'JavaScript 框架更新'
                ]
            },
            'tech_companies': {
                'name': '科技公司',
                'topics': [
                    'OpenAI 新模型发布',
                    'Google 技术报告',
                    'Microsoft 开发者工具',
                    'Meta 开源项目',
                    'Apple 开发者大会',
                    'Amazon 云服务更新',
                    'NVIDIA AI 芯片'
                ]
            },
            'developer_tools': {
                'name': '开发者工具',
                'topics': [
                    'VS Code 新功能',
                    'Docker 更新',
                    'Kubernetes 新版本',
                    'GitHub 新功能',
                    'npm 包更新',
                    'Webpack 新版本',
                    'Vite 框架进展'
                ]
            },
            'ai_ml': {
                'name': '人工智能与机器学习',
                'topics': [
                    'GPT-4 新能力',
                    'Claude 模型更新',
                    'LLaMA 开源模型',
                    'Stable Diffusion 新版本',
                    'TensorFlow 更新',
                    'PyTorch 新特性',
                    'Hugging Face 新模型'
                ]
            },
            'web_development': {
                'name': 'Web 开发',
                'topics': [
                    'React 新版本',
                    'Vue.js 更新',
                    'Next.js 新功能',
                    'Astro 框架进展',
                    'Svelte 新特性',
                    'Tailwind CSS 更新',
                    'Web 标准更新'
                ]
            },
            'cloud_infrastructure': {
                'name': '云与基础设施',
                'topics': [
                    'AWS 新服务',
                    'Google Cloud 更新',
                    'Azure AI 服务',
                    'Vercel 新功能',
                    'Netlify 更新',
                    'Cloudflare Workers',
                    'Deno 新版本'
                ]
            },
            'open_source': {
                'name': '开源项目',
                'topics': [
                    'Linux 内核更新',
                    'Git 新版本',
                    'PostgreSQL 新特性',
                    'Redis 更新',
                    'Nginx 新版本',
                    'Apache 更新',
                    'Firefox 新版本'
                ]
            },
            'events_conferences': {
                'name': '会议与活动',
                'topics': [
                    'PyCon 大会',
                    'RustConf 会议',
                    'React Conf',
                    'Google I/O',
                    'Apple WWDC',
                    'Microsoft Build',
                    'AWS re:Invent'
                ]
            }
        }
    
    def select_random_topic(self, category: str = None) -> Dict:
        """
        随机选择一个话题
        
        Args:
            category: 话题类别，如果为 None 则随机选择类别
        
        Returns:
            话题字典
        """
        if category:
            if category not in self.topic_categories:
                logger.warning(f"类别 {category} 不存在，使用随机类别")
                category = None
        
        if not category:
            category = random.choice(list(self.topic_categories.keys()))
        
        topics = self.topic_categories[category]['topics']
        selected_topic = random.choice(topics)
        
        result = {
            'category': category,
            'category_name': self.topic_categories[category]['name'],
            'topic': selected_topic,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"选择话题: {selected_topic} (类别: {category})")
        return result
    
    def select_topic_by_trending(self, trending_topics: List[str]) -> Dict:
        """
        根据趋势话题选择
        
        Args:
            trending_topics: 趋势话题列表
        
        Returns:
            话题字典
        """
        if not trending_topics:
            return self.select_random_topic()
        
        selected_topic = random.choice(trending_topics)
        
        result = {
            'category': 'trending',
            'category_name': '趋势话题',
            'topic': selected_topic,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"选择趋势话题: {selected_topic}")
        return result
    
    def select_topic_by_keyword(self, keyword: str) -> Optional[Dict]:
        """
        根据关键词选择话题
        
        Args:
            keyword: 关键词
        
        Returns:
            话题字典，如果未找到则返回 None
        """
        for category, data in self.topic_categories.items():
            for topic in data['topics']:
                if keyword.lower() in topic.lower():
                    result = {
                        'category': category,
                        'category_name': data['name'],
                        'topic': topic,
                        'timestamp': datetime.now().isoformat()
                    }
                    logger.info(f"根据关键词选择话题: {topic}")
                    return result
        
        logger.warning(f"未找到包含关键词 '{keyword}' 的话题")
        return None
    
    def get_all_categories(self) -> List[str]:
        """
        获取所有类别
        
        Returns:
            类别列表
        """
        return list(self.topic_categories.keys())
    
    def get_topics_by_category(self, category: str) -> List[str]:
        """
        获取指定类别的所有话题
        
        Args:
            category: 类别名称
        
        Returns:
            话题列表
        """
        if category not in self.topic_categories:
            logger.warning(f"类别 {category} 不存在")
            return []
        
        return self.topic_categories[category]['topics']
    
    def generate_deep_dive_prompt(self, topic: str, category: str) -> str:
        """
        生成深度分析的提示词
        
        Args:
            topic: 话题
            category: 类别
        
        Returns:
            深度分析提示词
        """
        category_name = self.topic_categories.get(category, {}).get('name', '科技')
        
        prompt = f"""你是一个{category_name}领域的深度分析师，擅长从多个角度深入分析技术话题。

任务：对以下话题进行深度分析

话题：{topic}

要求：
1. **背景介绍**：提供话题的背景信息，包括历史、现状
2. **技术细节**：深入分析技术细节、实现原理、关键特性
3. **影响分析**：分析这个话题对行业、开发者、用户的影响
4. **对比分析**：与相关技术或产品进行对比
5. **未来展望**：预测这个话题的发展趋势和可能的变化
6. **实践建议**：给开发者或用户的实践建议
7. **争议点**：指出这个话题存在的争议或不同观点

输出格式：
# {topic}

## 背景介绍
[详细背景信息]

## 技术细节
[深入技术分析]

## 影响分析
[对行业、开发者、用户的影响]

## 对比分析
[与相关技术的对比]

## 未来展望
[发展趋势预测]

## 实践建议
[给开发者或用户的建议]

## 争议点
[存在的争议或不同观点]

## 总结
[简洁的总结]

要求：
- 每个部分都要有实质性内容，不能泛泛而谈
- 使用具体的数据、案例、引用
- 语言要专业但不晦涩
- 适合播客和文章两种形式"""
        
        return prompt
    
    def generate_podcast_prompt(self, topic: str, category: str) -> str:
        """
        生成播客专用的提示词
        
        Args:
            topic: 话题
            category: 类别
        
        Returns:
            播客提示词
        """
        category_name = self.topic_categories.get(category, {}).get('name', '科技')
        
        prompt = f"""你是一个{category_name}领域的播客主播，擅长用轻松幽默的方式深入讲解技术话题。

任务：为以下话题创作一集播客

话题：{topic}

要求：
1. **开场白**：用有趣的方式开场，吸引听众注意力
2. **背景介绍**：简单介绍话题背景，让听众快速了解
3. **深度讲解**：分层次讲解，从浅入深
4. **个人观点**：加入你的个人观点和见解
5. **互动提问**：在适当的地方提出问题，引发思考
6. **总结回顾**：用简洁的方式总结要点
7. **结尾互动**：鼓励听众评论、分享

播客时长：约 10-15 分钟

语言风格：
- 口语化，像和朋友聊天
- 适当使用比喻和例子
- 幽默但不失专业
- 避免过于技术化的术语

输出格式：
【开场白】
[有趣的开场]

【背景介绍】
[背景信息]

【深度讲解】
[分层次讲解]

【个人观点】
[你的见解]

【总结回顾】
[要点总结]

【结尾互动】
[鼓励互动]"""
        
        return prompt
    
    def generate_article_prompt(self, topic: str, category: str, platform: str = 'general') -> str:
        """
        生成文章专用的提示词
        
        Args:
            topic: 话题
            category: 类别
            platform: 平台（general/xiaohongshu/zhihu）
        
        Returns:
            文章提示词
        """
        category_name = self.topic_categories.get(category, {}).get('name', '科技')
        
        if platform == 'xiaohongshu':
            prompt = f"""你是一个小红书{category_name}博主，擅长用轻松活泼的方式分享技术知识。

任务：为以下话题创作一篇小红书文章

话题：{topic}

要求：
1. **标题吸睛**：使用表情符号，如"🔥"、"✨"、"💡"
2. **开头互动**：如"姐妹们！"、"宝子们！"
3. **内容实用**：提供实用的知识点和技巧
4. **分段清晰**：每段不要太长，适合手机阅读
5. **表情符号**：适当使用增加趣味性
6. **结尾互动**：引导评论和分享
7. **标签**：添加相关标签（#科技 #AI #编程等）

文章结构：
- 吸睛标题
- 开场互动
- 核心内容（分段）
- 实用技巧
- 结尾互动
- 相关标签"""
        
        elif platform == 'zhihu':
            prompt = f"""你是一个知乎{category_name}领域的专业答主，擅长深度分析技术话题。

任务：为以下话题创作一篇知乎深度文章

话题：{topic}

要求：
1. **标题专业**：如"如何看待..."、"深度解析..."
2. **深度分析**：不能只是简单介绍，要有深度思考
3. **数据支撑**：使用具体的数据、案例、引用
4. **逻辑清晰**：文章结构清晰，有引言、正文、结语
5. **专业但不晦涩**：适合知乎用户阅读
6. **避免表情符号**：保持专业感
7. **引用资料**：适当引用相关资料和链接

文章结构：
- 专业标题
- 引言（提出问题）
- 正文（分点分析）
- 案例分析
- 结论（总结观点）"""
        
        else:
            prompt = f"""你是一个{category_name}领域的专业编辑，擅长撰写深度技术文章。

任务：为以下话题创作一篇深度技术文章

话题：{topic}

要求：
1. **标题吸引**：适合社交媒体传播
2. **深度分析**：有深度思考，不能泛泛而谈
3. **技术细节**：深入分析技术原理和实现
4. **影响分析**：分析对行业和开发者的影响
5. **实践建议**：给开发者的具体建议
6. **结构清晰**：引言、正文、结语
7. **适当排版**：适合移动端阅读

文章结构：
- 吸引标题
- 引言（背景介绍）
- 正文（深度分析）
- 技术细节
- 影响分析
- 实践建议
- 结语（总结）"""
        
        return prompt
