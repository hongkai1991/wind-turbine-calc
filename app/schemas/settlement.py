"""
沉降分析数据模型模块
包含沉降计算结果和相关参数
"""
from pydantic import BaseModel, Field
from typing import Dict, Optional, Any, List


class SettlementLayerDetail(BaseModel):
    """沉降计算分层详情"""
    layer: int = Field(..., description="层号")
    zi: float = Field(..., description="距基础底面的距离(m)")
    absolute_depth: float = Field(..., description="绝对深度(m)")
    esi: float = Field(..., description="该层压缩模量(MPa)")
    alpha_i: float = Field(..., description="应力系数")
    delta_term: float = Field(..., description="应力分布项")
    current_es: float = Field(..., description="当前等效压缩模量(MPa)")
    current_psi_s: float = Field(..., description="当前ψs系数")
    delta_s: float = Field(..., description="该层沉降量(mm)")
    cumulative_s: float = Field(..., description="累积沉降(mm)")
    settlement_ratio: float = Field(..., description="沉降比值")
    
    class Config:
        json_schema_extra = {
            "example": {
                "layer": 1,
                "zi": 0.8,
                "absolute_depth": 3.3,
                "esi": 12.5,
                "alpha_i": 0.923,
                "delta_term": 0.738,
                "current_es": 12.5,
                "current_psi_s": 1.0,
                "delta_s": 0.735,
                "cumulative_s": 0.735,
                "settlement_ratio": 1.0
            }
        }


class EsCalculationLayerInfo(BaseModel):
    """Es计算过程层详情（用于综合接口）"""
    zi_m: float = Field(..., description="距基础底面距离Zi(m)")
    esi_mpa: float = Field(..., description="该层压缩模量Esi(MPa)")
    alpha_i: float = Field(..., description="应力系数ᾱi")
    es_mpa: float = Field(..., description="等效压缩模量Es(MPa)")
    delta_s_mm: float = Field(..., description="该层沉降量ΔSi(mm)")
    si_mm: float = Field(..., description="累积沉降Si(mm)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "zi_m": 0.8,
                "esi_mpa": 12.5,
                "alpha_i": 0.923,
                "es_mpa": 12.5,
                "delta_s_mm": 0.735,
                "si_mm": 0.735
            }
        }


class ConditionAnalysis(BaseModel):
    """单个工况的汇总结果（直接包含两类综合结果）"""
    comprehensive_settlement_analysis: Dict[str, Any] = Field(..., description="沉降验算综合结果")
    comprehensive_inclination_analysis: Dict[str, Any] = Field(..., description="倾斜验算综合结果")


class SettlementAnalysisResult(BaseModel):
    """简化的地基变形验算结果模型"""
    calculation_type: str = Field(..., description="计算类型")
    overall_compliance: bool = Field(..., description="整体是否满足要求")
    normal_condition: Optional[ConditionAnalysis] = Field(None, description="正常工况结果")
    extreme_condition: Optional[ConditionAnalysis] = Field(None, description="极端工况结果")
    frequent_seismic_condition: Optional[ConditionAnalysis] = Field(None, description="多遇地震工况结果")

    class Config:
        json_schema_extra = {
            "example": {
                "calculation_type": "地基变形验算",
                "overall_compliance": True,
                "normal_condition": {
                    "comprehensive_settlement_analysis": {
                        "layer_thickness": 1.0,
                        "layer_count": 15,
                        "p0k": 98.7,
                        "fak": 150.0
                    },
                    "comprehensive_inclination_analysis": {
                        "layer_thickness": 1.0,
                        "layer_count": 15,
                        "p0kmax": 120.5,
                        "p0kmin": 76.9
                    }
                },
                "extreme_condition": {
                    "comprehensive_settlement_analysis": {
                        "layer_thickness": 1.0,
                        "layer_count": 15,
                        "p0k": 110.2,
                        "fak": 150.0
                    },
                    "comprehensive_inclination_analysis": {
                        "layer_thickness": 1.0,
                        "layer_count": 15,
                        "p0kmax": 140.0,
                        "p0kmin": 60.0
                    }
                },
                "frequent_seismic_condition": {
                    "comprehensive_settlement_analysis": {
                        "layer_thickness": 1.0,
                        "layer_count": 15,
                        "p0k": 105.0,
                        "fak": 150.0
                    },
                    "comprehensive_inclination_analysis": {
                        "layer_thickness": 1.0,
                        "layer_count": 15,
                        "p0kmax": 130.0,
                        "p0kmin": 65.0
                    }
                }
            }
        }




