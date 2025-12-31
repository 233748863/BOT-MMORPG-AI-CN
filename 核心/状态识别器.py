"""
游戏状态识别器模块
实现基于UI检测和实体分析的游戏状态识别功能
"""

import logging
import os
from collections import deque
from typing import List, Optional, Callable, Tuple

import cv2
import numpy as np

from 核心.数据类型 import 游戏状态, 检测结果, 状态识别结果, 实体类型
from 配置.增强设置 import 状态识别配置, UI模板路径, 状态判定阈值

# 配置日志
logger = logging.getLogger(__name__)


class 状态识别器:
    """
    游戏状态识别器
    
    通过分析UI元素和检测到的实体来判断当前游戏状态
    """
    
    def __init__(
        self,
        历史长度: Optional[int] = None,
        置信度累积系数: Optional[float] = None
    ):
        """
        初始化状态识别器
        
        Args:
            历史长度: 状态历史记录的最大长度
            置信度累积系数: 连续相同状态时置信度的累积系数
        """
        self.历史长度 = 历史长度 if 历史长度 is not None else 状态识别配置["历史长度"]
        self.置信度累积系数 = 置信度累积系数 if 置信度累积系数 is not None else 状态识别配置["置信度累积系数"]
        
        # 状态历史记录
        self.状态历史: deque = deque(maxlen=self.历史长度)
        
        # 状态变更回调函数列表
        self._状态变更回调: List[Callable[[游戏状态, 游戏状态], None]] = []
        
        # 上一次识别的状态
        self._上次状态: Optional[游戏状态] = None
        
        # UI模板缓存
        self._UI模板缓存: dict = {}
        
        # 加载UI模板
        self._加载UI模板()
    
    def _加载UI模板(self):
        """加载UI元素模板图像"""
        for 名称, 路径 in UI模板路径.items():
            if os.path.exists(路径):
                模板 = cv2.imread(路径, cv2.IMREAD_GRAYSCALE)
                if 模板 is not None:
                    self._UI模板缓存[名称] = 模板
                    logger.info(f"UI模板加载成功: {名称}")
                else:
                    logger.warning(f"UI模板加载失败: {路径}")
            else:
                logger.debug(f"UI模板文件不存在: {路径}")
    
    def 识别状态(
        self, 
        图像: np.ndarray, 
        检测结果列表: List[检测结果]
    ) -> 状态识别结果:
        """
        识别当前游戏状态
        
        Args:
            图像: 当前游戏画面 (BGR格式)
            检测结果列表: YOLO检测器返回的检测结果
            
        Returns:
            状态识别结果
        """
        # 检测UI元素
        检测到的UI = self._检测UI元素(图像)
        
        # 统计附近实体
        附近实体数量 = len(检测结果列表)
        附近敌人 = [r for r in 检测结果列表 if r.类型 == 实体类型.怪物]
        附近物品 = [r for r in 检测结果列表 if r.类型 == 实体类型.物品]
        
        # 判定状态（按优先级）
        状态, 基础置信度 = self._判定状态(检测到的UI, 附近敌人, 附近物品, 检测结果列表)
        
        # 计算累积置信度
        最终置信度 = self._计算累积置信度(状态, 基础置信度)
        
        # 创建结果
        结果 = 状态识别结果(
            状态=状态,
            置信度=最终置信度,
            检测到的UI元素=检测到的UI,
            附近实体数量=附近实体数量
        )
        
        # 记录到历史
        self.状态历史.append(结果)
        
        # 检查状态变更并触发回调
        if self._上次状态 is not None and self._上次状态 != 状态:
            self._触发状态变更回调(self._上次状态, 状态)
        
        self._上次状态 = 状态
        
        return 结果
    
    def _判定状态(
        self,
        检测到的UI: List[str],
        附近敌人: List[检测结果],
        附近物品: List[检测结果],
        所有检测结果: List[检测结果]
    ) -> Tuple[游戏状态, float]:
        """
        根据检测信息判定游戏状态
        
        优先级顺序：
        1. 加载界面 (最高)
        2. 死亡界面
        3. 菜单界面
        4. 对话界面
        5. 战斗状态 (有近距离敌人)
        6. 拾取状态 (有近距离物品)
        7. 采集状态
        8. 移动状态
        9. 空闲状态 (最低)
        
        Returns:
            (游戏状态, 基础置信度)
        """
        # 1. 检查加载界面
        if "加载界面" in 检测到的UI:
            return 游戏状态.加载, 0.95
        
        # 2. 检查死亡界面
        if "死亡界面" in 检测到的UI:
            return 游戏状态.死亡, 0.95
        
        # 3. 检查菜单界面
        if "菜单" in 检测到的UI:
            return 游戏状态.菜单, 0.9
        
        # 4. 检查对话界面
        if "对话框" in 检测到的UI:
            return 游戏状态.对话, 0.9
        
        # 5. 检查战斗状态（有近距离敌人）
        战斗距离阈值 = 状态判定阈值["战斗_敌人距离"]
        近距离敌人 = [e for e in 附近敌人 if e.距离 < 战斗距离阈值]
        if len(近距离敌人) >= 状态判定阈值["战斗_敌人数量"]:
            置信度 = min(0.9, 0.6 + len(近距离敌人) * 0.1)
            return 游戏状态.战斗, 置信度
        
        # 6. 检查拾取状态（有近距离物品）
        拾取距离阈值 = 状态判定阈值["拾取_物品距离"]
        近距离物品 = [i for i in 附近物品 if i.距离 < 拾取距离阈值]
        if near_items := 近距离物品:
            置信度 = min(0.8, 0.5 + len(near_items) * 0.1)
            return 游戏状态.拾取, 置信度
        
        # 7. 如果有敌人但距离较远，可能是移动状态
        if 附近敌人:
            return 游戏状态.移动, 0.6
        
        # 8. 如果有其他实体，可能是移动或空闲
        if 所有检测结果:
            return 游戏状态.移动, 0.5
        
        # 9. 默认空闲状态
        return 游戏状态.空闲, 0.4
    
    def _检测UI元素(self, 图像: np.ndarray) -> List[str]:
        """
        检测屏幕上的UI元素
        
        使用模板匹配检测预定义的UI元素
        
        Args:
            图像: 当前游戏画面 (BGR格式)
            
        Returns:
            检测到的UI元素名称列表
        """
        if not 状态识别配置.get("UI检测启用", True):
            return []
        
        if 图像 is None or 图像.size == 0:
            return []
        
        检测到的UI = []
        
        # 转换为灰度图
        try:
            灰度图 = cv2.cvtColor(图像, cv2.COLOR_BGR2GRAY)
        except Exception as e:
            logger.warning(f"图像转换失败: {e}")
            return []
        
        # 对每个模板进行匹配
        for 名称, 模板 in self._UI模板缓存.items():
            try:
                匹配结果 = cv2.matchTemplate(灰度图, 模板, cv2.TM_CCOEFF_NORMED)
                _, 最大值, _, _ = cv2.minMaxLoc(匹配结果)
                
                # 如果匹配度超过阈值，认为检测到该UI元素
                if 最大值 > 0.7:
                    检测到的UI.append(名称)
                    logger.debug(f"检测到UI元素: {名称}, 匹配度: {最大值:.2f}")
            except Exception as e:
                logger.warning(f"UI模板匹配失败 ({名称}): {e}")
        
        return 检测到的UI
    
    def _计算累积置信度(self, 当前状态: 游戏状态, 基础置信度: float) -> float:
        """
        根据历史状态计算累积置信度
        
        如果连续多帧状态相同，置信度会累积增加
        
        Args:
            当前状态: 当前判定的状态
            基础置信度: 基础置信度值
            
        Returns:
            累积后的置信度（最大1.0）
        """
        if not self.状态历史:
            return 基础置信度
        
        # 统计连续相同状态的次数
        连续次数 = 0
        for 历史结果 in reversed(self.状态历史):
            if 历史结果.状态 == 当前状态:
                连续次数 += 1
            else:
                break
        
        # 累积置信度
        累积值 = 基础置信度 + 连续次数 * self.置信度累积系数
        
        return min(1.0, 累积值)
    
    def 注册状态变更回调(self, 回调函数: Callable[[游戏状态, 游戏状态], None]):
        """
        注册状态变更时的回调函数
        
        Args:
            回调函数: 回调函数，接收 (旧状态, 新状态) 两个参数
        """
        if 回调函数 not in self._状态变更回调:
            self._状态变更回调.append(回调函数)
            logger.debug(f"注册状态变更回调: {回调函数.__name__}")
    
    def 取消状态变更回调(self, 回调函数: Callable[[游戏状态, 游戏状态], None]):
        """
        取消状态变更回调
        
        Args:
            回调函数: 要取消的回调函数
        """
        if 回调函数 in self._状态变更回调:
            self._状态变更回调.remove(回调函数)
            logger.debug(f"取消状态变更回调: {回调函数.__name__}")
    
    def _触发状态变更回调(self, 旧状态: 游戏状态, 新状态: 游戏状态):
        """
        触发所有状态变更回调
        
        Args:
            旧状态: 变更前的状态
            新状态: 变更后的状态
        """
        logger.info(f"状态变更: {旧状态.value} -> {新状态.value}")
        
        for 回调 in self._状态变更回调:
            try:
                回调(旧状态, 新状态)
            except Exception as e:
                logger.error(f"状态变更回调执行失败: {e}")
    
    def 获取状态历史(self, 数量: int = 5) -> List[状态识别结果]:
        """
        获取最近N次状态记录
        
        Args:
            数量: 要获取的记录数量
            
        Returns:
            状态识别结果列表（从旧到新）
        """
        历史列表 = list(self.状态历史)
        return 历史列表[-数量:] if len(历史列表) > 数量 else 历史列表
    
    def 获取当前状态(self) -> Optional[游戏状态]:
        """
        获取当前状态（最近一次识别的状态）
        
        Returns:
            当前游戏状态，如果没有历史记录则返回None
        """
        if self.状态历史:
            return self.状态历史[-1].状态
        return None
    
    def 清空历史(self):
        """清空状态历史记录"""
        self.状态历史.clear()
        self._上次状态 = None
        logger.debug("状态历史已清空")
    
    def 是否处于状态(self, 状态: 游戏状态) -> bool:
        """
        检查当前是否处于指定状态
        
        Args:
            状态: 要检查的状态
            
        Returns:
            是否处于该状态
        """
        当前 = self.获取当前状态()
        return 当前 == 状态 if 当前 is not None else False
    
    def 获取连续状态次数(self, 状态: 游戏状态) -> int:
        """
        获取指定状态连续出现的次数
        
        Args:
            状态: 要统计的状态
            
        Returns:
            连续出现的次数
        """
        连续次数 = 0
        for 历史结果 in reversed(self.状态历史):
            if 历史结果.状态 == 状态:
                连续次数 += 1
            else:
                break
        return 连续次数
