import logging
import os
import json
import hashlib
from datetime import datetime
from typing import Any, Dict, Optional
from .config import TEMP_DIR, LOG_LEVEL

def setup_logger(name: str = None, level: str = None) -> logging.Logger:
    """
    设置日志记录器
    
    Args:
        name: 日志记录器名称
        level: 日志级别
    
    Returns:
        配置好的日志记录器
    """
    if level is None:
        level = LOG_LEVEL
    
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    if not logger.handlers:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, level.upper()))
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)
        
        logger.addHandler(console_handler)
    
    return logger

def generate_cache_key(text: str) -> str:
    """
    生成缓存键
    
    Args:
        text: 文本内容
    
    Returns:
        MD5 哈希值
    """
    return hashlib.md5(text.encode('utf-8')).hexdigest()

def save_cache(key: str, data: Any, cache_dir: str = None) -> bool:
    """
    保存缓存数据
    
    Args:
        key: 缓存键
        data: 要缓存的数据
        cache_dir: 缓存目录
    
    Returns:
        是否保存成功
    """
    if cache_dir is None:
        cache_dir = os.path.join(TEMP_DIR, 'cache')
    
    try:
        os.makedirs(cache_dir, exist_ok=True)
        
        cache_file = os.path.join(cache_dir, f"{key}.json")
        
        cache_data = {
            'timestamp': datetime.now().isoformat(),
            'data': data
        }
        
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
        
        return True
        
    except Exception as e:
        logging.getLogger(__name__).error(f"保存缓存失败: {str(e)}")
        return False

def load_cache(key: str, cache_dir: str = None, max_age_hours: int = 24) -> Optional[Any]:
    """
    加载缓存数据
    
    Args:
        key: 缓存键
        cache_dir: 缓存目录
        max_age_hours: 缓存最大有效期（小时）
    
    Returns:
        缓存的数据，如果不存在或已过期则返回 None
    """
    if cache_dir is None:
        cache_dir = os.path.join(TEMP_DIR, 'cache')
    
    try:
        cache_file = os.path.join(cache_dir, f"{key}.json")
        
        if not os.path.exists(cache_file):
            return None
        
        with open(cache_file, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
        
        timestamp = datetime.fromisoformat(cache_data['timestamp'])
        age = (datetime.now() - timestamp).total_seconds() / 3600
        
        if age > max_age_hours:
            logging.getLogger(__name__).info(f"缓存已过期（{age:.2f} 小时）")
            return None
        
        logging.getLogger(__name__).info(f"从缓存加载数据（{age:.2f} 小时前）")
        return cache_data['data']
        
    except Exception as e:
        logging.getLogger(__name__).error(f"加载缓存失败: {str(e)}")
        return None

def clear_cache(cache_dir: str = None) -> bool:
    """
    清空缓存
    
    Args:
        cache_dir: 缓存目录
    
    Returns:
        是否清空成功
    """
    if cache_dir is None:
        cache_dir = os.path.join(TEMP_DIR, 'cache')
    
    try:
        if not os.path.exists(cache_dir):
            return True
        
        for filename in os.listdir(cache_dir):
            file_path = os.path.join(cache_dir, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)
        
        logging.getLogger(__name__).info(f"缓存已清空: {cache_dir}")
        return True
        
    except Exception as e:
        logging.getLogger(__name__).error(f"清空缓存失败: {str(e)}")
        return False

def ensure_directories():
    """
    确保所有必要的目录存在
    """
    directories = [
        TEMP_DIR,
        os.path.join(TEMP_DIR, 'cache'),
        os.path.dirname(TEMP_DIR),
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

def format_duration(seconds: float) -> str:
    """
    格式化时长
    
    Args:
        seconds: 秒数
    
    Returns:
        格式化后的时长字符串（如 "1分30秒"）
    """
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    
    if minutes > 0:
        return f"{minutes}分{secs}秒"
    else:
        return f"{secs}秒"

def clean_temp_files(older_than_hours: int = 24):
    """
    清理临时文件
    
    Args:
        older_than_hours: 删除多少小时前的文件
    """
    try:
        if not os.path.exists(TEMP_DIR):
            return
        
        now = datetime.now()
        
        for filename in os.listdir(TEMP_DIR):
            file_path = os.path.join(TEMP_DIR, filename)
            
            if os.path.isfile(file_path):
                file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                age = (now - file_time).total_seconds() / 3600
                
                if age > older_than_hours:
                    os.remove(file_path)
                    logging.getLogger(__name__).info(f"删除临时文件: {filename}")
        
    except Exception as e:
        logging.getLogger(__name__).error(f"清理临时文件失败: {str(e)}")

def validate_api_key(api_key: str) -> bool:
    """
    验证 API Key 格式
    
    Args:
        api_key: API Key
    
    Returns:
        是否有效
    """
    if not api_key or len(api_key) < 10:
        return False
    
    return True

def get_file_size(file_path: str) -> str:
    """
    获取文件大小的可读格式
    
    Args:
        file_path: 文件路径
    
    Returns:
        文件大小字符串（如 "1.5 MB"）
    """
    try:
        size_bytes = os.path.getsize(file_path)
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        
        return f"{size_bytes:.2f} TB"
        
    except Exception as e:
        logging.getLogger(__name__).error(f"获取文件大小失败: {str(e)}")
        return "未知"
