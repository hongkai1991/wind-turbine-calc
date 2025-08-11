"""
综合计算数据模型模块
包含综合计算请求、响应和相关参数
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from .foundation import FoundationGeometry, MaterialProperties, SoilLayer
from .load import WindTurbineInfo, TowerDrum, TurbineLoadConditions, TowerBaseLoadRequest
from .stiffness import StiffnessRequirements
from .detachment import AllowedDetachmentArea
from .base import SoilType, LoadCase


class DesignParameters(BaseModel):
    """设计参数"""
    safety_level: str = Field(..., alias="safetyLevel", description="安全等级")
    importance_factor: float = Field(..., alias="importanceFactor", gt=0, description="结构重要性系数γ0")
    connection_type: str = Field(..., alias="connectionType", description="连接方式")
    turbine_capacity: float = Field(..., alias="turbineCapacity", gt=0, description="风机容量(MW)")
    hub_height: float = Field(..., alias="hubHeight", gt=0, description="轮毂高度(m)")
    cover_soil_density: float = Field(default=18.0, alias="coverSoilDensity", gt=0, description="覆土容重(kN/m³)")
    water_depth: float = Field(..., alias="waterDepth", ge=0, description="地下水深度(m)")
    
    def validate_parameters(self) -> bool:
        """验证参数有效性"""
        # 验证安全等级
        valid_safety_levels = ["一级", "二级", "三级"]
        if self.safety_level not in valid_safety_levels:
            return False
        
        # 验证重要性系数范围
        if not (0.8 <= self.importance_factor <= 1.1):
            return False
            
        # 验证风机容量范围
        if not (0.5 <= self.turbine_capacity <= 15.0):
            return False
            
        # 验证轮毂高度范围
        if not (50.0 <= self.hub_height <= 200.0):
            return False
            
        return True
    
    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "safetyLevel": "一级",
                "importanceFactor": 1.1,
                "connectionType": "法兰连接",
                "turbineCapacity": 3.0,
                "hubHeight": 120.0,
                "coverSoilDensity": 18.0,
                "waterDepth": 2.5
            }
        }


class FoundationCalculationRequest(BaseModel):
    """基础计算请求模式"""
    turbine_height: float = Field(..., gt=0, description="风机高度(m)")
    rotor_diameter: float = Field(..., gt=0, description="叶轮直径(m)")
    rated_power: float = Field(..., gt=0, description="额定功率(kW)")
    wind_speed: float = Field(..., gt=0, le=50, description="设计风速(m/s)")
    soil_type: SoilType = Field(..., description="土壤类型")
    
    class Config:
        json_schema_extra = {
            "example": {
                "turbine_height": 120.0,
                "rotor_diameter": 130.0,
                "rated_power": 3000.0,
                "wind_speed": 25.0,
                "soil_type": "粘土"
            }
        }


class FoundationResult(BaseModel):
    """基础计算结果模式"""
    foundation_type: str = Field(..., description="基础类型")
    foundation_diameter: float = Field(..., description="基础直径(m)")
    foundation_depth: float = Field(..., description="基础深度(m)")
    concrete_volume: float = Field(..., description="混凝土体积(m³)")
    steel_weight: float = Field(..., description="钢筋重量(t)")
    estimated_cost: Optional[float] = Field(None, description="预估成本(万元)")

    class Config:
        json_schema_extra = {
            "example": {
                "foundation_type": "圆形重力基础",
                "foundation_diameter": 24.0,
                "foundation_depth": 4.5,
                "concrete_volume": 450.2,
                "steel_weight": 12.5,
                "estimated_cost": 180.0
            }
        }


class StabilityResult(BaseModel):
    """稳定性检查结果模式"""
    stability_status: str = Field(..., description="稳定性状态")
    overturning_safety_factor: float = Field(..., description="抗倾覆安全系数")
    sliding_safety_factor: float = Field(..., description="抗滑移安全系数")
    bearing_capacity_ratio: float = Field(..., description="承载力比值")
    is_stable: bool = Field(..., description="是否稳定")

    class Config:
        json_schema_extra = {
            "example": {
                "stability_status": "稳定",
                "overturning_safety_factor": 2.5,
                "sliding_safety_factor": 3.2,
                "bearing_capacity_ratio": 0.75,
                "is_stable": True
            }
        }


class CalculationResponse(BaseModel):
    """通用计算响应模式"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")
    data: Optional[Dict[str, Any]] = Field(None, description="响应数据")
    errors: Optional[Dict[str, str]] = Field(None, description="错误信息")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "计算完成",
                "data": {"result": "success"},
                "errors": None
            }
        }


class ComprehensiveCalculationRequest(BaseModel):
    """综合计算请求 - 使用小驼峰命名"""  
    geometry: FoundationGeometry = Field(..., description="基础几何信息")
    material: MaterialProperties = Field(..., description="材料属性信息")
    soilLayers: List[SoilLayer] = Field(..., description="土层信息列表")
    windTurbine: WindTurbineInfo = Field(..., description="风机信息")
    towerDrums: List[TowerDrum] = Field(..., description="塔筒段信息列表")
    turbineLoads: TurbineLoadConditions = Field(..., description="塔筒底部风机荷载六种工况")
    designParameters: DesignParameters = Field(..., description="设计参数")
    stiffnessRequirements: StiffnessRequirements = Field(..., description="刚度要求参数")
    allowedDetachmentArea: AllowedDetachmentArea = Field(..., description="允许脱开面积参数")
    
    def to_original_format(self) -> tuple:
        """转换为原有格式以便与现有服务兼容"""
        return self.geometry, self.material, self.soilLayers, self.designParameters, self.stiffnessRequirements
    
    def get_tower_base_load_request(self) -> TowerBaseLoadRequest:
        """获取塔筒底部荷载计算请求对象"""
        return TowerBaseLoadRequest(
            windTurbine=self.windTurbine,
            towerDrums=self.towerDrums
        )
    
    def get_loading_conditions(self) -> List[Dict[str, Any]]:
        """获取四种工况的荷载条件列表，用于传递给LoadingCondition"""
        conditions = []
        
        # 正常工况
        conditions.append({
            "case_type": LoadCase.NORMAL,
            "Fr": self.turbineLoads.normal.Fr,
            "Fv": self.turbineLoads.normal.Fv,
            "Fz": self.turbineLoads.normal.Fz,
            "Mx": self.turbineLoads.normal.Mx,
            "My": self.turbineLoads.normal.My,
            "Mz": self.turbineLoads.normal.Mz
        })
        
        # 极端工况
        conditions.append({
            "case_type": LoadCase.EXTREME,
            "Fr": self.turbineLoads.extreme.Fr,
            "Fv": self.turbineLoads.extreme.Fv,
            "Fz": self.turbineLoads.extreme.Fz,
            "Mx": self.turbineLoads.extreme.Mx,
            "My": self.turbineLoads.extreme.My,
            "Mz": self.turbineLoads.extreme.Mz
        })
        
        # 疲劳工况上限
        conditions.append({
            "case_type": LoadCase.FATIGUE_UPPER,
            "Fr": self.turbineLoads.fatigueUpper.Fr,
            "Fv": self.turbineLoads.fatigueUpper.Fv,
            "Fz": self.turbineLoads.fatigueUpper.Fz,
            "Mx": self.turbineLoads.fatigueUpper.Mx,
            "My": self.turbineLoads.fatigueUpper.My,
            "Mz": self.turbineLoads.fatigueUpper.Mz
        })
        
        # 疲劳工况下限
        conditions.append({
            "case_type": LoadCase.FATIGUE_LOWER,
            "Fr": self.turbineLoads.fatigueLower.Fr,
            "Fv": self.turbineLoads.fatigueLower.Fv,
            "Fz": self.turbineLoads.fatigueLower.Fz,
            "Mx": self.turbineLoads.fatigueLower.Mx,
            "My": self.turbineLoads.fatigueLower.My,
            "Mz": self.turbineLoads.fatigueLower.Mz
        })
        
        return conditions
    
    class Config:
        json_schema_extra = {
            "example": {
                "geometry": {
                    "baseRadius": 12.0,
                    "buriedDepth": 4.5,
                    "columnHeight": 1.2,
                    "columnRadius": 3.1,
                    "edgeHeight": 0.8,
                    "frustumHeight": 3.1,
                    "groundHeight": 0.5
                },
                "material": {
                    "topCover": 60.0,
                    "bottomCover": 50.0,
                    "columnCover": 50.0,
                    "concreteGrade": "C40",
                    "cushionThickness": 100.0,
                    "density": 25.0,
                    "ec": 32500.0,
                    "efc": 15000.0,
                    "fc": 19.1,
                    "fck": 26.8,
                    "ft": 1.71,
                    "ftk": 2.39
                },
                "stiffnessRequirements": {
                    "requiredRotationalStiffness": 100000000000.0,
                    "requiredHorizontalStiffness": 1000000000.0
                },
                "soilLayers": [
                    {
                        "soilType": "粘性土",
                        "layerName": "粉质粘土层",
                        "thickness": 3.5,
                        "elevation": -2.5,
                        "density": 19.5,
                        "compressionModulus": 12.0,
                        "cohesion": 25.0,
                        "frictionAngle": 18.0,
                        "m": 0.35,
                        "fak": 150.0,
                        "etaB": 1.0,
                        "etaD": 1.2,
                        "zetaA": 1.0,
                        "poissonRatio": 0.25
                    }
                ],
                "designParameters": {
                    "importanceFactor": 1.1,
                    "safetyLevel": "一级",
                    "connectionType": "法兰连接",
                    "turbineCapacity": 3.0,
                    "hubHeight": 120.0,
                    "coverSoilDensity": 18.0,
                    "waterDepth": 2.5
                },
                "allowedDetachmentArea": {
                    "normal": 0.0,
                    "extreme": 0.25
                }
            }
        }

