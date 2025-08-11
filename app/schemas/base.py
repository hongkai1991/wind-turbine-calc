"""
基础数据模型模块
包含通用枚举、基础类型和共用的数据模型
"""
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum
from datetime import datetime


class SoilType(str, Enum):
    """土壤类型枚举"""
    CLAY = "粘土"
    SAND = "砂土"
    ROCK = "岩石"
    MIXED = "混合土"


class LoadCase(str, Enum):
    """工况枚举"""
    NORMAL = "正常工况"
    EXTREME = "极端工况"
    FREQUENT_EARTHQUAKE = "多遇地震工况"
    RARE_EARTHQUAKE = "罕遇地震工况"
    FATIGUE_UPPER = "疲劳工况上限"
    FATIGUE_LOWER = "疲劳工况下限"
    BASIC_COMBINATION_UNFAVORABLE = "基本组合(恒荷载对结构不利)"
    BASIC_COMBINATION_FAVORABLE = "基本组合(恒荷载对结构有利)"


class BasicInfo(BaseModel):
    """基础信息"""
    project_name: str = Field(..., description="项目名称")
    design_unit: str = Field(..., description="设计单位")
    calculation_date: datetime = Field(default_factory=datetime.now, description="计算日期")
    
    class Config:
        json_schema_extra = {
            "example": {
                "project_name": "某风电场风机基础",
                "design_unit": "某某设计院",
                "calculation_date": "2024-01-15T10:30:00"
            }
        }


class AntiPunchingSingleConditionResult(BaseModel):
    """单工况抗冲切验算结果"""
    condition_type: str = Field(..., description="工况类型")
    punching_force: float = Field(..., description="冲切力F(kN)")
    punching_capacity: float = Field(..., description="抗冲切承载力Fr(kN)")
    gamma_0_F: float = Field(..., description="γ0F(kN)")
    gamma_0: float = Field(..., description="重要性系数γ0")
    is_compliant: bool = Field(..., description="是否满足规范要求")
    check_details: str = Field(..., description="检查详情")

    class Config:
        json_schema_extra = {
            "example": {
                "condition_type": "正常工况",
                "punching_force": 12500.0,
                "punching_capacity": 18000.0,
                "gamma_0_F": 13750.0,
                "gamma_0": 1.1,
                "is_compliant": True,
                "check_details": "γ_0 F=1.1×12500.0=13750.0kN≤18000.0kN， 满足《陆上风电场工程风电机组基础设计规范》 7.2.8条规定。"
            }
        }


class PunchingCapacity(BaseModel):
    """抗冲切承载力计算明细对象"""
    h0: float = Field(..., description="有效截面高度(mm)")
    bhp: float = Field(..., description="高度影响系数Bhp")
    bt: float = Field(..., description="冲切破坏椎体上截面周长Bt(m)")
    bb: float = Field(..., description="冲切破坏椎体下截面周长Bb(m)")
    punching_capacity: float = Field(..., description="抗冲切承载力Fr(kN)")

    class Config:
        json_schema_extra = {
            "example": {
                "h0": 2000.0,
                "bhp": 0.9,
                "bt": 62.83,
                "bb": 188.50,
                "punching_capacity": 185000.0
            }
        }


class AntiPunchingAnalysisResult(BaseModel):
    """基础抗冲切验算结果"""
    # 为了在序列化后位于第2位，将overall_compliance置于首位
    overall_compliance: bool = Field(..., description="整体是否满足")

    # 抗冲切承载力对象
    punching_capacity: PunchingCapacity = Field(..., description="抗冲切承载力计算明细对象")
    
    # 各工况验算结果
    normal_condition: AntiPunchingSingleConditionResult = Field(..., description="正常工况抗冲切验算结果")
    extreme_condition: AntiPunchingSingleConditionResult = Field(..., description="极端工况抗冲切验算结果")
    frequent_seismic_condition: AntiPunchingSingleConditionResult = Field(..., description="多遇地震工况抗冲切验算结果")
    rare_seismic_condition: AntiPunchingSingleConditionResult = Field(..., description="罕遇地震工况抗冲切验算结果")
    
    class Config:
        json_schema_extra = {
            "example": {
                "overall_compliance": True,
                "punching_capacity": {
                    "h0": 2000.0,
                    "bhp": 0.9,
                    "bt": 62.83,
                    "bb": 188.50,
                    "punching_capacity": 185000.0
                },
                "normal_condition": {
                    "condition_type": "正常工况",
                    "punching_force": 125000.0,
                    "punching_capacity": 185000.0,
                    "gamma_0_F": 137500.0,
                    "gamma_0": 1.1,
                    "is_compliant": True,
                    "check_details": "γ_0 F=1.1×12500.0=13750.0kN≤18500.0kN， 满足《陆上风电场工程风电机组基础设计规范》 7.2.8条规定。"
                },
                "extreme_condition": {
                    "condition_type": "极端工况",
                    "punching_force": 140000.0,
                    "punching_capacity": 185000.0,
                    "gamma_0_F": 154000.0,
                    "gamma_0": 1.1,
                    "is_compliant": True,
                    "check_details": "γ_0 F=1.1×14000.0=15400.0kN≤18500.0kN， 满足《陆上风电场工程风电机组基础设计规范》 7.2.8条规定。"
                },
                "frequent_seismic_condition": {
                    "condition_type": "多遇地震工况",
                    "punching_force": 115000.0,
                    "punching_capacity": 185000.0,
                    "gamma_0_F": 126500.0,
                    "gamma_0": 1.1,
                    "is_compliant": True,
                    "check_details": "γ_0 F=1.1×11500.0=12650.0kN≤18500.0kN， 满足《陆上风电场工程风电机组基础设计规范》 7.2.8条规定。"
                },
                "rare_seismic_condition": {
                    "condition_type": "罕遇地震工况",
                    "punching_force": 165000.0,
                    "punching_capacity": 185000.0,
                    "gamma_0_F": 181500.0,
                    "gamma_0": 1.1,
                    "is_compliant": True,
                    "check_details": "γ_0 F=1.1×16500.0=18150.0kN≤18500.0kN， 满足《陆上风电场工程风电机组基础设计规范》 7.2.8条规定。"
                }
            }
        }


class StiffnessSingleResult(BaseModel):
    """单项刚度验算结果"""
    stiffness_type: str = Field(..., description="刚度类型(旋转/水平)")
    calculated_stiffness: float = Field(..., description="计算得到的刚度值")
    required_stiffness: float = Field(..., description="要求的刚度值")
    stiffness_unit: str = Field(..., description="刚度单位")
    is_compliant: bool = Field(..., description="是否满足刚度要求")
    check_details: str = Field(..., description="检查详情")

    class Config:
        json_schema_extra = {
            "example": {
                "stiffness_type": "旋转动态刚度",
                "calculated_stiffness": 3.072e11,
                "required_stiffness": 1.0e11,
                "stiffness_unit": "N·m/rad",
                "is_compliant": True,
                "check_details": "计算的动态旋转刚度：3.072E+11 ≥ 1.0E+11，满足刚度要求。"
            }
        }