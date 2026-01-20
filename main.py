import argparse
import asyncio
import logging
import os
import shutil
from datetime import datetime
from dotenv import load_dotenv

from src.web_searcher import WebSearcher
from src.article_engine import generate_article
from src.podcast_engine import generate_podcast
from src.image_engine import ImageEngine

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("output/pipeline.log", encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

async def run_pipeline(topic: str):
    """
    运行全自动内容生成流水线
    """
    start_time = datetime.now()
    timestamp = start_time.strftime('%Y%m%d_%H%M%S')
    
    # 创建本次运行的专属输出目录
    output_dir = os.path.join("output", f"{timestamp}_{topic.replace(' ', '_')}")
    os.makedirs(output_dir, exist_ok=True)
    
    print("\n" + "="*60)
    print(f"🚀 AI Auto Content Generator 启动")
    print(f"📌 主题: {topic}")
    print(f"📂 输出目录: {output_dir}")
    print("="*60)

    try:
        # ---------------------------------------------------------
        # Step 1: 智能搜索 (Tavily)
        # ---------------------------------------------------------
        print("\n[1/4] 🔍 正在搜集信息 (Tavily Search)...")
        searcher = WebSearcher()
        if not searcher.tavily_client:
            logger.error("❌ Tavily API Key 未配置，无法搜索。流程终止。")
            return

        search_results = searcher.search_topic(topic, max_results=5)
        
        if not search_results:
            logger.warning("❌ 未找到相关信息，请尝试更换关键词。")
            return
            
        print(f"   ✅ 找到 {len(search_results)} 条相关资讯")
        for i, r in enumerate(search_results[:3], 1):
            print(f"      - {r['title']} ({r.get('source', 'Unknown')})")

        # ---------------------------------------------------------
        # Step 2: 撰写深度长文 (Article Engine)
        # ---------------------------------------------------------
        print("\n[2/4] 📝 正在撰写深度文章 (Chain of Thought)...")
        article_path = os.path.join(output_dir, "article.md")
        try:
            generate_article(search_results, output_path=article_path)
            print(f"   ✅ 文章已生成: {article_path}")
        except Exception as e:
            logger.error(f"   ❌ 文章生成失败: {e}")

        # ---------------------------------------------------------
        # Step 3: 制作双人播客 (Podcast Engine)
        # ---------------------------------------------------------
        print("\n[3/4] 🎙️ 正在制作播客 (双人对谈 + BGM)...")
        # 准备合并的新闻文本供 LLM 写剧本
        news_summary_text = "\n".join([f"{r['title']}: {r['summary'][:300]}" for r in search_results])
        
        audio_path = os.path.join(output_dir, "podcast.mp3")
        script_path = os.path.join(output_dir, "script.json")
        
        try:
            await generate_podcast(news_summary_text, output_path=audio_path, script_path=script_path)
            print(f"   ✅ 播客音频已生成: {audio_path}")
        except Exception as e:
            logger.error(f"   ❌ 播客生成失败: {e}")

        # ---------------------------------------------------------
        # Step 4: 绘制封面图 (Image Engine)
        # ---------------------------------------------------------
        print("\n[4/4] 🎨 正在设计封面图 (FLUX/Qwen)...")
        try:
            img_engine = ImageEngine()
            if img_engine.api_key:
                # 选取第一条新闻的标题作为 prompt 基础，或者综合 summary
                main_title = search_results[0]['title']
                prompt = img_engine.generate_image_prompt(main_title, news_summary_text[:500])
                
                img_path = os.path.join(output_dir, "cover.jpg")
                generated_path = img_engine.generate_image(prompt, output_path=img_path)
                
                if generated_path:
                    print(f"   ✅ 封面图已生成: {generated_path}")
            else:
                print("   ⚠️ 跳过配图 (未配置 SILICONFLOW_API_KEY)")
        except Exception as e:
            logger.error(f"   ❌ 配图失败: {e}")

    except Exception as e:
        logger.error(f"❌ 流程发生未捕获异常: {e}")
        import traceback
        traceback.print_exc()

    finally:
        duration = datetime.now() - start_time
        print("\n" + "="*60)
        print(f"🎉 任务完成! 耗时: {duration}")
        print(f"👉 请查看目录: {output_dir}")
        print("="*60)


if __name__ == "__main__":
    load_dotenv()
    
    # 简单的命令行参数解析
    parser = argparse.ArgumentParser(description="自动新闻内容生成器")
    parser.add_argument("topic", nargs="?", default=None, help="你想生成内容的话题/关键词")
    args = parser.parse_args()

    # 如果没有提供参数，则交互式询问
    if args.topic is None:
        topic_input = input("请输入你想生成内容的话题 (默认为 'DeepSeek R1'): ").strip()
        final_topic = topic_input if topic_input else "DeepSeek R1"
    else:
        final_topic = args.topic

    asyncio.run(run_pipeline(final_topic))
