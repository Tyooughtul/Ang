import asyncio
import logging
import os
import edge_tts
from pydub import AudioSegment
from typing import List, Dict
from .config import TTS_VOICE, AUDIO_OUTPUT, ASSETS_DIR

logger = logging.getLogger(__name__)

# 音色配置 (Host=Yunxi男声, Guest=Xiaoxiao女声/Yunjian体育男声)
VOICE_MAP = {
    "Host": "zh-CN-YunxiNeural",
    "Guest": "zh-CN-XiaoxiaoNeural"
}

async def generate_audio(dialogue_script: List[Dict], output_path: str = None) -> str:
    """
    生成双人对谈音频 (支持 BGM 混音)
    
    Args:
        dialogue_script: 剧本列表 [{'role': 'Host', 'text': '...'}]
        output_path: 输出路径
    """
    if output_path is None:
        output_path = AUDIO_OUTPUT
        
    temp_dir = os.path.dirname(output_path)
    os.makedirs(temp_dir, exist_ok=True)
    temp_files = []
    
    combined_audio = AudioSegment.empty()
    # 每句话之间的静默停顿 (ms)
    pause_duration = 400 
    
    try:
        logger.info(f"🎙️ 开始生成双人对话音频，共 {len(dialogue_script)} 句台词...")
        
        # 1. 逐句生成干声并拼接
        for i, line in enumerate(dialogue_script):
            role = line.get("role", "Host")
            text = line.get("text", "")
            
            # 跳过空行和纯动作描述 (e.g. "[笑]")
            if not text.strip() or text.startswith("(") or text.startswith("["):
                continue
                
            voice = VOICE_MAP.get(role, VOICE_MAP["Host"])
            temp_file = os.path.join(temp_dir, f"temp_segment_{i}.mp3")
            
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(temp_file)
            temp_files.append(temp_file)
            
            segment = AudioSegment.from_mp3(temp_file)
            
            # 如果是 Guest 说话，稍微提高一点音量让它更清脆
            if role == "Guest":
                segment = segment + 2 
            
            combined_audio += segment
            combined_audio += AudioSegment.silent(duration=pause_duration)
            
        logger.info(f"✅ 干声拼接完成，总时长: {len(combined_audio)/1000:.2f}秒")

        # 2. BGM 混音 (如果 assets/bgm.mp3 存在)
        bgm_path = os.path.join(ASSETS_DIR, "bgm.mp3")
        if os.path.exists(bgm_path):
            logger.info("🎵 检测到 BGM 文件，正在进行混音...")
            bgm = AudioSegment.from_mp3(bgm_path)
            
            # 循环 BGM 直到覆盖全长
            while len(bgm) < len(combined_audio) + 5000:
                bgm += bgm
            
            # 裁剪 BGM
            bgm = bgm[:len(combined_audio) + 2000]
            
            # 降低 BGM 音量作为背景 (Duck)
            bgm = bgm - 15  # 降低 15dB
            
            # 淡入淡出
            bgm = bgm.fade_in(2000).fade_out(3000)
            
            # 叠加 (overlay)
            final_audio = bgm.overlay(combined_audio, position=1000) # 延迟1秒进人声
        else:
            logger.info("⚠️ 未检测到 BGM 文件 (assets/bgm.mp3)，输出纯干声")
            final_audio = combined_audio

        # 3. 导出
        final_audio.export(output_path, format="mp3")
        logger.info(f"🎉 最终音频导出成功: {output_path}")
        
        return output_path

    except Exception as e:
        logger.error(f"❌ 音频生成失败: {e}")
        raise
        
    finally:
        # 清理临时切片文件
        for f in temp_files:
            if os.path.exists(f):
                try:
                    os.remove(f)
                except:
                    pass

# 保留旧接口但不建议使用
async def generate_single_audio(text: str, voice: str = None, output_path: str = None) -> str:
    """[DEPRECATED] 旧单人 TTS 接口"""
    logger.warning("调用了旧的单人 TTS 接口 generate_single_audio")
    return await generate_audio([{'role':'Host', 'text': text}], output_path)

def get_audio_duration(audio_path: str) -> float:
    """
    获取音频时长（需要安装 pydub 或使用其他库）
    
    Args:
        audio_path: 音频文件路径
    
    Returns:
        音频时长（秒）
    """
    try:
        from pydub import AudioSegment
        audio = AudioSegment.from_mp3(audio_path)
        duration = len(audio) / 1000.0
        logger.info(f"音频时长: {duration:.2f} 秒")
        return duration
    except ImportError:
        logger.warning("pydub 未安装，无法获取音频时长")
        return 0.0
    except Exception as e:
        logger.error(f"获取音频时长失败: {str(e)}")
        return 0.0

async def generate_audio_sync(text: str, voice: str = None, output_path: str = None) -> str:
    """
    同步包装器，用于在非异步环境中调用
    
    Args:
        text: 待转换的文本
        voice: 语音模型
        output_path: 输出文件路径
    
    Returns:
        音频文件路径
    """
    return await generate_audio(text, voice, output_path)
