import os
from typing import List
from functools import lru_cache
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """应用配置设置"""
    
    # 项目信息
    PROJECT_NAME: str = "Wind Turbine Calculation Service"
    PROJECT_DESCRIPTION: str = "风机基础验算服务"
    PROJECT_VERSION: str = "1.0.4"
    
    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8088
    DEBUG: bool = False
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_DIR: str = "app/logs"  # 日志文件目录
    LOG_FILENAME: str = "wind_turbine.log"  # 日志文件名
    LOG_FILE_ENABLED: bool = True  # 是否启用文件日志
    LOG_FILE_MAX_SIZE: int = 10 * 1024 * 1024  # 单个日志文件最大大小（字节），默认10MB
    LOG_FILE_BACKUP_COUNT: int = 5  # 备份日志文件数量
    
    # 安全配置
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS配置
    ALLOWED_ORIGINS: List[str] = ["*"]
    
    # 数据库配置
    DATABASE_URL: str = "sqlite:///./wind_turbine.db"
    
    # Redis配置（缓存）
    REDIS_URL: str = "redis://localhost:6379/0"
    CACHE_ENABLED: bool = True
    
    # 计算配置
    MAX_CALCULATION_THREADS: int = 4
    CALCULATION_TIMEOUT: int = 30
    
    # 文件上传配置
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    UPLOAD_DIR: str = "uploads"
    
    # 环境配置
    ENVIRONMENT: str = "development"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

class DevelopmentSettings(Settings):
    """开发环境配置"""
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"
    ENVIRONMENT: str = "development"

class ProductionSettings(Settings):
    """生产环境配置"""
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    ENVIRONMENT: str = "production"
    ALLOWED_ORIGINS: List[str] = ["https://your-frontend-domain.com"]

class TestingSettings(Settings):
    """测试环境配置"""
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"
    ENVIRONMENT: str = "testing"
    DATABASE_URL: str = "sqlite:///./test_wind_turbine.db"

@lru_cache()
def get_settings() -> Settings:
    """获取应用配置实例（单例模式）"""
    environment = os.getenv("ENVIRONMENT", "development").lower()
    
    if environment == "production":
        return ProductionSettings()
    elif environment == "testing":
        return TestingSettings()
    else:
        return DevelopmentSettings() 