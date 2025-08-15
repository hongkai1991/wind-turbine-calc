"""
自重计算数据模型模块
包含基础自重计算相关结果
"""
from pydantic import BaseModel, Field


class SelfWeightResult(BaseModel):
    """自重计算结果"""
    # 原有的6个结果
    foundation_volume: float = Field(..., description="混凝土体积V1(m³)")
    backfill_volume: float = Field(..., description="回填土体积V2(m³)")
    concrete_weight: float = Field(..., description="混凝土（基础）自重G1(kN)")
    backfill_weight: float = Field(..., description="回填土自重G2(kN)")
    buoyancy_weight: float = Field(default=0.0, description="浮力Gw(kN)")
    total_weight: float = Field(..., description="总重量Gk(kN) = 基础自重+回填土自重-浮力")
    
    class Config:
        json_schema_extra = {
            "example": {
                "foundation_volume": 450.2,
                "backfill_volume": 280.5,
                "concrete_weight": 11255.0,
                "backfill_weight": 5610.0,
                "buoyancy_weight": 0.0,
                "total_weight": 16865.0
            }
        }

