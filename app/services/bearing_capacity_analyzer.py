"""
地基承载力验算器
实现地基承载力特征值计算、抗震承载力计算以及各工况下的地基压力验算
"""
import math
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from app.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class BearingCapacityParameters:
    """地基承载力计算参数"""
    # 基础几何参数
    b: float  # 基础圆台直径(m)
    d: float  # 基础埋深(m)
    
    # 土层参数
    fak: float  # 承载力特征值(kPa)
    eta_b: float  # 宽度修正系数
    eta_d: float  # 深度修正系数
    zeta_a: float  # 地基抗震承载力修正系数
    gamma_m: float  # 基础侧面以上土的加权平均重度(kN/m³)
    
    # 荷载参数
    pk_normal: float  # 正常工况下的地基压力(kPa)
    pkmax_normal: float  # 正常工况下的最大地基压力(kPa)
    pk_extreme: float  # 极端工况下的地基压力(kPa)
    pkmax_extreme: float  # 极端工况下的最大地基压力(kPa)
    pek_seismic: float  # 多遇地震工况下的地基压力(kPa)
    pekmax_seismic: float  # 多遇地震工况下的最大地基压力(kPa)


@dataclass
class BearingCapacityResult:
    """地基承载力验算结果"""
    # 计算参数
    b: float  # 基础圆台直径(m)
    d: float  # 基础埋深(m)
    
    # 承载力特征值
    fa: float  # 地基承载力特征值(kPa)
    fae: float  # 地基抗震承载力特征值(kPa)
    
    # 各工况地基压力
    pk_normal: float  # 正常工况地基压力(kPa)
    pkmax_normal: float  # 正常工况最大地基压力(kPa)
    pk_extreme: float  # 极端工况地基压力(kPa)
    pkmax_extreme: float  # 极端工况最大地基压力(kPa)
    pek_seismic: float  # 多遇地震工况地基压力(kPa)
    pekmax_seismic: float  # 多遇地震工况最大地基压力(kPa)
    
    # 符合性检查结果
    normal_condition_compliant: bool  # 正常工况是否满足
    extreme_condition_compliant: bool  # 极端工况是否满足
    seismic_condition_compliant: bool  # 多遇地震工况是否满足
    overall_compliant: bool  # 整体是否满足
    
    # 详细检查信息
    normal_check_details: str  # 正常工况检查详情
    extreme_check_details: str  # 极端工况检查详情
    seismic_check_details: str  # 多遇地震工况检查详情


class BearingCapacityAnalyzer:
    """地基承载力验算器"""
    
    def __init__(self):
        """初始化验算器"""
        self.logger = get_logger(__name__)
    
    def calculate_bearing_capacity_characteristic_value(
        self, 
        fak: float, 
        eta_b: float, 
        eta_d: float, 
        b: float, 
        d: float, 
        gamma_m: float
    ) -> float:
        """
        计算地基承载力特征值fa
        
        根据《陆上风电场工程风电机组基础设计规范》6.3.1条规定：
        fa = fak + η_b * γ_m * (b - 3) + η_d * γ_m * (d - 0.5)
        
        当b ≤ 6m时，取b = 6m
        当b > 6m时，取实际值
        
        Args:
            fak: 承载力特征值(kPa)
            eta_b: 宽度修正系数
            eta_d: 深度修正系数
            b: 基础圆台直径(m)
            d: 基础埋深(m)
            gamma_m: 基础侧面以上土的加权平均重度(kN/m³)
            
        Returns:
            float: 地基承载力特征值fa(kPa)
        """
        try:
            # 根据规范要求判断b值取值
            if b <= 6.0:
                b_effective = 6.0
                self.logger.info(f"基础直径b={b}m ≤ 6m，按6m计算")
            else:
                b_effective = b
                self.logger.info(f"基础直径b={b}m > 6m，按实际值计算")
            
            # 计算地基承载力特征值
            fa = fak + eta_b * gamma_m * (b_effective - 3.0) + eta_d * gamma_m * (d - 0.5)
            
            self.logger.info(f"地基承载力特征值计算: fa = {fak} + {eta_b} × {gamma_m} × ({b_effective} - 3) + {eta_d} × {gamma_m} × ({d} - 0.5) = {fa:.3f}kPa")
            
            return fa
            
        except Exception as e:
            self.logger.error(f"地基承载力特征值计算失败: {str(e)}")
            raise ValueError(f"地基承载力特征值计算失败: {str(e)}")
    
    def calculate_seismic_bearing_capacity(self, fa: float, zeta_a: float) -> float:
        """
        计算地基抗震承载力特征值fae
        
        根据《陆上风电场工程风电机组基础设计规范》6.3.1条规定：
        fae = ζ_a * fa
        
        Args:
            fa: 地基承载力特征值(kPa)
            zeta_a: 地基抗震承载力修正系数
            
        Returns:
            float: 地基抗震承载力特征值fae(kPa)
        """
        try:
            fae = zeta_a * fa
            self.logger.info(f"地基抗震承载力特征值计算: fae = {zeta_a} × {fa:.3f} = {fae:.3f}kPa")
            return fae
            
        except Exception as e:
            self.logger.error(f"地基抗震承载力特征值计算失败: {str(e)}")
            raise ValueError(f"地基抗震承载力特征值计算失败: {str(e)}")
    
    def check_normal_condition_compliance(self, pk: float, pkmax: float, fa: float) -> Tuple[bool, str]:
        """
        检查正常工况符合性
        
        根据《陆上风电场工程风电机组基础设计规范》6.3.1条规定：
        - pk ≤ fa
        - pkmax ≤ 1.2 * fa
        
        Args:
            pk: 正常工况地基压力(kPa)
            pkmax: 正常工况最大地基压力(kPa)
            fa: 地基承载力特征值(kPa)
            
        Returns:
            Tuple[bool, str]: (是否符合, 检查详情)
        """
        try:
            pk_check = pk <= fa
            pkmax_check = pkmax <= 1.2 * fa
            
            details = []
            details.append(f"pk={pk:.3f}kPa ≤ fa={fa:.3f}kPa，{'满足' if pk_check else '不满足'}")
            details.append(f"pkmax={pkmax:.3f}kPa ≤ 1.2fa={1.2*fa:.3f}kPa，{'满足' if pkmax_check else '不满足'}")
            
            compliance = pk_check and pkmax_check
            details_str = f"《陆上风电场工程风电机组基础设计规范》6.3.1条规定。{'; '.join(details)}"
            
            self.logger.info(f"正常工况符合性检查: {compliance}, {details_str}")
            return compliance, details_str
            
        except Exception as e:
            self.logger.error(f"正常工况符合性检查失败: {str(e)}")
            return False, f"检查失败: {str(e)}"
    
    def check_extreme_condition_compliance(self, pk: float, pkmax: float, fa: float) -> Tuple[bool, str]:
        """
        检查极端工况符合性
        
        根据《陆上风电场工程风电机组基础设计规范》6.3.1条规定：
        - pk ≤ fa
        - pkmax ≤ 1.2 * fa
        
        Args:
            pk: 极端工况地基压力(kPa)
            pkmax: 极端工况最大地基压力(kPa)
            fa: 地基承载力特征值(kPa)
            
        Returns:
            Tuple[bool, str]: (是否符合, 检查详情)
        """
        try:
            pk_check = pk <= fa
            pkmax_check = pkmax <= 1.2 * fa
            
            details = []
            details.append(f"pk={pk:.3f}kPa ≤ fa={fa:.3f}kPa，{'满足' if pk_check else '不满足'}")
            details.append(f"pkmax={pkmax:.3f}kPa ≤ 1.2fa={1.2*fa:.3f}kPa，{'满足' if pkmax_check else '不满足'}")
            
            compliance = pk_check and pkmax_check
            details_str = f"《陆上风电场工程风电机组基础设计规范》6.3.1条规定。{'; '.join(details)}"
            
            self.logger.info(f"极端工况符合性检查: {compliance}, {details_str}")
            return compliance, details_str
            
        except Exception as e:
            self.logger.error(f"极端工况符合性检查失败: {str(e)}")
            return False, f"检查失败: {str(e)}"
    
    def check_seismic_condition_compliance(self, pek: float, pekmax: float, fae: float) -> Tuple[bool, str]:
        """
        检查多遇地震工况符合性
        
        根据《陆上风电场工程风电机组基础设计规范》6.3.1条规定：
        - pek ≤ fae
        - pekmax ≤ 1.2 * fae
        
        Args:
            pek: 多遇地震工况地基压力(kPa)
            pekmax: 多遇地震工况最大地基压力(kPa)
            fae: 地基抗震承载力特征值(kPa)
            
        Returns:
            Tuple[bool, str]: (是否符合, 检查详情)
        """
        try:
            pek_check = pek <= fae
            pekmax_check = pekmax <= 1.2 * fae
            
            details = []
            details.append(f"pek={pek:.3f}kPa ≤ fae={fae:.3f}kPa，{'满足' if pek_check else '不满足'}")
            details.append(f"pekmax={pekmax:.3f}kPa ≤ 1.2fae={1.2*fae:.3f}kPa，{'满足' if pekmax_check else '不满足'}")
            
            compliance = pek_check and pekmax_check
            details_str = f"《陆上风电场工程风电机组基础设计规范》6.3.1条规定。{'; '.join(details)}"
            
            self.logger.info(f"多遇地震工况符合性检查: {compliance}, {details_str}")
            return compliance, details_str
            
        except Exception as e:
            self.logger.error(f"多遇地震工况符合性检查失败: {str(e)}")
            return False, f"检查失败: {str(e)}"
    
    def analyze_bearing_capacity(self, params: BearingCapacityParameters) -> BearingCapacityResult:
        """
        执行地基承载力验算
        
        Args:
            params: 地基承载力计算参数
            
        Returns:
            BearingCapacityResult: 地基承载力验算结果
        """
        try:
            self.logger.info("开始地基承载力验算")
            
            # 1. 计算地基承载力特征值fa
            fa = self.calculate_bearing_capacity_characteristic_value(
                params.fak, params.eta_b, params.eta_d, 
                params.b, params.d, params.gamma_m
            )
            
            # 2. 计算地基抗震承载力特征值fae
            fae = self.calculate_seismic_bearing_capacity(fa, params.zeta_a)
            
            # 3. 检查正常工况符合性
            normal_compliant, normal_details = self.check_normal_condition_compliance(
                params.pk_normal, params.pkmax_normal, fa
            )
            
            # 4. 检查极端工况符合性
            extreme_compliant, extreme_details = self.check_extreme_condition_compliance(
                params.pk_extreme, params.pkmax_extreme, fa
            )
            
            # 5. 检查多遇地震工况符合性
            seismic_compliant, seismic_details = self.check_seismic_condition_compliance(
                params.pek_seismic, params.pekmax_seismic, fae
            )
            
            # 6. 整体符合性判断
            overall_compliant = normal_compliant and extreme_compliant and seismic_compliant
            
            # 7. 组装结果
            result = BearingCapacityResult(
                b=params.b,
                d=params.d,
                fa=fa,
                fae=fae,
                pk_normal=params.pk_normal,
                pkmax_normal=params.pkmax_normal,
                pk_extreme=params.pk_extreme,
                pkmax_extreme=params.pkmax_extreme,
                pek_seismic=params.pek_seismic,
                pekmax_seismic=params.pekmax_seismic,
                normal_condition_compliant=normal_compliant,
                extreme_condition_compliant=extreme_compliant,
                seismic_condition_compliant=seismic_compliant,
                overall_compliant=overall_compliant,
                normal_check_details=normal_details,
                extreme_check_details=extreme_details,
                seismic_check_details=seismic_details
            )
            
            self.logger.info(f"地基承载力验算完成，整体符合性: {overall_compliant}")
            return result
            
        except Exception as e:
            self.logger.error(f"地基承载力验算失败: {str(e)}")
            raise ValueError(f"地基承载力验算失败: {str(e)}")