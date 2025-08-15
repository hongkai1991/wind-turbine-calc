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
from app.services.anti_overturning_analyzer import AntiOverturningAnalyzer
from app.services.anti_sliding_analyzer import AntiSlidingAnalyzer
from app.services.stiffness_analyzer import StiffnessAnalyzer
from app.services.shear_strength_analyzer import ShearStrengthAnalyzer
from app.services.anti_punching_analyzer import AntiPunchingAnalyzer
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
                {"normal": allowed_detachment_area.normal, "extreme": allowed_detachment_area.extreme, "frequent_seismic": allowed_detachment_area.frequent_seismic}
            )
            
            logger.info(f"脱开面积验算分析完成: 整体符合={result.overall_compliance}")
            
            return result
            
        except Exception as e:
            logger.error(f"脱开面积验算分析失败: {str(e)}")
            # 返回默认的失败结果
            from app.schemas.detachment import DetachmentAreaResult
            
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

            default_frequent_seismic = DetachmentAreaResult(
                condition_type="多遇地震工况",
                compressed_height=0.0,
                foundation_area=foundation_area,
                detachment_area=0.0,
                detachment_ratio=0.0,
                allowed_ratio=allowed_detachment_area.get("frequent_seismic", 0.25),
                is_compliant=False,
                pressure_type="计算失败",
                check_details=f"脱开面积百分比:0.000/{foundation_area:.3f}=0.000≤{allowed_detachment_area.get('frequent_seismic', 0.25):.2f}，不满足《陆上风电场工程风电机组基础设计规范》 6.1.3条规定。"
            )

            return DetachmentAreaAnalysisResult(
                normal_condition=default_normal,
                extreme_condition=default_extreme,
                frequent_seismic_condition=default_frequent_seismic,
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

                elif load_case == "多遇地震工况":
                    # 提取多遇地震工况的地基压力
                    simple_pk = standard.get("simple_pk", {})
                    pek_seismic = simple_pk.get("pk", {}).get("value", 0.0)
                    pekmax_seismic = standard.get("Pkmax", {}).get("value", 0.0)
                    # 如果没有Pkmax，尝试获取Pmax
                    if pekmax_seismic == 0.0:
                        pekmax_seismic = standard.get("Pmax", {}).get("value", 0.0)

            logger.info(f"提取地基压力: 正常工况 pk={pk_normal:.3f}, pkmax={pkmax_normal:.3f}")
            logger.info(f"提取地基压力: 极端工况 pk={pk_extreme:.3f}, pkmax={pkmax_extreme:.3f}")
            logger.info(f"提取地基压力: 多遇地震工况 pk={pek_seismic:.3f}, pkmax={pekmax_seismic:.3f}")
            
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
                pek_seismic=pek_seismic,
                pekmax_seismic=pekmax_seismic
            )
            
            # 创建地基承载力验算器
            analyzer = BearingCapacityAnalyzer()
            
            # 执行地基承载力验算
            result = analyzer.analyze_bearing_capacity(params)
            
            # 组装简化响应：calculation_type由控制器注入，这里仅返回主体
            overall = result.normal_condition_compliant and result.extreme_condition_compliant and result.seismic_condition_compliant
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
                frequent_seismic_condition={
                    "pk": result.pek_seismic,
                    "pkmax": result.pekmax_seismic,
                    "check_details": result.seismic_check_details
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
        anti_overturning_analyzer = AntiOverturningAnalyzer()
        return await anti_overturning_analyzer.analyze(geometry, load_calculation_results, self_weight_result, importance_factor)

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
        anti_sliding_analyzer = AntiSlidingAnalyzer()
        return await anti_sliding_analyzer.analyze(
            geometry, load_calculation_results, self_weight_result, importance_factor
        )



    async def calculate_stiffness_analysis(
        self,
        geometry: FoundationGeometry,
        soil_layers: List[SoilLayer],
        stiffness_requirements: StiffnessRequirements
    ) -> StiffnessAnalysisResult:
        """
        刚度验算
        
        根据图片中的公式计算地基旋转动态刚度和水平动态刚度，并验证是否满足要求
        
        Args:
            geometry: 基础几何信息
            soil_layers: 土层信息列表（使用第一个土层的压缩模量和泊松比）
            stiffness_requirements: 刚度要求参数
            
        Returns:
            StiffnessAnalysisResult: 刚度验算结果
        """
        try:
            logger.info("开始刚度验算")
            
            # 创建刚度分析器
            stiffness_analyzer = StiffnessAnalyzer(geometry, soil_layers)
            
            # 执行刚度验算分析
            result = stiffness_analyzer.analyze_stiffness(stiffness_requirements)
            
            logger.info(f"刚度验算完成: 旋转刚度{'满足' if result.rotational_stiffness.is_compliant else '不满足'}, "
                       f"水平刚度{'满足' if result.horizontal_stiffness.is_compliant else '不满足'}, "
                       f"整体符合性: {result.overall_compliance}")
            
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
            
            # 创建抗剪强度分析器
            shear_strength_analyzer = ShearStrengthAnalyzer(
                geometry=geometry,
                load_calculation_results=load_calculation_results,
                self_weight_result=self_weight_result,
                material=material,
                reinforcement_diameter=reinforcement_diameter,
                importance_factor=importance_factor
            )
            
            # 执行抗剪强度分析
            result = shear_strength_analyzer.analyze_shear_strength()
            
            logger.info(f"基础抗剪强度计算完成，整体符合性: {result.overall_compliance}")
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
            
            # 创建抗冲切分析器
            anti_punching_analyzer = AntiPunchingAnalyzer(
                geometry=geometry,
                load_calculation_results=load_calculation_results,
                self_weight_result=self_weight_result,
                material=material,
                reinforcement_diameter=reinforcement_diameter,
                importance_factor=importance_factor
            )
            
            # 执行抗冲切验算分析
            result = anti_punching_analyzer.analyze()
            
            logger.info(f"基础抗冲切验算完成，整体符合性: {result.overall_compliance}")
            return result
            
        except Exception as e:
            logger.error(f"基础抗冲切验算失败: {str(e)}")
            raise ValueError(f"基础抗冲切验算失败: {str(e)}")

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
        allowable_settlement: float = 150.0,
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
            # 只处理正常工况、极端工况、多遇地震工况
            target_load_cases = ["正常工况", "极端工况","多遇地震工况"]
            
            # 临时保存两个工况的结果
            normal_condition_payload: Optional[Dict[str, Any]] = None
            extreme_condition_payload: Optional[Dict[str, Any]] = None
            frequent_seismic_condition_payload: Optional[Dict[str, Any]] = None

            # 保存各个工况的合规性结果
            normal_settlement_compliant = True
            normal_inclination_compliant = True
            extreme_settlement_compliant = True
            extreme_inclination_compliant = True
            frequent_seismic_settlement_compliant = True
            frequent_seismic_inclination_compliant = True
            
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
                elif load_case == "多遇地震工况":
                    frequent_seismic_condition_payload = payload
                    frequent_seismic_settlement_compliant = settlement_compliant
                    frequent_seismic_inclination_compliant = inclination_compliant

                logger.info(f"{load_case} 地基变形验算完成")
            
            # 计算整体合规性（需要所有工况的沉降和倾斜都满足要求）
            overall_compliance = (
                normal_settlement_compliant and normal_inclination_compliant and
                extreme_settlement_compliant and extreme_inclination_compliant and
                frequent_seismic_settlement_compliant and frequent_seismic_inclination_compliant
            )
            
            # 创建最终结果模型（英文键名）
            result = SettlementAnalysisResult(
                calculation_type="地基变形验算",
                overall_compliance=overall_compliance,
                normal_condition=normal_condition_payload,
                extreme_condition=extreme_condition_payload,
                frequent_seismic_condition=frequent_seismic_condition_payload
            )
            
            logger.info("地基变形验算完成")
            
            return result
            
        except Exception as e:
            logger.error(f"地基变形验算失败: {str(e)}")
            raise ValueError(f"地基变形验算失败: {str(e)}")

    
