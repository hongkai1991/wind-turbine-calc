#!/usr/bin/env python3
"""
生成风机基础计算项目流程图
使用matplotlib和graphviz生成PNG格式的流程图
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, ConnectionPatch
import numpy as np

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']  
plt.rcParams['axes.unicode_minus'] = False

def create_flowchart():
    """创建风机基础计算项目流程图"""
    
    # 创建图形和轴
    fig, ax = plt.subplots(1, 1, figsize=(20, 16))
    ax.set_xlim(0, 20)
    ax.set_ylim(0, 16)
    ax.axis('off')
    
    # 定义颜色
    colors = {
        'input': '#E3F2FD',      # 浅蓝色 - 输入
        'process': '#FFF3E0',    # 浅橙色 - 处理过程
        'validation': '#E8F5E8', # 浅绿色 - 验算
        'output': '#FCE4EC',     # 浅粉色 - 输出
        'decision': '#F3E5F5'    # 浅紫色 - 决策
    }
    
    # 定义框的样式
    box_style = "round,pad=0.1"
    
    def draw_box(x, y, width, height, text, color, text_size=9):
        """绘制带文本的圆角矩形"""
        box = FancyBboxPatch(
            (x - width/2, y - height/2), width, height,
            boxstyle=box_style,
            facecolor=color,
            edgecolor='black',
            linewidth=1.5
        )
        ax.add_patch(box)
        ax.text(x, y, text, ha='center', va='center', fontsize=text_size, fontweight='bold', wrap=True)
        return (x, y)
    
    def draw_arrow(start, end, style='->', color='black', width=2):
        """绘制箭头连接"""
        ax.annotate('', xy=end, xytext=start,
                   arrowprops=dict(arrowstyle=style, color=color, lw=width))
    
    # 标题
    ax.text(10, 15.5, '风机重力基础整体验算系统流程图', ha='center', va='center', 
            fontsize=20, fontweight='bold')
    
    # 1. 输入层
    input1 = draw_box(3, 14, 2.5, 0.8, '基础几何参数\n(geometry)', colors['input'])
    input2 = draw_box(7, 14, 2.5, 0.8, '材料属性\n(material)', colors['input'])
    input3 = draw_box(11, 14, 2.5, 0.8, '土层信息\n(soilLayers)', colors['input'])
    input4 = draw_box(15, 14, 2.5, 0.8, '风机荷载\n(turbineLoads)', colors['input'])
    input5 = draw_box(17, 14, 2.5, 0.8, '设计参数\n(designParameters)', colors['input'])
    
    # 2. 数据预处理
    preprocess = draw_box(10, 12.5, 4, 0.8, '数据预处理与土层选择', colors['process'])
    
    # 连接输入到预处理
    for inp in [input1, input2, input3, input4, input5]:
        draw_arrow(inp, preprocess)
    
    # 3. 第一阶段验算
    stage1_title = ax.text(3, 11.3, '第一阶段：基础设计验算', ha='left', va='center', 
                          fontsize=12, fontweight='bold', color='red')
    
    geom_valid = draw_box(3, 10.5, 2.8, 0.8, '1. 基础体型验算', colors['validation'])
    self_weight = draw_box(7, 10.5, 2.8, 0.8, '2. 基础自重计算', colors['validation'])
    tower_load = draw_box(11, 10.5, 2.8, 0.8, '3. 塔底荷载计算', colors['validation'])
    
    # 连接预处理到第一阶段
    draw_arrow(preprocess, geom_valid)
    draw_arrow(preprocess, self_weight)
    draw_arrow(preprocess, tower_load)
    
    # 4. 荷载组合计算
    load_combo = draw_box(10, 9, 5, 0.8, '4. 荷载组合计算 (四种工况)', colors['process'])
    
    # 连接第一阶段到荷载组合
    draw_arrow(geom_valid, load_combo)
    draw_arrow(self_weight, load_combo)
    draw_arrow(tower_load, load_combo)
    
    # 5. 第二阶段验算 - 左侧
    stage2_title = ax.text(1, 7.8, '第二阶段：承载力与稳定性验算', ha='left', va='center', 
                          fontsize=12, fontweight='bold', color='red')
    
    detachment = draw_box(3, 7, 2.5, 0.7, '5. 脱开面积\n验算', colors['validation'], 8)
    bearing = draw_box(6.5, 7, 2.5, 0.7, '6. 地基承载力\n验算', colors['validation'], 8)
    settlement = draw_box(10, 7, 2.5, 0.7, '7. 地基变形\n验算', colors['validation'], 8)
    overturning = draw_box(13.5, 7, 2.5, 0.7, '8. 抗倾覆\n验算', colors['validation'], 8)
    sliding = draw_box(17, 7, 2.5, 0.7, '9. 基础抗滑\n验算', colors['validation'], 8)
    
    # 连接荷载组合到第二阶段
    for val in [detachment, bearing, settlement, overturning, sliding]:
        draw_arrow(load_combo, val)
    
    # 6. 第三阶段验算
    stage3_title = ax.text(3, 5.8, '第三阶段：刚度与强度验算', ha='left', va='center', 
                          fontsize=12, fontweight='bold', color='red')
    
    stiffness = draw_box(4, 5, 2.5, 0.7, '10. 刚度验算', colors['validation'], 8)
    shear = draw_box(8, 5, 2.8, 0.7, '11. 基础抗剪\n强度验算', colors['validation'], 8)
    punching = draw_box(12.5, 5, 2.8, 0.7, '12. 地基抗冲切\n验算', colors['validation'], 8)
    
    # 连接到第三阶段
    draw_arrow(load_combo, stiffness)
    draw_arrow(load_combo, shear)
    draw_arrow(load_combo, punching)
    
    # 7. 结果汇总
    summary = draw_box(10, 3.5, 4, 0.8, '结果汇总与评估', colors['process'])
    
    # 连接所有验算到汇总
    for val in [detachment, bearing, settlement, overturning, sliding, stiffness, shear, punching]:
        draw_arrow(val, summary)
    
    # 8. 决策判断
    decision = draw_box(10, 2, 3, 1.2, '整体设计\n是否符合要求？', colors['decision'])
    draw_arrow(summary, decision)
    
    # 9. 输出结果
    success = draw_box(6, 0.5, 2.5, 0.8, '设计通过\n输出报告', colors['output'])
    failure = draw_box(14, 0.5, 2.5, 0.8, '设计不通过\n需要调整', colors['output'])
    
    # 连接决策到结果
    draw_arrow(decision, success)
    draw_arrow(decision, failure)
    
    # 添加决策标签
    ax.text(7.5, 1.2, '是', ha='center', va='center', fontsize=10, fontweight='bold', color='green')
    ax.text(12.5, 1.2, '否', ha='center', va='center', fontsize=10, fontweight='bold', color='red')
    
    # 10. 添加技术规范框
    spec_box = FancyBboxPatch(
        (0.5, 8.5), 1.5, 4,
        boxstyle="round,pad=0.05",
        facecolor='#FFF9C4',
        edgecolor='orange',
        linewidth=2
    )
    ax.add_patch(spec_box)
    
    spec_text = """技术规范:
    
《陆上风电场工程
风电机组基础
设计规范》

6.3.1条 - 承载力
6.4.1条 - 沉降
6.4.2条 - 倾斜
6.4.3条 - 深度
"""
    ax.text(1.25, 10.5, spec_text, ha='center', va='center', fontsize=8, 
           bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8))
    
    # 11. 添加主要模块框
    module_box = FancyBboxPatch(
        (18.2, 8.5), 1.5, 4,
        boxstyle="round,pad=0.05",
        facecolor='#E1F5FE',
        edgecolor='blue',
        linewidth=2
    )
    ax.add_patch(module_box)
    
    module_text = """核心模块:

• CalculationService
• SettlementAnalyzer  
• BearingCapacityAnalyzer
• SelfWeightCalculator
• LoadCalculator
• DetachmentAnalyzer
"""
    ax.text(18.95, 10.5, module_text, ha='center', va='center', fontsize=8,
           bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8))
    
    # 12. 添加图例
    legend_y = 1.5
    ax.text(1, legend_y + 0.3, '图例:', fontsize=10, fontweight='bold')
    
    # 输入
    legend_box1 = FancyBboxPatch((1, legend_y - 0.2), 0.3, 0.2, boxstyle=box_style, 
                                facecolor=colors['input'], edgecolor='black')
    ax.add_patch(legend_box1)
    ax.text(1.5, legend_y - 0.1, '输入数据', fontsize=8)
    
    # 处理
    legend_box2 = FancyBboxPatch((1, legend_y - 0.6), 0.3, 0.2, boxstyle=box_style, 
                                facecolor=colors['process'], edgecolor='black')
    ax.add_patch(legend_box2)
    ax.text(1.5, legend_y - 0.5, '处理过程', fontsize=8)
    
    # 验算
    legend_box3 = FancyBboxPatch((1, legend_y - 1.0), 0.3, 0.2, boxstyle=box_style, 
                                facecolor=colors['validation'], edgecolor='black')
    ax.add_patch(legend_box3)
    ax.text(1.5, legend_y - 0.9, '验算模块', fontsize=8)
    
    # 决策
    legend_box4 = FancyBboxPatch((3, legend_y - 0.2), 0.3, 0.2, boxstyle=box_style, 
                                facecolor=colors['decision'], edgecolor='black')
    ax.add_patch(legend_box4)
    ax.text(3.5, legend_y - 0.1, '决策判断', fontsize=8)
    
    # 输出
    legend_box5 = FancyBboxPatch((3, legend_y - 0.6), 0.3, 0.2, boxstyle=box_style, 
                                facecolor=colors['output'], edgecolor='black')
    ax.add_patch(legend_box5)
    ax.text(3.5, legend_y - 0.5, '输出结果', fontsize=8)
    
    # 保存图片
    plt.tight_layout()
    plt.savefig('wind_turbine_foundation_flowchart.png', dpi=300, bbox_inches='tight', 
               facecolor='white', edgecolor='none')
    print("✓ 流程图已生成: wind_turbine_foundation_flowchart.png")
    
    return fig

if __name__ == "__main__":
    try:
        print("=== 生成风机基础计算项目流程图 ===")
        fig = create_flowchart()
        print("🎉 流程图生成成功！")
    except Exception as e:
        print(f"❌ 流程图生成失败: {e}")
        raise
