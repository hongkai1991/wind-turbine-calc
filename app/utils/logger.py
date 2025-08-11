import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from typing import Optional
from app.core.config import get_settings

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    获取配置好的日志记录器
    
    Args:
        name: 日志记录器名称，默认使用调用模块名
        
    Returns:
        logging.Logger: 配置好的日志记录器
    """
    settings = get_settings()
    
    # 创建日志记录器
    logger = logging.getLogger(name or __name__)
    
    # 避免重复添加处理器
    if logger.handlers:
        return logger
    
    # 设置日志级别
    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    
    # 创建格式化器
    formatter = logging.Formatter(
        settings.LOG_FORMAT,
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 如果启用文件日志，创建文件处理器
    if settings.LOG_FILE_ENABLED:
        # 确保日志目录存在
        log_dir = settings.LOG_DIR
        if not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
            
        # 完整的日志文件路径
        log_file_path = os.path.join(log_dir, settings.LOG_FILENAME)
        
        # 创建轮转文件处理器
        file_handler = RotatingFileHandler(
            filename=log_file_path,
            maxBytes=settings.LOG_FILE_MAX_SIZE,
            backupCount=settings.LOG_FILE_BACKUP_COUNT,
            encoding='utf-8'
        )
        file_handler.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # 防止日志向上传播（避免重复输出）
    logger.propagate = False
    
    return logger 