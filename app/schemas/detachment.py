"""
脱开面积分析数据模型模块
包含脱开面积验算结果和相关参数
"""
from pydantic import BaseModel, Field


class AllowedDetachmentArea(BaseModel):
    """允许脱开面积参数"""
    normal: float = Field(default=0.0, ge=0.0, le=1.0, alias="normal", description="正常工况允许脱开面积百分比(0.0-1.0)")
    extreme: float = Field(default=0.25, ge=0.0, le=1.0, alias="extreme", description="极端工况允许脱开面积百分比(0.0-1.0)")
    frequent_seismic: float = Field(default=0.15, ge=0.0, le=1.0, alias="frequentSeismic", description="多遇地震工况允许脱开面积百分比(0.0-1.0)")

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "normal": 0.0,
                "extreme": 0.25,
                "frequent_seismic": 0.25
            }
        }


class DetachmentAreaResult(BaseModel):
    """脱开面积验算结果"""
    condition_type: str = Field(..., description="工况类型")
    compressed_height: float = Field(..., description="受压区域高度(m)")
    foundation_area: float = Field(..., description="基础底面积(m²)")
    detachment_area: float = Field(..., description="脱开面积(m²)")
    detachment_ratio: float = Field(..., description="脱开面积百分比")
    allowed_ratio: float = Field(..., description="允许脱开面积百分比")
    is_compliant: bool = Field(..., description="是否满足规定")
    pressure_type: str = Field(..., description="受压类型(全截面受压/偏心受压)")
    check_details: str = Field(..., description="检查详情")
    
    class Config:
        json_schema_extra = {
            "example": {
                "condition_type": "正常工况",
                "compressed_height": 24.0,
                "foundation_area": 452.389,
                "detachment_area": 0.0,
                "detachment_ratio": 0.0,
                "allowed_ratio": 0.0,
                "is_compliant": True,
                "pressure_type": "全截面受压",
                "check_details": "脱开面积百分比:0.000/452.389=0.000≤0.00，满足《陆上风电场工程风电机组基础设计规范》 6.1.3条规定。"
            }
        }


class DetachmentAreaAnalysisResult(BaseModel):
    """脱开面积验算分析结果"""
    overall_compliance: bool = Field(..., description="整体是否符合规定")
    normal_condition: DetachmentAreaResult = Field(..., description="正常工况脱开面积验算结果")
    extreme_condition: DetachmentAreaResult = Field(..., description="极端工况脱开面积验算结果")
    frequent_seismic_condition: DetachmentAreaResult = Field(..., description="多遇地震工况脱开面积验算结果")

    class Config:
        json_schema_extra = {
            "example": {
                "normal_condition": {
                    "condition_type": "正常工况",
                    "compressed_height": 24.0,
                    "foundation_area": 452.389,
                    "detachment_area": 0.0,
                    "detachment_ratio": 0.0,
                    "allowed_ratio": 0.0,
                    "is_compliant": True,
                    "pressure_type": "全截面受压"
                },
                "extreme_condition": {
                    "condition_type": "极端工况",
                    "compressed_height": 21.422,
                    "foundation_area": 452.389,
                    "detachment_area": 26.142,
                    "detachment_ratio": 0.058,
                    "allowed_ratio": 0.25,
                    "is_compliant": True,
                    "pressure_type": "偏心受压"
                },
                "overall_compliance": True
            }
        }

