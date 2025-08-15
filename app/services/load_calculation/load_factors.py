"""
荷载分项系数模块

该模块定义了荷载计算中使用的各种分项系数。
"""

from app.utils.logger import get_logger

logger = get_logger(__name__)


class LoadFactors:
    """荷载分项系数（固定值）"""
    
    def __init__(self):
        # 荷载分项系数 - 固定值，不依赖工况
        self.dead_load_favorable = 1.0      # 恒载分项系数(有利)
        self.dead_load_unfavorable = 1.3    # 恒载分项系数(不利)
        self.live_load_factor = 1.5         # 活荷载分项系数
        self.seismic_vertical = 0.5        # 地震荷载分项系数(竖向)
        self.seismic_horizontal = 1.3       # 地震荷载分项系数(水平)
        self.prestress_favorable = 1.0     # 预应力组合系数(有利)
        self.prestress_unfavorable = 1.2   # 预应力组合系数(不利)
        self.horizontal_seismic_factor = 1.0  # 水平地震增大系数 (50m以内) 平地取1.0 (100m以内) 丘陵取1.1 (200m以上) 山地取1.2
