"""
地基承载力分析数据模型模块
包含承载力验算结果和相关分析结果
"""
from pydantic import BaseModel, Field


 


class BearingCapacityCharacteristic(BaseModel):
    """地基承载力特征值对象"""
    fa: float = Field(..., description="地基承载力特征值fa(kPa)")
    fae: float = Field(..., description="地基抗震承载力特征值fae(kPa)")

    class Config:
        json_schema_extra = {
            "example": {
                "fa": 829.603,
                "fae": 1078.484
            }
        }


class BearingCapacityCondition(BaseModel):
    """单工况承载力校核对象"""
    pk: float = Field(..., description="基础底面净反力pk(kPa)")
    pkmax: float = Field(..., description="基础底面最大净反力pkmax(kPa)")
    check_details: str = Field(..., description="检查详情")

    class Config:
        json_schema_extra = {
            "example": {
                "pk": 113.993,
                "pkmax": 227.340,
                "check_details": "正常工况：pk ≤ fa 且 pkmax ≤ 1.2fa，满足规范。"
            }
        }


class BearingCapacityAnalysisResult(BaseModel):
    """简化后的地基承载力验算结果"""
    # 为了在序列化时位于calculation_type之后，这里将overall_compliance置于首位
    overall_compliance: bool = Field(..., description="整体是否满足(仅考虑正常+极端)")
    # 其后为特征值与两工况
    bearing_capacity_characteristic: BearingCapacityCharacteristic = Field(..., description="地基承载力特征值对象")
    normal_condition: BearingCapacityCondition = Field(..., description="正常工况验算结果")
    extreme_condition: BearingCapacityCondition = Field(..., description="极端工况验算结果")

    class Config:
        json_schema_extra = {
            "example": {
                "overall_compliance": True,
                "bearing_capacity_characteristic": {
                    "fa": 829.603,
                    "fae": 1078.484
                },
                "normal_condition": {
                    "pk": 113.993,
                    "pkmax": 227.340,
                    "check_details": "正常工况：pk ≤ fa 且 pkmax ≤ 1.2fa，满足规范。"
                },
                "extreme_condition": {
                    "pk": 121.031,
                    "pkmax": 257.660,
                    "check_details": "极端工况：pk ≤ fa 且 pkmax ≤ 1.2fa，满足规范。"
                }
            }
        }
