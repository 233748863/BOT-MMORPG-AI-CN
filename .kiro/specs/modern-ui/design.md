# 设计文档

## 概述

本设计文档描述MMORPG游戏AI助手的现代化图形用户界面(GUI)实现方案。采用PySide6框架构建，提供明亮、清新的视觉风格，固定800x600像素窗口尺寸，支持数据收集、模型训练、机器人运行、配置管理等核心功能。

## 架构

### 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                      主应用程序 (QApplication)               │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌─────────────────────────────────────────┐  │
│  │          │  │              主内容区域                   │  │
│  │  导航栏   │  │  ┌─────────────────────────────────┐   │  │
│  │ QListWidget│  │  │      QStackedWidget             │   │  │
│  │  • 首页   │  │  │  • 首页(状态仪表盘)              │   │  │
│  │  • 数据   │  │  │  • 数据收集页面                  │   │  │
│  │  • 训练   │  │  │  • 训练页面                      │   │  │
│  │  • 运行   │  │  │  • 运行页面                      │   │  │
│  │  • 配置   │  │  │  • 配置页面                      │   │  │
│  │  • 管理   │  │  │  • 数据管理页面                  │   │  │
│  │          │  └─────────────────────────────────────────┘  │
│  └──────────┘                                               │
├─────────────────────────────────────────────────────────────┤
│                      状态栏 (QStatusBar)                     │
└─────────────────────────────────────────────────────────────┘
```

### 首页布局 (状态仪表盘)

```
┌─────────────────────────────────────────────────────────────┐
│  🎮 MMORPG游戏AI助手                                         │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ 📊 系统状态                                            │  │
│  │  模型状态:  ✅ 已加载  |  GPU:  ✅ 可用                 │  │
│  │  数据文件:  📁 12个文件 (6000样本)                      │  │
│  │  上次训练:  2025-01-01 12:30 (损失: 0.023)             │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌─────────────────────┐  ┌─────────────────────┐          │
│  │   ▶ 快速运行         │  │   🎥 开始录制        │          │
│  │   启动AI机器人       │  │   收集训练数据       │          │
│  └─────────────────────┘  └─────────────────────┘          │
│                                                             │
│  ┌─────────────────────┐  ┌─────────────────────┐          │
│  │   🧠 训练模型        │  │   📁 数据管理        │          │
│  │   训练AI大脑         │  │   管理训练数据       │          │
│  └─────────────────────┘  └─────────────────────┘          │
│                                                             │
│  💡 提示: 首次使用请先收集训练数据                            │
└─────────────────────────────────────────────────────────────┘
```

### 技术选型

- **GUI框架**: PySide6 (Qt官方Python绑定，LGPL开源协议)
- **图表库**: PyQtGraph (高性能Qt图表库) 或 Matplotlib (通过FigureCanvas嵌入)
- **线程管理**: QThread + Signal/Slot机制
- **事件通信**: Qt Signal/Slot机制
- **样式**: QSS (Qt Style Sheets)

### 模块划分

```
界面/
├── __init__.py
├── 主程序.py           # 应用入口和主窗口 (QMainWindow)
├── 组件/
│   ├── __init__.py
│   ├── 导航栏.py       # 左侧导航组件 (QListWidget)
│   ├── 控制面板.py     # 通用控制按钮组件 (QWidget)
│   ├── 状态监控.py     # 状态显示组件 (QWidget)
│   ├── 日志查看器.py   # 日志显示组件 (QTextEdit)
│   └── 配置编辑器.py   # 配置编辑组件 (QWidget)
├── 页面/
│   ├── __init__.py
│   ├── 首页.py         # 欢迎页面 (QWidget)
│   ├── 数据收集页.py   # 数据收集功能 (QWidget)
│   ├── 训练页.py       # 模型训练功能 (QWidget)
│   ├── 运行页.py       # 机器人运行功能 (QWidget)
│   ├── 配置页.py       # 配置管理功能 (QWidget)
│   └── 数据管理页.py   # 数据文件管理 (QWidget)
├── 线程/
│   ├── __init__.py
│   ├── 数据收集线程.py # 数据收集后台线程 (QThread)
│   ├── 训练线程.py     # 模型训练后台线程 (QThread)
│   └── 运行线程.py     # 机器人运行后台线程 (QThread)
├── 资源/
│   ├── icons/          # 图标资源
│   ├── styles/         # QSS样式文件
│   └── resources.qrc   # Qt资源文件
└── 样式/
    ├── __init__.py
    └── 主题.py         # 颜色和样式定义
```

## 组件和接口

### 1. 主窗口类 (MainWindow)

```python
from PySide6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QStackedWidget
from PySide6.QtCore import Signal, Slot
from PySide6.QtGui import QShortcut, QKeySequence

class MainWindow(QMainWindow):
    """主窗口类"""
    
    # 信号定义
    页面切换信号 = Signal(str)
    通知信号 = Signal(str, str, str)  # 标题, 内容, 类型
    
    def __init__(self):
        """初始化主窗口，设置固定尺寸800x600"""
        super().__init__()
        self.setWindowTitle("🎮 MMORPG游戏AI助手")
        self.setFixedSize(800, 600)
        self._初始化界面()
        self._绑定快捷键()
    
    def _初始化界面(self) -> None:
        """初始化界面布局"""
        pass
    
    @Slot(str)
    def 切换页面(self, 页面名称: str) -> None:
        """切换到指定功能页面"""
        pass
    
    def 显示通知(self, 标题: str, 内容: str, 类型: str = "info") -> None:
        """显示弹出通知 (使用QSystemTrayIcon或自定义Toast)"""
        pass
    
    def _绑定快捷键(self) -> None:
        """绑定全局快捷键"""
        pass
```

### 2. 导航栏组件 (NavigationBar)

```python
from PySide6.QtWidgets import QListWidget, QListWidgetItem
from PySide6.QtCore import Signal
from PySide6.QtGui import QIcon

class NavigationBar(QListWidget):
    """左侧导航栏组件"""
    
    # 信号定义
    导航项点击 = Signal(str)
    
    def __init__(self, parent=None):
        """初始化导航栏"""
        super().__init__(parent)
        self.setFixedWidth(120)
        self._初始化导航项()
    
    def _初始化导航项(self) -> None:
        """初始化导航项列表"""
        导航项 = [
            ("🏠", "首页"),
            ("🎥", "数据收集"),
            ("🧠", "训练"),
            ("🤖", "运行"),
            ("⚙️", "配置"),
            ("📁", "数据管理"),
        ]
        for 图标, 名称 in 导航项:
            item = QListWidgetItem(f"{图标} {名称}")
            self.addItem(item)
    
    def 设置选中项(self, 项目名称: str) -> None:
        """设置当前选中的导航项"""
        pass
```

### 3. 控制面板组件 (ControlPanel)

```python
from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton
from PySide6.QtCore import Signal

class ControlPanel(QWidget):
    """控制面板组件，包含操作按钮"""
    
    # 信号定义
    开始点击 = Signal()
    暂停点击 = Signal()
    停止点击 = Signal()
    
    def __init__(self, parent=None, 模式: str = "通用"):
        """初始化控制面板"""
        super().__init__(parent)
        self._模式 = 模式
        self._初始化按钮()
    
    def _初始化按钮(self) -> None:
        """初始化控制按钮"""
        pass
    
    def 设置按钮状态(self, 按钮名称: str, 启用: bool) -> None:
        """设置按钮启用/禁用状态"""
        pass
```

### 4. 状态监控组件 (StatusMonitor)

```python
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar
from PySide6.QtCore import Slot
from PySide6.QtGui import QImage, QPixmap
import numpy as np

class StatusMonitor(QWidget):
    """状态监控组件，显示实时状态信息"""
    
    def __init__(self, parent=None):
        """初始化状态监控"""
        super().__init__(parent)
        self._初始化界面()
    
    def _初始化界面(self) -> None:
        """初始化界面元素"""
        pass
    
    @Slot(dict)
    def 更新状态(self, 状态数据: dict) -> None:
        """更新状态显示"""
        pass
    
    def 设置状态颜色(self, 状态类型: str) -> None:
        """根据状态类型设置颜色（正常/警告/错误）"""
        颜色映射 = {
            "正常": "#10B981",  # 绿色
            "警告": "#F59E0B",  # 黄色
            "错误": "#EF4444",  # 红色
        }
        pass
    
    def 更新预览图像(self, 图像: np.ndarray) -> None:
        """更新游戏画面预览"""
        # 将numpy数组转换为QPixmap
        pass
```

### 5. 日志查看器组件 (LogViewer)

```python
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QLineEdit, QComboBox
from PySide6.QtCore import Slot
from datetime import datetime

class LogViewer(QWidget):
    """日志查看器组件"""
    
    def __init__(self, parent=None):
        """初始化日志查看器"""
        super().__init__(parent)
        self._日志列表 = []
        self._初始化界面()
    
    def _初始化界面(self) -> None:
        """初始化界面"""
        pass
    
    def 添加日志(self, 级别: str, 消息: str) -> None:
        """添加日志条目，自动添加时间戳"""
        时间戳 = datetime.now().strftime("%H:%M:%S")
        pass
    
    @Slot(str)
    def 过滤日志(self, 级别: str) -> None:
        """按级别过滤日志"""
        pass
    
    def 搜索日志(self, 关键词: str) -> list:
        """搜索日志内容"""
        pass
    
    def 导出日志(self, 文件路径: str) -> bool:
        """导出日志到文件"""
        pass
```

### 6. 配置编辑器组件 (ConfigEditor)

```python
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QFormLayout, 
                                QLineEdit, QSpinBox, QDoubleSpinBox,
                                QComboBox, QCheckBox, QPushButton)
from PySide6.QtCore import Signal

class ConfigEditor(QWidget):
    """配置编辑器组件"""
    
    # 信号定义
    配置已保存 = Signal()
    验证失败 = Signal(str, str)  # 配置项, 错误信息
    
    def __init__(self, parent=None, 配置类型: str = "通用"):
        """初始化配置编辑器"""
        super().__init__(parent)
        self._配置类型 = 配置类型
        self._配置项控件 = {}
        self._初始化界面()
    
    def _初始化界面(self) -> None:
        """初始化界面"""
        pass
    
    def 加载配置(self) -> dict:
        """从配置文件加载配置"""
        pass
    
    def 保存配置(self) -> bool:
        """保存配置到文件"""
        pass
    
    def 验证配置(self, 配置项: str, 值) -> tuple:
        """验证配置值有效性，返回(是否有效, 错误信息)"""
        pass
    
    def 重置配置(self) -> None:
        """重置为默认配置"""
        pass
```

### 7. 后台任务线程 (WorkerThread)

```python
from PySide6.QtCore import QThread, Signal

class WorkerThread(QThread):
    """通用后台任务线程基类"""
    
    # 信号定义
    进度更新 = Signal(int, str)  # 进度百分比, 状态消息
    任务完成 = Signal(bool, str)  # 是否成功, 结果消息
    错误发生 = Signal(str)  # 错误消息
    
    def __init__(self, parent=None):
        """初始化线程"""
        super().__init__(parent)
        self._停止标志 = False
    
    def run(self) -> None:
        """线程执行入口，子类重写"""
        pass
    
    def 请求停止(self) -> None:
        """请求停止线程"""
        self._停止标志 = True


class 数据收集线程(WorkerThread):
    """数据收集后台线程"""
    
    # 额外信号
    样本收集 = Signal(int, int)  # 样本数量, 文件编号
    帧更新 = Signal(object)  # numpy数组
    
    def run(self) -> None:
        """执行数据收集"""
        pass


class 训练线程(WorkerThread):
    """模型训练后台线程"""
    
    # 额外信号
    轮次完成 = Signal(int, int, float)  # 当前轮次, 总轮次, 损失值
    
    def run(self) -> None:
        """执行模型训练"""
        pass


class 运行线程(WorkerThread):
    """机器人运行后台线程"""
    
    # 额外信号
    状态更新 = Signal(dict)  # 运行状态数据
    
    def run(self) -> None:
        """执行机器人运行"""
        pass
```

## 数据模型

### 应用状态模型

```python
from dataclasses import dataclass, field
from typing import Optional, List, Dict
import numpy as np

@dataclass
class 应用状态:
    """应用全局状态"""
    当前页面: str = "首页"
    是否运行中: bool = False
    当前任务: Optional[str] = None
    最后错误: Optional[str] = None

@dataclass
class 数据收集状态:
    """数据收集状态"""
    是否录制中: bool = False
    是否暂停: bool = False
    样本数量: int = 0
    文件编号: int = 1
    当前帧: Optional[np.ndarray] = None

@dataclass
class 训练状态:
    """训练状态"""
    是否训练中: bool = False
    当前轮次: int = 0
    总轮次: int = 10
    当前损失: float = 0.0
    损失历史: List[float] = field(default_factory=list)
    预计剩余时间: str = "--:--"

@dataclass
class 运行状态:
    """机器人运行状态"""
    是否运行中: bool = False
    是否暂停: bool = False
    运行模式: str = "基础"
    子模式: str = "主线任务"
    当前动作: str = "无"
    动作来源: str = "model"
    游戏状态: str = "未知"
    帧率: float = 0.0
    运动量: float = 0.0
    增强模块状态: Dict[str, bool] = field(default_factory=dict)
```

### 样式定义

```python
# QSS样式表 (light_theme.qss)
LIGHT_THEME_QSS = """
/* 主窗口 */
QMainWindow {
    background-color: #F8FAFC;
}

/* 导航栏 */
QListWidget {
    background-color: #FFFFFF;
    border: none;
    border-right: 1px solid #E2E8F0;
    font-size: 13px;
}

QListWidget::item {
    padding: 12px 16px;
    border-radius: 8px;
    margin: 4px 8px;
}

QListWidget::item:selected {
    background-color: #EFF6FF;
    color: #3B82F6;
}

QListWidget::item:hover {
    background-color: #F1F5F9;
}

/* 按钮 */
QPushButton {
    background-color: #3B82F6;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-size: 13px;
}

QPushButton:hover {
    background-color: #2563EB;
}

QPushButton:pressed {
    background-color: #1D4ED8;
}

QPushButton:disabled {
    background-color: #CBD5E1;
}

/* 卡片容器 */
QFrame[class="card"] {
    background-color: #FFFFFF;
    border-radius: 12px;
    border: 1px solid #E2E8F0;
}

/* 标签 */
QLabel {
    color: #334155;
    font-size: 13px;
}

QLabel[class="title"] {
    font-size: 16px;
    font-weight: bold;
    color: #1E293B;
}

/* 进度条 */
QProgressBar {
    border: none;
    border-radius: 4px;
    background-color: #E2E8F0;
    height: 8px;
}

QProgressBar::chunk {
    background-color: #10B981;
    border-radius: 4px;
}

/* 输入框 */
QLineEdit, QSpinBox, QDoubleSpinBox {
    border: 1px solid #CBD5E1;
    border-radius: 6px;
    padding: 8px;
    background-color: #FFFFFF;
}

QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {
    border-color: #3B82F6;
}

/* 下拉框 */
QComboBox {
    border: 1px solid #CBD5E1;
    border-radius: 6px;
    padding: 8px;
    background-color: #FFFFFF;
}

/* 状态栏 */
QStatusBar {
    background-color: #FFFFFF;
    border-top: 1px solid #E2E8F0;
}
"""

# 颜色常量
class 颜色:
    主色 = "#3B82F6"      # 蓝色
    成功 = "#10B981"      # 绿色
    警告 = "#F59E0B"      # 黄色
    错误 = "#EF4444"      # 红色
    背景 = "#F8FAFC"      # 浅灰背景
    卡片背景 = "#FFFFFF"  # 白色
    边框 = "#E2E8F0"      # 边框灰
    文字 = "#334155"      # 深灰文字
    标题 = "#1E293B"      # 深色标题
```

## 正确性属性

*正确性属性是指在系统所有有效执行中都应保持为真的特征或行为——本质上是关于系统应该做什么的形式化陈述。属性作为人类可读规范和机器可验证正确性保证之间的桥梁。*

### Property 1: 导航切换一致性
*对于任意* 导航项点击操作，点击后主内容区域应显示对应的功能页面，且导航栏应正确标识当前选中项
**Validates: Requirements 1.4, 1.6**

### Property 2: 数据收集状态显示一致性
*对于任意* 数据收集过程中的状态变化，Status_Monitor显示的录制状态、样本数量和文件编号应与实际数据收集状态一致
**Validates: Requirements 2.2, 2.3**

### Property 3: 暂停/继续状态切换
*对于任意* 按下快捷键T的操作，当前运行状态应在暂停和继续之间正确切换
**Validates: Requirements 2.6, 8.1**

### Property 4: 训练进度显示一致性
*对于任意* 训练过程中的进度更新，进度条和轮次显示应与实际训练进度一致
**Validates: Requirements 3.3**

### Property 5: 日志显示功能
*对于任意* 添加的日志消息，应包含时间戳；对于任意过滤条件，过滤结果应只包含符合条件的日志；对于任意搜索关键词，搜索结果应包含该关键词
**Validates: Requirements 3.6, 7.1, 7.2, 7.3**

### Property 6: 运行状态显示一致性
*对于任意* 机器人运行过程中的状态更新，显示的动作名称、游戏状态、帧率、运动量和增强模块状态应与实际运行状态一致
**Validates: Requirements 4.4, 4.5, 4.6, 4.7**

### Property 7: 配置验证逻辑
*对于任意* 配置项输入，验证函数应正确判断输入有效性；对于无效输入，应阻止保存并显示错误提示
**Validates: Requirements 5.5, 5.7**

### Property 8: 配置保存一致性
*对于任意* 有效的配置修改，保存后配置文件内容应与用户输入一致
**Validates: Requirements 5.6**

### Property 9: 数据文件显示一致性
*对于任意* 数据目录中的文件，Data_Manager应正确显示文件列表、文件信息和统计数据
**Validates: Requirements 6.1, 6.2, 6.3**

### Property 10: 快捷键功能
*对于任意* 已注册的快捷键，按下后应触发对应的操作
**Validates: Requirements 8.1, 8.2, 8.5**

### Property 11: 后台任务界面响应性
*对于任意* 耗时操作（数据收集/训练/运行），操作期间主界面应保持响应，不阻塞用户交互
**Validates: Requirements 9.1, 9.2, 9.3**

### Property 12: 状态更新延迟
*对于任意* 状态更新，从数据变化到界面显示的延迟应不超过100ms
**Validates: Requirements 9.4**

### Property 13: 错误处理安全性
*对于任意* 后台操作中发生的错误，应安全地显示错误信息而不导致程序崩溃
**Validates: Requirements 9.5**

### Property 14: 状态颜色编码
*对于任意* 状态类型（正常/警告/错误），应使用对应的颜色（绿色/黄色/红色）显示
**Validates: Requirements 10.6**

## 错误处理

### 错误类型和处理策略

| 错误类型 | 处理策略 | 用户提示 |
|---------|---------|---------|
| 配置文件读取失败 | 使用默认配置 | 显示警告通知 |
| 配置保存失败 | 保留当前状态 | 显示错误对话框 |
| 模型加载失败 | 阻止运行操作 | 显示错误通知并提示解决方案 |
| 数据收集异常 | 自动暂停并保存已收集数据 | 显示警告通知 |
| 训练过程异常 | 保存当前模型检查点 | 显示错误通知 |
| 后台线程崩溃 | 安全终止线程 | 显示错误通知 |
| 屏幕截取失败 | 重试3次后暂停 | 显示警告通知 |

### 错误日志记录

所有错误应记录到日志系统，包含：
- 时间戳
- 错误级别
- 错误消息
- 堆栈跟踪（如适用）

## 测试策略

### 单元测试

- 测试各组件的独立功能
- 测试配置验证逻辑
- 测试事件总线的发布订阅机制
- 测试后台任务管理器

### 属性测试

使用Hypothesis库进行属性测试：
- 导航切换一致性测试
- 配置验证逻辑测试
- 日志过滤和搜索测试
- 状态显示一致性测试

### 集成测试

- 测试页面切换流程
- 测试数据收集完整流程
- 测试配置保存和加载流程
- 测试后台任务与界面交互

### 测试框架

- **单元测试**: pytest
- **属性测试**: hypothesis
- **GUI测试**: pytest-qt (PySide6专用测试框架)

### 依赖项

```
# requirements.txt 新增
PySide6>=6.5.0
pyqtgraph>=0.13.0  # 可选，用于高性能图表
```
