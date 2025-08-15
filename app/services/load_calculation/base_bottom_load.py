"""
基础底部荷载模块

该模块定义了基础底部荷载值的计算类。
"""

import math
from typing import Dict
from app.schemas import (
    FoundationGeometry,
    MaterialProperties, 
    SelfWeightResult,
    LoadCase
)
from .loading_condition import LoadingCondition
from .load_factors import LoadFactors
from app.services.foundation_pressure_coefficients import foundation_pressure_coefficients
from app.utils.logger import get_logger

logger = get_logger(__name__)


class BaseBottomLoad:
    """基础底部荷载值"""
    
    def __init__(
        self,
        geometry: FoundationGeometry,
        material: MaterialProperties,
        condition: LoadingCondition
    ):
        self.wind_load: float = 0.0              # 风荷载(kN)
        self.seismic_load: float = 0.0           # 地震荷载(kN)
        self.total_horizontal_load: float = 0.0  # 总水平荷载(kN)
        self.total_vertical_load: float = 0.0    # 总竖向荷载(kN)
        self.total_moment: float = 0.0           # 总弯矩(kN·m)
        self.geometry = geometry                 # 基础几何信息
        self.material = material                 # 材料属性
        self.condition = condition               # 荷载工况
    
    # 计算荷载标准值=开根号(Fr平方+Fv平方)
    def calculate_load_standard_value(self) -> float:
        """计算荷载标准值"""
        return math.sqrt(self.condition.Fr**2 + self.condition.Fv**2)
    
    # 计算基础总恒载（Gk + Nk）= 总重量Gk + z轴向荷载Fz
    def calculate_total_dead_load(self, self_weight: SelfWeightResult) -> float:
        """计算基础总恒载"""
        return self_weight.total_weight + self.condition.Fz

    # 计算水平力矩之和Mrk=开根号(Mx平方+My平方)+Fr*基础高度
    def calculate_horizontal_moment_sum(self) -> float:
        """计算水平力矩之和"""
        # 基础高度 = 基础边缘高度 + 基础棱台高度 + 基础台柱高度 + 垫层厚度
        # 垫层厚度从mm转换为m
        cushion_thickness_m = self.material.cushion_thickness / 1000
        base_height = self.geometry.edge_height + self.geometry.frustum_height + self.geometry.column_height + cushion_thickness_m
        return math.sqrt(self.condition.Mx**2 + self.condition.My**2) + self.condition.Fr*base_height

    # 计算偏心距e0=Mrk/（Gk + Nk）
    def calculate_eccentricity(self, self_weight: SelfWeightResult) -> float:
        """计算偏心距"""
        return self.calculate_horizontal_moment_sum() / self.calculate_total_dead_load(self_weight)
    
    def calculate_net_pressure(self, self_weight: SelfWeightResult, combination_type: str = "standard", compressed_area: float = None) -> float:
        """
        计算基础底面净反力，支持6种组合情况
        
        根据正常工况和极端工况下各3种组合的情况，分别有6种情况：
        极端工况下：
        1. 极端工况标准组合计算 (extreme_standard)
        2. 极端工况基本组合（恒荷载对结构不利） (extreme_basic_unfavorable)
        3. 极端工况基本组合（恒荷载对结构有利） (extreme_basic_favorable)
        正常工况下：
        1. 标准组合计算 (normal_standard)
        2. 基本组合（恒荷载对结构不利） (normal_basic_unfavorable)
        3. 基本组合（恒荷载对结构有利） (normal_basic_favorable)
        
        公式: Pj = N/A + (Mr/I)×(2R+r1)/3
        其中: I = π/64×D⁴, N = 轴向荷载, Mr = 弯矩, A = 受压面积
        
        Args:
            self_weight: 自重计算结果
            combination_type: 组合类型，默认为"standard"（标准组合）
            compressed_area: 实际受压面积(m²)，如果不提供则使用基础底板面积
            
        Returns:
            float: 基础底面净反力(kPa)
        """
        # 创建荷载分项系数对象
        load_factors = LoadFactors()
        
        # 基础值计算
        Nk = self.condition.Fz  # 风机重量
        Nk_Gk = self.calculate_total_dead_load(self_weight)  # 基础总恒载
        Mrk = self.calculate_horizontal_moment_sum()  # 水平力矩之和
        
        # 根据组合类型应用荷载分项系数
        if combination_type in ["normal_standard", "extreme_standard"]:
            # 标准组合：不乘系数
            N = Nk
            N_total = Nk_Gk
            Mr = Mrk
        elif combination_type in ["normal_basic_unfavorable", "extreme_basic_unfavorable"]:
            # 基本组合（恒荷载对结构不利）
            N = Nk * load_factors.dead_load_unfavorable
            N_total = Nk_Gk * load_factors.dead_load_unfavorable
            Mr = Mrk * load_factors.live_load_factor
        elif combination_type in ["normal_basic_favorable", "extreme_basic_favorable"]:
            # 基本组合（恒荷载对结构有利）
            N = Nk * load_factors.dead_load_favorable
            N_total = Nk_Gk * load_factors.dead_load_favorable
            Mr = Mrk * load_factors.live_load_factor
        else:
            # 默认为标准组合
            N = Nk
            N_total = Nk_Gk
            Mr = Mrk
        
        # 几何参数
        base_radius = self.geometry.base_radius
        column_radius = self.geometry.column_radius
        diameter = 2 * base_radius
        
        # 确定实际受压面积
        if compressed_area is None:
            # 如果没有传入 compressed_area，则使用基础底板面积作为默认值
            compressed_area = math.pi * base_radius**2
        
        # 计算惯性矩 I = π/64 × D⁴
        I = (math.pi / 64) * diameter**4
        
        # 计算基础底面净反力 Pj = N/A + (Mr/I)×(2R+r1)/3
        # 第一项: N/A (使用实际受压面积)
        first_term = N / compressed_area
        
        # 第二项: (Mr/I) × (2R + r1) / 3
        second_term = (Mr / I) * (2 * base_radius + column_radius) / 3
        
        # 基础底面净反力 Pj
        net_pressure = first_term + second_term
        
        return net_pressure
    
    def calculate_max_net_pressure(self, self_weight: SelfWeightResult) -> float:
        """
        计算基础底面最大净反力
        
        公式: Pkmax = (Nk+Gk)/A + Mrk/W
        其中: A = π×基础底板半径², W = π/32×直径³
        
        Args:
            self_weight: 自重计算结果
            
        Returns:
            float: 基础底面最大净反力(kPa)
        """
        # 基础总恒载 Nk+Gk (这里Nk包含了Gk，所以直接使用total_dead_load)
        total_dead_load = self.calculate_total_dead_load(self_weight)
        
        # 水平力矩之和 Mrk
        horizontal_moment = self.calculate_horizontal_moment_sum()
        
        # 基础底板半径
        base_radius = self.geometry.base_radius
        
        # 基础底板面积 A = π × R²
        base_area = math.pi * base_radius**2
        
        # 抗弯截面模量 W = π/32 × D³ (D = 2R)
        diameter = 2 * base_radius
        section_modulus = (math.pi / 32) * diameter**3
        
        # 第一项: (Nk+Gk)/A
        first_term = total_dead_load / base_area
        
        # 第二项: Mrk/W
        second_term = horizontal_moment / section_modulus
        
        # 基础底面最大净反力 Pkmax
        max_net_pressure = first_term + second_term
        
        return max_net_pressure

    def calculate_min_net_pressure(self, self_weight: SelfWeightResult) -> float:
        """
        计算基础底面最小净反力
        
        公式: Pkmin = (Nk+Gk)/A - Mrk/W
        其中: A = π×基础底板半径², W = π/32×直径³
        
        Args:
            self_weight: 自重计算结果
            
        Returns:
            float: 基础底面最小净反力(kPa)
        """
        # 基础总恒载 Nk+Gk
        total_dead_load = self.calculate_total_dead_load(self_weight)
        
        # 水平力矩之和 Mrk
        horizontal_moment = self.calculate_horizontal_moment_sum()
        
        # 基础底板半径
        base_radius = self.geometry.base_radius
        
        # 基础底板面积 A = π × R²
        base_area = math.pi * base_radius**2
        
        # 抗弯截面模量 W = π/32 × D³ (D = 2R)
        diameter = 2 * base_radius
        section_modulus = (math.pi / 32) * diameter**3
        
        # 第一项: (Nk+Gk)/A
        first_term = total_dead_load / base_area
        
        # 第二项: Mrk/W
        second_term = horizontal_moment / section_modulus
        
        # 基础底面最小净反力 Pkmin
        min_net_pressure = first_term - second_term
        
        return min_net_pressure

    def calculate_simple_pk(self, self_weight: SelfWeightResult) -> Dict:
        """
        计算Pk的简单方法
        
        使用简化公式：Pk = (Nk+Gk)/A
        同时根据偏心距和基础半径的比值，调用foundation_pressure_coefficients类中的插值方法，
        获取τ和ξ系数，计算受压区高度=τR
        
        Args:
            self_weight: 自重计算结果
            
        Returns:
            Dict: 包含以下键值的字典
                - pk: 基础底面净反力 Pk (kPa)
                - eccentricity: 偏心距 e (m)
                - e_over_r: 偏心距与基础半径的比值 e/R
                - tau: τ系数
                - xi: ξ系数
                - compressed_height: 受压区高度 τR (m)
        """
        # 基础总恒载 Nk+Gk
        total_dead_load = self.calculate_total_dead_load(self_weight)
        
        # 基础底板半径
        base_radius = self.geometry.base_radius
        
        # 基础底板面积 A = π × R²
        base_area = math.pi * base_radius**2
        
        # 简化公式计算Pk
        pk = total_dead_load / base_area
        
        # 计算偏心距 e = Mrk/(Nk+Gk)
        horizontal_moment = self.calculate_horizontal_moment_sum()
        eccentricity = horizontal_moment / total_dead_load if total_dead_load > 0 else 0
        
        # 计算偏心距与基础半径的比值 e/R
        e_over_r = eccentricity / base_radius if base_radius > 0 else 0
        
        # 通过插值获取τ和ξ系数
        tau, xi = foundation_pressure_coefficients.get_coefficients_by_interpolation(
            e_over_r1=e_over_r, 
            r2_over_r1=0.0  # 假设为实心圆形基础
        )
        
        # 计算受压区高度 = τR
        compressed_height = tau * base_radius
        
        logger.info(f"简化Pk计算结果: Pk={pk:.3f}kPa, e={eccentricity:.3f}m, e/R={e_over_r:.3f}")
        logger.info(f"插值系数: τ={tau:.3f}, ξ={xi:.3f}, 受压区高度={compressed_height:.3f}m")
        
        return {
            'pk': pk,
            'eccentricity': eccentricity,
            'e_over_r': e_over_r,
            'tau': tau,
            'xi': xi,
            'compressed_height': compressed_height
        }
    
    def calculate_coefficients_by_eccentricity(self, eccentricity: float) -> Dict:
        """
        根据给定的偏心距计算τ和ξ系数
        
        Args:
            eccentricity: 偏心距 (m)
            
        Returns:
            Dict: 包含τ和ξ系数的字典
            
        Raises:
            ValueError: 当e/r1 > 0.52时，基础设计不合理
        """
        # 基础底板半径
        base_radius = self.geometry.base_radius
        
        # 计算偏心距与基础半径的比值 e/R
        e_over_r = eccentricity / base_radius if base_radius > 0 else 0
        
        # 检查实心圆形基础的 e/r1 限制
        if e_over_r > 0.52:
            error_msg = (
                f"基础设计不合理：偏心距与基础半径比值 e/r1 = {e_over_r:.3f} > 0.52，"
                f"偏心距 {eccentricity:.3f}m 超过基础半径 {base_radius:.3f}m 的一半。"
                f"此时基础接近失稳状态，请重新设计基础尺寸或减小作用荷载。"
            )
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # 通过插值获取τ和ξ系数
        tau, xi = foundation_pressure_coefficients.get_coefficients_by_interpolation(
            e_over_r1=e_over_r, 
            r2_over_r1=0.0  # 假设为实心圆形基础
        )
        
        # 计算受压区高度 = τR
        compressed_height = tau * base_radius
        
        logger.info(f"根据偏心距{eccentricity:.3f}m计算系数: e/R={e_over_r:.3f}, τ={tau:.3f}, ξ={xi:.3f}")
        
        return {
            'eccentricity': eccentricity,
            'e_over_r': e_over_r,
            'tau': tau,
            'xi': xi,
            'compressed_height': compressed_height
        }

    def calculate_basic_combination_design_values(self, self_weight: SelfWeightResult, load_factor: float) -> Dict:
        """
        计算基本组合荷载设计值
        
        Args:
            self_weight: 自重计算结果
            load_factor: 荷载分项系数
            
        Returns:
            Dict: 包含设计值的字典
        """
        # 荷载设计值 = 荷载标准值 × 分项系数
        design_Fv = self.condition.Fv * load_factor
        design_N_G = (self.condition.Fz + self_weight.total_weight) * load_factor
        design_Mx = self.condition.Mx * load_factor
        design_Mz = self.condition.Mz * load_factor
        
        return {
            "design_Fv": design_Fv,
            "design_N_G": design_N_G, 
            "design_Mx": design_Mx,
            "design_Mz": design_Mz,
            "load_factor": load_factor
        }
    
    def calculate_basic_combination_eccentricity(self, self_weight: SelfWeightResult, load_factor: float) -> float:
        """
        计算基本组合偏心距
        
        公式: e = Mx / (N + G)
        
        Args:
            self_weight: 自重计算结果
            load_factor: 荷载分项系数
            
        Returns:
            float: 偏心距(m)
        """
        design_values = self.calculate_basic_combination_design_values(self_weight, load_factor)
        return design_values["design_Mx"] / design_values["design_N_G"]
    
    def calculate_basic_combination_max_pressure(self, self_weight: SelfWeightResult, load_factor: float) -> float:
        """
        计算基本组合最大压力
        
        根据偏心距判断受压区高度，采用相应公式计算
        使用《高耸结构设计标准》附录H表H.0.1的系数表进行精确计算
        
        Args:
            self_weight: 自重计算结果
            load_factor: 荷载分项系数
            
        Returns:
            float: 最大压力(kPa)
        """
        design_values = self.calculate_basic_combination_design_values(self_weight, load_factor)
        eccentricity = self.calculate_basic_combination_eccentricity(self_weight, load_factor)
        
        # 基础底板半径
        base_radius = self.geometry.base_radius
        
        # 计算偏心距与基础外半径的比值
        e_over_r1 = eccentricity / base_radius
        
        # 判断偏心距与0.25R的关系
        if e_over_r1 > 0.25:
            # e > 0.25R, 按《高耸结构设计标准》7.2.3计算
            # 使用标准系数表进行插值计算
            
            # 验证参数范围
            is_valid, error_msg = foundation_pressure_coefficients.validate_parameters(e_over_r1)
            if not is_valid:
                logger.warning(f"参数验证失败: {error_msg}，使用边界值计算")
            
            # 获取ξ系数（假设为实心圆形基础，r2/r1 = 0.0）
            xi = foundation_pressure_coefficients.get_xi_coefficient(e_over_r1, r2_over_r1=0.0)
            
            # 使用ξ系数计算最大压力
            # 公式: pmax = N / (ξ × r1²)
            pmax = design_values["design_N_G"] / (xi * base_radius**2)
            
            logger.info(f"偏心距比值 e/r1 = {e_over_r1:.3f}, 插值得到 ξ = {xi:.3f}")
            
        else:
            # e ≤ 0.25R, 全截面受压
            # 使用传统的圆形截面公式
            base_area = math.pi * base_radius**2
            diameter = 2 * base_radius
            section_modulus = (math.pi / 32) * diameter**3
            
            pmax = design_values["design_N_G"] / base_area + design_values["design_Mx"] / section_modulus
            
            logger.info(f"偏心距比值 e/r1 = {e_over_r1:.3f} ≤ 0.25，采用全截面受压公式")
        
        return pmax
    
    def calculate_basic_combination_average_pressure(self, self_weight: SelfWeightResult, load_factor: float) -> float:
        """
        计算基本组合平均压力
        
        公式: P = (N + G) / A
        
        Args:
            self_weight: 自重计算结果
            load_factor: 荷载分项系数
            
        Returns:
            float: 平均压力(kPa)
        """
        design_values = self.calculate_basic_combination_design_values(self_weight, load_factor)
        base_area = math.pi * self.geometry.base_radius**2
        
        return design_values["design_N_G"] / base_area
        
    def calculate_basic_combination_net_pressure(self, self_weight: SelfWeightResult, load_factor: float) -> float:
        """
        计算基本组合基础底面净反力
        
        公式: Pj = N/A + (Mx × 2R + r1)/I × 1/3
        其中: I = π/64 × D⁴, r1 = 台柱半径
        
        Args:
            self_weight: 自重计算结果
            load_factor: 荷载分项系数
            
        Returns:
            float: 基础底面净反力(kPa)
        """
        design_values = self.calculate_basic_combination_design_values(self_weight, load_factor)
        
        # 基础底板半径和台柱半径
        base_radius = self.geometry.base_radius
        column_radius = self.geometry.column_radius
        
        # 基础底板面积
        base_area = math.pi * base_radius**2
        
        # 惯性矩 I = π/64 × D⁴
        diameter = 2 * base_radius
        I = (math.pi / 64) * diameter**4
        
        # 第一项: N/A
        first_term = design_values["design_N_G"] / base_area
        
        # 第二项: (Mx × 2R + r1)/I × 1/3
        second_term = (design_values["design_Mx"] * (2 * base_radius + column_radius)) / I / 3
        
        return first_term + second_term

    def apply_load_factors(self, load_factors: LoadFactors):
        """应用荷载分项系数"""
        # 根据工况类型选择合适的荷载分项系数
        if self.condition.case_type == LoadCase.BASIC_COMBINATION_FAVORABLE:
            factor = load_factors.dead_load_favorable
        elif self.condition.case_type == LoadCase.BASIC_COMBINATION_UNFAVORABLE:
            factor = load_factors.dead_load_unfavorable
        elif self.condition.case_type in [LoadCase.FREQUENT_EARTHQUAKE, LoadCase.RARE_EARTHQUAKE]:
            factor = load_factors.seismic_horizontal
        else:
            factor = load_factors.dead_load_unfavorable
        
        self.condition.Fr *= factor
        self.condition.Fv *= factor
        self.condition.Fz *= factor
        self.condition.Mx *= factor
        self.condition.My *= factor
        self.condition.Mz *= factor
    
    def calculate_total_loads(self, loading_condition: LoadingCondition, self_weight: float):
        """计算总荷载"""
        self.total_horizontal_load = math.sqrt(
            loading_condition.Fr**2 + 
            (self.wind_load + self.seismic_load)**2
        )
        
        self.total_vertical_load = (
            loading_condition.Fv + 
            loading_condition.Fz + 
            self_weight
        )
        
        self.total_moment = math.sqrt(
            loading_condition.Mx**2 + 
            loading_condition.My**2
        )
    
    def apply_load_factors_by_case(self, load_factors: LoadFactors, load_case: LoadCase):
        """根据工况应用荷载分项系数"""
        # 根据工况类型选择合适的荷载分项系数
        if load_case == LoadCase.BASIC_COMBINATION_FAVORABLE:
            factor = load_factors.dead_load_favorable
        elif load_case == LoadCase.BASIC_COMBINATION_UNFAVORABLE:
            factor = load_factors.dead_load_unfavorable
        elif load_case in [LoadCase.FREQUENT_EARTHQUAKE, LoadCase.RARE_EARTHQUAKE]:
            factor = load_factors.seismic_horizontal
        else:
            factor = load_factors.dead_load_unfavorable
        
        self.wind_load *= factor
        self.seismic_load *= factor
        self.total_horizontal_load *= factor
        self.total_vertical_load *= factor
        self.total_moment *= factor
    
    def validate_loads(self) -> bool:
        """验证荷载数据"""
        return all(load >= 0 for load in [
            self.wind_load, 
            self.seismic_load, 
            self.total_horizontal_load,
            abs(self.total_vertical_load)  # 竖向荷载可以为负（上拔）
        ])
