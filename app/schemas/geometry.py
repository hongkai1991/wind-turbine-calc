"""
几何验算数据模型模块
包含基础体型验算请求和结果
"""
from pydantic import BaseModel, Field
from .foundation import FoundationGeometry


class GeometryValidationRequest(BaseModel):
    """基础体型验算请求"""
    geometry: FoundationGeometry = Field(..., description="基础几何信息")
    
    class Config:
        json_schema_extra = {
            "example": {
                "geometry": {
                    "base_radius": 12.0,
                    "column_radius": 4.0,
                    "ground_height": 0.2,
                    "column_height": 1.5,
                    "frustum_height": 2.0,
                    "edge_height": 0.5,
                    "buried_depth": 2.0
                }
            }
        }


class GeometryValidationResult(BaseModel):
    """基础体型验算结果"""
    is_geometry_valid: bool = Field(..., description="基础几何尺寸是否合理")
    overall_dimension_ratio: float = Field(..., description="整体尺寸比值")
    
    # 坡度相关信息 - 符合规范的表示方式
    slope_horizontal_to_vertical: float = Field(..., description="坡度水平:垂直比例(规范表示)")
    slope_description: str = Field(..., description="坡度描述(如1:4.0)")
    is_slope_compliant: bool = Field(..., description="坡度是否符合规范要求(1:4)")
    
    validation_message: str = Field(..., description="验算说明")
    
    class Config:
        json_schema_extra = {
            "example": {
                "is_geometry_valid": True,
                "overall_dimension_ratio": 3.2,
                "slope_horizontal_to_vertical": 4.0,
                "slope_description": "1:4.00",
                "is_slope_compliant": True,
                "validation_message": "基础体型验算通过，几何尺寸合理，坡度1:4.00符合规范要求(不超过1:4)"
            }
        }
