"""
共享数据类型模块
定义实体类型、方向、游戏状态枚举以及各种数据类
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Tuple, Callable
import time


# ==================== 枚举类型 ====================
class 实体类型(Enum):
    """游戏中可识别的实体类型"""
    怪物 = "monster"
    NPC = "npc"
    玩家 = "player"
    物品 = "item"
    技能特效 = "skill_effect"
    未知 = "unknown"


class 方向(Enum):
    """相对于屏幕中心的方向"""
    左 = "left"
    右 = "right"
    上 = "up"
    下 = "down"
    中心 = "center"
    左上 = "top_left"
    右上 = "top_right"
    左下 = "bottom_left"
    右下 = "bottom_right"


class 游戏状态(Enum):
    """游戏状态枚举"""
    战斗 = "combat"
    对话 = "dialogue"
    菜单 = "menu"
    移动 = "moving"
    拾取 = "looting"
    采集 = "gathering"
    死亡 = "dead"
    加载 = "loading"
    空闲 = "idle"
    未知 = "unknown"


class 决策策略(Enum):
    """决策策略类型"""
    规则优先 = "rule_first"
    模型优先 = "model_first"
    混合加权 = "weighted_mix"


# ==================== 检测结果数据类 ====================
@dataclass
class 检测结果:
    """单个目标检测结果"""
    类型: 实体类型
    置信度: float  # 0.0 - 1.0
    边界框: Tuple[int, int, int, int]  # (x, y, width, height)
    中心点: Tuple[int, int]  # (x, y)
    方向: 方向
    距离: float  # 相对于屏幕中心的距离

    def __post_init__(self):
        """验证数据有效性"""
        if not 0.0 <= self.置信度 <= 1.0:
            raise ValueError(f"置信度必须在0-1范围内，当前值: {self.置信度}")
        if self.距离 < 0:
            raise ValueError(f"距离不能为负数，当前值: {self.距离}")


# ==================== 状态识别结果数据类 ====================
@dataclass
class 状态识别结果:
    """状态识别结果"""
    状态: 游戏状态
    置信度: float  # 0.0 - 1.0
    检测到的UI元素: List[str] = field(default_factory=list)
    附近实体数量: int = 0

    def __post_init__(self):
        """验证数据有效性"""
        if not 0.0 <= self.置信度 <= 1.0:
            raise ValueError(f"置信度必须在0-1范围内，当前值: {self.置信度}")
        if self.附近实体数量 < 0:
            raise ValueError(f"附近实体数量不能为负数，当前值: {self.附近实体数量}")


# ==================== 决策相关数据类 ====================
@dataclass
class 决策上下文:
    """决策时的上下文信息"""
    游戏状态: 游戏状态
    检测结果: List[检测结果] = field(default_factory=list)
    模型预测: List[float] = field(default_factory=list)  # 32维动作概率
    血量百分比: float = 1.0
    附近敌人数量: int = 0
    上次动作: Optional[int] = None
    上次动作时间: float = 0.0

    def __post_init__(self):
        """验证数据有效性"""
        if not 0.0 <= self.血量百分比 <= 1.0:
            raise ValueError(f"血量百分比必须在0-1范围内，当前值: {self.血量百分比}")
        if self.附近敌人数量 < 0:
            raise ValueError(f"附近敌人数量不能为负数，当前值: {self.附近敌人数量}")


@dataclass
class 决策结果:
    """决策结果"""
    动作索引: int
    动作名称: str
    来源: str  # "rule" 或 "model" 或 "mixed"
    置信度: float
    原因: str

    def __post_init__(self):
        """验证数据有效性"""
        if self.动作索引 < 0:
            raise ValueError(f"动作索引不能为负数，当前值: {self.动作索引}")
        if not 0.0 <= self.置信度 <= 1.0:
            raise ValueError(f"置信度必须在0-1范围内，当前值: {self.置信度}")
        if self.来源 not in ("rule", "model", "mixed"):
            raise ValueError(f"来源必须是 'rule', 'model' 或 'mixed'，当前值: {self.来源}")


@dataclass
class 决策规则:
    """决策规则定义"""
    名称: str
    优先级: int  # 数字越大优先级越高
    条件: Callable[['决策上下文'], bool]
    动作: int  # 动作索引
    冷却时间: float = 0.0  # 秒

    def 检查条件(self, 上下文: 决策上下文) -> bool:
        """检查规则条件是否满足"""
        try:
            return self.条件(上下文)
        except Exception:
            return False


@dataclass
class 决策日志:
    """决策日志记录"""
    时间戳: float
    上下文: 决策上下文
    候选动作: List[Tuple[int, float]]  # (动作索引, 分数)
    最终决策: 决策结果

    def __post_init__(self):
        """设置默认时间戳"""
        if self.时间戳 <= 0:
            self.时间戳 = time.time()
