# 风机基础验算服务架构优化方案

## 🎯 优化目标

1. **提升性能**: 减少重复计算，提高响应速度
2. **增强可维护性**: 改善代码结构，降低耦合度
3. **提高可扩展性**: 支持新的计算模块和功能扩展
4. **增强稳定性**: 完善错误处理和异常管理

## 🏗️ 架构优化方案

### 1. 依赖注入容器改进

#### 当前问题
```python
# app/controllers/calculation_controller.py - 问题代码
def get_calculation_service() -> CalculationService:
    return CalculationService()  # 每次创建新实例
```

#### 优化方案
```python
# app/core/container.py - 新增依赖注入容器
from functools import lru_cache
from typing import Protocol

class ServiceContainer:
    """服务容器，管理服务生命周期"""
    
    def __init__(self):
        self._services = {}
    
    @lru_cache()
    def get_calculation_service(self) -> CalculationService:
        """单例模式获取计算服务"""
        if 'calculation_service' not in self._services:
            self._services['calculation_service'] = CalculationService()
        return self._services['calculation_service']

# 使用单例容器
container = ServiceContainer()
```

### 2. 服务分层优化

#### 当前架构
```
Controller → Service → Multiple Analyzers
```

#### 优化后架构
```
Controller → Facade → Domain Services → Infrastructure
```

#### 实现方案
```python
# app/services/calculation_facade.py - 新增门面模式
class CalculationFacade:
    """计算服务门面，简化客户端调用"""
    
    def __init__(self, container: ServiceContainer):
        self.container = container
        
    async def comprehensive_calculation(
        self, 
        request: ComprehensiveCalculationRequest
    ) -> ComprehensiveCalculationResponse:
        """综合验算门面方法"""
        # 协调多个服务完成复杂计算
        pass
```

### 3. 缓存策略引入

#### Redis缓存层
```python
# app/core/cache.py - 新增缓存层
from redis import Redis
from typing import Optional
import json
import hashlib

class CalculationCache:
    """计算结果缓存"""
    
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.ttl = 3600  # 1小时过期
    
    def get_cache_key(self, request: dict) -> str:
        """生成缓存键"""
        content = json.dumps(request, sort_keys=True)
        return f"calc:{hashlib.md5(content.encode()).hexdigest()}"
    
    async def get(self, request: dict) -> Optional[dict]:
        """获取缓存结果"""
        key = self.get_cache_key(request)
        cached = await self.redis.get(key)
        return json.loads(cached) if cached else None
    
    async def set(self, request: dict, result: dict):
        """设置缓存结果"""
        key = self.get_cache_key(request)
        await self.redis.setex(key, self.ttl, json.dumps(result))
```

### 4. 异常处理优化

#### 自定义业务异常
```python
# app/exceptions/business_exceptions.py - 新增业务异常
class CalculationError(Exception):
    """计算异常基类"""
    
    def __init__(self, message: str, error_code: str, details: dict = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(message)

class GeometryValidationError(CalculationError):
    """几何验证异常"""
    pass

class LoadCalculationError(CalculationError):
    """荷载计算异常"""
    pass

class BearingCapacityError(CalculationError):
    """承载力验算异常"""
    pass
```

#### 异常处理器优化
```python
# app/exceptions/handlers.py - 优化异常处理
@app.exception_handler(CalculationError)
async def calculation_exception_handler(request: Request, exc: CalculationError):
    """业务计算异常处理器"""
    logger.warning(f"计算异常: {exc.error_code} - {exc.message}")
    
    return JSONResponse(
        status_code=400,
        content={
            "success": False,
            "message": exc.message,
            "error_code": exc.error_code,
            "details": exc.details,
            "path": str(request.url.path),
            "timestamp": datetime.utcnow().isoformat()
        }
    )
```

### 5. 性能监控与度量

#### 性能指标收集
```python
# app/middleware/metrics_middleware.py - 新增性能监控
import time
from prometheus_client import Counter, Histogram, generate_latest

# 定义度量指标
REQUEST_COUNT = Counter('http_requests_total', 'HTTP请求总数', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP请求耗时')
CALCULATION_DURATION = Histogram('calculation_duration_seconds', '计算耗时', ['calc_type'])

class MetricsMiddleware(BaseHTTPMiddleware):
    """性能指标中间件"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path
        ).inc()
        
        response = await call_next(request)
        
        REQUEST_DURATION.observe(time.time() - start_time)
        
        return response
```

### 6. 配置管理优化

#### 环境特定配置
```python
# app/core/config.py - 优化配置管理
class CalculationSettings(BaseSettings):
    """计算专用配置"""
    
    # 计算性能配置
    MAX_CONCURRENT_CALCULATIONS: int = 5
    CALCULATION_TIMEOUT_SECONDS: int = 60
    ENABLE_RESULT_CACHE: bool = True
    CACHE_TTL_SECONDS: int = 3600
    
    # 精度配置
    DECIMAL_PRECISION: int = 6
    CONVERGENCE_TOLERANCE: float = 1e-6
    MAX_ITERATIONS: int = 1000
    
    # 验证规则配置
    MIN_FOUNDATION_RADIUS: float = 1.0
    MAX_FOUNDATION_RADIUS: float = 50.0
    MIN_CONCRETE_STRENGTH: float = 10.0
    MAX_CONCRETE_STRENGTH: float = 100.0
```

### 7. 数据访问层优化

#### Repository模式
```python
# app/repositories/calculation_repository.py - 新增数据访问层
from abc import ABC, abstractmethod

class CalculationRepositoryInterface(ABC):
    """计算数据访问接口"""
    
    @abstractmethod
    async def save_calculation_result(self, result: CalculationResult) -> str:
        """保存计算结果"""
        pass
    
    @abstractmethod
    async def get_calculation_result(self, calc_id: str) -> Optional[CalculationResult]:
        """获取计算结果"""
        pass

class SQLCalculationRepository(CalculationRepositoryInterface):
    """SQL数据库实现"""
    
    def __init__(self, db_session):
        self.db = db_session
    
    async def save_calculation_result(self, result: CalculationResult) -> str:
        # 实现数据库保存逻辑
        pass
```

### 8. 测试策略改进

#### 分层测试
```python
# tests/unit/test_calculation_service.py - 单元测试
class TestCalculationService:
    """计算服务单元测试"""
    
    def setup_method(self):
        self.service = CalculationService()
    
    @pytest.mark.asyncio
    async def test_foundation_calculation(self):
        """测试基础计算功能"""
        request = FoundationCalculationRequest(...)
        result = await self.service.calculate_foundation(request)
        assert result.is_valid
    
    @pytest.mark.parametrize("geometry,expected", [
        ({"radius": 10}, True),
        ({"radius": 0}, False),
    ])
    def test_geometry_validation(self, geometry, expected):
        """参数化测试几何验证"""
        result = self.service.validate_geometry(geometry)
        assert result == expected

# tests/integration/test_api.py - 集成测试
class TestCalculationAPI:
    """计算API集成测试"""
    
    @pytest.mark.asyncio
    async def test_comprehensive_calculation_flow(self):
        """测试完整计算流程"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post("/api/calculation/comprehensive", json=test_data)
            assert response.status_code == 200
            assert response.json()["success"] is True
```

## 📊 实施优先级

### 🔥 高优先级（立即实施）
1. **依赖注入容器** - 解决服务实例重复创建问题
2. **缓存层引入** - 提升计算性能
3. **业务异常优化** - 改善错误处理

### 🟡 中优先级（短期实施）
1. **性能监控** - 建立性能基线
2. **配置管理优化** - 支持更细粒度配置
3. **分层测试完善** - 提高代码质量

### 🟢 低优先级（长期考虑）
1. **数据访问层** - 支持数据持久化
2. **微服务拆分** - 大规模部署时考虑
3. **API版本管理** - 向后兼容性

## 🎯 预期收益

### 性能提升
- **响应时间减少**: 50%+ (通过缓存)
- **内存使用优化**: 30%+ (通过单例服务)
- **并发处理能力**: 3x+ (通过异步优化)

### 可维护性提升
- **代码耦合度降低**: 通过依赖注入
- **测试覆盖率提升**: 分层测试策略
- **错误诊断时间减少**: 结构化异常处理

### 可扩展性提升
- **新功能开发速度**: 2x+ (通过清晰架构)
- **部署灵活性**: 支持多环境
- **监控可观测性**: 全面性能指标

## 🛠️ 实施建议

### 阶段1: 基础设施优化（1-2周）
1. 创建依赖注入容器
2. 引入Redis缓存
3. 优化异常处理

### 阶段2: 性能优化（2-3周）
1. 添加性能监控
2. 实施缓存策略
3. 优化计算算法

### 阶段3: 架构完善（3-4周）
1. 完善测试策略
2. 优化配置管理
3. 添加数据持久化

这个优化方案将显著提升项目的性能、可维护性和可扩展性，为后续功能开发奠定坚实基础。
