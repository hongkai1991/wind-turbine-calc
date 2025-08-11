import math
from typing import Optional, List, Dict, Any
from app.schemas import (
    FoundationGeometry, 
    MaterialProperties, 
    SelfWeightResult,
    SoilLayer
)
from app.utils.logger import get_logger

logger = get_logger(__name__)


class SelfWeightCalculator:
    """自重计算类 - 计算基础自重、回填土重量和浮力"""
    
    def __init__(
        self, 
        geometry: FoundationGeometry,
        material: MaterialProperties,
        cover_soil_density: float = 18.0,
        groundwater_depth: Optional[float] = None,
        soil_layers: Optional[List[Dict[str, Any]]] = None
    ):
        """
        初始化自重计算器
        
        Args:
            geometry: 基础几何信息
            material: 材料属性
            cover_soil_density: 覆土容重(kN/m³)
            groundwater_depth: 地下水埋深(m)，None表示无地下水
            soil_layers: 土层信息列表，用于浮力计算中的重度计算
        """
        self.geometry = geometry
        self.material = material
        self.cover_soil_density = cover_soil_density
        self.groundwater_depth = groundwater_depth
        self.soil_layers = soil_layers or []
        
        # 计算结果缓存
        self._concrete_weight: Optional[float] = None #混凝土（基础）自重 G1(kN)
        self._backfill_weight: Optional[float] = None #回填土自重 G2(kN)
        self._buoyancy_weight: Optional[float] = None #浮力 Gw(kN)
        self._total_weight: Optional[float] = None #总重量 Gk(kN)=基础自重+回填土自重-浮力
        self._foundation_volume: Optional[float] = None #混凝土体积 V1(m³)  
        self._backfill_volume: Optional[float] = None #回填土体积 V2(m³)

        self.base_foundation_volume: Optional[float] = None #基础直径的圆柱体积(m³)
        self.waf_foundation_volume: Optional[float] = None #挖方-圆柱体积(m³)
        self.cover_soil_volume: Optional[float] = None #覆土体积=回填土体积-(挖方-圆柱体积)(m³) 

    # 计算单个基础体积
    def calculate_foundation_volume(self) -> float:
        """计算基础混凝土体积"""
        r1 = self.geometry.base_radius    # 基础底板半径
        r2 = self.geometry.column_radius  # 台柱半径
        h1 = self.geometry.edge_height    # 基础边缘高度
        h2 = self.geometry.frustum_height # 基础底板棱台高度
        h3 = self.geometry.column_height  # 台柱高度
        h4 = self.material.cushion_thickness / 1000  # 垫层厚度，从mm转换为m
        base_depth = self.geometry.buried_depth # 基础埋深

        # 基础边缘体积=π*基础底板半径²*基础边缘高度
        frustum_volume=math.pi*r1**2*h1
        # 基础棱台体积=1/3*π*基础底板棱台高度*(基础底板半径²+基础底板半径*台柱半径+台柱半径²)
        prismatic_volume=1/3*math.pi*h2*(r1**2+r1*r2+r2**2)

        # 台柱底面积=π*台柱半径²
        column_area=math.pi*r2**2
        # 台柱体积=台柱底面积*(基础埋深-基础边缘高度-基础底板棱台高度)*(台柱高度-(基础埋深-基础边缘高度-基础底板棱台高度))
        column_volume=column_area*(h3-self.geometry.ground_height)
        #垫层体积=π*(基础底板半径+0.1)²*垫层厚度
        cushion_volume=math.pi*(r1+0.1)**2*h4
        #基础混凝土体积=基础底板体积+底板棱台体积+台柱体积+垫层体积
        total_volume=frustum_volume+prismatic_volume+column_volume+cushion_volume
        return max(0.0, total_volume)
    
    # 计算单个基础挖方体积
    def calculate_single_waf_foundation_volume(self):
        """计算单个基础挖方体积"""
        # 单个基础挖方体积=1/3π*（垫层厚度+基础埋深）*{（基础底板半径+0.5）^2+[基础底板半径+0.5+1*(垫层厚度+基础埋深)]^2+（基础底板半径+0.5）*[基础底板半径+0.5+1*(垫层厚度+基础埋深)]}
        cushion_thickness_m = self.material.cushion_thickness / 1000  # 从mm转换为m
        self.single_waf_foundation_volume = (1/3)*math.pi * (cushion_thickness_m + self.geometry.buried_depth) * (
            (self.geometry.base_radius + 0.5)**2 + 
            (self.geometry.base_radius + 0.5 + 1 * (cushion_thickness_m + self.geometry.buried_depth))**2 + 
            (self.geometry.base_radius + 0.5) * (self.geometry.base_radius + 0.5 + 1 * (cushion_thickness_m + self.geometry.buried_depth))
        )
        return self.single_waf_foundation_volume
    
    # 计算单个基础回填体积
    def calculate_single_backfill_volume(self):
        """计算单个基础回填体积"""
        # 单个基础回填体积=1/3π*（垫层厚度+基础埋深）*{（基础底板半径+0.5）^2+[基础底板半径+0.5+1*(垫层厚度+基础埋深)]^2+（基础底板半径+0.5）*[基础底板半径+0.5+1*(垫层厚度+基础埋深)]}
        self.single_backfill_volume = self.calculate_single_waf_foundation_volume()-self.calculate_foundation_volume()
        return self.single_backfill_volume

    def calculate_base_foundation_volume(self):
        """计算基础直径的圆柱体积"""
        # 基础直径的圆柱体积=πR²*(垫层厚度+基础埋深)
        cushion_thickness_m = self.material.cushion_thickness / 1000  # 从mm转换为m
        self.base_foundation_volume = math.pi * self.geometry.base_radius**2 * (cushion_thickness_m + self.geometry.buried_depth)
        return self.base_foundation_volume


    def calculate_waf_foundation_volume(self):
        """计算挖方-圆柱体积"""
        # 挖方-圆柱体积=1/3π*（垫层厚度+基础埋深）*{（基础底板半径+1）^2+[基础底板半径+1+0.5*(垫层厚度+基础埋深)]^2+（基础底板半径+1）*[基础底板半径+1+0.5*(垫层厚度+基础埋深)]}-基础直径的圆柱体积
        self.waf_foundation_volume = self.calculate_single_waf_foundation_volume() - self.calculate_base_foundation_volume()
        return self.waf_foundation_volume

    def calculate_cover_soil_volume(self):
        """计算覆土体积"""
        # 覆土体积=单个基础回填体积-(挖方-圆柱体积)
        self.cover_soil_volume = self.calculate_single_backfill_volume() - self.calculate_waf_foundation_volume()
        self._backfill_volume=self.cover_soil_volume
        return self.cover_soil_volume

    def calculate_concrete_weight(self) -> float:
        """
        计算基础自重
        
        Returns:
            float: 基础自重G1(kN)
        """
        if self._concrete_weight is not None: return self._concrete_weight
        try:
            logger.info("开始计算基础自重")
            if self._foundation_volume is None: self._foundation_volume = self.calculate_foundation_volume()
            # 基础自重 = 混凝土体积 × 混凝土容重
            concrete_weight = self._foundation_volume * self.material.density
            self._concrete_weight = concrete_weight
            logger.info(f"基础自重计算完成: {concrete_weight:.2f}kN (体积: {self._foundation_volume:.2f}m³)")
            return concrete_weight
        except Exception as e:
            logger.error(f"混凝土自重计算失败: {str(e)}")
            raise

    def calculate_backfill_weight(self) -> float:
        """
        计算回填土自重
        
        Returns:
            float: 回填土自重G2(kN)
        """
        if self._backfill_weight is not None:
            return self._backfill_weight
        
        try:
            logger.info("开始计算回填土自重")
            # 计算回填土体积
            if self._backfill_volume is None: self._backfill_volume = self._calculate_backfill_volume()
            # 回填土自重 = 回填土体积 * 覆土容重
            self._backfill_weight = self._backfill_volume * self.cover_soil_density
            logger.info(f"回填土自重计算完成: {self._backfill_weight:.2f}kN (体积: {self._backfill_volume:.2f}m³)")
            return self._backfill_weight
        except Exception as e:
            logger.error(f"回填土自重计算失败: {str(e)}")
            raise

    def _get_affected_soil_layers_and_average_density(self) -> float:
        """
        根据基础埋深和地下水深度，确定受影响的土层并计算平均重度
        
        Returns:
            float: 计算浮力用的平均重度(kN/m³)，即所跨土层重度减10后的平均值
        """
        if not self.soil_layers or self.groundwater_depth is None:
            logger.warning("缺少土层信息或地下水深度，使用默认重度10.0 kN/m³")
            return 10.0  # 默认水的重度
        
        # 地下水以下的基础埋深范围
        submerged_start_depth = self.groundwater_depth  # 地下水位深度
        submerged_end_depth = self.geometry.buried_depth  # 基础底部深度
        
        if submerged_end_depth <= submerged_start_depth:
            logger.info("基础未进入地下水位以下，无需计算浮力")
            return 0.0
        
        logger.info(f"计算浮力：地下水位深度={submerged_start_depth}m，基础埋深={submerged_end_depth}m")
        
        # 收集被浸没部分跨越的土层
        affected_layers = []
        total_thickness = 0.0
        
        # 按标高从高到低排序土层（假设elevation是负值，表示距离地面的深度）
        sorted_layers = sorted(self.soil_layers, key=lambda x: abs(x.get('elevation', 0)))
        
        for layer in sorted_layers:
            layer_elevation = abs(layer.get('elevation', 0))  # 土层顶部深度
            layer_thickness = layer.get('thickness', 0)  # 土层厚度
            layer_bottom_depth = layer_elevation + layer_thickness  # 土层底部深度
            layer_density = layer.get('density', 18.0)  # 土层重度
            layer_name = layer.get('layerName') or layer.get('layer_name', '未知土层')
            
            # 判断土层是否与地下水以下的基础部分有重叠
            if layer_elevation < submerged_end_depth and layer_bottom_depth > submerged_start_depth:
                # 计算重叠部分的厚度
                overlap_start = max(layer_elevation, submerged_start_depth)
                overlap_end = min(layer_bottom_depth, submerged_end_depth)
                overlap_thickness = overlap_end - overlap_start
                
                if overlap_thickness > 0:
                    affected_layers.append({
                        'name': layer_name,
                        'density': layer_density,
                        'thickness': overlap_thickness,
                        'depth_range': (overlap_start, overlap_end)
                    })
                    total_thickness += overlap_thickness
                    
                    logger.debug(f"土层 '{layer_name}' 被浸没部分: {overlap_start}m - {overlap_end}m (厚度: {overlap_thickness}m, 重度: {layer_density}kN/m³)")
        
        if not affected_layers:
            logger.warning("未找到受影响的土层，使用默认重度10.0 kN/m³")
            return 10.0
        
        # 计算加权平均重度（减去10）
        weighted_density_sum = 0.0
        for layer in affected_layers:
            # 重度减去10（水的重度），然后按厚度加权
            effective_density = max(0, layer['density'] - 10)  # 确保不为负值
            weighted_density_sum += effective_density * layer['thickness']
            logger.debug(f"土层 '{layer['name']}': 有效重度 = {layer['density']} - 10 = {effective_density}kN/m³")
        
        average_effective_density = weighted_density_sum / total_thickness if total_thickness > 0 else 0.0
        
        logger.info(f"浮力计算：受影响土层数量={len(affected_layers)}，总厚度={total_thickness:.2f}m，平均有效重度={average_effective_density:.2f}kN/m³")
        
        return average_effective_density

    def calculate_buoyancy(self) -> float:
        """
        计算浮力
        基于新的逻辑：根据基础埋深和土层标高判断基础跨越的土层，
        计算地下水以下基础体积(圆柱体π*R²*h)乘以平均有效重度
        
        Returns:
            float: 浮力Gw(kN)
        """
        if self._buoyancy_weight is not None:
            return self._buoyancy_weight
        
        logger.info("开始计算浮力（新逻辑）")
        
        try:
            buoyancy_weight = 0.0
            
            # 检查是否有地下水
            if self.groundwater_depth is None:
                logger.info("无地下水信息，浮力为0")
                self._buoyancy_weight = 0.0
                return 0.0
            
            # 计算地下水位以下的基础深度
            submerged_depth = max(0, self.geometry.buried_depth - self.groundwater_depth)
            
            if submerged_depth <= 0:
                logger.info("基础未进入地下水位以下，浮力为0")
                self._buoyancy_weight = 0.0
                return 0.0
            
            # 计算地下水以下的基础体积（按圆柱体计算）
            # 使用基础底板半径作为圆柱体半径，不论地下水在哪个深度
            submerged_volume = math.pi * self.geometry.base_radius**2 * submerged_depth
            
            logger.info(f"地下水以下基础体积（圆柱体）: π × {self.geometry.base_radius}² × {submerged_depth} = {submerged_volume:.3f}m³")
            
            # 获取所跨土层的平均有效重度
            average_effective_density = self._get_affected_soil_layers_and_average_density()
            
            # 计算浮力 = 地下水以下基础体积 × 平均有效重度
            buoyancy_weight = submerged_volume * average_effective_density
            
            self._buoyancy_weight = buoyancy_weight
            
            logger.info(f"浮力计算完成: {submerged_volume:.3f}m³ × {average_effective_density:.2f}kN/m³ = {buoyancy_weight:.2f}kN")
            return buoyancy_weight
            
        except Exception as e:
            logger.error(f"浮力计算失败: {str(e)}")
            raise

    def calculate_total_weight(self) -> float:
        """
        计算总重量
        
        Returns:
            float: 总重量Gk(kN)
        """
        if self._total_weight is not None: return self._total_weight
        try:
            logger.info("开始计算总重量")
            concrete_weight = self.calculate_concrete_weight()
            backfill_weight = self.calculate_backfill_weight()
            buoyancy_weight = self.calculate_buoyancy()
            # 总重量 = 混凝土自重 + 回填土重量 - 浮力
            total_weight = concrete_weight + backfill_weight - buoyancy_weight
            self._total_weight = total_weight
            logger.info(f"总重量计算完成: {total_weight:.2f}kN")
            return total_weight
        except Exception as e:
            logger.error(f"总重量计算失败: {str(e)}")
            raise

    def get_calculation_result(self) -> SelfWeightResult:
        """
        获取完整的自重计算结果
        
        Returns:
            SelfWeightResult: 自重计算结果（包含所有9个计算结果）
        """
        logger.info("生成自重计算结果")
        
        # 计算基本的6个结果
        concrete_weight = self.calculate_concrete_weight()
        backfill_weight = self.calculate_backfill_weight()
        buoyancy_weight = self.calculate_buoyancy()
        total_weight = self.calculate_total_weight()
        
        # 计算额外的3个体积结果
        base_foundation_volume = self.calculate_base_foundation_volume()
        waf_foundation_volume = self.calculate_waf_foundation_volume()
        cover_soil_volume = self.calculate_cover_soil_volume()
        
        return SelfWeightResult(
            foundation_volume=self._foundation_volume,
            backfill_volume=self._backfill_volume,
            concrete_weight=concrete_weight,
            backfill_weight=backfill_weight,
            buoyancy_weight=buoyancy_weight,
            total_weight=total_weight
        )

    def _calculate_backfill_volume(self) -> float:
        """计算回填土体积"""
        backfill_volume = self.calculate_cover_soil_volume()
        return max(0.0, backfill_volume)

    def _calculate_submerged_volume(self, submerged_depth: float) -> float:
        """计算淹没体积"""
        if submerged_depth <= 0:
            return 0.0
        
        # 简化计算：按平均半径的圆柱体计算
        avg_radius = (self.geometry.base_radius + self.geometry.column_radius) / 2
        submerged_volume = math.pi * avg_radius**2 * submerged_depth
        
        return submerged_volume

    def validate_input_parameters(self) -> tuple[bool, str]:
        """
        验证输入参数
        
        Returns:
            tuple[bool, str]: (是否有效, 错误信息)
        """
        # 验证几何参数
        if not self.geometry.validate_geometry():
            return False, "基础几何参数不合理"
        
        if not self.geometry.check_slope_compliance():
            return False, "基础边坡坡度不符合要求"
        
        # 验证材料参数
        if not self.material.validate_parameters():
            return False, "材料参数不合理"
        
        # 验证其他参数
        if self.cover_soil_density <= 0:
            return False, "覆土容重必须大于0"
        
        if self.groundwater_depth is not None and self.groundwater_depth < 0:
            return False, "地下水埋深不能为负值"
        
        return True, "参数验证通过" 