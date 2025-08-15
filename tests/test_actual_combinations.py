"""
测试最优方案接口的实际参数组合情况
"""
import itertools

def test_actual_parameter_combinations():
    """测试实际接口中使用的参数组合"""
    print("测试最优方案接口的实际参数组合...")
    
    # 与接口中相同的参数范围
    base_radius_range = [9.0, 10.0, 11.0, 12.0]  # 基础底板半径：9-12米
    column_radius_range = [3.0, 4.0, 5.0]  # 台柱半径：3-5.3米（考虑到步长，取3,4,5）
    column_height_range = [1.4, 2.4]  # 台柱高度：1.4-2.8米（考虑到步长，取1.4,2.4）
    edge_height_range = [0.8, 1.0]  # 基础边缘高度：0.8-1米（考虑到步长，取0.8,1.0）
    frustum_height_range = [0.8, 1.8, 2.8]  # 基础底板棱台高度：0.8-2.8米
    
    # 生成所有参数组合
    param_combinations = list(itertools.product(
        base_radius_range,
        column_radius_range, 
        column_height_range,
        edge_height_range,
        frustum_height_range
    ))
    
    total_combinations = len(param_combinations)
    print(f"理论总组合数: {total_combinations}")
    
    # 模拟地面露出高度（从实际请求中获取）
    ground_height = 0.2  # 这个值需要从原始请求中获取
    
    # 统计有效组合
    valid_geometric = []  # 几何约束有效的组合
    valid_buried_depth = []  # 埋深约束有效的组合
    valid_all = []  # 所有约束都有效的组合
    
    for base_radius, column_radius, column_height, edge_height, frustum_height in param_combinations:
        # 检查几何约束：台柱半径必须小于底板半径
        geometric_valid = column_radius < base_radius
        
        # 计算基础埋深
        buried_depth = column_height + edge_height + frustum_height - ground_height
        
        # 检查埋深约束：3-5米
        depth_valid = 3.0 <= buried_depth <= 5.0
        
        if geometric_valid:
            valid_geometric.append((base_radius, column_radius, column_height, edge_height, frustum_height, buried_depth))
        
        if depth_valid:
            valid_buried_depth.append((base_radius, column_radius, column_height, edge_height, frustum_height, buried_depth))
        
        if geometric_valid and depth_valid:
            valid_all.append((base_radius, column_radius, column_height, edge_height, frustum_height, buried_depth))
    
    print(f"通过几何约束的组合: {len(valid_geometric)}")
    print(f"通过埋深约束的组合: {len(valid_buried_depth)}")
    print(f"通过所有约束的组合: {len(valid_all)}")
    print(f"过滤率: {(total_combinations - len(valid_all)) / total_combinations * 100:.1f}%")
    
    print("\n前10个有效组合示例:")
    for i, (br, cr, ch, eh, fh, bd) in enumerate(valid_all[:10]):
        print(f"  {i+1}. 底板={br}, 台柱={cr}, 台柱高={ch}, 边缘={eh}, 棱台={fh} → 埋深={bd:.1f}m")
    
    if len(valid_all) > 10:
        print(f"  ... 还有 {len(valid_all) - 10} 个有效组合")
    
    # 分析埋深分布
    depth_distribution = {}
    for _, _, _, _, _, bd in valid_all:
        depth_range = f"{int(bd)}-{int(bd)+1}"
        depth_distribution[depth_range] = depth_distribution.get(depth_range, 0) + 1
    
    print(f"\n埋深分布:")
    for range_key, count in sorted(depth_distribution.items()):
        print(f"  {range_key}m: {count} 个组合")
    
    return len(valid_all)

def test_specific_edge_cases():
    """测试特定的边界情况"""
    print("\n测试特定边界情况...")
    
    ground_height = 0.2
    
    # 边界测试用例
    edge_cases = [
        # [base_radius, column_radius, column_height, edge_height, frustum_height, 期望结果]
        (9.0, 9.0, 1.4, 0.8, 0.8, "几何无效"),  # 台柱半径=底板半径，几何无效
        (9.0, 4.0, 1.4, 0.8, 0.8, "埋深过浅"),  # 埋深=2.8m，过浅
        (12.0, 3.0, 1.4, 1.0, 0.8, "完全有效"),  # 埋深=3.0m，边界有效
        (12.0, 3.0, 2.4, 1.0, 1.8, "完全有效"),  # 埋深=5.0m，边界有效
        (12.0, 3.0, 2.4, 1.0, 2.8, "埋深过深"),  # 埋深=6.0m，过深
    ]
    
    for i, (br, cr, ch, eh, fh, expected) in enumerate(edge_cases):
        geometric_valid = cr < br
        buried_depth = ch + eh + fh - ground_height
        depth_valid = 3.0 <= buried_depth <= 5.0
        
        if not geometric_valid:
            actual = "几何无效"
        elif not depth_valid:
            actual = "埋深过深" if buried_depth > 5.0 else "埋深过浅"
        else:
            actual = "完全有效"
        
        status = "✓" if actual == expected else "✗"
        print(f"{status} 边界测试{i+1}: 底板={br}, 台柱={cr}, 台柱高={ch}, 边缘={eh}, 棱台={fh}")
        print(f"    埋深={buried_depth:.1f}m, 结果={actual}, 期望={expected}")

if __name__ == "__main__":
    print("=" * 70)
    valid_count = test_actual_parameter_combinations()
    test_specific_edge_cases()
    
    print("\n" + "=" * 70)
    print(f"🎯 总结: 在144个理论组合中，有 {valid_count} 个组合满足所有约束条件")
    print("   这些组合将被用于最优方案计算，寻找混凝土体积最小的设计方案。")
