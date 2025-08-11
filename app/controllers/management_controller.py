from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional
import datetime
from app.utils.logger import get_logger

logger = get_logger(__name__)

# 创建管理路由器
router = APIRouter(
    prefix="/api/management",
    tags=["系统管理"],
    responses={404: {"description": "未找到"}}
)

# 响应模型
class HealthStatus(BaseModel):
    status: str
    timestamp: str
    service: str
    version: str
    uptime_seconds: Optional[float] = None

class ConfigItem(BaseModel):
    key: str
    value: str
    description: Optional[str] = None
    category: Optional[str] = None

class LogEntry(BaseModel):
    timestamp: str
    level: str
    message: str
    module: Optional[str] = None

class SystemMetrics(BaseModel):
    api_calls_total: int
    calculation_requests_today: int
    average_response_time_ms: float
    error_rate_percent: float
    uptime_hours: float
    active_connections: int
    memory_usage_mb: Optional[float] = None
    cpu_usage_percent: Optional[float] = None

# 启动时间（用于计算运行时间）
start_time = datetime.datetime.now()

@router.get("/", summary="获取管理服务信息")
async def management_root():
    """获取系统管理服务信息"""
    return {
        "message": "系统管理服务",
        "version": "1.0.0",
        "available_endpoints": {
            "health": "GET /api/management/health - 健康检查",
            "config": "GET /api/management/config - 获取系统配置",
            "logs": "GET /api/management/logs - 获取系统日志",
            "metrics": "GET /api/management/metrics - 获取系统指标"
        }
    }

@router.get("/health", response_model=HealthStatus, summary="系统健康检查")
async def health_check():
    """系统健康检查"""
    uptime = (datetime.datetime.now() - start_time).total_seconds()
    
    logger.info("执行健康检查")
    
    return HealthStatus(
        status="healthy",
        timestamp=datetime.datetime.now().isoformat(),
        service="wind-turbine-calc",
        version="1.0.0",
        uptime_seconds=uptime
    )

@router.get("/config", response_model=List[ConfigItem], summary="获取系统配置")
async def get_config():
    """获取系统配置"""
    logger.info("获取系统配置")
    
    config_items = [
        ConfigItem(
            key="max_calculation_threads", 
            value="4", 
            description="最大计算线程数",
            category="performance"
        ),
        ConfigItem(
            key="cache_enabled", 
            value="true", 
            description="是否启用缓存",
            category="cache"
        ),
        ConfigItem(
            key="log_level", 
            value="info", 
            description="日志级别",
            category="logging"
        ),
        ConfigItem(
            key="api_timeout", 
            value="30", 
            description="API超时时间(秒)",
            category="api"
        ),
        ConfigItem(
            key="max_file_size", 
            value="10MB", 
            description="最大文件上传大小",
            category="upload"
        ),
        ConfigItem(
            key="cors_origins", 
            value="*", 
            description="允许的跨域源",
            category="security"
        ),
        ConfigItem(
            key="database_url", 
            value="sqlite:///./wind_turbine.db", 
            description="数据库连接URL",
            category="database"
        )
    ]
    return config_items

@router.get("/logs", response_model=List[LogEntry], summary="获取系统日志")
async def get_logs(limit: int = 50, level: Optional[str] = None):
    """
    获取系统日志
    
    Args:
        limit: 返回日志条数限制，默认50条
        level: 日志级别过滤，可选：DEBUG, INFO, WARNING, ERROR
    """
    logger.info(f"获取系统日志，限制: {limit}条，级别: {level}")
    
    # 这里应该从实际的日志文件或日志系统中读取
    # 为了演示，返回模拟数据
    sample_logs = [
        LogEntry(
            timestamp=datetime.datetime.now().isoformat(),
            level="INFO",
            message="风机基础验算服务启动",
            module="main"
        ),
        LogEntry(
            timestamp=(datetime.datetime.now() - datetime.timedelta(minutes=2)).isoformat(),
            level="INFO", 
            message="接收到基础计算请求",
            module="calculation_service"
        ),
        LogEntry(
            timestamp=(datetime.datetime.now() - datetime.timedelta(minutes=5)).isoformat(),
            level="DEBUG",
            message="计算参数验证通过",
            module="calculation_controller"
        ),
        LogEntry(
            timestamp=(datetime.datetime.now() - datetime.timedelta(minutes=8)).isoformat(),
            level="WARNING",
            message="缓存命中率较低，建议检查缓存配置",
            module="cache_manager"
        ),
        LogEntry(
            timestamp=(datetime.datetime.now() - datetime.timedelta(minutes=10)).isoformat(),
            level="ERROR",
            message="数据库连接超时，自动重连成功",
            module="database"
        )
    ]
    
    # 应用级别过滤
    if level:
        sample_logs = [log for log in sample_logs if log.level == level.upper()]
    
    # 应用数量限制
    return sample_logs[:limit]

@router.get("/metrics", response_model=SystemMetrics, summary="获取系统指标")
async def get_metrics():
    """获取系统指标"""
    logger.info("获取系统指标")
    
    uptime_hours = (datetime.datetime.now() - start_time).total_seconds() / 3600
    
    # 在实际项目中，这些指标应该从监控系统或缓存中获取
    return SystemMetrics(
        api_calls_total=156,
        calculation_requests_today=23,
        average_response_time_ms=245,
        error_rate_percent=0.8,
        uptime_hours=round(uptime_hours, 2),
        active_connections=3,
        memory_usage_mb=128.5,
        cpu_usage_percent=15.2
    )

@router.post("/clear-cache", summary="清除系统缓存")
async def clear_cache():
    """清除系统缓存"""
    logger.info("执行清除缓存操作")
    
    # 这里应该实现实际的缓存清除逻辑
    
    return {
        "success": True,
        "message": "缓存已清除",
        "timestamp": datetime.datetime.now().isoformat()
    }

@router.post("/reload-config", summary="重新加载配置")
async def reload_config():
    """重新加载系统配置"""
    logger.info("执行重新加载配置操作")
    
    # 这里应该实现实际的配置重载逻辑
    
    return {
        "success": True,
        "message": "配置已重新加载",
        "timestamp": datetime.datetime.now().isoformat()
    } 