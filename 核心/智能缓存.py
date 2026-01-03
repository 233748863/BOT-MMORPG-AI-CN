"""
智能缓存模块
用于检测结果的智能缓存

功能:
- 基于帧相似度的缓存决策
- 区域感知缓存
- 缓存统计
"""

import time
import json
import os
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass, field
import numpy as np
import logging

from 核心.帧比较 import 帧比较器, 快速帧差异检测

# 配置日志
logging.basicConfig(level=logging.INFO)
日志 = logging.getLogger(__name__)


@dataclass
class 缓存统计:
    """缓存性能统计"""
    总请求数: int = 0
    缓存命中数: int = 0
    缓存未命中数: int = 0
    过期失效数: int = 0
    区域失效数: int = 0
    强制刷新数: int = 0
    
    @property
    def 命中率(self) -> float:
        """计算缓存命中率"""
        if self.总请求数 == 0:
            return 0.0
        return self.缓存命中数 / self.总请求数
    
    def 重置(self):
        """重置统计"""
        self.总请求数 = 0
        self.缓存命中数 = 0
        self.缓存未命中数 = 0
        self.过期失效数 = 0
        self.区域失效数 = 0
        self.强制刷新数 = 0
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            '总请求数': self.总请求数,
            '缓存命中数': self.缓存命中数,
            '缓存未命中数': self.缓存未命中数,
            '过期失效数': self.过期失效数,
            '区域失效数': self.区域失效数,
            '强制刷新数': self.强制刷新数,
            '命中率': f"{self.命中率:.2%}"
        }


@dataclass
class 优先区域:
    """优先检测区域"""
    名称: str
    x: float  # 相对坐标 0-1
    y: float
    宽度: float
    高度: float
    阈值: float = 0.9  # 该区域的相似度阈值
    
    def 获取绝对坐标(self, 图像宽度: int, 图像高度: int) -> Tuple[int, int, int, int]:
        """获取绝对像素坐标"""
        return (
            int(self.x * 图像宽度),
            int(self.y * 图像高度),
            int(self.宽度 * 图像宽度),
            int(self.高度 * 图像高度)
        )


@dataclass
class 缓存条目:
    """缓存条目"""
    结果: List[Any]
    时间戳: float
    参考帧: np.ndarray
    
    def 已过期(self, 过期时间: float) -> bool:
        """检查是否已过期"""
        return (time.time() - self.时间戳) > 过期时间


class 缓存策略:
    """可配置的缓存策略"""
    
    def __init__(self, 配置: dict = None):
        """
        初始化缓存策略
        
        参数:
            配置: 策略配置字典
        """
        self.全局阈值: float = 0.95
        self.过期时间: float = 0.5  # 秒
        self.比较方法: str = "histogram"
        self.优先区域列表: List[优先区域] = []
        self.启用时间过期: bool = True
        
        if 配置:
            self.从字典加载(配置)
    
    def 从字典加载(self, 配置: dict):
        """从字典加载配置"""
        self.全局阈值 = 配置.get('全局相似度阈值', 0.95)
        self.过期时间 = 配置.get('过期时间', 0.5)
        self.比较方法 = 配置.get('比较方法', 'histogram')
        self.启用时间过期 = 配置.get('启用时间过期', True)
        
        # 加载优先区域
        self.优先区域列表 = []
        for 区域配置 in 配置.get('优先区域', []):
            区域坐标 = 区域配置.get('区域', [0, 0, 1, 1])
            self.优先区域列表.append(优先区域(
                名称=区域配置.get('名称', '未命名'),
                x=区域坐标[0],
                y=区域坐标[1],
                宽度=区域坐标[2],
                高度=区域坐标[3],
                阈值=区域配置.get('阈值', 0.9)
            ))
    
    def 从文件加载(self, 配置路径: str):
        """从配置文件加载策略"""
        with open(配置路径, 'r', encoding='utf-8') as f:
            配置 = json.load(f)
        self.从字典加载(配置)
    
    def 保存到文件(self, 配置路径: str):
        """保存策略到文件"""
        配置 = {
            '全局相似度阈值': self.全局阈值,
            '过期时间': self.过期时间,
            '比较方法': self.比较方法,
            '启用时间过期': self.启用时间过期,
            '优先区域': [
                {
                    '名称': 区域.名称,
                    '区域': [区域.x, 区域.y, 区域.宽度, 区域.高度],
                    '阈值': 区域.阈值
                }
                for 区域 in self.优先区域列表
            ]
        }
        
        os.makedirs(os.path.dirname(配置路径) or '.', exist_ok=True)
        with open(配置路径, 'w', encoding='utf-8') as f:
            json.dump(配置, f, ensure_ascii=False, indent=2)
    
    def 应该使用缓存(self, 全局相似度: float, 
                     区域相似度列表: List[float],
                     缓存年龄: float) -> Tuple[bool, str]:
        """
        判断是否应该使用缓存
        
        参数:
            全局相似度: 全局帧相似度
            区域相似度列表: 各优先区域的相似度
            缓存年龄: 缓存已存在的时间（秒）
            
        返回:
            (是否使用缓存, 原因)
        """
        # 检查时间过期
        if self.启用时间过期 and 缓存年龄 > self.过期时间:
            return False, "缓存已过期"
        
        # 检查全局相似度
        if 全局相似度 < self.全局阈值:
            return False, f"全局相似度不足 ({全局相似度:.3f} < {self.全局阈值})"
        
        # 检查优先区域
        for i, (区域, 相似度) in enumerate(zip(self.优先区域列表, 区域相似度列表)):
            if 相似度 < 区域.阈值:
                return False, f"区域 '{区域.名称}' 相似度不足 ({相似度:.3f} < {区域.阈值})"
        
        return True, "缓存有效"


class 智能缓存:
    """智能检测结果缓存"""
    
    def __init__(self, 检测器=None,
                 策略: 缓存策略 = None,
                 相似度阈值: float = 0.95,
                 过期时间: float = 0.5):
        """
        初始化智能缓存
        
        参数:
            检测器: 检测器实例（如 YOLO 检测器）
            策略: 缓存策略，None 则使用默认策略
            相似度阈值: 使用缓存的相似度阈值
            过期时间: 缓存过期时间（秒）
        """
        self.检测器 = 检测器
        self.策略 = 策略 or 缓存策略({
            '全局相似度阈值': 相似度阈值,
            '过期时间': 过期时间
        })
        
        self._缓存: Optional[缓存条目] = None
        self._比较器 = 帧比较器(self.策略.比较方法)
        self._统计 = 缓存统计()
    
    def 设置检测器(self, 检测器):
        """设置检测器"""
        self.检测器 = 检测器
    
    def 检测(self, 图像: np.ndarray) -> List[Any]:
        """
        智能检测（自动决定是否使用缓存）
        
        参数:
            图像: 输入图像
            
        返回:
            检测结果列表
        """
        self._统计.总请求数 += 1
        
        # 检查是否有缓存
        if self._缓存 is None:
            return self._执行检测并缓存(图像, "首次检测")
        
        # 快速差异检测
        if 快速帧差异检测(self._缓存.参考帧, 图像, 阈值=0.15):
            # 有明显差异，进行详细比较
            pass
        else:
            # 几乎相同，直接使用缓存
            self._统计.缓存命中数 += 1
            return self._缓存.结果
        
        # 计算全局相似度
        全局相似度 = self._比较器.比较(self._缓存.参考帧, 图像)
        
        # 计算优先区域相似度
        区域相似度列表 = []
        if self.策略.优先区域列表:
            高度, 宽度 = 图像.shape[:2]
            for 区域 in self.策略.优先区域列表:
                坐标 = 区域.获取绝对坐标(宽度, 高度)
                相似度 = self._比较器.比较区域(self._缓存.参考帧, 图像, 坐标)
                区域相似度列表.append(相似度)
        
        # 计算缓存年龄
        缓存年龄 = time.time() - self._缓存.时间戳
        
        # 判断是否使用缓存
        使用缓存, 原因 = self.策略.应该使用缓存(全局相似度, 区域相似度列表, 缓存年龄)
        
        if 使用缓存:
            self._统计.缓存命中数 += 1
            return self._缓存.结果
        else:
            # 更新统计
            if "过期" in 原因:
                self._统计.过期失效数 += 1
            elif "区域" in 原因:
                self._统计.区域失效数 += 1
            
            return self._执行检测并缓存(图像, 原因)
    
    def _执行检测并缓存(self, 图像: np.ndarray, 原因: str = "") -> List[Any]:
        """执行检测并更新缓存"""
        self._统计.缓存未命中数 += 1
        
        if self.检测器 is None:
            日志.warning("检测器未设置")
            return []
        
        # 执行检测
        try:
            结果 = self.检测器.检测(图像)
        except Exception as e:
            日志.error(f"检测失败: {e}")
            # 如果有缓存，返回缓存结果
            if self._缓存:
                return self._缓存.结果
            return []
        
        # 更新缓存
        self._缓存 = 缓存条目(
            结果=结果,
            时间戳=time.time(),
            参考帧=图像.copy()
        )
        
        return 结果
    
    def 强制刷新(self, 图像: np.ndarray) -> List[Any]:
        """
        强制执行新检测
        
        参数:
            图像: 输入图像
            
        返回:
            检测结果列表
        """
        self._统计.总请求数 += 1
        self._统计.强制刷新数 += 1
        return self._执行检测并缓存(图像, "强制刷新")
    
    def 清空缓存(self):
        """清空缓存"""
        self._缓存 = None
        日志.info("缓存已清空")
    
    def 获取统计(self) -> dict:
        """获取缓存统计信息"""
        return self._统计.to_dict()
    
    def 打印统计(self):
        """打印缓存统计"""
        统计 = self.获取统计()
        print("\n缓存统计:")
        print(f"  总请求数: {统计['总请求数']}")
        print(f"  缓存命中: {统计['缓存命中数']}")
        print(f"  缓存未命中: {统计['缓存未命中数']}")
        print(f"  过期失效: {统计['过期失效数']}")
        print(f"  区域失效: {统计['区域失效数']}")
        print(f"  强制刷新: {统计['强制刷新数']}")
        print(f"  命中率: {统计['命中率']}")
    
    def 重置统计(self):
        """重置统计数据"""
        self._统计.重置()
    
    def 预热(self, 图像: np.ndarray):
        """
        预热缓存
        
        参数:
            图像: 用于预热的图像
        """
        if self.检测器:
            self._执行检测并缓存(图像, "预热")
            日志.info("缓存预热完成")


# 默认缓存配置
默认缓存配置 = {
    "全局相似度阈值": 0.95,
    "过期时间": 0.5,
    "比较方法": "histogram",
    "优先区域": [
        {
            "名称": "屏幕中心",
            "区域": [0.3, 0.3, 0.4, 0.4],
            "阈值": 0.9
        }
    ],
    "启用时间过期": True
}
