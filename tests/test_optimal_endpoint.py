"""
测试最优方案计算接口
"""
import json
from app.schemas.comprehensive import ComprehensiveCalculationRequest

# 示例请求数据（简化版）
test_request_data = {
    "geometry": {
        "baseRadius": 12.0,
        "columnRadius": 4.0,
        "columnHeight": 1.5,
        "edgeHeight": 0.8,
        "frustumHeight": 2.0,
        "groundHeight": 0.2,
        "buriedDepth": 2.0
    },
    "material": {
        "concreteGrade": "C30",
        "concreteElasticModulus": 30000.0,
        "concreteDensity": 25.0,
        "concreteDesignCompressiveStrength": 14.3,
        "concreteTensileStrength": 2.01,
        "concreteAxialCompressiveStrength": 20.1,
        "rebarGrade": "HRB400",
        "rebarElasticModulus": 200000.0,
        "rebarDesignTensileStrength": 360.0,
        "soilFrictionCoefficient": 0.45
    },
    "soilLayers": [
        {
            "layerNumber": 1,
            "soilType": "粘土",
            "thickness": 3.0,
            "density": 18.5,
            "cohesion": 25.0,
            "frictionAngle": 15.0,
            "bearingCapacity": 180.0,
            "compressionModulus": 8.5,
            "k30": 15000.0
        }
    ],
    "windTurbine": {
        "model": "Test-3000",
        "ratedPower": 3000.0,
        "rotorDiameter": 130.0,
        "hubHeight": 120.0,
        "cutInWindSpeed": 3.0,
        "ratedWindSpeed": 11.0,
        "cutOutWindSpeed": 25.0,
        "nacelleWeight": 85000.0,
        "rotorWeight": 65000.0,
        "hubWeight": 25000.0,
        "maxTipSpeed": 80.0
    },
    "towerDrums": [
        {
            "drumNumber": 1,
            "bottomDiameter": 4.2,
            "topDiameter": 4.0,
            "height": 30.0,
            "wallThickness": 0.025,
            "weight": 15000.0
        }
    ],
    "turbineLoads": {
        "normal": {
            "Fr": 125.5,
            "Fv": 85.2,
            "Fz": -1200.0,
            "Mx": 2500.0,
            "My": 3200.0,
            "Mz": 150.0
        },
        "extreme": {
            "Fr": 285.5,
            "Fv": 125.2,
            "Fz": -1350.0,
            "Mx": 5500.0,
            "My": 7200.0,
            "Mz": 250.0
        },
        "fatigueUpper": {
            "Fr": 85.5,
            "Fv": 65.2,
            "Fz": -1100.0,
            "Mx": 1800.0,
            "My": 2200.0,
            "Mz": 100.0
        },
        "fatigueLower": {
            "Fr": 45.5,
            "Fv": 35.2,
            "Fz": -950.0,
            "Mx": 1200.0,
            "My": 1500.0,
            "Mz": 50.0
        }
    },
    "designParameters": {
        "safetyLevel": "一级",
        "importanceFactor": 1.1,
        "connectionType": "法兰连接",
        "turbineCapacity": 3.0,
        "hubHeight": 120.0,
        "coverSoilDensity": 18.0,
        "waterDepth": 2.5
    },
    "stiffnessRequirements": {
        "horizontalStiffness": 500000.0,
        "rotationalStiffness": 80000000.0,
        "verticalStiffness": 1200000.0,
        "allowableHorizontalDisplacement": 0.01,
        "allowableRotationalAngle": 0.005,
        "allowableVerticalSettlement": 0.02
    },
    "allowedDetachmentArea": {
        "maxDetachmentRatio": 0.15,
        "criticalDetachmentRatio": 0.10
    }
}

def test_request_parsing():
    """测试请求数据解析"""
    try:
        request = ComprehensiveCalculationRequest(**test_request_data)
        print("✓ 请求数据解析成功")
        
        # 测试参数范围
        geometry = request.geometry
        print(f"当前几何参数:")
        print(f"  - 基础底板半径: {geometry.base_radius} m")
        print(f"  - 台柱半径: {geometry.column_radius} m") 
        print(f"  - 台柱高度: {geometry.column_height} m")
        print(f"  - 基础边缘高度: {geometry.edge_height} m")
        print(f"  - 基础底板棱台高度: {geometry.frustum_height} m")
        
        return True
    except Exception as e:
        print(f"✗ 请求数据解析失败: {e}")
        return False

if __name__ == "__main__":
    print("测试最优方案计算接口...")
    test_request_parsing()
