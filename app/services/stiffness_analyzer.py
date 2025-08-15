import math
from typing import List
from app.schemas import (
    FoundationGeometry,
    SoilLayer,
    StiffnessRequirements,
    StiffnessAnalysisResult,
    StiffnessSingleResult
)
from app.utils.logger import get_logger
from app.utils.soil_layer_selector import select_soil_layer_by_depth_from_pydantic

logger = get_logger(__name__)


class StiffnessAnalyzer:
    """
    刚度验算分析器
    
    根据图片中的公式计算地基旋转动态刚度和水平动态刚度，并验证是否满足要求
    
    公式：
    - 地基旋转动态刚度：Kφ,dyn = (4(1-2ν))/(3(1-ν)²) × R³ × Es,dyn
    - 地基水平动态刚度：KH,dyn = 2 × (1-2ν)/(1-ν)² × R × Es,dyn
    
    其中：
    - ν: 泊松比
    - R: 基础半径 (m)
    - Es,dyn: 动态压缩模量 (Pa) = 动态压缩模量 × 10⁶
    """
    
    def __init__(self, geometry: FoundationGeometry, soil_layers: List[SoilLayer]):
        """
        初始化刚度分析器
        
        Args:
            geometry: 基础几何信息
            soil_layers: 土层信息列表（使用第一个土层的压缩模量和泊松比）
        """
        self.geometry = geometry
        self.soil_layers = soil_layers
        
        # 使用第一个土层的参数
        if not soil_layers:
            raise ValueError("土层信息不能为空")

        self.first_soil_layer = select_soil_layer_by_depth_from_pydantic(geometry.buried_depth, soil_layers)
        self.R = geometry.base_radius  # 基础半径 (m)
        self.poisson_ratio = self.first_soil_layer.poisson_ratio  # 泊松比 ν
        
        # 动态压缩模量 (MPa)，乘以10是为了转换为动态值
        self.dynamic_compression_modulus = self.first_soil_layer.compression_modulus * 10
        
        # 计算 Es,dyn = 动态压缩模量 × 10⁶ (Pa)
        self.Es_dyn = self.dynamic_compression_modulus * 1e6  # 转换为Pa
        
        logger.info(f"刚度分析器初始化完成: R={self.R}m, ν={self.poisson_ratio}, "
                   f"Es_dyn={self.Es_dyn:.2e}Pa")
    
    def calculate_rotational_stiffness(self) -> float:
        """
        计算地基旋转动态刚度
        
        公式：Kφ,dyn = (4(1-2ν))/(3(1-ν)²) × R³ × Es,dyn
        
        Returns:
            float: 旋转动态刚度 (N·m/rad)
        """
        numerator = 4 * (1 - 2 * self.poisson_ratio)
        denominator = 3 * (1 - self.poisson_ratio) ** 2
        
        if denominator == 0:
            logger.warning(f"旋转刚度计算分母为零: denominator = 3 * (1 - {self.poisson_ratio})² = 0")
            return 0.0
        
        rotational_stiffness = (numerator / denominator) * (self.R ** 3) * self.Es_dyn
        
        logger.info(f"旋转动态刚度计算: ({numerator:.3f}/{denominator:.3f}) × {self.R}³ × "
                   f"{self.Es_dyn:.2e} = {rotational_stiffness:.3e}")
        
        return rotational_stiffness
    
    def calculate_horizontal_stiffness(self) -> float:
        """
        计算地基水平动态刚度
        
        公式：KH,dyn = 2 × (1-2ν)/(1-ν)² × R × Es,dyn
        
        Returns:
            float: 水平动态刚度 (N/m)
        """
        numerator = 1 - 2 * self.poisson_ratio
        denominator = (1 - self.poisson_ratio) ** 2
        
        if denominator == 0:
            logger.warning(f"水平刚度计算分母为零: denominator = (1 - {self.poisson_ratio})² = 0")
            return 0.0
        
        horizontal_stiffness = 2 * (numerator / denominator) * self.R * self.Es_dyn
        
        logger.info(f"水平动态刚度计算: 2 × ({numerator:.3f}/{denominator:.3f}) × {self.R} × "
                   f"{self.Es_dyn:.2e} = {horizontal_stiffness:.3e}")
        
        return horizontal_stiffness
    
    def analyze_stiffness(self, stiffness_requirements: StiffnessRequirements) -> StiffnessAnalysisResult:
        """
        执行刚度验算分析
        
        Args:
            stiffness_requirements: 刚度要求参数
            
        Returns:
            StiffnessAnalysisResult: 刚度验算结果
        """
        logger.info("开始刚度验算分析")
        
        try:
            # 计算刚度值
            calculated_rotational_stiffness = self.calculate_rotational_stiffness()
            calculated_horizontal_stiffness = self.calculate_horizontal_stiffness()
            
            # 获取要求的刚度值
            required_rotational = stiffness_requirements.required_rotational_stiffness
            required_horizontal = stiffness_requirements.required_horizontal_stiffness
            
            # 验证旋转刚度是否满足要求
            rotational_compliant = calculated_rotational_stiffness >= required_rotational
            rotational_details = self._generate_rotational_stiffness_details(
                calculated_rotational_stiffness, required_rotational, rotational_compliant
            )
            
            # 验证水平刚度是否满足要求
            horizontal_compliant = calculated_horizontal_stiffness >= required_horizontal
            horizontal_details = self._generate_horizontal_stiffness_details(
                calculated_horizontal_stiffness, required_horizontal, horizontal_compliant
            )
            
            # 整体符合性
            overall_compliance = rotational_compliant and horizontal_compliant
            
            # 创建旋转刚度结果
            rotational_result = StiffnessSingleResult(
                stiffness_type="旋转动态刚度",
                calculated_stiffness=calculated_rotational_stiffness,
                required_stiffness=required_rotational,
                stiffness_unit="N·m/rad",
                is_compliant=rotational_compliant,
                check_details=rotational_details
            )
            
            # 创建水平刚度结果
            horizontal_result = StiffnessSingleResult(
                stiffness_type="水平动态刚度",
                calculated_stiffness=calculated_horizontal_stiffness,
                required_stiffness=required_horizontal,
                stiffness_unit="N/m",
                is_compliant=horizontal_compliant,
                check_details=horizontal_details
            )
            
            # 创建最终结果
            result = StiffnessAnalysisResult(
                rotational_stiffness=rotational_result,
                horizontal_stiffness=horizontal_result,
                overall_compliance=overall_compliance
            )
            
            logger.info(f"刚度验算分析完成: 旋转刚度{'满足' if rotational_compliant else '不满足'}, "
                       f"水平刚度{'满足' if horizontal_compliant else '不满足'}, "
                       f"整体符合性: {overall_compliance}")
            
            return result
            
        except Exception as e:
            logger.error(f"刚度验算分析失败: {str(e)}")
            raise ValueError(f"刚度验算分析失败: {str(e)}")
    
    def _generate_rotational_stiffness_details(
        self, 
        calculated: float, 
        required: float, 
        compliant: bool
    ) -> str:
        """
        生成旋转刚度验算详情
        
        Args:
            calculated: 计算得到的旋转刚度
            required: 要求的旋转刚度
            compliant: 是否满足要求
            
        Returns:
            str: 验算详情描述
        """
        numerator = 4 * (1 - 2 * self.poisson_ratio)
        denominator = 3 * (1 - self.poisson_ratio) ** 2
        
        return (
            f"地基旋转动态刚度计算公式：Kφ,dyn = (4(1-2ν))/(3(1-ν)²) × R³ × Es,dyn = "
            f"({numerator:.3f})/({denominator:.3f}) × {self.R:.1f}³ × {self.Es_dyn:.2E} = "
            f"{calculated:.3E} N·m/rad {'≥' if compliant else '<'} "
            f"{required:.1E} N·m/rad，{'满足' if compliant else '不满足'}刚度要求。"
        )
    
    def _generate_horizontal_stiffness_details(
        self, 
        calculated: float, 
        required: float, 
        compliant: bool
    ) -> str:
        """
        生成水平刚度验算详情
        
        Args:
            calculated: 计算得到的水平刚度
            required: 要求的水平刚度
            compliant: 是否满足要求
            
        Returns:
            str: 验算详情描述
        """
        numerator = 1 - 2 * self.poisson_ratio
        denominator = (1 - self.poisson_ratio) ** 2
        
        return (
            f"地基水平动态刚度计算公式：KH,dyn = 2 × (1-2ν)/(1-ν)² × R × Es,dyn = "
            f"2 × ({numerator:.3f})/({denominator:.3f}) × {self.R:.1f} × {self.Es_dyn:.2E} = "
            f"{calculated:.3E} N/m {'≥' if compliant else '<'} "
            f"{required:.1E} N/m，{'满足' if compliant else '不满足'}刚度要求。"
        )
