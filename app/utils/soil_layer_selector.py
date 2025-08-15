"""
土层选择工具模块
根据基础埋深和土层标高选择合适的土层
"""
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


def select_soil_layer_by_depth(buried_depth: float, soil_layers: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    根据基础埋深选择合适的土层
    
    Args:
        buried_depth: 基础埋深(m)，正数
        soil_layers: 土层信息列表，每个土层包含elevation字段（土层顶部标高，负数）
        
    Returns:
        Dict[str, Any]: 选中的土层信息
        
    Raises:
        ValueError: 当没有找到合适的土层时
        
    Notes:
        - 基础埋深为正数，表示从地面向下的深度
        - 土层标高通常为负数，表示该土层顶部的标高位置
        - 选择逻辑：基础埋深 - |土层标高| = 在该土层中的深度，如果这个深度 ≤ 土层厚度，说明基础在该土层范围内
        - 使用绝对值防止用户错误传入正数标高，确保计算的鲁棒性
    """
    if not soil_layers:
        raise ValueError("土层信息列表不能为空")
    
    if buried_depth < 0:
        raise ValueError("基础埋深必须为非负数")
    
    logger.info(f"基础埋深: {buried_depth}m")
    
    # 遍历所有土层，找到合适的土层
    for layer in soil_layers:
        layer_elevation = layer.get('elevation', 0)  # 土层顶部标高（应为负数）
        layer_thickness = layer.get('thickness', 0)  # 土层厚度
        # 尝试获取土层名称，支持两种命名格式
        layer_name = layer.get('layer_name') or layer.get('layerName', '未知土层')
        
        # 计算基础在该土层中的深度
        # 使用绝对值确保计算正确，防止有人传入正数标高
        depth_in_layer = buried_depth - abs(layer_elevation)
        
        logger.debug(f"检查土层 '{layer_name}': 标高={layer_elevation}m, 厚度={layer_thickness}m, 基础在该层中深度={depth_in_layer}m")
        
        # 如果基础在该土层中的深度为正数且不超过土层厚度，说明基础在这个土层内
        if 0 <= depth_in_layer <= layer_thickness:
            logger.info(f"选择土层: '{layer_name}' (标高: {layer_elevation}m, 厚度: {layer_thickness}m, 基础在该层深度: {depth_in_layer}m)")
            return layer
    
    # 如果没有找到合适的土层，选择最接近的土层
    logger.warning(f"未找到基础埋深 {buried_depth}m 对应的土层，选择最接近的土层")
    
    # 计算与每个土层的距离，选择最近的
    min_distance = float('inf')
    closest_layer = None
    
    for layer in soil_layers:
        layer_elevation = layer.get('elevation', 0)
        layer_thickness = layer.get('thickness', 0)
        # 尝试获取土层名称，支持两种命名格式
        layer_name = layer.get('layer_name') or layer.get('layerName', '未知土层')
        
        # 使用绝对值确保计算正确
        depth_in_layer = buried_depth - abs(layer_elevation)
        
        # 计算距离
        if depth_in_layer < 0:
            # 基础在土层之上
            distance = abs(depth_in_layer)
        elif depth_in_layer > layer_thickness:
            # 基础在土层之下
            distance = depth_in_layer - layer_thickness
        else:
            # 基础在土层内（理论上不应该到这里）
            distance = 0
        
        if distance < min_distance:
            min_distance = distance
            closest_layer = layer
    
    if closest_layer:
        # 尝试获取土层名称，支持两种命名格式
        layer_name = closest_layer.get('layer_name') or closest_layer.get('layerName', '未知土层')
        logger.info(f"选择最接近的土层: '{layer_name}' (距离: {min_distance}m)")
        return closest_layer
    
    # 如果仍然没有找到，返回第一个土层作为默认值
    logger.warning("无法确定合适的土层，使用第一个土层作为默认值")
    return soil_layers[0]


def select_soil_layer_by_depth_from_pydantic(buried_depth: float, soil_layers: List[Any]) -> Any:
    """
    从Pydantic模型列表中根据基础埋深选择合适的土层
    
    Args:
        buried_depth: 基础埋深(m)
        soil_layers: SoilLayerModel对象列表
        
    Returns:
        SoilLayerModel: 选中的土层对象
    """
    if not soil_layers:
        raise ValueError("土层信息列表不能为空")
    
    # 转换为字典格式进行处理
    soil_layers_dict = []
    for layer in soil_layers:
        if hasattr(layer, 'dict'):
            # Pydantic模型
            layer_dict = layer.dict()
        elif hasattr(layer, '__dict__'):
            # 普通对象
            layer_dict = layer.__dict__.copy()
        else:
            # 字典
            layer_dict = dict(layer)
        soil_layers_dict.append(layer_dict)
    
    # 选择土层
    selected_dict = select_soil_layer_by_depth(buried_depth, soil_layers_dict)
    
    # 找到对应的原始对象
    for i, layer_dict in enumerate(soil_layers_dict):
        if layer_dict == selected_dict:
            return soil_layers[i]
    
    # 如果没找到匹配的，返回第一个
    return soil_layers[0]