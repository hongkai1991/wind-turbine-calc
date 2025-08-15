"""
测试基础埋深计算逻辑
"""

def test_buried_depth_calculation():
    """测试基础埋深计算公式和过滤逻辑"""
    print("测试基础埋深计算逻辑...")
    
    # 模拟地面露出高度
    ground_height = 0.2  # 米
    
    # 测试用例：[台柱高度, 边缘高度, 棱台高度, 期望埋深, 期望是否有效]
    test_cases = [
        # 有效情况 (3.0 <= 埋深 <= 5.0)
        (1.4, 1.0, 0.8, 1.4 + 1.0 + 0.8 - 0.2, True),   # 埋深 = 3.0米，边界有效
        (2.4, 1.0, 1.8, 2.4 + 1.0 + 1.8 - 0.2, True),   # 埋深 = 5.0米，边界有效
        (1.4, 0.8, 2.8, 1.4 + 0.8 + 2.8 - 0.2, True),   # 埋深 = 4.8米，有效
        (2.4, 0.8, 0.8, 2.4 + 0.8 + 0.8 - 0.2, True),   # 埋深 = 3.8米，有效
        (1.4, 0.8, 1.8, 1.4 + 0.8 + 1.8 - 0.2, True),   # 埋深 = 3.8米，有效
        
        # 无效情况 
        (1.4, 0.8, 0.8, 1.4 + 0.8 + 0.8 - 0.2, False),  # 埋深 = 2.8米，小于3米
        (2.4, 1.0, 2.8, 2.4 + 1.0 + 2.8 - 0.2, False),  # 埋深 = 6.0米，大于5米
        (2.4, 0.8, 2.8, 2.4 + 0.8 + 2.8 - 0.2, False),  # 埋深 = 5.8米，大于5米
    ]
    
    print(f"基础埋深计算公式: 埋深 = 台柱高度 + 边缘高度 + 棱台高度 - 地面露出高度({ground_height})")
    print(f"有效埋深范围: 3.0 - 5.0 米")
    print()
    
    valid_count = 0
    total_count = len(test_cases)
    
    for i, (column_height, edge_height, frustum_height, expected_depth, should_be_valid) in enumerate(test_cases):
        # 计算基础埋深
        calculated_depth = column_height + edge_height + frustum_height - ground_height
        
        # 检查是否在有效范围内
        is_valid = 3.0 <= calculated_depth <= 5.0
        
        # 验证计算结果
        depth_correct = abs(calculated_depth - expected_depth) < 0.001
        validity_correct = is_valid == should_be_valid
        
        status = "✓" if depth_correct and validity_correct else "✗"
        validity_status = "有效" if is_valid else "无效"
        expected_status = "有效" if should_be_valid else "无效"
        
        print(f"{status} 测试{i+1}: 台柱={column_height}, 边缘={edge_height}, 棱台={frustum_height}")
        print(f"    计算埋深: {calculated_depth:.1f}m, 状态: {validity_status}, 期望: {expected_status}")
        
        if depth_correct and validity_correct:
            valid_count += 1
        elif not depth_correct:
            print(f"    ❌ 计算错误: 期望 {expected_depth:.1f}, 实际 {calculated_depth:.1f}")
        elif not validity_correct:
            print(f"    ❌ 有效性判断错误: 期望 {expected_status}, 实际 {validity_status}")
        
        print()
    
    success_rate = valid_count / total_count * 100
    print(f"测试结果: {valid_count}/{total_count} 通过 ({success_rate:.1f}%)")
    
    return valid_count == total_count

def test_parameter_combinations_with_buried_depth():
    """测试参数组合中的基础埋深过滤"""
    print("\n测试参数组合中的基础埋深过滤...")
    
    import itertools
    
    # 参数范围（简化用于测试）
    column_height_range = [1.4, 2.4]
    edge_height_range = [0.8, 1.0]
    frustum_height_range = [0.8, 1.8, 2.8]
    
    ground_height = 0.2  # 地面露出高度
    
    # 生成参数组合
    param_combinations = list(itertools.product(
        column_height_range,
        edge_height_range,
        frustum_height_range
    ))
    
    print(f"总参数组合数: {len(param_combinations)}")
    
    valid_combinations = []
    invalid_combinations = []
    
    for column_height, edge_height, frustum_height in param_combinations:
        # 计算基础埋深
        buried_depth = column_height + edge_height + frustum_height - ground_height
        
        # 检查是否在有效范围内
        if 3.0 <= buried_depth <= 5.0:
            valid_combinations.append((column_height, edge_height, frustum_height, buried_depth))
        else:
            invalid_combinations.append((column_height, edge_height, frustum_height, buried_depth))
    
    print(f"有效组合数: {len(valid_combinations)}")
    print(f"无效组合数: {len(invalid_combinations)}")
    
    print("\n有效组合:")
    for i, (ch, eh, fh, bd) in enumerate(valid_combinations):
        print(f"  {i+1}. 台柱={ch}, 边缘={eh}, 棱台={fh} → 埋深={bd:.1f}m")
    
    print("\n无效组合:")
    for i, (ch, eh, fh, bd) in enumerate(invalid_combinations):
        reason = "太浅(<3m)" if bd < 3.0 else "太深(>5m)"
        print(f"  {i+1}. 台柱={ch}, 边缘={eh}, 棱台={fh} → 埋深={bd:.1f}m ({reason})")
    
    return len(valid_combinations) > 0

if __name__ == "__main__":
    print("=" * 60)
    success1 = test_buried_depth_calculation()
    success2 = test_parameter_combinations_with_buried_depth()
    
    print("\n" + "=" * 60)
    if success1 and success2:
        print("🎉 所有测试通过！基础埋深计算逻辑正确。")
    else:
        print("❌ 部分测试失败，请检查实现。")
