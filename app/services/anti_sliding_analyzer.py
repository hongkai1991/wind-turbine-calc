"""
抗滑移分析器模块
负责风机基础抗滑移验算的计算逻辑
"""
from typing import Dict, Any
from app.schemas import (
    FoundationGeometry,
    SelfWeightResult,
    AntiSlidingAnalysisResult,
    AntiSlidingSingleConditionResult
)
from app.utils.logger import get_logger

logger = get_logger(__name__)


class AntiSlidingAnalyzer:
    """抗滑移分析器"""
    
    def __init__(self):
        """初始化抗滑移分析器"""
        # 摩擦系数μ固定为0.3，实际应取自土层信息中的摩擦系数
        self.mu = 0.3
        # 设计系数γd为1.3（抗滑验算的设计系数）
        self.gamma_d = 1.3
    
    async def analyze(
        self,
        geometry: FoundationGeometry,
        load_calculation_results: Dict[str, Any],
        self_weight_result: SelfWeightResult,
        importance_factor: float = 1.1
    ) -> AntiSlidingAnalysisResult:
        """
        执行抗滑移验算分析
        
        Args:
            geometry: 基础几何信息
            load_calculation_results: 荷载计算结果
            self_weight_result: 基础自重计算结果
            importance_factor: 重要性系数γ0
            
        Returns:
            AntiSlidingAnalysisResult: 抗滑移验算结果
        """
        try:
            logger.info("开始基础抗滑验算")
            
            # 解析荷载数据
            condition_data, seismic_conditions = self._parse_load_data(load_calculation_results)
            
            # 计算各工况的抗滑移验算
            results = {}
            
            # 处理正常和极端工况（从detailed_calculations获取）
            self._process_normal_extreme_conditions(
                condition_data, self_weight_result, 
                importance_factor, results
            )
            
            # 处理地震工况（从load_conditions获取，使用估算方法）
            self._process_seismic_conditions(
                seismic_conditions, self_weight_result,
                importance_factor, results
            )
            
            # 检查所有工况是否都满足要求
            overall_compliance = all(result.is_compliant for result in results.values())
            
            # 创建默认结果（如果某个工况缺失）
            default_result = self._create_default_result(importance_factor)
            
            # 创建最终结果
            analysis_result = AntiSlidingAnalysisResult(
                normal_condition=results.get("正常工况", default_result),
                extreme_condition=results.get("极端工况", default_result),
                frequent_seismic_condition=results.get("多遇地震工况", default_result),
                rare_seismic_condition=results.get("罕遇地震工况", default_result),
                overall_compliance=overall_compliance
            )
            
            logger.info(f"基础抗滑验算完成，整体符合性: {overall_compliance}")
            return analysis_result
            
        except Exception as e:
            logger.error(f"基础抗滑验算失败: {str(e)}")
            raise ValueError(f"基础抗滑验算失败: {str(e)}")
    
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
        importance_factor: float,
        results: Dict[str, AntiSlidingSingleConditionResult]
    ):
        """
        处理正常和极端工况的抗滑移验算
        
        Args:
            condition_data: 工况数据
            self_weight_result: 自重计算结果
            importance_factor: 重要性系数
            results: 结果字典
        """
        for case_name, case_data in condition_data.items():
            logger.info(f"计算 {case_name} 的抗滑验算")
            
            # 从standard组合中获取数据
            standard_combination = case_data.get("combinations", {}).get("standard", {})
            
            if standard_combination:
                # 滑动力Fs = Frk (kN)
                frk_data = standard_combination.get("Frk", {})
                sliding_force = frk_data.get("value", 0)
                
                # 抗滑力Fr = (Nk + Gk) * μ
                nk_gk_data = standard_combination.get("Nk_Gk", {})
                total_vertical_load = nk_gk_data.get("value", 0)  # Nk + Gk
                
                anti_sliding_force = total_vertical_load * self.mu
            else:
                logger.warning(f"{case_name} 未找到standard组合数据")
                sliding_force = 0
                anti_sliding_force = 0
                total_vertical_load = 0
            
            # 计算并存储结果
            self._calculate_single_condition_result(
                case_name, sliding_force, anti_sliding_force, total_vertical_load,
                importance_factor, results
            )
    
    def _process_seismic_conditions(
        self,
        seismic_conditions: Dict[str, Any],
        self_weight_result: SelfWeightResult,
        importance_factor: float,
        results: Dict[str, AntiSlidingSingleConditionResult]
    ):
        """
        处理地震工况的抗滑移验算
        
        Args:
            seismic_conditions: 地震工况数据
            self_weight_result: 自重计算结果
            importance_factor: 重要性系数
            results: 结果字典
        """
        for case_name, case_data in seismic_conditions.items():
            logger.info(f"计算 {case_name} 的抗滑验算（估算方法）")
            
            # 滑动力Fs = Fx (kN) 
            sliding_force = case_data.get("Fx", 0)
            
            # 抗滑力Fr = (Nk + Gk) * μ （使用估算的总重量）
            vertical_load = case_data.get("Fz", 0)  # Nk
            foundation_weight = self_weight_result.total_weight  # Gk
            total_vertical_load = abs(vertical_load) + foundation_weight  # Nk + Gk
            anti_sliding_force = total_vertical_load * self.mu
            
            # 计算并存储结果
            self._calculate_single_condition_result(
                case_name, sliding_force, anti_sliding_force, total_vertical_load,
                importance_factor, results
            )
    
    def _calculate_single_condition_result(
        self,
        case_name: str,
        sliding_force: float,
        anti_sliding_force: float,
        total_vertical_load: float,
        importance_factor: float,
        results: Dict[str, AntiSlidingSingleConditionResult]
    ):
        """
        计算单个工况的抗滑移验算结果
        
        Args:
            case_name: 工况名称
            sliding_force: 滑动力Fs
            anti_sliding_force: 抗滑力Fr
            total_vertical_load: 总竖向力(Nk + Gk)
            importance_factor: 重要性系数γ0
            results: 结果字典
        """
        # γ0 * Fs
        gamma_0_Fs = importance_factor * abs(sliding_force)
        
        # 设计值 = Fr / γd
        design_anti_sliding_force = anti_sliding_force / self.gamma_d
        
        # 判断是否满足规范要求: γ0 * Fs ≤ Fr / γd
        is_compliant = gamma_0_Fs <= design_anti_sliding_force
        
        # 生成检查详情
        check_details = (
            f"抗滑力：Fr = (Nk + Gk)μ = {total_vertical_load:.3f} × {self.mu} = {anti_sliding_force:.3f}kN，"
            f"滑动力：Fs = {abs(sliding_force):.1f}kN，"
            f"γ0Fs = {importance_factor} × {abs(sliding_force):.1f} = {gamma_0_Fs:.1f}kN "
            f"{'≤' if is_compliant else '>'} 1/γd Fr = 1/{self.gamma_d} × {anti_sliding_force:.3f} = {design_anti_sliding_force:.2f}kN，"
            f"{'满足' if is_compliant else '不满足'}《陆上风电场工程风电机组基础设计规范》 6.5.2 条规定。"
        )
        
        # 创建单工况结果
        condition_result = AntiSlidingSingleConditionResult(
            condition_type=case_name,
            sliding_force=abs(sliding_force),
            anti_sliding_force=anti_sliding_force,
            gamma_0_Fs=gamma_0_Fs,
            mu=self.mu,
            gamma_0=importance_factor,
            is_compliant=is_compliant,
            check_details=check_details
        )
        
        results[case_name] = condition_result
        logger.info(f"{case_name}: Fs={abs(sliding_force):.2f}, Fr={anti_sliding_force:.2f}, "
                   f"γ0Fs={gamma_0_Fs:.2f}, {'满足' if is_compliant else '不满足'}")
    
    def _create_default_result(
        self,
        importance_factor: float
    ) -> AntiSlidingSingleConditionResult:
        """
        创建默认的验算结果（当工况数据缺失时使用）
        
        Args:
            importance_factor: 重要性系数
            
        Returns:
            AntiSlidingSingleConditionResult: 默认结果
        """
        return AntiSlidingSingleConditionResult(
            condition_type="未找到",
            sliding_force=0.0,
            anti_sliding_force=0.0,
            gamma_0_Fs=0.0,
            mu=self.mu,
            gamma_0=importance_factor,
            is_compliant=False,
            check_details="工况数据未找到"
        )
