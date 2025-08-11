"""
荷载计算器主类

该模块包含主要的荷载计算逻辑和协调其他子模块的工作。
"""

import math
from typing import Dict, List, Optional, Any
from app.schemas import (
    FoundationGeometry,
    MaterialProperties, 
    SelfWeightResult,
    LoadCase
)
from app.schemas.load import (
    ConditionCalculationResult, 
    StandardCombinationResult,
    BasicCombinationResult,
    ValueWithUnit,
    SimpleValue,
    SimplePkResult
)
from app.schemas.load import TowerBaseLoadResponse
from .load_factors import LoadFactors
from .loading_condition import LoadingCondition
from .base_bottom_load import BaseBottomLoad
from app.utils.logger import get_logger

logger = get_logger(__name__)


class LoadCalculator:
    """荷载计算模块"""
    
    def __init__(
        self,
        geometry: FoundationGeometry,
        material: MaterialProperties,
        self_weight_result: SelfWeightResult = None,
        loading_conditions: List[Dict[str, Any]] = None,
        tower_base_load_result: TowerBaseLoadResponse = None,
        soil_layers: Optional[List[Dict[str, Any]]] = None
    ):
        """
        初始化荷载计算器
        
        Args:
            geometry: 基础几何信息
            material: 材料属性
            self_weight_result: 自重计算结果
            loading_conditions: 荷载工况列表，包含四种工况的Fr、Fv、Fz、Mx、My、Mz参数
            tower_base_load_result: 塔筒底部荷载计算结果，包含地震力数据
            soil_layers: 土层信息列表，用于浮力计算
        """
        self.geometry = geometry
        self.material = material
        self.self_weight_result = self_weight_result
        self.loading_conditions = loading_conditions
        self.tower_base_load_result = tower_base_load_result
        self.soil_layers = soil_layers
        
        # 初始化各个组件
        self.load_factors = LoadFactors()
        # BaseBottomLoad需要在使用时创建，因为需要特定的LoadingCondition
        self.base_bottom_load = None
        
    def add_loading_condition(self, loading_condition: LoadingCondition):
        """添加荷载工况"""
        self.loading_conditions.append(loading_condition)
        logger.info(f"添加荷载工况: {loading_condition.case_type.value}")
    
    def calculate_basic_combination(self, load_case: LoadCase) -> Dict:
        """
        计算基本组合
        
        Args:
            load_case: 基本组合工况类型（不利或有利）
            
        Returns:
            Dict: 基本组合计算结果
        """
        if load_case not in [LoadCase.BASIC_COMBINATION_UNFAVORABLE, LoadCase.BASIC_COMBINATION_FAVORABLE]:
            raise ValueError("工况类型必须是基本组合")
        
        logger.info(f"计算基本组合: {load_case.value}")
        
        # 找到对应工况的荷载条件
        loading_condition = None
        for condition in self.loading_conditions:
            if condition.case_type == load_case:
                loading_condition = condition
                break
        
        if loading_condition is None:
            raise ValueError(f"未找到工况 {load_case.value} 的荷载条件")
        
        # 获取荷载分项系数
        if load_case == LoadCase.BASIC_COMBINATION_FAVORABLE:
            load_factor = self.load_factors.dead_load_favorable
        elif load_case == LoadCase.BASIC_COMBINATION_UNFAVORABLE:
            load_factor = self.load_factors.dead_load_unfavorable
        else:
            load_factor = self.load_factors.dead_load_unfavorable
        
        # 创建基础底部荷载计算对象
        base_load = BaseBottomLoad(self.geometry, self.material, loading_condition)

        # 计算各项参数
        design_values = base_load.calculate_basic_combination_design_values(self.self_weight_result, load_factor)
        eccentricity = base_load.calculate_basic_combination_eccentricity(self.self_weight_result, load_factor)
        max_pressure = base_load.calculate_basic_combination_max_pressure(self.self_weight_result, load_factor)
        average_pressure = base_load.calculate_basic_combination_average_pressure(self.self_weight_result, load_factor)
        net_pressure = base_load.calculate_basic_combination_net_pressure(self.self_weight_result, load_factor)
        
        result = {
            "load_case": load_case.value,
            "design_values": design_values,
            "eccentricity": eccentricity,
            "max_pressure": max_pressure,
            "average_pressure": average_pressure,
            "net_pressure": net_pressure,
            "load_factor": load_factor,
            "is_favorable": load_case == LoadCase.BASIC_COMBINATION_FAVORABLE
        }
        
        logger.info(f"基本组合计算完成: {load_case.value}")
        return result
    
    def validate_all_parameters(self) -> tuple[bool, List[str]]:
        """验证所有参数"""
        errors = []
        
        # 验证自重计算参数
        is_valid, error_msg = self.self_weight_calculator.validate_input_parameters()
        if not is_valid:
            errors.append(f"自重计算参数错误: {error_msg}")
        
        # 验证荷载数据（如果有基础底部荷载对象）
        if self.base_bottom_load is not None:
            if not self.base_bottom_load.validate_loads():
                errors.append("基础底部荷载数据不合理")
        
        # 验证工况数据
        if not self.loading_conditions:
            errors.append("未设置任何荷载工况")
        
        return len(errors) == 0, errors
    
    def _calculate_seismic_conditions(self, conditions: List[LoadingCondition]) -> List[LoadingCondition]:
        """
        计算地震工况的单独方法
        
        Args:
            conditions: 现有的荷载工况列表
            
        Returns:
            List[LoadingCondition]: 包含地震工况的完整荷载工况列表
        """
        # 处理地震工况计算
        if self.tower_base_load_result is not None and self.tower_base_load_result.is_success:
            logger.info("开始处理地震工况计算")
            
            # 从tower_base_load_result中提取地震力数据
            horizontal_forces = self.tower_base_load_result.horizontal_shear_forces
            vertical_forces = self.tower_base_load_result.vertical_shear_forces
            overturn_moments = self.tower_base_load_result.overturn_moments
            
            # 提取多遇地震和罕遇地震的力值
            if len(horizontal_forces) >= 4 and len(vertical_forces) >= 4 and len(overturn_moments) >= 4:
                # 多遇地震工况的地震力（第3行，索引2）
                frequent_seismic_Fr = horizontal_forces[2]
                frequent_seismic_Fz = vertical_forces[2]
                frequent_seismic_Mx = overturn_moments[2]
                
                # 罕遇地震工况的地震力（第4行，索引3）
                rare_seismic_Fr = horizontal_forces[3]
                rare_seismic_Fz = vertical_forces[3]
                rare_seismic_Mx = overturn_moments[3]
                
                # 找到正常工况的荷载条件
                normal_condition = None
                for condition in conditions:
                    if condition.case_type == LoadCase.NORMAL:
                        normal_condition = condition
                        break
                
                if normal_condition is not None:
                    # 创建多遇地震工况：正常工况 + 多遇地震力
                    frequent_seismic_condition = LoadingCondition(
                        case_type=LoadCase.FREQUENT_EARTHQUAKE,
                        Fr=normal_condition.Fr + frequent_seismic_Fr,
                        Fv=normal_condition.Fv,  # Fv保持不变
                        Fz=normal_condition.Fz + frequent_seismic_Fz,
                        Mx=normal_condition.Mx + frequent_seismic_Mx,
                        My=normal_condition.My,  # My保持不变
                        Mz=normal_condition.Mz   # Mz保持不变
                    )
                    
                    # 创建罕遇地震工况：正常工况 + 罕遇地震力
                    rare_seismic_condition = LoadingCondition(
                        case_type=LoadCase.RARE_EARTHQUAKE,
                        Fr=normal_condition.Fr + rare_seismic_Fr,
                        Fv=normal_condition.Fv,  # Fv保持不变
                        Fz=normal_condition.Fz + rare_seismic_Fz,
                        Mx=normal_condition.Mx + rare_seismic_Mx,
                        My=normal_condition.My,  # My保持不变
                        Mz=normal_condition.Mz   # Mz保持不变
                    )
                    
                    # 添加地震工况到条件列表和计算器
                    conditions.extend([frequent_seismic_condition, rare_seismic_condition])
                    self.add_loading_condition(frequent_seismic_condition)
                    self.add_loading_condition(rare_seismic_condition)
                    
                    logger.info(f"成功添加地震工况 - 多遇地震: Fr={frequent_seismic_condition.Fr:.2f}, Fz={frequent_seismic_condition.Fz:.2f}, Mx={frequent_seismic_condition.Mx:.2f}")
                    logger.info(f"成功添加地震工况 - 罕遇地震: Fr={rare_seismic_condition.Fr:.2f}, Fz={rare_seismic_condition.Fz:.2f}, Mx={rare_seismic_condition.Mx:.2f}")
                else:
                    logger.warning("未找到正常工况，无法计算地震工况")
            else:
                logger.warning("地震力数据不完整，无法计算地震工况")
        else:
            logger.warning("未提供有效的塔筒底部荷载结果，跳过地震工况计算")
        
        return conditions
    
    def _generate_load_conditions_list(self, conditions: List[LoadingCondition]) -> List[Dict[str, Any]]:
        """
        生成荷载工况信息列表
        
        Args:
            conditions: 荷载工况对象列表
            
        Returns:
            List[Dict[str, Any]]: 荷载工况字典列表（保持原有格式）
        """
        load_conditions_list = []
        for condition in conditions:
            load_conditions_list.append({
                "case_type": condition.case_type.value,
                "Fr": condition.Fr,
                "Fv": condition.Fv,
                "Fz": condition.Fz,
                "Mx": condition.Mx,
                "My": condition.My,
                "Mz": condition.Mz
            })
        return load_conditions_list
    
    def _generate_calculation_summary(self, detailed_calculations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        生成计算总结信息
        
        Args:
            detailed_calculations: 详细计算结果列表
            
        Returns:
            Dict[str, Any]: 计算总结信息
        """
        total_load_cases = len(detailed_calculations)
        successful_calculations = 0
        design_error_cases = 0
        calculation_error_cases = 0
        
        # 统计成功和错误的计算
        for calc in detailed_calculations:
            combinations = calc.get("combinations", {})
            if "design_error" in combinations:
                design_error_cases += 1
            elif "error" in combinations:
                calculation_error_cases += 1
            elif combinations:
                successful_calculations += 1
        
        calculation_methods_applied = [
            "标准组合计算",
            "基本组合（恒荷载不利）计算", 
            "基本组合（恒荷载有利）计算",
            "荷载标准值计算",
            "基础总恒载计算",
            "水平力矩之和计算",
            "偏心距计算",
            "偏心距判断与压力类型分析",
            "基础底面净反力计算"
        ]
        
        return {
            "total_load_cases": total_load_cases,
            "successful_calculations": successful_calculations,
            "design_error_cases": design_error_cases,
            "calculation_error_cases": calculation_error_cases,
            "calculation_methods_applied": calculation_methods_applied
        }
    
    async def calculate_base_bottom_load(self,) -> Dict[str, Any]:
        """
        综合荷载分析 - 调用LoadingCondition中所有的核算方法，并计算地震工况
            
        Returns:
            Dict[str, Any]: 包含所有荷载计算结果的字典，包括6种工况
        """
        try:
            logger.info("开始综合荷载分析")
            
            # 创建荷载工况列表（使用对象而不是字典）
            conditions = []
            
            if self.loading_conditions:
                # 使用传入的荷载条件参数
                logger.info(f"使用传入的 {len(self.loading_conditions)} 个荷载工况")
                for condition_data in self.loading_conditions:
                    condition = LoadingCondition(
                        case_type=condition_data["case_type"],
                        Fr=condition_data["Fr"],
                        Fv=condition_data["Fv"],
                        Fz=condition_data["Fz"],
                        Mx=condition_data["Mx"],
                        My=condition_data["My"],
                        Mz=condition_data["Mz"]
                    )
                    conditions.append(condition)
            else:
                # 使用示例荷载工况（兼容性处理）
                logger.info("使用示例荷载工况")
                conditions = [
                    LoadingCondition(LoadCase.NORMAL, Fr=1000, Fv=500, Fz=2000, Mx=5000, My=3000, Mz=1000),
                    LoadingCondition(LoadCase.EXTREME, Fr=1500, Fv=800, Fz=2500, Mx=8000, My=5000, Mz=1500),
                    LoadingCondition(LoadCase.BASIC_COMBINATION_UNFAVORABLE, Fr=1200, Fv=600, Fz=2200, Mx=6000, My=4000, Mz=1200),
                    LoadingCondition(LoadCase.BASIC_COMBINATION_FAVORABLE, Fr=800, Fv=400, Fz=1800, Mx=4000, My=2500, Mz=800)
                ]
            
            # 添加荷载工况到计算器
            for condition in conditions:
                self.add_loading_condition(condition)

            # 使用单独的方法计算地震工况
            conditions = self._calculate_seismic_conditions(conditions)
            
            # 存储所有计算结果
            comprehensive_results = {}
            
            # 1. 首先生成6种工况下的Fr、Fv、Fz、Mx、My、Mz列表（放在第一位置）
            load_conditions_list = self._generate_load_conditions_list(conditions)
            comprehensive_results["load_conditions"] = load_conditions_list
            
            # 2. 针对6种工况进行基础底部荷载值计算
            logger.info("针对正常工况、极端工况、疲劳工况上限、疲劳工况下限、多遇地震工况、罕遇地震工况进行基础底部荷载值计算")
            detailed_calculations = []
            
            # 定义需要计算的6种工况（包括地震工况）
            target_load_cases = [
                LoadCase.NORMAL, LoadCase.EXTREME, LoadCase.FATIGUE_UPPER, LoadCase.FATIGUE_LOWER,
                LoadCase.FREQUENT_EARTHQUAKE, LoadCase.RARE_EARTHQUAKE
            ]
            
            for condition in conditions:
                # 只处理目标工况
                if condition.case_type not in target_load_cases:
                    continue
                
                logger.info(f"开始计算工况: {condition.case_type.value}")
                
                # 创建基础底部荷载计算对象
                base_load = BaseBottomLoad(self.geometry, self.material, condition)
                
                # 使用对象而不是字典
                condition_result = ConditionCalculationResult(load_case=condition.case_type.value)
                
                try:
                    # 对于正常工况、极端工况和地震工况，需要计算3种组合
                    if condition.case_type in [LoadCase.NORMAL, LoadCase.EXTREME, LoadCase.FREQUENT_EARTHQUAKE, LoadCase.RARE_EARTHQUAKE]:
                        logger.info(f"{condition.case_type.value}：计算标准组合、基本组合（恒荷载不利）、基本组合（恒荷载有利）")
                        
                        # 判断是否为极端工况，使用特殊的计算方法
                        if condition.case_type == LoadCase.EXTREME:
                            logger.info("极端工况：使用特殊计算方法，不考虑e/R比值判断")
                            
                            # 1. 极端工况标准组合计算
                            standard_combination = self._calculate_standard_combination_extreme(base_load, self.self_weight_result)
                            condition_result.add_combination("standard", standard_combination.to_dict())
                            
                            # 2. 极端工况基本组合（恒荷载对结构不利）
                            basic_unfavorable = self._calculate_basic_combination_unfavorable_extreme(base_load, self.self_weight_result)
                            condition_result.add_combination("basic_unfavorable", basic_unfavorable.to_dict())
                            
                            # 3. 极端工况基本组合（恒荷载对结构有利）
                            basic_favorable = self._calculate_basic_combination_favorable_extreme(base_load, self.self_weight_result)
                            condition_result.add_combination("basic_favorable", basic_favorable.to_dict())
                        else:
                            # 正常工况和地震工况使用原有的计算方法（包含e/r1检查）
                            # 1. 标准组合计算
                            standard_combination = self._calculate_standard_combination(base_load, self.self_weight_result)
                            condition_result.add_combination("standard", standard_combination.to_dict())
                            
                            # 2. 基本组合（恒荷载对结构不利）
                            basic_unfavorable = self._calculate_basic_combination_unfavorable(base_load, self.self_weight_result)
                            condition_result.add_combination("basic_unfavorable", basic_unfavorable.to_dict())
                            
                            # 3. 基本组合（恒荷载对结构有利）
                            basic_favorable = self._calculate_basic_combination_favorable(base_load, self.self_weight_result)
                            condition_result.add_combination("basic_favorable", basic_favorable.to_dict())
                        
                    else:
                        # 对于其他工况，创建标准组合对象
                        # 创建基本数值对象
                        frk = ValueWithUnit(
                            value=base_load.calculate_load_standard_value(),
                            unit="kN",
                            description="荷载标准值"
                        )
                        nk_gk = ValueWithUnit(
                            value=base_load.calculate_total_dead_load(self.self_weight_result),
                            unit="kN", 
                            description="基础总恒载"
                        )
                        mrk = ValueWithUnit(
                            value=base_load.calculate_horizontal_moment_sum(),
                            unit="kN·m",
                            description="水平力矩之和"
                        )
                        eccentricity = ValueWithUnit(
                            value=base_load.calculate_eccentricity(self.self_weight_result),
                            unit="m",
                            description="偏心距"
                        )
                        e_over_r = SimpleValue(
                            value=0.0,  # 暂时设为0，后续可计算
                            description="偏心距与基础半径比值"
                        )
                        
                        # 创建空的简单基础底面净反力对象
                        simple_pk = SimplePkResult(
                            compressed_height=ValueWithUnit(value=0.0, unit="m", description="受压区域高度"),
                            compressed_area=ValueWithUnit(value=0.0, unit="m²", description="受压区域面积"),
                            pk=ValueWithUnit(value=0.0, unit="kPa", description="简单基础底面净反力"),
                            tau=SimpleValue(value=0.0, description="受压区域系数τ"),
                            xi=SimpleValue(value=0.0, description="基础底面系数ξ")
                        )
                        
                        pj = ValueWithUnit(
                            value=0.0,
                            unit="kPa",
                            description="基础底面净反力"
                        )
                        
                        # 创建标准组合结果对象
                        standard = StandardCombinationResult(
                            Frk=frk,
                            Nk_Gk=nk_gk,
                            Mrk=mrk,
                            eccentricity=eccentricity,
                            e_over_R=e_over_r,
                            Pkmax=None,  # 可选字段设为None
                            Pkmin=None,  # 可选字段设为None
                            simple_pk=simple_pk,
                            Pj=pj,
                            pressure_type="未计算"
                        )
                        
                        condition_result.add_combination("standard", standard)
                    
                except ValueError as e:
                    # 专门处理基础设计不合理的情况
                    if "基础设计不合理" in str(e):
                        logger.error(f"工况 {condition.case_type.value} 基础设计不合理: {str(e)}")
                        design_error = {
                            "error_type": "基础设计不合理",
                            "message": str(e),
                            "suggestion": "建议增大基础尺寸或减小作用荷载以降低偏心距比值"
                        }
                        condition_result.add_combination("design_error", design_error)
                    else:
                        logger.warning(f"工况 {condition.case_type.value} 参数错误: {str(e)}")
                        condition_result.add_combination("error", str(e))
                except Exception as e:
                    logger.warning(f"工况 {condition.case_type.value} 计算失败: {str(e)}")
                    condition_result.add_combination("error", str(e))
                
                detailed_calculations.append(condition_result.to_dict())
            
            comprehensive_results["detailed_calculations"] = detailed_calculations
            
            # 5. 不再计算关键工况
            
            # 6. 添加计算汇总（使用新的方法）
            comprehensive_results["summary"] = self._generate_calculation_summary(detailed_calculations)
            
            # 检查设计错误并添加设计建议
            design_errors = [calc for calc in detailed_calculations if "design_error" in calc["combinations"]]
            if design_errors:
                comprehensive_results["summary"]["design_warnings"] = [
                    f"{calc['load_case']}: {calc['combinations']['design_error']['message']}" 
                    for calc in design_errors
                ]
                comprehensive_results["summary"]["design_recommendations"] = [
                    "当前基础设计存在安全隐患，建议采取以下措施：",
                    "1. 增大基础底板半径，降低偏心距与半径的比值",
                    "2. 增加基础埋深或密度，增大基础自重",
                    "3. 优化上部结构设计，减小作用在基础上的倾覆力矩",
                    "4. 考虑采用桩基础或其他基础形式"
                ]
            
            logger.info(f"综合荷载分析完成，共计算 {len(conditions)} 个工况")
            logger.info(f"返回工况列表: {[item['case_type'] for item in load_conditions_list]}")
            return comprehensive_results
            
        except Exception as e:
            logger.error(f"综合荷载分析失败: {str(e)}")
            raise

    def _calculate_standard_combination_extreme(self, base_load: BaseBottomLoad, self_weight_result: SelfWeightResult) -> StandardCombinationResult:
        """
        计算极端工况下的标准组合
        
        针对极端工况，不考虑e和R的比值，直接计算所有结果：
        1. Pkmax、Pkmin - 基础底面最大最小净反力
        2. Pk - 简单基础底面净反力
        3. Pj - 复杂基础底面净反力
        4. 偏心距、受压高度、受压区域面积
        """
        logger.info("开始计算极端工况下的标准组合")
        
        # 基础计算
        Frk = base_load.calculate_load_standard_value()  # 荷载标准值
        Nk_Gk = base_load.calculate_total_dead_load(self_weight_result)  # 基础总恒载
        Mrk = base_load.calculate_horizontal_moment_sum()  # 水平力矩之和
        e = base_load.calculate_eccentricity(self_weight_result)  # 偏心距
        
        # 基础底板半径
        R = base_load.geometry.base_radius
        
        # 计算偏心距与基础半径的比值（仅供参考，极端工况不以此判断）
        e_over_R = e / R if R > 0 else 0
        
        # 创建基础结果对象
        frk = ValueWithUnit(value=Frk, unit="kN", description="荷载标准值")
        nk_gk = ValueWithUnit(value=Nk_Gk, unit="kN", description="基础总恒载")
        mrk = ValueWithUnit(value=Mrk, unit="kN·m", description="水平力矩之和")
        eccentricity = ValueWithUnit(value=e, unit="m", description="偏心距")
        e_over_r = SimpleValue(value=e_over_R, description="偏心距与基础半径比值（仅供参考）")
        
        # 极端工况：无论e/R比值如何，都计算完整结果
        logger.info("极端工况：计算Pkmax、Pkmin、Pk、Pj以及相关参数")
        
        # 计算Pkmax和Pkmin
        Pkmax_value = base_load.calculate_max_net_pressure(self_weight_result)
        Pkmin_value = base_load.calculate_min_net_pressure(self_weight_result)
        
        pkmax = ValueWithUnit(value=Pkmax_value, unit="kPa", description="基础底面最大净反力")
        pkmin = ValueWithUnit(value=Pkmin_value, unit="kPa", description="基础底面最小净反力")
        
        # 根据偏心距计算τ和ξ系数以及受压区域
        coefficients_result = base_load.calculate_coefficients_by_eccentricity(e)

        # 调用calculate_simple_pk方法获取pk值和系数
        simple_pk_result = base_load.calculate_simple_pk(self_weight_result)
        
        # 根据偏心距计算受压区域面积
        if e_over_R < 0.25:
            # 全截面受压情况下，受压区域面积为基础底板面积
            compressed_area = math.pi * R**2
            pressure_type_desc = "全截面受压"
            area_description = "受压区域面积（基础底板面积）"
        else:
            # 偏心受压情况下，受压区域面积为弓形面积
            compressed_area = self._calculate_segment_area(coefficients_result["compressed_height"], R)
            pressure_type_desc = "偏心受压"
            area_description = "受压区域面积（弓形面积）"
        
        # 创建SimplePkResult对象
        simple_pk = SimplePkResult(
            compressed_height=ValueWithUnit(
                value=coefficients_result["compressed_height"], 
                unit="m", 
                description="受压区域高度"
            ),
            compressed_area=ValueWithUnit(
                value=compressed_area, 
                unit="m²", 
                description=area_description
            ),
            pk=ValueWithUnit(
                value=simple_pk_result["pk"], 
                unit="kPa", 
                description="简单基础底面净反力"
            ),
            tau=SimpleValue(
                value=coefficients_result.get("tau", 1.0), 
                description="受压区域系数τ"
            ),
            xi=SimpleValue(
                value=coefficients_result.get("xi", 1.0), 
                description="基础底面系数ξ"
            )
        )
        
        # 调用calculate_net_pressure方法 - 极端工况标准组合
        Pj_value = base_load.calculate_net_pressure(self_weight_result, "extreme_standard", compressed_area)
        pj = ValueWithUnit(value=Pj_value, unit="kPa", description="基础底面净反力")
        
        # 创建并返回StandardCombinationResult对象
        return StandardCombinationResult(
            Frk=frk,
            Nk_Gk=nk_gk,
            Mrk=mrk,
            eccentricity=eccentricity,
            e_over_R=e_over_r,
            Pkmax=pkmax,
            Pkmin=pkmin,
            simple_pk=simple_pk,
            Pj=pj,
            pressure_type=pressure_type_desc
        )
    def _calculate_basic_combination_unfavorable_extreme(self, base_load: BaseBottomLoad, self_weight_result: SelfWeightResult) -> BasicCombinationResult:
        """
        计算极端工况下的基本组合（恒荷载对结构不利）
        
        针对极端工况，不考虑e和R的比值，直接计算所有结果：
        1. Pkmax、Pkmin - 基础底面最大最小净反力
        2. Pk - 简单基础底面净反力
        3. Pj - 复杂基础底面净反力
        4. 偏心距、受压高度、受压区域面积
        """
        logger.info("开始计算极端工况下的基本组合（恒荷载对结构不利）")
        
        # 获取荷载分项系数
        live_load_factor = self.load_factors.live_load_factor
        dead_load_unfavorable = self.load_factors.dead_load_unfavorable
        
        # 先计算标准组合的基础值
        Frk = base_load.calculate_load_standard_value()
        Nk_Gk = base_load.calculate_total_dead_load(self_weight_result)
        Mrk = base_load.calculate_horizontal_moment_sum()
        
        # 应用荷载分项系数
        Fr = Frk * live_load_factor
        N_G = Nk_Gk * dead_load_unfavorable
        Mr = Mrk * live_load_factor
        
        # 计算偏心距
        e = Mr / N_G if N_G > 0 else 0
        
        # 基础底板半径
        R = base_load.geometry.base_radius
        e_over_R = e / R if R > 0 else 0
        
        # 创建基础结果对象
        fr = ValueWithUnit(value=Fr, unit="kN", description=f"设计荷载值 = Frk * {live_load_factor}")
        n_g = ValueWithUnit(value=N_G, unit="kN", description=f"设计总恒载 = (Nk+Gk) * {dead_load_unfavorable}")
        mr = ValueWithUnit(value=Mr, unit="kN·m", description=f"设计弯矩 = Mrk * {live_load_factor}")
        eccentricity = ValueWithUnit(value=e, unit="m", description="基本组合偏心距")
        e_over_r = SimpleValue(value=e_over_R, description="偏心距与基础半径比值（仅供参考）")
        
        # 极端工况：无论e/R比值如何，都计算完整结果
        logger.info("极端工况：计算Pkmax、Pkmin、P、Pj以及相关参数")
        
        # 根据基本组合（恒荷载不利）的偏心距计算正确的τ和ξ系数
        coefficients_result = base_load.calculate_coefficients_by_eccentricity(e)
        
        # 获取受压区高度
        compressed_height = coefficients_result.get("compressed_height", 0.0) if e_over_R >= 0.25 else None
        
        # 使用通用方法计算压力值
        column_radius = base_load.geometry.column_radius
        pressures = self._calculate_basic_combination_pressures(N_G, Mr, R, column_radius, e_over_R, compressed_height, base_load, self_weight_result, "extreme_basic_unfavorable")
        
        pmax = ValueWithUnit(value=pressures["Pmax"], unit="kPa", description="基本组合最大压力")
        
        # 对于极端工况，我们也需要计算Pkmin（最小压力）
        # 使用类似于标准组合的方法，但应用基本组合的系数
        base_area = math.pi * R**2
        if base_area > 0:
            Pkmin = (N_G / base_area) - (6 * Mr) / (math.pi * R**3) if R > 0 else 0
        else:
            Pkmin = 0
        pmin = ValueWithUnit(value=Pkmin, unit="kPa", description="基本组合最小压力")
        
        p = ValueWithUnit(value=pressures["P"], unit="kPa", description="简单基础底面净反力（平均压力）")
        pj = ValueWithUnit(value=pressures["Pj"], unit="kPa", description="复杂基础底面净反力")
        
        # 根据偏心距计算受压区域面积
        if e_over_R < 0.25:
            # 全截面受压情况下，受压区域面积为基础底板面积
            compressed_area = base_area
            pressure_type_desc = "全截面受压"
        else:
            # 偏心受压情况下，受压区域面积为弓形面积
            compressed_area = self._calculate_segment_area(coefficients_result["compressed_height"], R)
            pressure_type_desc = "偏心受压"
        
        # 为了获取pk值，仍然需要调用calculate_simple_pk
        simple_pk_result = base_load.calculate_simple_pk(self_weight_result)
        
        simple_pk = SimplePkResult(
            compressed_height=ValueWithUnit(
                value=coefficients_result["compressed_height"], 
                unit="m", 
                description="受压区域高度"
            ),
            compressed_area=ValueWithUnit(
                value=compressed_area, 
                unit="m²", 
                description="受压区域面积"
            ),
            pk=ValueWithUnit(
                value=simple_pk_result["pk"], 
                unit="kPa", 
                description="简单基础底面净反力"
            ),
            tau=SimpleValue(
                value=coefficients_result.get("tau", 1.0), 
                description="受压区域系数τ"
            ),
            xi=SimpleValue(
                value=coefficients_result.get("xi", 1.0), 
                description="基础底面系数ξ"
            )
        )
        
        # 创建并返回BasicCombinationResult对象
        return BasicCombinationResult(
            Fr=fr,
            N_G=n_g,
            Mr=mr,
            eccentricity=eccentricity,
            e_over_R=e_over_r,
            Pmax=pmax,
            Pmin=pmin,
            P=p,
            simple_pk=simple_pk,
            Pj=pj,
            pressure_type=pressure_type_desc
        )
    def _calculate_basic_combination_favorable_extreme(self, base_load: BaseBottomLoad, self_weight_result: SelfWeightResult) -> BasicCombinationResult:
        """
        计算极端工况下的基本组合（恒荷载对结构有利）
        
        针对极端工况，不考虑e和R的比值，直接计算所有结果：
        1. Pkmax、Pkmin - 基础底面最大最小净反力
        2. Pk - 简单基础底面净反力
        3. Pj - 复杂基础底面净反力
        4. 偏心距、受压高度、受压区域面积
        """
        logger.info("开始计算极端工况下的基本组合（恒荷载对结构有利）")
        
        # 获取荷载分项系数
        live_load_factor = self.load_factors.live_load_factor
        dead_load_favorable = self.load_factors.dead_load_favorable
        
        # 先计算标准组合的基础值
        Frk = base_load.calculate_load_standard_value()
        Nk_Gk = base_load.calculate_total_dead_load(self_weight_result)
        Mrk = base_load.calculate_horizontal_moment_sum()
        
        # 应用荷载分项系数
        Fr = Frk * live_load_factor
        N_G = Nk_Gk * dead_load_favorable
        Mr = Mrk * live_load_factor
        
        # 计算偏心距
        e = Mr / N_G if N_G > 0 else 0
        
        # 基础底板半径
        R = base_load.geometry.base_radius
        e_over_R = e / R if R > 0 else 0
        
        # 创建基础结果对象
        fr = ValueWithUnit(value=Fr, unit="kN", description=f"设计荷载值 = Frk * {live_load_factor}")
        n_g = ValueWithUnit(value=N_G, unit="kN", description=f"设计总恒载 = (Nk+Gk) * {dead_load_favorable}")
        mr = ValueWithUnit(value=Mr, unit="kN·m", description=f"设计弯矩 = Mrk * {live_load_factor}")
        eccentricity = ValueWithUnit(value=e, unit="m", description="基本组合偏心距")
        e_over_r = SimpleValue(value=e_over_R, description="偏心距与基础半径比值（仅供参考）")
        
        # 极端工况：无论e/R比值如何，都计算完整结果
        logger.info("极端工况：计算Pkmax、Pkmin、P、Pj以及相关参数")
        
        # 根据基本组合（恒荷载有利）的偏心距计算正确的τ和ξ系数
        coefficients_result = base_load.calculate_coefficients_by_eccentricity(e)
        
        # 获取受压区高度
        compressed_height = coefficients_result.get("compressed_height", 0.0) if e_over_R >= 0.25 else None
        
        # 使用通用方法计算压力值
        column_radius = base_load.geometry.column_radius
        pressures = self._calculate_basic_combination_pressures(N_G, Mr, R, column_radius, e_over_R, compressed_height, base_load, self_weight_result, "extreme_basic_favorable")
        
        pmax = ValueWithUnit(value=pressures["Pmax"], unit="kPa", description="基本组合最大压力")
        
        # 对于极端工况，我们也需要计算Pkmin（最小压力）
        # 使用类似于标准组合的方法，但应用基本组合的系数
        base_area = math.pi * R**2
        if base_area > 0:
            Pkmin = (N_G / base_area) - (6 * Mr) / (math.pi * R**3) if R > 0 else 0
        else:
            Pkmin = 0
        pmin = ValueWithUnit(value=Pkmin, unit="kPa", description="基本组合最小压力")
        
        p = ValueWithUnit(value=pressures["P"], unit="kPa", description="简单基础底面净反力（平均压力）")
        pj = ValueWithUnit(value=pressures["Pj"], unit="kPa", description="复杂基础底面净反力")
        
        # 根据偏心距计算受压区域面积
        if e_over_R < 0.25:
            # 全截面受压情况下，受压区域面积为基础底板面积
            compressed_area = base_area
            pressure_type_desc = "全截面受压"
        else:
            # 偏心受压情况下，受压区域面积为弓形面积
            compressed_area = self._calculate_segment_area(coefficients_result["compressed_height"], R)
            pressure_type_desc = "偏心受压"
        
        # 为了获取pk值，仍然需要调用calculate_simple_pk
        simple_pk_result = base_load.calculate_simple_pk(self_weight_result)
        
        simple_pk = SimplePkResult(
            compressed_height=ValueWithUnit(
                value=coefficients_result["compressed_height"], 
                unit="m", 
                description="受压区域高度"
            ),
            compressed_area=ValueWithUnit(
                value=compressed_area, 
                unit="m²", 
                description="受压区域面积"
            ),
            pk=ValueWithUnit(
                value=simple_pk_result["pk"], 
                unit="kPa", 
                description="简单基础底面净反力"
            ),
            tau=SimpleValue(
                value=coefficients_result.get("tau", 1.0), 
                description="受压区域系数τ"
            ),
            xi=SimpleValue(
                value=coefficients_result.get("xi", 1.0), 
                description="基础底面系数ξ"
            )
        )
        
        # 创建并返回BasicCombinationResult对象
        return BasicCombinationResult(
            Fr=fr,
            N_G=n_g,
            Mr=mr,
            eccentricity=eccentricity,
            e_over_R=e_over_r,
            Pmax=pmax,
            Pmin=pmin,
            P=p,
            simple_pk=simple_pk,
            Pj=pj,
            pressure_type=pressure_type_desc
        )
    def _calculate_segment_area(self, compressed_height: float, R: float) -> float:
        """
        根据受压区高度计算圆形基础的实际受压面积
        
        基于提供的公式计算偏心距大于0.25时的受压面积：
        Ac = (2π - 2sin⁻¹(√(R² - (ac - R)²)/R)) × πR²/2π + 1/2 × 2 × √(R² - (ac - R)² × (ac - R))
        
        其中：
        - ac = compressed_height (受压区高度)
        - R = 基础底板半径
        - 公式中2π中的π代表180度
        - 其他π为正常的3.1415926...
        
        Args:
            compressed_height: 受压区高度 ac (m)
            R: 基础半径 (m)
            
        Returns:
            float: 实际受压面积 (m²)
        """
        try:
            ac = compressed_height
            
            # 全截面面积
            total_area = math.pi * R**2
            
            # 如果受压区高度等于或大于直径，为全截面受压
            if ac >= 2 * R:
                logger.debug(f"受压面积计算: ac={ac:.4f}m, R={R:.4f}m, 全截面受压")
                return total_area
            
            # 如果受压区高度为0或负值，无受压面积
            if ac <= 0:
                logger.debug(f"受压面积计算: ac={ac:.4f}m, R={R:.4f}m, 无受压面积")
                return 0.0
            
            # 计算 根号下√(R² - (ac - R)²)
            sqrt_term = math.sqrt(R**2 - (ac - R)**2)
            
            # 计算 sin⁻¹(√(R² - (ac - R)²)/R)
            sin_inv_arg = sqrt_term / R
            
            # 确保反正弦函数的参数在有效范围内 [-1, 1]
            sin_inv_arg = max(-1.0, min(1.0, sin_inv_arg))
            sin_inv_value = math.asin(sin_inv_arg)
            
            # 根据公式计算受压面积
            # Ac = (2π - 2sin⁻¹(√(R² - (ac - R)²)/R)) × πR²/2π + I/2 × 2 × √(R² - (ac - R)² × (ac - R))
            # 注意：2π中的π代表180度，即2π = 2 × 180° = 360°
            # 所以 2π = 2 × math.pi （这里用正常的π值）
            
            # 第一项：(2π - 2sin⁻¹(...)) × πR²/2π
            # 简化：(2π - 2sin⁻¹(...)) × πR²/(2π) = (1 - sin⁻¹(...)/π) × πR²
            first_term = (2 * math.pi - 2 * sin_inv_value) * math.pi * R**2 / (2 * math.pi)
            first_term = (1 - sin_inv_value / math.pi) * math.pi * R**2
            
            # 第二项：I/2 × 2 × √(R² - (ac - R)²) × (ac - R)
            # 这里I应该是1（从公式结构推测），所以第二项为：√(R² - (ac - R)²) × (ac - R)
            second_term = sqrt_term * (ac - R)
            
            # 总面积
            segment_area = first_term + second_term
            
            # 确保面积在合理范围内
            segment_area = max(0.0, min(segment_area, total_area))
            
            logger.debug(f"受压面积计算: ac={ac:.4f}m, R={R:.4f}m, "
                        f"第一项={first_term:.4f}m², 第二项={second_term:.4f}m², "
                        f"受压面积={segment_area:.4f}m², 占比={segment_area/total_area:.2%}")
            
            return segment_area
            
        except Exception as ex:
            logger.error(f"受压面积计算出错: {str(ex)}")
            # 返回保守估计值
            return total_area * 0.5

    def _calculate_standard_combination(self, base_load: BaseBottomLoad, self_weight_result: SelfWeightResult) -> StandardCombinationResult:
        """
        计算标准组合
        
        在标准组合中，需要计算：
        1. 荷载标准值 (Frk)
        2. 基础总恒载 (Nk+Gk)
        3. 水平力矩之和 (Mrk)
        4. 偏心距 (e)
        5. 判断偏心距与基础半径比值，如果小于0.25，计算Pkmax和Pkmin
        6. 如果Pkmin>0，为全截面受压，调用calculate_simple_pk和calculate_net_pressure
        """
        logger.info("开始计算标准组合")
        
        # 基础计算
        Frk = base_load.calculate_load_standard_value()  # 荷载标准值
        Nk_Gk = base_load.calculate_total_dead_load(self_weight_result)  # 基础总恒载
        Mrk = base_load.calculate_horizontal_moment_sum()  # 水平力矩之和
        e = base_load.calculate_eccentricity(self_weight_result)  # 偏心距
        
        # 基础底板半径
        R = base_load.geometry.base_radius
        
        # 计算偏心距与基础半径的比值
        e_over_R = e / R if R > 0 else 0
        
        # 创建基础结果对象
        frk = ValueWithUnit(value=Frk, unit="kN", description="荷载标准值")
        nk_gk = ValueWithUnit(value=Nk_Gk, unit="kN", description="基础总恒载")
        mrk = ValueWithUnit(value=Mrk, unit="kN·m", description="水平力矩之和")
        eccentricity = ValueWithUnit(value=e, unit="m", description="偏心距")
        e_over_r = SimpleValue(value=e_over_R, description="偏心距与基础半径比值")
        
        # 判断偏心距与基础半径的比值
        if e_over_R < 0.25:
            logger.info("偏心距与基础半径比值小于0.25，计算Pkmax和Pkmin")
            
            # 计算Pkmax和Pkmin
            Pkmax_value = base_load.calculate_max_net_pressure(self_weight_result)
            Pkmin_value = base_load.calculate_min_net_pressure(self_weight_result)
            
            pkmax = ValueWithUnit(value=Pkmax_value, unit="kPa", description="基础底面最大净反力")
            pkmin = ValueWithUnit(value=Pkmin_value, unit="kPa", description="基础底面最小净反力")
            
            # 判断是否为全截面受压
            if Pkmin_value > 0:
                logger.info("Pkmin > 0，为全截面受压，调用calculate_simple_pk方法")
                
                # 调用calculate_simple_pk方法
                simple_pk_result = base_load.calculate_simple_pk(self_weight_result)
                
                # 计算基础底板面积
                compressed_area = math.pi * R**2
                
                # 创建SimplePkResult对象
                simple_pk = SimplePkResult(
                    compressed_height=ValueWithUnit(
                        value=simple_pk_result["compressed_height"], 
                        unit="m", 
                        description="受压区域高度"
                    ),
                    compressed_area=ValueWithUnit(
                        value=compressed_area, 
                        unit="m²", 
                        description="受压区域面积（基础底板面积）"
                    ),
                    pk=ValueWithUnit(
                        value=simple_pk_result["pk"], 
                        unit="kPa", 
                        description="简单基础底面净反力"
                    ),
                    tau=SimpleValue(
                        value=simple_pk_result.get("tau", 1.0), 
                        description="受压区域系数τ"
                    ),
                    xi=SimpleValue(
                        value=simple_pk_result.get("xi", 1.0), 
                        description="基础底面系数ξ"
                    )
                )
                
                # 调用calculate_net_pressure方法 - 正常工况标准组合
                Pj_value = base_load.calculate_net_pressure(self_weight_result, "normal_standard", compressed_area)
                pj = ValueWithUnit(value=Pj_value, unit="kPa", description="基础底面净反力")
                
                pressure_type = "全截面受压"
            else:
                # 部分截面受压情况下，需要创建一个默认的simple_pk对象
                simple_pk_result = base_load.calculate_simple_pk(self_weight_result)
                simple_pk = SimplePkResult(
                    compressed_height=ValueWithUnit(
                        value=simple_pk_result["compressed_height"], 
                        unit="m", 
                        description="受压区域高度"
                    ),
                    compressed_area=ValueWithUnit(
                        value=0.0, 
                        unit="m²", 
                        description="受压区域面积"
                    ),
                    pk=ValueWithUnit(
                        value=simple_pk_result["pk"], 
                        unit="kPa", 
                        description="简单基础底面净反力"
                    ),
                    tau=SimpleValue(
                        value=simple_pk_result.get("tau", 1.0), 
                        description="受压区域系数τ"
                    ),
                    xi=SimpleValue(
                        value=simple_pk_result.get("xi", 1.0), 
                        description="基础底面系数ξ"
                    )
                )
                pj = ValueWithUnit(value=0.0, unit="kPa", description="基础底面净反力")
                pressure_type = "部分截面受压"
        else:
            logger.info("偏心距与基础半径比值大于等于0.25，计算偏心受压情况下的受压区域")
            
            # 根据偏心距计算τ和ξ系数
            coefficients_result = base_load.calculate_coefficients_by_eccentricity(e)
            
            # 根据偏心距计算弓形面积
            compressed_area = self._calculate_segment_area(coefficients_result["compressed_height"], R)
            
            # 调用calculate_simple_pk方法获取pk值
            simple_pk_result = base_load.calculate_simple_pk(self_weight_result)
            
            # 创建SimplePkResult对象
            simple_pk = SimplePkResult(
                compressed_height=ValueWithUnit(
                    value=coefficients_result["compressed_height"], 
                    unit="m", 
                    description="受压区域高度"
                ),
                compressed_area=ValueWithUnit(
                    value=compressed_area, 
                    unit="m²", 
                    description="受压区域面积（弓形面积）"
                ),
                pk=ValueWithUnit(
                    value=simple_pk_result["pk"], 
                    unit="kPa", 
                    description="简单基础底面净反力"
                ),
                tau=SimpleValue(
                    value=coefficients_result.get("tau", 1.0), 
                    description="受压区域系数τ"
                ),
                xi=SimpleValue(
                    value=coefficients_result.get("xi", 1.0), 
                    description="基础底面系数ξ"
                )
            )
            
            # 调用calculate_net_pressure方法 - 正常工况标准组合
            Pj_value = base_load.calculate_net_pressure(self_weight_result, "normal_standard", compressed_area)
            pj = ValueWithUnit(value=Pj_value, unit="kPa", description="基础底面净反力")
            
            pressure_type = "偏心受压"
            
            # 即使在偏心受压情况下也需要计算Pkmax和Pkmin，用于后续的地基变形验算
            logger.info("偏心受压情况下，计算Pkmax和Pkmin用于地基变形验算")
            Pkmax_value = base_load.calculate_max_net_pressure(self_weight_result)
            Pkmin_value = base_load.calculate_min_net_pressure(self_weight_result)
            
            pkmax = ValueWithUnit(value=Pkmax_value, unit="kPa", description="基础底面最大净反力")
            pkmin = ValueWithUnit(value=Pkmin_value, unit="kPa", description="基础底面最小净反力")
        
        # 创建并返回StandardCombinationResult对象
        return StandardCombinationResult(
            Frk=frk,
            Nk_Gk=nk_gk,
            Mrk=mrk,
            eccentricity=eccentricity,
            e_over_R=e_over_r,
            Pkmax=pkmax,
            Pkmin=pkmin,
            simple_pk=simple_pk,
            Pj=pj,
            pressure_type=pressure_type
        )
    def _calculate_basic_combination_unfavorable(self, base_load: BaseBottomLoad, self_weight_result: SelfWeightResult) -> BasicCombinationResult:
        """
        计算基本组合（恒荷载对结构不利）
        
        在基本组合（恒荷载对结构不利）中：
        1. Fr = 标准组合中的Frk * live_load_factor
        2. N+G = 标准组合的(Nk+Gk) * dead_load_unfavorable
        3. Mr = Mrk * live_load_factor
        4. 计算偏心距e，判断e/R是否>=0.25
        5. 如果>=0.25，计算Pmax、P（简单基础底面净反力）、Pj（复杂基础底面净反力）
        """
        logger.info("开始计算基本组合（恒荷载对结构不利）")
        
        # 获取荷载分项系数
        live_load_factor = self.load_factors.live_load_factor
        dead_load_unfavorable = self.load_factors.dead_load_unfavorable
        
        # 先计算标准组合的基础值
        Frk = base_load.calculate_load_standard_value()
        Nk = base_load.condition.Fz  # 获取极端工况下的Fz值
        Nk_Gk = base_load.calculate_total_dead_load(self_weight_result)
        Mrk = base_load.calculate_horizontal_moment_sum()
        
        # 应用荷载分项系数
        Fr = Frk * live_load_factor
        N = Nk * dead_load_unfavorable
        N_G = Nk_Gk * dead_load_unfavorable
        Mr = Mrk * live_load_factor
        
        # 计算偏心距
        e = Mr / N_G if N_G > 0 else 0
        
        # 基础底板半径
        R = base_load.geometry.base_radius
        e_over_R = e / R if R > 0 else 0
        
        # 创建基础结果对象
        fr = ValueWithUnit(value=Fr, unit="kN", description=f"设计荷载值 = Frk * {live_load_factor}")
        n_g = ValueWithUnit(value=N_G, unit="kN", description=f"设计总恒载 = (Nk+Gk) * {dead_load_unfavorable}")
        mr = ValueWithUnit(value=Mr, unit="kN·m", description=f"设计弯矩 = Mrk * {live_load_factor}")
        eccentricity = ValueWithUnit(value=e, unit="m", description="基本组合偏心距")
        e_over_r = SimpleValue(value=e_over_R, description="偏心距与基础半径比值")
        
        # 判断偏心距与基础半径的比值
        if e_over_R >= 0.25:
            logger.info("偏心距与基础半径比值大于等于0.25，计算Pmax、P和Pj")
            
            # 根据基本组合（恒荷载不利）的偏心距计算正确的τ和ξ系数
            coefficients_result = base_load.calculate_coefficients_by_eccentricity(e)
            
            # 获取受压区高度
            compressed_height = coefficients_result.get("compressed_height", 0.0)
            
            # 使用通用方法计算压力值
            column_radius = base_load.geometry.column_radius
            pressures = self._calculate_basic_combination_pressures(N_G, Mr, R, column_radius, e_over_R, compressed_height, base_load, self_weight_result, "normal_basic_unfavorable")
            
            pmax = ValueWithUnit(value=pressures["Pmax"], unit="kPa", description="基本组合最大压力")
            p = ValueWithUnit(value=pressures["P"], unit="kPa", description="简单基础底面净反力（平均压力）")
            pj = ValueWithUnit(value=pressures["Pj"], unit="kPa", description="复杂基础底面净反力")
            
            # 根据偏心距计算弓形面积
            compressed_area = self._calculate_segment_area(coefficients_result["compressed_height"], R)
            
            # 为了获取pk值，仍然需要调用calculate_simple_pk
            simple_pk_result = base_load.calculate_simple_pk(self_weight_result)
            
            simple_pk = SimplePkResult(
                compressed_height=ValueWithUnit(
                    value=coefficients_result["compressed_height"], 
                    unit="m", 
                    description="受压区域高度"
                ),
                compressed_area=ValueWithUnit(
                    value=compressed_area, 
                    unit="m²", 
                    description="受压区域面积（弓形面积）"
                ),
                pk=ValueWithUnit(
                    value=simple_pk_result["pk"], 
                    unit="kPa", 
                    description="简单基础底面净反力"
                ),
                tau=SimpleValue(
                    value=coefficients_result.get("tau", 1.0), 
                    description="受压区域系数τ"
                ),
                xi=SimpleValue(
                    value=coefficients_result.get("xi", 1.0), 
                    description="基础底面系数ξ"
                )
            )
            
            pressure_type = "偏心受压"
        else:
            logger.info("偏心距与基础半径比值小于0.25，为全截面受压")
            
            # 根据基本组合（恒荷载不利）的偏心距计算正确的τ和ξ系数
            coefficients_result = base_load.calculate_coefficients_by_eccentricity(e)
            
            # 计算基础底板面积
            compressed_area = math.pi * R**2
            
            # 为了获取pk值，仍然需要调用calculate_simple_pk
            simple_pk_result = base_load.calculate_simple_pk(self_weight_result)
            
            simple_pk = SimplePkResult(
                compressed_height=ValueWithUnit(
                    value=coefficients_result["compressed_height"], 
                    unit="m", 
                    description="受压区域高度"
                ),
                compressed_area=ValueWithUnit(
                    value=compressed_area, 
                    unit="m²", 
                    description="受压区域面积（基础底板面积）"
                ),
                pk=ValueWithUnit(
                    value=simple_pk_result["pk"], 
                    unit="kPa", 
                    description="简单基础底面净反力"
                ),
                tau=SimpleValue(
                    value=coefficients_result.get("tau", 1.0), 
                    description="受压区域系数τ"
                ),
                xi=SimpleValue(
                    value=coefficients_result.get("xi", 1.0), 
                    description="基础底面系数ξ"
                )
            )
            
            # 调用calculate_net_pressure方法 - 正常工况基本组合（恒荷载对结构不利）
            Pj_value = base_load.calculate_net_pressure(self_weight_result, "normal_basic_unfavorable", compressed_area)
            pj = ValueWithUnit(value=Pj_value, unit="kPa", description="基础底面净反力")
            pressure_type = "全截面受压"
            # 在全截面受压情况下，没有Pmax和P
            pmax = None
            p = None
        
        # 创建并返回BasicCombinationResult对象
        return BasicCombinationResult(
            Fr=fr,
            N_G=n_g,
            Mr=mr,
            eccentricity=eccentricity,
            e_over_R=e_over_r,
            Pmax=pmax,
            P=p,
            simple_pk=simple_pk,
            Pj=pj,
            pressure_type=pressure_type
        )
    def _calculate_basic_combination_favorable(self, base_load: BaseBottomLoad, self_weight_result: SelfWeightResult) -> BasicCombinationResult:
        """
        计算基本组合（恒荷载对结构有利）
        
        计算逻辑与基本组合（恒荷载对结构不利）一致，
        只是N+G的系数使用dead_load_favorable
        """
        logger.info("开始计算基本组合（恒荷载对结构有利）")
        
        # 获取荷载分项系数
        live_load_factor = self.load_factors.live_load_factor
        dead_load_favorable = self.load_factors.dead_load_favorable
        
        # 先计算标准组合的基础值
        Frk = base_load.calculate_load_standard_value()
        Nk_Gk = base_load.calculate_total_dead_load(self_weight_result)
        Mrk = base_load.calculate_horizontal_moment_sum()
        
        # 应用荷载分项系数
        Fr = Frk * live_load_factor
        N_G = Nk_Gk * dead_load_favorable
        Mr = Mrk * live_load_factor
        
        # 计算偏心距
        e = Mr / N_G if N_G > 0 else 0
        
        # 基础底板半径
        R = base_load.geometry.base_radius
        e_over_R = e / R if R > 0 else 0
        
        # 创建基础结果对象
        fr = ValueWithUnit(value=Fr, unit="kN", description=f"设计荷载值 = Frk * {live_load_factor}")
        n_g = ValueWithUnit(value=N_G, unit="kN", description=f"设计总恒载 = (Nk+Gk) * {dead_load_favorable}")
        mr = ValueWithUnit(value=Mr, unit="kN·m", description=f"设计弯矩 = Mrk * {live_load_factor}")
        eccentricity = ValueWithUnit(value=e, unit="m", description="基本组合偏心距")
        e_over_r = SimpleValue(value=e_over_R, description="偏心距与基础半径比值")
        
        # 判断偏心距与基础半径的比值
        if e_over_R >= 0.25:
            logger.info("偏心距与基础半径比值大于等于0.25，计算Pmax、P和Pj")
            
            # 根据基本组合（恒荷载有利）的偏心距计算正确的τ和ξ系数
            coefficients_result = base_load.calculate_coefficients_by_eccentricity(e)
            
            # 获取受压区高度
            compressed_height = coefficients_result.get("compressed_height", 0.0)
            
            # 使用通用方法计算压力值
            column_radius = base_load.geometry.column_radius
            pressures = self._calculate_basic_combination_pressures(N_G, Mr, R, column_radius, e_over_R, compressed_height, base_load, self_weight_result, "normal_basic_favorable")
            
            pmax = ValueWithUnit(value=pressures["Pmax"], unit="kPa", description="基本组合最大压力")
            p = ValueWithUnit(value=pressures["P"], unit="kPa", description="简单基础底面净反力（平均压力）")
            pj = ValueWithUnit(value=pressures["Pj"], unit="kPa", description="复杂基础底面净反力")
            
            # 根据偏心距计算弓形面积
            compressed_area = self._calculate_segment_area(coefficients_result["compressed_height"], R)
            
            # 为了获取pk值，仍然需要调用calculate_simple_pk
            simple_pk_result = base_load.calculate_simple_pk(self_weight_result)
            
            simple_pk = SimplePkResult(
                compressed_height=ValueWithUnit(
                    value=coefficients_result["compressed_height"], 
                    unit="m", 
                    description="受压区域高度"
                ),
                compressed_area=ValueWithUnit(
                    value=compressed_area, 
                    unit="m²", 
                    description="受压区域面积（弓形面积）"
                ),
                pk=ValueWithUnit(
                    value=simple_pk_result["pk"], 
                    unit="kPa", 
                    description="简单基础底面净反力"
                ),
                tau=SimpleValue(
                    value=coefficients_result.get("tau", 1.0), 
                    description="受压区域系数τ"
                ),
                xi=SimpleValue(
                    value=coefficients_result.get("xi", 1.0), 
                    description="基础底面系数ξ"
                )
            )
            
            pressure_type = "偏心受压"
        else:
            logger.info("偏心距与基础半径比值小于0.25，为全截面受压")
            
            # 根据基本组合（恒荷载有利）的偏心距计算正确的τ和ξ系数
            coefficients_result = base_load.calculate_coefficients_by_eccentricity(e)
            
            # 计算基础底板面积
            compressed_area = math.pi * R**2
            
            # 为了获取pk值，仍然需要调用calculate_simple_pk
            simple_pk_result = base_load.calculate_simple_pk(self_weight_result)
            
            simple_pk = SimplePkResult(
                compressed_height=ValueWithUnit(
                    value=coefficients_result["compressed_height"], 
                    unit="m", 
                    description="受压区域高度"
                ),
                compressed_area=ValueWithUnit(
                    value=compressed_area, 
                    unit="m²", 
                    description="受压区域面积（基础底板面积）"
                ),
                pk=ValueWithUnit(
                    value=simple_pk_result["pk"], 
                    unit="kPa", 
                    description="简单基础底面净反力"
                ),
                tau=SimpleValue(
                    value=coefficients_result.get("tau", 1.0), 
                    description="受压区域系数τ"
                ),
                xi=SimpleValue(
                    value=coefficients_result.get("xi", 1.0), 
                    description="基础底面系数ξ"
                )
            )
            
            # 调用calculate_net_pressure方法 - 正常工况基本组合（恒荷载对结构有利）
            Pj_value = base_load.calculate_net_pressure(self_weight_result, "normal_basic_favorable", compressed_area)
            pj = ValueWithUnit(value=Pj_value, unit="kPa", description="基础底面净反力")
            pressure_type = "全截面受压"
            # 在全截面受压情况下，没有Pmax和P
            pmax = None
            p = None
        
        # 创建并返回BasicCombinationResult对象
        return BasicCombinationResult(
            Fr=fr,
            N_G=n_g,
            Mr=mr,
            eccentricity=eccentricity,
            e_over_R=e_over_r,
            Pmax=pmax,
            P=p,
            simple_pk=simple_pk,
            Pj=pj,
            pressure_type=pressure_type
        )
    
    def _calculate_basic_combination_pressures(
            self,
            N_G: float,
            Mr: float,
            R: float,
            column_radius: float,
            e_over_R: float,
            compressed_height: float = None,
            base_load: 'BaseBottomLoad' = None,
            self_weight_result: 'SelfWeightResult' = None,
            combination_type: str = "normal_basic_unfavorable"
        ) -> Dict[str, float]:
        """
        通用的基本组合压力计算方法
        
        Args:
            N_G: 设计总恒载 (kN)
            Mr: 设计弯矩 (kN·m)  
            R: 基础半径 (m)
            column_radius: 台柱半径 (m)
            e_over_R: 偏心距与基础半径的比值
            compressed_height: 受压区高度 (m), 当 e_over_R >= 0.25 时必需
            base_load: BaseBottomLoad 对象，用于调用 calculate_net_pressure 方法
            self_weight_result: 自重计算结果，用于调用 calculate_net_pressure 方法
            combination_type: 组合类型，用于确定传递给 calculate_net_pressure 的参数
            
        Returns:
            Dict[str, float]: 包含 Pmax, P, Pj 的字典
        """
        from app.services.foundation_pressure_coefficients import foundation_pressure_coefficients
        
        base_area = math.pi * R**2
        
        # 根据偏心距比值确定实际受压面积和计算最大压力
        if e_over_R >= 0.25:
            # 偏心受压情况，需要计算实际受压面积
            if compressed_height is None:
                raise ValueError("当 e_over_R >= 0.25 时，必须提供 compressed_height 参数")
            
            # 计算实际受压面积
            compressed_area = self._calculate_segment_area(compressed_height, R)
            logger.debug(f"偏心受压: e/R = {e_over_R:.3f}, 受压面积 = {compressed_area:.2f} m²")
            
            # 按《高耸结构设计标准》7.2.3计算最大压力
            # 验证参数范围
            is_valid, error_msg = foundation_pressure_coefficients.validate_parameters(e_over_R)
            if not is_valid:
                logger.warning(f"参数验证失败: {error_msg}，使用边界值计算")
            
            # 获取ξ系数（假设为实心圆形基础，r2/r1 = 0.0）
            xi = foundation_pressure_coefficients.get_xi_coefficient(e_over_R, r2_over_r1=0.0)
            
            # 使用ξ系数计算最大压力
            # 公式: pmax = N / (ξ × r1²)
            Pmax = N_G / (xi * R**2)
            
            logger.debug(f"偏心距比值 e/r1 = {e_over_R:.3f}, 插值得到 ξ = {xi:.3f}")
            
        else:
            # 全截面受压情况
            compressed_area = base_area
            logger.debug(f"全截面受压: e/R = {e_over_R:.3f}, 受压面积 = {compressed_area:.2f} m²")
            
            # 使用传统的圆形截面公式计算最大压力
            diameter = 2 * R
            section_modulus = (math.pi / 32) * diameter**3
            
            Pmax = N_G / compressed_area + Mr / section_modulus
            
            logger.debug(f"偏心距比值 e/r1 = {e_over_R:.3f} < 0.25，采用全截面受压公式")
        
        # 计算简单基础底面净反力（平均压力）
        # 公式: P = (N + G) / A_compressed (使用实际受压面积)
        P = N_G / compressed_area
        
        # 计算复杂基础底面净反力
        # 使用通用的 calculate_net_pressure 方法以保持一致性
        if base_load is not None and self_weight_result is not None:
            # 调用通用的 calculate_net_pressure 方法
            Pj = base_load.calculate_net_pressure(self_weight_result, combination_type, compressed_area)
        else:
            # 如果没有提供必要的参数，使用原始计算方法作为后备
            diameter = 2 * R
            I = (math.pi / 64) * diameter**4
            
            # 第一项: N/A_compressed (使用实际受压面积)
            first_term = N_G / compressed_area
            # 第二项: (Mr/I) × (2R + column_radius) / 3
            second_term = (Mr / I) * (2 * R + column_radius) / 3
            
            Pj = first_term + second_term
        
        return {
            "Pmax": Pmax,
            "P": P, 
            "Pj": Pj,
            "compressed_area": compressed_area  # 返回受压面积供参考
        }