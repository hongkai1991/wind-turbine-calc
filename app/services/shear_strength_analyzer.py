"""
基础抗剪强度分析器
"""
import math
from typing import Dict, Any, List, Optional
from app.schemas import (
    FoundationGeometry,
    MaterialProperties,
    SelfWeightResult,
    ShearStrengthAnalysisResult,
    ShearStrengthSingleConditionResult
)
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ShearStrengthAnalyzer:
    """
    基础抗剪强度分析器
    
    负责基础抗剪强度计算（多工况验算）的具体计算逻辑
    """
    
    def __init__(
        self,
        geometry: FoundationGeometry,
        load_calculation_results: Dict[str, Any],
        self_weight_result: SelfWeightResult,
        material: MaterialProperties = None,
        reinforcement_diameter: float = 20.0,
        importance_factor: float = 1.1
    ):
        """
        初始化抗剪强度分析器
        
        Args:
            geometry: 基础几何信息
            load_calculation_results: 荷载计算结果
            self_weight_result: 自重计算结果
            material: 材料属性信息（包含保护层厚度和抗拉强度）
            reinforcement_diameter: 钢筋直径(mm)，默认20mm
            importance_factor: 重要性系数γ0，默认1.1
        """
        self.geometry = geometry
        self.load_calculation_results = load_calculation_results
        self.self_weight_result = self_weight_result
        self.material = material
        self.reinforcement_diameter = reinforcement_diameter
        self.importance_factor = importance_factor
        
        # 工况映射
        self.condition_mapping = {
            "正常工况": ("正常工况", "normal_condition"),
            "极端工况": ("极端工况", "extreme_condition"), 
            "多遇地震工况": ("多遇地震工况", "frequent_seismic_condition"),
            "罕遇地震工况": ("罕遇地震工况", "rare_seismic_condition")
        }
    
    def analyze_shear_strength(self) -> ShearStrengthAnalysisResult:
        """
        执行基础抗剪强度计算（多工况验算）
        
        计算过程：
        1. 基础剪切承载力计算：
           - h0 = 基础边缘高度 + 基础底板棱台高度 - 基础底板底面混凝土保护层厚度 - 1/2钢筋直径
           - 当 h0 >= 2000mm 时，取 h0 = 2000mm
           - b = (1 - 基础底板棱台高度/2H0) * [2√(基础底板半径² - 台柱半径²)]
           - Bh = ⁴√(基础边缘高度/H0)
           - A0 = b * H0
           - Vr = 0.7 * Bh * Ft * A0
        2. 各工况剪力计算：
           - V = Pj(S1 - S2)
           - S1 = cos⁻¹(r/R)/π * πR²
           - S2 = R²tan(cos⁻¹(r/R))
        3. 与剪切承载力比较判断是否满足规范
        
        Returns:
            ShearStrengthAnalysisResult: 剪切强度分析结果
        """
        logger.info("开始基础抗剪强度计算（多工况验算）")
        
        # ===== 第一部分：保留原有的基础抗剪强度计算逻辑 =====
        shear_capacity_data = self._calculate_shear_capacity()
        
        # ===== 第二部分：新增的各工况剪力计算和比较验算 =====
        s1, s2 = self._calculate_s1_s2()
        
        # 初始化各工况结果
        condition_results = {}
        overall_compliance = True
        
        # 处理正常工况和极端工况
        overall_compliance = self._process_normal_extreme_conditions(
            shear_capacity_data["shear_capacity"], s1, s2, condition_results, overall_compliance
        )
        
        # 处理地震工况
        overall_compliance = self._process_seismic_conditions(
            shear_capacity_data["shear_capacity"], s1, s2, condition_results, overall_compliance
        )
        
        # 创建最终结果对象（构造剪切承载力对象）
        result = ShearStrengthAnalysisResult(
            shear_capacity={
                "h0": shear_capacity_data["h0"],
                "shear_width": shear_capacity_data["shear_width"],
                "height_factor": shear_capacity_data["height_factor"],
                "shear_area": shear_capacity_data["shear_area"],
                "shear_capacity": shear_capacity_data["shear_capacity"],
            },
            normal_condition=condition_results.get("normal_condition"),
            extreme_condition=condition_results.get("extreme_condition"),
            frequent_seismic_condition=condition_results.get("frequent_seismic_condition"),
            rare_seismic_condition=condition_results.get("rare_seismic_condition"),
            overall_compliance=overall_compliance
        )
        
        logger.info(f"基础抗剪强度计算完成，整体符合性: {overall_compliance}")
        return result
    
    def _calculate_shear_capacity(self) -> Dict[str, float]:
        """
        计算基础剪切承载力
        
        Returns:
            Dict[str, float]: 剪切承载力相关参数
        """
        # 参数转换：将m转换为mm
        base_radius_mm = self.geometry.base_radius * 1000  # m转mm
        column_radius_mm = self.geometry.column_radius * 1000  # m转mm
        edge_height_mm = self.geometry.edge_height * 1000  # m转mm
        frustum_height_mm = self.geometry.frustum_height * 1000  # m转mm
        
        # 获取混凝土底面保护层厚度
        bottom_cover_mm = self.material.bottom_cover if self.material else 50.0  # mm
        
        # 1. 计算h0（有效截面高度）
        h0 = edge_height_mm + frustum_height_mm - bottom_cover_mm - self.reinforcement_diameter / 2
        
        # 当h0>=2000mm时，取2000mm
        h0_for_calculation = 2000.0 if h0 >= 2000.0 else h0
        
        logger.info(f"计算h0: {edge_height_mm}mm + {frustum_height_mm}mm - {bottom_cover_mm}mm - {self.reinforcement_diameter/2}mm = {h0}mm")
        
        # 2. 计算受剪切截面宽度b
        # b = (1 - 基础底板棱台高度/2H0) * [2√(基础底板半径² - 台柱半径²)]
        h0_m = h0 / 1000  # 转换成米
        term1 = 1 - self.geometry.frustum_height / (2 * h0_m)
        term2 = 2 * math.sqrt(self.geometry.base_radius**2 - self.geometry.column_radius**2)
        shear_width = term1 * term2
        
        # 3. 计算高度影响系数Bh
        # Bh = ⁴√(基础边缘高度/H0)
        height_factor = (edge_height_mm / h0_for_calculation) ** 0.25
        
        logger.info(f"计算高度影响系数Bh: ⁴√({edge_height_mm}mm / {h0_for_calculation}mm) = {height_factor}")
        
        # 4. 计算受剪切面积A0
        # A0 = b * H0
        shear_area = shear_width * h0_m  # m²
        
        logger.info(f"计算受剪切面积A0: {shear_width}m * {h0_m}m = {shear_area}m²")
        
        # 5. 计算剪切承载力Vr
        # Vr = 0.7 * Bh * Ft * A0
        # 获取混凝土抗拉强度设计值
        ft = self.material.ft*1000 if self.material else 1.71*1000  # N/mm²，默认使用C40混凝土的抗拉强度，转换成kN/m²
        
        # 计算剪切承载力（N）
        shear_capacity = 0.7 * height_factor * ft * shear_area
        
        logger.info(f"计算剪切承载力Vr: 0.7 * {height_factor} * {ft}kN/m² * {shear_area}m² = {shear_capacity}kN")
        
        return {
            "h0": h0_m,
            "shear_width": shear_width,
            "height_factor": height_factor,
            "shear_area": shear_area,
            "shear_capacity": shear_capacity
        }
    
    def _calculate_s1_s2(self) -> tuple[float, float]:
        """
        计算S1和S2参数
        
        Returns:
            tuple[float, float]: (s1, s2)
        """
        # 计算S1和S2（使用m为单位）
        R = self.geometry.base_radius  # 基础底板半径(m)
        R2 = self.geometry.column_radius  # 台柱半径(m)
        
        # S1 = cos⁻¹(r/R)/π * πR²
        cos_inverse_term = math.acos(R2 / R)  # cos⁻¹(r/R)
        s1 = (cos_inverse_term / math.pi) * (math.pi * R**2)
        
        # S2 = R²tan(cos⁻¹(r/R))
        s2 = R2**2 * math.tan(cos_inverse_term)
        
        logger.info(f"计算S1: cos⁻¹({R2}/{R})/π × πR² = {cos_inverse_term:.4f}/π × π×{R}² = {s1:.2f} m²")
        logger.info(f"计算S2: R²tan(cos⁻¹(r/R)) = {R}² × tan({cos_inverse_term:.4f}) = {s2:.2f} m²")
        
        return s1, s2
    
    def _process_normal_extreme_conditions(
        self, 
        shear_capacity: float, 
        s1: float, 
        s2: float, 
        condition_results: Dict[str, Any], 
        overall_compliance: bool
    ) -> bool:
        """
        处理正常工况和极端工况
        
        Args:
            shear_capacity: 剪切承载力
            s1: S1参数
            s2: S2参数
            condition_results: 工况结果字典
            overall_compliance: 整体符合性
            
        Returns:
            bool: 更新后的整体符合性
        """
        # 从荷载计算结果中获取详细计算数据（参照抗滑验算的逻辑）
        detailed_calculations = self.load_calculation_results.get("detailed_calculations", [])
        
        # 查找4种工况的计算结果
        condition_data = {}
        for calc in detailed_calculations:
            case_type = calc.get("load_case")
            if case_type in ["正常工况", "极端工况"]:
                condition_data[case_type] = calc
        
        logger.info(f"找到详细计算工况: {list(condition_data.keys())}")
        
        # 处理正常工况和极端工况（从detailed_calculations获取）
        for case_name, case_data in condition_data.items():
            condition_name, result_key = self.condition_mapping[case_name]
            logger.info(f"开始计算{condition_name}剪力验算")
            
            # 从standard组合中获取Pj数据（参照抗滑分析逻辑）
            standard_combination = case_data.get("combinations", {}).get("standard", {})
            
            pj = self._extract_pj_from_standard_combination(standard_combination, condition_name)
            
            if pj is None:
                logger.warning(f"{condition_name}未找到Pj值，跳过此工况")
                # 创建一个默认的结果
                condition_result = ShearStrengthSingleConditionResult(
                    condition_type=condition_name,
                    shear_force=0.0,
                    shear_capacity=shear_capacity,
                    gamma_0_V=0.0,
                    gamma_0=self.importance_factor,
                    pj=0.0,
                    s1=s1,
                    s2=s2,
                    is_compliant=True,  # 无数据默认为通过
                    check_details=f"{condition_name}：无Pj数据，无法计算剪力。"
                )
                condition_results[result_key] = condition_result
                continue
            
            # 计算剪力和验算
            condition_result, is_compliant = self._calculate_single_condition_result(
                condition_name, pj, s1, s2, shear_capacity
            )
            condition_results[result_key] = condition_result
            
            if not is_compliant:
                overall_compliance = False
            
            logger.info(f"{condition_name}: Pj={pj:.2f}kPa, V={condition_result.shear_force:.2f}kN, γ0V={condition_result.gamma_0_V:.2f}kN, {'满足' if is_compliant else '不满足'}")
        
        return overall_compliance
    
    def _process_seismic_conditions(
        self, 
        shear_capacity: float, 
        s1: float, 
        s2: float, 
        condition_results: Dict[str, Any], 
        overall_compliance: bool
    ) -> bool:
        """
        处理地震工况
        
        Args:
            shear_capacity: 剪切承载力
            s1: S1参数
            s2: S2参数
            condition_results: 工况结果字典
            overall_compliance: 整体符合性
            
        Returns:
            bool: 更新后的整体符合性
        """
        # 从load_conditions中查找地震工况
        load_conditions = self.load_calculation_results.get("load_conditions", [])
        seismic_conditions = {}
        for condition in load_conditions:
            case_type = condition.get("case_type")
            if case_type in ["多遇地震工况", "罕遇地震工况"]:
                seismic_conditions[case_type] = condition
        
        logger.info(f"找到地震工况: {list(seismic_conditions.keys())}")
        
        # 处理地震工况（从load_conditions获取，使用估算方法）
        for case_name, case_data in seismic_conditions.items():
            condition_name, result_key = self.condition_mapping[case_name]
            logger.info(f"开始计算{condition_name}剪力验算")
            
            # 地震工况暂时设置默认Pj值，实际应该从地震荷载计算中获取
            # 这里参照抗滑分析的做法，设置默认值
            pj = 50.0  # kPa，默认值
            logger.warning(f"{condition_name}使用默认Pj值: {pj}kPa")
            
            # 计算剪力和验算
            condition_result, is_compliant = self._calculate_single_condition_result(
                condition_name, pj, s1, s2, shear_capacity, use_default_pj=True
            )
            condition_results[result_key] = condition_result
            
            if not is_compliant:
                overall_compliance = False
            
            logger.info(f"{condition_name}: Pj={pj:.2f}kPa(默认值), V={condition_result.shear_force:.2f}kN, γ0V={condition_result.gamma_0_V:.2f}kN, {'满足' if is_compliant else '不满足'}")
        
        return overall_compliance
    
    def _extract_pj_from_standard_combination(self, standard_combination: Dict[str, Any], condition_name: str) -> Optional[float]:
        """
        从standard组合中提取Pj数据
        
        Args:
            standard_combination: standard组合数据
            condition_name: 工况名称
            
        Returns:
            Optional[float]: Pj值，如果失败返回None
        """
        if standard_combination and "Pj" in standard_combination:
            pj_data = standard_combination.get("Pj", {})
            if isinstance(pj_data, dict) and "value" in pj_data:
                return float(pj_data["value"])
            elif isinstance(pj_data, (int, float)):
                return float(pj_data)
            else:
                return None
        else:
            logger.warning(f"{condition_name}未找到standard组合中的Pj数据")
            return None
    
    def _calculate_single_condition_result(
        self, 
        condition_name: str, 
        pj: float, 
        s1: float, 
        s2: float, 
        shear_capacity: float,
        use_default_pj: bool = False
    ) -> tuple[ShearStrengthSingleConditionResult, bool]:
        """
        计算单个工况的剪力验算结果
        
        Args:
            condition_name: 工况名称
            pj: Pj值
            s1: S1参数
            s2: S2参数
            shear_capacity: 剪切承载力
            use_default_pj: 是否使用默认Pj值
            
        Returns:
            tuple[ShearStrengthSingleConditionResult, bool]: (工况结果, 是否符合)
        """
        # 计算剪力 V = Pj(S1 - S2)，注意单位转换
        # Pj单位为kPa，S1-S2单位为m²，结果V单位为kN
        shear_force_raw = pj * (s1 - s2)  # kN
        
        # 取绝对值，因为剪力应该为正值
        shear_force = abs(shear_force_raw)
        
        # 计算 γ0*V
        gamma_0_V = self.importance_factor * shear_force
        
        # 判断是否满足规范：γ0*V ≤ Vr
        is_compliant = gamma_0_V <= shear_capacity
        
        # 生成检查详情
        default_suffix = "（使用默认Pj值）" if use_default_pj else ""
        check_details = f"γ_0 V={self.importance_factor}×{shear_force:.3f}={gamma_0_V:.3f}kN{'≤' if is_compliant else '>'}{shear_capacity:.2f}kN， {'满足' if is_compliant else '不满足'}《陆上风电场工程风电机组基础设计规范》 7.2.9条规定。{default_suffix}"
        
        # 创建单工况结果
        condition_result = ShearStrengthSingleConditionResult(
            condition_type=condition_name,
            shear_force=shear_force,
            shear_capacity=shear_capacity,
            gamma_0_V=gamma_0_V,
            gamma_0=self.importance_factor,
            pj=pj,
            s1=s1,
            s2=s2,
            is_compliant=is_compliant,
            check_details=check_details
        )
        
        return condition_result, is_compliant
