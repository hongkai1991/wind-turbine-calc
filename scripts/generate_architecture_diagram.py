#!/usr/bin/env python3
"""
生成风机基础计算系统架构图
详细展示系统的模块结构和数据流
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, Rectangle, Circle
import numpy as np

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']  
plt.rcParams['axes.unicode_minus'] = False

def create_architecture_diagram():
    """创建系统架构图"""
    
    # 创建图形和轴
    fig, ax = plt.subplots(1, 1, figsize=(24, 16))
    ax.set_xlim(0, 24)
    ax.set_ylim(0, 16)
    ax.axis('off')
    
    # 定义颜色
    colors = {
        'controller': '#E3F2FD',    # 浅蓝色 - 控制层
        'service': '#FFF3E0',       # 浅橙色 - 服务层
        'analyzer': '#E8F5E8',      # 浅绿色 - 分析器
        'schema': '#FCE4EC',        # 浅粉色 - 数据模型
        'util': '#F3E5F5',          # 浅紫色 - 工具层
        'database': '#FFEBEE',      # 浅红色 - 数据层
        'api': '#E0F2F1'            # 浅青色 - API层
    }
    
    def draw_layer_box(x, y, width, height, title, color, text_size=10):
        """绘制分层框"""
        box = FancyBboxPatch(
            (x, y), width, height,
            boxstyle="round,pad=0.02",
            facecolor=color,
            edgecolor='black',
            linewidth=2,
            alpha=0.7
        )
        ax.add_patch(box)
        ax.text(x + width/2, y + height - 0.3, title, ha='center', va='center', 
               fontsize=text_size, fontweight='bold')
        return (x, y, width, height)
    
    def draw_module_box(x, y, width, height, text, color, text_size=8):
        """绘制模块框"""
        box = FancyBboxPatch(
            (x, y), width, height,
            boxstyle="round,pad=0.05",
            facecolor=color,
            edgecolor='black',
            linewidth=1
        )
        ax.add_patch(box)
        ax.text(x + width/2, y + height/2, text, ha='center', va='center', 
               fontsize=text_size, fontweight='bold', wrap=True)
        return (x + width/2, y + height/2)
    
    def draw_arrow(start, end, style='->', color='black', width=1.5):
        """绘制箭头连接"""
        ax.annotate('', xy=end, xytext=start,
                   arrowprops=dict(arrowstyle=style, color=color, lw=width))
    
    # 标题
    ax.text(12, 15.5, '风机基础计算系统架构图', ha='center', va='center', 
            fontsize=22, fontweight='bold')
    
    # === 第1层：API接口层 ===
    api_layer = draw_layer_box(1, 13.5, 22, 1.5, 'API接口层 (FastAPI)', colors['api'], 12)
    
    # API模块
    main_api = draw_module_box(2, 14, 3, 0.8, 'app/main.py\n主应用入口', colors['api'])
    calc_api = draw_module_box(6, 14, 4, 0.8, 'calculation_controller.py\n综合计算接口', colors['controller'])
    mgmt_api = draw_module_box(11, 14, 4, 0.8, 'management_controller.py\n管理接口', colors['controller'])
    middleware = draw_module_box(16, 14, 3, 0.8, 'middleware/\n中间件', colors['api'])
    exception = draw_module_box(20, 14, 2.5, 0.8, 'exceptions/\n异常处理', colors['api'])
    
    # === 第2层：业务服务层 ===
    service_layer = draw_layer_box(1, 11, 22, 2, '业务服务层 (Services)', colors['service'], 12)
    
    # 主要服务
    calc_service = draw_module_box(2, 11.5, 4.5, 1.2, 'CalculationService\n计算业务逻辑\n• 统一计算流程\n• 结果组合', colors['service'])
    
    # === 第3层：计算分析器层 ===
    analyzer_layer = draw_layer_box(1, 8, 22, 2.5, '计算分析器层 (Analyzers)', colors['analyzer'], 12)
    
    # 分析器模块
    settlement = draw_module_box(1.5, 9, 3, 1, 'SettlementAnalyzer\n沉降分析器', colors['analyzer'])
    bearing = draw_module_box(5, 9, 3, 1, 'BearingCapacityAnalyzer\n承载力分析器', colors['analyzer'])
    detachment = draw_module_box(8.5, 9, 3, 1, 'DetachmentAnalyzer\n脱开面积分析器', colors['analyzer'])
    
    self_weight = draw_module_box(1.5, 8.5, 3, 1, 'SelfWeightCalculator\n自重计算器', colors['analyzer'])
    load_calc = draw_module_box(5, 8.5, 3, 1, 'LoadCalculator\n荷载计算器', colors['analyzer'])
    foundation_calc = draw_module_box(8.5, 8.5, 3, 1, 'FoundationCalculator\n基础计算器', colors['analyzer'])
    
    # 其他分析器
    other_analyzers = draw_module_box(12.5, 8.5, 4, 1.5, '其他分析器:\n• 抗倾覆验算\n• 抗滑移验算\n• 刚度验算\n• 抗剪强度验算\n• 抗冲切验算', colors['analyzer'])
    
    # 外部API
    tower_api = draw_module_box(17.5, 9, 4.5, 1, '塔筒荷载API\n(外部服务调用)', colors['analyzer'])
    
    # === 第4层：数据模型层 ===
    schema_layer = draw_layer_box(1, 5, 22, 2.5, '数据模型层 (Schemas/Pydantic)', colors['schema'], 12)
    
    # 数据模型
    base_schema = draw_module_box(1.5, 6.5, 2.5, 0.8, 'base.py\n基础模型', colors['schema'])
    foundation_schema = draw_module_box(4.5, 6.5, 2.5, 0.8, 'foundation.py\n基础几何', colors['schema'])
    load_schema = draw_module_box(7.5, 6.5, 2.5, 0.8, 'load.py\n荷载模型', colors['schema'])
    settlement_schema = draw_module_box(10.5, 6.5, 2.5, 0.8, 'settlement.py\n沉降模型', colors['schema'])
    stiffness_schema = draw_module_box(13.5, 6.5, 2.5, 0.8, 'stiffness.py\n刚度模型', colors['schema'])
    
    bearing_schema = draw_module_box(1.5, 5.5, 2.5, 0.8, 'bearing_capacity.py\n承载力模型', colors['schema'])
    stability_schema = draw_module_box(4.5, 5.5, 2.5, 0.8, 'stability.py\n稳定性模型', colors['schema'])
    comprehensive_schema = draw_module_box(7.5, 5.5, 2.5, 0.8, 'comprehensive.py\n综合模型', colors['schema'])
    detachment_schema = draw_module_box(10.5, 5.5, 2.5, 0.8, 'detachment.py\n脱开模型', colors['schema'])
    self_weight_schema = draw_module_box(13.5, 5.5, 2.5, 0.8, 'self_weight.py\n自重模型', colors['schema'])
    
    geometry_schema = draw_module_box(16.5, 6, 2.5, 0.8, 'geometry.py\n几何验算', colors['schema'])
    init_schema = draw_module_box(20, 6, 2.5, 0.8, '__init__.py\n统一导出', colors['schema'])
    
    # === 第5层：工具层 ===
    util_layer = draw_layer_box(1, 2.5, 22, 2, '工具层 (Utils)', colors['util'], 12)
    
    # 工具模块
    logger_util = draw_module_box(2, 3.5, 3, 0.8, 'logger.py\n日志工具', colors['util'])
    soil_util = draw_module_box(6, 3.5, 4, 0.8, 'soil_layer_selector.py\n土层选择工具', colors['util'])
    config_util = draw_module_box(11, 3.5, 3, 0.8, 'config.py\n配置管理', colors['util'])
    validator_util = draw_module_box(15, 3.5, 3, 0.8, 'validators.py\n数据验证', colors['util'])
    
    # === 第6层：外部依赖 ===
    external_layer = draw_layer_box(1, 0.5, 22, 1.5, '外部依赖', colors['database'], 12)
    
    # 外部依赖
    fastapi_dep = draw_module_box(2, 1, 2.5, 0.8, 'FastAPI\nWeb框架', colors['database'])
    pydantic_dep = draw_module_box(5.5, 1, 2.5, 0.8, 'Pydantic\n数据验证', colors['database'])
    numpy_dep = draw_module_box(9, 1, 2.5, 0.8, 'NumPy\n数值计算', colors['database'])
    httpx_dep = draw_module_box(12.5, 1, 2.5, 0.8, 'HTTPX\nHTTP客户端', colors['database'])
    uvicorn_dep = draw_module_box(16, 1, 2.5, 0.8, 'Uvicorn\nASGI服务器', colors['database'])
    matplotlib_dep = draw_module_box(19.5, 1, 2.5, 0.8, 'Matplotlib\n图表生成', colors['database'])
    
    # === 绘制数据流箭头 ===
    
    # API层到服务层
    draw_arrow(calc_api, calc_service, color='blue', width=2)
    
    # 服务层到分析器层
    draw_arrow(calc_service, settlement, color='green')
    draw_arrow(calc_service, bearing, color='green')
    draw_arrow(calc_service, detachment, color='green')
    draw_arrow(calc_service, self_weight, color='green')
    draw_arrow(calc_service, load_calc, color='green')
    draw_arrow(calc_service, other_analyzers, color='green')
    
    # 分析器层到数据模型层
    draw_arrow(settlement, settlement_schema, color='orange')
    draw_arrow(bearing, bearing_schema, color='orange')
    draw_arrow(self_weight, self_weight_schema, color='orange')
    draw_arrow(load_calc, load_schema, color='orange')
    
    # 工具层到其他层
    draw_arrow(logger_util, calc_service, color='purple')
    draw_arrow(soil_util, calc_service, color='purple')
    
    # === 添加技术规范信息框 ===
    spec_box = FancyBboxPatch(
        (17.5, 11), 5, 2,
        boxstyle="round,pad=0.1",
        facecolor='#FFF9C4',
        edgecolor='orange',
        linewidth=2
    )
    ax.add_patch(spec_box)
    
    spec_text = """技术规范依据：
    
《陆上风电场工程风电机组基础设计规范》
• 6.3.1条 - 地基承载力验算
• 6.4.1条 - 沉降验算要求  
• 6.4.2条 - 倾斜验算要求
• 6.4.3条 - 沉降计算深度
• 相关抗震、抗滑、抗倾覆要求"""
    
    ax.text(20, 12, spec_text, ha='center', va='center', fontsize=9, 
           bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.9))
    
    # === 添加数据流说明 ===
    flow_box = FancyBboxPatch(
        (17.5, 3), 5, 4.5,
        boxstyle="round,pad=0.1",
        facecolor='#E1F5FE',
        edgecolor='blue',
        linewidth=2
    )
    ax.add_patch(flow_box)
    
    flow_text = """主要数据流：
    
1️⃣ 用户请求 → API控制器
2️⃣ 控制器 → 计算服务
3️⃣ 计算服务 → 各分析器
4️⃣ 分析器 → 数据模型验证
5️⃣ 工具层提供支持功能
6️⃣ 结果汇总 → 响应返回

计算步骤：
• 体型验算 → 自重计算
• 荷载组合 → 各项验算
• 结果评估 → 报告生成"""
    
    ax.text(20, 5.25, flow_text, ha='center', va='center', fontsize=9,
           bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.9))
    
    # === 添加图例 ===
    legend_y = 0.2
    ax.text(1, legend_y + 0.2, '图例:', fontsize=10, fontweight='bold')
    
    # 创建图例项
    legend_items = [
        (colors['api'], 'API层'),
        (colors['controller'], '控制层'),
        (colors['service'], '服务层'),
        (colors['analyzer'], '分析器'),
        (colors['schema'], '数据模型'),
        (colors['util'], '工具层'),
        (colors['database'], '外部依赖')
    ]
    
    for i, (color, label) in enumerate(legend_items):
        x_pos = 1 + i * 3
        if x_pos > 20:  # 换行
            x_pos = x_pos - 21
            legend_y = legend_y - 0.4
        
        legend_box = FancyBboxPatch((x_pos, legend_y), 0.3, 0.15, 
                                   boxstyle="round,pad=0.02", 
                                   facecolor=color, edgecolor='black')
        ax.add_patch(legend_box)
        ax.text(x_pos + 0.4, legend_y + 0.075, label, fontsize=8, va='center')
    
    # 保存图片
    plt.tight_layout()
    plt.savefig('wind_turbine_architecture_diagram.png', dpi=300, bbox_inches='tight', 
               facecolor='white', edgecolor='none')
    print("✓ 架构图已生成: wind_turbine_architecture_diagram.png")
    
    return fig

if __name__ == "__main__":
    try:
        print("=== 生成风机基础计算系统架构图 ===")
        fig = create_architecture_diagram()
        print("🎉 架构图生成成功！")
    except Exception as e:
        print(f"❌ 架构图生成失败: {e}")
        raise
