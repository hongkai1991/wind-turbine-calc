"""
基础几何和材料属性数据模型模块
包含基础几何信息、材料属性和土层信息
"""
from pydantic import BaseModel, Field
from .base import SoilType


class FoundationGeometry(BaseModel):
    """基础几何信息"""
    base_radius: float = Field(..., gt=0, alias='baseRadius',description="基础底板半径(m)")
    buried_depth: float = Field(..., ge=0, alias='buriedDepth',description="基础埋深(m)")
    column_radius: float = Field(..., gt=0, alias='columnRadius',description="台柱半径(m)")
    column_height: float = Field(..., gt=0, alias='columnHeight',description="台柱高度(m)")
    edge_height: float = Field(..., gt=0, alias='edgeHeight',description="基础边缘高度(m)")
    ground_height: float = Field(..., gt=0, alias='groundHeight',description="地面露出高度(m)")
    frustum_height: float = Field(..., gt=0, alias='frustumHeight',description="基础底板棱台高度(m)")

    def validate_geometry(self) -> float:
        """验证基础外形尺寸"""
        if self.column_radius >= self.base_radius: return False
        if self.edge_height <= 0 or self.frustum_height <= 0: return False
        # 检查基础外形尺寸，基础底板棱台坡度不超过1:2.5
        horizontal_distance = self.base_radius - self.column_radius
        vertical_distance = self.edge_height + self.frustum_height
        overall_dimension = horizontal_distance / vertical_distance
        return overall_dimension
    
    def check_slope_compliance(self) -> dict:
        """检查基础圆台坡度
        
        Returns:
            dict: 包含坡度信息的字典
                - horizontal_to_vertical: 水平:垂直比例 (符合规范表示)
                - is_compliant: 是否符合1:4的规范要求
                - slope_description: 坡度描述
        """
        # 基础圆台坡度检查，通常要求坡度不超过1:4
        horizontal_distance = self.base_radius - self.column_radius
        
        if horizontal_distance <= 0 or self.frustum_height <= 0:
            return {
                "horizontal_to_vertical": 0,
                "is_compliant": False,
                "slope_description": "无效的几何尺寸"
            }
        
        # 水平:垂直比例 (规范表示方式)
        horizontal_to_vertical =round(horizontal_distance / self.frustum_height,3)
        
        # 检查是否符合1:4的规范要求 (即水平:垂直 >= 1:4，也就是水平距离至少是垂直距离的1/4)
        # 1:4 意味着 horizontal_to_vertical >= 0.25
        is_compliant = horizontal_to_vertical >= 0.25
        
        # 生成坡度描述 - 格式为 1:horizontal_to_vertical
        slope_description = f"1:{horizontal_to_vertical:.3f}"
        
        return {
            "horizontal_to_vertical": horizontal_to_vertical,
            "is_compliant": is_compliant,
            "slope_description": slope_description
        }


class MaterialProperties(BaseModel):
    """材料属性信息"""
    concrete_grade: str = Field(default="C40", alias='concreteGrade', description="混凝土等级")
    fc: float = Field(default=19.1, gt=0, alias='fc', description="抗压强度设计值(N/mm²)")
    ft: float = Field(default=1.71, gt=0, alias='ft', description="抗拉强度设计值(N/mm²)")
    fck: float = Field(default=26.8, gt=0, alias='fck', description="抗压强度标准值(N/mm²)")
    ftk: float = Field(default=2.39, gt=0, alias='ftk', description="抗拉强度标准值(N/mm²)")
    ec: float = Field(default=32500.0, gt=0, alias='ec', description="弹性模量(N/mm²)")
    efc: float = Field(default=15000.0, gt=0, alias='efc', description="疲劳变形模量(N/mm²)")
    density: float = Field(default=25.0, gt=0, alias='density', description="混凝土容重(kN/m³)")
    top_cover: float = Field(default=50.0, gt=0, alias='topCover', description="基础底板顶面混凝土保护层厚度(mm)")
    bottom_cover: float = Field(default=60.0, gt=0, alias='bottomCover', description="基础底板底面混凝土保护层厚度(mm)")
    column_cover: float = Field(default=50.0, gt=0, alias='columnCover', description="台柱侧面混凝土保护层厚度(mm)")
    cushion_thickness: float = Field(default=100.0, gt=0, alias='cushionThickness', description="垫层厚度(mm)")
    
    def validate_parameters(self) -> bool:
        """验证参数有效性"""
        return (self.fc > 0 and self.ft > 0 and 
                self.fck >= self.fc and self.ftk >= self.ft)
    
    class Config:
        json_schema_extra = {
            "example": {
                "concrete_grade": "C40",
                "fc": 19.1,
                "ft": 1.71,
                "fck": 26.8,
                "ftk": 2.39,
                "ec": 32500,
                "efc": 32500,
                "density": 25.0,
                "bottom_cover": 50.0,
                "top_cover": 50.0,
                "column_cover": 50.0,
                "cushion_thickness": 100.0
            }
        }


class SoilLayer(BaseModel):
    """土层信息"""
    soil_type: str = Field(..., alias='soilType', description="土层类型(粘性土/砂土)")
    layer_name: str = Field(..., alias='layerName', description="土层名称")
    thickness: float = Field(..., gt=0, alias='thickness', description="厚度(m)")
    elevation: float = Field(..., alias='elevation', description="标高(m)")
    density: float = Field(..., gt=0, alias='density', description="重度(kN/m³)")
    compression_modulus: float = Field(..., gt=0, alias='compressionModulus', description="压缩模量(MPa)")
    cohesion: float = Field(..., ge=0, alias='cohesion', description="内聚力(kPa)")
    friction_angle: float = Field(..., ge=0, le=90, alias='frictionAngle', description="摩擦角(°)")
    m: float = Field(..., ge=0, le=0.5, alias='m', description="摩擦系数")
    fak: float = Field(..., gt=0, alias='fak', description="承载力特征值(kPa)")
    eta_b: float = Field(default=1.0, gt=0, alias='etaB', description="宽度修正系数")
    eta_d: float = Field(default=1.0, gt=0, alias='etaD', description="深度修正系数")
    zeta_a: float = Field(default=1.0, gt=0, alias='zetaA', description="地基抗震承载力修正系数")
    poisson_ratio: float = Field(default=0.25, ge=0, le=0.5, alias='poissonRatio', description="泊松比")
    
    def validate_parameters(self) -> bool:
        """验证参数有效性"""
        try:
            # 验证土层类型
            valid_soil_types = ["粘性土", "砂土", "岩石", "混合土", "粉土", "填土"]
            if self.soil_type not in valid_soil_types:
                return False
            
            # 验证密度范围 (一般土的重度在14-22 kN/m³之间)
            if not (14.0 <= self.density <= 25.0):
                return False
            
            # 验证压缩模量范围 (一般在1-100 MPa之间)
            if not (1.0 <= self.compression_modulus <= 100.0):
                return False
            
            # 验证内聚力范围 (0-200 kPa)
            if not (0.0 <= self.cohesion <= 200.0):
                return False
            
            # 验证摩擦角范围 (0-45°)
            if not (0.0 <= self.friction_angle <= 45.0):
                return False
            
            # 验证摩擦系数范围 (0-0.5)
            if not (0.0 <= self.m <= 0.5):
                return False
            
            # 验证承载力特征值范围 (50-1000 kPa)
            if not (50.0 <= self.fak <= 1000.0):
                return False
            
            # 验证修正系数范围 (0.5-2.0)
            if not (0.5 <= self.eta_b <= 2.0):
                return False
            if not (0.5 <= self.eta_d <= 2.0):
                return False
            if not (0.5 <= self.zeta_a <= 2.0):
                return False
            
            return True
            
        except Exception:
            return False
    
    class Config:
        json_schema_extra = {
            "example": {
                "soil_type": "粘性土",
                "layer_name": "粉质粘土层",
                "thickness": 3.5,
                "density": 19.5,
                "compression_modulus": 12.0,
                "cohesion": 25.0,
                "friction_angle": 18.0,
                "m": 0.35,
                "fak": 150.0,
                "eta_b": 1.0,
                "eta_d": 1.2,
                "zeta_a": 1.0
            }
        }

