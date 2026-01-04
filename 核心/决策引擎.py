"""
智能决策引擎模块
结合规则引擎和模型预测，根据游戏状态做出智能决策

集成自动调参模块，支持实时参数优化。
集成ONNX推理、模型管理、状态检测等新功能模块。
需求: 10.3 - 与决策引擎集成，实时应用参数调整
"""

import time
import logging
from collections import deque
from typing import List, Dict, Optional, Tuple, Callable

import numpy as np

from 核心.数据类型 import (
    游戏状态, 决策策略, 检测结果, 决策上下文, 决策结果, 决策规则, 决策日志
)
from 配置.增强设置 import (
    决策引擎配置, 状态动作权重, 动作冷却时间, 紧急规则配置, 游戏状态枚举,
    状态检测配置
)
from 配置.设置 import 动作定义, 总动作数

# 尝试导入自动调参模块
try:
    from 核心.自动调参 import AutoTuner, PerformanceMetric, AggressivenessLevel
    自动调参可用 = True
except ImportError:
    自动调参可用 = False

# 尝试导入ONNX推理模块
try:
    from 核心.ONNX推理 import 统一推理引擎
    ONNX推理可用 = True
except ImportError:
    ONNX推理可用 = False

# 尝试导入模型管理模块
try:
    from 核心.模型管理 import 模型管理器, 自动切换器, 快捷键处理器
    模型管理可用 = True
except ImportError:
    模型管理可用 = False

# 尝试导入状态检测模块
try:
    from 核心.状态检测 import 状态检测器
    状态检测可用 = True
except ImportError:
    状态检测可用 = False

# 配置日志
logger = logging.getLogger(__name__)


class 决策引擎:
    """
    智能决策引擎
    
    功能:
    - 规则引擎: 支持规则添加、优先级排序、条件匹配
    - 状态-动作权重: 根据游戏状态获取动作权重
    - 动作冷却: 避免重复执行相同动作
    - 决策日志: 记录决策过程
    - 冲突解决: 处理规则和模型预测的冲突
    """
    
    def __init__(self, 策略: 决策策略 = None, 启用自动调参: bool = False,
                 启用ONNX推理: bool = True, 启用状态检测: bool = True):
        """
        初始化决策引擎
        
        Args:
            策略: 决策策略，默认从配置读取
            启用自动调参: 是否启用自动调参功能
            启用ONNX推理: 是否启用ONNX推理加速
            启用状态检测: 是否启用血量/蓝量状态检测
        """
        # 决策策略
        if 策略 is None:
            配置策略 = 决策引擎配置.get("策略", 决策策略.混合加权)
            if isinstance(配置策略, 决策策略):
                self.策略 = 配置策略
            else:
                self.策略 = 决策策略.混合加权
        else:
            self.策略 = 策略
        
        # 规则列表 (按优先级排序)
        self.规则列表: List[决策规则] = []
        
        # 动作冷却记录 {动作索引: 上次执行时间}
        self.动作冷却: Dict[int, float] = {}
        
        # 决策日志
        日志长度 = 决策引擎配置.get("日志长度", 100)
        self.决策日志: deque = deque(maxlen=日志长度)
        
        # 配置参数
        self.规则权重 = 决策引擎配置.get("规则权重", 0.6)
        self.模型权重 = 决策引擎配置.get("模型权重", 0.4)
        self.启用日志 = 决策引擎配置.get("启用日志", True)
        
        # 自动调参模块集成
        self._auto_tuner: Optional['AutoTuner'] = None
        self._启用自动调参 = 启用自动调参 and 自动调参可用
        self._性能统计 = {
            "总决策数": 0,
            "成功执行数": 0,
            "卡住次数": 0,
            "上次调参时间": 0.0
        }
        self._调参间隔 = 300.0  # 5分钟调参一次
        
        if self._启用自动调参:
            self._初始化自动调参()
        
        # ONNX推理引擎集成
        self._推理引擎: Optional['统一推理引擎'] = None
        self._启用ONNX推理 = 启用ONNX推理 and ONNX推理可用
        if self._启用ONNX推理:
            self._初始化推理引擎()
        
        # 模型管理器集成
        self._模型管理器: Optional['模型管理器'] = None
        # 自动切换器集成 - 需求: 3.2 - 当游戏状态匹配规则时，切换到指定模型
        self._自动切换器: Optional['自动切换器'] = None
        # 快捷键处理器集成 - 需求: 4.1 - 支持模型切换的快捷键
        self._快捷键处理器: Optional['快捷键处理器'] = None
        if 模型管理可用:
            self._初始化模型管理器()
        
        # 状态检测器集成
        self._状态检测器: Optional['状态检测器'] = None
        self._启用状态检测 = 启用状态检测 and 状态检测可用
        if self._启用状态检测:
            self._初始化状态检测器()
        
        logger.info(f"决策引擎初始化完成，策略: {self.策略.value}, 自动调参: {self._启用自动调参}, "
                   f"ONNX推理: {self._启用ONNX推理}, 状态检测: {self._启用状态检测}")
    
    def 添加规则(self, 规则: 决策规则) -> None:
        """
        添加决策规则
        
        Args:
            规则: 要添加的决策规则
        """
        self.规则列表.append(规则)
        # 按优先级降序排序
        self.规则列表.sort(key=lambda r: r.优先级, reverse=True)
        logger.debug(f"添加规则: {规则.名称}, 优先级: {规则.优先级}")
    
    def 移除规则(self, 规则名称: str) -> bool:
        """
        移除指定名称的规则
        
        Args:
            规则名称: 要移除的规则名称
            
        Returns:
            是否成功移除
        """
        原长度 = len(self.规则列表)
        self.规则列表 = [r for r in self.规则列表 if r.名称 != 规则名称]
        已移除 = len(self.规则列表) < 原长度
        if 已移除:
            logger.debug(f"移除规则: {规则名称}")
        return 已移除
    
    def 清空规则(self) -> None:
        """清空所有规则"""
        self.规则列表.clear()
        logger.debug("已清空所有规则")
    
    def 决策(self, 上下文: 决策上下文) -> 决策结果:
        """
        执行决策，返回最终动作
        
        Args:
            上下文: 决策上下文信息
            
        Returns:
            决策结果
        """
        候选动作: List[Tuple[int, float]] = []
        
        # 根据策略执行决策
        if self.策略 == 决策策略.规则优先:
            结果 = self._规则优先决策(上下文, 候选动作)
        elif self.策略 == 决策策略.模型优先:
            结果 = self._模型优先决策(上下文, 候选动作)
        else:  # 混合加权
            结果 = self._混合加权决策(上下文, 候选动作)
        
        # 记录决策日志
        if self.启用日志:
            日志 = 决策日志(
                时间戳=time.time(),
                上下文=上下文,
                候选动作=候选动作,
                最终决策=结果
            )
            self.决策日志.append(日志)
        
        return 结果
    
    def _规则优先决策(self, 上下文: 决策上下文, 
                     候选动作: List[Tuple[int, float]]) -> 决策结果:
        """
        规则优先策略: 先尝试规则，规则不匹配时使用模型
        """
        # 尝试应用规则
        规则结果 = self._应用规则(上下文)
        if 规则结果 is not None:
            候选动作.append((规则结果.动作索引, 规则结果.置信度))
            return 规则结果
        
        # 规则不匹配，使用模型
        return self._应用模型(上下文, 候选动作)
    
    def _模型优先决策(self, 上下文: 决策上下文,
                     候选动作: List[Tuple[int, float]]) -> 决策结果:
        """
        模型优先策略: 先使用模型，紧急规则可覆盖
        """
        # 检查紧急规则
        紧急结果 = self._检查紧急规则(上下文)
        if 紧急结果 is not None:
            候选动作.append((紧急结果.动作索引, 紧急结果.置信度))
            return 紧急结果
        
        # 使用模型预测
        return self._应用模型(上下文, 候选动作)
    
    def _混合加权决策(self, 上下文: 决策上下文,
                     候选动作: List[Tuple[int, float]]) -> 决策结果:
        """
        混合加权策略: 结合规则和模型的结果
        """
        # 检查紧急规则 (紧急规则始终优先)
        紧急结果 = self._检查紧急规则(上下文)
        if 紧急结果 is not None:
            候选动作.append((紧急结果.动作索引, 紧急结果.置信度))
            return 紧急结果
        
        # 尝试应用普通规则
        规则结果 = self._应用规则(上下文, 排除紧急=True)
        
        # 获取模型结果
        模型结果 = self._应用模型(上下文, 候选动作)
        
        # 如果规则匹配，解决冲突
        if 规则结果 is not None:
            候选动作.append((规则结果.动作索引, 规则结果.置信度))
            return self._解决冲突(规则结果, 模型结果)
        
        return 模型结果
    
    def _应用规则(self, 上下文: 决策上下文, 
                 排除紧急: bool = False) -> Optional[决策结果]:
        """
        应用规则引擎
        
        Args:
            上下文: 决策上下文
            排除紧急: 是否排除紧急规则
            
        Returns:
            匹配的规则结果，无匹配返回None
        """
        for 规则 in self.规则列表:
            # 排除紧急规则
            if 排除紧急 and "紧急" in 规则.名称:
                continue
            
            # 检查冷却
            if not self._检查规则冷却(规则):
                continue
            
            # 检查动作冷却
            if not self.检查冷却(规则.动作):
                continue
            
            # 检查条件
            try:
                if 规则.检查条件(上下文):
                    动作名称 = self._获取动作名称(规则.动作)
                    return 决策结果(
                        动作索引=规则.动作,
                        动作名称=动作名称,
                        来源="rule",
                        置信度=1.0,
                        原因=f"规则匹配: {规则.名称}"
                    )
            except Exception as e:
                logger.warning(f"规则 {规则.名称} 执行异常: {e}")
                continue
        
        return None
    
    def _检查紧急规则(self, 上下文: 决策上下文) -> Optional[决策结果]:
        """
        检查紧急规则
        
        Args:
            上下文: 决策上下文
            
        Returns:
            紧急规则结果，无匹配返回None
        """
        低血量阈值 = 紧急规则配置.get("低血量阈值", 0.3)
        被围攻阈值 = 紧急规则配置.get("被围攻阈值", 3)
        紧急动作 = 紧急规则配置.get("紧急动作", 19)
        
        # 检查低血量
        if 上下文.血量百分比 < 低血量阈值:
            if self.检查冷却(紧急动作):
                动作名称 = self._获取动作名称(紧急动作)
                return 决策结果(
                    动作索引=紧急动作,
                    动作名称=动作名称,
                    来源="rule",
                    置信度=1.0,
                    原因=f"紧急规则: 低血量 ({上下文.血量百分比:.1%})"
                )
        
        # 检查被围攻
        if 上下文.附近敌人数量 >= 被围攻阈值:
            if self.检查冷却(紧急动作):
                动作名称 = self._获取动作名称(紧急动作)
                return 决策结果(
                    动作索引=紧急动作,
                    动作名称=动作名称,
                    来源="rule",
                    置信度=1.0,
                    原因=f"紧急规则: 被围攻 ({上下文.附近敌人数量}个敌人)"
                )
        
        return None
    
    def _检查规则冷却(self, 规则: 决策规则) -> bool:
        """检查规则是否在冷却中"""
        if 规则.冷却时间 <= 0:
            return True
        
        规则键 = f"rule_{规则.名称}"
        上次时间 = self.动作冷却.get(规则键, 0)
        return time.time() - 上次时间 >= 规则.冷却时间

    def _应用模型(self, 上下文: 决策上下文,
                 候选动作: List[Tuple[int, float]]) -> 决策结果:
        """
        应用模型预测
        
        使用统一推理引擎进行模型预测，支持 ONNX 和 TFLearn 后端。
        
        Args:
            上下文: 决策上下文
            候选动作: 候选动作列表 (会被修改)
            
        Returns:
            模型预测结果
            
        需求: 4.2 - 加载旧格式模型时使用原始 TFLearn 推理
        需求: 4.3 - 加载新格式模型时使用 ONNX Runtime 推理
        """
        # 获取状态动作权重
        状态权重 = self.获取状态动作权重(上下文.游戏状态)
        
        # 获取模型预测
        模型预测 = 上下文.模型预测
        
        # 如果上下文中没有模型预测，但有图像且推理引擎可用，则进行推理
        if (not 模型预测 or len(模型预测) == 0) and self._启用ONNX推理 and self._推理引擎:
            if hasattr(上下文, '当前图像') and 上下文.当前图像 is not None:
                推理结果 = self.使用统一推理(上下文.当前图像)
                if 推理结果:
                    模型预测 = 推理结果
        
        # 如果有模型预测，结合权重
        if 模型预测 and len(模型预测) > 0:
            加权分数 = self._计算加权分数(模型预测, 状态权重)
        else:
            # 没有模型预测，使用状态权重作为分数
            加权分数 = 状态权重.copy()
        
        # 过滤冷却中的动作
        for i in range(len(加权分数)):
            if not self.检查冷却(i):
                加权分数[i] = 0.0
        
        # 找到最高分动作
        最高分 = max(加权分数)
        if 最高分 <= 0:
            # 所有动作都在冷却中，返回无操作
            return 决策结果(
                动作索引=8,  # 无操作
                动作名称="无操作",
                来源="model",
                置信度=0.0,
                原因="所有动作都在冷却中"
            )
        
        最佳动作 = 加权分数.index(最高分)
        
        # 记录候选动作 (前5个)
        排序索引 = sorted(range(len(加权分数)), 
                        key=lambda i: 加权分数[i], reverse=True)
        for i in 排序索引[:5]:
            候选动作.append((i, 加权分数[i]))
        
        动作名称 = self._获取动作名称(最佳动作)
        置信度 = 最高分 / max(sum(加权分数), 1.0)  # 归一化置信度
        
        # 记录使用的推理后端
        后端信息 = ""
        if self._推理引擎 and self._启用ONNX推理:
            后端信息 = f", 后端={self._推理引擎.获取当前后端()}"
        
        return 决策结果(
            动作索引=最佳动作,
            动作名称=动作名称,
            来源="model",
            置信度=min(置信度, 1.0),
            原因=f"模型预测: 状态={上下文.游戏状态.value}{后端信息}"
        )
    
    def _计算加权分数(self, 模型预测: List[float], 
                    状态权重: List[float]) -> List[float]:
        """
        计算加权分数
        
        Args:
            模型预测: 模型预测的动作概率
            状态权重: 状态对应的动作权重
            
        Returns:
            加权后的分数列表
        """
        结果 = []
        for i in range(总动作数):
            模型分 = 模型预测[i] if i < len(模型预测) else 0.0
            权重分 = 状态权重[i] if i < len(状态权重) else 1.0
            # 加权计算
            加权分 = 模型分 * self.模型权重 + 权重分 * self.规则权重
            结果.append(加权分)
        return 结果
    
    def _解决冲突(self, 规则结果: 决策结果, 
                 模型结果: 决策结果) -> 决策结果:
        """
        解决规则和模型的冲突
        
        Args:
            规则结果: 规则引擎的结果
            模型结果: 模型预测的结果
            
        Returns:
            最终决策结果
        """
        # 如果动作相同，合并结果
        if 规则结果.动作索引 == 模型结果.动作索引:
            return 决策结果(
                动作索引=规则结果.动作索引,
                动作名称=规则结果.动作名称,
                来源="mixed",
                置信度=max(规则结果.置信度, 模型结果.置信度),
                原因=f"规则和模型一致: {规则结果.原因}"
            )
        
        # 根据策略和权重决定
        规则分数 = 规则结果.置信度 * self.规则权重
        模型分数 = 模型结果.置信度 * self.模型权重
        
        if 规则分数 >= 模型分数:
            return 决策结果(
                动作索引=规则结果.动作索引,
                动作名称=规则结果.动作名称,
                来源="mixed",
                置信度=规则结果.置信度,
                原因=f"规则优先: {规则结果.原因}"
            )
        else:
            return 决策结果(
                动作索引=模型结果.动作索引,
                动作名称=模型结果.动作名称,
                来源="mixed",
                置信度=模型结果.置信度,
                原因=f"模型优先: {模型结果.原因}"
            )
    
    def 获取状态动作权重(self, 状态: 游戏状态) -> List[float]:
        """
        获取特定状态下的动作权重
        
        Args:
            状态: 游戏状态
            
        Returns:
            32维动作权重列表
        """
        # 将游戏状态转换为配置中的枚举
        状态映射 = {
            游戏状态.战斗: 游戏状态枚举.战斗,
            游戏状态.对话: 游戏状态枚举.对话,
            游戏状态.菜单: 游戏状态枚举.菜单,
            游戏状态.移动: 游戏状态枚举.移动,
            游戏状态.拾取: 游戏状态枚举.拾取,
            游戏状态.采集: 游戏状态枚举.采集,
            游戏状态.死亡: 游戏状态枚举.死亡,
            游戏状态.加载: 游戏状态枚举.加载,
            游戏状态.空闲: 游戏状态枚举.空闲,
            游戏状态.未知: 游戏状态枚举.未知,
        }
        
        配置状态 = 状态映射.get(状态, 游戏状态枚举.未知)
        类型权重 = 状态动作权重.get(配置状态, {})
        
        # 构建32维权重列表
        权重列表 = []
        for i in range(总动作数):
            动作信息 = 动作定义.get(i, {})
            动作类型 = 动作信息.get("类型", "未知")
            权重 = 类型权重.get(动作类型, 1.0)
            权重列表.append(权重)
        
        return 权重列表
    
    def 检查冷却(self, 动作索引: int) -> bool:
        """
        检查动作是否在冷却中
        
        Args:
            动作索引: 动作索引
            
        Returns:
            True表示可以执行，False表示在冷却中
        """
        冷却时间 = 动作冷却时间.get(动作索引, 0)
        if 冷却时间 <= 0:
            return True
        
        上次时间 = self.动作冷却.get(动作索引, 0)
        return time.time() - 上次时间 >= 冷却时间
    
    def 记录动作执行(self, 动作索引: int) -> None:
        """
        记录动作执行时间（用于冷却计算）
        
        Args:
            动作索引: 执行的动作索引
        """
        self.动作冷却[动作索引] = time.time()
        logger.debug(f"记录动作执行: {动作索引}")
    
    def 获取决策日志(self, 数量: int = 10) -> List[决策日志]:
        """
        获取最近的决策日志
        
        Args:
            数量: 要获取的日志数量
            
        Returns:
            决策日志列表
        """
        日志列表 = list(self.决策日志)
        return 日志列表[-数量:] if len(日志列表) > 数量 else 日志列表
    
    def 清空日志(self) -> None:
        """清空决策日志"""
        self.决策日志.clear()
        logger.debug("已清空决策日志")
    
    def 重置冷却(self) -> None:
        """重置所有动作冷却"""
        self.动作冷却.clear()
        logger.debug("已重置所有动作冷却")
    
    def _获取动作名称(self, 动作索引: int) -> str:
        """获取动作名称"""
        动作信息 = 动作定义.get(动作索引, {})
        return 动作信息.get("名称", f"动作{动作索引}")
    
    def 获取统计信息(self) -> Dict:
        """
        获取决策引擎统计信息
        
        Returns:
            统计信息字典
        """
        日志列表 = list(self.决策日志)
        
        if not 日志列表:
            return {
                "总决策数": 0,
                "规则决策数": 0,
                "模型决策数": 0,
                "混合决策数": 0,
                "规则数量": len(self.规则列表),
            }
        
        规则数 = sum(1 for log in 日志列表 if log.最终决策.来源 == "rule")
        模型数 = sum(1 for log in 日志列表 if log.最终决策.来源 == "model")
        混合数 = sum(1 for log in 日志列表 if log.最终决策.来源 == "mixed")
        
        return {
            "总决策数": len(日志列表),
            "规则决策数": 规则数,
            "模型决策数": 模型数,
            "混合决策数": 混合数,
            "规则数量": len(self.规则列表),
            "规则决策比例": 规则数 / len(日志列表) if 日志列表 else 0,
        }
    
    # ==================== 自动调参集成方法 ====================
    
    def _初始化自动调参(self) -> None:
        """初始化自动调参模块
        
        需求: 10.3 - 与决策引擎集成，实时应用参数调整
        """
        if not 自动调参可用:
            logger.warning("自动调参模块不可用")
            return
        
        try:
            self._auto_tuner = AutoTuner(
                enabled=True,
                aggressiveness=AggressivenessLevel.BALANCED
            )
            logger.info("自动调参模块初始化成功")
        except Exception as e:
            logger.error(f"自动调参模块初始化失败: {e}")
            self._auto_tuner = None
            self._启用自动调参 = False
    
    def 启用自动调参(self, 启用: bool = True) -> None:
        """启用或禁用自动调参
        
        Args:
            启用: 是否启用
        """
        if not 自动调参可用:
            logger.warning("自动调参模块不可用")
            return
        
        self._启用自动调参 = 启用
        
        if 启用 and self._auto_tuner is None:
            self._初始化自动调参()
        
        if self._auto_tuner:
            self._auto_tuner.enabled = 启用
        
        logger.info(f"自动调参已{'启用' if 启用 else '禁用'}")
    
    def 设置调参激进程度(self, 程度: str) -> None:
        """设置调参激进程度
        
        Args:
            程度: "conservative"(保守), "balanced"(平衡), "aggressive"(激进)
        """
        if not self._auto_tuner:
            return
        
        程度映射 = {
            "conservative": AggressivenessLevel.CONSERVATIVE,
            "balanced": AggressivenessLevel.BALANCED,
            "aggressive": AggressivenessLevel.AGGRESSIVE,
            "保守": AggressivenessLevel.CONSERVATIVE,
            "平衡": AggressivenessLevel.BALANCED,
            "激进": AggressivenessLevel.AGGRESSIVE,
        }
        
        if 程度 in 程度映射:
            self._auto_tuner.aggressiveness = 程度映射[程度]
            logger.info(f"调参激进程度已设置为: {程度}")
        else:
            logger.warning(f"无效的激进程度: {程度}")
    
    def 记录执行结果(self, 成功: bool, 卡住: bool = False) -> None:
        """记录动作执行结果，用于性能指标收集
        
        Args:
            成功: 动作是否执行成功
            卡住: 是否检测到卡住状态
        """
        self._性能统计["总决策数"] += 1
        if 成功:
            self._性能统计["成功执行数"] += 1
        if 卡住:
            self._性能统计["卡住次数"] += 1
        
        # 定期收集性能指标
        if self._启用自动调参 and self._auto_tuner:
            self._收集性能指标()
            self._尝试自动调参()
    
    def _收集性能指标(self) -> None:
        """收集性能指标并发送到自动调参器"""
        if not self._auto_tuner:
            return
        
        总数 = self._性能统计["总决策数"]
        if 总数 == 0:
            return
        
        # 计算成功率
        成功率 = self._性能统计["成功执行数"] / 总数
        
        # 从决策日志计算状态识别准确率（简化估算）
        日志列表 = list(self.决策日志)
        状态准确率 = 0.8  # 默认值
        if 日志列表:
            # 基于置信度估算准确率
            置信度总和 = sum(log.最终决策.置信度 for log in 日志列表)
            状态准确率 = 置信度总和 / len(日志列表)
        
        # 创建性能指标
        from datetime import datetime
        metric = PerformanceMetric(
            timestamp=datetime.now(),
            action_success_rate=成功率,
            state_accuracy=状态准确率,
            stuck_count=self._性能统计["卡住次数"],
            task_efficiency=成功率 * 0.8 + 状态准确率 * 0.2  # 简化的效率计算
        )
        
        self._auto_tuner.collect_metric(metric)
    
    def _尝试自动调参(self) -> None:
        """尝试执行自动调参"""
        if not self._auto_tuner or not self._启用自动调参:
            return
        
        当前时间 = time.time()
        if 当前时间 - self._性能统计["上次调参时间"] < self._调参间隔:
            return
        
        # 执行自动调参
        record = self._auto_tuner.auto_tune_cycle()
        if record:
            self._性能统计["上次调参时间"] = 当前时间
            self._应用调参结果(record)
    
    def _应用调参结果(self, record) -> None:
        """应用调参结果到决策引擎
        
        Args:
            record: 调参记录
        """
        param_name = record.parameter_name
        new_value = record.new_value
        
        # 根据参数名称应用到决策引擎
        if param_name == "rule_priority_weight":
            self.规则权重 = new_value
            self.模型权重 = 1.0 - new_value
            logger.info(f"已应用参数调整: 规则权重={new_value:.2f}")
        
        elif param_name == "action_cooldown":
            # 更新全局动作冷却时间（需要配置支持）
            logger.info(f"已应用参数调整: 动作冷却={new_value:.2f}")
        
        elif param_name == "state_switch_threshold":
            # 状态切换阈值（需要状态识别器支持）
            logger.info(f"已应用参数调整: 状态切换阈值={new_value:.2f}")
        
        elif param_name == "detection_confidence_threshold":
            # 检测置信度阈值（需要检测器支持）
            logger.info(f"已应用参数调整: 检测置信度阈值={new_value:.2f}")
    
    def 获取自动调参状态(self) -> Dict:
        """获取自动调参状态信息
        
        Returns:
            状态信息字典
        """
        if not self._auto_tuner:
            return {
                "可用": False,
                "启用": False,
                "消息": "自动调参模块不可用"
            }
        
        return {
            "可用": True,
            "启用": self._启用自动调参,
            "激进程度": self._auto_tuner.aggressiveness.value,
            "指标数量": self._auto_tuner.get_metrics_count(),
            "调参记录数": len(self._auto_tuner.get_records()),
            "锁定参数": self._auto_tuner.get_locked_parameters(),
            "参数差异": self._auto_tuner.get_parameter_diff()
        }
    
    def 锁定参数(self, 参数名: str) -> None:
        """锁定指定参数，防止自动调参修改
        
        Args:
            参数名: 参数名称
        """
        if self._auto_tuner:
            try:
                self._auto_tuner.lock_parameter(参数名)
            except ValueError as e:
                logger.warning(f"锁定参数失败: {e}")
    
    def 解锁参数(self, 参数名: str) -> None:
        """解锁指定参数
        
        Args:
            参数名: 参数名称
        """
        if self._auto_tuner:
            try:
                self._auto_tuner.unlock_parameter(参数名)
            except ValueError as e:
                logger.warning(f"解锁参数失败: {e}")
    
    def 重置参数为默认值(self) -> None:
        """重置所有参数为默认值"""
        if self._auto_tuner:
            self._auto_tuner.reset_to_defaults()
            # 重置决策引擎参数
            self.规则权重 = 决策引擎配置.get("规则权重", 0.6)
            self.模型权重 = 决策引擎配置.get("模型权重", 0.4)
            logger.info("已重置所有参数为默认值")
    
    # ==================== ONNX推理集成方法 ====================
    
    def _初始化推理引擎(self, 模型路径: str = None) -> None:
        """初始化统一推理引擎
        
        使用统一推理引擎替换原有的 TFLearn 推理调用，
        支持自动检测模型格式并选择对应后端。
        
        Args:
            模型路径: 可选，模型文件路径。如果不指定，从配置加载。
            
        需求: 4.2 - 加载旧格式模型时使用原始 TFLearn 推理
        需求: 4.3 - 加载新格式模型时使用 ONNX Runtime 推理
        """
        if not ONNX推理可用:
            logger.warning("ONNX推理模块不可用")
            return
        
        try:
            # 从配置获取推理设置
            from 配置.设置 import 获取推理配置
            配置 = 获取推理配置()
            
            # 使用传入的模型路径或配置中的路径
            实际模型路径 = 模型路径 or 配置.get("模型路径", "")
            
            self._推理引擎 = 统一推理引擎(
                模型路径=实际模型路径,
                首选后端=配置.get("首选后端", "auto"),
                使用GPU=配置.get("使用GPU", True),
                配置=配置
            )
            
            后端 = self._推理引擎.获取当前后端()
            logger.info(f"统一推理引擎初始化成功，使用后端: {后端}")
        except Exception as e:
            logger.error(f"统一推理引擎初始化失败: {e}")
            self._推理引擎 = None
            self._启用ONNX推理 = False
    
    def 使用统一推理(self, 图像: np.ndarray) -> Optional[List[float]]:
        """使用统一推理引擎进行推理
        
        统一推理引擎会自动选择 ONNX 或 TFLearn 后端。
        
        Args:
            图像: 输入图像
            
        Returns:
            推理结果（动作概率列表），失败返回None
            
        需求: 4.2 - 加载旧格式模型时使用原始 TFLearn 推理
        需求: 4.3 - 加载新格式模型时使用 ONNX Runtime 推理
        """
        if not self._推理引擎 or not self._启用ONNX推理:
            return None
        
        try:
            结果 = self._推理引擎.预测(图像)
            return 结果 if isinstance(结果, list) else 结果.tolist()
        except Exception as e:
            logger.warning(f"统一推理失败: {e}")
            return None
    
    def 使用ONNX推理(self, 图像: np.ndarray) -> Optional[List[float]]:
        """使用ONNX引擎进行推理（兼容旧接口）
        
        此方法保留用于向后兼容，内部调用统一推理引擎。
        
        Args:
            图像: 输入图像
            
        Returns:
            推理结果（动作概率列表），失败返回None
        """
        return self.使用统一推理(图像)
    
    def 获取推理引擎状态(self) -> Dict:
        """获取推理引擎状态
        
        返回推理引擎的详细状态信息，包括当前后端、
        检测到的模型格式、延迟统计等。
        """
        if not self._推理引擎:
            return {"可用": False, "启用": False, "后端": "none"}
        
        状态 = {
            "可用": True,
            "启用": self._启用ONNX推理,
            "后端": self._推理引擎.获取当前后端() if hasattr(self._推理引擎, '获取当前后端') else "unknown",
            "检测到的格式": self._推理引擎.获取检测到的格式() if hasattr(self._推理引擎, '获取检测到的格式') else "unknown",
            "首选后端": self._推理引擎.首选后端 if hasattr(self._推理引擎, '首选后端') else "auto",
            "使用GPU": self._推理引擎.使用GPU if hasattr(self._推理引擎, '使用GPU') else False
        }
        
        # 获取延迟统计
        if hasattr(self._推理引擎, '获取延迟统计'):
            try:
                延迟统计 = self._推理引擎.获取延迟统计()
                状态["延迟统计"] = {
                    "平均延迟": 延迟统计.平均延迟,
                    "最小延迟": 延迟统计.最小延迟,
                    "最大延迟": 延迟统计.最大延迟,
                    "推理次数": 延迟统计.推理次数,
                    "满足延迟要求": 延迟统计.满足延迟要求
                }
            except Exception:
                pass
        
        return 状态
    
    def 切换推理后端(self, 后端: str) -> bool:
        """切换推理后端
        
        允许在运行时切换推理后端（auto/onnx/tflearn）。
        
        Args:
            后端: "auto", "onnx", "tflearn"
            
        Returns:
            是否切换成功
            
        需求: 4.4 - 提供配置选项来选择首选的推理后端
        """
        if not self._推理引擎:
            logger.warning("推理引擎未初始化，无法切换后端")
            return False
        
        有效后端 = ["auto", "onnx", "tflearn"]
        if 后端 not in 有效后端:
            logger.error(f"无效的推理后端: {后端}，有效值: {有效后端}")
            return False
        
        try:
            self._推理引擎.设置首选后端(后端)
            
            # 重新加载模型以应用新后端
            if hasattr(self._推理引擎, '模型路径') and self._推理引擎.模型路径:
                self._推理引擎.加载模型(self._推理引擎.模型路径, 后端)
            
            logger.info(f"推理后端已切换为: {后端}")
            return True
        except Exception as e:
            logger.error(f"切换推理后端失败: {e}")
            return False
    
    def 加载推理模型(self, 模型路径: str, 首选后端: str = None) -> bool:
        """加载新的推理模型
        
        允许在运行时加载新模型，支持 ONNX 和 TFLearn 格式。
        
        Args:
            模型路径: 模型文件路径
            首选后端: 可选，指定首选后端
            
        Returns:
            是否加载成功
            
        需求: 4.1 - 自动检测模型格式
        """
        if not self._推理引擎:
            # 如果推理引擎未初始化，尝试初始化
            self._初始化推理引擎(模型路径)
            return self._推理引擎 is not None
        
        try:
            return self._推理引擎.加载模型(模型路径, 首选后端)
        except Exception as e:
            logger.error(f"加载推理模型失败: {e}")
            return False
    
    def 启用推理引擎(self, 启用: bool = True) -> None:
        """启用或禁用推理引擎
        
        Args:
            启用: 是否启用
        """
        self._启用ONNX推理 = 启用
        logger.info(f"推理引擎已{'启用' if 启用 else '禁用'}")
    
    # ==================== 模型管理集成方法 ====================
    
    def _初始化模型管理器(self) -> None:
        """
        初始化模型管理器、自动切换器和快捷键处理器
        
        需求: 2.1 - 在不停止 AI 的情况下切换活动模型
        需求: 3.2 - 当游戏状态匹配规则时，切换到指定模型
        需求: 4.1 - 支持模型切换的快捷键
        """
        if not 模型管理可用:
            logger.warning("模型管理模块不可用")
            return
        
        try:
            # 初始化模型管理器
            self._模型管理器 = 模型管理器()
            logger.info("模型管理器初始化成功")
            
            # 初始化自动切换器 - 需求: 3.2
            self._自动切换器 = 自动切换器(self._模型管理器)
            logger.info("自动切换器初始化成功")
            
            # 初始化快捷键处理器 - 需求: 4.1
            self._快捷键处理器 = 快捷键处理器(self._模型管理器)
            logger.info("快捷键处理器初始化成功")
            
        except Exception as e:
            logger.error(f"模型管理器初始化失败: {e}")
            self._模型管理器 = None
            self._自动切换器 = None
            self._快捷键处理器 = None
    
    def 切换模型(self, 模型名称: str) -> bool:
        """热切换模型
        
        Args:
            模型名称: 要切换到的模型名称
            
        Returns:
            是否切换成功
        """
        if not self._模型管理器:
            logger.warning("模型管理器不可用")
            return False
        
        try:
            return self._模型管理器.切换模型(模型名称)
        except Exception as e:
            logger.error(f"模型切换失败: {e}")
            return False
    
    def 获取可用模型列表(self) -> List[str]:
        """获取可用模型列表"""
        if not self._模型管理器:
            return []
        
        try:
            return self._模型管理器.获取模型列表()
        except Exception as e:
            logger.error(f"获取模型列表失败: {e}")
            return []
    
    def 获取当前模型(self) -> Optional[str]:
        """获取当前使用的模型名称"""
        if not self._模型管理器:
            return None
        
        try:
            return self._模型管理器.获取当前模型()
        except Exception as e:
            logger.error(f"获取当前模型失败: {e}")
            return None
    
    def 检查自动切换(self, 当前状态: str) -> bool:
        """
        检查并执行自动模型切换
        
        根据当前游戏状态检查是否需要自动切换模型。
        应在每个决策周期调用此方法。
        
        Args:
            当前状态: 当前游戏状态字符串
            
        Returns:
            是否执行了切换
            
        需求: 2.1 - 在不停止 AI 的情况下切换活动模型
        需求: 3.2 - 当游戏状态匹配规则时，切换到指定模型
        """
        if not self._自动切换器:
            return False
        
        try:
            return self._自动切换器.执行自动切换(当前状态)
        except Exception as e:
            logger.warning(f"自动切换检查失败: {e}")
            return False
    
    def 处理快捷键(self, 按键: str) -> bool:
        """
        处理模型切换快捷键
        
        Args:
            按键: 按键名称（如 "F1", "F2"）
            
        Returns:
            是否触发了模型切换
            
        需求: 4.1 - 支持模型切换的快捷键
        """
        if not self._快捷键处理器:
            return False
        
        try:
            return self._快捷键处理器.处理按键(按键)
        except Exception as e:
            logger.warning(f"快捷键处理失败: {e}")
            return False
    
    def 循环切换模型(self) -> Optional[str]:
        """
        循环切换到下一个模型
        
        Returns:
            新的活动模型名称，切换失败返回 None
            
        需求: 4.3 - 支持用单个按键循环切换可用模型
        """
        if not self._快捷键处理器:
            return None
        
        try:
            return self._快捷键处理器.循环切换()
        except Exception as e:
            logger.warning(f"循环切换失败: {e}")
            return None
    
    def 添加自动切换规则(self, 规则名称: str, 触发状态: List[str], 
                        目标模型: str, 优先级: int = 0, 
                        冷却时间: float = 5.0) -> bool:
        """
        添加自动切换规则
        
        Args:
            规则名称: 规则名称
            触发状态: 触发切换的游戏状态列表
            目标模型: 切换到的目标模型
            优先级: 优先级，数值越大优先级越高
            冷却时间: 该规则的冷却时间（秒）
            
        Returns:
            是否添加成功
            
        需求: 3.1 - 支持定义基于游戏状态的自动切换规则
        """
        if not self._自动切换器:
            logger.warning("自动切换器不可用")
            return False
        
        try:
            from 核心.模型管理 import 自动切换规则
            规则 = 自动切换规则(
                名称=规则名称,
                触发状态=触发状态,
                目标模型=目标模型,
                优先级=优先级,
                冷却时间=冷却时间
            )
            return self._自动切换器.添加规则(规则)
        except Exception as e:
            logger.error(f"添加自动切换规则失败: {e}")
            return False
    
    def 设置自动切换启用(self, 启用: bool) -> None:
        """
        设置自动切换启用状态
        
        Args:
            启用: 是否启用自动切换
            
        需求: 3.4 - 支持通过配置禁用自动切换
        """
        if self._自动切换器:
            self._自动切换器.设置启用状态(启用)
            logger.info(f"自动切换已{'启用' if 启用 else '禁用'}")
    
    def 设置自动切换冷却时间(self, 冷却时间: float) -> None:
        """
        设置自动切换全局冷却时间
        
        Args:
            冷却时间: 冷却时间（秒）
            
        需求: 3.3 - 支持自动切换之间的冷却时间
        """
        if self._自动切换器:
            self._自动切换器.设置全局冷却时间(冷却时间)
    
    def 注册快捷键(self, 按键: str, 模型名: str) -> bool:
        """
        注册模型切换快捷键
        
        Args:
            按键: 快捷键名称（如 "F1", "F2"）
            模型名: 对应的模型名称
            
        Returns:
            是否注册成功
            
        需求: 4.1 - 支持模型切换的快捷键
        """
        if not self._快捷键处理器:
            logger.warning("快捷键处理器不可用")
            return False
        
        try:
            return self._快捷键处理器.注册快捷键(按键, 模型名)
        except Exception as e:
            logger.error(f"注册快捷键失败: {e}")
            return False
    
    def 获取快捷键映射(self) -> Dict[str, str]:
        """
        获取快捷键映射
        
        Returns:
            {按键: 模型名}
        """
        if not self._快捷键处理器:
            return {}
        
        try:
            return self._快捷键处理器.获取快捷键映射()
        except Exception as e:
            logger.error(f"获取快捷键映射失败: {e}")
            return {}
    
    def 获取自动切换状态(self) -> Dict:
        """
        获取自动切换器状态
        
        Returns:
            状态信息字典
        """
        if not self._自动切换器:
            return {"可用": False, "启用": False}
        
        try:
            状态 = self._自动切换器.获取状态()
            状态["可用"] = True
            return 状态
        except Exception as e:
            logger.error(f"获取自动切换状态失败: {e}")
            return {"可用": False, "启用": False}
    
    def 获取快捷键处理器状态(self) -> Dict:
        """
        获取快捷键处理器状态
        
        Returns:
            状态信息字典
        """
        if not self._快捷键处理器:
            return {"可用": False, "启用": False}
        
        try:
            状态 = self._快捷键处理器.获取状态()
            状态["可用"] = True
            return 状态
        except Exception as e:
            logger.error(f"获取快捷键处理器状态失败: {e}")
            return {"可用": False, "启用": False}
    
    def 带自动切换的决策(self, 上下文: 决策上下文, 图像: np.ndarray = None) -> 决策结果:
        """
        执行带自动模型切换的决策
        
        在决策前自动检查是否需要切换模型，然后执行决策。
        这是推荐的决策入口方法，确保每个决策周期都会检查自动切换。
        
        Args:
            上下文: 决策上下文信息
            图像: 游戏画面图像（用于状态检测）
            
        Returns:
            决策结果
            
        需求: 2.1 - 在不停止 AI 的情况下切换活动模型
        需求: 3.2 - 当游戏状态匹配规则时，切换到指定模型
        """
        # 检查自动切换
        if self._自动切换器:
            状态字符串 = 上下文.游戏状态.value if hasattr(上下文.游戏状态, 'value') else str(上下文.游戏状态)
            self.检查自动切换(状态字符串)
        
        # 执行带状态检测的决策
        return self.带状态检测的决策(上下文, 图像)

    # ==================== 状态检测集成方法 ====================
    
    def _初始化状态检测器(self) -> None:
        """初始化状态检测器
        
        从配置文件加载状态检测配置，包括血条/蓝条区域和颜色配置。
        
        需求: 1.4 - 血量检测器应将区域配置保存到配置文件
        """
        if not 状态检测可用:
            logger.warning("状态检测模块不可用")
            return
        
        try:
            # 从配置构建检测器配置
            检测器配置 = {}
            
            # 血条配置
            血条配置 = 状态检测配置.get("血条", {})
            if 血条配置:
                检测器配置["血条"] = {
                    "区域": 血条配置.get("区域"),
                    "平滑窗口": 血条配置.get("平滑窗口", 5),
                    "失败超时": 状态检测配置.get("错误处理", {}).get("失败超时", 5.0)
                }
                # 处理颜色配置
                if 血条配置.get("使用渐变", False):
                    检测器配置["血条"]["颜色"] = 血条配置.get("渐变颜色", {})
                else:
                    检测器配置["血条"]["颜色"] = 血条配置.get("颜色", {})
            
            # 蓝条配置
            蓝条配置 = 状态检测配置.get("蓝条", {})
            if 蓝条配置:
                检测器配置["蓝条"] = {
                    "区域": 蓝条配置.get("区域"),
                    "平滑窗口": 蓝条配置.get("平滑窗口", 5),
                    "失败超时": 状态检测配置.get("错误处理", {}).get("失败超时", 5.0),
                    "颜色": 蓝条配置.get("颜色", {})
                }
            
            self._状态检测器 = 状态检测器(检测器配置)
            
            # 尝试加载默认配置文件
            配置目录 = 状态检测配置.get("配置目录", "配置/状态检测")
            默认配置 = 状态检测配置.get("默认配置", "default")
            配置路径 = f"{配置目录}/{默认配置}.json"
            
            import os
            if os.path.exists(配置路径):
                try:
                    self._状态检测器.从配置加载(配置路径)
                    logger.info(f"已加载状态检测配置: {配置路径}")
                except Exception as e:
                    logger.warning(f"加载状态检测配置失败: {e}")
            
            logger.info("状态检测器初始化成功")
        except Exception as e:
            logger.error(f"状态检测器初始化失败: {e}")
            self._状态检测器 = None
            self._启用状态检测 = False
    
    def 检测角色状态(self, 图像: np.ndarray) -> Dict:
        """检测角色血量/蓝量状态
        
        在每个决策周期调用，检测当前血量和蓝量百分比。
        
        Args:
            图像: 游戏画面图像
            
        Returns:
            状态字典，包含血量百分比、蓝量百分比等
            
        需求: 5.1 - 血量检测器应提供获取当前血量百分比的方法
        """
        if not self._状态检测器 or not self._启用状态检测:
            return {"血量百分比": 1.0, "蓝量百分比": 1.0, "检测成功": False}
        
        try:
            结果 = self._状态检测器.检测(图像)
            # 将状态检测结果转换为字典格式
            return {
                "血量百分比": 结果.血量百分比,
                "蓝量百分比": 结果.蓝量百分比,
                "血量置信度": 结果.血量置信度,
                "蓝量置信度": 结果.蓝量置信度,
                "检测时间": 结果.检测时间,
                "检测成功": True
            }
        except Exception as e:
            logger.warning(f"状态检测失败: {e}")
            return {"血量百分比": 1.0, "蓝量百分比": 1.0, "检测成功": False}
    
    def 更新决策上下文状态(self, 上下文: 决策上下文, 图像: np.ndarray) -> 决策上下文:
        """使用状态检测更新决策上下文
        
        在每个决策周期前调用，更新上下文中的血量和蓝量信息。
        
        Args:
            上下文: 原始决策上下文
            图像: 游戏画面图像
            
        Returns:
            更新后的决策上下文
            
        需求: 5.2 - 决策引擎应在每个决策周期前调用血量检测器
        """
        if self._启用状态检测 and self._状态检测器:
            状态 = self.检测角色状态(图像)
            if 状态.get("检测成功", False):
                上下文.血量百分比 = 状态.get("血量百分比", 上下文.血量百分比)
                # 如果上下文支持蓝量，也更新蓝量
                if hasattr(上下文, '蓝量百分比'):
                    上下文.蓝量百分比 = 状态.get("蓝量百分比", 1.0)
                
                # 记录血量变化日志（需求 5.4）
                logger.debug(f"状态检测更新: 血量={上下文.血量百分比*100:.1f}%, "
                           f"蓝量={状态.get('蓝量百分比', 1.0)*100:.1f}%")
        
        return 上下文
    
    def 获取状态检测器状态(self) -> Dict:
        """获取状态检测器状态"""
        if not self._状态检测器:
            return {"可用": False, "启用": False}
        
        return {
            "可用": True,
            "启用": self._启用状态检测
        }
    
    def 带状态检测的决策(self, 上下文: 决策上下文, 图像: np.ndarray = None) -> 决策结果:
        """
        执行带状态检测的决策
        
        在决策前自动检测血量/蓝量状态，更新上下文后执行决策。
        这是推荐的决策入口方法，确保每个决策周期都会调用状态检测。
        
        Args:
            上下文: 决策上下文信息
            图像: 游戏画面图像（用于状态检测）
            
        Returns:
            决策结果
            
        需求: 5.2 - 决策引擎应在每个决策周期前调用血量检测器
        需求: 5.3 - 当血量低于紧急阈值时，决策引擎应触发紧急规则
        """
        # 如果提供了图像，先进行状态检测更新上下文
        if 图像 is not None and self._启用状态检测:
            上下文 = self.更新决策上下文状态(上下文, 图像)
        
        # 执行决策（紧急规则会在 _检查紧急规则 中根据血量触发）
        return self.决策(上下文)
    
    def 设置状态检测配置(self, 血条区域: tuple = None, 蓝条区域: tuple = None,
                        血条颜色: dict = None, 蓝条颜色: dict = None):
        """
        设置状态检测配置
        
        Args:
            血条区域: 血条感兴趣区域 (x, y, width, height)
            蓝条区域: 蓝条感兴趣区域 (x, y, width, height)
            血条颜色: 血条颜色配置
            蓝条颜色: 蓝条颜色配置
            
        需求: 1.1 - 血量检测器应支持配置血条感兴趣区域
        """
        if not self._状态检测器:
            logger.warning("状态检测器不可用，无法设置配置")
            return
        
        if 血条区域:
            self._状态检测器.设置血条区域(血条区域)
            logger.info(f"已设置血条区域: {血条区域}")
        
        if 蓝条区域:
            self._状态检测器.设置蓝条区域(蓝条区域)
            logger.info(f"已设置蓝条区域: {蓝条区域}")
        
        if 血条颜色:
            self._状态检测器._血量检测器.设置颜色配置(血条颜色)
            logger.info("已设置血条颜色配置")
        
        if 蓝条颜色:
            self._状态检测器._蓝量检测器.设置颜色配置(蓝条颜色)
            logger.info("已设置蓝条颜色配置")
    
    def 从配置文件加载状态检测(self, 配置路径: str):
        """
        从配置文件加载状态检测配置
        
        Args:
            配置路径: 配置文件路径
            
        需求: 1.4 - 血量检测器应将区域配置保存到配置文件
        """
        if not self._状态检测器:
            logger.warning("状态检测器不可用，无法加载配置")
            return
        
        try:
            self._状态检测器.从配置加载(配置路径)
            logger.info(f"已从配置文件加载状态检测配置: {配置路径}")
        except Exception as e:
            logger.error(f"加载状态检测配置失败: {e}")
    
    def 保存状态检测配置(self, 配置路径: str):
        """
        保存状态检测配置到文件
        
        Args:
            配置路径: 配置文件路径
            
        需求: 1.4 - 血量检测器应将区域配置保存到配置文件
        """
        if not self._状态检测器:
            logger.warning("状态检测器不可用，无法保存配置")
            return
        
        try:
            self._状态检测器.保存配置(配置路径)
            logger.info(f"已保存状态检测配置: {配置路径}")
        except Exception as e:
            logger.error(f"保存状态检测配置失败: {e}")
    
    def 获取状态检测诊断信息(self) -> Dict:
        """
        获取状态检测诊断信息
        
        Returns:
            诊断信息字典
            
        需求: 6.3 - 血量检测器应记录检测失败及诊断信息
        """
        if not self._状态检测器:
            return {"可用": False, "消息": "状态检测器不可用"}
        
        return self._状态检测器.获取诊断信息()
    
    # ==================== 综合状态方法 ====================
    
    def 获取引擎完整状态(self) -> Dict:
        """获取决策引擎完整状态信息
        
        Returns:
            包含所有子模块状态的字典
        """
        # 获取状态检测详细信息
        状态检测信息 = self.获取状态检测器状态()
        if self._状态检测器 and self._启用状态检测:
            try:
                统计 = self._状态检测器.获取检测统计()
                状态检测信息.update({
                    "总检测次数": 统计.get("总检测次数", 0),
                    "总成功率": 统计.get("总成功率", 0.0),
                    "血量检测成功率": 统计.get("血量检测", {}).get("成功率", 0.0),
                    "蓝量检测成功率": 统计.get("蓝量检测", {}).get("成功率", 0.0)
                })
            except Exception as e:
                logger.debug(f"获取状态检测统计失败: {e}")
        
        # 获取推理引擎详细状态
        推理状态 = self.获取推理引擎状态()
        
        return {
            "决策引擎": {
                "策略": self.策略.value,
                "规则数量": len(self.规则列表),
                "规则权重": self.规则权重,
                "模型权重": self.模型权重
            },
            "自动调参": self.获取自动调参状态(),
            "推理引擎": 推理状态,
            "模型管理": {
                "可用": self._模型管理器 is not None,
                "当前模型": self.获取当前模型(),
                "可用模型数": len(self.获取可用模型列表())
            },
            "自动切换": self.获取自动切换状态(),
            "快捷键处理": self.获取快捷键处理器状态(),
            "状态检测": 状态检测信息,
            "统计信息": self.获取统计信息()
        }

