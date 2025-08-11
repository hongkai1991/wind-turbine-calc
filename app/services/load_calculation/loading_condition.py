"""
荷载工况模块

该模块定义了塔筒底部风机荷载的工况条件。
"""

from app.schemas import LoadCase
from .load_factors import LoadFactors
from app.utils.logger import get_logger

logger = get_logger(__name__)


class LoadingCondition:
    """塔筒底部风机荷载"""
    
    def __init__(
        self,
        case_type: LoadCase,
        Fr: float = 0.0,                # x轴向荷载(kN)
        Fv: float = 0.0,                # y轴向荷载(kN)
        Fz: float = 0.0,                # z轴向荷载(kN)
        Mx: float = 0.0,                # x轴向弯矩(kN·m)
        My: float = 0.0,                # y轴向弯矩(kN·m)
        Mz: float = 0.0                 # z轴向弯矩(kN·m)
    ):
        self.case_type = case_type
        self.Fr = Fr
        self.Fv = Fv
        self.Fz = Fz
        self.Mx = Mx
        self.My = My
        self.Mz = Mz
    
    def apply_load_factors(self, load_factors: LoadFactors):
        """应用荷载分项系数到荷载工况"""
        # 根据工况类型选择合适的荷载分项系数
        if self.case_type == LoadCase.BASIC_COMBINATION_FAVORABLE:
            factor = load_factors.dead_load_favorable
        elif self.case_type == LoadCase.BASIC_COMBINATION_UNFAVORABLE:
            factor = load_factors.dead_load_unfavorable
        elif self.case_type in [LoadCase.FREQUENT_EARTHQUAKE, LoadCase.RARE_EARTHQUAKE]:
            # 地震工况使用地震荷载分项系数
            factor = load_factors.seismic_horizontal
        else:
            # 其他工况使用不利恒载分项系数
            factor = load_factors.dead_load_unfavorable
        
        # 应用分项系数
        self.Fr *= factor
        self.Fv *= factor
        self.Fz *= factor
        self.Mx *= factor
        self.My *= factor
        self.Mz *= factor
