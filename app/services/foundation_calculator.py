"""
风电基础主计算控制器模块
"""
from typing import Dict, List, Optional, Any
import logging

from app.services.load_calculation import LoadCalculator
from app.services.self_weight_calculator import SelfWeightCalculator


# 导入其他需要的计算器类（未实现的类先注释掉）
# from app.services.detachment_analyzer import DetachmentAnalyzer
# from app.services.bearing_capacity_analyzer import BearingCapacityAnalyzer
# from app.services.overturn_analyzer import OverturnAnalyzer
# from app.services.sliding_analyzer import SlidingAnalyzer
# from app.services.stiffness_analyzer import StiffnessAnalyzer
# from app.services.shear_strength_analyzer import ShearStrengthAnalyzer

logger = logging.getLogger(__name__)


class FoundationCalculator:
    """主计算控制器
    
    集成各种计算器，执行完整的风机基础计算流程
    
    属性:
        load_calculator: 荷载计算器
        settlement_analyzer: 地基变形计算器
        以及其他各种计算器
    """
    
    def __init__(self, foundation_geometry: Dict[str, float], soil_layers: List[Dict], material_properties: Dict[str, Any]):
        """初始化主计算控制器
        
        Args:
            foundation_geometry: 基础几何信息，包含:
                - base_radius: 基础底板半径(m)
                - column_radius: 台柱半径(m)
                - edge_height: 基础边缘高度(m)
                - frustum_height: 棱台高度(m)
                - column_height: 台柱高度(m)
                - buried_depth: 基础埋深(m)
            soil_layers: 土层信息列表
            material_properties: 材料属性
        """
        self.foundation_geometry = foundation_geometry
        self.soil_layers = soil_layers
        self.material_properties = material_properties
        
        # 初始化各种计算器
        self.load_calculator = None
        self.self_weight_calculator = None
        self.settlement_analyzer = None
        
        # 其他计算器暂时为None
        self.detachment_analyzer = None
        self.bearing_capacity_analyzer = None
        self.overturn_analyzer = None
        self.sliding_analyzer = None
        self.stiffness_analyzer = None
        self.shear_strength_analyzer = None

        
        # 计算结果
        self.calculation_results = {}
    
    def initialize_calculators(self):
        """初始化所有计算器"""
        # 初始化自重计算器
        self._initialize_self_weight_calculator()
        
        # 初始化荷载计算器
        self._initialize_load_calculator()
        
        # 初始化地基变形计算器
        self._initialize_settlement_analyzer()
        

        
        # 其他计算器的初始化（后续实现）
        # self._initialize_detachment_analyzer()
        # self._initialize_bearing_capacity_analyzer()
        # self._initialize_overturn_analyzer()
        # self._initialize_sliding_analyzer()
        # self._initialize_stiffness_analyzer()
        # self._initialize_shear_strength_analyzer()
        
        logger.info("所有计算器初始化完成")
    
    def _initialize_self_weight_calculator(self):
        """初始化自重计算器"""
        try:
            # 这里需要适配SelfWeightCalculator的参数要求
            # 暂时留空，等SelfWeightCalculator实现后再完善
            logger.info("初始化自重计算器")
            # self.self_weight_calculator = SelfWeightCalculator(...)
        except Exception as e:
            logger.error(f"初始化自重计算器失败: {str(e)}")
            raise
    
    def _initialize_load_calculator(self):
        """初始化荷载计算器"""
        try:
            # 这里需要适配LoadCalculator的参数要求
            # 暂时留空，等LoadCalculator实现后再完善
            logger.info("初始化荷载计算器")
            # self.load_calculator = LoadCalculator(...)
        except Exception as e:
            logger.error(f"初始化荷载计算器失败: {str(e)}")
            raise
    
    def execute_all_calculations(self):
        """执行全部计算"""
        logger.info("开始执行全部计算")
        
        # 确保所有计算器已初始化
        if not self.settlement_analyzer:
            self.initialize_calculators()
        
        # 执行地基变形计算
        self._execute_settlement_calculation()
        

        
        # 其他计算（后续实现）
        # self._execute_detachment_calculation()
        # self._execute_bearing_capacity_calculation()
        # self._execute_overturn_calculation()
        # self._execute_sliding_calculation()
        # self._execute_stiffness_calculation()
        # self._execute_shear_strength_calculation()
        
        logger.info("全部计算执行完成")
        return self.calculation_results
    
    def _execute_settlement_calculation(self):
        """执行地基变形计算"""
        try:
            logger.info("执行地基变形计算")
            
            # 计算沉降
            settlement = self.settlement_analyzer.calculate_settlement()
            
            # 计算倾斜
            inclination = self.settlement_analyzer.calculate_inclination()
            
            # 检查结果
            check_results = self.settlement_analyzer.check_results()
            
            # 获取详细报告
            settlement_report = self.settlement_analyzer.get_settlement_report()
            
            # 保存计算结果
            self.calculation_results["settlement"] = {
                "settlement": settlement,
                "inclination": inclination,
                "check_results": check_results,
                "report": settlement_report
            }
            
            logger.info(f"地基变形计算完成: 沉降={settlement:.2f}mm, 倾斜率={inclination:.6f}")
        except Exception as e:
            logger.error(f"地基变形计算失败: {str(e)}")
            self.calculation_results["settlement"] = {"error": str(e)}
    

    
    def calculate_for_load_case(self, load_case: str):
        """按工况计算
        
        Args:
            load_case: 工况名称
        """
        logger.info(f"开始按工况计算: {load_case}")
        
        # 这里应该根据工况选择相应的荷载条件进行计算
        # 暂时简化处理，调用全部计算
        self.execute_all_calculations()
        
        logger.info(f"工况计算完成: {load_case}")
        return self.calculation_results
    
    def generate_results(self) -> List[Dict]:
        """组织结果数据
        
        Returns:
            List[Dict]: 验算结果列表
        """
        logger.info("生成计算结果报告")
        
        results = []
        
        # 添加地基变形计算结果
        if "settlement" in self.calculation_results:
            settlement_data = self.calculation_results["settlement"]
            if "error" not in settlement_data:
                results.append({
                    "check_type": "地基变形验算",
                    "load_case": "正常工况",  # 假设工况
                    "calculated_value": settlement_data["settlement"],
                    "allowable_value": settlement_data["report"]["allowable_settlement"],
                    "unit": "mm",
                    "is_valid": settlement_data["check_results"]["settlement"],
                    "description": "地基沉降验算"
                })
                
                results.append({
                    "check_type": "地基倾斜验算",
                    "load_case": "正常工况",  # 假设工况
                    "calculated_value": settlement_data["inclination"],
                    "allowable_value": settlement_data["report"]["allowable_inclination"],
                    "unit": "",
                    "is_valid": settlement_data["check_results"]["inclination"],
                    "description": "地基倾斜验算"
                })
        

        
        # 其他验算结果（后续添加）
        
        logger.info(f"生成计算结果报告完成，共{len(results)}项验算结果")
        return results 