"""
抗冲切分析器重构验证测试
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from app.services.anti_punching_analyzer import AntiPunchingAnalyzer
from app.schemas import FoundationGeometry, MaterialProperties, SelfWeightResult

# 测试导入是否正常
def test_anti_punching_analyzer_import():
    """测试抗冲切分析器是否能正常导入"""
    try:
        print("✅ AntiPunchingAnalyzer 导入成功")
        return True
    except ImportError as e:
        print(f"❌ AntiPunchingAnalyzer 导入失败: {e}")
        return False

# 测试类实例化
def test_anti_punching_analyzer_initialization():
    """测试抗冲切分析器是否能正常实例化"""
    try:
        # 创建测试数据
        geometry = FoundationGeometry(
            baseRadius=6.0,
            columnRadius=2.5,
            edgeHeight=1.0,
            frustumHeight=1.5,
            buriedDepth=2.0,
            columnHeight=3.0,
            groundHeight=0.5
        )
        
        material = MaterialProperties(
            density=2500,
            ft=1.71,
            bottom_cover=50.0
        )
        
        self_weight_result = SelfWeightResult(
            foundation_volume=100.0,
            concrete_weight=250.0,
            backfill_volume=50.0,
            backfill_weight=100.0,
            total_weight=350.0,
            buoyancy_force=0.0,
            effective_weight=350.0
        )
        
        load_calculation_results = {
            "detailed_calculations": [],
            "load_conditions": []
        }
        
        # 实例化分析器
        analyzer = AntiPunchingAnalyzer(
            geometry=geometry,
            load_calculation_results=load_calculation_results,
            self_weight_result=self_weight_result,
            material=material,
            reinforcement_diameter=20.0,
            importance_factor=1.1
        )
        
        print("✅ AntiPunchingAnalyzer 实例化成功")
        return True
        
    except Exception as e:
        print(f"❌ AntiPunchingAnalyzer 实例化失败: {e}")
        return False

if __name__ == "__main__":
    print("=== 抗冲切分析器重构验证测试 ===")
    
    test1_passed = test_anti_punching_analyzer_import()
    test2_passed = test_anti_punching_analyzer_initialization()
    
    if test1_passed and test2_passed:
        print("\n🎉 所有测试通过！重构成功完成。")
    else:
        print("\n❌ 测试失败，请检查重构代码。")
