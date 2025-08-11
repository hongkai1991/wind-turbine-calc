"""
稳定性分析数据模型模块
包含抗倾覆、抗滑移、抗剪强度等稳定性验算结果
"""
from pydantic import BaseModel, Field
from .base import AntiPunchingSingleConditionResult


class ShearStrengthSingleConditionResult(BaseModel):
    """单个工况的基础抗剪强度验算结果"""
    condition_type: str = Field(..., description="工况类型")
    shear_force: float = Field(..., description="剪力V(kN)")
    shear_capacity: float = Field(..., description="剪切承载力Vr(kN)")
    gamma_0_V: float = Field(..., description="γ0*V(kN)")
    gamma_0: float = Field(..., description="重要性系数γ0")
    pj: float = Field(..., description="基础底面净反力Pj(kPa)")
    s1: float = Field(..., description="S1面积(m²)")
    s2: float = Field(..., description="S2面积(m²)")
    is_compliant: bool = Field(..., description="是否满足规范要求")
    check_details: str = Field(..., description="检查详情")

    class Config:
        json_schema_extra = {
            "example": {
                "condition_type": "正常工况",
                "shear_force": 17719.304,
                "shear_capacity": 33364.69,
                "gamma_0_V": 19491.234,
                "gamma_0": 1.1,
                "pj": 125.5,
                "s1": 312.8,
                "s2": 171.6,
                "is_compliant": True,
                "check_details": "γ_0 V=1.1×17719.304=19491.234kN≤33364.69kN， 满足《陆上风电场工程风电机组基础设计规范》 7.2.9条规定。"
            }
        }


class ShearCapacity(BaseModel):
    """剪切承载力计算明细对象"""
    h0: float = Field(..., description="有效截面高度(mm)")
    shear_width: float = Field(..., description="受剪切截面宽度b(mm)")
    height_factor: float = Field(..., description="高度影响系数Bh")
    shear_area: float = Field(..., description="受剪切面积A0(mm²)")
    shear_capacity: float = Field(..., description="剪切承载力Vr(kN)")

    class Config:
        json_schema_extra = {
            "example": {
                "h0": 2000.0,
                "shear_width": 15000.0,
                "height_factor": 0.8,
                "shear_area": 30000000.0,
                "shear_capacity": 36500.0
            }
        }


class ShearStrengthAnalysisResult(BaseModel):
    """基础抗剪强度验算结果"""
    # 为了在序列化时整体合并后位于第2位，这里将overall_compliance置于首位
    overall_compliance: bool = Field(..., description="整体是否满足")

    # 剪切承载力对象
    shear_capacity: ShearCapacity = Field(..., description="剪切承载力计算明细对象")
    
    # 各工况验算结果
    normal_condition: ShearStrengthSingleConditionResult = Field(..., description="正常工况抗剪强度验算结果")
    extreme_condition: ShearStrengthSingleConditionResult = Field(..., description="极端工况抗剪强度验算结果")
    frequent_seismic_condition: ShearStrengthSingleConditionResult = Field(..., description="多遇地震工况抗剪强度验算结果")
    rare_seismic_condition: ShearStrengthSingleConditionResult = Field(..., description="罕遇地震工况抗剪强度验算结果")
    
    class Config:
        json_schema_extra = {
            "example": {
                "overall_compliance": True,
                "shear_capacity": {
                    "h0": 2000.0,
                    "shear_width": 15000.0,
                    "height_factor": 0.8,
                    "shear_area": 30000000.0,
                    "shear_capacity": 36500.0
                },
                "normal_condition": {
                    "condition_type": "正常工况",
                    "shear_force": 17719.304,
                    "shear_capacity": 33364.69,
                    "gamma_0_V": 19491.234,
                    "gamma_0": 1.1,
                    "pj": 125.5,
                    "s1": 312.8,
                    "s2": 171.6,
                    "is_compliant": True,
                    "check_details": "γ_0 V=1.1×17719.304=19491.234kN≤33364.69kN， 满足《陆上风电场工程风电机组基础设计规范》 7.2.9条规定。"
                },
                "extreme_condition": {
                    "condition_type": "极端工况",
                    "shear_force": 18500.0,
                    "shear_capacity": 33364.69,
                    "gamma_0_V": 20350.0,
                    "gamma_0": 1.1,
                    "pj": 131.0,
                    "s1": 312.8,
                    "s2": 171.6,
                    "is_compliant": True,
                    "check_details": "γ_0 V=1.1×18500.0=20350.0kN≤33364.69kN， 满足《陆上风电场工程风电机组基础设计规范》 7.2.9条规定。"
                },
                "frequent_seismic_condition": {
                    "condition_type": "多遇地震工况",
                    "shear_force": 16500.0,
                    "shear_capacity": 33364.69,
                    "gamma_0_V": 18150.0,
                    "gamma_0": 1.1,
                    "pj": 118.5,
                    "s1": 312.8,
                    "s2": 171.6,
                    "is_compliant": True,
                    "check_details": "γ_0 V=1.1×16500.0=18150.0kN≤33364.69kN， 满足《陆上风电场工程风电机组基础设计规范》 7.2.9条规定。"
                },
                "rare_seismic_condition": {
                    "condition_type": "罕遇地震工况",
                    "shear_force": 19800.0,
                    "shear_capacity": 33364.69,
                    "gamma_0_V": 21780.0,
                    "gamma_0": 1.1,
                    "pj": 142.0,
                    "s1": 312.8,
                    "s2": 171.6,
                    "is_compliant": True,
                    "check_details": "γ_0 V=1.1×19800.0=21780.0kN≤33364.69kN， 满足《陆上风电场工程风电机组基础设计规范》 7.2.9条规定。"
                }
            }
        }


class AntiOverturningSingleConditionResult(BaseModel):
    """单个工况的抗倾覆验算结果"""
    condition_type: str = Field(..., description="工况类型")
    overturning_moment: float = Field(..., description="倾覆力矩Ms(kN·m)")
    anti_overturning_moment: float = Field(..., description="抗倾覆力矩Mr(kN·m)")
    safety_factor: float = Field(..., description="安全系数Mr/Ms")
    gamma_0: float = Field(..., description="重要性系数γ0")
    gamma_d: float = Field(..., description="设计系数γd")
    required_safety_factor: float = Field(..., description="要求的安全系数γ0*γd")
    is_compliant: bool = Field(..., description="是否满足规范要求")
    check_details: str = Field(..., description="检查详情")

    class Config:
        json_schema_extra = {
            "example": {
                "condition_type": "正常工况",
                "overturning_moment": 153831.2,
                "anti_overturning_moment": 618829.659,
                "safety_factor": 4.023,
                "gamma_0": 1.1,
                "gamma_d": 1.6,
                "required_safety_factor": 1.76,
                "is_compliant": True,
                "check_details": "Mr/Ms = 618829.659/153831.2 = 4.023 ≥ γ0γd = 1.1 × 1.6 = 1.76，满足 《陆上风电场工程风电机组基础设计规范》 6.5.2 条规定。"
            }
        }


class AntiOverturningAnalysisResult(BaseModel):
    """抗倾覆验算分析结果"""
    overall_compliance: bool = Field(..., description="整体是否满足")
    normal_condition: AntiOverturningSingleConditionResult = Field(..., description="正常工况抗倾覆验算结果")
    extreme_condition: AntiOverturningSingleConditionResult = Field(..., description="极端工况抗倾覆验算结果")
    
    class Config:
        json_schema_extra = {
            "example": {
                "normal_condition": {
                    "condition_type": "正常工况",
                    "overturning_moment": 153831.2,
                    "anti_overturning_moment": 618829.659,
                    "safety_factor": 4.023,
                    "gamma_0": 1.1,
                    "gamma_d": 1.6,
                    "required_safety_factor": 1.76,
                    "is_compliant": True,
                    "check_details": "Mr/Ms = 618829.659/153831.2 = 4.023 ≥ γ0γd = 1.1 × 1.6 = 1.76，满足规范。"
                },
                "extreme_condition": {
                    "condition_type": "极端工况",
                    "overturning_moment": 185000.0,
                    "anti_overturning_moment": 618829.659,
                    "safety_factor": 3.345,
                    "gamma_0": 1.1,
                    "gamma_d": 1.6,
                    "required_safety_factor": 1.76,
                    "is_compliant": True,
                    "check_details": "Mr/Ms = 618829.659/185000.0 = 3.345 ≥ γ0γd = 1.1 × 1.6 = 1.76，满足规范。"
                }
            }
        }


class AntiSlidingSingleConditionResult(BaseModel):
    """单个工况的基础抗滑验算结果"""
    condition_type: str = Field(..., description="工况类型")
    sliding_force: float = Field(..., description="滑动力Fs(kN)")
    anti_sliding_force: float = Field(..., description="抗滑力Fr(kN)")
    gamma_0_Fs: float = Field(..., description="γ0*Fs(kN)")
    mu: float = Field(..., description="摩擦系数μ")
    gamma_0: float = Field(..., description="重要性系数γ0")
    is_compliant: bool = Field(..., description="是否满足规范要求")
    check_details: str = Field(..., description="检查详情")

    class Config:
        json_schema_extra = {
            "example": {
                "condition_type": "正常工况",
                "sliding_force": 1082.0,
                "anti_sliding_force": 15470.741,
                "gamma_0_Fs": 1190.2,
                "mu": 1.3,
                "gamma_0": 1.1,
                "is_compliant": True,
                "check_details": "抗滑力：Fr = (Nk + Gk)μ = 51569.138 × 1.3 = 15470.741kN，滑动力：Fs = 1082.0kN，γ0Fs = 1.1 × 1082.0 = 1190.2kN ≤ 1/γd Fr = 1/1.3 × 15470.741 = 11900.57kN，满足《陆上风电场工程风电机组基础设计规范》 6.5.2 条规定。"
            }
        }


class AntiSlidingAnalysisResult(BaseModel):
    """抗滑移验算分析结果"""
    overall_compliance: bool = Field(..., description="整体是否满足")
    normal_condition: AntiSlidingSingleConditionResult = Field(..., description="正常工况抗滑移验算结果")
    extreme_condition: AntiSlidingSingleConditionResult = Field(..., description="极端工况抗滑移验算结果")
    
    class Config:
        json_schema_extra = {
            "example": {
                "normal_condition": {
                    "condition_type": "正常工况",
                    "sliding_force": 1082.0,
                    "anti_sliding_force": 15470.741,
                    "gamma_0_Fs": 1190.2,
                    "mu": 1.3,
                    "gamma_0": 1.1,
                    "is_compliant": True,
                    "check_details": "抗滑力满足要求"
                },
                "extreme_condition": {
                    "condition_type": "极端工况",
                    "sliding_force": 1450.0,
                    "anti_sliding_force": 15470.741,
                    "gamma_0_Fs": 1595.0,
                    "mu": 1.3,
                    "gamma_0": 1.1,
                    "is_compliant": True,
                    "check_details": "抗滑力满足要求"
                }
            }
        }

