from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List
import copy
import itertools

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
                                       settlement_result.overall_compliance and
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


@router.post(
    "/optimal",
    response_model=CalculationResponse,
    summary="计算最优方案",
    description="通过参数优化找到混凝土体积最小的最优基础设计方案"
)
async def calculate_optimal_solution(
    request: ComprehensiveCalculationRequest,
    service: CalculationService = Depends(get_calculation_service)
):
    """
    计算最优方案接口 - 通过调整基础几何参数找到混凝土体积最小的方案
    
    该接口通过以下步骤找到最优方案：
    1. 设置参数调整范围：
       - 基础底板半径：9-12米
       - 台柱半径：3-5.3米  
       - 台柱高度：1.4-2.8米
       - 基础边缘高度：0.8-1米
       - 基础底板棱台高度：0.8-2.8米
    2. 以1米步长对5个参数进行排列组合
    3. 根据公式计算基础埋深：埋深 = 台柱高度 + 棱台高度 + 边缘高度 - 地面露出高度
    4. 过滤基础埋深不在3-5米范围内的组合
    5. 生成所有有效的几何参数组合
    6. 对每个组合调用综合计算方法
    7. 过滤设计不可接受(is_design_acceptable=false)的结果
    8. 筛选出混凝土体积(foundation_volume)最小的结果
    
    Args:
        request: 综合计算请求，包含基础几何信息、材料属性和土层信息
        service: 计算服务实例
        
    Returns:
        CalculationResponse: 混凝土体积最小且设计可接受的最优计算结果
        
    Raises:
        HTTPException: 当计算失败或没有可接受的设计方案时抛出异常
    """
    try:
        logger.info("开始计算最优方案")
        
        # 定义参数范围和步长
        step_size = 1.0
        
        # 参数范围定义
        base_radius_range = [9.0, 10.0, 11.0, 12.0]  # 基础底板半径：9-12米
        column_radius_range = [3.0, 4.0, 5.0]  # 台柱半径：3-5.3米（考虑到步长，取3,4,5）
        column_height_range = [1.4, 2.4]  # 台柱高度：1.4-2.8米（考虑到步长，取1.4,2.4）
        edge_height_range = [0.8, 1.0]  # 基础边缘高度：0.8-1米（考虑到步长，取0.8,1.0）
        frustum_height_range = [0.8, 1.8, 2.8]  # 基础底板棱台高度：0.8-2.8米
        
        logger.info(f"参数组合数量: {len(base_radius_range) * len(column_radius_range) * len(column_height_range) * len(edge_height_range) * len(frustum_height_range)}")
        
        # 生成所有参数组合
        param_combinations = list(itertools.product(
            base_radius_range,
            column_radius_range, 
            column_height_range,
            edge_height_range,
            frustum_height_range
        ))
        
        logger.info(f"开始计算 {len(param_combinations)} 种参数组合")
        
        calculation_results = []
        valid_results = []
        
        for i, (base_radius, column_radius, column_height, edge_height, frustum_height) in enumerate(param_combinations):
            try:
                # 检查几何约束：台柱半径必须小于底板半径
                if column_radius >= base_radius:
                    logger.warning(f"跳过无效组合 {i+1}: 台柱半径({column_radius})大于等于底板半径({base_radius})")
                    continue
                
                # 计算基础埋深：基础埋深 = 台柱高度 + 基础底板棱台高度 + 基础边缘高度 - 地面露出高度
                ground_height = request.geometry.ground_height  # 使用原始请求中的地面露出高度
                calculated_buried_depth = column_height + frustum_height + edge_height - ground_height
                
                # 检查基础埋深范围：3-5米
                if not (3.0 <= calculated_buried_depth <= 5.0):
                    logger.warning(f"跳过无效组合 {i+1}: 计算出的基础埋深({calculated_buried_depth:.2f}m)不在3-5米范围内")
                    continue
                
                # 创建新的请求对象副本
                current_request = copy.deepcopy(request)
                
                # 更新几何参数
                current_request.geometry.base_radius = base_radius
                current_request.geometry.column_radius = column_radius
                current_request.geometry.column_height = column_height
                current_request.geometry.edge_height = edge_height
                current_request.geometry.frustum_height = frustum_height
                current_request.geometry.buried_depth = calculated_buried_depth  # 使用计算出的基础埋深
                
                logger.info(f"计算组合 {i+1}/{len(param_combinations)}: 底板半径={base_radius}, 台柱半径={column_radius}, 台柱高度={column_height}, 边缘高度={edge_height}, 棱台高度={frustum_height}, 计算埋深={calculated_buried_depth:.2f}")
                
                # 调用综合计算方法
                result = await comprehensive_calculation(current_request, service)
                
                if result.success and result.data:
                    # 检查设计可接受性
                    summary_data = result.data.get("summary", {})
                    is_design_acceptable = summary_data.get("is_design_acceptable", False)
                    
                    if not is_design_acceptable:
                        logger.warning(f"组合 {i+1} 设计不可接受，跳过此结果")
                        continue
                    
                    # 提取自重计算结果中的混凝土体积
                    self_weight_data = result.data.get("self_weight", {})
                    foundation_volume = self_weight_data.get("foundation_volume", float('inf'))
                    
                    # 存储结果和对应的参数
                    calculation_result = {
                        "parameters": {
                            "base_radius": base_radius,
                            "column_radius": column_radius,
                            "column_height": column_height,
                            "edge_height": edge_height,
                            "frustum_height": frustum_height,
                            "buried_depth": calculated_buried_depth  # 添加计算出的基础埋深
                        },
                        "foundation_volume": foundation_volume,
                        "calculation_data": result.data,
                        "is_design_acceptable": is_design_acceptable
                    }
                    
                    calculation_results.append(calculation_result)
                    valid_results.append(calculation_result)
                    
                    logger.info(f"组合 {i+1} 计算成功且设计可接受，混凝土体积: {foundation_volume} m³")
                else:
                    logger.warning(f"组合 {i+1} 计算失败")
                    
            except Exception as e:
                logger.error(f"组合 {i+1} 计算异常: {str(e)}")
                continue
        
        if not valid_results:
            raise HTTPException(status_code=400, detail="所有参数组合都计算失败或设计不可接受，请检查输入参数或调整设计要求")
        
        # 找到混凝土体积最小的结果
        optimal_result = min(valid_results, key=lambda x: x["foundation_volume"])
        
        logger.info(f"最优方案找到: 混凝土体积 {optimal_result['foundation_volume']} m³")
        logger.info(f"最优参数: {optimal_result['parameters']}")
        
        # 构造最优结果响应
        optimal_data = optimal_result["calculation_data"].copy()
        optimal_data["optimization_info"] = {
            "total_combinations_tested": len(param_combinations),
            "valid_combinations": len(valid_results),
            "optimal_parameters": optimal_result["parameters"],
            "optimal_foundation_volume": optimal_result["foundation_volume"],
            "optimization_summary": f"在{len(valid_results)}个设计可接受的有效组合中找到最优方案，混凝土体积为{optimal_result['foundation_volume']:.2f}m³"
        }
        
        logger.info("最优方案计算完成")
        
        return CalculationResponse(
            success=True,
            message=f"最优方案计算完成，混凝土体积最小值为{optimal_result['foundation_volume']:.2f}m³",
            data=optimal_data
        )
        
    except ValueError as e:
        logger.warning(f"输入参数错误: {str(e)}")
        raise HTTPException(status_code=400, detail=f"输入参数错误: {str(e)}")
    
    except Exception as e:
        logger.error(f"最优方案计算失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"最优方案计算失败: {str(e)}")

