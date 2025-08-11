import math
import asyncio
import httpx
from typing import Dict, Any, List, Optional
from app.schemas import (
    FoundationCalculationRequest,
    LoadCalculationRequest,
    FoundationResult,
    LoadResult,
    StabilityResult,
    FoundationGeometry,
    MaterialProperties,
    SelfWeightResult,
    LoadCase,
    GeometryValidationResult,
    GeometryValidationRequest,
    TowerBaseLoadRequest,
    TowerBaseLoadResponse,
    DetachmentAreaAnalysisResult,
    AllowedDetachmentArea,
    BearingCapacityAnalysisResult,
    SoilLayer,
    DesignParameters,
    StiffnessRequirements,
    StiffnessAnalysisResult,
    StiffnessSingleResult,
    AntiPunchingAnalysisResult,
    AntiPunchingSingleConditionResult,
    ShearStrengthAnalysisResult,
    ShearStrengthSingleConditionResult,
    AntiOverturningAnalysisResult,
    AntiOverturningSingleConditionResult,
    AntiSlidingAnalysisResult,
    AntiSlidingSingleConditionResult,
    SettlementAnalysisResult

)
from app.services.load_calculation import LoadCalculator, LoadingCondition, BaseBottomLoad
from app.services.load_calculation.tower_base_load import TowerBaseLoadCalculator
from app.services.self_weight_calculator import SelfWeightCalculator
from app.services.detachment_analyzer import DetachmentAnalyzer
from app.services.bearing_capacity_analyzer import BearingCapacityAnalyzer, BearingCapacityParameters
from app.services.settlement_analyzer import SettlementAnalyzer
from app.core.config import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

class CalculationService:
    """计算业务逻辑服务"""
    
    def __init__(self):
        self.safety_factors = {
            "overturning": 2.0,
            "sliding": 1.5,
            "bearing": 1.2
        }
    
    async def validate_foundation_geometry(self, geometry: FoundationGeometry) -> GeometryValidationResult:
        """
        基础体型验算
        
        Args:
            geometry: 基础几何信息
            
        Returns:
            GeometryValidationResult: 基础体型验算结果
        """
        logger.info("开始进行基础体型验算")
        
        try:
            # 模拟异步计算过程
            await asyncio.sleep(0.1)
            
            # 调用FoundationGeometry类的验算方法
            overall_dimension_ratio = geometry.validate_geometry()
            slope_info = geometry.check_slope_compliance()
            
            # 判断几何尺寸是否合理，应小于等于2.5
            is_geometry_valid = isinstance(overall_dimension_ratio, (int, float)) and overall_dimension_ratio <= 2.5

            # 从坡度信息中获取各项数据
            slope_horizontal_to_vertical = slope_info.get("horizontal_to_vertical", 0)
            slope_description = slope_info.get("slope_description", "无效")
            is_slope_compliant = slope_info.get("is_compliant", False)
            
            # 生成验算说明
            validation_messages = []
            
            if not is_geometry_valid:
                validation_messages.append("基础几何尺寸不合理")
                if geometry.column_radius >= geometry.base_radius:
                    validation_messages.append("台柱半径不能大于等于底板半径")
                if geometry.edge_height <= 0 or geometry.frustum_height <= 0:
                    validation_messages.append("基础高度参数必须大于0")
            else:
                validation_messages.append(f"基础整体尺寸比值为{overall_dimension_ratio:.2f}")
                if overall_dimension_ratio >= 2.5:
                    validation_messages.append("基础外形尺寸符合不超过1:2.5的要求")
                else:
                    validation_messages.append("基础底板棱台坡度过陡，建议调整尺寸")
            
            if not is_slope_compliant:
                validation_messages.append(f"基础圆台坡度{slope_description}不符合1:4规范要求(水平:垂直≥1:4)")
            else:
                validation_messages.append(f"基础圆台坡度{slope_description}符合规范要求(不超过1:4)")
            
            # 综合评价
            if is_geometry_valid and is_slope_compliant:
                validation_messages.insert(0, "基础体型验算通过，几何尺寸合理")
            else:
                validation_messages.insert(0, "基础体型验算不通过，需要调整设计")
            
            validation_message = "，".join(validation_messages)
            
            result = GeometryValidationResult(
                is_geometry_valid=is_geometry_valid,
                overall_dimension_ratio=overall_dimension_ratio if is_geometry_valid else 0.0,
                slope_horizontal_to_vertical=slope_horizontal_to_vertical,
                slope_description=slope_description,
                is_slope_compliant=is_slope_compliant,
                validation_message=validation_message
            )
            
            logger.info(f"基础体型验算完成: {'通过' if (is_geometry_valid and is_slope_compliant) else '不通过'}")
            return result
            
        except Exception as e:
            logger.error(f"基础体型验算失败: {str(e)}")
            raise
    
    async def calculate_self_weight(
        self, 
        geometry: FoundationGeometry, 
        material: MaterialProperties,
        cover_soil_density: float,
        groundwater_depth: float,
        soil_layers: Optional[List[Dict[str, Any]]] = None
    ) -> SelfWeightResult:
        """
        计算自重，包括体积、重力、浮力、总重量
        
        Args:
            geometry: 基础几何信息
            material: 材料属性
            cover_soil_density: 覆土容重
            groundwater_depth: 地下水埋深
            soil_layers: 土层信息列表，用于浮力计算
            
        Returns:
            SelfWeightResult: 自重计算结果
        """
        logger.info("开始计算基础自重")
        
        try:
            # 模拟异步计算过程
            await asyncio.sleep(0.1)
            
            calculator = SelfWeightCalculator(geometry, material, cover_soil_density, groundwater_depth, soil_layers)
            
            # 验证参数
            is_valid, error_msg = calculator.validate_input_parameters()
            if not is_valid:
                raise ValueError(f"参数验证失败: {error_msg}")
            
            result = calculator.get_calculation_result()
            
            logger.info(f"自重计算完成，总重量: {result.total_weight:.2f}kN")
            return result
            
        except Exception as e:
            logger.error(f"自重计算失败: {str(e)}")
            raise
    
    async def calculate_tower_base_turbine_load(self, request: TowerBaseLoadRequest) -> TowerBaseLoadResponse:
        """
        计算塔筒底部风机荷载
        
        Args:
            request: 塔筒底部荷载计算请求
            
        Returns:
            TowerBaseLoadResponse: 塔筒底部荷载计算结果
        """
        calculator = TowerBaseLoadCalculator()
        return await calculator.calculate(request)
    
    async def calculate_comprehensive_load_analysis(
        self,
        geometry: FoundationGeometry,
        material: MaterialProperties,
        self_weight_result: SelfWeightResult = None,
        loading_conditions: List[Dict[str, Any]] = None,
        tower_base_load_result: TowerBaseLoadResponse = None,
        soil_layers: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        综合荷载分析 - 调用LoadingCondition中所有的核算方法，并计算地震工况
        
        Args:
            geometry: 基础几何信息
            material: 材料属性
            self_weight_result: 自重计算结果
            loading_conditions: 荷载工况列表，包含四种工况的Fr、Fv、Fz、Mx、My、Mz参数
            tower_base_load_result: 塔筒底部荷载计算结果，包含地震力数据
            soil_layers: 土层信息列表，用于浮力计算
            
        Returns:
            Dict[str, Any]: 包含所有荷载计算结果的字典，包括6种工况
        """
        try:
            load_calculator = LoadCalculator(geometry, material, self_weight_result, loading_conditions, tower_base_load_result, soil_layers)
            comprehensive_results=await load_calculator.calculate_base_bottom_load()
            return comprehensive_results
        except Exception as e:
            logger.error(f"综合荷载分析失败: {str(e)}")
            raise
    
    async def calculate_detachment_area_analysis(
        self,
        geometry: FoundationGeometry,
        load_calculation_results: Dict[str, Any],
        allowed_detachment_area: AllowedDetachmentArea
    ) -> DetachmentAreaAnalysisResult:
        """
        脱开面积验算分析
        
        Args:
            geometry: 基础几何信息
            load_calculation_results: 荷载计算结果
            allowed_detachment_area: 允许脱开面积百分比字典
            
        Returns:
            DetachmentAreaAnalysisResult: 脱开面积验算分析结果
        """
        try:
            logger.info("开始脱开面积验算分析")
            
            # 创建脱开面积分析器
            detachment_analyzer = DetachmentAnalyzer(geometry)
            
            # 执行脱开面积验算分析
            result = detachment_analyzer.analyze_detachment_area(
                load_calculation_results,
                {"normal": allowed_detachment_area.normal, "extreme": allowed_detachment_area.extreme}
            )
            
            logger.info(f"脱开面积验算分析完成: 整体符合={result.overall_compliance}")
            
            return result
            
        except Exception as e:
            logger.error(f"脱开面积验算分析失败: {str(e)}")
            # 返回默认的失败结果
            from app.schemas import DetachmentAreaResult
            
            foundation_area = math.pi * (geometry.base_radius ** 2)
            
            default_normal = DetachmentAreaResult(
                condition_type="正常工况",
                compressed_height=0.0,
                foundation_area=foundation_area,
                detachment_area=0.0,
                detachment_ratio=0.0,
                allowed_ratio=allowed_detachment_area.get("normal", 0.0),
                is_compliant=False,
                pressure_type="计算失败",
                check_details=f"脱开面积百分比:0.000/{foundation_area:.3f}=0.000≤{allowed_detachment_area.get('normal', 0.0):.2f}，不满足《陆上风电场工程风电机组基础设计规范》 6.1.3条规定。"
            )
            
            default_extreme = DetachmentAreaResult(
                condition_type="极端工况",
                compressed_height=0.0,
                foundation_area=foundation_area,
                detachment_area=0.0,
                detachment_ratio=0.0,
                allowed_ratio=allowed_detachment_area.get("extreme", 0.25),
                is_compliant=False,
                pressure_type="计算失败",
                check_details=f"脱开面积百分比:0.000/{foundation_area:.3f}=0.000≤{allowed_detachment_area.get('extreme', 0.25):.2f}，不满足《陆上风电场工程风电机组基础设计规范》 6.1.3条规定。"
            )
            
            return DetachmentAreaAnalysisResult(
                normal_condition=default_normal,
                extreme_condition=default_extreme,
                overall_compliance=False
            )
    
    async def calculate_foundation_bearing_capacity(
        self,
        geometry: FoundationGeometry,
        soil_layer: Any,
        load_calculation_results: Dict[str, Any]
    ) -> BearingCapacityAnalysisResult:
        """
        地基承载力验算
        
        Args:
            geometry: 基础几何信息
            soil_layer: 选定的土层信息
            load_calculation_results: 荷载计算结果
            
        Returns:
            BearingCapacityResult: 地基承载力验算结果
        """
        logger.info("开始地基承载力验算")
        
        try:
            # 提取基础几何参数
            b = geometry.base_radius*2  # 基础圆台直径
            d = geometry.buried_depth  # 基础埋深
            
            # 提取土层参数
            if not soil_layer:
                raise ValueError("土层信息不能为空")
            
            fak = soil_layer.fak  # 承载力特征值
            eta_b = soil_layer.eta_b  # 宽度修正系数
            eta_d = soil_layer.eta_d  # 深度修正系数
            zeta_a = soil_layer.zeta_a  # 地基抗震承载力修正系数
            gamma_m = soil_layer.density  # 重度
            
            # 从荷载计算结果中提取地基压力
            # 从detailed_calculations列表中提取各工况的地基压力
            detailed_calculations = load_calculation_results.get("detailed_calculations", [])
            
            # 初始化地基压力值（仅正常与极端工况）
            pk_normal = 0.0
            pkmax_normal = 0.0
            pk_extreme = 0.0
            pkmax_extreme = 0.0
            
            # 遍历detailed_calculations找到对应工况的数据
            for calculation in detailed_calculations:
                load_case = calculation.get("load_case", "")
                combinations = calculation.get("combinations", {})
                standard = combinations.get("standard", {})
                
                if load_case == "正常工况":
                    # 提取正常工况的地基压力
                    simple_pk = standard.get("simple_pk", {})
                    pk_normal = simple_pk.get("pk", {}).get("value", 0.0)
                    pkmax_normal = standard.get("Pkmax", {}).get("value", 0.0)
                    
                elif load_case == "极端工况":
                    # 提取极端工况的地基压力
                    simple_pk = standard.get("simple_pk", {})
                    pk_extreme = simple_pk.get("pk", {}).get("value", 0.0)
                    pkmax_extreme = standard.get("Pkmax", {}).get("value", 0.0)
                    # 如果没有Pkmax，尝试获取Pmax
                    if pkmax_extreme == 0.0:
                        pkmax_extreme = standard.get("Pmax", {}).get("value", 0.0)
                        
            logger.info(f"提取地基压力: 正常工况 pk={pk_normal:.3f}, pkmax={pkmax_normal:.3f}")
            logger.info(f"提取地基压力: 极端工况 pk={pk_extreme:.3f}, pkmax={pkmax_extreme:.3f}")
            
            # 创建地基承载力计算参数（仍计算fa与fae，但最终响应仅包含normal/extreme）
            params = BearingCapacityParameters(
                b=b,
                d=d,
                fak=fak,
                eta_b=eta_b,
                eta_d=eta_d,
                zeta_a=zeta_a,
                gamma_m=gamma_m,
                pk_normal=pk_normal,
                pkmax_normal=pkmax_normal,
                pk_extreme=pk_extreme,
                pkmax_extreme=pkmax_extreme,
                pek_seismic=0.0,
                pekmax_seismic=0.0
            )
            
            # 创建地基承载力验算器
            analyzer = BearingCapacityAnalyzer()
            
            # 执行地基承载力验算
            result = analyzer.analyze_bearing_capacity(params)
            
            # 组装简化响应：calculation_type由控制器注入，这里仅返回主体
            overall = result.normal_condition_compliant and result.extreme_condition_compliant
            response = BearingCapacityAnalysisResult(
                bearing_capacity_characteristic={
                    "fa": result.fa,
                    "fae": result.fae
                },
                normal_condition={
                    "pk": result.pk_normal,
                    "pkmax": result.pkmax_normal,
                    "check_details": result.normal_check_details
                },
                extreme_condition={
                    "pk": result.pk_extreme,
                    "pkmax": result.pkmax_extreme,
                    "check_details": result.extreme_check_details
                },
                overall_compliance=overall
            )
            
            logger.info(f"地基承载力验算完成，整体符合性(仅正/极): {overall}")
            return response
            
        except Exception as e:
            logger.error(f"地基承载力验算失败: {str(e)}")
            raise ValueError(f"地基承载力验算失败: {str(e)}")

    async def calculate_anti_overturning_analysis(
        self, 
        geometry: FoundationGeometry, 
        load_calculation_results: Dict[str, Any],
        self_weight_result: SelfWeightResult,
        importance_factor: float = 1.1
    ) -> AntiOverturningAnalysisResult:
        """
        抗倾覆验算
        
        Args:
            geometry: 基础几何信息
            load_calculation_results: 荷载计算结果
            self_weight_result: 基础自重计算结果
            importance_factor: 重要性系数γ0（从设计参数中获取）
            
        Returns:
            AntiOverturningAnalysisResult: 抗倾覆验算结果
        """
        try:
            logger.info("开始抗倾覆验算")
            
            # 设计系数γd固定为1.6
            gamma_d = 1.6
            required_safety_factor = importance_factor * gamma_d
            
            # 基础半径R，用于计算抗倾覆力矩
            R = geometry.base_radius
            
            # 从荷载计算结果中获取详细计算数据
            detailed_calculations = load_calculation_results.get("detailed_calculations", [])
            
            # 查找4种工况的计算结果
            condition_data = {}
            for calc in detailed_calculations:
                case_type = calc.get("load_case")
                if case_type in ["正常工况", "极端工况"]:
                    condition_data[case_type] = calc
            
            # 从load_conditions中查找地震工况（地震工况可能不在detailed_calculations中）
            load_conditions = load_calculation_results.get("load_conditions", [])
            seismic_conditions = {}
            for condition in load_conditions:
                case_type = condition.get("case_type")
                if case_type in ["多遇地震工况", "罕遇地震工况"]:
                    seismic_conditions[case_type] = condition
            
            logger.info(f"找到详细计算工况: {list(condition_data.keys())}")
            logger.info(f"找到地震工况: {list(seismic_conditions.keys())}")
            
            # 计算各工况的抗倾覆验算
            results = {}
            
            # 处理正常工况和极端工况（从detailed_calculations获取）
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
                    total_vertical_load = 0
                
                # 计算并存储结果
                self._calculate_single_condition_result(
                    case_name, overturning_moment, anti_overturning_moment, 
                    importance_factor, gamma_d, required_safety_factor, results
                )
            
            # 处理地震工况（从load_conditions获取，使用估算方法）
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
                    importance_factor, gamma_d, required_safety_factor, results
                )
            
            # 检查所有工况是否都满足要求
            overall_compliance = all(result.is_compliant for result in results.values())
            
            # 确保有4种工况的结果，如果没有则创建默认结果
            default_result = AntiOverturningSingleConditionResult(
                condition_type="未找到",
                overturning_moment=0.0,
                anti_overturning_moment=0.0,
                safety_factor=0.0,
                gamma_0=importance_factor,
                gamma_d=gamma_d,
                required_safety_factor=required_safety_factor,
                is_compliant=False,
                check_details="工况数据未找到"
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

    def _calculate_single_condition_result(
        self,
        case_name: str,
        overturning_moment: float,
        anti_overturning_moment: float,
        importance_factor: float,
        gamma_d: float,
        required_safety_factor: float,
        results: dict
    ):
        """
        计算单个工况的抗倾覆验算结果
        
        Args:
            case_name: 工况名称
            overturning_moment: 倾覆力矩
            anti_overturning_moment: 抗倾覆力矩
            importance_factor: 重要性系数
            gamma_d: 设计系数
            required_safety_factor: 要求的安全系数
            results: 结果字典
        """
        # 安全系数
        safety_factor = anti_overturning_moment / abs(overturning_moment) if overturning_moment != 0 else 999999.0
        
        # 判断是否满足规范要求
        is_compliant = safety_factor >= required_safety_factor
        
        # 生成检查详情
        if overturning_moment == 0:
            safety_factor_display = "∞"
        else:
            safety_factor_display = f"{safety_factor:.3f}"
        
        check_details = (
            f"Mr/Ms = {anti_overturning_moment:.3f}/{abs(overturning_moment):.3f} = {safety_factor_display} "
            f"{'≥' if is_compliant else '<'} γ0γd = {importance_factor} × {gamma_d} = {required_safety_factor:.2f}，"
            f"{'满足' if is_compliant else '不满足'} 《陆上风电场工程风电机组基础设计规范》 6.5.2 条规定。"
        )
        
        # 创建单个工况结果
        condition_result = AntiOverturningSingleConditionResult(
            condition_type=case_name,
            overturning_moment=abs(overturning_moment),
            anti_overturning_moment=anti_overturning_moment,
            safety_factor=safety_factor,
            gamma_0=importance_factor,
            gamma_d=gamma_d,
            required_safety_factor=required_safety_factor,
            is_compliant=is_compliant,
            check_details=check_details
        )
        
        results[case_name] = condition_result
        
        logger.info(f"{case_name}: Ms={abs(overturning_moment):.2f}, Mr={anti_overturning_moment:.2f}, "
                   f"安全系数={safety_factor:.3f}, {'满足' if is_compliant else '不满足'}")

    async def calculate_anti_sliding_analysis(
        self, 
        geometry: FoundationGeometry, 
        load_calculation_results: Dict[str, Any],
        self_weight_result: SelfWeightResult,
        importance_factor: float = 1.1
    ) -> AntiSlidingAnalysisResult:
        """
        基础抗滑验算
        
        Args:
            geometry: 基础几何信息
            load_calculation_results: 荷载计算结果
            self_weight_result: 基础自重计算结果
            importance_factor: 重要性系数γ0（从设计参数中获取）
            
        Returns:
            AntiSlidingAnalysisResult: 基础抗滑验算结果
        """
        try:
            logger.info("开始基础抗滑验算")
            
            # 摩擦系数μ固定为0.3，实际应取自土层信息中的摩擦系数
            mu = 0.3
            # 设计系数γd为1.3（抗滑验算的设计系数）
            gamma_d = 1.3
            
            # 从荷载计算结果中获取详细计算数据
            detailed_calculations = load_calculation_results.get("detailed_calculations", [])
            
            # 查找4种工况的计算结果
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
            
            # 计算各工况的抗滑验算
            results = {}
            
            # 处理正常工况和极端工况（从detailed_calculations获取）
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
                    
                    anti_sliding_force = total_vertical_load * mu
                else:
                    logger.warning(f"{case_name} 未找到standard组合数据")
                    sliding_force = 0
                    anti_sliding_force = 0
                    total_vertical_load = 0
                
                # 计算并存储结果
                self._calculate_single_sliding_condition_result(
                    case_name, sliding_force, anti_sliding_force, total_vertical_load,
                    importance_factor, mu, gamma_d, results
                )
            
            # 处理地震工况（从load_conditions获取，使用估算方法）
            for case_name, case_data in seismic_conditions.items():
                logger.info(f"计算 {case_name} 的抗滑验算（估算方法）")
                
                # 滑动力Fs = Fx (kN) 
                sliding_force = case_data.get("Fx", 0)
                
                # 抗滑力Fr = (Nk + Gk) * μ （使用估算的总重量）
                vertical_load = case_data.get("Fz", 0)  # Nk
                foundation_weight = self_weight_result.total_weight  # Gk
                total_vertical_load = abs(vertical_load) + foundation_weight  # Nk + Gk
                anti_sliding_force = total_vertical_load * mu
                
                # 计算并存储结果
                self._calculate_single_sliding_condition_result(
                    case_name, sliding_force, anti_sliding_force, total_vertical_load,
                    importance_factor, mu, gamma_d, results
                )
            
            # 检查所有工况是否都满足要求
            overall_compliance = all(result.is_compliant for result in results.values())
            
            # 确保有4种工况的结果，如果没有则创建默认结果
            default_result = AntiSlidingSingleConditionResult(
                condition_type="未找到",
                sliding_force=0.0,
                anti_sliding_force=0.0,
                gamma_0_Fs=0.0,
                mu=mu,
                gamma_0=importance_factor,
                is_compliant=False,
                check_details="工况数据未找到"
            )
            
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

    def _calculate_single_sliding_condition_result(
        self,
        case_name: str,
        sliding_force: float,
        anti_sliding_force: float,
        total_vertical_load: float,
        importance_factor: float,
        mu: float,
        gamma_d: float,
        results: dict
    ):
        """
        计算单个工况的抗滑验算结果
        
        Args:
            case_name: 工况名称
            sliding_force: 滑动力Fs
            anti_sliding_force: 抗滑力Fr
            total_vertical_load: 总竖向力(Nk + Gk)
            importance_factor: 重要性系数γ0
            mu: 摩擦系数μ
            gamma_d: 设计系数γd
            results: 结果字典
        """
        # γ0 * Fs
        gamma_0_Fs = importance_factor * abs(sliding_force)
        
        # 设计值 = Fr / γd
        design_anti_sliding_force = anti_sliding_force / gamma_d
        
        # 判断是否满足规范要求: γ0 * Fs ≤ Fr / γd
        is_compliant = gamma_0_Fs <= design_anti_sliding_force
        
        # 生成检查详情
        check_details = (
            f"抗滑力：Fr = (Nk + Gk)μ = {total_vertical_load:.3f} × {mu} = {anti_sliding_force:.3f}kN，"
            f"滑动力：Fs = {abs(sliding_force):.1f}kN，"
            f"γ0Fs = {importance_factor} × {abs(sliding_force):.1f} = {gamma_0_Fs:.1f}kN "
            f"{'≤' if is_compliant else '>'} 1/γd Fr = 1/{gamma_d} × {anti_sliding_force:.3f} = {design_anti_sliding_force:.2f}kN，"
            f"{'满足' if is_compliant else '不满足'}《陆上风电场工程风电机组基础设计规范》 6.5.2 条规定。"
        )
        
        # 创建单个工况结果
        condition_result = AntiSlidingSingleConditionResult(
            condition_type=case_name,
            sliding_force=abs(sliding_force),
            anti_sliding_force=anti_sliding_force,
            gamma_0_Fs=gamma_0_Fs,
            mu=mu,
            gamma_0=importance_factor,
            is_compliant=is_compliant,
            check_details=check_details
        )
        
        results[case_name] = condition_result
        
        logger.info(f"{case_name}: Fs={abs(sliding_force):.2f}, Fr={anti_sliding_force:.2f}, "
                   f"γ0Fs={gamma_0_Fs:.2f}, {'满足' if is_compliant else '不满足'}")

    async def calculate_stiffness_analysis(
        self,
        geometry: FoundationGeometry,
        soil_layers: List[SoilLayer],
        stiffness_requirements: StiffnessRequirements
    ) -> StiffnessAnalysisResult:
        """
        刚度验算
        
        根据图片中的公式计算地基旋转动态刚度和水平动态刚度，并验证是否满足要求
        
        公式：
        - 地基旋转动态刚度：Kφ,dyn = (4(1-2ν))/(3(1-ν)²) × R³ × Es,dyn
        - 地基水平动态刚度：KH,dyn = 2 × (1-2ν)/(1-ν)² × R × Es,dyn
        
        其中：
        - ν: 泊松比
        - R: 基础半径 (m)
        - Es,dyn: 动态压缩模量 (MPa) = 动态压缩模量 × 基础半径 × 10⁶
        
        Args:
            geometry: 基础几何信息
            soil_layers: 土层信息列表（使用第一个土层的压缩模量和泊松比）
            stiffness_requirements: 刚度要求参数
            
        Returns:
            StiffnessAnalysisResult: 刚度验算结果
        """
        try:
            logger.info("开始刚度验算")
            
            # 从参数中获取计算所需的值
            R = geometry.base_radius  # 基础半径 (m)
            # poisson_ratio = base_parameters.poisson_ratio  # 泊松比 ν
            # dynamic_compression_modulus = base_parameters.dynamic_compression_modulus  # 动态压缩模量 (MPa)
            # 使用第一个土层的参数
            first_soil_layer = soil_layers[0]
            poisson_ratio = first_soil_layer.poisson_ratio  # 泊松比 ν
            dynamic_compression_modulus = first_soil_layer.compression_modulus * 10 # 动态压缩模量 (MPa)
            
            # 计算 Es,dyn = 动态压缩模量 × 10⁶ (Pa)
            # 根据图片显示：Es,dyn = 150.0 × 10⁶ = 1.8 × 10⁹ Pa
            # 这里的150.0是动态压缩模量
            Es_dyn = dynamic_compression_modulus * 1e6  # 转换为Pa
            
            logger.info(f"计算参数: R={R}m, ν={poisson_ratio}, Es_dyn={Es_dyn:.2e}Pa")
            
            # 计算地基旋转动态刚度 Kφ,dyn
            # Kφ,dyn = (4(1-2ν))/(3(1-ν)²) × R³ × Es,dyn
            numerator_rot = 4 * (1 - 2 * poisson_ratio)
            denominator_rot = 3 * (1 - poisson_ratio) ** 2
            if denominator_rot == 0:
                logger.warning(f"分母为零: denominator_rot = 3 * (1 - {poisson_ratio})² = 0")
                calculated_rotational_stiffness = 0.0
            else:
                calculated_rotational_stiffness = (numerator_rot / denominator_rot) * (R ** 3) * Es_dyn
            
            logger.info(f"旋转动态刚度计算: ({numerator_rot:.3f}/{denominator_rot:.3f}) × {R}³ × {Es_dyn:.2e} = {calculated_rotational_stiffness:.3e}")
            
            # 计算地基水平动态刚度 KH,dyn
            # KH,dyn = 2 × (1-2ν)/(1-ν)² × R × Es,dyn
            numerator_hor = 1 - 2 * poisson_ratio
            denominator_hor = (1 - poisson_ratio) ** 2
            if denominator_hor == 0:
                logger.warning(f"分母为零: denominator_hor = (1 - {poisson_ratio})² = 0")
                calculated_horizontal_stiffness = 0.0
            else:
                calculated_horizontal_stiffness = 2 * (numerator_hor / denominator_hor) * R * Es_dyn
            
            logger.info(f"水平动态刚度计算: 2 × ({numerator_hor:.3f}/{denominator_hor:.3f}) × {R} × {Es_dyn:.2e} = {calculated_horizontal_stiffness:.3e}")
            
            # 获取要求的刚度值
            required_rotational = stiffness_requirements.required_rotational_stiffness
            required_horizontal = stiffness_requirements.required_horizontal_stiffness
            
            # 验证旋转刚度是否满足要求
            rotational_compliant = calculated_rotational_stiffness >= required_rotational
            rotational_details = (
                f"地基旋转动态刚度计算公式：Kφ,dyn = (4(1-2ν))/(3(1-ν)²) × R³ × Es,dyn = "
                f"({numerator_rot:.3f})/({denominator_rot:.3f}) × {R:.1f}³ × {Es_dyn:.2E} = "
                f"{calculated_rotational_stiffness:.3E} N·m/rad {'≥' if rotational_compliant else '<'} "
                f"{required_rotational:.1E} N·m/rad，{'满足' if rotational_compliant else '不满足'}刚度要求。"
            )
            
            # 验证水平刚度是否满足要求
            horizontal_compliant = calculated_horizontal_stiffness >= required_horizontal
            horizontal_details = (
                f"地基水平动态刚度计算公式：KH,dyn = 2 × (1-2ν)/(1-ν)² × R × Es,dyn = "
                f"2 × ({numerator_hor:.3f})/({denominator_hor:.3f}) × {R:.1f} × {Es_dyn:.2E} = "
                f"{calculated_horizontal_stiffness:.3E} N/m {'≥' if horizontal_compliant else '<'} "
                f"{required_horizontal:.1E} N/m，{'满足' if horizontal_compliant else '不满足'}刚度要求。"
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
            
            logger.info(f"刚度验算完成: 旋转刚度{'满足' if rotational_compliant else '不满足'}, "
                       f"水平刚度{'满足' if horizontal_compliant else '不满足'}, "
                       f"整体符合性: {overall_compliance}")
            
            return result
            
        except Exception as e:
            logger.error(f"刚度验算失败: {str(e)}")
            raise ValueError(f"刚度验算失败: {str(e)}")

    async def calculate_shear_strength_analysis(
        self,
        geometry: FoundationGeometry,
        load_calculation_results: Dict[str, Any],
        self_weight_result: SelfWeightResult,
        material: MaterialProperties = None,
        reinforcement_diameter: float = 20.0,
        importance_factor: float = 1.1
    ) -> ShearStrengthAnalysisResult:
        """
        基础抗剪强度计算（多工况验算）
        
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
        
        Args:
            geometry: 基础几何信息
            load_calculation_results: 荷载计算结果
            self_weight_result: 自重计算结果
            material: 材料属性信息（包含保护层厚度和抗拉强度）
            reinforcement_diameter: 钢筋直径(mm)，默认20mm
            importance_factor: 重要性系数γ0，默认1.1
            
        Returns:
            ShearStrengthAnalysisResult: 剪切强度分析结果
        """
        try:
            logger.info("开始基础抗剪强度计算（多工况验算）")
            
            # ===== 第一部分：保留原有的基础抗剪强度计算逻辑 =====
            
            # 参数转换：将m转换为mm
            base_radius_mm = geometry.base_radius * 1000  # m转mm
            column_radius_mm = geometry.column_radius * 1000  # m转mm
            edge_height_mm = geometry.edge_height * 1000  # m转mm
            frustum_height_mm = geometry.frustum_height * 1000  # m转mm
            
            # 获取混凝土底面保护层厚度
            bottom_cover_mm = material.bottom_cover if material else 50.0  # mm
            
            # 1. 计算h0（有效截面高度）
            h0 = edge_height_mm + frustum_height_mm - bottom_cover_mm - reinforcement_diameter / 2
            
            # 当h0>=2000mm时，取2000mm
            if h0 >= 2000.0:
                h0_for_calculation = 2000.0
            
            logger.info(f"计算h0: {edge_height_mm}mm + {frustum_height_mm}mm - {bottom_cover_mm}mm - {reinforcement_diameter/2}mm = {h0}mm")
            
            # 2. 计算受剪切截面宽度b
            # b = (1 - 基础底板棱台高度/2H0) * [2√(基础底板半径² - 台柱半径²)]
            h0 = h0 / 1000; #转换成米
            term1 = 1 - geometry.frustum_height / (2 * h0)
            term2 = 2 * math.sqrt(geometry.base_radius**2 - geometry.column_radius**2)
            shear_width = term1 * term2
            
            # 3. 计算高度影响系数Bh
            # Bh = ⁴√(基础边缘高度/H0)
            height_factor = (edge_height_mm / h0_for_calculation) ** 0.25
            
            logger.info(f"计算高度影响系数Bh: ⁴√({edge_height_mm}mm / {h0_for_calculation}mm) = {height_factor}")
            
            # 4. 计算受剪切面积A0
            # A0 = b * H0
            shear_area = shear_width * h0  # mm²
            
            logger.info(f"计算受剪切面积A0: {shear_width}m * {h0}m = {shear_area}m²")
            
            # 5. 计算剪切承载力Vr
            # Vr = 0.7 * Bh * Ft * A0
            # 获取混凝土抗拉强度设计值
            ft = material.ft*1000 if material else 1.71*1000  # N/mm²，默认使用C40混凝土的抗拉强度，转换成kN/m²
            
            # 计算剪切承载力（N）
            shear_capacity = 0.7 * height_factor * ft * shear_area
            
            logger.info(f"计算剪切承载力Vr: 0.7 * {height_factor} * {ft}kN/m² * {shear_area}m² = {shear_capacity}kN")
            
            # ===== 第二部分：新增的各工况剪力计算和比较验算 =====
            
            # 计算S1和S2（使用m为单位）
            R = geometry.base_radius  # 基础底板半径(m)
            R2 = geometry.column_radius  # 台柱半径(m)
            
            # S1 = cos⁻¹(r/R)/π * πR²
            cos_inverse_term = math.acos(R2 / R)  # cos⁻¹(r/R)
            s1 = (cos_inverse_term / math.pi) * (math.pi * R**2)
            
            # S2 = R²tan(cos⁻¹(r/R))
            s2 = R2**2 * math.tan(cos_inverse_term)
            
            logger.info(f"计算S1: cos⁻¹({R2}/{R})/π × πR² = {cos_inverse_term:.4f}/π × π×{R}² = {s1:.2f} m²")
            logger.info(f"计算S2: R²tan(cos⁻¹(r/R)) = {R}² × tan({cos_inverse_term:.4f}) = {s2:.2f} m²")
            
            # 初始化各工况结果
            condition_results = {}
            overall_compliance = True
            
            # 从荷载计算结果中获取详细计算数据（参照抗滑验算的逻辑）
            detailed_calculations = load_calculation_results.get("detailed_calculations", [])
            
            # 查找4种工况的计算结果
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
            
            # 工况映射
            condition_mapping = {
                "正常工况": ("正常工况", "normal_condition"),
                "极端工况": ("极端工况", "extreme_condition"), 
                "多遇地震工况": ("多遇地震工况", "frequent_seismic_condition"),
                "罕遇地震工况": ("罕遇地震工况", "rare_seismic_condition")
            }
            
            # 处理正常工况和极端工况（从detailed_calculations获取）
            for case_name, case_data in condition_data.items():
                condition_name, result_key = condition_mapping[case_name]
                logger.info(f"开始计算{condition_name}剪力验算")
                
                # 从standard组合中获取Pj数据（参照抗滑分析逻辑）
                standard_combination = case_data.get("combinations", {}).get("standard", {})
                
                if standard_combination and "Pj" in standard_combination:
                    pj_data = standard_combination.get("Pj", {})
                    if isinstance(pj_data, dict) and "value" in pj_data:
                        pj = float(pj_data["value"])
                    elif isinstance(pj_data, (int, float)):
                        pj = float(pj_data)
                    else:
                        pj = None
                else:
                    logger.warning(f"{condition_name}未找到standard组合中的Pj数据")
                    pj = None
                
                if pj is None:
                    logger.warning(f"{condition_name}未找到Pj值，跳过此工况")
                    # 创建一个默认的结果
                    condition_result = ShearStrengthSingleConditionResult(
                        condition_type=condition_name,
                        shear_force=0.0,
                        shear_capacity=shear_capacity,
                        gamma_0_V=0.0,
                        gamma_0=importance_factor,
                        pj=0.0,
                        s1=s1,
                        s2=s2,
                        is_compliant=True,  # 无数据默认为通过
                        check_details=f"{condition_name}：无Pj数据，无法计算剪力。"
                    )
                    condition_results[result_key] = condition_result
                    continue
                
                # 计算剪力 V = Pj(S1 - S2)，注意单位转换
                # Pj单位为kPa，S1-S2单位为m²，结果V单位为kN
                shear_force_raw = pj * (s1 - s2)  # kN
                
                # 取绝对值，因为剪力应该为正值
                shear_force = abs(shear_force_raw)
                
                # 计算 γ0*V
                gamma_0_V = importance_factor * shear_force
                
                # 判断是否满足规范：γ0*V ≤ Vr
                is_compliant = gamma_0_V <= shear_capacity
                
                if not is_compliant:
                    overall_compliance = False
                
                # 生成检查详情
                check_details = f"γ_0 V={importance_factor}×{shear_force:.3f}={gamma_0_V:.3f}kN{'≤' if is_compliant else '>'}{shear_capacity:.2f}kN， {'满足' if is_compliant else '不满足'}《陆上风电场工程风电机组基础设计规范》 7.2.9条规定。"
                
                # 创建单工况结果
                condition_result = ShearStrengthSingleConditionResult(
                    condition_type=condition_name,
                    shear_force=shear_force,
                    shear_capacity=shear_capacity,
                    gamma_0_V=gamma_0_V,
                    gamma_0=importance_factor,
                    pj=pj,
                    s1=s1,
                    s2=s2,
                    is_compliant=is_compliant,
                    check_details=check_details
                )
                
                condition_results[result_key] = condition_result
                
                logger.info(f"{condition_name}: Pj={pj:.2f}kPa, V={shear_force:.2f}kN, γ0V={gamma_0_V:.2f}kN, {'满足' if is_compliant else '不满足'}")
            
            # 处理地震工况（从load_conditions获取，使用估算方法）
            for case_name, case_data in seismic_conditions.items():
                condition_name, result_key = condition_mapping[case_name]
                logger.info(f"开始计算{condition_name}剪力验算")
                
                # 地震工况暂时设置默认Pj值，实际应该从地震荷载计算中获取
                # 这里参照抗滑分析的做法，设置默认值
                pj = 50.0  # kPa，默认值
                logger.warning(f"{condition_name}使用默认Pj值: {pj}kPa")
                
                # 计算剪力 V = Pj(S1 - S2)，注意单位转换
                shear_force_raw = pj * (s1 - s2)  # kN
                shear_force = abs(shear_force_raw)
                
                # 计算 γ0*V
                gamma_0_V = importance_factor * shear_force
                
                # 判断是否满足规范：γ0*V ≤ Vr
                is_compliant = gamma_0_V <= shear_capacity
                
                if not is_compliant:
                    overall_compliance = False
                
                # 生成检查详情
                check_details = f"γ_0 V={importance_factor}×{shear_force:.3f}={gamma_0_V:.3f}kN{'≤' if is_compliant else '>'}{shear_capacity:.2f}kN， {'满足' if is_compliant else '不满足'}《陆上风电场工程风电机组基础设计规范》 7.2.9条规定。（使用默认Pj值）"
                
                # 创建单工况结果
                condition_result = ShearStrengthSingleConditionResult(
                    condition_type=condition_name,
                    shear_force=shear_force,
                    shear_capacity=shear_capacity,
                    gamma_0_V=gamma_0_V,
                    gamma_0=importance_factor,
                    pj=pj,
                    s1=s1,
                    s2=s2,
                    is_compliant=is_compliant,
                    check_details=check_details
                )
                
                condition_results[result_key] = condition_result
                logger.info(f"{condition_name}: Pj={pj:.2f}kPa(默认值), V={shear_force:.2f}kN, γ0V={gamma_0_V:.2f}kN, {'满足' if is_compliant else '不满足'}")
            
            # 创建最终结果对象（构造剪切承载力对象）
            result = ShearStrengthAnalysisResult(
                shear_capacity={
                    "h0": h0,
                    "shear_width": shear_width,
                    "height_factor": height_factor,
                    "shear_area": shear_area,
                    "shear_capacity": shear_capacity,
                },
                normal_condition=condition_results.get("normal_condition"),
                extreme_condition=condition_results.get("extreme_condition"),
                frequent_seismic_condition=condition_results.get("frequent_seismic_condition"),
                rare_seismic_condition=condition_results.get("rare_seismic_condition"),
                overall_compliance=overall_compliance
            )
            
            logger.info(f"基础抗剪强度计算完成，整体符合性: {overall_compliance}")
            return result
            
        except Exception as e:
            logger.error(f"基础抗剪强度计算失败: {str(e)}")
            raise ValueError(f"基础抗剪强度计算失败: {str(e)}")

    async def calculate_anti_punching_analysis(
        self,
        geometry: FoundationGeometry,
        load_calculation_results: Dict[str, Any],
        self_weight_result: SelfWeightResult,
        material: MaterialProperties,
        reinforcement_diameter: float = 20.0,
        importance_factor: float = 1.1
    ) -> AntiPunchingAnalysisResult:
        """
        基础抗冲切验算
        
        Args:
            geometry: 基础几何信息
            load_calculation_results: 荷载计算结果
            self_weight_result: 基础自重计算结果
            material: 材料属性
            reinforcement_diameter: 钢筋直径(mm)，默认20，可取15
            importance_factor: 重要性系数γ0（从设计参数中获取）
            
        Returns:
            AntiPunchingAnalysisResult: 基础抗冲切验算结果
        """
        try:
            logger.info("开始基础抗冲切验算")
            
            # 1. 计算有效截面高度h0（与抗剪强度分析保持一致）
            # h0 = 基础边缘高度 + 基础底板棱台高度 - 基础底板底面混凝土保护层厚度 - 1/2钢筋直径
            
            # 参数转换：将m转换为mm
            edge_height_mm = geometry.edge_height * 1000  # m转mm
            frustum_height_mm = geometry.frustum_height * 1000  # m转mm
            
            # 获取混凝土底面保护层厚度
            bottom_cover_mm = material.bottom_cover if material else 50.0  # mm
            half_rebar_diameter = reinforcement_diameter / 2
            
            h0 = edge_height_mm + frustum_height_mm - bottom_cover_mm - half_rebar_diameter
            logger.info(f"计算有效截面高度h0: {edge_height_mm}mm + {frustum_height_mm}mm - {bottom_cover_mm}mm - {half_rebar_diameter}mm = {h0}mm")
            
            # 2. 计算高度影响系数Bhp
            if h0 <= 800:
                bhp = 1.0
            elif h0 >= 2000:
                bhp = 0.9
            else:
                # 线性内插
                bhp = 1.0 - (h0 - 800) / (2000 - 800) * (1.0 - 0.9)
            
            logger.info(f"计算高度影响系数Bhp: h0={h0}mm，Bhp={bhp:.3f}")
            
            # 3. 计算冲切破坏椎体上截面周长Bt
            bt = 2 * math.pi * geometry.column_radius
            logger.info(f"计算冲切破坏椎体上截面周长Bt: 2π×{geometry.column_radius}m = {bt:.2f}m")
            
            # 4. 计算R1+H0
            R1_plus_H0 = geometry.base_radius + h0 / 1000  # h0转换为m
            logger.info(f"计算R1+H0: {geometry.base_radius}m + {h0/1000}m = {R1_plus_H0:.3f}m")
            
            # 5. 计算冲切破坏椎体下截面周长Bb
            bb = 2 * math.pi * R1_plus_H0
            logger.info(f"计算冲切破坏椎体下截面周长Bb: 2π×{R1_plus_H0}m = {bb:.2f}m")
            
            # 6. 计算抗冲切承载力Fr
            # Fr = 0.35 * Bhp * 轴心抗拉强度设计值Ft * (Bt + Bb) * H0
            ft = material.ft * 1000 if material else 1.71 * 1000  # N/mm²，转换成kN/m²
            h0_m = h0 / 1000  # 转换为m
            punching_capacity = 0.35 * bhp * ft * (bt + bb) * h0_m  # 转换为kN
            
            logger.info(f"计算抗冲切承载力Fr: 0.35 × {bhp:.3f} × {ft}kN/m² × ({bt:.2f}+{bb:.2f})/{h0_m:.3f} = {punching_capacity:.2f}kN")
            
            # 7. 从荷载计算结果中获取各工况的冲切力
            detailed_calculations = load_calculation_results.get("detailed_calculations", [])
            load_conditions = load_calculation_results.get("load_conditions", [])
            
            # 查找4种工况的计算结果
            condition_results = {}
            overall_compliance = True
            
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
                
                self._calculate_single_punching_condition_result(
                    case_name, case_data, geometry, h0, punching_capacity, importance_factor, condition_results
                )
                
                if not condition_results[case_name].is_compliant:
                    overall_compliance = False
            
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
                loads = case_data.get("loads", {})
                foundation_weight = abs(loads.get("foundation_total_weight", 0))
                vertical_load = abs(loads.get("vertical_force", 0))
                
                # 估算Pj = (基础自重 + 竖向荷载) / 基础底板面积
                base_area = math.pi * geometry.base_radius**2
                estimated_pj = (foundation_weight + vertical_load) / base_area if base_area > 0 else 0
                
                # 构造简化的condition_data结构
                simplified_condition_data = {
                    "combinations": {
                        "standard": {
                            "Pj": {"value": estimated_pj, "unit": "kPa", "description": "估算基础底面净反力"}
                        }
                    }
                }
                
                self._calculate_single_punching_condition_result(
                    case_name, simplified_condition_data, geometry, h0, punching_capacity, importance_factor, condition_results
                )
                
                if not condition_results[case_name].is_compliant:
                    overall_compliance = False
            
            # 8. 创建最终结果对象（构造抗冲切承载力对象）
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

    def _calculate_single_punching_condition_result(
        self,
        case_name: str,
        condition_data: Dict[str, Any],
        geometry: FoundationGeometry,
        h0: float,
        punching_capacity: float,
        importance_factor: float,
        results: dict
    ):
        """
        计算单个工况的抗冲切验算结果
        
        使用公式：Fl = 基础底面净反力Pj * π * [基础底板半径² - (台柱半径 + 高度H0)²]
        验算：γ_0 * F_l ≤ 抗冲切承载力Fr
        """
        
        # 从standard组合中获取Pj数据
        standard_combination = condition_data.get("combinations", {}).get("standard", {})
        
        if standard_combination and "Pj" in standard_combination:
            pj_data = standard_combination.get("Pj", {})
            if isinstance(pj_data, dict) and "value" in pj_data:
                pj = float(pj_data["value"])  # kPa
            elif isinstance(pj_data, (int, float)):
                pj = float(pj_data)  # kPa
            else:
                pj = None
        else:
            logger.warning(f"{case_name}未找到standard组合中的Pj数据")
            pj = None
        
        if pj is None:
            logger.warning(f"{case_name}未找到Pj值，跳过此工况")
            # 创建一个默认的结果
            condition_result = AntiPunchingSingleConditionResult(
                condition_type=case_name,
                punching_force=0.0,
                punching_capacity=punching_capacity,
                gamma_0_F=0.0,
                gamma_0=importance_factor,
                is_compliant=True,  # 无数据默认为通过
                check_details=f"{case_name}：无Pj数据，无法计算冲切力。"
            )
            results[case_name] = condition_result
            return
        
        # 计算冲切力：Fl = Pj * π * [R1² - (r1 + H0)²]
        # R1: 基础底板半径 (m)
        # r1: 台柱半径 (m) 
        # H0: 有效截面高度 (m)
        R1 = geometry.base_radius  # m
        r1 = geometry.column_radius  # m
        H0 = h0 / 1000  # 从mm转换为m
        
        # 计算冲切面积 (m²)
        punching_area = math.pi * (R1**2 - (r1 + H0)**2)
        
        # 计算冲切力：Fl = Pj (kPa) * 冲切面积 (m²) = kN
        punching_force = pj * punching_area
        
        # 计算γ0Fl
        gamma_0_F = importance_factor * punching_force
        
        # 判断是否满足要求：γ0Fl ≤ Fr
        is_compliant = gamma_0_F <= punching_capacity
        
        # 生成检查详情，按照用户要求的格式
        check_details = (
            f"γ_0 F_l={punching_force:.3f}×{importance_factor}={gamma_0_F:.3f}kN"
            f"{'≤' if is_compliant else '>'}{punching_capacity:.1f}kN，"
            f"{'满足' if is_compliant else '不满足'}《陆上风电场工程风电机组基础设计规范》7.2.7条规定。"
        )
        
        # 创建单个工况结果
        condition_result = AntiPunchingSingleConditionResult(
            condition_type=case_name,
            punching_force=punching_force,
            punching_capacity=punching_capacity,
            gamma_0_F=gamma_0_F,
            gamma_0=importance_factor,
            is_compliant=is_compliant,
            check_details=check_details
        )
        
        results[case_name] = condition_result
        
        logger.info(f"{case_name}: Pj={pj:.2f}kPa, 冲切面积={punching_area:.3f}m², "
                   f"Fl={punching_force:.2f}kN, γ0Fl={gamma_0_F:.2f}kN, "
                   f"Fr={punching_capacity:.2f}kN, {'满足' if is_compliant else '不满足'}")

    def _get_standard_combination_from_calculation(self, calc: Dict[str, Any], load_case: str) -> Optional[Dict[str, Any]]:
        """
        从荷载计算结果中获取standard组合数据
        
        Args:
            calc: 单个工况的计算结果
            load_case: 工况名称
            
        Returns:
            Optional[Dict[str, Any]]: standard组合数据，如果失败返回None
        """
        try:
            combinations = calc.get("combinations", {})
            standard_combination = combinations.get("standard", {})
            
            if not standard_combination:
                logger.warning(f"{load_case} 未找到standard组合数据")
                return None
                
            return standard_combination
            
        except Exception as e:
            logger.error(f"获取{load_case}的standard组合数据时发生错误: {str(e)}")
            return None

    def _extract_pk_value_from_calculation(self, calc: Dict[str, Any], load_case: str) -> Optional[Dict[str, float]]:
        """
        从荷载计算结果中提取pk、Pkmax和Pkmin值
        
        Args:
            calc: 单个工况的计算结果
            load_case: 工况名称
            
        Returns:
            Optional[Dict[str, float]]: 包含pk、Pkmax和Pkmin的字典，如果失败返回None
            格式: {"pk": value, "Pkmax": value, "Pkmin": value}
        """
        try:
            # 获取standard组合数据
            standard_combination = self._get_standard_combination_from_calculation(calc, load_case)
            if not standard_combination:
                return None
            
            result = {}
            
            # 提取pk值 (保留原有逻辑)
            simple_pk_data = standard_combination.get("simple_pk", {})
            if simple_pk_data:
                pk_data = simple_pk_data.get("pk", {})
                if isinstance(pk_data, dict):
                    pk_value = pk_data.get("value")
                else:
                    pk_value = pk_data
                
                if pk_value is not None and pk_value > 0:
                    result["pk"] = float(pk_value)
                else:
                    logger.warning(f"{load_case} 的pk值无效: {pk_value}")
                    # 不返回None，继续尝试提取Pkmax和Pkmin
            else:
                logger.warning(f"{load_case} 未找到simple_pk数据")
            
            # 提取Pkmax
            pkmax_data = standard_combination.get("Pkmax", {})
            if isinstance(pkmax_data, dict):
                pkmax_value = pkmax_data.get("value")
                if pkmax_value is not None:
                    result["Pkmax"] = float(pkmax_value)
                else:
                    logger.warning(f"{load_case} 的Pkmax数据格式不正确: {pkmax_data}")
            else:
                logger.warning(f"{load_case} 未找到Pkmax数据或格式不正确")
            
            # 提取Pkmin
            pkmin_data = standard_combination.get("Pkmin", {})
            if isinstance(pkmin_data, dict):
                pkmin_value = pkmin_data.get("value")
                if pkmin_value is not None:
                    result["Pkmin"] = float(pkmin_value)
                else:
                    logger.warning(f"{load_case} 的Pkmin数据格式不正确: {pkmin_data}")
            else:
                logger.warning(f"{load_case} 未找到Pkmin数据或格式不正确")
            
            # 检查是否至少提取到一个有效值
            if not result:
                logger.warning(f"{load_case} 未能提取到任何有效的压力值")
                return None
            
            # 记录提取结果
            extracted_values = []
            if "pk" in result:
                extracted_values.append(f"pk={result['pk']:.3f}kPa")
            if "Pkmax" in result:
                extracted_values.append(f"Pkmax={result['Pkmax']:.3f}kPa")
            if "Pkmin" in result:
                extracted_values.append(f"Pkmin={result['Pkmin']:.3f}kPa")
            
            logger.info(f"{load_case} 成功提取压力值: {', '.join(extracted_values)}")
            return result
                
        except Exception as e:
            logger.error(f"从{load_case}提取压力值时发生错误: {str(e)}")
            return None

    def _convert_soil_layers_to_dict_format(self, soil_layers: List[Any]) -> List[Dict[str, Any]]:
        """
        将土层数据转换为字典格式
        
        Args:
            soil_layers: 土层信息列表，可能包含Pydantic模型或字典
            
        Returns:
            List[Dict[str, Any]]: 转换后的土层字典列表
        """
        try:
            soil_layers_dict = []
            
            # 处理单个土层对象的情况（从soil_layer_selector返回的是单个对象）
            if not isinstance(soil_layers, list):
                soil_layers = [soil_layers]
            
            for layer in soil_layers:
                if hasattr(layer, '__dict__'):
                    # 如果是Pydantic模型，转换为字典
                    layer_dict = {
                        'layerName': layer.layer_name,
                        'elevation': layer.elevation,
                        'thickness': layer.thickness,
                        'density': layer.density,
                        'compression_modulus': layer.compression_modulus,
                        'fak': layer.fak
                    }
                else:
                    # 如果已经是字典，直接使用
                    layer_dict = layer
                soil_layers_dict.append(layer_dict)
            
            logger.info(f"成功转换{len(soil_layers_dict)}个土层数据为字典格式")
            return soil_layers_dict
            
        except Exception as e:
            logger.error(f"转换土层数据格式时发生错误: {str(e)}")
            raise

    async def calculate_settlement_analysis(
        self,
        geometry: FoundationGeometry,
        soil_layers: List[Any],
        load_calculation_results: Dict[str, Any],
        groundwater_depth: Optional[float] = None,
        allowable_settlement: float = 100.0,
        allowable_inclination: float = 0.003
    ) -> "SettlementAnalysisResult":
        """
        地基变形验算
        
        根据《陆上风电场工程风电机组基础设计规范》6.4.1条、6.4.2条、6.4.3条进行
        沉降和倾斜变形验算
        
        Args:
            geometry: 基础几何信息
            soil_layers: 土层信息列表
            load_calculation_results: 荷载计算结果
            groundwater_depth: 地下水埋深(m)，None表示无地下水
            allowable_settlement: 允许沉降(mm)，默认100mm
            allowable_inclination: 允许倾斜率，默认0.003
            
        Returns:
            SettlementAnalysisResult: 简化的三层结构地基变形验算结果模型
        """
        
        try:
            # 转换土层数据格式
            soil_layers_dict = self._convert_soil_layers_to_dict_format(soil_layers)
            # 从load_calculation_results中提取各工况的地基压力
            detailed_calculations = load_calculation_results.get("detailed_calculations", [])
            # 只处理正常工况和极端工况
            target_load_cases = ["正常工况", "极端工况"]
            
            # 临时保存两个工况的结果
            normal_condition_payload: Optional[Dict[str, Any]] = None
            extreme_condition_payload: Optional[Dict[str, Any]] = None
            
            # 保存各个工况的合规性结果
            normal_settlement_compliant = True
            normal_inclination_compliant = True
            extreme_settlement_compliant = True
            extreme_inclination_compliant = True
            
            # 为每个工况构建沉降验算和倾斜验算结构
            for calc in detailed_calculations:
                load_case = calc.get("load_case")
                if load_case not in target_load_cases:
                    continue
                    
                pressure_values = self._extract_pk_value_from_calculation(calc, load_case)
                pk = pressure_values.get("pk")
                pkmax = pressure_values.get("Pkmax")
                pkmin = pressure_values.get("Pkmin")
                
                # 创建沉降分析器
                analyzer = SettlementAnalyzer(geometry, soil_layers_dict, pk, pkmax, pkmin, None, groundwater_depth, allowable_settlement, allowable_inclination)
                
                # 计算沉降和倾斜
                analyzer.calculate_settlement()
                analyzer.calculate_inclination()
                
                # 获取沉降验算和倾斜验算结果
                comprehensive_settlement_result = analyzer.get_comprehensive_settlement_result()
                comprehensive_inclination_result = analyzer.get_comprehensive_inclination_result()
                
                # 检查沉降和倾斜是否满足要求
                settlement_compliant = analyzer.final_settlement <= analyzer.allowable_settlement
                inclination_compliant = analyzer.inclination <= analyzer.allowable_inclination
                
                payload = {
                    "comprehensive_settlement_analysis": comprehensive_settlement_result,
                    "comprehensive_inclination_analysis": comprehensive_inclination_result
                }
                
                if load_case == "正常工况":
                    normal_condition_payload = payload
                    normal_settlement_compliant = settlement_compliant
                    normal_inclination_compliant = inclination_compliant
                elif load_case == "极端工况":
                    extreme_condition_payload = payload
                    extreme_settlement_compliant = settlement_compliant
                    extreme_inclination_compliant = inclination_compliant
                
                logger.info(f"{load_case} 地基变形验算完成")
            
            # 计算整体合规性（需要所有工况的沉降和倾斜都满足要求）
            overall_compliance = (
                normal_settlement_compliant and normal_inclination_compliant and
                extreme_settlement_compliant and extreme_inclination_compliant
            )
            
            # 创建最终结果模型（英文键名）
            result = SettlementAnalysisResult(
                calculation_type="地基变形验算",
                overall_compliance=overall_compliance,
                normal_condition=normal_condition_payload,
                extreme_condition=extreme_condition_payload
            )
            
            logger.info("地基变形验算完成")
            
            return result
            
        except Exception as e:
            logger.error(f"地基变形验算失败: {str(e)}")
            raise ValueError(f"地基变形验算失败: {str(e)}")

    
