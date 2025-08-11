from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List

from app.schemas import (
    CalculationResponse,
    ComprehensiveCalculationRequest
)
from app.services.calculation_service import CalculationService
from app.utils.logger import get_logger
from app.utils.soil_layer_selector import select_soil_layer_by_depth_from_pydantic

logger = get_logger(__name__)

# 创建路由器
router = APIRouter(
    prefix="/api/calculation",
    tags=["风机计算"],
    responses={404: {"description": "未找到"}}
)

# 依赖注入
def get_calculation_service() -> CalculationService:
    """获取计算服务实例"""
    return CalculationService()


@router.post(
    "/comprehensive",
    response_model=CalculationResponse,
    summary="一键综合计算",
    description="风机重力基础整体验算服务"
)
async def comprehensive_calculation(
    request: ComprehensiveCalculationRequest,
    service: CalculationService = Depends(get_calculation_service)
):
    """
    综合计算接口 - 包含基础体型验算、基础自重计算和荷载组合计算
    
    该接口执行完整的计算流程：
    1. 基础体型验算 - 验证基础几何尺寸是否合理
    2. 基础自重计算 - 计算基础自重、回填土重量和浮力等9个结果
    3. 荷载组合计算 - 调用LoadingCondition中所有的核算方法
    4. 脱开面积验算 - 计算基础脱开面积
    5. 地基承载力验算 - 计算地基承载力
    6. 地基变形验算 - 计算地基变形
    7. 抗倾覆验算 - 计算抗倾覆力矩
    8. 基础抗滑验算 - 计算基础抗滑力矩
    9. 刚度验算 - 计算基础刚度
    10. 抗剪强度验算 - 计算基础抗剪强度
    11. 基础抗冲切验算 - 计算基础抗冲切承载力
    
    支持小驼峰命名的完整参数结构，包括geometry、material和soilLayers。
    
    Args:
        request: 综合计算请求，包含基础几何信息、材料属性和土层信息
        service: 计算服务实例
        
    Returns:
        CalculationResponse: 包含体型验算、自重计算和荷载组合计算结果的响应
        
    Raises:
        HTTPException: 当计算失败时抛出异常
    """
    try:
        logger.info("开始综合计算流程")
        
        # 转换为原有格式
        # geometry, material, soil_layers, design_parameters, stiffness_requirements = request.to_original_format()
        
        # 根据基础埋深选择合适的土层
        selected_soil_layer = select_soil_layer_by_depth_from_pydantic(request.geometry.buried_depth, request.soilLayers)
        
        # 从设计参数中获取覆土容重和地下水深度
        cover_soil_density = request.designParameters.cover_soil_density
        groundwater_depth = request.designParameters.water_depth
        
        # 1. 基础体型验算
        logger.info("开始基础体型验算")
        validation_result = await service.validate_foundation_geometry(request.geometry)
        logger.info(f"基础体型验算完成")
        
        # 2. 基础自重计算
        logger.info(f"开始自重计算")
        # 将土层数据转换为字典格式以传递给自重计算器
        soil_layers_dict = [layer.model_dump() for layer in request.soilLayers]
        self_weight_result = await service.calculate_self_weight(request.geometry, request.material, cover_soil_density, groundwater_depth, soil_layers_dict)
        logger.info("自重计算完成")

        # 3. 计算塔筒底部风机荷载
        logger.info("开始计算塔筒底部风机荷载")
        tower_base_load_request = request.get_tower_base_load_request()
        tower_base_load_result = await service.calculate_tower_base_turbine_load(tower_base_load_request)
        logger.info("塔筒底部风机荷载计算完成")
        
        # 4. 获取四种工况的荷载条件
        logger.info("获取塔筒底部风机荷载四种工况参数")
        loading_conditions = request.get_loading_conditions()
        logger.info(f"获取到 {len(loading_conditions)} 种工况的荷载参数")
        
        # 5. 基础底部荷载值计算 - 调用LoadingCondition中所有的核算方法，传入四种工况荷载和地震力数据
        logger.info("开始荷载组合计算")
        load_calculation_results = await service.calculate_comprehensive_load_analysis(request.geometry, request.material, self_weight_result, loading_conditions, tower_base_load_result, soil_layers_dict)
        logger.info("荷载组合计算完成")

        # 6. 脱开面积验算
        logger.info("开始脱开面积验算")
        detachment_area_result = await service.calculate_detachment_area_analysis(request.geometry, load_calculation_results,request.allowedDetachmentArea)
        logger.info("脱开面积验算完成")

        # 7. 地基承载力验算
        logger.info("开始地基承载力验算")
        foundation_bearing_result = await service.calculate_foundation_bearing_capacity(request.geometry, selected_soil_layer, load_calculation_results)
        logger.info("地基承载力验算完成")

        # 8. 地基变形验算
        logger.info("开始地基变形验算")
        settlement_result = await service.calculate_settlement_analysis(request.geometry, request.soilLayers, load_calculation_results)
        logger.info("地基变形验算完成")

        # 9. 抗倾覆验算
        logger.info("开始抗倾覆验算")
        anti_overturning_result = await service.calculate_anti_overturning_analysis(request.geometry, load_calculation_results, self_weight_result, request.designParameters.importance_factor)
        logger.info("抗倾覆验算完成")

        # 10. 基础抗滑验算
        logger.info("开始基础抗滑验算")
        anti_sliding_result = await service.calculate_anti_sliding_analysis(request.geometry, load_calculation_results, self_weight_result, request.designParameters.importance_factor)
        logger.info("基础抗滑验算完成")

        # 11. 刚度验算
        logger.info("开始刚度验算")
        stiffness_result = await service.calculate_stiffness_analysis(request.geometry, request.soilLayers, request.stiffnessRequirements)
        logger.info("刚度验算完成")

        # 12. 基础抗剪强度计算
        logger.info("开始基础抗剪强度计算")
        shear_strength_result = await service.calculate_shear_strength_analysis(
            request.geometry, load_calculation_results, self_weight_result, request.material, 
            reinforcement_diameter=20.0, importance_factor=request.designParameters.importance_factor
        )
        logger.info("基础抗剪强度计算完成")

        # 13. 地基抗冲切验算
        logger.info("开始地基抗冲切验算")
        anti_punching_result = await service.calculate_anti_punching_analysis(
            request.geometry, load_calculation_results, self_weight_result, request.material, 
            reinforcement_diameter=20.0, importance_factor=request.designParameters.importance_factor
        )
        logger.info("地基抗冲切验算完成")
        
        # 组合结果
        # 为每个模块添加calculation_type字段并放在第一位
        geometry_validation_data = {"calculation_type": "基础体型验算", **validation_result.model_dump()}
        self_weight_data = {"calculation_type": "基础自重计算", **self_weight_result.model_dump()}
        tower_base_load_data = {"calculation_type": "塔底荷载计算", **tower_base_load_result.model_dump()}
        load_analysis_data = {"calculation_type": "荷载组合计算", **load_calculation_results}
        detachment_area_data = {"calculation_type": "脱开面积验算", **detachment_area_result.model_dump()}
        bearing_capacity_data = {"calculation_type": "地基承载力验算", **foundation_bearing_result.model_dump()}
        settlement_analysis_data = {"calculation_type": "地基变形验算", **settlement_result.model_dump()}
        anti_overturning_data = {"calculation_type": "抗倾覆验算", **anti_overturning_result.model_dump()}
        anti_sliding_data = {"calculation_type": "基础抗滑验算", **anti_sliding_result.model_dump()}
        stiffness_data = {"calculation_type": "刚度验算", **stiffness_result.model_dump()}
        shear_strength_data = {"calculation_type": "基础抗剪强度验算", **shear_strength_result.model_dump()}
        anti_punching_data = {"calculation_type": "基础抗冲切验算", **anti_punching_result.model_dump()}
        comprehensive_result = {
            "geometry_validation": geometry_validation_data,
            "self_weight": self_weight_data,
            "tower_base_load": tower_base_load_data,
            "load_analysis": load_analysis_data,
            "detachment_area_analysis": detachment_area_data,
            "bearing_capacity_analysis": bearing_capacity_data,
            "settlement_analysis": settlement_analysis_data,
            "anti_overturning_analysis": anti_overturning_data,
            "anti_sliding_analysis": anti_sliding_data,
            "stiffness_analysis": stiffness_data,
            "shear_strength_analysis": shear_strength_data,
            "anti_punching_analysis": anti_punching_data,
            "summary": {
                "is_design_acceptable": (validation_result.is_geometry_valid and 
                                       validation_result.is_slope_compliant and 
                                        detachment_area_result.overall_compliance and 
                                        foundation_bearing_result.overall_compliance and
                                       settlement_analysis_data.get("overall_compliance", False) and
                                       anti_overturning_result.overall_compliance and
                                       anti_sliding_result.overall_compliance and
                                       stiffness_result.overall_compliance and
                                       shear_strength_result.overall_compliance and
                                       anti_punching_result.overall_compliance),
                "critical_factors": [],
                "recommendations": []
            }
        }
        
        # 添加设计建议
        if not validation_result.is_geometry_valid:
            comprehensive_result["summary"]["critical_factors"].append("基础几何尺寸不符合要求")
            comprehensive_result["summary"]["recommendations"].append("建议调整基础尺寸参数")
        
        if not validation_result.is_slope_compliant:
            comprehensive_result["summary"]["critical_factors"].append("基础坡度不符合规范要求")
            comprehensive_result["summary"]["recommendations"].append("建议调整基础坡度设计")
        
        if not detachment_area_result.overall_compliance:
            comprehensive_result["summary"]["critical_factors"].append("脱开面积验算不符合规范要求")
            comprehensive_result["summary"]["recommendations"].append("建议增大基础尺寸或优化荷载分布")
        
        if not foundation_bearing_result.overall_compliance:
            comprehensive_result["summary"]["critical_factors"].append("地基承载力验算不符合规范要求")
            comprehensive_result["summary"]["recommendations"].append("建议增大基础尺寸或改善地基土质")
        
        if not settlement_result.overall_compliance:
            comprehensive_result["summary"]["critical_factors"].append("地基沉降验算不符合规范要求")
            comprehensive_result["summary"]["recommendations"].append("建议增大基础尺寸或改善地基土质以减少沉降")
        
        if not anti_overturning_result.overall_compliance:
            comprehensive_result["summary"]["critical_factors"].append("抗倾覆验算不符合规范要求")
            comprehensive_result["summary"]["recommendations"].append("建议增大基础尺寸或减小倾覆力矩")
        
        if not anti_sliding_result.overall_compliance:
            comprehensive_result["summary"]["critical_factors"].append("基础抗滑验算不符合规范要求")
            comprehensive_result["summary"]["recommendations"].append("建议增大基础尺寸或优化地基处理")
        
        if not shear_strength_result.overall_compliance:
            comprehensive_result["summary"]["critical_factors"].append("基础抗剪强度验算不符合规范要求")
            comprehensive_result["summary"]["recommendations"].append("建议增大基础有效截面高度或提高混凝土强度")
        
        if not anti_punching_result.overall_compliance:
            comprehensive_result["summary"]["critical_factors"].append("基础抗冲切验算不符合规范要求")
            comprehensive_result["summary"]["recommendations"].append("建议增大基础有效截面高度或提高混凝土强度")
        
        logger.info("综合计算流程完成")
        
        return CalculationResponse(
            success=True,
            message="综合计算完成",
            data=comprehensive_result
        )
        
    except ValueError as e:
        logger.warning(f"输入参数错误: {str(e)}")
        raise HTTPException(status_code=400, detail=f"输入参数错误: {str(e)}")
    
    except Exception as e:
        logger.error(f"综合计算失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"综合计算失败: {str(e)}")

