"""
地基变形计算模块
用于计算风力发电机基础的沉降和倾斜
根据《陆上风电场工程风电机组基础设计规范》6.4.1条、6.4.2条、6.4.3条进行
沉降和倾斜变形验算
"""
import math
from typing import Dict, Optional, List, Any, Tuple
from app.schemas import FoundationGeometry, SoilLayer
from app.schemas.settlement import SettlementLayerDetail
from app.utils.soil_layer_selector import select_soil_layer_by_depth
from app.utils.logger import get_logger

logger = get_logger(__name__)


class SettlementAnalyzer:
    """地基变形计算类
    
    用于计算风力发电机基础的沉降和倾斜，并验证结果是否满足要求
    
    属性:
        final_settlement: 最终沉降(mm)
        allowable_settlement: 允许沉降(mm)
        inclination: 倾斜率
        allowable_inclination: 允许倾斜率
        additional_stress: 附加应力P0k(kPa)
        psi_value: 沉降计算经验系数
    """
    
    def __init__(self, 
                 geometry: FoundationGeometry,
                 soil_layers: List[Dict[str, Any]],
                 pk_value: float,
                 pkmax: float,
                 pkmin: float,
                 ps_value: Optional[float] = None,
                 groundwater_depth: Optional[float] = None,
                 allowable_settlement: float = 100.0,
                 allowable_inclination: float = 0.003):
        """初始化地基变形计算器
        
        Args:
            geometry: 基础几何信息
            soil_layers: 土层信息列表
            pk_value: 对应工况下的Pk（标准值）或P（设计值）(kPa)
            ps_value: 土层自重应力，如果为None则自动计算
            groundwater_depth: 地下水埋深(m)，None表示无地下水
            allowable_settlement: 允许沉降(mm)，默认100mm
            allowable_inclination: 允许倾斜率，默认0.003
        """
        self.geometry = geometry
        self.soil_layers = soil_layers
        self.pk_value = pk_value
        self.ps_value = ps_value
        self.pkmax = pkmax
        self.pkmin = pkmin
        self.groundwater_depth = groundwater_depth
        
        # 计算结果
        self.final_settlement = 0.0
        self.allowable_settlement = allowable_settlement
        self.inclination = 0.0
        self.allowable_inclination = allowable_inclination
        self.additional_stress = 0.0  # P0k = Pk - Ps
        self.psi_value = 0.0  # 沉降计算经验系数，通过插值计算获得
        
        # 计算分量
        self.settlement_details: List[SettlementLayerDetail] = []  # 分层沉降详情
        
        # 计算P0k和获取基础底面对应的fak值
        self._calculate_p0k()
        self.foundation_fak = self._get_foundation_fak()
        
        # 等效Es值和ψs系数将在沉降计算循环中动态计算
        
    def _calculate_p0k(self) -> None:
        """计算附加应力P0k = Pk - Ps"""
        if self.ps_value is None:
            self.ps_value = self._calculate_ps()
        self.additional_stress = self.pk_value - self.ps_value
    
    def _calculate_ps(self) -> float:
        """计算土层自重应力Ps
        
        根据基础埋深与各土层标高比对，获取土层的平均重力密度
        当有浮力时，埋深水以下的基础部分的土层容重要减掉10
        """
        if not self.soil_layers:
            logger.warning("无土层信息，Ps设为0")
            return 0.0
            
        total_stress = 0.0
        current_depth = 0.0
        buried_depth = self.geometry.buried_depth
        
        # 按标高排序土层（从浅到深）
        sorted_layers = sorted(self.soil_layers, key=lambda x: abs(x.get('elevation', 0)))
        
        for layer in sorted_layers:
            layer_elevation = abs(layer.get('elevation', 0))  # 土层顶部深度
            layer_thickness = layer.get('thickness', 0)
            layer_density = layer.get('density', 18.0)
            layer_name = layer.get('layerName') or layer.get('layer_name', '未知土层')
            
            layer_bottom_depth = layer_elevation + layer_thickness
            
            # 判断土层是否在基础埋深范围内
            if layer_elevation < buried_depth and layer_bottom_depth > current_depth:
                # 计算重叠部分
                overlap_start = max(layer_elevation, current_depth)
                overlap_end = min(layer_bottom_depth, buried_depth)
                overlap_thickness = overlap_end - overlap_start
                
                if overlap_thickness > 0:
                    # 判断是否在地下水以下
                    effective_density = layer_density
                    if (self.groundwater_depth is not None and 
                        overlap_start >= self.groundwater_depth):
                        # 地下水以下，重度减去10
                        effective_density = layer_density - 10.0
                        logger.debug(f"土层 '{layer_name}' 在地下水以下，有效重度: {effective_density}kN/m³")
                    
                    layer_stress = effective_density * overlap_thickness
                    total_stress += layer_stress
                    
                    logger.debug(f"土层 '{layer_name}': 深度{overlap_start}-{overlap_end}m, "
                               f"厚度{overlap_thickness}m, 重度{effective_density}kN/m³, "
                               f"应力{layer_stress:.2f}kPa")
                    
                current_depth = overlap_end
                if current_depth >= buried_depth:
                    break
        
        logger.info(f"Ps计算完成: {total_stress:.3f}kPa")
        return total_stress
    
    def _get_foundation_fak(self) -> float:
        """根据基础埋设与土层的标高对比，取对应土层的fak值"""
        try:
            selected_layer = select_soil_layer_by_depth(self.geometry.buried_depth, self.soil_layers)
            fak = selected_layer.get('fak', 150.0)
            layer_name = selected_layer.get('layerName') or selected_layer.get('layer_name', '未知土层')
            logger.info(f"基础位于土层 '{layer_name}'，fak={fak}kPa")
            return fak
        except Exception as e:
            logger.warning(f"获取fak值失败: {str(e)}，使用默认值150kPa")
            return 150.0
    
    def _calculate_equivalent_es(self) -> float:
        """计算等效压缩模量Es
        
        使用公式: Es = Σ(Zi·ᾱi - Zi-1·ᾱi-1) / Σ((Zi·ᾱi - Zi-1·ᾱi-1)/Esi)
        
        Returns:
            float: 等效压缩模量(MPa)
        """
        logger.info("开始计算等效压缩模量Es")
        
        base_radius = self.geometry.base_radius
        layer_thickness = 1.0  # 分层厚度1m
        first_offset = 0.8  # 第一层从0.8m开始
        convergence_ratio = 0.025  # 收敛条件
        max_layers = 50  # 最大层数限制
        buried_depth = self.geometry.buried_depth
        
        numerator = 0.0    # 分子
        denominator = 0.0  # 分母
        
        # 动态分层计算，与沉降计算保持一致
        for i in range(max_layers):
            # 计算zi（距基础底面的距离）
            if i == 0:
                zi = first_offset  # 第1层底面距基础底面0.8m
                zi_prev = 0.0  # 第0层（基础底面）
            else:
                zi = first_offset + i * layer_thickness
                zi_prev = first_offset + (i-1) * layer_thickness
            
            # 计算绝对深度用于查找土层
            absolute_depth = buried_depth + zi
            
            # 计算应力系数
            alpha_i = self._calculate_stress_coefficient(zi, base_radius)
            alpha_i_prev = self._calculate_stress_coefficient(zi_prev, base_radius) if i > 0 else 0
            
            # 获取该深度对应的压缩模量
            esi = self._get_compression_modulus_at_depth(absolute_depth)
            
            # 计算分子分母项
            delta_term = zi * alpha_i - zi_prev * alpha_i_prev
            numerator += delta_term
            if esi > 0:
                denominator += delta_term / esi
            
            logger.debug(f"ES计算第{i+1}层: Zi={zi:.1f}m, Esi={esi:.1f}MPa, "
                        f"delta_term={delta_term:.6f}, 累计分子={numerator:.6f}, 累计分母={denominator:.6f}")
            
            # 简化的收敛检查：当delta_term足够小时停止
            if abs(delta_term) < 0.001:  # 当增量很小时停止
                logger.info(f"ES计算收敛，停止在第{i+1}层")
                break
        
        # 计算等效压缩模量
        if denominator > 0:
            equivalent_es = numerator / denominator
        else:
            equivalent_es = 20.0  # 默认值
            
        logger.info(f"等效压缩模量Es计算完成: {equivalent_es:.3f}MPa")
        return equivalent_es
    
    def _calculate_psi_s(self) -> float:
        """根据表6.4.2插值计算沉降计算经验系数ψs
        
        表6.4.2的数据:
        Es(MPa): 2.5, 4.0, 7.0, 15.0, 20.0
        p0k≥fak: 1.4, 1.3, 1.0, 0.4, 0.2
        p0k≤0.75fak: 1.1, 1.0, 0.7, 0.4, 0.2
        
        Returns:
            float: 沉降计算经验系数ψs
        """
        logger.info("开始插值计算ψs")
        
        # 表6.4.2的数据
        es_values = [2.5, 4.0, 7.0, 15.0, 20.0]
        
        # 判断P0k与fak的关系
        if self.additional_stress >= self.foundation_fak:
            # p0k ≥ fak 的情况
            psi_values = [1.4, 1.3, 1.0, 0.4, 0.2]
            relationship = "p0k ≥ fak"
        elif self.additional_stress <= 0.75 * self.foundation_fak:
            # p0k ≤ 0.75fak 的情况
            psi_values = [1.1, 1.0, 0.7, 0.4, 0.2]
            relationship = "p0k ≤ 0.75fak"
        else:
            # 0.75fak < p0k < fak 的情况，需要在两行之间插值
            psi_values_upper = [1.4, 1.3, 1.0, 0.4, 0.2]  # p0k ≥ fak
            psi_values_lower = [1.1, 1.0, 0.7, 0.4, 0.2]  # p0k ≤ 0.75fak
            
            # 线性插值系数
            ratio = (self.additional_stress - 0.75 * self.foundation_fak) / (0.25 * self.foundation_fak)
            psi_values = [lower + ratio * (upper - lower) 
                         for lower, upper in zip(psi_values_lower, psi_values_upper)]
            relationship = f"0.75fak < p0k < fak (插值比例: {ratio:.3f})"
        
        # 根据Es值进行插值
        es = self.equivalent_es
        
        if es <= es_values[0]:
            # Es小于最小值，使用第一个值
            psi_s = psi_values[0]
            logger.info(f"Es={es:.3f}MPa ≤ {es_values[0]}MPa，使用ψs={psi_s}")
        elif es >= es_values[-1]:
            # Es大于最大值，使用最后一个值
            psi_s = psi_values[-1]
            logger.info(f"Es={es:.3f}MPa ≥ {es_values[-1]}MPa，使用ψs={psi_s}")
        else:
            # 在范围内，进行线性插值
            for i in range(len(es_values) - 1):
                if es_values[i] <= es <= es_values[i + 1]:
                    # 线性插值
                    ratio = (es - es_values[i]) / (es_values[i + 1] - es_values[i])
                    psi_s = psi_values[i] + ratio * (psi_values[i + 1] - psi_values[i])
                    logger.info(f"Es插值: {es_values[i]}MPa ≤ {es:.3f}MPa ≤ {es_values[i+1]}MPa，"
                              f"插值ψs={psi_s:.5f}")
                    break
            else:
                psi_s = 0.63330  # 默认值
        
        logger.info(f"ψs计算完成: P0k={self.additional_stress:.3f}kPa, fak={self.foundation_fak:.1f}kPa")
        logger.info(f"关系判断: {relationship}")
        logger.info(f"等效Es={es:.3f}MPa, 最终ψs={psi_s:.5f}")
        
        return psi_s

    def _calculate_psi_s_by_es(self, es: float) -> float:
        """根据给定的Es值计算ψs系数
        
        Args:
            es: 等效压缩模量(MPa)
            
        Returns:
            float: ψs系数
        """
        # 表6.4.2的数据
        es_values = [2.5, 4.0, 7.0, 15.0, 20.0]
        
        # 判断P0k与fak的关系
        if self.additional_stress >= self.foundation_fak:
            # p0k ≥ fak 的情况
            psi_values = [1.4, 1.3, 1.0, 0.4, 0.2]
        elif self.additional_stress <= 0.75 * self.foundation_fak:
            # p0k ≤ 0.75fak 的情况
            psi_values = [1.1, 1.0, 0.7, 0.4, 0.2]
        else:
            # 0.75fak < p0k < fak 的情况，需要在两行之间插值
            psi_values_upper = [1.4, 1.3, 1.0, 0.4, 0.2]  # p0k ≥ fak
            psi_values_lower = [1.1, 1.0, 0.7, 0.4, 0.2]  # p0k ≤ 0.75fak
            
            # 线性插值系数
            ratio = (self.additional_stress - 0.75 * self.foundation_fak) / (0.25 * self.foundation_fak)
            psi_values = [lower + ratio * (upper - lower) 
                         for lower, upper in zip(psi_values_lower, psi_values_upper)]
        
        # 根据Es值进行插值
        if es <= es_values[0]:
            return psi_values[0]
        elif es >= es_values[-1]:
            return psi_values[-1]
        else:
            for i in range(len(es_values) - 1):
                if es_values[i] <= es <= es_values[i + 1]:
                    ratio = (es - es_values[i]) / (es_values[i + 1] - es_values[i])
                    return psi_values[i] + ratio * (psi_values[i + 1] - psi_values[i])
        
        return 0.63330  # 默认值

    def calculate_settlement(self) -> float:
        """计算沉降
        
        使用分层总和法计算基础沉降
        公式: s = ψs * ∑(P0k/Esi)(Zi·ᾱi - Zi-1·ᾱi-1)
        
        Returns:
            float: 计算得到的沉降值(mm)
        """
        logger.info("开始沉降计算")
        
        total_settlement = 0.0 # 累计沉降
        self.settlement_details: List[SettlementLayerDetail] = [] # 沉降计算详情
        
        # 计算分层参数
        layer_thickness = 1.0  # 计算分层厚度：1.0m
        first_offset = 0.8  # 第一层相对基础底面偏移0.8m
        convergence_ratio = 0.025  # 收敛条件：Δs'i/s' ≤ 0.025
        max_layers = 50  # 最大层数限制，防止无限循环
        
        buried_depth = self.geometry.buried_depth # 基础埋深
        base_radius = self.geometry.base_radius # 基础底板半径
        
        # 等效压缩模量ES计算的累积变量
        es_numerator = 0.0    # ES计算分子：Σ(Zi·ᾱi - Zi-1·ᾱi-1)
        es_denominator = 0.0  # ES计算分母：Σ((Zi·ᾱi - Zi-1·ᾱi-1)/Esi)
        
        # 动态分层计算沉降
        layer_count = 0
        for i in range(max_layers):
            layer_count += 1
            
            # 计算zi（距基础底面的距离）和对应的绝对深度
            if i == 0:
                zi = first_offset  # 第1层底面距基础底面0.8m
                zi_prev = 0.0  # 第0层（基础底面）
            else:
                zi = first_offset + i * layer_thickness  # 第i+1层底面距基础底面的距离
                zi_prev = first_offset + (i-1) * layer_thickness  # 第i层底面距基础底面的距离
            
            # 计算绝对深度（距地面的深度）用于查找对应土层
            absolute_depth = buried_depth + zi
            
            # 计算平均附加应力系数 ᾱi（根据规范表D.0.3插值计算）
            # 对圆形基础，在深度zi处的应力系数
            alpha_i = self._calculate_stress_coefficient(zi, base_radius)
            alpha_i_prev = self._calculate_stress_coefficient(zi_prev, base_radius) if i > 0 else 0
            
            # 获取该深度对应的土层压缩模量
            esi = self._get_compression_modulus_at_depth(absolute_depth)
            
            # 计算当前层的应力分布项
            delta_term = zi * alpha_i - zi_prev * alpha_i_prev
            
            # 累积等效压缩模量ES的计算项
            es_numerator += delta_term
            if esi > 0:
                es_denominator += delta_term / esi
            
            # 计算当前的等效压缩模量ES
            current_es = es_numerator / es_denominator if es_denominator > 0 else 20.0
            
            # 根据当前ES值计算ψs系数
            current_psi_s = self._calculate_psi_s_by_es(current_es)
            
            # 计算该层沉降 ΔSi = (P0k/Esi)(Zi·ᾱi - Zi-1·ᾱi-1)
            delta_s_i = (self.additional_stress / esi) * delta_term
            total_settlement += delta_s_i
            
            # 计算当前层沉降与累积沉降的比值
            settlement_ratio = delta_s_i / total_settlement
            
            # 记录分层详情
            layer_detail = SettlementLayerDetail(
                layer=layer_count,
                zi=zi,
                absolute_depth=absolute_depth,
                esi=esi,
                alpha_i=alpha_i,
                delta_term=delta_term,
                current_es=current_es,
                current_psi_s=current_psi_s,
                delta_s=delta_s_i,  # mm
                cumulative_s=total_settlement,  # mm
                settlement_ratio=settlement_ratio
            )
            self.settlement_details.append(layer_detail)
            
            logger.debug(f"第{layer_count}层: Zi={zi:.1f}m, 绝对深度={absolute_depth:.1f}m, z/r={zi/base_radius:.2f}, "
                        f"Esi={esi:.1f}MPa, ᾱi={alpha_i:.3f}, ES={current_es:.3f}MPa, ψs={current_psi_s:.5f}, "
                        f"ΔSi={delta_s_i:.3f}mm, 比值={settlement_ratio:.4f}")
            
            # 检查收敛条件：Δs'i/s' ≤ 0.025
            if settlement_ratio <= convergence_ratio:
                logger.info(f"满足收敛条件 Δs'i/s' = {settlement_ratio:.4f} ≤ {convergence_ratio}，停止计算")
                break
        
        # 记录最终值
        self.equivalent_es = current_es
        self.psi_value = current_psi_s
        
        # 记录总分层数
        logger.info(f"总共计算了 {layer_count} 层，最大深度 {zi:.1f}m")
        logger.info(f"最终等效压缩模量ES: {self.equivalent_es:.3f}MPa")
        logger.info(f"最终沉降计算经验系数ψs: {self.psi_value:.5f}")
        
        # 应用沉降计算经验系数
        self.final_settlement = total_settlement * self.psi_value  # mm
        
        logger.info(f"分层总和沉降: {total_settlement:.3f}mm")
        logger.info(f"最终沉降: s = ψs × {total_settlement:.3f} = {self.final_settlement:.3f}mm")
        
        return self.final_settlement
    
    def calculate_inclination(self) -> float:
        """计算倾斜
        
        根据图片中的逻辑，先计算附加应力P0kmax和P0kmin，
        然后计算三角形荷载和矩形荷载对应的附加应力，
        最后进行三角形分布2点沉降计算、三角形分布1点沉降计算、均匀分布沉降计算
        
        使用公式: tanθ = (s1 - s2) / ac
        Returns:
            float: 计算得到的倾斜率
        """
        try:
            logger.info("开始倾斜计算")
            
            # 1. 计算附加应力P0kmax和P0kmin
            p0kmax, p0kmin = self._calculate_additional_stress_max_min()
            
            # 2. 计算三角形荷载和矩形荷载对应的附加应力
            triangular_stress, rectangular_stress = self._calculate_triangular_rectangular_stress(p0kmax, p0kmin)
            
            # 3. 进行三种沉降计算
            # 三角形分布2点沉降计算
            settlement_triangular_2points = self._calculate_settlement_for_stress(triangular_stress, "triangular_2points")
            
            # 三角形分布1点沉降计算  
            settlement_triangular_1point = self._calculate_settlement_for_stress(triangular_stress, "triangular_1point")
            
            # 均匀分布沉降计算
            settlement_uniform = self._calculate_settlement_for_stress(rectangular_stress, "uniform")
            
            # 4. 根据计算结果计算倾斜率
            # 使用三角形2点沉降的差值来计算倾斜
            s2 = settlement_triangular_2points + settlement_uniform
            s1 = settlement_triangular_1point + settlement_uniform
            
            # 倾斜率 = (s1 - s2) / (2 * base_radius)
            base_diameter = 2 * self.geometry.base_radius
            self.inclination = abs(s2 - s1) / (base_diameter * 1000) #直径是米，要转换成毫米
            
            logger.info(f"倾斜计算完成:")
            return self.inclination
            
        except Exception as e:
            logger.error(f"计算倾斜时发生错误: {str(e)}")
            return 0.0
    
    def _calculate_additional_stress_max_min(self) -> Tuple[float, float]:
        """计算附加应力P0kmax和P0kmin
        
        类似于沉降计算中的P0k计算，但针对最大和最小压力值
        P0kmax = Pkmax - Ps
        P0kmin = Pkmin - Ps
        
        Returns:
            Tuple[float, float]: (P0kmax, P0kmin) 附加应力值(kPa)
        """
        if self.ps_value is None:
            self.ps_value = self._calculate_ps()
            
        p0kmax = self.pkmax - self.ps_value
        p0kmin = self.pkmin - self.ps_value
        
        logger.debug(f"附加应力计算: Pkmax={self.pkmax:.3f}kPa, Pkmin={self.pkmin:.3f}kPa, Ps={self.ps_value:.3f}kPa")
        logger.debug(f"P0kmax={p0kmax:.3f}kPa, P0kmin={p0kmin:.3f}kPa")
        
        return p0kmax, p0kmin
    
    def _calculate_triangular_rectangular_stress(self, p0kmax: float, p0kmin: float) -> Tuple[float, float]:
        """计算三角形荷载和矩形荷载对应的附加应力
        
        根据图片中的逻辑：
        - 矩形荷载应力 = P0kmin（均匀分布的部分）
        - 三角形荷载应力 = P0kmax - P0kmin（变化的部分）
        
        Args:
            p0kmax: 最大附加应力(kPa)
            p0kmin: 最小附加应力(kPa)
            
        Returns:
            Tuple[float, float]: (triangular_stress, rectangular_stress) 三角形和矩形荷载应力(kPa)
        """
        # 矩形荷载应力（均匀分布部分）
        rectangular_stress = p0kmin
        
        # 三角形荷载应力（变化部分）  
        triangular_stress = p0kmax - p0kmin
        
        logger.debug(f"荷载分解: 三角形应力={triangular_stress:.3f}kPa, 矩形应力={rectangular_stress:.3f}kPa")
        
        return triangular_stress, rectangular_stress
    
    def _calculate_settlement_for_stress(self, stress_value: float, stress_type: str) -> float:
        """为给定应力值计算沉降
        
        复用现有的沉降计算逻辑，但使用不同的应力值和计算方式
        
        Args:
            stress_value: 应力值(kPa)
            stress_type: 应力类型 ("triangular_2points", "triangular_1point", "uniform")
            
        Returns:
            float: 沉降值(mm)
        """
        
        logger.debug(f"开始{stress_type}沉降计算，应力值={stress_value:.3f}kPa")
        
        total_settlement = 0.0
        settlement_details = []
        
        # 使用与原沉降计算相同的参数
        layer_thickness = 1.0
        first_offset = 0.8
        convergence_ratio = 0.025
        max_layers = 100
        
        buried_depth = self.geometry.buried_depth
        base_radius = self.geometry.base_radius
        
        # 等效压缩模量ES计算的累积变量
        es_numerator = 0.0
        es_denominator = 0.0
        
        layer_count = 0
        for i in range(max_layers):
            layer_count += 1
            
            # 计算zi和绝对深度
            if i == 0:
                zi = first_offset
                zi_prev = 0.0
            else:
                zi = first_offset + i * layer_thickness
                zi_prev = first_offset + (i-1) * layer_thickness
            
            absolute_depth = buried_depth + zi
            
            # 根据stress_type计算应力系数
            if stress_type == "triangular_2points":
                # 三角形分布2点沉降计算，使用表D.0.4的点2数据
                alpha_i = self._calculate_stress_coefficient_with_points(zi, base_radius, "point2")
                alpha_i_prev = self._calculate_stress_coefficient_with_points(zi_prev, base_radius, "point2") if i > 0 else 0
            elif stress_type == "triangular_1point":
                # 三角形分布1点沉降计算，使用表D.0.4的点1数据
                alpha_i = self._calculate_stress_coefficient_with_points(zi, base_radius, "point1")
                alpha_i_prev = self._calculate_stress_coefficient_with_points(zi_prev, base_radius, "point1") if i > 0 else 0
            else:
                # 均匀分布沉降计算，使用表D.0.3数据
                alpha_i = self._calculate_stress_coefficient(zi, base_radius)
                alpha_i_prev = self._calculate_stress_coefficient(zi_prev, base_radius) if i > 0 else 0
            
            # 获取压缩模量
            esi = self._get_compression_modulus_at_depth(absolute_depth)
            
            # 计算应力分布项
            delta_term = zi * alpha_i - zi_prev * alpha_i_prev
            
            # 累积等效压缩模量ES的计算项
            es_numerator += delta_term
            if esi > 0:
                es_denominator += delta_term / esi
            
            # 计算当前等效压缩模量ES
            current_es = es_numerator / es_denominator if es_denominator > 0 else 20.0
            
            # 根据当前ES值计算ψs系数（使用临时的additional_stress）
            original_stress = self.additional_stress
            self.additional_stress = stress_value  # 临时替换
            current_psi_s = self._calculate_psi_s_by_es(current_es)
            self.additional_stress = original_stress  # 恢复原值
            
            # 计算该层沉降
            delta_s_i = (stress_value / esi) * delta_term
            total_settlement += delta_s_i
            
            # 收敛检查
            settlement_ratio = delta_s_i / total_settlement
            if settlement_ratio <= convergence_ratio:
                logger.debug(f"{stress_type}计算收敛，停止在第{layer_count}层")
                break
        
        # 应用沉降计算经验系数
        final_settlement = total_settlement * current_psi_s
        
        logger.debug(f"{stress_type}沉降计算完成: {final_settlement:.3f}mm (层数:{layer_count})")
        
        return final_settlement
    
    def _calculate_stress_coefficient(self, depth: float, radius: float) -> float:
        """计算附加应力系数ᾱ
        
        根据规范表D.0.3，通过z/r比值插值获取圆形面积上均布荷载作用下中点的附加应力系数ᾱ
        仅用于均匀分布荷载(uniform)的情况
        """
        if depth <= 0:
            return 1.0
            
        # 无量纲深度比 z/r
        z_over_r = depth / radius
        
        # 规范表D.0.3 圆形面积上均布荷载作用下中点的附加应力系数
        # 注意：这里使用的是第三列的ᾱ值（平均附加应力系数）
        alpha_table = {
            0.0: 1.000,
            0.1: 1.000,
            0.2: 0.998,
            0.3: 0.993,
            0.4: 0.986,
            0.5: 0.974,
            0.6: 0.960,
            0.7: 0.942,
            0.8: 0.923,
            0.9: 0.901,
            1.0: 0.878,
            1.1: 0.855,
            1.2: 0.831,
            1.3: 0.808,
            1.4: 0.784,
            1.5: 0.762,
            1.6: 0.739,
            1.7: 0.718,
            1.8: 0.697,
            1.9: 0.677,
            2.0: 0.658,
            2.1: 0.640,
            2.2: 0.623,
            2.3: 0.606,
            2.4: 0.590,
            2.5: 0.574,
            2.6: 0.560,
            2.7: 0.546,
            2.8: 0.532,
            2.9: 0.519,
            3.0: 0.507,
            3.1: 0.495,
            3.2: 0.484,
            3.3: 0.473,
            3.4: 0.463,
            3.5: 0.453,
            3.6: 0.443,
            3.7: 0.434,
            3.8: 0.425,
            3.9: 0.417,
            4.0: 0.409,
            4.1: 0.401,
            4.2: 0.393,
            4.3: 0.386,
            4.4: 0.379,
            4.5: 0.372,
            4.6: 0.365,
            4.7: 0.359,
            4.8: 0.353,
            4.9: 0.347,
            5.0: 0.341
        }
        
        # 如果超出表格范围，使用边界值
        if z_over_r <= 0.0:
            return 1.000
        elif z_over_r >= 5.0:
            return 0.341
        
        # 线性插值
        return self._linear_interpolate(z_over_r, alpha_table)
    
    def _calculate_stress_coefficient_with_points(self, depth: float, radius: float, point_type: str) -> float:
        """计算附加应力系数ᾱ（针对三角形荷载的点1和点2）
        
        根据规范表D.0.4，通过z/r比值插值获取圆形面积上三角形分布荷载作用下的附加应力系数ᾱ
        点1使用正比插值，点2使用反比插值
        
        Args:
            depth: 深度(m)
            radius: 基础半径(m)
            point_type: 点类型，"point1"或"point2"
            
        Returns:
            float: 附加应力系数ᾱ
        """
        if depth <= 0:
            return 1.0 if point_type == "point1" else 0.5
            
        # 无量纲深度比 z/r
        z_over_r = depth / radius
        
        # 规范表D.0.4 圆形面积上三角形分布荷载作用下的附加应力系数ᾱ
        # 根据上传图片中的表格数据，point1对应第2列，point2对应第4列
        table_d04_data = {
            0.0: {"point1": 0.000, "point2": 0.500},
            0.1: {"point1": 0.008, "point2": 0.483},
            0.2: {"point1": 0.016, "point2": 0.466},
            0.3: {"point1": 0.023, "point2": 0.450},
            0.4: {"point1": 0.030, "point2": 0.435},
            0.5: {"point1": 0.035, "point2": 0.420},
            0.6: {"point1": 0.041, "point2": 0.406},
            0.7: {"point1": 0.045, "point2": 0.393},
            0.8: {"point1": 0.050, "point2": 0.380},
            0.9: {"point1": 0.054, "point2": 0.368},
            1.0: {"point1": 0.057, "point2": 0.356},
            1.1: {"point1": 0.061, "point2": 0.344},
            1.2: {"point1": 0.063, "point2": 0.333},
            1.3: {"point1": 0.065, "point2": 0.323},
            1.4: {"point1": 0.067, "point2": 0.313},
            1.5: {"point1": 0.069, "point2": 0.303},
            1.6: {"point1": 0.070, "point2": 0.294},
            1.7: {"point1": 0.071, "point2": 0.286},
            1.8: {"point1": 0.072, "point2": 0.278},
            1.9: {"point1": 0.072, "point2": 0.270},
            2.0: {"point1": 0.073, "point2": 0.263},
            2.1: {"point1": 0.073, "point2": 0.255},
            2.2: {"point1": 0.073, "point2": 0.249},
            2.3: {"point1": 0.073, "point2": 0.242},
            2.4: {"point1": 0.073, "point2": 0.236},
            2.5: {"point1": 0.072, "point2": 0.230},
            2.6: {"point1": 0.072, "point2": 0.225},
            2.7: {"point1": 0.071, "point2": 0.219},
            2.8: {"point1": 0.071, "point2": 0.214},
            2.9: {"point1": 0.070, "point2": 0.209},
            3.0: {"point1": 0.070, "point2": 0.204},
            3.1: {"point1": 0.069, "point2": 0.200},
            3.2: {"point1": 0.069, "point2": 0.196},
            3.3: {"point1": 0.068, "point2": 0.192},
            3.4: {"point1": 0.067, "point2": 0.188},
            3.5: {"point1": 0.067, "point2": 0.184},
            3.6: {"point1": 0.066, "point2": 0.180},
            3.7: {"point1": 0.065, "point2": 0.177},
            3.8: {"point1": 0.065, "point2": 0.173},
            3.9: {"point1": 0.064, "point2": 0.170},
            4.0: {"point1": 0.063, "point2": 0.167},
            4.2: {"point1": 0.062, "point2": 0.161},
            4.4: {"point1": 0.061, "point2": 0.155},
            4.6: {"point1": 0.059, "point2": 0.150},
            4.8: {"point1": 0.058, "point2": 0.145},
            5.0: {"point1": 0.057, "point2": 0.140}
        }
        
        # 如果超出表格范围，使用边界值
        if z_over_r <= 0.0:
            return table_d04_data[0.0][point_type]
        elif z_over_r >= 5.0:
            return table_d04_data[5.0][point_type]
        
        # 为插值创建对应点的数据表
        point_table = {k: v[point_type] for k, v in table_d04_data.items()}
        
        # 根据点类型选择不同的插值方法
        if point_type == "point1":
            # 点1使用正比插值（常规线性插值）
            return self._linear_interpolate(z_over_r, point_table)
        else:
            # 点2使用反比插值
            return self._inverse_interpolate(z_over_r, point_table)
    
    def _inverse_interpolate(self, x: float, table: dict) -> float:
        """反比插值函数
        
        Args:
            x: 待插值的x值
            table: 插值表格，格式为 {x: y}
            
        Returns:
            float: 插值结果
        """
        # 获取排序后的x值列表
        x_values = sorted(table.keys())
        
        # 找到x值所在的区间
        for i in range(len(x_values) - 1):
            x1, x2 = x_values[i], x_values[i + 1]
            if x1 <= x <= x2:
                y1, y2 = table[x1], table[x2]
                # 反比插值：权重与距离成反比
                # 计算权重
                if x2 - x1 != 0:
                    w1 = (x2 - x) / (x2 - x1)  # 距离x1越近，权重越大
                    w2 = (x - x1) / (x2 - x1)  # 距离x2越近，权重越大
                    # 反比插值公式
                    return w1 * y1 + w2 * y2
                else:
                    return y1
        
        # 如果没找到合适的区间，返回最接近的值
        return table[min(x_values, key=lambda k: abs(k - x))]
    
    def _linear_interpolate(self, x: float, table: dict) -> float:
        """线性插值函数
        
        Args:
            x: 待插值的x值
            table: 插值表格，格式为 {x: y}
            
        Returns:
            float: 插值结果
        """
        # 获取排序后的x值列表
        x_values = sorted(table.keys())
        
        # 找到x值所在的区间
        for i in range(len(x_values) - 1):
            x1, x2 = x_values[i], x_values[i + 1]
            if x1 <= x <= x2:
                y1, y2 = table[x1], table[x2]
                # 线性插值公式: y = y1 + (x - x1) * (y2 - y1) / (x2 - x1)
                return y1 + (x - x1) * (y2 - y1) / (x2 - x1)
        
        # 如果没找到合适的区间，返回最接近的值
        return table[min(x_values, key=lambda k: abs(k - x))]
    
    def _get_compression_modulus_at_depth(self, absolute_depth: float) -> float:
        """根据绝对深度从土层列表中获取对应土层的压缩模量
        
        Args:
            absolute_depth: 距离地面的绝对深度(m)
            
        Returns:
            float: 压缩模量(MPa)
        """
        if not self.soil_layers:
            logger.warning("土层信息列表为空，使用默认压缩模量12.5MPa")
            return 12.5
        
        # 遍历土层列表，找到包含该深度的土层
        for layer in self.soil_layers:
            # 获取土层参数
            layer_elevation = layer.get('elevation', 0)  # 土层顶部标高（通常为负值）
            layer_thickness = layer.get('thickness', 0)  # 土层厚度
            layer_name = layer.get('layerName') or layer.get('layer_name', '未知土层')
            compression_modulus = layer.get('compression_modulus', 12.5)  # 压缩模量
            
            # 计算土层的深度范围
            # 土层顶部深度 = |土层标高|
            layer_top_depth = abs(layer_elevation)
            # 土层底部深度 = 土层顶部深度 + 土层厚度
            layer_bottom_depth = layer_top_depth + layer_thickness
            
            # 判断绝对深度是否在该土层范围内
            # 当 层顶深度 <= 绝对深度 <= 层底深度时，该点在此土层内
            if layer_top_depth <= absolute_depth <= layer_bottom_depth:
                logger.debug(f"深度{absolute_depth:.1f}m位于土层'{layer_name}': "
                           f"标高{layer_elevation}m, 厚度{layer_thickness}m, "
                           f"深度范围{layer_top_depth:.1f}m-{layer_bottom_depth:.1f}m, "
                           f"压缩模量{compression_modulus}MPa")
                return compression_modulus
        
        # 如果没找到匹配的土层，选择最接近的土层
        logger.warning(f"深度{absolute_depth:.1f}m未找到匹配的土层，选择最接近的土层")
        
        min_distance = float('inf')
        closest_layer = None
        
        for layer in self.soil_layers:
            layer_elevation = layer.get('elevation', 0)
            layer_thickness = layer.get('thickness', 0)
            layer_name = layer.get('layerName') or layer.get('layer_name', '未知土层')
            
            layer_top_depth = abs(layer_elevation)
            layer_bottom_depth = layer_top_depth + layer_thickness
            
            # 计算距离
            if absolute_depth < layer_top_depth:
                # 深度在土层之上
                distance = layer_top_depth - absolute_depth
            elif absolute_depth > layer_bottom_depth:
                # 深度在土层之下
                distance = absolute_depth - layer_bottom_depth
            else:
                # 深度在土层内（理论上不应该到这里）
                distance = 0
            
            if distance < min_distance:
                min_distance = distance
                closest_layer = layer
        
        if closest_layer:
            compression_modulus = closest_layer.get('compression_modulus', 12.5)
            layer_name = closest_layer.get('layerName') or closest_layer.get('layer_name', '未知土层')
            logger.info(f"选择最接近的土层'{layer_name}', 压缩模量: {compression_modulus}MPa")
            return compression_modulus
        
        # 如果仍然没有找到，返回默认值
        logger.warning("无法确定合适的土层，使用默认压缩模量12.5MPa")
        return 12.5
    

    
    def get_comprehensive_settlement_result(self) -> Dict[str, Any]:
        """获取综合接口需要的沉降验算结果格式
        
        返回简化的沉降验算结果，只包含关键信息
        
        Returns:
            Dict[str, Any]: 简化的沉降验算结果
        """
        # 1. 计算沉降的分层厚度
        layer_thickness = 1.0  # 分层厚度固定为1.0m
        
        # 2. 地基沉降计算深度范围内所划分的土层数
        layer_count = len(self.settlement_details)
        
        # 3. 基础底面平均附加压力：P_0k
        p0k = self.additional_stress
        
        # 4. 基底承载力特征值：f_ak
        fak = self.foundation_fak
        
        # 5. 沉降计算深度范围内压缩模量的当量值Es计算过程列表
        from app.schemas.settlement import EsCalculationLayerInfo
        es_calculation_list = list[EsCalculationLayerInfo]()
        for detail in self.settlement_details:
            layer_info = EsCalculationLayerInfo(
                zi_m=detail.zi,  # Zi (m)
                esi_mpa=detail.esi,  # Esi (MPa) 
                alpha_i=detail.alpha_i,  # ᾱi
                es_mpa=detail.current_es,  # Es (MPa)
                delta_s_mm=detail.delta_s,  # ΔSi (mm)
                si_mm=detail.cumulative_s  # Si (mm)
            )
            es_calculation_list.append(layer_info)
        
        # 6. 沉降计算深度验算
        if self.settlement_details:
            last_layer = self.settlement_details[-1]
            delta_s_last = last_layer.delta_s  # 最后一层的沉降量
            total_settlement = last_layer.cumulative_s  # 累积沉降
            ratio = abs(delta_s_last) / total_settlement if total_settlement > 0 else 0
            depth_check_formula = f"Δs_i^'={delta_s_last:.5f}mm≤0.025s^'=0.025×{total_settlement:.5f}={0.025*total_settlement:.5f}mm"
            depth_check_result = "满足" if ratio <= 0.025 else "不满足"
            depth_verification = f"{depth_check_formula}，{depth_check_result}《陆上风电场工程风电机组基础设计规范》6.4.3条规定。"
        else:
            depth_verification = "沉降计算深度验算：无计算数据"
        
        # 7. 沉降计算经验系数
        psi_s_description = f"查规范表6.4.2得ψ_s={self.psi_value:.5f}"
        
        # 8. 基础最大沉降量
        settlement_before_psi = total_settlement if self.settlement_details else 0
        max_settlement_formula = f"s=ψ_s×s^'={self.psi_value:.5f}×{settlement_before_psi:.5f}={self.final_settlement:.3f}mm"
        
        # 9. 允许沉降量
        allowable_settlement = f"{self.allowable_settlement:.0f}mm"
        
        # 10. 验算结果
        settlement_check_result = "满足" if self.final_settlement <= self.allowable_settlement else "不满足"
        verification_result = f"基础最大沉降量（{self.final_settlement:.3f}mm）{'小于' if self.final_settlement <= self.allowable_settlement else '大于'}允许沉降量（{self.allowable_settlement:.0f}mm），{settlement_check_result}《陆上风电场工程风电机组基础设计规范》6.4.1条规定。"
        
        return {
            "layer_thickness": layer_thickness,
            "layer_count": layer_count,
            "p0k": p0k,
            "fak": fak,
            "es_calculation_list": es_calculation_list,
            "depth_verification": depth_verification,
            "psi_s_description": psi_s_description,
            "max_settlement_formula": max_settlement_formula,
            "allowable_settlement": allowable_settlement,
            "verification_result": verification_result
        }
    
    def get_comprehensive_inclination_result(self) -> Dict[str, Any]:
        """获取综合接口需要的倾斜验算结果格式
        
        返回简化的倾斜验算结果，结构类似沉降验算
        
        Returns:
            Dict[str, Any]: 简化的倾斜验算结果
        """
        # 1. 计算基础
        layer_thickness = 1.0  # 分层厚度固定为1.0m
        layer_count = len(self.settlement_details)
        
        # 2. 压力值
        p0kmax = self.pkmax - (self.ps_value or 0)
        p0kmin = self.pkmin - (self.ps_value or 0)
        
        # 3. 基底承载力特征值
        fak = self.foundation_fak
        
        # 4. 倾斜计算过程（可以复用Es计算列表的结构）
        from app.schemas.settlement import EsCalculationLayerInfo
        inclination_calculation_list = list[EsCalculationLayerInfo]()
        for detail in self.settlement_details:
            layer_info = EsCalculationLayerInfo(
                zi_m=detail.zi,
                esi_mpa=detail.esi,
                alpha_i=detail.alpha_i,
                es_mpa=detail.current_es,
                delta_s_mm=detail.delta_s,
                si_mm=detail.cumulative_s
            )
            inclination_calculation_list.append(layer_info)
        
        # 5. 倾斜计算公式
        base_diameter = 2 * self.geometry.base_radius
        inclination_formula = f"倾斜率=|s2-s1|/基础直径={self.inclination:.6f}/{base_diameter:.1f}m={self.inclination:.6f}"
        
        # 6. 允许倾斜值
        allowable_inclination = f"{self.allowable_inclination:.6f}"
        
        # 7. 验算结果
        inclination_check_result = "满足" if self.inclination <= self.allowable_inclination else "不满足"
        verification_result = f"计算倾斜率（{self.inclination:.6f}）{'小于' if self.inclination <= self.allowable_inclination else '大于'}允许倾斜率（{self.allowable_inclination:.6f}），{inclination_check_result}《陆上风电场工程风电机组基础设计规范》6.4.2条规定。"
        
        return {
            "layer_thickness": layer_thickness,
            "layer_count": layer_count,
            "p0kmax": p0kmax,
            "p0kmin": p0kmin,
            "fak": fak,
            "inclination_calculation_list": inclination_calculation_list,
            "inclination_formula": inclination_formula,
            "allowable_inclination": allowable_inclination,
            "verification_result": verification_result
        }