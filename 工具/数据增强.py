"""
数据增强模块
用于训练数据的图像增强

功能:
- 多种图像变换操作
- 可配置的增强管道
- 批量增强处理
- 增强预览功能
"""

import numpy as np
import cv2
import random
import json
import os
from abc import ABC, abstractmethod
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
日志 = logging.getLogger(__name__)


class 变换基类(ABC):
    """变换操作基类"""
    
    def __init__(self, 概率: float = 0.5, 强度: float = 1.0):
        """
        初始化变换
        
        参数:
            概率: 应用变换的概率 (0-1)
            强度: 变换强度 (0-1)
        """
        self.概率 = max(0.0, min(1.0, 概率))
        self.强度 = max(0.0, min(1.0, 强度))
        self.名称 = self.__class__.__name__
    
    def __call__(self, 图像: np.ndarray) -> np.ndarray:
        """
        应用变换
        
        参数:
            图像: 输入图像 (H, W, C) 或 (H, W)
            
        返回:
            变换后的图像
        """
        if random.random() > self.概率:
            return 图像
        
        try:
            return self._应用变换(图像)
        except Exception as e:
            日志.warning(f"{self.名称} 变换失败: {e}")
            return 图像
    
    @abstractmethod
    def _应用变换(self, 图像: np.ndarray) -> np.ndarray:
        """实际的变换实现"""
        pass
    
    def 获取配置(self) -> dict:
        """获取变换配置"""
        return {
            '类型': self.名称,
            '概率': self.概率,
            '强度': self.强度
        }


class 亮度调整(变换基类):
    """调整图像亮度"""
    
    def __init__(self, 范围: Tuple[float, float] = (-0.2, 0.2), **kwargs):
        """
        参数:
            范围: 亮度调整范围 (最小值, 最大值)，相对于原始亮度
        """
        super().__init__(**kwargs)
        self.范围 = 范围
    
    def _应用变换(self, 图像: np.ndarray) -> np.ndarray:
        # 计算实际调整值
        调整值 = random.uniform(self.范围[0], self.范围[1]) * self.强度
        
        # 转换为浮点数处理
        图像浮点 = 图像.astype(np.float32)
        图像浮点 = 图像浮点 + 调整值 * 255
        
        # 裁剪到有效范围
        return np.clip(图像浮点, 0, 255).astype(np.uint8)
    
    def 获取配置(self) -> dict:
        配置 = super().获取配置()
        配置['范围'] = self.范围
        return 配置


class 对比度调整(变换基类):
    """调整图像对比度"""
    
    def __init__(self, 范围: Tuple[float, float] = (0.8, 1.2), **kwargs):
        """
        参数:
            范围: 对比度调整范围 (最小值, 最大值)，1.0 为原始对比度
        """
        super().__init__(**kwargs)
        self.范围 = 范围
    
    def _应用变换(self, 图像: np.ndarray) -> np.ndarray:
        # 计算实际调整因子
        基础因子 = random.uniform(self.范围[0], self.范围[1])
        因子 = 1.0 + (基础因子 - 1.0) * self.强度
        
        # 转换为浮点数处理
        图像浮点 = 图像.astype(np.float32)
        均值 = np.mean(图像浮点)
        图像浮点 = (图像浮点 - 均值) * 因子 + 均值
        
        return np.clip(图像浮点, 0, 255).astype(np.uint8)
    
    def 获取配置(self) -> dict:
        配置 = super().获取配置()
        配置['范围'] = self.范围
        return 配置


class 水平翻转(变换基类):
    """水平翻转图像"""
    
    def _应用变换(self, 图像: np.ndarray) -> np.ndarray:
        return cv2.flip(图像, 1)


class 垂直翻转(变换基类):
    """垂直翻转图像"""
    
    def _应用变换(self, 图像: np.ndarray) -> np.ndarray:
        return cv2.flip(图像, 0)


class 高斯噪声(变换基类):
    """添加高斯噪声"""
    
    def __init__(self, 标准差: float = 0.02, **kwargs):
        """
        参数:
            标准差: 噪声标准差（相对于255）
        """
        super().__init__(**kwargs)
        self.标准差 = 标准差
    
    def _应用变换(self, 图像: np.ndarray) -> np.ndarray:
        实际标准差 = self.标准差 * self.强度 * 255
        噪声 = np.random.normal(0, 实际标准差, 图像.shape)
        图像浮点 = 图像.astype(np.float32) + 噪声
        return np.clip(图像浮点, 0, 255).astype(np.uint8)
    
    def 获取配置(self) -> dict:
        配置 = super().获取配置()
        配置['标准差'] = self.标准差
        return 配置


class 颜色抖动(变换基类):
    """颜色抖动（色调、饱和度）"""
    
    def __init__(self, 色调范围: float = 0.1, 饱和度范围: float = 0.2, **kwargs):
        """
        参数:
            色调范围: 色调调整范围
            饱和度范围: 饱和度调整范围
        """
        super().__init__(**kwargs)
        self.色调范围 = 色调范围
        self.饱和度范围 = 饱和度范围
    
    def _应用变换(self, 图像: np.ndarray) -> np.ndarray:
        # 转换到 HSV 空间
        if len(图像.shape) == 2:
            return 图像  # 灰度图不处理
        
        hsv = cv2.cvtColor(图像, cv2.COLOR_BGR2HSV).astype(np.float32)
        
        # 调整色调
        色调偏移 = random.uniform(-self.色调范围, self.色调范围) * self.强度 * 180
        hsv[:, :, 0] = (hsv[:, :, 0] + 色调偏移) % 180
        
        # 调整饱和度
        饱和度因子 = 1.0 + random.uniform(-self.饱和度范围, self.饱和度范围) * self.强度
        hsv[:, :, 1] = np.clip(hsv[:, :, 1] * 饱和度因子, 0, 255)
        
        # 转换回 BGR
        return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)
    
    def 获取配置(self) -> dict:
        配置 = super().获取配置()
        配置['色调范围'] = self.色调范围
        配置['饱和度范围'] = self.饱和度范围
        return 配置


class 高斯模糊(变换基类):
    """高斯模糊"""
    
    def __init__(self, 核大小范围: Tuple[int, int] = (3, 7), **kwargs):
        """
        参数:
            核大小范围: 模糊核大小范围（必须为奇数）
        """
        super().__init__(**kwargs)
        self.核大小范围 = 核大小范围
    
    def _应用变换(self, 图像: np.ndarray) -> np.ndarray:
        # 选择核大小（确保为奇数）
        核大小 = random.randint(self.核大小范围[0], self.核大小范围[1])
        if 核大小 % 2 == 0:
            核大小 += 1
        
        return cv2.GaussianBlur(图像, (核大小, 核大小), 0)
    
    def 获取配置(self) -> dict:
        配置 = super().获取配置()
        配置['核大小范围'] = self.核大小范围
        return 配置


class 旋转(变换基类):
    """小角度旋转"""
    
    def __init__(self, 角度范围: Tuple[float, float] = (-10, 10), **kwargs):
        """
        参数:
            角度范围: 旋转角度范围（度）
        """
        super().__init__(**kwargs)
        self.角度范围 = 角度范围
    
    def _应用变换(self, 图像: np.ndarray) -> np.ndarray:
        角度 = random.uniform(self.角度范围[0], self.角度范围[1]) * self.强度
        
        高度, 宽度 = 图像.shape[:2]
        中心 = (宽度 // 2, 高度 // 2)
        
        旋转矩阵 = cv2.getRotationMatrix2D(中心, 角度, 1.0)
        return cv2.warpAffine(图像, 旋转矩阵, (宽度, 高度), borderMode=cv2.BORDER_REFLECT)
    
    def 获取配置(self) -> dict:
        配置 = super().获取配置()
        配置['角度范围'] = self.角度范围
        return 配置


class 缩放裁剪(变换基类):
    """随机缩放并裁剪回原始大小"""
    
    def __init__(self, 缩放范围: Tuple[float, float] = (0.9, 1.1), **kwargs):
        """
        参数:
            缩放范围: 缩放比例范围
        """
        super().__init__(**kwargs)
        self.缩放范围 = 缩放范围
    
    def _应用变换(self, 图像: np.ndarray) -> np.ndarray:
        原始高度, 原始宽度 = 图像.shape[:2]
        
        # 计算缩放比例
        缩放比例 = random.uniform(self.缩放范围[0], self.缩放范围[1])
        缩放比例 = 1.0 + (缩放比例 - 1.0) * self.强度
        
        新宽度 = int(原始宽度 * 缩放比例)
        新高度 = int(原始高度 * 缩放比例)
        
        # 缩放图像
        缩放图像 = cv2.resize(图像, (新宽度, 新高度))
        
        # 裁剪或填充回原始大小
        if 缩放比例 > 1.0:
            # 裁剪
            起始x = (新宽度 - 原始宽度) // 2
            起始y = (新高度 - 原始高度) // 2
            return 缩放图像[起始y:起始y+原始高度, 起始x:起始x+原始宽度]
        else:
            # 填充
            结果 = np.zeros_like(图像)
            起始x = (原始宽度 - 新宽度) // 2
            起始y = (原始高度 - 新高度) // 2
            结果[起始y:起始y+新高度, 起始x:起始x+新宽度] = 缩放图像
            return 结果
    
    def 获取配置(self) -> dict:
        配置 = super().获取配置()
        配置['缩放范围'] = self.缩放范围
        return 配置


# 变换类型映射
变换类型映射 = {
    '亮度调整': 亮度调整,
    '对比度调整': 对比度调整,
    '水平翻转': 水平翻转,
    '垂直翻转': 垂直翻转,
    '高斯噪声': 高斯噪声,
    '颜色抖动': 颜色抖动,
    '高斯模糊': 高斯模糊,
    '旋转': 旋转,
    '缩放裁剪': 缩放裁剪,
}


class 增强管道:
    """可配置的增强管道"""
    
    def __init__(self):
        self.变换列表: List[变换基类] = []
    
    def 添加变换(self, 变换: 变换基类) -> '增强管道':
        """
        添加变换操作
        
        参数:
            变换: 变换操作实例
            
        返回:
            self，支持链式调用
        """
        self.变换列表.append(变换)
        return self
    
    def 清空(self) -> '增强管道':
        """清空所有变换"""
        self.变换列表 = []
        return self
    
    def 从配置加载(self, 配置: dict) -> '增强管道':
        """
        从配置字典加载管道
        
        参数:
            配置: 增强配置字典
            
        返回:
            self
        """
        self.清空()
        
        for 变换名称, 变换配置 in 配置.items():
            if not 变换配置.get('启用', True):
                continue
            
            if 变换名称 not in 变换类型映射:
                日志.warning(f"未知的变换类型: {变换名称}")
                continue
            
            # 提取参数
            参数 = {k: v for k, v in 变换配置.items() if k != '启用'}
            
            try:
                变换实例 = 变换类型映射[变换名称](**参数)
                self.添加变换(变换实例)
            except Exception as e:
                日志.warning(f"创建变换 {变换名称} 失败: {e}")
        
        return self
    
    def 获取配置(self) -> dict:
        """获取管道配置"""
        配置 = {}
        for 变换 in self.变换列表:
            变换配置 = 变换.获取配置()
            变换类型 = 变换配置.pop('类型')
            变换配置['启用'] = True
            配置[变换类型] = 变换配置
        return 配置
    
    def 保存配置(self, 路径: str):
        """保存管道配置到文件"""
        配置 = self.获取配置()
        with open(路径, 'w', encoding='utf-8') as f:
            json.dump(配置, f, ensure_ascii=False, indent=2)
        日志.info(f"增强配置已保存: {路径}")
    
    def 加载配置文件(self, 路径: str) -> '增强管道':
        """从文件加载配置"""
        with open(路径, 'r', encoding='utf-8') as f:
            配置 = json.load(f)
        return self.从配置加载(配置)
    
    def __call__(self, 图像: np.ndarray) -> np.ndarray:
        """
        执行管道
        
        参数:
            图像: 输入图像
            
        返回:
            增强后的图像
        """
        结果 = 图像.copy()
        for 变换 in self.变换列表:
            结果 = 变换(结果)
        return 结果
    
    def __len__(self) -> int:
        return len(self.变换列表)


class 数据增强器:
    """训练数据增强器"""
    
    def __init__(self, 配置: dict = None, 随机种子: int = None):
        """
        初始化数据增强器
        
        参数:
            配置: 增强配置字典，None 则使用默认配置
            随机种子: 随机种子，用于可重复性
        """
        self.管道 = 增强管道()
        self.随机种子 = 随机种子
        
        if 配置:
            self.管道.从配置加载(配置)
        else:
            self._使用默认配置()
    
    def _使用默认配置(self):
        """使用默认增强配置"""
        默认配置 = {
            "亮度调整": {"启用": True, "概率": 0.5, "范围": [-0.2, 0.2]},
            "对比度调整": {"启用": True, "概率": 0.5, "范围": [0.8, 1.2]},
            "水平翻转": {"启用": True, "概率": 0.5},
            "高斯噪声": {"启用": True, "概率": 0.3, "标准差": 0.02},
            "颜色抖动": {"启用": True, "概率": 0.3, "色调范围": 0.1, "饱和度范围": 0.2},
        }
        self.管道.从配置加载(默认配置)
    
    def _设置随机种子(self, 种子: int = None):
        """设置随机种子"""
        if 种子 is not None:
            random.seed(种子)
            np.random.seed(种子)
    
    def 增强(self, 图像: np.ndarray, 种子: int = None) -> np.ndarray:
        """
        对单张图像应用增强
        
        参数:
            图像: 输入图像 (H, W, C)
            种子: 可选的随机种子
            
        返回:
            增强后的图像
        """
        if 图像 is None or 图像.size == 0:
            日志.warning("输入图像无效")
            return 图像
        
        self._设置随机种子(种子 or self.随机种子)
        return self.管道(图像)
    
    def 批量增强(self, 图像列表: List[np.ndarray]) -> List[np.ndarray]:
        """
        对批量图像应用增强
        
        参数:
            图像列表: 输入图像列表
            
        返回:
            增强后的图像列表
        """
        return [self.增强(图像) for 图像 in 图像列表]
    
    def 增强批次(self, 数据: List) -> List:
        """
        对训练数据批次应用增强（兼容训练流程）
        
        此方法用于与训练流程集成，支持处理包含 (图像, 标签) 元组的数据列表。
        
        参数:
            数据: 训练数据列表，每个元素为 (图像, 标签) 元组或单独的图像
            
        返回:
            增强后的数据列表，保持原有格式
            
        需求: 4.1, 4.2 - 与训练数据加载器集成，实时应用随机增强
        """
        增强后数据 = []
        for 样本 in 数据:
            if isinstance(样本, (tuple, list)) and len(样本) >= 2:
                # 处理 (图像, 标签) 格式的数据
                图像 = 样本[0]
                标签 = 样本[1]
                其他数据 = 样本[2:] if len(样本) > 2 else ()
                
                增强图像 = self.增强(图像)
                增强后数据.append((增强图像, 标签) + tuple(其他数据))
            else:
                # 处理单独的图像
                增强后数据.append(self.增强(样本))
        
        return 增强后数据
    
    def 预览(self, 图像: np.ndarray, 数量: int = 5) -> List[np.ndarray]:
        """
        生成多个增强预览
        
        参数:
            图像: 输入图像
            数量: 生成的预览数量
            
        返回:
            增强后的图像列表
        """
        预览列表 = [图像.copy()]  # 包含原图
        for i in range(数量):
            预览列表.append(self.增强(图像, 种子=i))
        return 预览列表
    
    def 保存预览(self, 图像: np.ndarray, 保存目录: str, 数量: int = 5):
        """
        保存增强预览图像
        
        参数:
            图像: 输入图像
            保存目录: 保存目录
            数量: 生成的预览数量
        """
        os.makedirs(保存目录, exist_ok=True)
        
        预览列表 = self.预览(图像, 数量)
        
        for i, 预览图像 in enumerate(预览列表):
            文件名 = f"preview_{i:02d}.png" if i > 0 else "original.png"
            路径 = os.path.join(保存目录, 文件名)
            cv2.imwrite(路径, 预览图像)
        
        日志.info(f"预览图像已保存到: {保存目录}")
    
    def 获取配置(self) -> dict:
        """获取当前配置"""
        return self.管道.获取配置()
    
    def 保存配置(self, 路径: str):
        """保存配置到文件"""
        self.管道.保存配置(路径)


# 游戏特定增强变换
class 光照模拟(变换基类):
    """模拟游戏中的光照变化"""
    
    def __init__(self, 强度范围: Tuple[float, float] = (0.7, 1.3), **kwargs):
        super().__init__(**kwargs)
        self.强度范围 = 强度范围
    
    def _应用变换(self, 图像: np.ndarray) -> np.ndarray:
        光照因子 = random.uniform(self.强度范围[0], self.强度范围[1])
        光照因子 = 1.0 + (光照因子 - 1.0) * self.强度
        
        图像浮点 = 图像.astype(np.float32) * 光照因子
        return np.clip(图像浮点, 0, 255).astype(np.uint8)


class UI遮挡模拟(变换基类):
    """模拟UI元素遮挡"""
    
    def __init__(self, 遮挡数量: int = 2, 最大尺寸: float = 0.1, **kwargs):
        """
        参数:
            遮挡数量: 最大遮挡块数量
            最大尺寸: 遮挡块最大尺寸（相对于图像）
        """
        super().__init__(**kwargs)
        self.遮挡数量 = 遮挡数量
        self.最大尺寸 = 最大尺寸
    
    def _应用变换(self, 图像: np.ndarray) -> np.ndarray:
        结果 = 图像.copy()
        高度, 宽度 = 图像.shape[:2]
        
        数量 = random.randint(1, self.遮挡数量)
        
        for _ in range(数量):
            # 随机遮挡块大小
            块宽 = int(random.uniform(0.02, self.最大尺寸) * 宽度)
            块高 = int(random.uniform(0.02, self.最大尺寸) * 高度)
            
            # 随机位置
            x = random.randint(0, 宽度 - 块宽)
            y = random.randint(0, 高度 - 块高)
            
            # 随机颜色（模拟UI元素）
            颜色 = [random.randint(0, 255) for _ in range(3)]
            
            结果[y:y+块高, x:x+块宽] = 颜色
        
        return 结果


class 透视变换(变换基类):
    """模拟轻微镜头移动的透视变换"""
    
    def __init__(self, 最大偏移: float = 0.05, **kwargs):
        """
        参数:
            最大偏移: 角点最大偏移比例（相对于图像尺寸）
        """
        super().__init__(**kwargs)
        self.最大偏移 = 最大偏移
    
    def _应用变换(self, 图像: np.ndarray) -> np.ndarray:
        高度, 宽度 = 图像.shape[:2]
        
        # 计算实际最大偏移量
        实际偏移 = self.最大偏移 * self.强度
        偏移x = int(宽度 * 实际偏移)
        偏移y = int(高度 * 实际偏移)
        
        # 原始四个角点
        原始点 = np.float32([
            [0, 0],           # 左上
            [宽度, 0],        # 右上
            [宽度, 高度],     # 右下
            [0, 高度]         # 左下
        ])
        
        # 随机偏移后的角点（模拟轻微镜头移动）
        目标点 = np.float32([
            [random.randint(0, 偏移x), random.randint(0, 偏移y)],
            [宽度 - random.randint(0, 偏移x), random.randint(0, 偏移y)],
            [宽度 - random.randint(0, 偏移x), 高度 - random.randint(0, 偏移y)],
            [random.randint(0, 偏移x), 高度 - random.randint(0, 偏移y)]
        ])
        
        # 计算透视变换矩阵
        变换矩阵 = cv2.getPerspectiveTransform(原始点, 目标点)
        
        # 应用透视变换
        return cv2.warpPerspective(图像, 变换矩阵, (宽度, 高度), borderMode=cv2.BORDER_REFLECT)
    
    def 获取配置(self) -> dict:
        配置 = super().获取配置()
        配置['最大偏移'] = self.最大偏移
        return 配置


# ============================================================================
# 语义保护机制
# ============================================================================

# 语义安全的变换强度限制
# 这些限制确保变换不会改变动作的语义含义
语义安全限制 = {
    '亮度调整': {
        '最大强度': 0.8,
        '安全范围': (-0.15, 0.15),
        '说明': '过大的亮度变化可能导致关键特征不可见'
    },
    '对比度调整': {
        '最大强度': 0.8,
        '安全范围': (0.85, 1.15),
        '说明': '过大的对比度变化可能导致细节丢失'
    },
    '水平翻转': {
        '最大强度': 1.0,
        '安全范围': None,
        '说明': '水平翻转通常是安全的，但可能改变方向性动作的含义'
    },
    '垂直翻转': {
        '最大强度': 0.0,  # 默认禁用
        '安全范围': None,
        '说明': '垂直翻转可能严重改变动作语义，默认禁用'
    },
    '高斯噪声': {
        '最大强度': 0.6,
        '安全范围': None,
        '最大标准差': 0.03,
        '说明': '过多噪声可能掩盖关键特征'
    },
    '颜色抖动': {
        '最大强度': 0.7,
        '安全色调范围': 0.08,
        '安全饱和度范围': 0.15,
        '说明': '过大的颜色变化可能影响基于颜色的识别'
    },
    '高斯模糊': {
        '最大强度': 0.5,
        '安全核大小范围': (3, 5),
        '说明': '过度模糊会丢失关键细节'
    },
    '旋转': {
        '最大强度': 0.7,
        '安全角度范围': (-8, 8),
        '说明': '过大的旋转可能改变动作方向的语义'
    },
    '缩放裁剪': {
        '最大强度': 0.7,
        '安全缩放范围': (0.92, 1.08),
        '说明': '过大的缩放可能丢失边缘的关键信息'
    },
    '光照模拟': {
        '最大强度': 0.8,
        '安全强度范围': (0.75, 1.25),
        '说明': '过大的光照变化可能导致特征不可见'
    },
    'UI遮挡模拟': {
        '最大强度': 0.5,
        '最大遮挡数量': 2,
        '最大尺寸': 0.08,
        '说明': '过多遮挡可能覆盖关键区域'
    },
    '透视变换': {
        '最大强度': 0.6,
        '安全最大偏移': 0.04,
        '说明': '过大的透视变换可能扭曲关键特征'
    }
}


def 检查语义安全(变换名称: str, 参数: dict) -> Tuple[bool, str, dict]:
    """
    检查变换参数是否在语义安全范围内
    
    参数:
        变换名称: 变换类型名称
        参数: 变换参数字典
        
    返回:
        (是否安全, 警告信息, 建议参数)
    """
    if 变换名称 not in 语义安全限制:
        return True, "", 参数
    
    限制 = 语义安全限制[变换名称]
    警告列表 = []
    建议参数 = 参数.copy()
    
    # 检查强度
    if '强度' in 参数:
        最大强度 = 限制.get('最大强度', 1.0)
        if 参数['强度'] > 最大强度:
            警告列表.append(f"强度 {参数['强度']} 超过安全限制 {最大强度}")
            建议参数['强度'] = 最大强度
    
    # 检查特定参数
    if 变换名称 == '亮度调整' and '范围' in 参数:
        安全范围 = 限制.get('安全范围', (-0.2, 0.2))
        if 参数['范围'][0] < 安全范围[0] or 参数['范围'][1] > 安全范围[1]:
            警告列表.append(f"亮度范围超出安全限制 {安全范围}")
            建议参数['范围'] = 安全范围
    
    if 变换名称 == '对比度调整' and '范围' in 参数:
        安全范围 = 限制.get('安全范围', (0.8, 1.2))
        if 参数['范围'][0] < 安全范围[0] or 参数['范围'][1] > 安全范围[1]:
            警告列表.append(f"对比度范围超出安全限制 {安全范围}")
            建议参数['范围'] = 安全范围
    
    if 变换名称 == '高斯噪声' and '标准差' in 参数:
        最大标准差 = 限制.get('最大标准差', 0.03)
        if 参数['标准差'] > 最大标准差:
            警告列表.append(f"噪声标准差超出安全限制 {最大标准差}")
            建议参数['标准差'] = 最大标准差
    
    if 变换名称 == '旋转' and '角度范围' in 参数:
        安全范围 = 限制.get('安全角度范围', (-10, 10))
        if 参数['角度范围'][0] < 安全范围[0] or 参数['角度范围'][1] > 安全范围[1]:
            警告列表.append(f"旋转角度范围超出安全限制 {安全范围}")
            建议参数['角度范围'] = 安全范围
    
    if 变换名称 == '透视变换' and '最大偏移' in 参数:
        安全偏移 = 限制.get('安全最大偏移', 0.05)
        if 参数['最大偏移'] > 安全偏移:
            警告列表.append(f"透视偏移超出安全限制 {安全偏移}")
            建议参数['最大偏移'] = 安全偏移
    
    是否安全 = len(警告列表) == 0
    警告信息 = "; ".join(警告列表) if 警告列表 else ""
    
    return 是否安全, 警告信息, 建议参数


class 语义安全变换(变换基类):
    """带语义保护的变换包装器"""
    
    def __init__(self, 内部变换: 变换基类, 强制安全: bool = True):
        """
        参数:
            内部变换: 被包装的变换
            强制安全: 是否强制应用安全限制
        """
        super().__init__(概率=内部变换.概率, 强度=内部变换.强度)
        self.内部变换 = 内部变换
        self.强制安全 = 强制安全
        self.名称 = f"安全_{内部变换.名称}"
        
        # 应用安全限制
        if 强制安全:
            self._应用安全限制()
    
    def _应用安全限制(self):
        """应用语义安全限制"""
        变换名称 = self.内部变换.__class__.__name__
        
        if 变换名称 not in 语义安全限制:
            return
        
        限制 = 语义安全限制[变换名称]
        
        # 限制强度
        最大强度 = 限制.get('最大强度', 1.0)
        if self.内部变换.强度 > 最大强度:
            日志.info(f"{变换名称}: 强度从 {self.内部变换.强度} 调整为 {最大强度}")
            self.内部变换.强度 = 最大强度
            self.强度 = 最大强度
    
    def _应用变换(self, 图像: np.ndarray) -> np.ndarray:
        return self.内部变换._应用变换(图像)
    
    def 获取配置(self) -> dict:
        配置 = self.内部变换.获取配置()
        配置['语义安全'] = True
        return 配置


class 语义安全增强管道(增强管道):
    """带语义保护的增强管道"""
    
    def __init__(self, 强制安全: bool = True):
        """
        参数:
            强制安全: 是否强制应用安全限制
        """
        super().__init__()
        self.强制安全 = 强制安全
        self._禁用变换列表 = ['垂直翻转']  # 默认禁用可能改变语义的变换
    
    def 添加变换(self, 变换: 变换基类) -> '语义安全增强管道':
        """添加变换操作（带安全检查）"""
        变换名称 = 变换.__class__.__name__
        
        # 检查是否在禁用列表中
        if 变换名称 in self._禁用变换列表:
            日志.warning(f"{变换名称} 已被禁用以保护语义安全")
            return self
        
        # 包装为安全变换
        if self.强制安全:
            安全变换 = 语义安全变换(变换, 强制安全=True)
            self.变换列表.append(安全变换)
        else:
            self.变换列表.append(变换)
        
        return self
    
    def 从配置加载(self, 配置: dict) -> '语义安全增强管道':
        """从配置字典加载管道（带安全检查）"""
        self.清空()
        
        for 变换名称, 变换配置 in 配置.items():
            if not 变换配置.get('启用', True):
                continue
            
            # 检查是否在禁用列表中
            if 变换名称 in self._禁用变换列表:
                日志.warning(f"{变换名称} 已被禁用以保护语义安全")
                continue
            
            if 变换名称 not in 变换类型映射:
                日志.warning(f"未知的变换类型: {变换名称}")
                continue
            
            # 提取参数
            参数 = {k: v for k, v in 变换配置.items() if k != '启用'}
            
            # 检查语义安全
            是否安全, 警告信息, 建议参数 = 检查语义安全(变换名称, 参数)
            if not 是否安全:
                日志.warning(f"{变换名称} 参数不安全: {警告信息}")
                if self.强制安全:
                    参数 = 建议参数
                    日志.info(f"{变换名称} 已自动调整为安全参数")
            
            try:
                变换实例 = 变换类型映射[变换名称](**参数)
                self.添加变换(变换实例)
            except Exception as e:
                日志.warning(f"创建变换 {变换名称} 失败: {e}")
        
        return self
    
    def 设置禁用变换(self, 变换列表: List[str]):
        """设置禁用的变换类型"""
        self._禁用变换列表 = 变换列表
    
    def 添加禁用变换(self, 变换名称: str):
        """添加禁用的变换类型"""
        if 变换名称 not in self._禁用变换列表:
            self._禁用变换列表.append(变换名称)
    
    def 移除禁用变换(self, 变换名称: str):
        """移除禁用的变换类型"""
        if 变换名称 in self._禁用变换列表:
            self._禁用变换列表.remove(变换名称)


def 创建语义安全增强器(配置: dict = None, 随机种子: int = None) -> 数据增强器:
    """
    创建带语义保护的数据增强器
    
    参数:
        配置: 增强配置字典
        随机种子: 随机种子
        
    返回:
        配置了语义安全管道的数据增强器
    """
    增强器 = 数据增强器(配置=None, 随机种子=随机种子)
    增强器.管道 = 语义安全增强管道(强制安全=True)
    
    if 配置:
        增强器.管道.从配置加载(配置)
    else:
        # 使用语义安全的默认配置
        安全默认配置 = {
            "亮度调整": {"启用": True, "概率": 0.5, "范围": [-0.15, 0.15], "强度": 0.8},
            "对比度调整": {"启用": True, "概率": 0.5, "范围": [0.85, 1.15], "强度": 0.8},
            "水平翻转": {"启用": True, "概率": 0.5},
            "高斯噪声": {"启用": True, "概率": 0.3, "标准差": 0.02, "强度": 0.6},
            "颜色抖动": {"启用": True, "概率": 0.3, "色调范围": 0.08, "饱和度范围": 0.15, "强度": 0.7},
            "旋转": {"启用": True, "概率": 0.3, "角度范围": [-8, 8], "强度": 0.7},
            "透视变换": {"启用": True, "概率": 0.2, "最大偏移": 0.04, "强度": 0.6},
        }
        增强器.管道.从配置加载(安全默认配置)
    
    return 增强器


# 更新变换类型映射
变换类型映射.update({
    '光照模拟': 光照模拟,
    'UI遮挡模拟': UI遮挡模拟,
    '透视变换': 透视变换,
})
