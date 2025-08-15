"""
抗倾覆分析器模块
负责风机基础抗倾覆验算的计算逻辑
"""
from typing import Dict, Any
from app.schemas import (
    FoundationGeometry,
    SelfWeightResult,
    AntiOverturningAnalysisResult,
    AntiOverturningSingleConditionResult
)
from app.utils.logger import get_logger

logger = get_logger(__name__)


class AntiOverturningAnalyzer:
    """抗倾覆分析器"""
    
    def __init__(self):
        """初始化抗倾覆分析器"""
        # 设计系数γd固定为1.6
        self.gamma_d = 1.6
    
    async def analyze(
        self,
        geometry: FoundationGeometry,
        load_calculation_results: Dict[str, Any],
        self_weight_result: SelfWeightResult,
        importance_factor: float = 1.1
    ) -> AntiOverturningAnalysisResult:
        """
        执行抗倾覆验算分析
        
        Args:
            geometry: 基础几何信息
            load_calculation_results: 荷载计算结果
            self_weight_result: 基础自重计算结果
            importance_factor: 重要性系数γ0
            
        Returns:
            AntiOverturningAnalysisResult: 抗倾覆验算结果
        """
        try:
            logger.info("开始抗倾覆验算")
            
            # 计算要求的安全系数
            required_safety_factor = importance_factor * self.gamma_d
            
            # 基础半径R，用于计算抗倾覆力矩
            R = geometry.base_radius
            
            # 解析荷载数据
            condition_data, seismic_conditions = self._parse_load_data(load_calculation_results)
            
            # 计算各工况的抗倾覆验算
            results = {}
            
            # 处理正常和极端工况（从detailed_calculations获取）
            self._process_normal_extreme_conditions(
                condition_data, self_weight_result, R, 
                importance_factor, required_safety_factor, results
            )
            
            # 处理地震工况（从load_conditions获取，使用估算方法）
            self._process_seismic_conditions(
                seismic_conditions, self_weight_result, R,
                importance_factor, required_safety_factor, results
            )
            
            # 检查所有工况是否都满足要求
            overall_compliance = all(result.is_compliant for result in results.values())
            
            # 创建默认结果（如果某个工况缺失）
            default_result = self._create_default_result(
                importance_factor, required_safety_factor
            )
            
            # 创建最终结果
            analysis_result = AntiOverturningAnalysisResult(
                normal_condition=results.get("正常工况", default_result),
                extreme_condition=results.get("极端工况", default_result),
                frequent_seismic_condition=results.get("多遇地震工况", default_result),
                rare_seismic_condition=results.get("罕遇地震工况", default_result),
                overall_compliance=overall_compliance
            )
            
            logger.info(f"抗倾覆验算完成，整体符合性: {overall_compliance}")
            return analysis_result
            
        except Exception as e:
            logger.error(f"抗倾覆验算失败: {str(e)}")
            raise ValueError(f"抗倾覆验算失败: {str(e)}")
    
    def _parse_load_data(self, load_calculation_results: Dict[str, Any]) -> tuple:
        """
        解析荷载计算结果数据
        
        Args:
            load_calculation_results: 荷载计算结果
            
        Returns:
            tuple: (condition_data, seismic_conditions)
        """
        # 从荷载计算结果中获取详细计算数据
        detailed_calculations = load_calculation_results.get("detailed_calculations", [])
        
        # 查找正常和极端工况的计算结果
        condition_data = {}
        for calc in detailed_calculations:
            case_type = calc.get("load_case")
            if case_type in ["正常工况", "极端工况"]:
                condition_data[case_type] = calc
        
        # 从load_conditions中查找地震工况
        load_conditions = load_calculation_results.get("load_conditions", [])
        seismic_conditions = {}
        for condition in load_conditions:
            case_type = condition.get("case_type")
            if case_type in ["多遇地震工况", "罕遇地震工况"]:
                seismic_conditions[case_type] = condition
        
        logger.info(f"找到详细计算工况: {list(condition_data.keys())}")
        logger.info(f"找到地震工况: {list(seismic_conditions.keys())}")
        
        return condition_data, seismic_conditions
    
    def _process_normal_extreme_conditions(
        self,
        condition_data: Dict[str, Any],
        self_weight_result: SelfWeightResult,
        R: float,
        importance_factor: float,
        required_safety_factor: float,
        results: Dict[str, AntiOverturningSingleConditionResult]
    ):
        """
        处理正常和极端工况的抗倾覆验算
        
        Args:
            condition_data: 工况数据
            self_weight_result: 自重计算结果
            R: 基础半径
            importance_factor: 重要性系数
            required_safety_factor: 要求的安全系数
            results: 结果字典
        """
        for case_name, case_data in condition_data.items():
            logger.info(f"计算 {case_name} 的抗倾覆验算")
            
            # 从standard组合中获取数据
            standard_combination = case_data.get("combinations", {}).get("standard", {})
            
            if standard_combination:
                # 倾覆力矩Ms = Mrk (kN·m)
                mrk_data = standard_combination.get("Mrk", {})
                overturning_moment = mrk_data.get("value", 0)
                
                # 抗倾覆力矩Mr = (Nk + Gk) * R
                nk_gk_data = standard_combination.get("Nk_Gk", {})
                total_vertical_load = nk_gk_data.get("value", 0)  # Nk + Gk
                
                anti_overturning_moment = total_vertical_load * R
            else:
                logger.warning(f"{case_name} 未找到standard组合数据")
                overturning_moment = 0
                anti_overturning_moment = 0
            
            # 计算并存储结果
            self._calculate_single_condition_result(
                case_name, overturning_moment, anti_overturning_moment,
                importance_factor, required_safety_factor, results
            )
    
    def _process_seismic_conditions(
        self,
        seismic_conditions: Dict[str, Any],
        self_weight_result: SelfWeightResult,
        R: float,
        importance_factor: float,
        required_safety_factor: float,
        results: Dict[str, AntiOverturningSingleConditionResult]
    ):
        """
        处理地震工况的抗倾覆验算
        
        Args:
            seismic_conditions: 地震工况数据
            self_weight_result: 自重计算结果
            R: 基础半径
            importance_factor: 重要性系数
            required_safety_factor: 要求的安全系数
            results: 结果字典
        """
        for case_name, case_data in seismic_conditions.items():
            logger.info(f"计算 {case_name} 的抗倾覆验算（估算方法）")
            
            # 倾覆力矩Ms = Mx (kN·m)
            overturning_moment = case_data.get("Mx", 0)
            
            # 抗倾覆力矩Mr = (Nk + Gk) * R （使用估算的总重量）
            vertical_load = case_data.get("Fz", 0)  # Nk
            foundation_weight = self_weight_result.total_weight  # Gk
            total_vertical_load = abs(vertical_load) + foundation_weight  # Nk + Gk
            anti_overturning_moment = total_vertical_load * R
            
            # 计算并存储结果
            self._calculate_single_condition_result(
                case_name, overturning_moment, anti_overturning_moment,
                importance_factor, required_safety_factor, results
            )
    
    def _calculate_single_condition_result(
        self,
        case_name: str,
        overturning_moment: float,
        anti_overturning_moment: float,
        importance_factor: float,
        required_safety_factor: float,
        results: Dict[str, AntiOverturningSingleConditionResult]
    ):
        """
        计算单个工况的抗倾覆验算结果
        
        Args:
            case_name: 工况名称
            overturning_moment: 倾覆力矩
            anti_overturning_moment: 抗倾覆力矩
            importance_factor: 重要性系数
            required_safety_factor: 要求的安全系数
            results: 结果字典
        """
        # 安全系数
        safety_factor = (
            anti_overturning_moment / abs(overturning_moment) 
            if overturning_moment != 0 else 999999.0
        )
        
        # 判断是否满足规范要求
        is_compliant = safety_factor >= required_safety_factor
        
        # 生成检查详情
        if overturning_moment == 0:
            safety_factor_display = "∞"
        else:
            safety_factor_display = f"{safety_factor:.3f}"
        
        check_details = (
            f"Mr/Ms = {anti_overturning_moment:.3f}/{abs(overturning_moment):.3f} = {safety_factor_display} "
            f"{'≥' if is_compliant else '<'} γ0γd = {importance_factor} × {self.gamma_d} = {required_safety_factor:.2f}，"
            f"{'满足' if is_compliant else '不满足'} 《陆上风电场工程风电机组基础设计规范》 6.5.2 条规定。"
        )
        
        # 创建单工况结果
        condition_result = AntiOverturningSingleConditionResult(
            condition_type=case_name,
            overturning_moment=abs(overturning_moment),
            anti_overturning_moment=anti_overturning_moment,
            safety_factor=safety_factor,
            gamma_0=importance_factor,
            gamma_d=self.gamma_d,
            required_safety_factor=required_safety_factor,
            is_compliant=is_compliant,
            check_details=check_details
        )
        
        results[case_name] = condition_result
        logger.info(f"{case_name}: Ms={abs(overturning_moment):.2f}, Mr={anti_overturning_moment:.2f}, "
                   f"安全系数={safety_factor:.3f}, {'满足' if is_compliant else '不满足'}")
    
    def _create_default_result(
        self,
        importance_factor: float,
        required_safety_factor: float
    ) -> AntiOverturningSingleConditionResult:
        """
        创建默认的验算结果（当工况数据缺失时使用）
        
        Args:
            importance_factor: 重要性系数
            required_safety_factor: 要求的安全系数
            
        Returns:
            AntiOverturningSingleConditionResult: 默认结果
        """
        return AntiOverturningSingleConditionResult(
            condition_type="未找到",
            overturning_moment=0.0,
            anti_overturning_moment=0.0,
            safety_factor=0.0,
            gamma_0=importance_factor,
            gamma_d=self.gamma_d,
            required_safety_factor=required_safety_factor,
            is_compliant=False,
            check_details="工况数据未找到"
        )
