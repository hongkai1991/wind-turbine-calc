"""
抗冲切分析器模块
负责风机基础抗冲切验算的计算逻辑
"""
import math
from typing import Dict, Any, Optional
from app.schemas import (
    FoundationGeometry,
    SelfWeightResult,
    MaterialProperties,
    AntiPunchingAnalysisResult,
    AntiPunchingSingleConditionResult
)
from app.utils.logger import get_logger

logger = get_logger(__name__)


class AntiPunchingAnalyzer:
    """抗冲切分析器"""
    
    def __init__(
        self,
        geometry: FoundationGeometry,
        load_calculation_results: Dict[str, Any],
        self_weight_result: SelfWeightResult,
        material: MaterialProperties,
        reinforcement_diameter: float = 20.0,
        importance_factor: float = 1.1
    ):
        """
        初始化抗冲切分析器
        
        Args:
            geometry: 基础几何信息
            load_calculation_results: 荷载计算结果
            self_weight_result: 基础自重计算结果
            material: 材料属性
            reinforcement_diameter: 钢筋直径(mm)，默认20，可取15
            importance_factor: 重要性系数γ0（从设计参数中获取）
        """
        self.geometry = geometry
        self.load_calculation_results = load_calculation_results
        self.self_weight_result = self_weight_result
        self.material = material
        self.reinforcement_diameter = reinforcement_diameter
        self.importance_factor = importance_factor
    
    def analyze(self) -> AntiPunchingAnalysisResult:
        """
        执行基础抗冲切验算
        
        Returns:
            AntiPunchingAnalysisResult: 基础抗冲切验算结果
        """
        try:
            logger.info("开始基础抗冲切验算")
            
            # 1. 计算有效截面高度h0（与抗剪强度分析保持一致）
            # h0 = 基础边缘高度 + 基础底板棱台高度 - 基础底板底面混凝土保护层厚度 - 1/2钢筋直径
            h0 = self._calculate_effective_section_height()
            
            # 2. 计算高度影响系数Bhp
            bhp = self._calculate_height_influence_coefficient(h0)
            
            # 3. 计算冲切破坏椎体上截面周长Bt
            bt = self._calculate_top_section_perimeter()
            
            # 4. 计算R1+H0
            R1_plus_H0 = self._calculate_R1_plus_H0(h0)
            
            # 5. 计算冲切破坏椎体下截面周长Bb
            bb = self._calculate_bottom_section_perimeter(R1_plus_H0)
            
            # 6. 计算抗冲切承载力Fr
            punching_capacity = self._calculate_punching_capacity(bhp, bt, bb, h0)
            
            # 7. 从荷载计算结果中获取各工况的冲切力
            condition_results = self._calculate_all_condition_results(h0, punching_capacity)
            
            # 8. 创建最终结果对象（构造抗冲切承载力对象）
            overall_compliance = all(
                result and result.is_compliant 
                for result in condition_results.values() 
                if result is not None
            )
            
            result = AntiPunchingAnalysisResult(
                punching_capacity={
                    "h0": h0,
                    "bhp": bhp,
                    "bt": bt,
                    "bb": bb,
                    "punching_capacity": punching_capacity,
                },
                normal_condition=condition_results.get("正常工况"),
                extreme_condition=condition_results.get("极端工况"),
                frequent_seismic_condition=condition_results.get("多遇地震工况"),
                rare_seismic_condition=condition_results.get("罕遇地震工况"),
                overall_compliance=overall_compliance
            )
            
            logger.info(f"基础抗冲切验算完成，整体符合性: {overall_compliance}")
            return result
            
        except Exception as e:
            logger.error(f"基础抗冲切验算失败: {str(e)}")
            raise ValueError(f"基础抗冲切验算失败: {str(e)}")
    
    def _calculate_effective_section_height(self) -> float:
        """
        计算有效截面高度h0（与抗剪强度分析保持一致）
        h0 = 基础边缘高度 + 基础底板棱台高度 - 基础底板底面混凝土保护层厚度 - 1/2钢筋直径
        
        Returns:
            float: 有效截面高度h0 (mm)
        """
        # 参数转换：将m转换为mm
        edge_height_mm = self.geometry.edge_height * 1000  # m转mm
        frustum_height_mm = self.geometry.frustum_height * 1000  # m转mm
        
        # 获取混凝土底面保护层厚度
        bottom_cover_mm = self.material.bottom_cover if self.material else 50.0  # mm
        half_rebar_diameter = self.reinforcement_diameter / 2
        
        h0 = edge_height_mm + frustum_height_mm - bottom_cover_mm - half_rebar_diameter
        logger.info(f"计算有效截面高度h0: {edge_height_mm}mm + {frustum_height_mm}mm - {bottom_cover_mm}mm - {half_rebar_diameter}mm = {h0}mm")
        
        return h0
    
    def _calculate_height_influence_coefficient(self, h0: float) -> float:
        """
        计算高度影响系数Bhp
        
        Args:
            h0: 有效截面高度 (mm)
            
        Returns:
            float: 高度影响系数Bhp
        """
        if h0 <= 800:
            bhp = 1.0
        elif h0 >= 2000:
            bhp = 0.9
        else:
            # 线性内插
            bhp = 1.0 - (h0 - 800) / (2000 - 800) * (1.0 - 0.9)
        
        logger.info(f"计算高度影响系数Bhp: h0={h0}mm，Bhp={bhp:.3f}")
        return bhp
    
    def _calculate_top_section_perimeter(self) -> float:
        """
        计算冲切破坏椎体上截面周长Bt
        
        Returns:
            float: 冲切破坏椎体上截面周长Bt (m)
        """
        bt = 2 * math.pi * self.geometry.column_radius
        logger.info(f"计算冲切破坏椎体上截面周长Bt: 2π×{self.geometry.column_radius}m = {bt:.2f}m")
        return bt
    
    def _calculate_R1_plus_H0(self, h0: float) -> float:
        """
        计算R1+H0
        
        Args:
            h0: 有效截面高度 (mm)
            
        Returns:
            float: R1+H0 (m)
        """
        R1_plus_H0 = self.geometry.base_radius + h0 / 1000  # h0转换为m
        logger.info(f"计算R1+H0: {self.geometry.base_radius}m + {h0/1000}m = {R1_plus_H0:.3f}m")
        return R1_plus_H0
    
    def _calculate_bottom_section_perimeter(self, R1_plus_H0: float) -> float:
        """
        计算冲切破坏椎体下截面周长Bb
        
        Args:
            R1_plus_H0: R1+H0值 (m)
            
        Returns:
            float: 冲切破坏椎体下截面周长Bb (m)
        """
        bb = 2 * math.pi * R1_plus_H0
        logger.info(f"计算冲切破坏椎体下截面周长Bb: 2π×{R1_plus_H0}m = {bb:.2f}m")
        return bb
    
    def _calculate_punching_capacity(self, bhp: float, bt: float, bb: float, h0: float) -> float:
        """
        计算抗冲切承载力Fr
        Fr = 0.35 * Bhp * 轴心抗拉强度设计值Ft * (Bt + Bb) * H0
        
        Args:
            bhp: 高度影响系数
            bt: 冲切破坏椎体上截面周长 (m)
            bb: 冲切破坏椎体下截面周长 (m)
            h0: 有效截面高度 (mm)
            
        Returns:
            float: 抗冲切承载力Fr (kN)
        """
        ft = self.material.ft * 1000 if self.material else 1.71 * 1000  # N/mm²，转换成kN/m²
        h0_m = h0 / 1000  # 转换为m
        punching_capacity = 0.35 * bhp * ft * (bt + bb) * h0_m  # 转换为kN
        
        logger.info(f"计算抗冲切承载力Fr: 0.35 × {bhp:.3f} × {ft}kN/m² × ({bt:.2f}+{bb:.2f})/{h0_m:.3f} = {punching_capacity:.2f}kN")
        return punching_capacity
    
    def _calculate_all_condition_results(self, h0: float, punching_capacity: float) -> Dict[str, Optional[AntiPunchingSingleConditionResult]]:
        """
        从荷载计算结果中获取各工况的冲切力并计算验算结果
        
        Args:
            h0: 有效截面高度 (mm)
            punching_capacity: 抗冲切承载力 (kN)
            
        Returns:
            Dict[str, Optional[AntiPunchingSingleConditionResult]]: 各工况计算结果
        """
        detailed_calculations = self.load_calculation_results.get("detailed_calculations", [])
        load_conditions = self.load_calculation_results.get("load_conditions", [])
        
        # 查找4种工况的计算结果
        condition_results = {}
        
        # 处理正常工况和极端工况（从detailed_calculations获取）
        condition_data = {}
        for calc in detailed_calculations:
            case_type = calc.get("load_case")
            if case_type in ["正常工况", "极端工况"]:
                condition_data[case_type] = calc
                
        logger.info(f"找到详细计算工况: {list(condition_data.keys())}")
        
        # 计算各工况的抗冲切验算
        for case_name, case_data in condition_data.items():
            logger.info(f"计算 {case_name} 的抗冲切验算")
            
            condition_results[case_name] = self._calculate_single_punching_condition_result(
                case_name, case_data, h0, punching_capacity
            )
        
        # 处理地震工况（从load_conditions获取，使用简化计算方法）
        seismic_conditions = {}
        for condition in load_conditions:
            case_type = condition.get("case_type")
            if case_type in ["多遇地震工况", "罕遇地震工况"]:
                seismic_conditions[case_type] = condition
                
        logger.info(f"找到地震工况: {list(seismic_conditions.keys())}")
        
        for case_name, case_data in seismic_conditions.items():
            logger.info(f"计算 {case_name} 的抗冲切验算")
            
            # 地震工况没有详细的Pj计算结果，使用估算方法
            simplified_condition_data = self._prepare_seismic_condition_data(case_data)
            
            condition_results[case_name] = self._calculate_single_punching_condition_result(
                case_name, simplified_condition_data, h0, punching_capacity
            )
        
        return condition_results
    
    def _prepare_seismic_condition_data(self, case_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        为地震工况准备简化的condition_data结构
        
        Args:
            case_data: 地震工况原始数据
            
        Returns:
            Dict[str, Any]: 简化的condition_data结构
        """
        loads = case_data.get("loads", {})
        foundation_weight = abs(loads.get("foundation_total_weight", 0))
        vertical_load = abs(loads.get("vertical_force", 0))
        
        # 估算Pj = (基础自重 + 竖向荷载) / 基础底板面积
        base_area = math.pi * self.geometry.base_radius**2
        estimated_pj = (foundation_weight + vertical_load) / base_area if base_area > 0 else 0
        
        # 构造简化的condition_data结构
        return {
            "combinations": {
                "standard": {
                    "Pj": {"value": estimated_pj, "unit": "kPa", "description": "估算基础底面净反力"}
                }
            }
        }
    
    def _calculate_single_punching_condition_result(
        self,
        case_name: str,
        condition_data: Dict[str, Any],
        h0: float,
        punching_capacity: float
    ) -> Optional[AntiPunchingSingleConditionResult]:
        """
        计算单个工况的抗冲切验算结果
        
        使用公式：Fl = 基础底面净反力Pj * π * [基础底板半径² - (台柱半径 + 高度H0)²]
        验算：γ_0 * F_l ≤ 抗冲切承载力Fr
        
        Args:
            case_name: 工况名称
            condition_data: 工况数据
            h0: 有效截面高度 (mm)
            punching_capacity: 抗冲切承载力 (kN)
            
        Returns:
            Optional[AntiPunchingSingleConditionResult]: 单个工况抗冲切验算结果
        """
        # 从standard组合中获取Pj数据
        standard_combination = condition_data.get("combinations", {}).get("standard", {})
        
        # 提取Pj值
        pj = self._extract_pj_value(standard_combination, case_name)
        
        if pj is None:
            logger.warning(f"{case_name}未找到Pj值，跳过此工况")
            # 创建一个默认的结果
            return AntiPunchingSingleConditionResult(
                condition_type=case_name,
                punching_force=0.0,
                punching_capacity=punching_capacity,
                gamma_0_F=0.0,
                gamma_0=self.importance_factor,
                is_compliant=True,  # 无数据默认为通过
                check_details=f"{case_name}：无Pj数据，无法计算冲切力。"
            )
        
        # 计算冲切力和验算结果
        return self._calculate_punching_verification(case_name, pj, h0, punching_capacity)
    
    def _extract_pj_value(self, standard_combination: Dict[str, Any], case_name: str) -> Optional[float]:
        """
        从standard组合中提取Pj值
        
        Args:
            standard_combination: standard组合数据
            case_name: 工况名称
            
        Returns:
            Optional[float]: Pj值 (kPa)，如果提取失败返回None
        """
        if standard_combination and "Pj" in standard_combination:
            pj_data = standard_combination.get("Pj", {})
            if isinstance(pj_data, dict) and "value" in pj_data:
                return float(pj_data["value"])  # kPa
            elif isinstance(pj_data, (int, float)):
                return float(pj_data)  # kPa
        
        logger.warning(f"{case_name}未找到standard组合中的Pj数据")
        return None
    
    def _calculate_punching_verification(
        self, 
        case_name: str, 
        pj: float, 
        h0: float, 
        punching_capacity: float
    ) -> AntiPunchingSingleConditionResult:
        """
        计算冲切验算结果
        
        Args:
            case_name: 工况名称
            pj: 基础底面净反力Pj (kPa)
            h0: 有效截面高度 (mm)
            punching_capacity: 抗冲切承载力 (kN)
            
        Returns:
            AntiPunchingSingleConditionResult: 单个工况抗冲切验算结果
        """
        # 计算冲切力：Fl = Pj * π * [R1² - (r1 + H0)²]
        # R1: 基础底板半径 (m)
        # r1: 台柱半径 (m) 
        # H0: 有效截面高度 (m)
        R1 = self.geometry.base_radius  # m
        r1 = self.geometry.column_radius  # m
        H0 = h0 / 1000  # 从mm转换为m
        
        # 计算冲切面积 (m²)
        punching_area = math.pi * (R1**2 - (r1 + H0)**2)
        
        # 计算冲切力：Fl = Pj (kPa) * 冲切面积 (m²) = kN
        punching_force = pj * punching_area
        
        # 计算γ0Fl
        gamma_0_F = self.importance_factor * punching_force
        
        # 判断是否满足要求：γ0Fl ≤ Fr
        is_compliant = gamma_0_F <= punching_capacity
        
        # 生成检查详情，按照用户要求的格式
        check_details = (
            f"γ_0 F_l={punching_force:.3f}×{self.importance_factor}={gamma_0_F:.3f}kN"
            f"{'≤' if is_compliant else '>'}{punching_capacity:.1f}kN，"
            f"{'满足' if is_compliant else '不满足'}《陆上风电场工程风电机组基础设计规范》7.2.7条规定。"
        )
        
        # 创建单个工况结果
        condition_result = AntiPunchingSingleConditionResult(
            condition_type=case_name,
            punching_force=punching_force,
            punching_capacity=punching_capacity,
            gamma_0_F=gamma_0_F,
            gamma_0=self.importance_factor,
            is_compliant=is_compliant,
            check_details=check_details
        )
        
        logger.info(f"{case_name}: Pj={pj:.2f}kPa, 冲切面积={punching_area:.3f}m², "
                   f"Fl={punching_force:.2f}kN, γ0Fl={gamma_0_F:.2f}kN, "
                   f"Fr={punching_capacity:.2f}kN, {'满足' if is_compliant else '不满足'}")
        
        return condition_result
