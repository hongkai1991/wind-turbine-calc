"""
荷载计算相关数据模型模块
包含风机荷载、塔筒信息和荷载计算请求响应
"""
from __future__ import annotations
from pydantic import BaseModel, Field
from typing import List, Optional
from .base import SoilType


class WindTurbineInfo(BaseModel):
    """风机信息"""
    weight_fj: float = Field(..., alias="weightFJ", description="风机重量(kN)")
    elevation_fj: float = Field(..., alias="elevationFJ", description="风机标高(m)")
    top_height: float = Field(..., alias="topHeight", description="塔筒顶部高度(m)")
    damp: float = Field(default=0.0025, description="阻尼比")
    damp_h: float = Field(..., alias="dampH", description="阻尼系数")
    seismic_intensity_value: float = Field(..., alias="seismicIntensityValue", description="地震烈度值")
    seismic_group_value: float = Field(..., alias="seismicGroupValue", description="地震分组值")
    soil_type_value: float = Field(..., alias="soilTypeValue", description="土壤类型值")

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "weightFJ": 297.13,
                "elevationFJ": 140.0,
                "topHeight": 500,
                "damp": 0.0025,
                "dampH": 0.05,
                "seismicIntensityValue": 7.0,
                "seismicGroupValue": 1.0,
                "soilTypeValue": 2.0
            }
        }


class TowerDrum(BaseModel):
    """塔筒段信息"""
    length: float = Field(..., alias="length", description="长度(m)")
    bottom_outer_diameter: float = Field(..., alias="bottomOuterDiameter", description="底部外径(m)")
    top_outer_diameter: float = Field(..., alias="topOuterDiameter", description="顶部外径(m)")
    wall_thickness: float = Field(..., alias="wallThickness", description="壁厚(m)")
    material_name: str = Field(..., alias="materialName", description="材料名称")

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "length": 20.0,
                "bottomOuterDiameter": 5.36,
                "topOuterDiameter": 5.36,
                "wallThickness": 0.03,
                "materialName": "Q355"
            }
        }


class TurbineLoadCondition(BaseModel):
    """塔筒底部风机荷载工况"""
    Fr: float = Field(..., description="x轴向荷载(kN)")
    Fv: float = Field(..., description="y轴向荷载(kN)")
    Fz: float = Field(..., description="z轴向荷载(kN)")
    Mx: float = Field(..., description="x轴向弯矩(kN·m)")
    My: float = Field(..., description="y轴向弯矩(kN·m)")
    Mz: float = Field(..., description="z轴向弯矩(kN·m)")

    class Config:
        json_schema_extra = {
            "example": {
                "Fr": 1500.0,
                "Fv": 1623.0,
                "Fz": 2970.0,
                "Mx": 230746.8,
                "My": 150000.0,
                "Mz": 19253.415
            }
        }


class TurbineLoadConditions(BaseModel):
    """塔筒底部风机荷载四种工况"""
    normal: TurbineLoadCondition = Field(..., description="正常工况")
    extreme: TurbineLoadCondition = Field(..., description="极端工况")
    frequentSeismic: TurbineLoadCondition = Field(..., description="多遇地震工况")
    rareSeismic: TurbineLoadCondition = Field(..., description="罕遇地震工况")
    fatigueUpper: TurbineLoadCondition = Field(..., description="疲劳工况上限")
    fatigueLower: TurbineLoadCondition = Field(..., description="疲劳工况下限")

    class Config:
        json_schema_extra = {
            "example": {
                "normal": {
                    "Fr": 1500.0,
                    "Fv": 1623.0,
                    "Fz": 2970.0,
                    "Mx": 230746.8,
                    "My": 150000.0,
                    "Mz": 19253.415
                },
                "extreme": {
                    "Fr": 2200.0,
                    "Fv": 2400.0,
                    "Fz": 3200.0,
                    "Mx": 350000.0,
                    "My": 220000.0,
                    "Mz": 28000.0
                },
                "frequentSeismic": {
                    "Fr": 1300.0,
                    "Fv": 1400.0,
                    "Fz": 2900.0,
                    "Mx": 200000.0,
                    "My": 130000.0,
                    "Mz": 17000.0
                },
                "rareSeismic": {
                    "Fr": 2800.0,
                    "Fv": 3000.0,
                    "Fz": 3500.0,
                    "Mx": 420000.0,
                    "My": 280000.0,
                    "Mz": 35000.0
                },
                "fatigueUpper": {
                    "Fr": 1800.0,
                    "Fv": 1900.0,
                    "Fz": 3100.0,
                    "Mx": 280000.0,
                    "My": 180000.0,
                    "Mz": 25000.0
                },
                "fatigueLower": {
                    "Fr": 1200.0,
                    "Fv": 1300.0,
                    "Fz": 2800.0,
                    "Mx": 180000.0,
                    "My": 120000.0,
                    "Mz": 15000.0
                }
            }
        }


class TowerBaseLoadRequest(BaseModel):
    """塔筒底部荷载计算请求"""
    wind_turbine: WindTurbineInfo = Field(..., alias="windTurbine", description="风机信息")
    tower_drums: List[TowerDrum] = Field(..., alias="towerDrums", description="塔筒段信息列表")

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "windTurbine": {
                    "weightFJ": 297.13,
                    "elevationFJ": 140.0,
                    "topHeight": 500,
                    "damp": 0.0025,
                    "dampH": 0.05,
                    "seismicIntensityValue": 7.0,
                    "seismicGroupValue": 1.0,
                    "soilTypeValue": 2.0
                },
                "towerDrums": [
                    {
                        "length": 20.0,
                        "bottomOuterDiameter": 5.36,
                        "topOuterDiameter": 5.36,
                        "wallThickness": 0.03,
                        "materialName": "Q355"
                    }
                ]
            }
        }


class TowerBaseLoadResponse(BaseModel):
    """塔筒底部荷载计算响应"""
    is_success: bool = Field(..., alias="isSuccess", description="计算是否成功")
    error_message: Optional[str] = Field(None, alias="errorMessage", description="错误信息")
    max_vibration_period: float = Field(..., alias="maxVibrationPeriod", description="最大振动周期(s)")
    vibration_periods: List[float] = Field(..., alias="vibrationPeriods", description="振动周期列表(s)")
    horizontal_shear_forces: List[float] = Field(..., alias="horizontalShearForces", description="水平剪力列表(kN)")
    vertical_shear_forces: List[float] = Field(..., alias="verticalShearForces", description="竖向剪力列表(kN)")
    overturn_moments: List[float] = Field(..., alias="overturnMoments", description="倾覆力矩列表(kN·m)")
    tower_drum_validation_message: str = Field(..., alias="towerDrumValidationMessage", description="塔筒验证信息")
    wind_turbine_rod_length: int = Field(..., alias="windTurbineRodLength", description="风机杆长度")
    tower_drum_count: int = Field(..., alias="towerDrumCount", description="塔筒段数量")

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "isSuccess": True,
                "errorMessage": None,
                "maxVibrationPeriod": 6.872547661136967,
                "vibrationPeriods": [6.872547661136967, 0.8369951738116618],
                "horizontalShearForces": [68.57465408399453, 452.1592075371073],
                "verticalShearForces": [44.573525154596446, 293.90348489911975],
                "overturnMoments": [8057.231517386483, 53126.79249365395],
                "towerDrumValidationMessage": "塔筒验证通过",
                "windTurbineRodLength": 3,
                "towerDrumCount": 6
            }
        }


class LoadCalculationRequest(BaseModel):
    """荷载计算请求模式"""
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


class LoadResult(BaseModel):
    """荷载计算结果"""
    horizontal_force: float = Field(..., description="水平荷载(kN)")
    vertical_force: float = Field(..., description="垂直荷载(kN)")
    moment: float = Field(..., description="弯矩(kN·m)")
    success: bool = Field(..., description="计算是否成功")
    message: str = Field(..., description="计算消息")
    
    class Config:
        json_schema_extra = {
            "example": {
                "horizontal_force": 1500.0,
                "vertical_force": 3000.0,
                "moment": 180000.0,
                "success": True,
                "message": "荷载计算成功"
            }
        }


class ConditionCalculationResult(BaseModel):
    """单个工况计算结果对象"""
    load_case: str = Field(..., description="工况类型")
    combinations: CombinationsResult = Field(default_factory=lambda: CombinationsResult(), description="各种组合的计算结果")
    
    def add_combination(self, combination_name: str, combination_data: dict):
        """添加组合计算结果"""
        if combination_name == "standard":
            # 从字典创建 StandardCombinationResult 对象
            if isinstance(combination_data, dict):
                # 确保所有必需的字段存在，否则跳过
                try:
                    self.combinations.standard = StandardCombinationResult(**combination_data)
                except Exception:
                    # 如果无法创建对象，保持为 None
                    pass
            elif isinstance(combination_data, StandardCombinationResult):
                self.combinations.standard = combination_data
        elif combination_name == "basic_unfavorable":
            # 从字典创建 BasicCombinationResult 对象
            if isinstance(combination_data, dict):
                try:
                    self.combinations.basic_unfavorable = BasicCombinationResult(**combination_data)
                except Exception:
                    # 如果无法创建对象，保持为 None
                    pass
            elif isinstance(combination_data, BasicCombinationResult):
                self.combinations.basic_unfavorable = combination_data
        elif combination_name == "basic_favorable":
            # 从字典创建 BasicCombinationResult 对象
            if isinstance(combination_data, dict):
                try:
                    self.combinations.basic_favorable = BasicCombinationResult(**combination_data)
                except Exception:
                    # 如果无法创建对象，保持为 None
                    pass
            elif isinstance(combination_data, BasicCombinationResult):
                self.combinations.basic_favorable = combination_data
    
    def get_pj_values(self) -> dict:
        """获取所有组合的Pj值"""
        pj_values = {}
        
        # 检查标准组合
        if self.combinations.standard and hasattr(self.combinations.standard, 'Pj'):
            pj_values["standard"] = self.combinations.standard.Pj.value
        
        # 检查基本组合不利
        if self.combinations.basic_unfavorable and hasattr(self.combinations.basic_unfavorable, 'Pj'):
            pj_values["basic_unfavorable"] = self.combinations.basic_unfavorable.Pj.value
        
        # 检查基本组合有利
        if self.combinations.basic_favorable and hasattr(self.combinations.basic_favorable, 'Pj'):
            pj_values["basic_favorable"] = self.combinations.basic_favorable.Pj.value
            
        return pj_values
    
    def get_pjmax_values(self) -> dict:
        """获取所有组合的Pjmax值"""
        pjmax_values = {}
        
        # 检查标准组合 - 标准组合使用 Pkmax
        if self.combinations.standard:
            if hasattr(self.combinations.standard, 'Pkmax') and self.combinations.standard.Pkmax:
                pjmax_values["standard"] = self.combinations.standard.Pkmax.value
        
        # 检查基本组合不利 - 基本组合使用 Pmax
        if self.combinations.basic_unfavorable:
            if hasattr(self.combinations.basic_unfavorable, 'Pmax') and self.combinations.basic_unfavorable.Pmax:
                pjmax_values["basic_unfavorable"] = self.combinations.basic_unfavorable.Pmax.value
        
        # 检查基本组合有利 - 基本组合使用 Pmax
        if self.combinations.basic_favorable:
            if hasattr(self.combinations.basic_favorable, 'Pmax') and self.combinations.basic_favorable.Pmax:
                pjmax_values["basic_favorable"] = self.combinations.basic_favorable.Pmax.value
                
        return pjmax_values
    
    def to_dict(self) -> dict:
        """转换为字典格式（保持原有的数据结构）"""
        return {
            "load_case": self.load_case,
            "combinations": self.combinations.to_dict()
        }

    class Config:
        json_schema_extra = {
            "example": {
                "load_case": "正常工况",
                "combinations": {
                    "standard": {
                        "Frk": {"value": 1081.95, "unit": "kN", "description": "荷载标准值"},
                        "Nk_Gk": {"value": 52328.06, "unit": "kN", "description": "基础总恒载"},
                        "Mrk": {"value": 153884.99, "unit": "kN·m", "description": "水平力矩之和"},
                        "eccentricity": {"value": 2.94, "unit": "m", "description": "偏心距"},
                        "e_over_R": {"value": 0.245, "description": "偏心距与基础半径比值"},
                        "Pj": {"value": 100.20, "unit": "kPa", "description": "基础底面净反力"},
                        "pressure_type": "全截面受压"
                    },
                    "basic_unfavorable": {
                        "Fr": {"value": 1622.93, "unit": "kN", "description": "设计荷载值"},
                        "N_G": {"value": 68026.47, "unit": "kN", "description": "设计总恒载"},
                        "Mr": {"value": 230827.49, "unit": "kN·m", "description": "设计弯矩"},
                        "eccentricity": {"value": 3.39, "unit": "m", "description": "基本组合偏心距"},
                        "Pj": {"value": 147.82, "unit": "kPa", "description": "基础底面净反力"},
                        "pressure_type": "偏心受压"
                    }
                }
            }
        }


class ValueWithUnit(BaseModel):
    """带单位的数值对象"""
    value: float = Field(..., description="数值")
    unit: str = Field(..., description="单位")
    description: str = Field(..., description="描述")

    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "value": self.value,
            "unit": self.unit,
            "description": self.description
        }

    class Config:
        json_schema_extra = {
            "example": {
                "value": 1500.0,
                "unit": "kN",
                "description": "荷载标准值"
            }
        }


class SimpleValue(BaseModel):
    """简单数值对象（无单位）"""
    value: float = Field(..., description="数值")
    description: str = Field(..., description="描述")

    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "value": self.value,
            "description": self.description
        }

    class Config:
        json_schema_extra = {
            "example": {
                "value": 0.25,
                "description": "偏心距与基础半径比值"
            }
        }


class SimplePkResult(BaseModel):
    """简单基础底面净反力计算结果"""
    compressed_height: ValueWithUnit = Field(..., description="受压区域高度")
    compressed_area: ValueWithUnit = Field(..., description="受压区域面积")
    pk: ValueWithUnit = Field(..., description="简单基础底面净反力")
    tau: SimpleValue = Field(..., description="受压区域系数τ")
    xi: SimpleValue = Field(..., description="基础底面系数ξ")

    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "compressed_height": self.compressed_height.to_dict(),
            "compressed_area": self.compressed_area.to_dict(),
            "pk": self.pk.to_dict(),
            "tau": self.tau.to_dict(),
            "xi": self.xi.to_dict()
        }

    class Config:
        json_schema_extra = {
            "example": {
                "compressed_height": {"value": 24.0, "unit": "m", "description": "受压区域高度"},
                "compressed_area": {"value": 452.16, "unit": "m²", "description": "受压区域面积"},
                "pk": {"value": 115.67, "unit": "kPa", "description": "简单基础底面净反力"},
                "tau": {"value": 2.0, "description": "受压区域系数τ"},
                "xi": {"value": 1.571, "description": "基础底面系数ξ"}
            }
        }


class StandardCombinationResult(BaseModel):
    """标准组合计算结果"""
    Frk: ValueWithUnit = Field(..., description="荷载标准值")
    Nk_Gk: ValueWithUnit = Field(..., description="基础总恒载")
    Mrk: ValueWithUnit = Field(..., description="水平力矩之和")
    eccentricity: ValueWithUnit = Field(..., description="偏心距")
    e_over_R: SimpleValue = Field(..., description="偏心距与基础半径比值")
    Pkmax: Optional[ValueWithUnit] = Field(None, description="基础底面最大净反力")
    Pkmin: Optional[ValueWithUnit] = Field(None, description="基础底面最小净反力")
    simple_pk: SimplePkResult = Field(..., description="简单基础底面净反力计算结果")
    Pj: ValueWithUnit = Field(..., description="基础底面净反力")
    pressure_type: str = Field(..., description="压力类型")

    def to_dict(self) -> dict:
        """转换为字典格式（保持原有结构）"""
        result = {
            "Frk": self.Frk.to_dict(),
            "Nk_Gk": self.Nk_Gk.to_dict(),
            "Mrk": self.Mrk.to_dict(),
            "eccentricity": self.eccentricity.to_dict(),
            "e_over_R": self.e_over_R.to_dict(),
            "simple_pk": self.simple_pk.to_dict(),
            "Pj": self.Pj.to_dict(),
            "pressure_type": self.pressure_type
        }
        
        # 只有当 Pkmax 和 Pkmin 存在时才添加到结果中
        if self.Pkmax:
            result["Pkmax"] = self.Pkmax.to_dict()
        if self.Pkmin:
            result["Pkmin"] = self.Pkmin.to_dict()
            
        return result

    class Config:
        json_schema_extra = {
            "example": {
                "Frk": {"value": 1081.95, "unit": "kN", "description": "荷载标准值"},
                "Nk_Gk": {"value": 52328.06, "unit": "kN", "description": "基础总恒载"},
                "Mrk": {"value": 153884.99, "unit": "kN·m", "description": "水平力矩之和"},
                "eccentricity": {"value": 2.94, "unit": "m", "description": "偏心距"},
                "e_over_R": {"value": 0.245, "description": "偏心距与基础半径比值"},
                "Pkmax": {"value": 229.06, "unit": "kPa", "description": "基础底面最大净反力"},
                "Pkmin": {"value": 2.28, "unit": "kPa", "description": "基础底面最小净反力"},
                "simple_pk": {
                    "compressed_height": {"value": 24.0, "unit": "m", "description": "受压区域高度"},
                    "compressed_area": {"value": 452.16, "unit": "m²", "description": "受压区域面积"},
                    "pk": {"value": 115.67, "unit": "kPa", "description": "简单基础底面净反力"},
                    "tau": {"value": 2.0, "description": "受压区域系数τ"},
                    "xi": {"value": 1.571, "description": "基础底面系数ξ"}
                },
                "Pj": {"value": 100.20, "unit": "kPa", "description": "基础底面净反力"},
                "pressure_type": "全截面受压"
            }
        }


class BasicCombinationResult(BaseModel):
    """基本组合计算结果"""
    Fr: ValueWithUnit = Field(..., description="设计荷载值")
    N_G: ValueWithUnit = Field(..., description="设计总恒载")
    Mr: ValueWithUnit = Field(..., description="设计弯矩")
    eccentricity: ValueWithUnit = Field(..., description="基本组合偏心距")
    e_over_R: SimpleValue = Field(..., description="偏心距与基础半径比值")
    Pmax: Optional[ValueWithUnit] = Field(None, description="基本组合最大压力")
    Pmin: Optional[ValueWithUnit] = Field(None, description="基本组合最小压力")
    P: Optional[ValueWithUnit] = Field(None, description="简单基础底面净反力（平均压力）")
    simple_pk: SimplePkResult = Field(..., description="简单基础底面净反力计算结果")
    Pj: ValueWithUnit = Field(..., description="基础底面净反力")
    pressure_type: str = Field(..., description="压力类型")

    def to_dict(self) -> dict:
        """转换为字典格式（保持原有结构）"""
        result = {
            "Fr": self.Fr.to_dict(),
            "N_G": self.N_G.to_dict(),
            "Mr": self.Mr.to_dict(),
            "eccentricity": self.eccentricity.to_dict(),
            "e_over_R": self.e_over_R.to_dict(),
            "simple_pk": self.simple_pk.to_dict(),
            "Pj": self.Pj.to_dict(),
            "pressure_type": self.pressure_type
        }
        
        # 只有当 Pmax、Pmin 和 P 存在时才添加到结果中
        if self.Pmax:
            result["Pmax"] = self.Pmax.to_dict()
        if self.Pmin:
            result["Pmin"] = self.Pmin.to_dict()
        if self.P:
            result["P"] = self.P.to_dict()
            
        return result

    class Config:
        json_schema_extra = {
            "example": {
                "Fr": {"value": 1622.93, "unit": "kN", "description": "设计荷载值"},
                "N_G": {"value": 68026.47, "unit": "kN", "description": "设计总恒载"},
                "Mr": {"value": 230827.49, "unit": "kN·m", "description": "设计弯矩"},
                "eccentricity": {"value": 3.39, "unit": "m", "description": "基本组合偏心距"},
                "e_over_R": {"value": 0.283, "description": "偏心距与基础半径比值"},
                "Pmax": {"value": 320.99, "unit": "kPa", "description": "基本组合最大压力"},
                "P": {"value": 154.18, "unit": "kPa", "description": "简单基础底面净反力（平均压力）"},
                "simple_pk": {
                    "compressed_height": {"value": 22.55, "unit": "m", "description": "受压区域高度"},
                    "compressed_area": {"value": 441.21, "unit": "m²", "description": "受压区域面积"},
                    "pk": {"value": 115.67, "unit": "kPa", "description": "简单基础底面净反力"},
                    "tau": {"value": 1.88, "description": "受压区域系数τ"},
                    "xi": {"value": 1.47, "description": "基础底面系数ξ"}
                },
                "Pj": {"value": 147.82, "unit": "kPa", "description": "基础底面净反力"},
                "pressure_type": "偏心受压"
            }
        }


class CombinationsResult(BaseModel):
    """各种组合的计算结果对象"""
    standard: Optional[StandardCombinationResult] = Field(None, description="标准组合计算结果")
    basic_unfavorable: Optional[BasicCombinationResult] = Field(None, description="基本组合不利计算结果")
    basic_favorable: Optional[BasicCombinationResult] = Field(None, description="基本组合有利计算结果")

    def to_dict(self) -> dict:
        """转换为字典格式（保持原有的数据结构）"""
        result = {}
        if self.standard:
            result["standard"] = self.standard.to_dict()
        if self.basic_unfavorable:
            result["basic_unfavorable"] = self.basic_unfavorable.to_dict()
        if self.basic_favorable:
            result["basic_favorable"] = self.basic_favorable.to_dict()
        return result

    class Config:
        json_schema_extra = {
            "example": {
                "standard": {
                    "Frk": {"value": 1081.95, "unit": "kN", "description": "荷载标准值"},
                    "Nk_Gk": {"value": 52328.06, "unit": "kN", "description": "基础总恒载"},
                    "Mrk": {"value": 153884.99, "unit": "kN·m", "description": "水平力矩之和"},
                    "eccentricity": {"value": 2.94, "unit": "m", "description": "偏心距"},
                    "e_over_R": {"value": 0.245, "description": "偏心距与基础半径比值"},
                    "Pj": {"value": 100.20, "unit": "kPa", "description": "基础底面净反力"},
                    "pressure_type": "全截面受压"
                },
                "basic_unfavorable": {
                    "Fr": {"value": 1622.93, "unit": "kN", "description": "设计荷载值"},
                    "N_G": {"value": 68026.47, "unit": "kN", "description": "设计总恒载"},
                    "Mr": {"value": 230827.49, "unit": "kN·m", "description": "设计弯矩"},
                    "eccentricity": {"value": 3.39, "unit": "m", "description": "基本组合偏心距"},
                    "Pj": {"value": 147.82, "unit": "kPa", "description": "基础底面净反力"},
                    "pressure_type": "偏心受压"
                }
            }
        }


