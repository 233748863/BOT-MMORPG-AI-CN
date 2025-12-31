"""
YOLO目标检测器模块
实现基于YOLO的游戏实体检测功能
"""

import logging
import math
from typing import List, Optional, Tuple

import numpy as np

from 核心.数据类型 import 实体类型, 方向, 检测结果
from 配置.增强设置 import YOLO配置, 实体类型映射, 实体类型枚举

# 配置日志
logger = logging.getLogger(__name__)


class YOLO检测器:
    """
    YOLO目标检测器
    
    用于检测游戏画面中的实体（怪物、NPC、玩家、物品、技能特效等）
    """
    
    def __init__(
        self, 
        模型路径: Optional[str] = None, 
        置信度阈值: Optional[float] = None,
        NMS阈值: Optional[float] = None,
        输入尺寸: Optional[Tuple[int, int]] = None
    ):
        """
        初始化YOLO检测器
        
        Args:
            模型路径: YOLO模型文件路径，默认使用配置文件中的路径
            置信度阈值: 检测置信度阈值，低于此值的结果将被过滤
            NMS阈值: 非极大值抑制阈值
            输入尺寸: 模型输入图像尺寸
        """
        self.模型路径 = 模型路径 or YOLO配置["模型路径"]
        self.置信度阈值 = 置信度阈值 if 置信度阈值 is not None else YOLO配置["置信度阈值"]
        self.NMS阈值 = NMS阈值 if NMS阈值 is not None else YOLO配置["NMS阈值"]
        self.输入尺寸 = 输入尺寸 or YOLO配置["输入尺寸"]
        
        self._模型 = None
        self._已加载 = False
        self._上次检测结果: List[检测结果] = []
        
        # 尝试加载模型
        self._加载模型()
    
    def _加载模型(self) -> bool:
        """
        加载YOLO模型
        
        Returns:
            是否加载成功
        """
        try:
            # 尝试导入ultralytics库
            from ultralytics import YOLO
            self._模型 = YOLO(self.模型路径)
            self._已加载 = True
            logger.info(f"YOLO模型加载成功: {self.模型路径}")
            return True
        except ImportError:
            logger.warning("未安装ultralytics库，YOLO检测器将返回空结果")
            self._已加载 = False
            return False
        except Exception as e:
            logger.warning(f"YOLO模型加载失败: {e}，检测器将返回空结果")
            self._已加载 = False
            return False
    
    def 是否已加载(self) -> bool:
        """
        检查模型是否已加载
        
        Returns:
            模型是否已加载
        """
        return self._已加载
    
    def 检测(self, 图像: np.ndarray) -> List[检测结果]:
        """
        执行目标检测
        
        Args:
            图像: 输入图像 (BGR格式的numpy数组)
            
        Returns:
            检测结果列表，按置信度降序排列
        """
        # 如果模型未加载，返回空列表
        if not self._已加载:
            logger.warning("模型未加载，返回空检测结果")
            return []
        
        # 验证图像
        if 图像 is None or 图像.size == 0:
            logger.warning("输入图像无效，返回空检测结果")
            return []
        
        try:
            # 获取屏幕尺寸
            屏幕高度, 屏幕宽度 = 图像.shape[:2]
            屏幕尺寸 = (屏幕宽度, 屏幕高度)
            
            # 执行检测
            结果 = self._模型(图像, conf=self.置信度阈值, iou=self.NMS阈值, verbose=False)
            
            # 解析检测结果
            检测列表 = self._解析检测结果(结果, 屏幕尺寸)
            
            # 后处理：过滤和排序
            检测列表 = self.后处理(检测列表, self.置信度阈值)
            
            # 缓存结果
            self._上次检测结果 = 检测列表
            
            return 检测列表
            
        except Exception as e:
            logger.error(f"检测过程出错: {e}")
            return self._上次检测结果  # 返回上一帧结果
    
    def _解析检测结果(
        self, 
        原始结果, 
        屏幕尺寸: Tuple[int, int]
    ) -> List[检测结果]:
        """
        解析YOLO原始检测结果
        
        Args:
            原始结果: YOLO模型返回的原始结果
            屏幕尺寸: 屏幕尺寸 (宽度, 高度)
            
        Returns:
            解析后的检测结果列表
        """
        检测列表 = []
        
        for result in 原始结果:
            boxes = result.boxes
            if boxes is None:
                continue
                
            for i in range(len(boxes)):
                # 获取边界框坐标 (x1, y1, x2, y2)
                box = boxes.xyxy[i].cpu().numpy()
                x1, y1, x2, y2 = map(int, box)
                
                # 计算边界框 (x, y, width, height)
                宽度 = x2 - x1
                高度 = y2 - y1
                边界框 = (x1, y1, 宽度, 高度)
                
                # 计算中心点
                中心x = x1 + 宽度 // 2
                中心y = y1 + 高度 // 2
                中心点 = (中心x, 中心y)
                
                # 获取置信度
                置信度 = float(boxes.conf[i].cpu().numpy())
                
                # 获取类别
                类别id = int(boxes.cls[i].cpu().numpy())
                实体 = self._映射实体类型(类别id)
                
                # 计算方向和距离
                方向值 = self.计算方向(中心点, 屏幕尺寸)
                距离值 = self._计算距离(中心点, 屏幕尺寸)
                
                检测列表.append(检测结果(
                    类型=实体,
                    置信度=置信度,
                    边界框=边界框,
                    中心点=中心点,
                    方向=方向值,
                    距离=距离值
                ))
        
        return 检测列表
    
    def _映射实体类型(self, 类别id: int) -> 实体类型:
        """
        将YOLO类别ID映射为实体类型
        
        Args:
            类别id: YOLO检测的类别ID
            
        Returns:
            对应的实体类型
        """
        映射结果 = 实体类型映射.get(类别id)
        if 映射结果 is None:
            return 实体类型.未知
        
        # 将配置中的枚举转换为数据类型中的枚举
        类型映射 = {
            实体类型枚举.怪物: 实体类型.怪物,
            实体类型枚举.NPC: 实体类型.NPC,
            实体类型枚举.玩家: 实体类型.玩家,
            实体类型枚举.物品: 实体类型.物品,
            实体类型枚举.技能特效: 实体类型.技能特效,
            实体类型枚举.未知: 实体类型.未知,
        }
        return 类型映射.get(映射结果, 实体类型.未知)
    
    def 计算方向(self, 中心点: Tuple[int, int], 屏幕尺寸: Tuple[int, int]) -> 方向:
        """
        计算实体相对于屏幕中心的方向
        
        Args:
            中心点: 实体中心点坐标 (x, y)
            屏幕尺寸: 屏幕尺寸 (宽度, 高度)
            
        Returns:
            相对于屏幕中心的方向
        """
        屏幕宽度, 屏幕高度 = 屏幕尺寸
        屏幕中心x = 屏幕宽度 // 2
        屏幕中心y = 屏幕高度 // 2
        
        实体x, 实体y = 中心点
        
        # 计算相对位置
        dx = 实体x - 屏幕中心x
        dy = 实体y - 屏幕中心y
        
        # 定义中心区域阈值（屏幕尺寸的10%）
        中心阈值x = 屏幕宽度 * 0.1
        中心阈值y = 屏幕高度 * 0.1
        
        # 判断是否在中心区域
        在中心x = abs(dx) < 中心阈值x
        在中心y = abs(dy) < 中心阈值y
        
        if 在中心x and 在中心y:
            return 方向.中心
        
        # 判断水平方向
        if 在中心x:
            水平 = None
        elif dx < 0:
            水平 = "左"
        else:
            水平 = "右"
        
        # 判断垂直方向
        if 在中心y:
            垂直 = None
        elif dy < 0:
            垂直 = "上"
        else:
            垂直 = "下"
        
        # 组合方向
        if 水平 is None and 垂直 == "上":
            return 方向.上
        elif 水平 is None and 垂直 == "下":
            return 方向.下
        elif 垂直 is None and 水平 == "左":
            return 方向.左
        elif 垂直 is None and 水平 == "右":
            return 方向.右
        elif 水平 == "左" and 垂直 == "上":
            return 方向.左上
        elif 水平 == "右" and 垂直 == "上":
            return 方向.右上
        elif 水平 == "左" and 垂直 == "下":
            return 方向.左下
        elif 水平 == "右" and 垂直 == "下":
            return 方向.右下
        
        return 方向.中心
    
    def _计算距离(self, 中心点: Tuple[int, int], 屏幕尺寸: Tuple[int, int]) -> float:
        """
        计算实体中心点到屏幕中心的距离
        
        Args:
            中心点: 实体中心点坐标 (x, y)
            屏幕尺寸: 屏幕尺寸 (宽度, 高度)
            
        Returns:
            到屏幕中心的欧几里得距离
        """
        屏幕宽度, 屏幕高度 = 屏幕尺寸
        屏幕中心x = 屏幕宽度 // 2
        屏幕中心y = 屏幕高度 // 2
        
        实体x, 实体y = 中心点
        
        dx = 实体x - 屏幕中心x
        dy = 实体y - 屏幕中心y
        
        return math.sqrt(dx * dx + dy * dy)
    
    @staticmethod
    def 后处理(检测列表: List[检测结果], 置信度阈值: float) -> List[检测结果]:
        """
        对检测结果进行后处理：过滤低置信度结果并按置信度降序排序
        
        Args:
            检测列表: 原始检测结果列表
            置信度阈值: 置信度阈值，低于此值的结果将被过滤
            
        Returns:
            处理后的检测结果列表，按置信度降序排列
        """
        # 过滤低置信度结果
        过滤后列表 = [r for r in 检测列表 if r.置信度 >= 置信度阈值]
        
        # 按置信度降序排序
        排序后列表 = sorted(过滤后列表, key=lambda x: x.置信度, reverse=True)
        
        return 排序后列表
    
    def 获取上次检测结果(self) -> List[检测结果]:
        """
        获取上一次检测的结果（用于检测超时时的降级）
        
        Returns:
            上一次的检测结果列表
        """
        return self._上次检测结果.copy()
    
    def 按类型过滤(self, 检测列表: List[检测结果], 类型: 实体类型) -> List[检测结果]:
        """
        按实体类型过滤检测结果
        
        Args:
            检测列表: 检测结果列表
            类型: 要过滤的实体类型
            
        Returns:
            指定类型的检测结果列表
        """
        return [r for r in 检测列表 if r.类型 == 类型]
    
    def 获取最近实体(
        self, 
        检测列表: List[检测结果], 
        类型: Optional[实体类型] = None
    ) -> Optional[检测结果]:
        """
        获取距离屏幕中心最近的实体
        
        Args:
            检测列表: 检测结果列表
            类型: 可选的实体类型过滤
            
        Returns:
            最近的实体，如果没有则返回None
        """
        if not 检测列表:
            return None
        
        候选列表 = 检测列表
        if 类型 is not None:
            候选列表 = self.按类型过滤(检测列表, 类型)
        
        if not 候选列表:
            return None
        
        return min(候选列表, key=lambda x: x.距离)
