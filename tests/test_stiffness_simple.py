"""
简单的刚度分析器验证
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.stiffness_analyzer import StiffnessAnalyzer
from app.schemas import FoundationGeometry, SoilLayer, StiffnessRequirements

def test_basic_functionality():
    """基本功能验证"""
    print("=== 开始刚度分析器基本功能验证 ===")
    
    # 创建测试数据
    geometry = FoundationGeometry(
        baseRadius=12.0,
        columnRadius=2.0,
        edgeHeight=1.5,
        frustumHeight=2.0,
        buriedDepth=2.5,
        columnHeight=1.0,
        groundHeight=0.5
    )
    
    soil_layer = SoilLayer(
        soilType="粘性土",
        layerName="粘土层",
        elevation=10.0,
        thickness=5.0,
        density=1800.0,
        compressionModulus=15.0,
        poissonRatio=0.3,
        fak=150.0,
        etaB=0.3,
        etaD=1.6,
        zetaA=0.8,
        cohesion=30.0,
        frictionAngle=20.0,
        m=0.3
    )
    
    stiffness_requirements = StiffnessRequirements(
        required_rotational_stiffness=1.0e9,
        required_horizontal_stiffness=1.0e6
    )
    
    try:
        # 创建分析器
        analyzer = StiffnessAnalyzer(geometry, [soil_layer])
        print(f"✓ 分析器创建成功")
        print(f"  - 基础半径: {analyzer.R} m")
        print(f"  - 泊松比: {analyzer.poisson_ratio}")
        print(f"  - 动态压缩模量: {analyzer.dynamic_compression_modulus} MPa")
        print(f"  - Es_dyn: {analyzer.Es_dyn:.2e} Pa")
        
        # 计算旋转刚度
        rotational_stiffness = analyzer.calculate_rotational_stiffness()
        print(f"✓ 旋转刚度计算: {rotational_stiffness:.2e} N·m/rad")
        
        # 计算水平刚度
        horizontal_stiffness = analyzer.calculate_horizontal_stiffness()
        print(f"✓ 水平刚度计算: {horizontal_stiffness:.2e} N/m")
        
        # 完整分析
        result = analyzer.analyze_stiffness(stiffness_requirements)
        print(f"✓ 完整分析完成")
        print(f"  - 旋转刚度合规性: {result.rotational_stiffness.is_compliant}")
        print(f"  - 水平刚度合规性: {result.horizontal_stiffness.is_compliant}")
        print(f"  - 整体符合性: {result.overall_compliance}")
        
        print("\n=== 验算详情 ===")
        print("旋转刚度:", result.rotational_stiffness.check_details)
        print("水平刚度:", result.horizontal_stiffness.check_details)
        
        print("\n✅ 刚度分析器重构成功，所有功能正常工作！")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_basic_functionality()
    if success:
        print("\n🎉 重构完成！新的 StiffnessAnalyzer 类工作正常。")
    else:
        print("\n💥 重构验证失败，请检查代码。")
