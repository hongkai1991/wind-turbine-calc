"""
脱开面积验算分析器

该模块实现风机基础脱开面积验算功能，根据荷载计算结果中的受压区域高度和受压类型，
计算基础脱开面积和脱开面积百分比，并判断是否符合规范要求。
"""

import math
from typing import Dict, Any
from app.schemas import (
    FoundationGeometry,
    DetachmentAreaResult,
    DetachmentAreaAnalysisResult
)
from app.utils.logger import get_logger

logger = get_logger(__name__)


class DetachmentAnalyzer:
    """脱开面积分析器"""
    
    def __init__(self, geometry: FoundationGeometry):
        """
        初始化脱开面积分析器
        
        Args:
            geometry: 基础几何信息
        """
        self.geometry = geometry
        self.foundation_area = math.pi * (geometry.base_radius ** 2)
        logger.info(f"初始化脱开面积分析器，基础底面积: {self.foundation_area:.3f} m²")
    
    def calculate_detachment_area(self, compressed_height: float, pressure_type: str) -> float:
        """
        计算脱开面积
        
        Args:
            compressed_height: 受压区域高度(m)
            pressure_type: 受压类型(全截面受压/偏心受压)
            
        Returns:
            float: 脱开面积(m²)
        """
        R = self.geometry.base_radius
        
        if pressure_type == "全截面受压":
            # 全截面受压时，脱开面积为0
            detachment_area = 0.0
            logger.info("全截面受压，脱开面积为0")
        else:
            # 偏心受压时，根据受压区域高度计算脱开面积
            # 脱开面积 = 基础总面积 - 受压区域面积
            
            # 根据受压区域高度计算受压区域面积（弓形面积）
            # 这里需要根据受压区域高度反推偏心距，然后计算弓形面积
            compressed_area = self._calculate_compressed_area_from_height(compressed_height, R)
            detachment_area = self.foundation_area - compressed_area
            
            logger.info(f"偏心受压，受压区域高度: {compressed_height:.3f}m，受压面积: {compressed_area:.3f}m²，脱开面积: {detachment_area:.3f}m²")
        
        return max(0.0, detachment_area)  # 确保脱开面积不为负
    
    def _calculate_compressed_area_from_height(self, compressed_height: float, radius: float) -> float:
        """
        根据受压区域高度计算受压区域面积
        
        Args:
            compressed_height: 受压区域高度(m)
            radius: 基础半径(m)
            
        Returns:
            float: 受压区域面积(m²)
        """
        # 如果受压区域高度等于直径，说明是全截面受压
        if compressed_height >= 2 * radius:
            return self.foundation_area
        
        # 根据受压区域高度计算弓形面积
        # h = compressed_height, R = radius
        # 弓形高度 h，半径 R
        # 弓形面积 = R²×arccos((R-h)/R) - (R-h)×sqrt(2Rh-h²)
        
        h = compressed_height
        R = radius
        
        # 边界检查
        if h <= 0:
            return 0.0
        if h >= 2 * R:
            return self.foundation_area
        
        # 计算弓形面积
        try:
            # 使用标准弓形面积公式
            cos_term = (R - h) / R
            if abs(cos_term) > 1.0:  # 处理数值误差
                cos_term = max(-1.0, min(1.0, cos_term))
            
            angle = math.acos(cos_term)
            sqrt_term = math.sqrt(2 * R * h - h * h) if (2 * R * h - h * h) >= 0 else 0
            
            segment_area = R * R * angle - (R - h) * sqrt_term
            
            logger.debug(f"弓形面积计算: h={h:.3f}, R={R:.3f}, angle={angle:.3f}, area={segment_area:.3f}")
            
            return segment_area
            
        except Exception as e:
            logger.warning(f"弓形面积计算出错: {e}，使用近似计算")
            # 使用近似公式: A ≈ (2/3) * h * sqrt(2*R*h - h²)
            if 2 * R * h - h * h >= 0:
                return (2/3) * h * math.sqrt(2 * R * h - h * h)
            else:
                return 0.0
    
    def calculate_detachment_ratio(self, detachment_area: float) -> float:
        """
        计算脱开面积百分比
        
        Args:
            detachment_area: 脱开面积(m²)
            
        Returns:
            float: 脱开面积百分比(0-1之间的小数)
        """
        if self.foundation_area <= 0:
            return 0.0
        
        ratio = detachment_area / self.foundation_area
        logger.debug(f"脱开面积百分比: {detachment_area:.3f} / {self.foundation_area:.3f} = {ratio:.4f}")
        
        return ratio
    
    def analyze_single_condition_from_detailed_calc(
        self,
        condition_type: str,
        detailed_calc: Dict[str, Any],
        allowed_ratio: float
    ) -> DetachmentAreaResult:
        """
        从detailed_calculations结构中分析单个工况的脱开面积
        
        Args:
            condition_type: 工况类型
            detailed_calc: detailed_calculations中的单个工况计算结果
            allowed_ratio: 允许脱开面积百分比
            
        Returns:
            DetachmentAreaResult: 脱开面积验算结果
        """
        logger.info(f"开始分析{condition_type}脱开面积")
        
        # 从detailed_calc的combinations.standard中获取数据
        standard_result = detailed_calc.get("combinations", {}).get("standard", {})
        
        if not standard_result:
            logger.warning(f"{condition_type}：未找到standard组合结果")
            return self._create_default_result(condition_type, allowed_ratio, "未找到计算结果")
        
        # 获取受压类型
        pressure_type = standard_result.get("pressure_type", "未知")
        
        # 获取simple_pk对象中的数据
        simple_pk = standard_result.get("simple_pk", {})
        if not simple_pk:
            logger.warning(f"{condition_type}：未找到simple_pk结果")
            return self._create_default_result(condition_type, allowed_ratio, "未找到simple_pk结果")
        
        # 获取受压区域高度
        compressed_height = 0.0
        compressed_height_info = simple_pk.get("compressed_height", {})
        if isinstance(compressed_height_info, dict) and "value" in compressed_height_info:
            compressed_height = compressed_height_info["value"]
        else:
            compressed_height = compressed_height_info if isinstance(compressed_height_info, (int, float)) else 0.0
        
        # 获取受压区域面积（从simple_pk中获取，这是已经计算好的）
        compressed_area_info = simple_pk.get("compressed_area", {})
        if isinstance(compressed_area_info, dict) and "value" in compressed_area_info:
            compressed_area = compressed_area_info["value"]
        else:
            compressed_area = compressed_area_info if isinstance(compressed_area_info, (int, float)) else self.foundation_area
        
        logger.info(f"{condition_type}: 受压类型={pressure_type}, 受压区域高度={compressed_height:.3f}m, 受压区域面积={compressed_area:.3f}m²")
        
        # 计算脱开面积 = 基础总面积 - 受压区域面积
        detachment_area = max(0.0, self.foundation_area - compressed_area)
        
        # 处理浮点数精度问题，如果脱开面积非常小，则视为0
        if detachment_area < 1e-6:
            detachment_area = 0.0
        
        # 计算脱开面积百分比
        detachment_ratio = self.calculate_detachment_ratio(detachment_area)
        
        # 判断是否符合规定
        is_compliant = detachment_ratio <= allowed_ratio

        # 生成检查详情
        check_details = (
            f"脱开面积百分比:{detachment_area:.3f}/{self.foundation_area:.3f}={detachment_ratio:.3f}"
            f"≤{allowed_ratio:.2f}，{'满足' if is_compliant else '不满足'}《陆上风电场工程风电机组基础设计规范》 6.1.3条规定。"
        )

        logger.info(f"{condition_type}验算结果: 脱开面积={detachment_area:.3f}m², 百分比={detachment_ratio:.4f}, 允许值={allowed_ratio:.4f}, 符合规定={is_compliant}")

        return DetachmentAreaResult(
            condition_type=condition_type,
            compressed_height=compressed_height,
            foundation_area=compressed_area,
            detachment_area=detachment_area,
            detachment_ratio=detachment_ratio,
            allowed_ratio=allowed_ratio,
            is_compliant=is_compliant,
            pressure_type=pressure_type,
            check_details=check_details
        )
    
    def _create_default_result(self, condition_type: str, allowed_ratio: float, reason: str) -> DetachmentAreaResult:
        """创建默认的脱开面积验算结果"""
        # 生成检查详情
        check_details = (
            f"脱开面积百分比:0.000/{self.foundation_area:.3f}=0.000≤{allowed_ratio:.2f}，不满足《陆上风电场工程风电机组基础设计规范》 6.1.3条规定。"
        )

        return DetachmentAreaResult(
            condition_type=condition_type,
            compressed_height=0.0,
            foundation_area=self.foundation_area,
            detachment_area=0.0,
            detachment_ratio=0.0,
            allowed_ratio=allowed_ratio,
            is_compliant=False,
            pressure_type=f"计算失败: {reason}",
            check_details=check_details
        )
    
    def analyze_detachment_area(
        self,
        load_calculation_results: Dict[str, Any],
        allowed_detachment_area: Dict[str, float]
    ) -> DetachmentAreaAnalysisResult:
        """
        分析脱开面积验算
        
        Args:
            load_calculation_results: 荷载计算结果字典，包含detailed_calculations结构
            allowed_detachment_area: 允许脱开面积百分比字典
            
        Returns:
            DetachmentAreaAnalysisResult: 脱开面积验算分析结果
        """
        logger.info("开始脱开面积验算分析")
        
        # 从load_calculation_results中获取detailed_calculations
        detailed_calculations = load_calculation_results.get("detailed_calculations", [])
        
        if not detailed_calculations:
            logger.warning("未找到detailed_calculations数据")
            return self._create_default_analysis_result(allowed_detachment_area, "未找到detailed_calculations数据")
        
        # 查找正常工况和极端工况的计算结果
        normal_calc = None
        extreme_calc = None
        
        for calc in detailed_calculations:
            load_case = calc.get("load_case", "")
            if load_case == "正常工况":
                normal_calc = calc
            elif load_case == "极端工况":
                extreme_calc = calc
            elif load_case == "多遇地震工况":
                frequent_seismic_calc=calc
        
        # 分析正常工况
        normal_result = None
        if normal_calc:
            normal_result = self.analyze_single_condition_from_detailed_calc(
                "正常工况",
                normal_calc,
                allowed_detachment_area.get("normal", 0.0)
            )
        else:
            logger.warning("未找到正常工况计算结果")
            normal_result = self._create_default_result("正常工况", allowed_detachment_area.get("normal", 0.0), "未找到正常工况数据")
        
        # 分析极端工况
        extreme_result = None
        if extreme_calc:
            extreme_result = self.analyze_single_condition_from_detailed_calc(
                "极端工况",
                extreme_calc,
                allowed_detachment_area.get("extreme", 0.25)
            )
        else:
            logger.warning("未找到极端工况计算结果")
            extreme_result = self._create_default_result("极端工况", allowed_detachment_area.get("extreme", 0.25), "未找到极端工况数据")

        # 分析多遇地震工况
        frequent_seismic_result = None
        if frequent_seismic_calc:
            frequent_seismic_result = self.analyze_single_condition_from_detailed_calc(
                "多遇地震工况",
                frequent_seismic_calc,
                allowed_detachment_area.get("frequent_seismic", 0.25)
            )
        else:
            logger.warning("未找到多遇地震工况计算结果")
            frequent_seismic_result = self._create_default_result("多遇地震工况", allowed_detachment_area.get("frequent_seismic", 0.25), "未找到多遇地震工况数据")
        # 判断整体符合性
        overall_compliance = normal_result.is_compliant and extreme_result.is_compliant and frequent_seismic_result.is_compliant

        logger.info(f"脱开面积验算分析完成: 整体符合={overall_compliance}")
        
        return DetachmentAreaAnalysisResult(
            normal_condition=normal_result,
            extreme_condition=extreme_result,
            frequent_seismic_condition=frequent_seismic_result,
            overall_compliance=overall_compliance
        )
    
    def _create_default_analysis_result(self, allowed_detachment_area: Dict[str, float], reason: str) -> DetachmentAreaAnalysisResult:
        """创建默认的脱开面积验算分析结果"""
        normal_result = self._create_default_result("正常工况", allowed_detachment_area.get("normal", 0.0), reason)
        extreme_result = self._create_default_result("极端工况", allowed_detachment_area.get("extreme", 0.25), reason)
        
        return DetachmentAreaAnalysisResult(
            normal_condition=normal_result,
            extreme_condition=extreme_result,
            overall_compliance=False
        )