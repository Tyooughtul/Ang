import logging
import os
import json
import re
from datetime import datetime
from .config import PODCAST_SYSTEM_PROMPT, AUDIO_OUTPUT, SCRIPT_OUTPUT
from .llm_engine import generate_script_with_retry
from .tts_engine import generate_audio

logger = logging.getLogger(__name__)

def generate_dialogue_script(news_text: str) -> list:
    """
    生成双人对话剧本
    Host (老杨): 沉稳专业
    Guest (小七): 犀利幽默毒舌
    """
    prompt = f"""任务：将以下科技新闻改编成一段引人入胜的双人播客对话剧本。

【角色设定】
Host (主持人): 名字叫“老杨”。沉稳专业，声音温暖，负责控场、引导话题、总结。
Guest (嘉宾): 名字叫“小七”。科技极客，年轻，犀利、幽默、喜欢吐槽，说话直白，经常打比方。

【新闻素材】
{news_text}

【要求】
1. 必须生成 JSON 格式的列表，不要任何 Markdown 标记。
2. 保持对话自然，加入口语化词汇（如"哎"、"我去"、"那个啥"）。
3. 嘉宾可以打断主持人，或者用反问句。
4. 开头要寒暄，结尾要互动。
5. 总长度控制在 8-15 轮对话。

【重要】输出示例：
[
    {{"role": "Host", "text": "大家好，欢迎收听今天的科技茶馆，我是老杨。"}},
    {{"role": "Guest", "text": "我是小七！今天这新闻可太炸裂了，看得我下巴都掉了。"}},
    {{"role": "Host", "text": "哦？是因为那个新发布的模型吗？"}}
]"""

    logger.info("正在生成双人对话剧本 (LLM)...")
    response_text = generate_script_with_retry(prompt, system_prompt="你是一个王牌播客制作人，擅长编写像《脱口秀大会》一样幽默自然的对话稿。")
    
    # 清洗数据，提取 JSON
    try:
        clean_text = re.sub(r'```json\s*', '', response_text)
        clean_text = re.sub(r'```\s*', '', clean_text)
        clean_text = clean_text.strip()
        
        script_json = json.loads(clean_text)
        logger.info(f"✅ 剧本解析成功，共 {len(script_json)} 轮对话")
        return script_json
        
    except json.JSONDecodeError:
        logger.error("❌ LLM 返回的不是有效的 JSON，回退到空列表")
        logger.debug(f"Raw Response: {response_text}")
        return []

async def generate_podcast(news_text: str, output_path: str = None, script_path: str = None) -> tuple:
    """
    生成双人播客音频和脚本 (Podcast 2.0)
    """
    if output_path is None:
        output_path = AUDIO_OUTPUT
    if script_path is None:
        script_path = SCRIPT_OUTPUT
    
    try:
        logger.info("🎬 开始制作双人播客...")
        
        # Step 1: LLM 写剧本
        logger.info("Step 1: 生成双人对话脚本")
        dialogue_script = generate_dialogue_script(news_text)
        
        if not dialogue_script:
            raise ValueError("剧本生成失败或为空")
        
        # 保存剧本 (JSON 格式方便调试，也可以转成 txt)
        os.makedirs(os.path.dirname(script_path), exist_ok=True)
        with open(script_path, 'w', encoding='utf-8') as f:
            json.dump(dialogue_script, f, ensure_ascii=False, indent=2)
            
        # 顺便存一个人类可读的 txt
        readable_script_path = script_path.replace('.json', '.txt').replace('.xml', '.txt')
        with open(readable_script_path, 'w', encoding='utf-8') as f:
             for line in dialogue_script:
                 f.write(f"[{line['role']}]: {line['text']}\n")
        
        logger.info(f"📝 剧本已保存: {script_path}")
        
        # Step 2: TTS 生成混音
        logger.info("Step 2: 语音合成与混音 (BGM)...")
        audio_path = await generate_audio(dialogue_script, output_path=output_path)
        logger.info(f"🎧 播客制作完成: {audio_path}")
        
        return audio_path, script_path
        
    except Exception as e:
        logger.error(f"❌ 生成播客失败: {str(e)}")
        raise

def generate_podcast_metadata(news_list: list, audio_path: str) -> dict:
    """
    生成播客元数据
    
    Args:
        news_list: 新闻列表
        audio_path: 音频文件路径
    
    Returns:
        播客元数据字典
    """
    try:
        from .tts_engine import get_audio_duration
        
        duration = get_audio_duration(audio_path)
        
        metadata = {
            'title': f"科技早报 - {datetime.now().strftime('%Y年%m月%d日')}",
            'description': f"本期播客涵盖 {len(news_list)} 条最新科技新闻，包括：{', '.join([news['title'][:30] + '...' for news in news_list[:3]])}",
            'duration': duration,
            'pub_date': datetime.now().isoformat(),
            'author': 'AutoNews AI',
            'category': 'Technology',
            'keywords': [news['title'].split()[0] for news in news_list],
            'news_count': len(news_list)
        }
        
        logger.info(f"播客元数据生成成功: {metadata['title']}")
        return metadata
        
    except Exception as e:
        logger.error(f"生成播客元数据失败: {str(e)}")
        return {}

def generate_podcast_rss(metadata: dict, audio_url: str, output_path: str = None) -> str:
    """
    生成播客 RSS Feed（用于发布到播客平台）
    
    Args:
        metadata: 播客元数据
        audio_url: 音频文件的 URL
        output_path: RSS 输出路径
    
    Returns:
        RSS 文件路径
    """
    if output_path is None:
        output_path = os.path.join(os.path.dirname(AUDIO_OUTPUT), 'podcast_rss.xml')
    
    try:
        rss_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">
  <channel>
    <title>{metadata.get('title', '科技早报')}</title>
    <description>{metadata.get('description', '')}</description>
    <itunes:author>{metadata.get('author', 'AutoNews AI')}</itunes:author>
    <itunes:category text="{metadata.get('category', 'Technology')}"/>
    <pubDate>{metadata.get('pub_date', '')}</pubDate>
    <language>zh-CN</language>
    
    <item>
      <title>{metadata.get('title', '科技早报')}</title>
      <description>{metadata.get('description', '')}</description>
      <enclosure url="{audio_url}" type="audio/mpeg" length="{metadata.get('duration', 0)}"/>
      <pubDate>{metadata.get('pub_date', '')}</pubDate>
      <itunes:duration>{int(metadata.get('duration', 0))}</itunes:duration>
    </item>
  </channel>
</rss>"""
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(rss_content)
        
        logger.info(f"播客 RSS 生成成功: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"生成播客 RSS 失败: {str(e)}")
        raise

def generate_podcast_chapters(script: str, output_path: str = None) -> str:
    """
    生成播客章节标记（用于支持章节的播客应用）
    
    Args:
        script: 播客脚本
        output_path: 章节文件输出路径
    
    Returns:
        章节文件路径
    """
    if output_path is None:
        output_path = os.path.join(os.path.dirname(SCRIPT_OUTPUT), 'chapters.json')
    
    try:
        import json
        import re
        
        lines = script.split('\n')
        chapters = []
        current_time = 0
        
        for line in lines:
            if line.strip() and (line.startswith('1.') or line.startswith('2.') or line.startswith('3.') or line.startswith('4.') or line.startswith('5.')):
                chapters.append({
                    'title': line.strip(),
                    'startTime': current_time,
                    'endTime': current_time + 60
                })
                current_time += 60
        
        chapter_data = {
            'version': '1.2.0',
            'chapters': chapters
        }
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(chapter_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"播客章节生成成功: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"生成播客章节失败: {str(e)}")
        return ""
