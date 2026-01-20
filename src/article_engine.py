import logging
import os
import json
from datetime import datetime
from .config import ARTICLE_SYSTEM_PROMPT, ARTICLE_OUTPUT
from .llm_engine import generate_script_with_retry

logger = logging.getLogger(__name__)

def generate_outline(news_text: str) -> str:
    """生成文章大纲"""
    prompt = f"""任务：根据以下新闻素材，为一篇深度科技文章规划一个详细的大纲。

新闻素材：
{news_text}

要求：
1. 标题：设计3个吸引人的备选标题。
2. 结构：包含引言、3-5个核心段落（每段明确一个核心观点）、结语。
3. 角度：不要平铺直叙，要找到新闻背后的趋势或对行业的影响。
4. 读者：面向科技爱好者和从业者。

请直接输出大纲内容。"""
    
    logger.info("Step 1: 正在生成大纲...")
    return generate_script_with_retry(prompt, system_prompt="你是一个逻辑严密的文章架构师。")

def optimize_outline(outline: str) -> str:
    """(可选) 优化大纲 - 模拟 Reviewer 角色"""
    prompt = f"""任务：作为一名资深主编，请优化以下文章大纲。

当前大纲：
{outline}

要求：
1. 检查逻辑是否连贯。
2. 确保观点够犀利，不是陈词滥调。
3. 如果某些部分太单薄，通过联想补充一些背景或预测。
4. 输出最终确认的优化版大纲。"""
    
    logger.info("Step 2: 正在优化大纲 (Reviewer Mode)...")
    return generate_script_with_retry(prompt, system_prompt="你是一个挑剔的资深科技主编。")

def write_full_article(news_text: str, outline: str) -> str:
    """根据大纲生成全文"""
    prompt = f"""任务：根据以下大纲和素材，撰写一篇完整的深度科技文章。

大纲：
{outline}

新闻素材：
{news_text}

要求：
1. 严格遵循大纲的结构（你可以选择大纲中最好的那个标题）。
2. 语言风格：专业、客观但有温度，类似“少数派”或“36氪”的深度稿件。
3. 字数：1500字左右。
4. 格式：使用 Markdown，重点内容加粗。

请直接开始写作。"""
    
    logger.info("Step 3: 正在撰写正文 (Writer Mode)...")
    return generate_script_with_retry(prompt, system_prompt="你是一个文笔极佳的科技专栏作家。")


def generate_article(news_list: list, output_path: str = None) -> str:
    """
    生成科技文章（采用多步生成策略：Cot）
    """
    if output_path is None:
        output_path = ARTICLE_OUTPUT
    
    try:
        logger.info("开始多步生成文章流程 (Chain of Thought)...")
        
        # 0. 准备素材
        news_text = ""
        for i, news in enumerate(news_list, 1):
             # Tavily 清洗过的数据可能没有 summary 字段，或者叫 content
            content = news.get('summary') or news.get('content') or ""
            news_text += f"【新闻 {i}】{news.get('title')}\n{content[:800]}\n来源：{news.get('source')}\n\n"
        
        logger.info(f"素材准备完毕，长度: {len(news_text)} 字符")
        
        # 1. 生成大纲
        outline = generate_outline(news_text)
        logger.debug(f"大纲生成完毕:\n{outline[:200]}...")
        
        # 2. 优化大纲 (Reviewer 介入)
        # 这里把 reviewer 和 writer 分开了，reviewer 只review 大纲，大大节省 token
        refined_outline = optimize_outline(outline)
        
        # 3. 撰写正文
        article = write_full_article(news_text, refined_outline)
        
        if not article or len(article.strip()) < 100:
            logger.error("生成的文章过短，可能无效")
            raise ValueError("文章生成失败")
        
        logger.info(f"文章生成成功，长度: {len(article)} 字符")
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(article)
        
        logger.info(f"文章已保存至: {output_path}")
        
        return output_path
        
    except Exception as e:
        logger.error(f"生成文章失败: {str(e)}")
        raise

def generate_xiaohongshu_article(news_list: list, output_path: str = None) -> str:
    """
    生成小红书风格的文章
    
    Args:
        news_list: 新闻列表
        output_path: 文章输出路径
    
    Returns:
        文章文件路径
    """
    if output_path is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = os.path.join(os.path.dirname(ARTICLE_OUTPUT), f'xiaohongshu_{timestamp}.md')
    
    try:
        logger.info("开始生成小红书风格文章...")
        
        xiaohongshu_prompt = """你是一个小红书科技博主，擅长用轻松活泼的语言分享科技资讯。
任务：将以下新闻摘要改写成一篇小红书风格的科技文章。
要求：
1. 标题要吸睛，使用表情符号，如"🔥"、"✨"、"💡"
2. 开头要有互动，如"姐妹们！"、"宝子们！"
3. 正文要分段，每段不要太长
4. 多用表情符号增加趣味性
5. 结尾要有互动提问，引导评论
6. 添加相关标签（#科技 #AI #数码等）
7. 语言要口语化，像和朋友聊天一样"""
        
        news_text = ""
        for i, news in enumerate(news_list, 1):
            news_text += f"{i}. {news['title']}\n{news['summary']}\n\n"
        
        article = generate_script_with_retry(news_text, system_prompt=xiaohongshu_prompt)
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(article)
        
        logger.info(f"小红书文章已保存至: {output_path}")
        
        return output_path
        
    except Exception as e:
        logger.error(f"生成小红书文章失败: {str(e)}")
        raise

def generate_zhihu_article(news_list: list, output_path: str = None) -> str:
    """
    生成知乎风格的文章
    
    Args:
        news_list: 新闻列表
        output_path: 文章输出路径
    
    Returns:
        文章文件路径
    """
    if output_path is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = os.path.join(os.path.dirname(ARTICLE_OUTPUT), f'zhihu_{timestamp}.md')
    
    try:
        logger.info("开始生成知乎风格文章...")
        
        zhihu_prompt = """你是一个知乎科技领域的专业答主，擅长深度分析科技新闻。
任务：将以下新闻摘要改写成一篇知乎风格的深度文章。
要求：
1. 标题要专业且有吸引力，如"如何看待..."、"深度解析..."
2. 正文要有深度分析，不能只是简单复述新闻
3. 加入行业背景、技术原理、影响分析
4. 使用数据和案例支撑观点
5. 语言要专业但不晦涩，适合知乎用户阅读
6. 文章结构清晰，有引言、正文、结语
7. 适当引用相关资料和链接
8. 避免使用表情符号，保持专业感"""
        
        news_text = ""
        for i, news in enumerate(news_list, 1):
            news_text += f"{i}. {news['title']}\n{news['summary']}\n\n"
        
        article = generate_script_with_retry(news_text, system_prompt=zhihu_prompt)
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(article)
        
        logger.info(f"知乎文章已保存至: {output_path}")
        
        return output_path
        
    except Exception as e:
        logger.error(f"生成知乎文章失败: {str(e)}")
        raise

def generate_wechat_article(news_list: list, output_path: str = None) -> str:
    """
    生成微信公众号风格的文章
    
    Args:
        news_list: 新闻列表
        output_path: 文章输出路径
    
    Returns:
        文章文件路径
    """
    if output_path is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = os.path.join(os.path.dirname(ARTICLE_OUTPUT), f'wechat_{timestamp}.md')
    
    try:
        logger.info("开始生成微信公众号风格文章...")
        
        wechat_prompt = """你是一个微信公众号科技编辑，擅长撰写高质量的科技文章。
任务：将以下新闻摘要改写成一篇微信公众号风格的科技文章。
要求：
1. 标题要有吸引力，适合微信传播
2. 正文要有深度，兼顾专业性和可读性
3. 加入行业背景、技术解析、市场影响
4. 适当使用小标题分割内容
5. 语言要流畅，适合移动端阅读
6. 文章结构清晰，有引言、正文、结语
7. 可以适当使用表情符号，但不要过多
8. 结尾可以引导关注和分享"""
        
        news_text = ""
        for i, news in enumerate(news_list, 1):
            news_text += f"{i}. {news['title']}\n{news['summary']}\n\n"
        
        article = generate_script_with_retry(news_text, system_prompt=wechat_prompt)
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(article)
        
        logger.info(f"微信公众号文章已保存至: {output_path}")
        
        return output_path
        
    except Exception as e:
        logger.error(f"生成微信公众号文章失败: {str(e)}")
        raise

def generate_article_metadata(news_list: list, article_path: str) -> dict:
    """
    生成文章元数据
    
    Args:
        news_list: 新闻列表
        article_path: 文章文件路径
    
    Returns:
        文章元数据字典
    """
    try:
        with open(article_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        metadata = {
            'title': f"科技早报 - {datetime.now().strftime('%Y年%m月%d日')}",
            'summary': f"本期涵盖 {len(news_list)} 条最新科技新闻",
            'word_count': len(content),
            'news_count': len(news_list),
            'tags': [news['title'].split()[0] for news in news_list[:5]],
            'pub_date': datetime.now().isoformat(),
            'platform': '通用'
        }
        
        logger.info(f"文章元数据生成成功: {metadata['title']}")
        return metadata
        
    except Exception as e:
        logger.error(f"生成文章元数据失败: {str(e)}")
        return {}

def format_article_for_platform(article_path: str, platform: str) -> str:
    """
    根据平台格式化文章
    
    Args:
        article_path: 文章文件路径
        platform: 平台名称（xiaohongshu, zhihu, wechat）
    
    Returns:
        格式化后的文章内容
    """
    try:
        with open(article_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if platform == 'xiaohongshu':
            return content
        elif platform == 'zhihu':
            return content
        elif platform == 'wechat':
            return content
        else:
            return content
            
    except Exception as e:
        logger.error(f"格式化文章失败: {str(e)}")
        return ""
