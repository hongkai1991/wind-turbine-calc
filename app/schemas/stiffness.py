"""
刚度验算数据模型模块
包含刚度要求参数和刚度验算结果
"""
from pydantic import BaseModel, Field
from .base import StiffnessSingleResult


class StiffnessRequirements(BaseModel):
    """刚度要求参数"""
    required_rotational_stiffness: float = Field(..., gt=0, description="旋转动态刚度要求(N·m/rad)", alias="requiredRotationalStiffness")
    required_horizontal_stiffness: float = Field(..., gt=0, description="水平动态刚度要求(N/m)", alias="requiredHorizontalStiffness")
    
    def validate_parameters(self) -> bool:
        """验证参数有效性"""
        # 验证旋转刚度范围 (一般在1E8-1E15之间)
        if not (1e8 <= self.required_rotational_stiffness <= 1e15):
            return False
        
        # 验证水平刚度范围 (一般在1E6-1E12之间)
        if not (1e6 <= self.required_horizontal_stiffness <= 1e12):
            return False
        
        return True
    
    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "requiredRotationalStiffness": 100000000000.0,
                "requiredHorizontalStiffness": 1000000000.0
            }
        }


class StiffnessAnalysisResult(BaseModel):
    """刚度验算结果"""
    overall_compliance: bool = Field(..., description="整体是否满足刚度要求")
    rotational_stiffness: StiffnessSingleResult = Field(..., description="旋转动态刚度验算结果")
    horizontal_stiffness: StiffnessSingleResult = Field(..., description="水平动态刚度验算结果")

    class Config:
        json_schema_extra = {
            "example": {
                "rotational_stiffness": {
                    "stiffness_type": "旋转动态刚度",
                    "calculated_stiffness": 3.072e11,
                    "required_stiffness": 1.0e11,
                    "stiffness_unit": "N·m/rad",
                    "is_compliant": True,
                    "check_details": "计算的动态旋转刚度：3.072E+11 ≥ 1.0E+11，满足刚度要求。"
                },
                "horizontal_stiffness": {
                    "stiffness_type": "水平动态刚度",
                    "calculated_stiffness": 3.2e9,
                    "required_stiffness": 1.0e9,
                    "stiffness_unit": "N/m",
                    "is_compliant": True,
                    "check_details": "计算的水平动态刚度：3.2E+09 ≥ 1.0E+09，满足刚度要求。"
                },
                "overall_compliance": True
            }
        }
