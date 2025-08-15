# 风机重力基础验算服务

基于FastAPI框架的风机重力基础验算后端服务，提供完整的风机基础设计验证、承载力分析、沉降计算、抗冲切验算、抗倾覆验算、刚度验算等综合验算功能。

## 项目特性

- 🏗️ **专业验算**: 完整的风机重力基础验算体系，符合《陆上风电场工程风电机组基础设计规范》
- 🔧 **多工况分析**: 支持正常、极端、疲劳、地震等6种工况的荷载组合计算
- 📊 **精确计算**: 基础自重、塔筒荷载、地基承载力、沉降、抗倾覆等全方位计算
- 🚀 **FastAPI框架**: 高性能、自动API文档生成、类型安全
- 📝 **详细文档**: 完整的接口文档和计算说明
- 🔍 **结构化日志**: 完整的请求日志和错误追踪
- ⚡ **异步处理**: 支持高并发请求处理
- 🛡️ **异常处理**: 全局异常处理和错误响应
- 🐳 **Docker支持**: 完整的容器化部署方案

## 主要功能模块

### 基础验算模块
- **基础体型验算**: 验证基础几何尺寸合理性和边坡符合性
- **基础自重计算**: 计算混凝土重量、回填土重量和浮力影响
- **塔筒底部荷载计算**: 振动周期分析和地震力计算
- **荷载分析**: 六种工况的详细荷载组合计算和压力分析

### 全面验算模块
- **脱空面积验算**: 验证正常和极端工况下的基础脱空情况
- **地基承载力验算**: 验证地基承载能力满足各工况要求
- **地基变形验算**: 计算基础沉降和倾斜度（支持分层土计算）
- **抗倾覆验算**: 验证基础抗倾覆安全性
- **抗滑移验算**: 验证基础抗滑移稳定性
- **刚度验算**: 验证地基旋转和水平动态刚度
- **抗剪强度验算**: 验证基础抗剪承载能力
- **抗冲切验算**: 验证基础抗冲切承载能力

## 项目结构

```
wind-turbine-calc/
├── app/                          # 应用主目录
│   ├── controllers/              # 控制器层 (处理HTTP请求)
│   │   ├── calculation_controller.py    # 计算控制器
│   │   └── management_controller.py     # 管理控制器
│   ├── services/                 # 业务逻辑层
│   │   ├── calculation_service.py       # 计算服务主入口
│   │   ├── foundation_calculator.py     # 基础计算器
│   │   ├── load_calculator.py           # 荷载计算器
│   │   ├── self_weight_calculator.py    # 自重计算器
│   │   ├── bearing_capacity_analyzer.py # 承载力分析器
│   │   ├── settlement_analyzer.py       # 沉降分析器
│   │   ├── detachment_analyzer.py       # 脱空分析器
│   │   └── foundation_pressure_coefficients.py # 压力系数
│   ├── schemas/                  # API请求/响应模式
│   │   └── calculation_schemas.py       # 计算模式定义
│   ├── core/                     # 核心配置
│   │   └── config.py                    # 配置管理
│   ├── middleware/               # 中间件
│   │   └── logging_middleware.py        # 日志中间件
│   ├── utils/                    # 工具函数
│   │   ├── logger.py                    # 日志工具
│   │   └── soil_layer_selector.py       # 土层选择工具
│   ├── exceptions/               # 异常处理
│   │   └── handlers.py                  # 异常处理器
│   ├── main.py                   # 应用入口
│   ├── requirements.txt          # 依赖文件
│   ├── Dockerfile               # Docker配置
│   └── docker-compose.yml       # Docker编排配置
├── demo/                         # 演示示例
│   ├── demo_basic_combination.py        # 基本组合演示
│   ├── demo_bearing_capacity.py         # 承载力演示
│   ├── demo_comprehensive_with_tower.py # 综合验算演示
│   ├── demo_foundation_calculator.py    # 基础计算演示
│   ├── demo_geometry_validation.py      # 几何验证演示
│   ├── demo_self_weight.py             # 自重计算演示
│   ├── demo_settlement_new.py          # 沉降计算演示
│   └── demo_settlement_service.py      # 沉降服务演示
├── tests/                        # 测试文件
│   ├── comprehensive_request_example.json # 完整请求示例
│   ├── test_comprehensive.py           # 综合测试
│   ├── test_bearing_capacity.py        # 承载力测试
│   ├── test_settlement_analyzer.py     # 沉降分析测试
│   └── ...                             # 其他专项测试
├── docs/                         # 文档目录
│   └── 风机重力基础验算服务说明 V1.0.4.md # 详细使用说明
└── README.md                     # 项目文档
```

## 快速开始

### 1. 环境要求

- Python 3.8+
- FastAPI 0.104.1+
- Uvicorn 0.34.2

### 2. 安装依赖

```bash
# 克隆项目
git clone <repository-url>
cd wind-turbine-calc

# 安装依赖
pip install -r app/requirements.txt
```

### 3. 启动服务

```bash
# 开发模式启动
cd app
python main.py

# 或使用 uvicorn 直接启动
uvicorn app.main:app --host 0.0.0.0 --port 8088 --reload
```

### 4. 访问API文档

- Swagger UI: http://localhost:8088/docs
- ReDoc: http://localhost:8088/redoc

## 主要API接口

### 综合验算服务

**POST** `/api/calculation/comprehensive`

风机重力基础综合验算服务，提供完整的基础设计验证功能。

#### 请求参数

```json
{
  "designParameters": {
    "safetyLevel": "一级",           // 安全等级
    "importanceFactor": 1.1,        // 重要性系数
    "connectionType": "锚栓笼",      // 连接方式
    "turbineCapacity": 6.25,        // 风机容量 (MW)
    "hubHeight": 140,               // 轮毂高度 (m)
    "coverSoilDensity": 18.0,       // 覆土容重 (kN/m³)
    "waterDepth": 20                // 地下水埋深 (m)
  },
  "geometry": {
    "baseRadius": 11.5,             // 基础底面半径 (m)
    "columnRadius": 3.5,            // 台柱半径 (m)
    "edgeHeight": 0.8,              // 基础边缘高度 (m)
    "frustumHeight": 2.4,           // 基础底板棱台高度 (m)
    "columnHeight": 1.775,          // 台柱高度 (m)
    "groundHeight": 0.475,          // 地面裸露高度 (m)
    "buriedDepth": 4.5              // 基础埋深 (m)
  },
  "material": {
    "concreteGrade": "C40",         // 混凝土强度等级
    "fc": 19.1,                     // 轴心抗压强度设计值 (N/mm²)
    "ft": 1.71,                     // 轴心抗拉强度设计值 (N/mm²)
    "density": 25                   // 混凝土密度 (kN/m³)
  },
  "soilLayers": [...],              // 土层参数数组
  "windTurbine": {...},             // 风机参数
  "towerDrums": [...],              // 塔筒段参数数组
  "turbineLoads": {...},            // 风机荷载参数（四种工况）
  "allowedDetachmentArea": {...},   // 允许脱空面积配置
  "stiffnessRequirements": {...}    // 刚度要求配置
}
```

详细的请求参数和响应格式请参考：`docs/风机重力基础验算服务说明 V1.0.4.md`

### 管理服务

- `GET /api/management/health` - 健康检查
- `GET /api/management/config` - 获取系统配置

## 使用示例

### Python客户端调用

```python
import requests
import json

# 读取示例请求
with open('tests/comprehensive_request_example.json', 'r', encoding='utf-8') as f:
    request_data = json.load(f)

# 发送请求
url = "http://localhost:8088/api/calculation/comprehensive"
response = requests.post(url, json=request_data)

# 处理响应
if response.status_code == 200:
    result = response.json()
    print("验算成功！")
    print(f"设计是否可接受: {result['data']['summary']['is_design_acceptable']}")
else:
    print(f"请求失败: {response.status_code}")
    print(response.text)
```

### 核心计算流程

1. **基础体型验算** - 验证基础几何尺寸合理性
2. **基础自重计算** - 计算基础自重、回填土重量和浮力
3. **塔筒底部荷载计算** - 基于塔筒信息和风机参数
4. **六种工况荷载处理** - 正常、极端、疲劳、地震工况
5. **荷载组合计算** - 标准组合、基本组合计算
6. **地基承载力验算** - 验证地基承载能力
7. **地基变形计算** - 计算基础沉降量和倾斜度
8. **抗倾覆验算** - 验证基础抗倾覆稳定性
9. **脱空面积验算** - 检查基础脱空面积
10. **抗冲切验算** - 验证基础抗冲切承载力
11. **刚度验算** - 验证基础动态刚度

## Docker部署

### 使用docker-compose（推荐）

```bash
cd app
docker-compose up -d
```

### 手动Docker部署

```bash
# 构建镜像
cd app
docker build -t wind-turbine-calc .

# 运行容器
docker run -d -p 8088:8088 --name wind-turbine-calc wind-turbine-calc
```

## 开发指南

### 本地开发环境设置

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装开发依赖
pip install -r app/requirements.txt

# 运行测试
python -m pytest tests/ -v
```

### 添加新的验算功能

1. **定义数据模式** (`app/schemas/calculation_schemas.py`)
2. **实现业务逻辑** (`app/services/`)
3. **更新控制器接口** (`app/controllers/calculation_controller.py`)
4. **编写测试用例** (`tests/`)

### 代码规范

- 使用类型注解
- 编写详细的文档字符串
- 遵循PEP 8编码规范
- 使用异步函数处理IO操作

## 版本说明

### V1.0.4（当前版本）
- ✅ 新增地基变形计算模块
- ✅ 新增沉降计算功能（支持分层土计算）
- ✅ 优化接口返回结果，添加中文标识字段
- ✅ 增强错误处理和设计建议

### V1.0.3
- ✅ 优化接口返回结果
- ✅ 添加各计算模块中文标识字段

### V1.0.2
- ✅ 修正偏心受压区域面积计算逻辑
- ✅ 调整Pj计算方式
- ✅ 增加按基础埋深选择土层参数

### V1.0.1
- ✅ 增加基础参数、设计参数模块
- ✅ 增加允许脱空面积和刚度要求配置

### V1.0.0
- ✅ 基础验算核心功能实现

## 技术栈

- **后端框架**: FastAPI 0.104.1
- **ASGI服务器**: Uvicorn 0.34.2
- **数据验证**: Pydantic 2.5.0
- **配置管理**: Pydantic Settings 2.1.0
- **HTTP客户端**: HTTPX 0.28.1
- **容器化**: Docker + Docker Compose

## 注意事项

1. **计算精度**: 所有计算基于《陆上风电场工程风电机组基础设计规范》
2. **参数单位**: 严格按照文档要求的单位输入参数
3. **工况完整性**: 确保提供完整的六种工况荷载数据
4. **设计安全**: 当偏心距过大时系统会给出设计警告

## 许可证

本项目采用私有许可证，仅供授权用户使用。

## 联系方式

如有技术问题或功能建议，请联系开发团队。

---

**版本**: V1.0.4  
**最后更新**: 2025/08/08