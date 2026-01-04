"""
缓存策略模块
定义智能缓存的决策规则

功能:
- 全局相似度阈值判断
- 优先区域阈值判断
- 缓存过期判断
- 配置文件加载

需求: 2.1, 2.2, 2.3, 3.1, 3.2, 3.3, 3.4
"""

import json
import os
import logging
from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Any, Optional

# 配置日志
logging.basicConfig(level=logging.INFO)
日志 = logging.getLogger(__name__)


@dataclass
class 优先区域:
    """优先区域配置"""
    名称: str  # 区域名称
    区域: Tuple[float, float, float, float]  # 相对坐标 (x, y, w, h)，范围 0.0-1.0
    阈值: float = 0.9  # 该区域的相似度阈值（比全局阈值更严格）
    
    def __post_init__(self):
        """验证数据有效性"""
        if len(self.区域) != 4:
            raise ValueError(f"区域必须是4元组 (x, y, w, h)，当前值: {self.区域}")
        
        x, y, w, h = self.区域
        if not (0.0 <= x <= 1.0 and 0.0 <= y <= 1.0):
            raise ValueError(f"区域坐标必须在 0.0-1.0 范围内，当前值: x={x}, y={y}")
        if not (0.0 < w <= 1.0 and 0.0 < h <= 1.0):
            raise ValueError(f"区域宽高必须在 0.0-1.0 范围内，当前值: w={w}, h={h}")
        if not (0.0 <= self.阈值 <= 1.0):
            raise ValueError(f"阈值必须在 0.0-1.0 范围内，当前值: {self.阈值}")
    
    def 转换为像素坐标(self, 图像宽度: int, 图像高度: int) -> Tuple[int, int, int, int]:
        """
        将相对坐标转换为像素坐标
        
        参数:
            图像宽度: 图像宽度（像素）
            图像高度: 图像高度（像素）
            
        返回:
            (x, y, w, h) 像素坐标
        """
        x, y, w, h = self.区域
        return (
            int(x * 图像宽度),
            int(y * 图像高度),
            int(w * 图像宽度),
            int(h * 图像高度)
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "名称": self.名称,
            "区域": list(self.区域),
            "阈值": self.阈值
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> '优先区域':
        """从字典创建"""
        return cls(
            名称=data.get("名称", "未命名区域"),
            区域=tuple(data.get("区域", [0.0, 0.0, 1.0, 1.0])),
            阈值=data.get("阈值", 0.9)
        )


@dataclass
class 缓存策略:
    """
    可配置的缓存策略
    
    决定何时使用缓存、何时重新检测的规则
    
    需求: 2.1, 2.2, 2.3, 3.1, 3.2, 3.3
    """
    全局阈值: float = 0.95  # 全局相似度阈值
    过期时间: float = 0.5  # 缓存过期时间（秒）
    启用时间过期: bool = True  # 是否启用基于时间的过期
    比较方法: str = "histogram"  # 帧比较方法
    优先区域列表: List[优先区域] = field(default_factory=list)  # 优先区域列表
    预热帧数: int = 1  # 预热帧数
    
    def __post_init__(self):
        """验证数据有效性"""
        if not (0.0 <= self.全局阈值 <= 1.0):
            日志.warning(f"全局阈值 {self.全局阈值} 超出范围，使用默认值 0.95")
            self.全局阈值 = 0.95
        
        if self.过期时间 < 0:
            日志.warning(f"过期时间 {self.过期时间} 不能为负，使用默认值 0.5")
            self.过期时间 = 0.5
        
        if self.比较方法 not in ["histogram", "ssim", "mse", "hash"]:
            日志.warning(f"不支持的比较方法 {self.比较方法}，使用默认方法 histogram")
            self.比较方法 = "histogram"
    
    def 应该使用缓存(self, 全局相似度: float, 
                     区域相似度列表: List[float] = None,
                     缓存年龄: float = 0.0) -> bool:
        """
        判断是否应该使用缓存
        
        参数:
            全局相似度: 全帧相似度分数 (0.0-1.0)
            区域相似度列表: 各优先区域的相似度列表
            缓存年龄: 缓存已存在的时间（秒）
            
        返回:
            是否应该使用缓存
            
        需求: 2.1, 2.2, 3.2
        """
        # 检查时间过期
        if self.启用时间过期 and 缓存年龄 > self.过期时间:
            日志.debug(f"缓存已过期: 年龄={缓存年龄:.3f}s > 过期时间={self.过期时间}s")
            return False
        
        # 检查全局相似度
        if 全局相似度 < self.全局阈值:
            日志.debug(f"全局相似度不足: {全局相似度:.3f} < {self.全局阈值}")
            return False
        
        # 检查优先区域相似度
        if 区域相似度列表 and self.优先区域列表:
            for i, (区域, 相似度) in enumerate(zip(self.优先区域列表, 区域相似度列表)):
                if 相似度 < 区域.阈值:
                    日志.debug(f"优先区域 '{区域.名称}' 相似度不足: {相似度:.3f} < {区域.阈值}")
                    return False
        
        return True
    
    def 获取失效原因(self, 全局相似度: float,
                     区域相似度列表: List[float] = None,
                     缓存年龄: float = 0.0) -> str:
        """
        获取缓存失效的原因
        
        返回:
            失效原因描述，如果应该使用缓存则返回空字符串
        """
        # 检查时间过期
        if self.启用时间过期 and 缓存年龄 > self.过期时间:
            return f"时间过期 ({缓存年龄:.3f}s > {self.过期时间}s)"
        
        # 检查全局相似度
        if 全局相似度 < self.全局阈值:
            return f"全局相似度不足 ({全局相似度:.3f} < {self.全局阈值})"
        
        # 检查优先区域相似度
        if 区域相似度列表 and self.优先区域列表:
            for i, (区域, 相似度) in enumerate(zip(self.优先区域列表, 区域相似度列表)):
                if 相似度 < 区域.阈值:
                    return f"优先区域 '{区域.名称}' 变化显著 ({相似度:.3f} < {区域.阈值})"
        
        return ""
    
    def 添加优先区域(self, 名称: str, 区域: Tuple[float, float, float, float], 
                     阈值: float = 0.9) -> None:
        """
        添加优先区域
        
        参数:
            名称: 区域名称
            区域: 相对坐标 (x, y, w, h)
            阈值: 该区域的相似度阈值
            
        需求: 3.1
        """
        新区域 = 优先区域(名称=名称, 区域=区域, 阈值=阈值)
        self.优先区域列表.append(新区域)
        日志.info(f"添加优先区域: {名称}, 区域={区域}, 阈值={阈值}")
    
    def 移除优先区域(self, 名称: str) -> bool:
        """
        移除优先区域
        
        参数:
            名称: 要移除的区域名称
            
        返回:
            是否成功移除
        """
        原长度 = len(self.优先区域列表)
        self.优先区域列表 = [区域 for 区域 in self.优先区域列表 if 区域.名称 != 名称]
        已移除 = len(self.优先区域列表) < 原长度
        
        if 已移除:
            日志.info(f"移除优先区域: {名称}")
        
        return 已移除
    
    def 清空优先区域(self) -> None:
        """清空所有优先区域"""
        self.优先区域列表.clear()
        日志.info("已清空所有优先区域")
    
    def 获取像素区域列表(self, 图像宽度: int, 图像高度: int) -> List[Tuple[int, int, int, int]]:
        """
        获取所有优先区域的像素坐标
        
        参数:
            图像宽度: 图像宽度（像素）
            图像高度: 图像高度（像素）
            
        返回:
            像素坐标列表 [(x, y, w, h), ...]
        """
        return [区域.转换为像素坐标(图像宽度, 图像高度) for 区域 in self.优先区域列表]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "全局相似度阈值": self.全局阈值,
            "过期时间": self.过期时间,
            "启用时间过期": self.启用时间过期,
            "比较方法": self.比较方法,
            "优先区域": [区域.to_dict() for 区域 in self.优先区域列表],
            "预热帧数": self.预热帧数
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> '缓存策略':
        """从字典创建"""
        优先区域数据 = data.get("优先区域", [])
        优先区域列表 = [优先区域.from_dict(区域) for 区域 in 优先区域数据]
        
        return cls(
            全局阈值=data.get("全局相似度阈值", 0.95),
            过期时间=data.get("过期时间", 0.5),
            启用时间过期=data.get("启用时间过期", True),
            比较方法=data.get("比较方法", "histogram"),
            优先区域列表=优先区域列表,
            预热帧数=data.get("预热帧数", 1)
        )


    def 从配置加载(self, 配置路径: str) -> bool:
        """
        从配置文件加载策略参数
        
        参数:
            配置路径: JSON 配置文件路径
            
        返回:
            加载是否成功
            
        需求: 3.4
        """
        if not os.path.exists(配置路径):
            日志.warning(f"配置文件不存在: {配置路径}，使用默认配置")
            return False
        
        try:
            with open(配置路径, 'r', encoding='utf-8') as f:
                配置数据 = json.load(f)
            
            # 加载缓存相关配置
            缓存配置 = 配置数据.get("缓存配置", 配置数据)
            
            # 更新策略参数
            if "全局相似度阈值" in 缓存配置:
                self.全局阈值 = float(缓存配置["全局相似度阈值"])
            
            if "过期时间" in 缓存配置:
                self.过期时间 = float(缓存配置["过期时间"])
            
            if "启用时间过期" in 缓存配置:
                self.启用时间过期 = bool(缓存配置["启用时间过期"])
            
            if "比较方法" in 缓存配置:
                self.比较方法 = str(缓存配置["比较方法"])
            
            if "预热帧数" in 缓存配置:
                self.预热帧数 = int(缓存配置["预热帧数"])
            
            # 加载优先区域
            if "优先区域" in 缓存配置:
                self.优先区域列表.clear()
                for 区域数据 in 缓存配置["优先区域"]:
                    try:
                        区域 = 优先区域.from_dict(区域数据)
                        self.优先区域列表.append(区域)
                    except (ValueError, KeyError) as e:
                        日志.warning(f"加载优先区域失败: {e}")
            
            # 重新验证参数
            self.__post_init__()
            
            日志.info(f"成功从 {配置路径} 加载缓存策略配置")
            return True
            
        except json.JSONDecodeError as e:
            日志.error(f"配置文件格式错误: {e}")
            return False
        except Exception as e:
            日志.error(f"加载配置文件失败: {e}")
            return False
    
    def 保存到配置(self, 配置路径: str) -> bool:
        """
        保存策略参数到配置文件
        
        参数:
            配置路径: JSON 配置文件路径
            
        返回:
            保存是否成功
        """
        try:
            # 确保目录存在
            目录 = os.path.dirname(配置路径)
            if 目录 and not os.path.exists(目录):
                os.makedirs(目录)
            
            配置数据 = {"缓存配置": self.to_dict()}
            
            with open(配置路径, 'w', encoding='utf-8') as f:
                json.dump(配置数据, f, ensure_ascii=False, indent=2)
            
            日志.info(f"成功保存缓存策略配置到 {配置路径}")
            return True
            
        except Exception as e:
            日志.error(f"保存配置文件失败: {e}")
            return False
    
    @classmethod
    def 从配置文件创建(cls, 配置路径: str) -> '缓存策略':
        """
        从配置文件创建缓存策略实例
        
        参数:
            配置路径: JSON 配置文件路径
            
        返回:
            缓存策略实例
            
        需求: 3.4
        """
        策略 = cls()
        策略.从配置加载(配置路径)
        return 策略


# 默认缓存配置路径
默认缓存配置路径 = "配置/cache_config.json"


def 获取默认缓存策略() -> 缓存策略:
    """
    获取默认缓存策略
    
    如果存在配置文件则从配置文件加载，否则使用默认值
    
    返回:
        缓存策略实例
    """
    策略 = 缓存策略()
    
    if os.path.exists(默认缓存配置路径):
        策略.从配置加载(默认缓存配置路径)
    
    return 策略


def 创建示例配置文件(配置路径: str = None) -> bool:
    """
    创建示例缓存配置文件
    
    参数:
        配置路径: 配置文件路径，默认为 默认缓存配置路径
        
    返回:
        创建是否成功
    """
    if 配置路径 is None:
        配置路径 = 默认缓存配置路径
    
    示例策略 = 缓存策略(
        全局阈值=0.95,
        过期时间=0.5,
        启用时间过期=True,
        比较方法="histogram",
        预热帧数=1
    )
    
    # 添加示例优先区域
    示例策略.添加优先区域(
        名称="屏幕中心",
        区域=(0.3, 0.3, 0.4, 0.4),
        阈值=0.9
    )
    
    return 示例策略.保存到配置(配置路径)
