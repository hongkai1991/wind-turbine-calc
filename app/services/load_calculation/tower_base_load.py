import httpx
from typing import Optional
from app.schemas.load import TowerBaseLoadRequest, TowerBaseLoadResponse
from app.utils.logger import get_logger

logger = get_logger(__name__)

class TowerBaseLoadCalculator:
    """塔筒底部荷载计算器 - 负责调用外部API计算塔筒荷载"""
    
    def __init__(self, api_url: Optional[str] = None, timeout: float = 30.0):
        """初始化计算器
        
        Args:
            api_url: 外部API地址，默认使用配置中的地址
            timeout: 请求超时时间（秒）
        """
        self.api_url = api_url or "http://39.105.37.215:8082/wind/loadcalc"
        self.timeout = timeout

    async def calculate(self, request: TowerBaseLoadRequest) -> TowerBaseLoadResponse:
        """
        计算塔筒底部风机荷载
        
        Args:
            request: 塔筒底部荷载计算请求
            
        Returns:
            TowerBaseLoadResponse: 塔筒底部荷载计算结果
        """
        logger.info("开始计算塔筒底部风机荷载")
        
        try:
            # 调用外部API
            
            # 准备请求数据，使用别名进行序列化
            request_data = request.model_dump(by_alias=True)
            
            logger.info(f"调用外部API: {self.api_url}")
            logger.debug(f"请求参数: {request_data}")
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(self.api_url, json=request_data)
                response.raise_for_status()
                
                # 解析响应数据
                response_data = response.json()
                logger.debug(f"API响应: {response_data}")
                
                # 将响应数据转换为模型
                result = TowerBaseLoadResponse(**response_data)
                
                if result.is_success:
                    logger.info(f"塔筒底部风机荷载计算完成，最大振动周期: {result.max_vibration_period:.4f}s")
                    logger.info(f"塔筒验证结果: {result.tower_drum_validation_message}")
                else:
                    logger.warning(f"API计算失败: {result.error_message}")
                
                return result
            
        except httpx.TimeoutException:
            error_msg = "调用外部API超时"
            logger.error(error_msg)
            raise Exception(error_msg)
        except httpx.HTTPStatusError as e:
            error_msg = f"API调用失败，状态码: {e.response.status_code}"
            logger.error(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            logger.error(f"塔筒底部风机荷载计算失败: {str(e)}")
            raise

