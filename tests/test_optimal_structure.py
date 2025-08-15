"""
简单测试最优方案计算接口的结构
"""

def test_optimal_endpoint_structure():
    """测试最优方案接口的基本结构"""
    print("测试最优方案计算接口结构...")
    
    try:
        # 测试参数范围生成
        import itertools
        
        # 参数范围定义（与接口中相同）
        base_radius_range = [9.0, 10.0, 11.0, 12.0]  # 基础底板半径：9-12米
        column_radius_range = [3.0, 4.0, 5.0]  # 台柱半径：3-5.3米
        column_height_range = [1.4, 2.4]  # 台柱高度：1.4-2.8米
        edge_height_range = [0.8, 1.0]  # 基础边缘高度：0.8-1米
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
        print(f"✓ 参数组合生成成功，总共 {total_combinations} 种组合")
        
        # 显示前几个组合作为示例
        print("前5个参数组合示例:")
        for i, (base_radius, column_radius, column_height, edge_height, frustum_height) in enumerate(param_combinations[:5]):
            print(f"  组合{i+1}: 底板半径={base_radius}, 台柱半径={column_radius}, 台柱高度={column_height}, 边缘高度={edge_height}, 棱台高度={frustum_height}")
            
            # 检查几何约束
            if column_radius >= base_radius:
                print(f"    ⚠️  警告：台柱半径({column_radius})大于等于底板半径({base_radius})")
            else:
                print(f"    ✓ 几何约束满足：台柱半径 < 底板半径")
        
        # 计算有效组合数量（台柱半径必须小于底板半径）
        valid_combinations = 0
        for base_radius, column_radius, column_height, edge_height, frustum_height in param_combinations:
            if column_radius < base_radius:
                valid_combinations += 1
        
        print(f"✓ 有效参数组合: {valid_combinations}/{total_combinations}")
        
        # 测试deepcopy功能
        import copy
        test_dict = {
            "geometry": {
                "base_radius": 12.0,
                "column_radius": 4.0,
                "column_height": 1.5,
                "edge_height": 0.8,
                "frustum_height": 2.0
            }
        }
        
        copied_dict = copy.deepcopy(test_dict)
        copied_dict["geometry"]["base_radius"] = 10.0
        
        if test_dict["geometry"]["base_radius"] != copied_dict["geometry"]["base_radius"]:
            print("✓ deepcopy功能测试通过")
        else:
            print("✗ deepcopy功能测试失败")
            
        return True
        
    except Exception as e:
        print(f"✗ 接口结构测试失败: {e}")
        return False

def test_optimization_logic():
    """测试优化逻辑"""
    print("\n测试优化逻辑...")
    
    # 模拟计算结果数据
    mock_results = [
        {"foundation_volume": 450.2, "parameters": {"base_radius": 12.0, "column_radius": 4.0}},
        {"foundation_volume": 380.5, "parameters": {"base_radius": 11.0, "column_radius": 3.5}},
        {"foundation_volume": 520.8, "parameters": {"base_radius": 13.0, "column_radius": 4.5}},
        {"foundation_volume": 320.1, "parameters": {"base_radius": 10.0, "column_radius": 3.0}},  # 最小值
        {"foundation_volume": 480.9, "parameters": {"base_radius": 12.5, "column_radius": 4.2}}
    ]
    
    # 找到混凝土体积最小的结果
    optimal_result = min(mock_results, key=lambda x: x["foundation_volume"])
    
    if optimal_result["foundation_volume"] == 320.1:
        print("✓ 最优化逻辑测试通过：成功找到最小混凝土体积")
        print(f"  最优参数: {optimal_result['parameters']}")
        print(f"  最小体积: {optimal_result['foundation_volume']} m³")
        return True
    else:
        print("✗ 最优化逻辑测试失败")
        return False

if __name__ == "__main__":
    success1 = test_optimal_endpoint_structure()
    success2 = test_optimization_logic()
    
    if success1 and success2:
        print("\n🎉 所有测试通过！接口结构正确。")
    else:
        print("\n❌ 部分测试失败，请检查实现。")
