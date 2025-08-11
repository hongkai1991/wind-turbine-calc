import sys
import os
# 将项目根目录添加到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.controllers import calculation_controller, management_controller
from app.middleware.logging_middleware import LoggingMiddleware
from app.exceptions.handlers import setup_exception_handlers

def create_app() -> FastAPI:
    """创建并配置FastAPI应用实例"""
    settings = get_settings()
    
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description=settings.PROJECT_DESCRIPTION,
        version=settings.PROJECT_VERSION,
        debug=settings.DEBUG,
    )
    
    # 配置CORS中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 添加自定义中间件
    app.add_middleware(LoggingMiddleware)
    
    # 设置异常处理器
    setup_exception_handlers(app)
    
    # 注册路由控制器
    app.include_router(calculation_controller.router)
    # app.include_router(management_controller.router)
    
    @app.get("/")
    async def root():
        """根路径健康检查"""
        return {
            "message": f"欢迎使用{settings.PROJECT_NAME}",
            "version": settings.PROJECT_VERSION,
            "status": "running",
            "api_groups": {
                "calculation": "/api/calculation",
                "management": "/api/management"
            },
            "docs": "/docs",
            "redoc": "/redoc"
        }
    
    return app

# 创建应用实例
app = create_app()

if __name__ == "__main__":
    import uvicorn
    from app.core.config import get_settings
    
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    ) 