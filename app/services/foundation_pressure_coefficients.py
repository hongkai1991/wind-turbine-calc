"""
基础基底压力计算系数表
用于偏心荷载作用下圆形、环形基础基底零应力区的基底压力计算
"""
import math
from typing import Tuple, Optional
from app.utils.logger import get_logger

logger = get_logger(__name__)


class FoundationPressureCoefficients:
    """
    基础基底压力计算系数表
    
    根据《高耸结构设计标准》附录H表H.0.1
    在偏心荷载作用下，圆形、环形基础基底零应力区的基底压力计算系数
    """
    
    def __init__(self):
        """初始化系数表数据"""
        # e/r1 - 偏心距与基础外半径的比值
        self.e_over_r1_values = [
            0.25, 0.26, 0.27, 0.28, 0.29, 0.30, 0.31, 0.32, 0.33, 0.34,
            0.35, 0.36, 0.37, 0.38, 0.39, 0.40, 0.41, 0.42, 0.43, 0.44,
            0.45, 0.46, 0.47, 0.48, 0.49, 0.50, 0.51, 0.52, 0.53, 0.54,
            0.55, 0.56, 0.57, 0.58, 0.59, 0.60, 0.61, 0.62, 0.63, 0.64,
            0.65, 0.66, 0.67
        ]
        
        # r2/r1 - 基础内半径与外半径的比值（对于实心圆形基础，r2/r1 = 0.00）
        self.r2_over_r1_values = [
            0.00, 0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90
        ]
        
        # τ系数表 - 基底压力计算系数τ
        # 行对应e/r1，列对应r2/r1
        self.tau_coefficients = [
            [2.000, None, None, None, None, None, None, None, None, None],  # e/r1 = 0.25
            [1.960, None, None, None, None, None, None, None, None, None],  # e/r1 = 0.26
            [1.924, None, None, None, None, None, None, None, None, None],  # e/r1 = 0.27
            [1.889, None, None, None, None, None, None, None, None, None],  # e/r1 = 0.28
            [1.854, None, None, None, None, None, None, None, None, None],  # e/r1 = 0.29
            [1.820, None, None, None, None, None, None, None, None, None],  # e/r1 = 0.30
            [1.787, None, None, None, None, None, None, None, None, None],  # e/r1 = 0.31
            [1.755, 1.976, None, None, None, None, None, None, None, None],  # e/r1 = 0.32
            [1.723, 1.946, 1.987, None, None, None, None, None, None, None],  # e/r1 = 0.33
            [1.692, 1.917, 1.957, 2.000, None, None, None, None, None, None],  # e/r1 = 0.34
            [1.661, 1.888, 1.929, 1.971, None, None, None, None, None, None],  # e/r1 = 0.35
            [1.630, 1.860, 1.900, 1.943, 1.998, None, None, None, None, None],  # e/r1 = 0.36
            [1.601, 1.832, 1.873, 1.916, 1.961, 2.000, None, None, None, None],  # e/r1 = 0.37
            [1.571, 1.804, 1.846, 1.890, 1.934, 1.980, None, None, None, None],  # e/r1 = 0.38
            [1.541, 1.777, 1.819, 1.863, 1.908, 1.955, 2.000, None, None, None],  # e/r1 = 0.39
            [1.513, 1.750, 1.792, 1.837, 1.883, 1.929, 1.976, None, None, None],  # e/r1 = 0.40
            [1.484, 1.723, 1.766, 1.811, 1.857, 1.904, 1.952, 2.000, None, None],  # e/r1 = 0.41
            [1.455, 1.695, 1.739, 1.785, 1.831, 1.879, 1.928, 1.976, None, None],  # e/r1 = 0.42
            [1.427, 1.668, 1.712, 1.758, 1.806, 1.854, 1.903, 1.952, 2.000, None],  # e/r1 = 0.43
            [1.399, 1.640, 1.685, 1.732, 1.780, 1.829, 1.879, 1.929, 1.979, None],  # e/r1 = 0.44
            [1.371, 1.613, 1.658, 1.705, 1.754, 1.804, 1.855, 1.905, 1.955, 2.000],  # e/r1 = 0.45
            [1.343, 1.584, 1.630, 1.678, 1.727, 1.778, 1.830, 1.881, 1.933, 1.984],  # e/r1 = 0.46
            [1.316, 1.555, 1.601, 1.650, 1.700, 1.752, 1.804, 1.857, 1.910, 1.962],  # e/r1 = 0.47
            [1.288, 1.526, 1.572, 1.621, 1.672, 1.724, 1.778, 1.832, 1.886, 1.939],  # e/r1 = 0.48
            [1.261, 1.495, 1.541, 1.591, 1.642, 1.695, 1.750, 1.805, 1.861, 1.916],  # e/r1 = 0.49
            [1.234, 1.463, 1.510, 1.559, 1.611, 1.665, 1.721, 1.777, 1.834, 1.891],  # e/r1 = 0.50
            [1.208, 1.430, 1.477, 1.527, 1.580, 1.634, 1.690, 1.748, 1.806, 1.864],  # e/r1 = 0.51
            [1.181, 1.397, 1.444, 1.494, 1.547, 1.602, 1.659, 1.717, 1.776, 1.836],  # e/r1 = 0.52
            [None, 1.363, 1.410, 1.460, 1.513, 1.569, 1.627, 1.686, 1.746, 1.807],  # e/r1 = 0.53
            [None, 1.328, 1.375, 1.425, 1.479, 1.536, 1.594, 1.654, 1.715, 1.776],  # e/r1 = 0.54
            [None, 1.293, 1.340, 1.390, 1.444, 1.501, 1.560, 1.621, 1.683, 1.745],  # e/r1 = 0.55
            [None, 1.258, 1.304, 1.355, 1.409, 1.466, 1.526, 1.587, 1.650, 1.713],  # e/r1 = 0.56
            [None, None, 1.268, 1.318, 1.373, 1.430, 1.491, 1.553, 1.616, 1.680],  # e/r1 = 0.57
            [None, None, None, 1.282, 1.336, 1.394, 1.455, 1.518, 1.582, 1.647],  # e/r1 = 0.58
            [None, None, None, None, 1.299, 1.357, 1.418, 1.482, 1.547, 1.613],  # e/r1 = 0.59
            [None, None, None, None, 1.261, 1.320, 1.381, 1.445, 1.511, 1.578],  # e/r1 = 0.60
            [None, None, None, None, None, 1.282, 1.344, 1.408, 1.475, 1.542],  # e/r1 = 0.61
            [None, None, None, None, None, None, 1.306, 1.371, 1.438, 1.506],  # e/r1 = 0.62
            [None, None, None, None, None, None, None, 1.333, 1.400, 1.469],  # e/r1 = 0.63
            [None, None, None, None, None, None, None, 1.294, 1.362, 1.432],  # e/r1 = 0.64
            [None, None, None, None, None, None, None, None, 1.324, 1.394],  # e/r1 = 0.65
            [None, None, None, None, None, None, None, None, None, 1.356],  # e/r1 = 0.66
            [None, None, None, None, None, None, None, None, None, 1.317],  # e/r1 = 0.67
        ]
        
        # ξ系数表 - 基底压力计算系数ξ
        # 行对应e/r1，列对应r2/r1
        self.xi_coefficients = [
            [1.571, None, None, None, None, None, None, None, None, None],  # e/r1 = 0.25
            [1.539, None, None, None, None, None, None, None, None, None],  # e/r1 = 0.26
            [1.509, None, None, None, None, None, None, None, None, None],  # e/r1 = 0.27
            [1.480, None, None, None, None, None, None, None, None, None],  # e/r1 = 0.28
            [1.450, None, None, None, None, None, None, None, None, None],  # e/r1 = 0.29
            [1.421, None, None, None, None, None, None, None, None, None],  # e/r1 = 0.30
            [1.392, None, None, None, None, None, None, None, None, None],  # e/r1 = 0.31
            [1.364, 1.164, None, None, None, None, None, None, None, None],  # e/r1 = 0.32
            [1.335, 1.146, 1.088, None, None, None, None, None, None, None],  # e/r1 = 0.33
            [1.307, 1.128, 1.072, 1.005, None, None, None, None, None, None],  # e/r1 = 0.34
            [1.279, 1.110, 1.056, 0.991, None, None, None, None, None, None],  # e/r1 = 0.35
            [1.252, 1.092, 1.039, 0.976, 0.902, None, None, None, None, None],  # e/r1 = 0.36
            [1.224, 1.075, 1.024, 0.962, 0.889, 0.801, None, None, None, None],  # e/r1 = 0.37
            [1.197, 1.057, 1.008, 0.948, 0.877, 0.793, None, None, None, None],  # e/r1 = 0.38
            [1.170, 1.040, 0.992, 0.934, 0.865, 0.783, 0.687, None, None, None],  # e/r1 = 0.39
            [1.143, 1.023, 0.977, 0.920, 0.852, 0.772, 0.679, None, None, None],  # e/r1 = 0.40
            [1.116, 1.006, 0.961, 0.907, 0.840, 0.762, 0.670, 0.565, None, None],  # e/r1 = 0.41
            [1.090, 0.988, 0.946, 0.893, 0.828, 0.752, 0.662, 0.559, None, None],  # e/r1 = 0.42
            [1.063, 0.971, 0.930, 0.879, 0.816, 0.741, 0.653, 0.552, 0.436, None],  # e/r1 = 0.43
            [1.037, 0.954, 0.915, 0.865, 0.804, 0.731, 0.645, 0.545, 0.431, None],  # e/r1 = 0.44
            [1.010, 0.937, 0.900, 0.852, 0.792, 0.721, 0.637, 0.538, 0.426, 0.299],  # e/r1 = 0.45
            [0.984, 0.920, 0.884, 0.838, 0.780, 0.711, 0.628, 0.532, 0.421, 0.296],  # e/r1 = 0.46
            [0.959, 0.902, 0.868, 0.824, 0.768, 0.700, 0.620, 0.525, 0.416, 0.293],  # e/r1 = 0.47
            [0.933, 0.884, 0.852, 0.810, 0.756, 0.690, 0.611, 0.518, 0.411, 0.290],  # e/r1 = 0.48
            [0.908, 0.866, 0.836, 0.795, 0.743, 0.679, 0.602, 0.511, 0.406, 0.286],  # e/r1 = 0.49
            [0.883, 0.848, 0.819, 0.780, 0.730, 0.668, 0.593, 0.504, 0.401, 0.283],  # e/r1 = 0.50
            [0.858, 0.829, 0.802, 0.765, 0.717, 0.657, 0.584, 0.497, 0.396, 0.279],  # e/r1 = 0.51
            [0.833, 0.810, 0.785, 0.750, 0.704, 0.646, 0.575, 0.490, 0.390, 0.276],  # e/r1 = 0.52
            [None, 0.791, 0.768, 0.735, 0.691, 0.635, 0.565, 0.482, 0.385, 0.272],  # e/r1 = 0.53
            [None, 0.772, 0.750, 0.719, 0.677, 0.623, 0.556, 0.475, 0.379, 0.269],  # e/r1 = 0.54
            [None, 0.752, 0.732, 0.703, 0.663, 0.611, 0.546, 0.467, 0.374, 0.265],  # e/r1 = 0.55
            [None, 0.732, 0.714, 0.687, 0.649, 0.599, 0.536, 0.459, 0.368, 0.261],  # e/r1 = 0.56
            [None, None, 0.696, 0.670, 0.635, 0.587, 0.526, 0.452, 0.362, 0.257],  # e/r1 = 0.57
            [None, None, None, 0.654, 0.620, 0.575, 0.516, 0.444, 0.356, 0.254],  # e/r1 = 0.58
            [None, None, None, None, 0.605, 0.562, 0.506, 0.436, 0.350, 0.250],  # e/r1 = 0.59
            [None, None, None, None, 0.591, 0.550, 0.496, 0.427, 0.344, 0.246],  # e/r1 = 0.60
            [None, None, None, None, None, 0.537, 0.485, 0.419, 0.338, 0.242],  # e/r1 = 0.61
            [None, None, None, None, None, None, 0.474, 0.411, 0.332, 0.238],  # e/r1 = 0.62
            [None, None, None, None, None, None, None, 0.402, 0.326, 0.234],  # e/r1 = 0.63
            [None, None, None, None, None, None, None, 0.393, 0.319, 0.230],  # e/r1 = 0.64
            [None, None, None, None, None, None, None, None, 0.313, 0.225],  # e/r1 = 0.65
            [None, None, None, None, None, None, None, None, None, 0.221],  # e/r1 = 0.66
            [None, None, None, None, None, None, None, None, None, 0.217],  # e/r1 = 0.67
        ]
    
    def get_coefficients_by_interpolation(self, e_over_r1: float, r2_over_r1: float = 0.0) -> Tuple[float, float]:
        """
        通过插值计算获取τ和ξ系数
        
        Args:
            e_over_r1: 偏心距与基础外半径的比值
            r2_over_r1: 基础内半径与外半径的比值，默认0.0（实心圆形基础）
            
        Returns:
            Tuple[float, float]: (τ系数, ξ系数)
            
        Raises:
            ValueError: 当参数超出表格范围时
        """
        # 参数范围检查
        if e_over_r1 < 0.25:
            logger.warning(f"e/r1 = {e_over_r1} 小于表格最小值0.25，使用边界值")
            e_over_r1 = 0.25
        elif e_over_r1 > 0.67:
            logger.warning(f"e/r1 = {e_over_r1} 大于表格最大值0.67，使用边界值")
            e_over_r1 = 0.67
            
        if r2_over_r1 < 0.0:
            logger.warning(f"r2/r1 = {r2_over_r1} 小于0，使用0.0")
            r2_over_r1 = 0.0
        elif r2_over_r1 > 0.90:
            logger.warning(f"r2/r1 = {r2_over_r1} 大于表格最大值0.90，使用边界值")
            r2_over_r1 = 0.90
        
        # 对于实心圆形基础（r2/r1 = 0.0），直接进行e/r1的插值
        if r2_over_r1 == 0.0:
            tau = self._interpolate_e_over_r1(e_over_r1, self.tau_coefficients, column_index=0)
            xi = self._interpolate_e_over_r1(e_over_r1, self.xi_coefficients, column_index=0)
            return tau, xi
        
        # 对于环形基础，需要进行二维插值
        # 这里简化处理，先实现实心圆形基础的情况
        # 后续可以扩展为完整的二维插值
        logger.warning("当前版本仅支持实心圆形基础(r2/r1=0.0)，环形基础功能待扩展")
        tau = self._interpolate_e_over_r1(e_over_r1, self.tau_coefficients, column_index=0)
        xi = self._interpolate_e_over_r1(e_over_r1, self.xi_coefficients, column_index=0)
        return tau, xi
    
    def _interpolate_e_over_r1(self, e_over_r1: float, coefficient_table: list, column_index: int) -> float:
        """
        对e/r1进行线性插值
        
        Args:
            e_over_r1: 偏心距与基础外半径的比值
            coefficient_table: 系数表
            column_index: 列索引（对应不同的r2/r1值）
            
        Returns:
            float: 插值得到的系数
            
        Raises:
            ValueError: 当所需的系数值不存在时
        """
        # 找到e_over_r1在表格中的位置
        for i, e_val in enumerate(self.e_over_r1_values):
            if e_over_r1 <= e_val:
                if i == 0 or e_over_r1 == e_val:
                    # 直接返回表格值
                    coeff = coefficient_table[i][column_index]
                    if coeff is None:
                        raise ValueError(f"系数表中e/r1={e_val}, r2/r1={self.r2_over_r1_values[column_index]}处的值不存在")
                    return coeff
                else:
                    # 线性插值
                    e1 = self.e_over_r1_values[i-1]
                    e2 = self.e_over_r1_values[i]
                    coeff1 = coefficient_table[i-1][column_index]
                    coeff2 = coefficient_table[i][column_index]
                    
                    # 检查系数是否存在
                    if coeff1 is None or coeff2 is None:
                        raise ValueError(f"无法在e/r1={e1}-{e2}, r2/r1={self.r2_over_r1_values[column_index]}范围内进行插值，系数值不存在")
                    
                    # 线性插值公式
                    interpolated_coeff = coeff1 + (coeff2 - coeff1) * (e_over_r1 - e1) / (e2 - e1)
                    return interpolated_coeff
        
        # 如果超出范围，返回最后一个值
        coeff = coefficient_table[-1][column_index]
        if coeff is None:
            raise ValueError(f"系数表中e/r1={self.e_over_r1_values[-1]}, r2/r1={self.r2_over_r1_values[column_index]}处的值不存在")
        return coeff
    
    def get_xi_coefficient(self, e_over_r1: float, r2_over_r1: float = 0.0) -> float:
        """
        获取ξ系数（用于兼容现有代码）
        
        Args:
            e_over_r1: 偏心距与基础外半径的比值
            r2_over_r1: 基础内半径与外半径的比值，默认0.0
            
        Returns:
            float: ξ系数
        """
        _, xi = self.get_coefficients_by_interpolation(e_over_r1, r2_over_r1)
        return xi
    
    def get_tau_coefficient(self, e_over_r1: float, r2_over_r1: float = 0.0) -> float:
        """
        获取τ系数
        
        Args:
            e_over_r1: 偏心距与基础外半径的比值
            r2_over_r1: 基础内半径与外半径的比值，默认0.0
            
        Returns:
            float: τ系数
        """
        tau, _ = self.get_coefficients_by_interpolation(e_over_r1, r2_over_r1)
        return tau
    
    def validate_parameters(self, e_over_r1: float, r2_over_r1: float = 0.0) -> Tuple[bool, str]:
        """
        验证输入参数是否在合理范围内
        
        Args:
            e_over_r1: 偏心距与基础外半径的比值
            r2_over_r1: 基础内半径与外半径的比值
            
        Returns:
            Tuple[bool, str]: (是否有效, 错误信息)
        """
        if e_over_r1 < 0:
            return False, "偏心距比值e/r1不能为负数"
        
        if e_over_r1 > 0.5:
            return False, "偏心距比值e/r1过大，可能导致基础失稳"
        
        if r2_over_r1 < 0 or r2_over_r1 >= 1.0:
            return False, "内外半径比值r2/r1应在[0, 1)范围内"
        
        if e_over_r1 > 0.67:
            logger.warning("偏心距比值e/r1超出标准表格范围，计算结果可能不准确")
        
        return True, ""


# 创建全局实例供其他模块使用
foundation_pressure_coefficients = FoundationPressureCoefficients()