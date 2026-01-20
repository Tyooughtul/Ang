import logging
import os
import time
import requests
import json
from typing import Optional
from .config import SILICONFLOW_API_KEY, ASSETS_DIR
from .llm_engine import generate_script_with_retry

logger = logging.getLogger(__name__)

class ImageEngine:
    """
    以及 SiliconFlow API 为核心的自动配图引擎
    """
    def __init__(self, api_key: str = None):
        self.api_key = api_key or SILICONFLOW_API_KEY
        self.base_url = "https://api.siliconflow.cn/v1/images/generations"
        # 默认使用 FLUX.1-schnell，因为它在 SiliconFlow 上通常免费且效果极好
        # 如果用户非要用 Qwen，可以在这里改，但 FLUX 画封面图是目前最强的
        self.model = "black-forest-labs/FLUX.1-schnell" 
        
        if not self.api_key:
            logger.warning("⚠️ 未配置 SILICONFLOW_API_KEY，无法生成配图")

    def generate_image_prompt(self, news_title: str, news_summary: str) -> str:
        """
        使用 LLM 将新闻转换为英文绘画提示词 (Prompt Engineering)
        """
        logger.info("🎨 正在构思封面图提示词...")
        
        system_prompt = "You are an expert AI Art Prompter for Midjourney and FLUX."
        prompt = f"""Task: Create a high-quality image generation prompt based on this tech news.

News Title: {news_title}
Summary: {news_summary}

Requirements:
1. Style: Cyberpunk / Futuristic / Tech minimalist.
2. Format: Returns ONLY the prompt string in English. No markdown, no explanations.
3. Elements: Include visual metaphors (e.g., glowing brain for AI, holographic screens).
4. Keywords to include: "8k resolution", "cinematic lighting", "unreal engine 5 render", "high detail".

Example Output:
futuristic laboratory with glowing blue holographic data streams, golden trophy floating in center, dark background with neon accents, cinematic lighting, 8k, photorealistic
"""
        # 调用 LLM 生成提示词
        image_prompt = generate_script_with_retry(prompt, system_prompt=system_prompt)
        
        # 清理一下可能多余的符号
        image_prompt = image_prompt.replace('"', '').replace("'", "").strip()
        logger.info(f"✨ 提示词已生成: {image_prompt[:50]}...")
        return image_prompt

    def generate_image(self, prompt: str, output_path: str = None) -> Optional[str]:
        """
        调用 API 生成图片并保存
        """
        if not self.api_key:
            logger.error("❌ 无法生成图片: 缺少 API Key")
            return None

        if output_path is None:
            timestamp = int(time.time())
            output_path = os.path.join(ASSETS_DIR, 'temp', f'cover_{timestamp}.jpg')

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # SiliconFlow (OpenAI Format) Payload
        payload = {
            "model": self.model,
            "prompt": prompt,
            "image_size": "1024x1024", # 播客封面通常是正方形
            "batch_size": 1,
            "seed": 42, # 固定种子方便复现，或者去掉以随机
            "num_inference_steps": 20, # FLUX schnell 只需要很少步数
            "guidance_scale": 7.5
        }

        try:
            logger.info(f"🚀 调用绘图 API ({self.model})...")
            response = requests.post(self.base_url, json=payload, headers=headers, timeout=60)
            
            if response.status_code != 200:
                logger.error(f"❌ API 请求失败: {response.status_code} - {response.text}")
                return None
                
            result = response.json()
            
            # 解析 OpenAI 格式的响应
            # 通常是 {'data': [{'url': '...'}]}
            if 'data' in result and len(result['data']) > 0:
                image_url = result['data'][0].get('url')
                if not image_url:
                     logger.error("❌ API 返回了空 URL")
                     logger.debug(str(result))
                     return None
                     
                logger.info(f"📥 正在下载图片: {image_url[:30]}...")
                
                # 下载图片
                img_data = requests.get(image_url).content
                
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                with open(output_path, 'wb') as f:
                    f.write(img_data)
                    
                logger.info(f"🖼️ 图片已保存至: {output_path}")
                return output_path
                
            else:
                logger.error(f"❌ 无法解析响应结果: {result}")
                return None

        except Exception as e:
            logger.error(f"❌ 绘图过程发生异常: {e}")
            return None
