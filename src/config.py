import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, 'assets')
TEMP_DIR = os.path.join(ASSETS_DIR, 'temp')
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')

RSS_SOURCES = [
    "https://techcrunch.com/feed/",
    "https://www.theverge.com/rss/index.xml",
    "https://www.wired.com/feed/rss",
]

NEWS_LIMIT = 3

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = "deepseek-chat"

DOUBAO_API_KEY = os.getenv("DOUBAO_API_KEY")
DOUBAO_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3/responses"
DOUBAO_MODEL = "glm-4-7-251222"

GLM_API_KEY = os.getenv("DOUBAO_API_KEY")
GLM_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3/responses"
GLM_MODEL = "glm-4-7-251222"

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

SILICONFLOW_API_KEY = os.getenv("SILICONFLOW_API_KEY")
IMAGE_MODEL = "black-forest-labs/FLUX.1-schnell"

PODCAST_SYSTEM_PROMPT = """你是一个犀利、幽默的科技评论员，擅长用大白话讲新闻。
任务：将以下新闻摘要改写成一段 3-5 分钟的播客口播文案。
要求：
1. 开头要有爆点，吸引注意力
2. 中间要有逻辑，条理清晰，可以加入个人观点和评论
3. 结尾有简单的总结和互动提问
4. 语言口语化，适合播客形式
5. 每条新闻之间要有过渡语"""

ARTICLE_SYSTEM_PROMPT = """你是一个专业的科技媒体编辑，擅长撰写深度科技文章。
任务：将以下新闻摘要改写成一篇适合发布在小红书、知乎等平台的科技文章。
要求：
1. 标题要吸引人，适合社交媒体传播
2. 正文要有深度分析，不能只是简单复述新闻
3. 加入行业背景、影响分析、未来趋势
4. 语言要专业但不晦涩，适合大众阅读
5. 文章结构清晰，有引言、正文、结语
6. 适当使用表情符号和排版，适合移动端阅读"""

TTS_VOICE = "zh-CN-YunxiNeural"

TRANSLATE_ENABLED = os.getenv("TRANSLATE_ENABLED", "false").lower() == "true"

AUDIO_OUTPUT = os.path.join(TEMP_DIR, "podcast.mp3")
SCRIPT_OUTPUT = os.path.join(TEMP_DIR, "podcast_script.txt")
ARTICLE_OUTPUT = os.path.join(OUTPUT_DIR, "article.md")

PODCAST_ENABLED = os.getenv("PODCAST_ENABLED", "true").lower() == "true"
ARTICLE_ENABLED = os.getenv("ARTICLE_ENABLED", "true").lower() == "true"

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
