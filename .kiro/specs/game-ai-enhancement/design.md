# Design Document: 游戏AI增强系统

## Overview

本设计文档描述了MMORPG游戏AI助手的三个核心增强模块：YOLO目标检测集成、游戏状态识别系统、以及智能决策引擎。这些模块将与现有的模仿学习系统协同工作，提供更智能、更精准的游戏自动化能力。

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Game_AI_System (主控制器)                    │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  屏幕截取     │  │  YOLO检测器   │  │  状态识别器   │          │
│  │  (现有模块)   │──▶│  (新增)      │──▶│  (新增)      │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│         │                  │                  │                 │
│         ▼                  ▼                  ▼                 │
│  ┌─────────────────────────────────────────────────────┐       │
│  │              Decision_Engine (智能决策引擎)           │       │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │       │
│  │  │  规则引擎    │  │  模型预测    │  │  冲突解决    │  │       │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  │       │
│  └─────────────────────────────────────────────────────┘       │
│                              │                                  │
│                              ▼                                  │
│  ┌──────────────┐  ┌──────────────┐                            │
│  │  键盘控制     │  │  鼠标控制     │                            │
│  │  (现有模块)   │  │  (现有模块)   │                            │
│  └──────────────┘  └──────────────┘                            │
└─────────────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### 1. YOLO目标检测器 (YOLO_Detector)

**文件位置**: `核心/目标检测器.py`

```python
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Tuple

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

@dataclass
class 检测结果:
    """单个检测结果"""
    类型: 实体类型
    置信度: float  # 0.0 - 1.0
    边界框: Tuple[int, int, int, int]  # (x, y, width, height)
    中心点: Tuple[int, int]  # (x, y)
    方向: 方向
    距离: float  # 相对于屏幕中心的距离

class YOLO检测器:
    """YOLO目标检测器"""
    
    def __init__(self, 模型路径: str, 置信度阈值: float = 0.5):
        """初始化检测器"""
        pass
    
    def 检测(self, 图像: np.ndarray) -> List[检测结果]:
        """执行目标检测，返回按置信度降序排列的结果"""
        pass
    
    def 计算方向(self, 中心点: Tuple[int, int], 屏幕尺寸: Tuple[int, int]) -> 方向:
        """计算实体相对于屏幕中心的方向"""
        pass
    
    def 是否已加载(self) -> bool:
        """检查模型是否已加载"""
        pass
```

### 2. 游戏状态识别器 (State_Recognizer)

**文件位置**: `核心/状态识别器.py`

```python
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Callable
from collections import deque

class 游戏状态(Enum):
    """游戏状态枚举"""
    战斗 = "combat"
    对话 = "dialogue"
    菜单 = "menu"
    移动 = "moving"
    拾取 = "looting"
    采集 = "gathering"  # 采矿、采药、钓鱼等
    死亡 = "dead"
    加载 = "loading"
    空闲 = "idle"
    未知 = "unknown"

@dataclass
class 状态识别结果:
    """状态识别结果"""
    状态: 游戏状态
    置信度: float
    检测到的UI元素: List[str]
    附近实体数量: int

class 状态识别器:
    """游戏状态识别器"""
    
    def __init__(self, 历史长度: int = 10, 置信度累积系数: float = 0.1):
        """初始化状态识别器"""
        self.状态历史: deque = deque(maxlen=历史长度)
        self.状态变更回调: List[Callable] = []
        pass
    
    def 识别状态(self, 图像: np.ndarray, 检测结果: List[检测结果]) -> 状态识别结果:
        """识别当前游戏状态"""
        pass
    
    def 注册状态变更回调(self, 回调函数: Callable[[游戏状态, 游戏状态], None]):
        """注册状态变更时的回调函数"""
        pass
    
    def 获取状态历史(self, 数量: int = 5) -> List[状态识别结果]:
        """获取最近N次状态记录"""
        pass
    
    def _检测UI元素(self, 图像: np.ndarray) -> List[str]:
        """检测屏幕上的UI元素"""
        pass
    
    def _计算累积置信度(self, 当前状态: 游戏状态, 基础置信度: float) -> float:
        """根据历史状态计算累积置信度"""
        pass
```

### 3. 智能决策引擎 (Decision_Engine)

**文件位置**: `核心/决策引擎.py`

```python
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Callable
import time

class 决策策略(Enum):
    """决策策略类型"""
    规则优先 = "rule_first"
    模型优先 = "model_first"
    混合加权 = "weighted_mix"

@dataclass
class 决策规则:
    """决策规则定义"""
    名称: str
    优先级: int  # 数字越大优先级越高
    条件: Callable[['决策上下文'], bool]
    动作: int  # 动作索引
    冷却时间: float = 0.0  # 秒

@dataclass
class 决策上下文:
    """决策时的上下文信息"""
    游戏状态: 游戏状态
    检测结果: List[检测结果]
    模型预测: List[float]  # 32维动作概率
    血量百分比: float = 1.0
    附近敌人数量: int = 0
    上次动作: Optional[int] = None
    上次动作时间: float = 0.0

@dataclass
class 决策结果:
    """决策结果"""
    动作索引: int
    动作名称: str
    来源: str  # "rule" 或 "model" 或 "mixed"
    置信度: float
    原因: str

@dataclass
class 决策日志:
    """决策日志记录"""
    时间戳: float
    上下文: 决策上下文
    候选动作: List[Tuple[int, float]]  # (动作索引, 分数)
    最终决策: 决策结果

class 决策引擎:
    """智能决策引擎"""
    
    def __init__(self, 策略: 决策策略 = 决策策略.混合加权):
        """初始化决策引擎"""
        self.规则列表: List[决策规则] = []
        self.动作冷却: Dict[int, float] = {}  # 动作索引 -> 上次执行时间
        self.决策日志: deque = deque(maxlen=100)
        pass
    
    def 添加规则(self, 规则: 决策规则):
        """添加决策规则"""
        pass
    
    def 决策(self, 上下文: 决策上下文) -> 决策结果:
        """执行决策，返回最终动作"""
        pass
    
    def 获取状态动作权重(self, 状态: 游戏状态) -> List[float]:
        """获取特定状态下的动作权重"""
        pass
    
    def 检查冷却(self, 动作索引: int) -> bool:
        """检查动作是否在冷却中"""
        pass
    
    def 记录动作执行(self, 动作索引: int):
        """记录动作执行时间（用于冷却计算）"""
        pass
    
    def 获取决策日志(self, 数量: int = 10) -> List[决策日志]:
        """获取最近的决策日志"""
        pass
    
    def _应用规则(self, 上下文: 决策上下文) -> Optional[决策结果]:
        """应用规则引擎"""
        pass
    
    def _应用模型(self, 上下文: 决策上下文) -> 决策结果:
        """应用模型预测"""
        pass
    
    def _解决冲突(self, 规则结果: 决策结果, 模型结果: 决策结果) -> 决策结果:
        """解决规则和模型的冲突"""
        pass
```

## Data Models

### 配置数据模型

**文件位置**: `配置/增强设置.py`

```python
"""增强模块配置"""

# ==================== YOLO检测器设置 ====================
YOLO配置 = {
    "模型路径": "模型/yolo/game_detector.pt",
    "置信度阈值": 0.5,
    "NMS阈值": 0.4,
    "输入尺寸": (640, 640),
    "启用": True,
    "检测间隔": 3,  # 每N帧检测一次
}

# 实体类型映射 (YOLO类别ID -> 实体类型)
实体类型映射 = {
    0: "怪物",
    1: "NPC",
    2: "玩家",
    3: "物品",
    4: "技能特效",
}

# ==================== 状态识别器设置 ====================
状态识别配置 = {
    "历史长度": 10,
    "置信度累积系数": 0.1,
    "UI检测启用": True,
    "启用": True,
}

# UI元素模板路径
UI模板路径 = {
    "对话框": "资源/ui/dialogue_box.png",
    "菜单": "资源/ui/menu.png",
    "血条": "资源/ui/health_bar.png",
    "死亡界面": "资源/ui/death_screen.png",
    "加载界面": "资源/ui/loading.png",
}

# 状态判定阈值
状态判定阈值 = {
    "战斗_敌人距离": 200,  # 像素
    "战斗_敌人数量": 1,
    "拾取_物品距离": 100,
}

# ==================== 决策引擎设置 ====================
决策引擎配置 = {
    "策略": "混合加权",  # "规则优先", "模型优先", "混合加权"
    "规则权重": 0.6,
    "模型权重": 0.4,
    "启用日志": True,
    "日志长度": 100,
    "启用": True,
}

# 状态-动作权重映射
状态动作权重 = {
    "战斗": {
        "移动": 1.5,
        "技能": 2.5,
        "特殊": 2.0,
        "鼠标": 2.0,
        "组合": 1.5,
    },
    "对话": {
        "移动": 0.1,
        "技能": 0.0,
        "特殊": 0.5,
        "鼠标": 2.5,
        "组合": 0.0,
    },
    "移动": {
        "移动": 3.0,
        "技能": 0.2,
        "特殊": 0.5,
        "鼠标": 1.0,
        "组合": 0.1,
    },
    "拾取": {
        "移动": 1.0,
        "技能": 0.0,
        "特殊": 1.0,
        "鼠标": 2.0,
        "组合": 0.0,
    },
    "采集": {
        "移动": 0.1,  # 采集时不应移动
        "技能": 0.0,
        "特殊": 0.3,  # 可能需要取消采集
        "鼠标": 1.5,  # 点击确认等
        "组合": 0.0,
    },
}

# 动作冷却时间 (秒)
动作冷却时间 = {
    9: 1.0,   # 技能1
    10: 1.5,  # 技能2
    11: 2.0,  # 技能3
    12: 2.5,  # 技能4
    19: 0.5,  # 跳跃
    20: 1.0,  # 切换目标
}

# 紧急规则配置
紧急规则配置 = {
    "低血量阈值": 0.3,
    "被围攻阈值": 3,  # 敌人数量
    "紧急动作": 19,  # 跳跃/闪避
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: 检测结果后处理正确性
*For any* 检测结果列表和置信度阈值，经过后处理后的结果应该：(1) 按置信度降序排列，(2) 所有结果的置信度都 >= 阈值
**Validates: Requirements 1.2, 1.3**

### Property 2: 方向计算正确性
*For any* 实体中心点坐标和屏幕尺寸，计算出的方向应该正确反映实体相对于屏幕中心的位置
**Validates: Requirements 1.6**

### Property 3: 状态识别返回格式正确性
*For any* 输入图像，状态识别器应该返回包含状态和置信度的结果，置信度在0-1范围内
**Validates: Requirements 2.2**

### Property 4: 状态判定优先级正确性
*For any* 检测到UI元素的情况，状态应该优先判定为UI相关状态；*For any* 检测到近距离敌对实体的情况，状态应该判定为战斗状态
**Validates: Requirements 2.3, 2.4**

### Property 5: 状态历史记录正确性
*For any* N次状态更新，状态历史应该正确记录最近N次状态，且长度不超过配置的最大长度
**Validates: Requirements 2.6**

### Property 6: 置信度累积正确性
*For any* 连续相同状态的序列，累积置信度应该随着连续次数增加而增加
**Validates: Requirements 2.7**

### Property 7: 状态-动作权重映射正确性
*For any* 游戏状态，决策引擎应该返回对应的动作权重，战斗状态偏向技能，对话状态偏向交互，移动状态偏向移动
**Validates: Requirements 3.1, 3.2, 3.3, 3.4**

### Property 8: 规则优先级覆盖正确性
*For any* 高优先级规则触发的情况，规则结果应该覆盖模型预测结果
**Validates: Requirements 3.5**

### Property 9: 动作冷却机制正确性
*For any* 处于冷却中的动作，决策引擎应该阻止该动作被选择
**Validates: Requirements 3.9**

### Property 10: 决策日志完整性
*For any* 决策过程，日志应该包含状态、候选动作、最终选择及原因
**Validates: Requirements 3.7**

### Property 11: 模块降级正确性
*For any* 模块出错的情况，系统应该降级到基础模仿学习模式而不是崩溃
**Validates: Requirements 4.2**

## Error Handling

### YOLO检测器错误处理
- 模型文件不存在：记录警告，返回空检测结果，系统继续运行
- 图像格式错误：记录错误，返回空检测结果
- 检测超时：使用上一帧的检测结果

### 状态识别器错误处理
- UI模板文件缺失：跳过UI检测，仅使用实体检测判断状态
- 识别失败：返回"未知"状态，置信度为0

### 决策引擎错误处理
- 规则执行异常：跳过该规则，继续执行其他规则
- 模型预测失败：使用默认动作权重
- 所有模块失败：降级到基础模仿学习模式

## Testing Strategy

### 单元测试
- 测试各模块的独立功能
- 测试边界条件和错误处理
- 使用mock对象隔离依赖

### 属性测试 (Property-Based Testing)
- 使用hypothesis库进行属性测试
- 每个属性测试至少运行100次迭代
- 测试标签格式: **Feature: game-ai-enhancement, Property N: {property_text}**

### 集成测试
- 测试模块间的协作
- 测试完整的决策流程
- 测试降级机制

### 测试框架
- 使用pytest作为测试框架
- 使用hypothesis进行属性测试
- 测试文件位置: `测试/` 目录
