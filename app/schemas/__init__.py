"""
数据模型模块
重新导出所有拆分后的数据模型，保持向后兼容性
"""

# 基础模型
from .base import (
    SoilType,
    LoadCase,
    BasicInfo,
    AntiPunchingSingleConditionResult,
    AntiPunchingAnalysisResult,
    StiffnessSingleResult
)

# 基础几何和材料
from .foundation import (
    FoundationGeometry,
    MaterialProperties,
    SoilLayer
)

# 荷载相关
from .load import (
    WindTurbineInfo,
    TowerDrum,
    TurbineLoadCondition,
    TurbineLoadConditions,
    TowerBaseLoadRequest,
    TowerBaseLoadResponse,
    LoadCalculationRequest,
    LoadResult
)

# 承载力分析
from .bearing_capacity import (
    BearingCapacityAnalysisResult
)

# 沉降分析
from .settlement import (
    SettlementLayerDetail,
    EsCalculationLayerInfo,
    ConditionAnalysis,
    SettlementAnalysisResult
)

# 刚度分析
from .stiffness import (
    StiffnessRequirements,
    StiffnessAnalysisResult
)

# 脱开面积分析
from .detachment import (
    AllowedDetachmentArea,
    DetachmentAreaResult,
    DetachmentAreaAnalysisResult
)

# 几何验算
from .geometry import (
    GeometryValidationRequest,
    GeometryValidationResult
)

# 自重计算
from .self_weight import (
    SelfWeightResult
)

# 稳定性分析
from .stability import (
    ShearStrengthSingleConditionResult,
    ShearCapacity,
    ShearStrengthAnalysisResult,
    AntiOverturningSingleConditionResult,
    AntiOverturningAnalysisResult,
    AntiSlidingSingleConditionResult,
    AntiSlidingAnalysisResult
)

# 综合计算
from .comprehensive import (
    DesignParameters,
    FoundationCalculationRequest,
    FoundationResult,
    StabilityResult,
    CalculationResponse,
    ComprehensiveCalculationRequest
)

# 为了保持向后兼容性，将所有模型导出到模块级别
__all__ = [
    # 基础模型
    'SoilType',
    'LoadCase', 
    'BasicInfo',
    'AntiPunchingSingleConditionResult',
    'AntiPunchingAnalysisResult',
    'StiffnessSingleResult',
    
    # 基础几何和材料
    'FoundationGeometry',
    'MaterialProperties',
    'SoilLayer',
    
    # 荷载相关
    'WindTurbineInfo',
    'TowerDrum',
    'TurbineLoadCondition',
    'TurbineLoadConditions',
    'TowerBaseLoadRequest',
    'TowerBaseLoadResponse',
    'LoadCalculationRequest',
    'LoadResult',
    
    # 承载力分析
    'BearingCapacityAnalysisResult',
    
    # 沉降分析
    'SettlementLayerDetail',
    'EsCalculationLayerInfo',
    'ConditionAnalysis',
    'SettlementAnalysisResult',
    
    # 刚度分析
    'StiffnessRequirements',
    'StiffnessAnalysisResult',
    
    # 脱开面积分析
    'AllowedDetachmentArea',
    'DetachmentAreaResult',
    'DetachmentAreaAnalysisResult',
    
    # 几何验算
    'GeometryValidationRequest',
    'GeometryValidationResult',
    
    # 自重计算
    'SelfWeightResult',
    
    # 稳定性分析
    'ShearStrengthSingleConditionResult',
    'ShearCapacity',
    'ShearStrengthAnalysisResult',
    'AntiOverturningSingleConditionResult',
    'AntiOverturningAnalysisResult',
    'AntiSlidingSingleConditionResult',
    'AntiSlidingAnalysisResult',
    
    # 综合计算
    'DesignParameters',
    'FoundationCalculationRequest', 
    'FoundationResult',
    'StabilityResult',
    'CalculationResponse',
    'ComprehensiveCalculationRequest'
]