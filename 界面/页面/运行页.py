# -*- coding: utf-8 -*-
"""
运行页面

提供机器人运行功能的图形界面，包括模式选择、控制面板和状态监控。
支持基础模式和增强模式运行。

布局优化 (Requirements 4.1-4.5):
- 采用左右两栏布局，左栏占50%宽度，右栏占50%宽度
- 左栏：运行模式卡片 + 增强模块状态卡片
- 右栏：运行状态卡片 + 运行日志卡片

性能优化:
- 使用状态更新节流器，最小更新间隔50ms
"""

from typing import Optional, Dict
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QGridLayout, QComboBox,
    QSizePolicy, QGroupBox, QCheckBox, QTextEdit,
    QScrollArea
)
from PySide6.QtCore import Signal, Slot, Qt, QTimer
from PySide6.QtGui import QImage, QPixmap, QTextCursor

import numpy as np

from 界面.样式.主题 import 颜色
from 界面.样式.布局常量 import 布局常量
from 界面.组件.通用组件 import Card
from 界面.组件.性能优化 import 状态更新节流器


class 运行模式卡片(Card):
    """运行模式选择卡片组件 (Requirements 4.2)"""
    
    # 信号定义
    启动点击 = Signal()
    暂停点击 = Signal()
    停止点击 = Signal()
    运行模式改变 = Signal(str)
    子模式改变 = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__("🎮 运行模式", "", parent)
        self._初始化内容()

    def _初始化内容(self) -> None:
        """初始化卡片内容"""
        内容布局 = self.获取内容布局()
        
        # 运行模式选择
        运行模式容器 = QWidget()
        运行模式布局 = QHBoxLayout(运行模式容器)
        运行模式布局.setContentsMargins(0, 0, 0, 0)
        运行模式布局.setSpacing(8)
        
        运行模式标签 = QLabel("运行模式:")
        运行模式标签.setStyleSheet(f"color: {颜色.文字}; font-size: {布局常量.正文字号}px;")
        运行模式标签.setFixedWidth(60)
        运行模式布局.addWidget(运行模式标签)
        
        self._运行模式选择 = QComboBox()
        self._运行模式选择.addItems(["基础模式", "增强模式"])
        self._运行模式选择.setFixedHeight(布局常量.表单控件高度)
        self._运行模式选择.setStyleSheet(f"""
            QComboBox {{
                padding-left: 8px;
                font-size: {布局常量.正文字号}px;
            }}
        """)
        self._运行模式选择.currentTextChanged.connect(self.运行模式改变.emit)
        运行模式布局.addWidget(self._运行模式选择, 1)
        
        内容布局.addWidget(运行模式容器)
        
        # 子模式选择
        子模式容器 = QWidget()
        子模式布局 = QHBoxLayout(子模式容器)
        子模式布局.setContentsMargins(0, 0, 0, 0)
        子模式布局.setSpacing(8)
        
        子模式标签 = QLabel("任务模式:")
        子模式标签.setStyleSheet(f"color: {颜色.文字}; font-size: {布局常量.正文字号}px;")
        子模式标签.setFixedWidth(60)
        子模式布局.addWidget(子模式标签)
        
        self._子模式选择 = QComboBox()
        self._子模式选择.addItems(["主线任务", "自动战斗"])
        self._子模式选择.setFixedHeight(布局常量.表单控件高度)
        self._子模式选择.setStyleSheet(f"""
            QComboBox {{
                padding-left: 8px;
                font-size: {布局常量.正文字号}px;
            }}
        """)
        self._子模式选择.currentTextChanged.connect(self.子模式改变.emit)
        子模式布局.addWidget(self._子模式选择, 1)
        
        内容布局.addWidget(子模式容器)

        # 按钮容器
        按钮容器 = QWidget()
        按钮布局 = QHBoxLayout(按钮容器)
        按钮布局.setContentsMargins(0, 4, 0, 0)
        按钮布局.setSpacing(布局常量.按钮间距)
        
        # 启动按钮
        self._启动按钮 = QPushButton("🚀 启动")
        self._启动按钮.setFixedSize(布局常量.按钮最小宽度 + 10, 布局常量.按钮高度)
        self._启动按钮.setCursor(Qt.PointingHandCursor)
        self._启动按钮.setStyleSheet(f"""
            QPushButton {{
                background-color: {颜色.成功};
                color: white;
                border: none;
                border-radius: {布局常量.按钮圆角}px;
                font-size: {布局常量.按钮文字字号}px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: #059669;
            }}
            QPushButton:disabled {{
                background-color: {颜色.按钮禁用};
                color: {颜色.禁用文字};
            }}
        """)
        self._启动按钮.clicked.connect(self.启动点击.emit)
        按钮布局.addWidget(self._启动按钮)
        
        # 暂停按钮
        self._暂停按钮 = QPushButton("⏸ 暂停")
        self._暂停按钮.setFixedSize(布局常量.按钮最小宽度 + 10, 布局常量.按钮高度)
        self._暂停按钮.setCursor(Qt.PointingHandCursor)
        self._暂停按钮.setEnabled(False)
        self._暂停按钮.setStyleSheet(f"""
            QPushButton {{
                background-color: {颜色.警告};
                color: white;
                border: none;
                border-radius: {布局常量.按钮圆角}px;
                font-size: {布局常量.按钮文字字号}px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: #D97706;
            }}
            QPushButton:disabled {{
                background-color: {颜色.按钮禁用};
                color: {颜色.禁用文字};
            }}
        """)
        self._暂停按钮.clicked.connect(self.暂停点击.emit)
        按钮布局.addWidget(self._暂停按钮)

        # 停止按钮
        self._停止按钮 = QPushButton("⏹ 停止")
        self._停止按钮.setFixedSize(布局常量.按钮最小宽度 + 10, 布局常量.按钮高度)
        self._停止按钮.setCursor(Qt.PointingHandCursor)
        self._停止按钮.setEnabled(False)
        self._停止按钮.setStyleSheet(f"""
            QPushButton {{
                background-color: {颜色.错误};
                color: white;
                border: none;
                border-radius: {布局常量.按钮圆角}px;
                font-size: {布局常量.按钮文字字号}px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: #DC2626;
            }}
            QPushButton:disabled {{
                background-color: {颜色.按钮禁用};
                color: {颜色.禁用文字};
            }}
        """)
        self._停止按钮.clicked.connect(self.停止点击.emit)
        按钮布局.addWidget(self._停止按钮)
        
        按钮布局.addStretch()
        内容布局.addWidget(按钮容器)
        
        # 快捷键提示
        提示 = QLabel("💡 T 暂停/继续, ESC 停止")
        提示.setStyleSheet(f"color: {颜色.次要文字}; font-size: {布局常量.次要文字字号}px;")
        内容布局.addWidget(提示)
    
    def 设置运行状态(self, 运行中: bool, 已暂停: bool = False) -> None:
        """设置运行状态，更新按钮状态"""
        self._启动按钮.setEnabled(not 运行中)
        self._暂停按钮.setEnabled(运行中)
        self._停止按钮.setEnabled(运行中)
        self._运行模式选择.setEnabled(not 运行中)
        self._子模式选择.setEnabled(not 运行中)
        
        if 运行中:
            if 已暂停:
                self._暂停按钮.setText("▶️ 继续")
            else:
                self._暂停按钮.setText("⏸️ 暂停")
    
    def 获取运行模式(self) -> str:
        """获取当前选择的运行模式"""
        return self._运行模式选择.currentText()
    
    def 获取子模式(self) -> str:
        """获取当前选择的子模式"""
        return self._子模式选择.currentText()
    
    def 是否增强模式(self) -> bool:
        """返回是否选择了增强模式"""
        return self._运行模式选择.currentText() == "增强模式"


class 增强模块状态卡片(Card):
    """增强模块状态显示卡片组件 (Requirements 4.5)"""
    
    def __init__(self, parent=None):
        super().__init__("🔧 增强模块状态", "", parent)
        self._初始化内容()
    
    def _初始化内容(self) -> None:
        """初始化卡片内容"""
        内容布局 = self.获取内容布局()
        
        # 模块状态网格
        模块网格 = QGridLayout()
        模块网格.setSpacing(6)
        模块网格.setContentsMargins(0, 0, 0, 0)
        
        # YOLO检测器
        self._YOLO状态 = self._创建模块状态项("YOLO检测器:", 模块网格, 0, 0)
        
        # 状态识别器
        self._状态识别状态 = self._创建模块状态项("状态识别器:", 模块网格, 1, 0)
        
        # 决策引擎
        self._决策引擎状态 = self._创建模块状态项("决策引擎:", 模块网格, 2, 0)
        
        # 脱困模块
        self._脱困状态 = self._创建模块状态项("脱困模块:", 模块网格, 0, 1)
        
        # 自动调参
        self._自动调参状态 = self._创建模块状态项("自动调参:", 模块网格, 1, 1)
        
        内容布局.addLayout(模块网格)
        
        # 性能模式
        性能容器 = QWidget()
        性能布局 = QHBoxLayout(性能容器)
        性能布局.setContentsMargins(0, 4, 0, 0)
        性能布局.setSpacing(6)
        
        性能标签 = QLabel("性能模式:")
        性能标签.setStyleSheet(f"color: {颜色.次要文字}; font-size: {布局常量.次要文字字号}px;")
        性能布局.addWidget(性能标签)
        
        self._性能模式标签 = QLabel("正常")
        self._性能模式标签.setStyleSheet(f"color: {颜色.成功}; font-size: {布局常量.次要文字字号}px; font-weight: 500;")
        性能布局.addWidget(self._性能模式标签)
        性能布局.addStretch()
        
        内容布局.addWidget(性能容器)
    
    def _创建模块状态项(self, 标题: str, 网格: QGridLayout, 行: int, 列: int) -> QLabel:
        """创建模块状态项"""
        容器 = QWidget()
        容器布局 = QHBoxLayout(容器)
        容器布局.setContentsMargins(0, 0, 0, 0)
        容器布局.setSpacing(4)
        
        标题标签 = QLabel(标题)
        标题标签.setStyleSheet(f"color: {颜色.次要文字}; font-size: {布局常量.次要文字字号}px;")
        标题标签.setFixedWidth(70)
        容器布局.addWidget(标题标签)
        
        状态标签 = QLabel("未加载")
        状态标签.setStyleSheet(f"color: {颜色.次要文字}; font-size: {布局常量.次要文字字号}px;")
        容器布局.addWidget(状态标签)
        容器布局.addStretch()
        
        网格.addWidget(容器, 行, 列)
        return 状态标签

    def 更新YOLO状态(self, 可用: bool) -> None:
        """更新YOLO检测器状态"""
        if 可用:
            self._YOLO状态.setText("✅ 已加载")
            self._YOLO状态.setStyleSheet(f"color: {颜色.成功}; font-size: {布局常量.次要文字字号}px;")
        else:
            self._YOLO状态.setText("❌ 不可用")
            self._YOLO状态.setStyleSheet(f"color: {颜色.错误}; font-size: {布局常量.次要文字字号}px;")
    
    def 更新状态识别状态(self, 可用: bool) -> None:
        """更新状态识别器状态"""
        if 可用:
            self._状态识别状态.setText("✅ 已加载")
            self._状态识别状态.setStyleSheet(f"color: {颜色.成功}; font-size: {布局常量.次要文字字号}px;")
        else:
            self._状态识别状态.setText("❌ 不可用")
            self._状态识别状态.setStyleSheet(f"color: {颜色.错误}; font-size: {布局常量.次要文字字号}px;")
    
    def 更新决策引擎状态(self, 可用: bool) -> None:
        """更新决策引擎状态"""
        if 可用:
            self._决策引擎状态.setText("✅ 已加载")
            self._决策引擎状态.setStyleSheet(f"color: {颜色.成功}; font-size: {布局常量.次要文字字号}px;")
        else:
            self._决策引擎状态.setText("❌ 不可用")
            self._决策引擎状态.setStyleSheet(f"color: {颜色.错误}; font-size: {布局常量.次要文字字号}px;")
    
    def 更新脱困状态(self, 可用: bool) -> None:
        """更新脱困模块状态"""
        if 可用:
            self._脱困状态.setText("✅ 已加载")
            self._脱困状态.setStyleSheet(f"color: {颜色.成功}; font-size: {布局常量.次要文字字号}px;")
        else:
            self._脱困状态.setText("❌ 不可用")
            self._脱困状态.setStyleSheet(f"color: {颜色.错误}; font-size: {布局常量.次要文字字号}px;")
    
    def 更新自动调参状态(self, 可用: bool) -> None:
        """更新自动调参状态"""
        if 可用:
            self._自动调参状态.setText("⚠️ 启用")
            self._自动调参状态.setStyleSheet(f"color: {颜色.警告}; font-size: {布局常量.次要文字字号}px;")
        else:
            self._自动调参状态.setText("⏸ 禁用")
            self._自动调参状态.setStyleSheet(f"color: {颜色.次要文字}; font-size: {布局常量.次要文字字号}px;")
    
    def 更新性能模式(self, 低性能: bool) -> None:
        """更新性能模式显示"""
        if 低性能:
            self._性能模式标签.setText("⚠️ 低性能")
            self._性能模式标签.setStyleSheet(f"color: {颜色.警告}; font-size: {布局常量.次要文字字号}px; font-weight: 500;")
        else:
            self._性能模式标签.setText("✅ 正常")
            self._性能模式标签.setStyleSheet(f"color: {颜色.成功}; font-size: {布局常量.次要文字字号}px; font-weight: 500;")
    
    def 更新模块状态(self, 状态数据: Dict[str, bool]) -> None:
        """批量更新模块状态"""
        if "YOLO" in 状态数据:
            self.更新YOLO状态(状态数据["YOLO"])
        if "状态识别" in 状态数据:
            self.更新状态识别状态(状态数据["状态识别"])
        if "决策引擎" in 状态数据:
            self.更新决策引擎状态(状态数据["决策引擎"])
        if "脱困" in 状态数据:
            self.更新脱困状态(状态数据["脱困"])
        if "自动调参" in 状态数据:
            self.更新自动调参状态(状态数据["自动调参"])
        if "低性能" in 状态数据:
            self.更新性能模式(状态数据["低性能"])
    
    def 重置(self) -> None:
        """重置所有状态"""
        self._YOLO状态.setText("未加载")
        self._YOLO状态.setStyleSheet(f"color: {颜色.次要文字}; font-size: {布局常量.次要文字字号}px;")
        self._状态识别状态.setText("未加载")
        self._状态识别状态.setStyleSheet(f"color: {颜色.次要文字}; font-size: {布局常量.次要文字字号}px;")
        self._决策引擎状态.setText("未加载")
        self._决策引擎状态.setStyleSheet(f"color: {颜色.次要文字}; font-size: {布局常量.次要文字字号}px;")
        self._脱困状态.setText("未加载")
        self._脱困状态.setStyleSheet(f"color: {颜色.次要文字}; font-size: {布局常量.次要文字字号}px;")
        self._自动调参状态.setText("⏸ 禁用")
        self._自动调参状态.setStyleSheet(f"color: {颜色.次要文字}; font-size: {布局常量.次要文字字号}px;")
        self._性能模式标签.setText("正常")
        self._性能模式标签.setStyleSheet(f"color: {颜色.成功}; font-size: {布局常量.次要文字字号}px; font-weight: 500;")


class 运行状态卡片(Card):
    """运行状态监控卡片组件 (Requirements 4.4)"""
    
    def __init__(self, parent=None):
        super().__init__("📊 运行状态", "", parent)
        self._初始化内容()
    
    def _初始化内容(self) -> None:
        """初始化卡片内容"""
        内容布局 = self.获取内容布局()
        
        # 状态网格
        状态网格 = QGridLayout()
        状态网格.setSpacing(6)
        状态网格.setContentsMargins(0, 0, 0, 0)
        
        # 运行状态
        self._运行状态标签 = self._创建状态项("运行状态:", "已停止", 状态网格, 0, 0)
        
        # 当前动作
        self._当前动作标签 = self._创建状态项("当前动作:", "无", 状态网格, 0, 1)
        
        # 动作来源
        self._动作来源标签 = self._创建状态项("动作来源:", "-", 状态网格, 1, 0)
        
        # 游戏状态
        self._游戏状态标签 = self._创建状态项("游戏状态:", "未知", 状态网格, 1, 1)
        
        # 帧率
        self._帧率标签 = self._创建状态项("帧率:", "0 FPS", 状态网格, 2, 0)
        
        # 运动量
        self._运动量标签 = self._创建状态项("运动量:", "0", 状态网格, 2, 1)
        
        内容布局.addLayout(状态网格)
    
    def _创建状态项(self, 标题: str, 初始值: str, 网格: QGridLayout, 
                   行: int, 列: int) -> QLabel:
        """创建状态项"""
        容器 = QWidget()
        容器布局 = QHBoxLayout(容器)
        容器布局.setContentsMargins(0, 0, 0, 0)
        容器布局.setSpacing(4)
        
        标题标签 = QLabel(标题)
        标题标签.setStyleSheet(f"color: {颜色.次要文字}; font-size: {布局常量.次要文字字号}px;")
        容器布局.addWidget(标题标签)
        
        值标签 = QLabel(初始值)
        值标签.setStyleSheet(f"color: {颜色.文字}; font-size: {布局常量.正文字号}px; font-weight: 500;")
        容器布局.addWidget(值标签)
        容器布局.addStretch()
        
        网格.addWidget(容器, 行, 列)
        return 值标签
    
    def 更新运行状态(self, 状态: str) -> None:
        """更新运行状态显示"""
        颜色映射 = {
            "运行中": 颜色.成功,
            "已暂停": 颜色.警告,
            "已停止": 颜色.次要文字,
            "倒计时": 颜色.主色,
            "准备中": 颜色.主色,
        }
        状态颜色 = 颜色映射.get(状态, 颜色.文字)
        self._运行状态标签.setText(状态)
        self._运行状态标签.setStyleSheet(f"color: {状态颜色}; font-size: {布局常量.正文字号}px; font-weight: 500;")
    
    def 更新当前动作(self, 动作: str) -> None:
        """更新当前动作显示"""
        self._当前动作标签.setText(动作)
    
    def 更新动作来源(self, 来源: str) -> None:
        """更新动作来源显示"""
        来源映射 = {
            "model": "模型预测",
            "rule": "规则决策",
            "mixed": "混合决策",
            "fallback": "降级模式",
        }
        显示文本 = 来源映射.get(来源, 来源)
        self._动作来源标签.setText(显示文本)

    def 更新游戏状态(self, 状态: str) -> None:
        """更新游戏状态显示"""
        颜色映射 = {
            "战斗": 颜色.错误,
            "对话": 颜色.主色,
            "移动": 颜色.成功,
            "空闲": 颜色.次要文字,
            "死亡": 颜色.错误,
            "加载": 颜色.警告,
            "未知": 颜色.次要文字,
        }
        状态颜色 = 颜色映射.get(状态, 颜色.文字)
        self._游戏状态标签.setText(状态)
        self._游戏状态标签.setStyleSheet(f"color: {状态颜色}; font-size: {布局常量.正文字号}px; font-weight: 500;")
    
    def 更新帧率(self, 帧率: float) -> None:
        """更新帧率显示"""
        # 根据帧率设置颜色
        if 帧率 >= 25:
            帧率颜色 = 颜色.成功
        elif 帧率 >= 15:
            帧率颜色 = 颜色.警告
        else:
            帧率颜色 = 颜色.错误
        
        self._帧率标签.setText(f"{帧率:.1f} FPS")
        self._帧率标签.setStyleSheet(f"color: {帧率颜色}; font-size: {布局常量.正文字号}px; font-weight: 500;")
    
    def 更新运动量(self, 运动量: float) -> None:
        """更新运动量显示"""
        self._运动量标签.setText(f"{运动量:.1f}")
    
    def 重置(self) -> None:
        """重置所有状态显示"""
        self.更新运行状态("已停止")
        self.更新当前动作("无")
        self.更新动作来源("-")
        self.更新游戏状态("未知")
        self.更新帧率(0)
        self.更新运动量(0)


class 运行日志卡片(Card):
    """运行日志显示卡片组件"""
    
    def __init__(self, parent=None):
        super().__init__("📝 运行日志", "", parent)
        self._初始化内容()
    
    def _初始化内容(self) -> None:
        """初始化卡片内容"""
        内容布局 = self.获取内容布局()
        
        # 日志文本框
        self._日志文本框 = QTextEdit()
        self._日志文本框.setReadOnly(True)
        self._日志文本框.setStyleSheet(f"""
            QTextEdit {{
                background-color: {颜色.背景};
                border: 1px solid {颜色.边框};
                border-radius: 4px;
                font-family: Consolas, Monaco, monospace;
                font-size: {布局常量.次要文字字号}px;
                color: {颜色.文字};
                padding: 4px;
            }}
        """)
        self._日志文本框.setMinimumHeight(120)
        内容布局.addWidget(self._日志文本框)
    
    def 添加日志(self, 消息: str, 级别: str = "info") -> None:
        """添加日志消息"""
        时间戳 = datetime.now().strftime("%H:%M:%S")
        
        颜色映射 = {
            "info": 颜色.文字,
            "success": 颜色.成功,
            "warning": 颜色.警告,
            "error": 颜色.错误,
        }
        消息颜色 = 颜色映射.get(级别, 颜色.文字)
        
        格式化消息 = f'<span style="color: {颜色.次要文字}">[{时间戳}]</span> <span style="color: {消息颜色}">{消息}</span>'
        self._日志文本框.append(格式化消息)
        
        # 滚动到底部
        光标 = self._日志文本框.textCursor()
        光标.movePosition(QTextCursor.End)
        self._日志文本框.setTextCursor(光标)
    
    def 清空日志(self) -> None:
        """清空日志"""
        self._日志文本框.clear()


class 脱困提示(QFrame):
    """脱困提示组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._初始化界面()
        self.hide()  # 默认隐藏
    
    def _初始化界面(self) -> None:
        """初始化界面"""
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {颜色.警告};
                border-radius: {布局常量.卡片圆角}px;
                border: none;
            }}
        """)
        
        布局 = QHBoxLayout(self)
        布局.setContentsMargins(布局常量.卡片内边距, 8, 布局常量.卡片内边距, 8)
        布局.setSpacing(8)
        
        图标 = QLabel("⚠️")
        图标.setStyleSheet(f"font-size: {布局常量.页面标题字号}px;")
        布局.addWidget(图标)
        
        self._提示文本 = QLabel("检测到角色可能卡住，正在执行脱困动作...")
        self._提示文本.setStyleSheet(f"color: white; font-size: {布局常量.正文字号}px; font-weight: 500;")
        布局.addWidget(self._提示文本, 1)
    
    def 显示提示(self, 消息: str = None) -> None:
        """显示脱困提示"""
        if 消息:
            self._提示文本.setText(消息)
        self.show()
    
    def 隐藏提示(self) -> None:
        """隐藏脱困提示"""
        self.hide()


class 运行页(QWidget):
    """
    运行页面 (Requirements 4.1-4.5)
    
    提供机器人运行功能的完整界面，包括模式选择、控制面板和状态监控。
    支持基础模式和增强模式运行。
    
    布局结构:
    - 左右两栏布局，左栏占50%宽度，右栏占50%宽度
    - 左栏：运行模式卡片 + 增强模块状态卡片
    - 右栏：运行状态卡片 + 运行日志卡片
    """
    
    # 信号定义
    启动运行 = Signal(str, str, bool)  # 子模式, 运行模式, 是否增强
    暂停运行 = Signal()
    停止运行 = Signal()
    
    def __init__(self, parent=None):
        """初始化运行页面"""
        super().__init__(parent)
        
        # 状态
        self._运行中 = False
        self._已暂停 = False
        self._倒计时 = 0
        self._倒计时定时器: Optional[QTimer] = None
        
        # 状态更新节流器（最小更新间隔50ms）
        self._状态节流器 = 状态更新节流器(最小间隔ms=50, parent=self)
        self._状态节流器.设置回调(self._执行状态更新)
        
        self._初始化界面()
    
    def _初始化界面(self) -> None:
        """初始化界面布局 (Requirements 4.1)"""
        主布局 = QVBoxLayout(self)
        主布局.setContentsMargins(
            布局常量.内容区外边距,
            布局常量.内容区外边距,
            布局常量.内容区外边距,
            布局常量.内容区外边距
        )
        主布局.setSpacing(布局常量.卡片间距)

        # 页面标题
        标题 = QLabel("🤖 机器人运行")
        标题.setStyleSheet(f"""
            font-size: {布局常量.页面标题字号}px;
            font-weight: bold;
            color: {颜色.标题};
        """)
        主布局.addWidget(标题)
        
        # 脱困提示 (默认隐藏)
        self._脱困提示 = 脱困提示()
        主布局.addWidget(self._脱困提示)
        
        # 内容区域 - 左右两栏布局 (50:50) (Requirements 4.1)
        内容容器 = QWidget()
        内容布局 = QHBoxLayout(内容容器)
        内容布局.setContentsMargins(0, 0, 0, 0)
        内容布局.setSpacing(布局常量.卡片间距)
        
        # 左栏 (50%) - 运行模式卡片 + 增强模块状态卡片 (Requirements 4.2)
        左栏 = QWidget()
        左栏布局 = QVBoxLayout(左栏)
        左栏布局.setContentsMargins(0, 0, 0, 0)
        左栏布局.setSpacing(布局常量.卡片间距)
        
        # 运行模式卡片
        self._运行模式卡片 = 运行模式卡片()
        self._运行模式卡片.启动点击.connect(self._处理启动)
        self._运行模式卡片.暂停点击.connect(self._处理暂停)
        self._运行模式卡片.停止点击.connect(self._处理停止)
        左栏布局.addWidget(self._运行模式卡片)
        
        # 增强模块状态卡片 (Requirements 4.5)
        self._增强模块状态卡片 = 增强模块状态卡片()
        左栏布局.addWidget(self._增强模块状态卡片)
        
        左栏布局.addStretch()
        内容布局.addWidget(左栏, 布局常量.运行页左栏比例)
        
        # 右栏 (50%) - 运行状态卡片 + 运行日志卡片 (Requirements 4.3, 4.4)
        右栏 = QWidget()
        右栏布局 = QVBoxLayout(右栏)
        右栏布局.setContentsMargins(0, 0, 0, 0)
        右栏布局.setSpacing(布局常量.卡片间距)
        
        # 运行状态卡片 (Requirements 4.4)
        self._运行状态卡片 = 运行状态卡片()
        右栏布局.addWidget(self._运行状态卡片)
        
        # 运行日志卡片
        self._运行日志卡片 = 运行日志卡片()
        右栏布局.addWidget(self._运行日志卡片, 1)
        
        内容布局.addWidget(右栏, 布局常量.运行页右栏比例)
        
        主布局.addWidget(内容容器, 1)

    def _处理启动(self) -> None:
        """处理启动运行"""
        # 开始倒计时
        self._倒计时 = 4
        self._运行状态卡片.更新运行状态(f"倒计时 {self._倒计时}...")
        self._运行模式卡片.设置运行状态(True, False)
        self._运行日志卡片.添加日志("准备启动运行...", "info")
        
        # 创建倒计时定时器
        self._倒计时定时器 = QTimer(self)
        self._倒计时定时器.timeout.connect(self._更新倒计时)
        self._倒计时定时器.start(1000)
    
    def _更新倒计时(self) -> None:
        """更新倒计时"""
        self._倒计时 -= 1
        
        if self._倒计时 > 0:
            self._运行状态卡片.更新运行状态(f"倒计时 {self._倒计时}...")
        else:
            # 倒计时结束，开始运行
            if self._倒计时定时器:
                self._倒计时定时器.stop()
                self._倒计时定时器 = None
            
            self._运行中 = True
            self._已暂停 = False
            self._运行状态卡片.更新运行状态("运行中")
            
            # 发送启动运行信号
            子模式 = self._运行模式卡片.获取子模式()
            运行模式 = self._运行模式卡片.获取运行模式()
            是否增强 = self._运行模式卡片.是否增强模式()
            
            self._运行日志卡片.添加日志(f"启动运行 - 模式: {运行模式}, 任务: {子模式}", "success")
            self.启动运行.emit(子模式, 运行模式, 是否增强)
    
    def _处理暂停(self) -> None:
        """处理暂停/继续"""
        if self._运行中:
            self._已暂停 = not self._已暂停
            self._运行模式卡片.设置运行状态(True, self._已暂停)
            
            if self._已暂停:
                self._运行状态卡片.更新运行状态("已暂停")
                self._运行日志卡片.添加日志("运行已暂停", "warning")
            else:
                self._运行状态卡片.更新运行状态("运行中")
                self._运行日志卡片.添加日志("运行已继续", "info")
            
            self.暂停运行.emit()
    
    def _处理停止(self) -> None:
        """处理停止运行"""
        # 停止倒计时定时器
        if self._倒计时定时器:
            self._倒计时定时器.stop()
            self._倒计时定时器 = None
        
        self._运行中 = False
        self._已暂停 = False
        self._倒计时 = 0
        
        self._运行模式卡片.设置运行状态(False, False)
        self._运行状态卡片.重置()
        self._增强模块状态卡片.重置()
        self._脱困提示.隐藏提示()
        
        self._运行日志卡片.添加日志("运行已停止", "info")
        self.停止运行.emit()

    @Slot(dict)
    def 更新状态(self, 状态数据: dict) -> None:
        """
        更新状态显示（通过节流器）
        
        参数:
            状态数据: 包含状态信息的字典
                - 当前动作: str
                - 动作来源: str (model/rule/mixed/fallback)
                - 游戏状态: str
                - 帧率: float
                - 运动量: float
                - 增强模块: dict (YOLO/状态识别/决策引擎/脱困/自动调参/低性能)
        """
        # 使用节流器控制更新频率
        self._状态节流器.请求更新(状态数据)
    
    def _执行状态更新(self, 状态数据: dict) -> None:
        """
        实际执行状态更新（由节流器调用）
        
        参数:
            状态数据: 包含状态信息的字典
        """
        if "当前动作" in 状态数据:
            self._运行状态卡片.更新当前动作(状态数据["当前动作"])
        
        if "动作来源" in 状态数据:
            self._运行状态卡片.更新动作来源(状态数据["动作来源"])
        
        if "游戏状态" in 状态数据:
            self._运行状态卡片.更新游戏状态(状态数据["游戏状态"])
        
        if "帧率" in 状态数据:
            self._运行状态卡片.更新帧率(状态数据["帧率"])
        
        if "运动量" in 状态数据:
            self._运行状态卡片.更新运动量(状态数据["运动量"])
        
        if "增强模块" in 状态数据:
            self._增强模块状态卡片.更新模块状态(状态数据["增强模块"])
    
    def 显示脱困提示(self, 消息: str = None) -> None:
        """显示脱困提示"""
        self._脱困提示.显示提示(消息)
        self._运行日志卡片.添加日志(消息 or "检测到角色可能卡住，正在执行脱困动作...", "warning")
        
        # 3秒后自动隐藏
        QTimer.singleShot(3000, self._脱困提示.隐藏提示)
    
    def 显示性能警告(self, 帧率: float) -> None:
        """显示性能警告"""
        self._脱困提示._提示文本.setText(f"⚠️ 性能不足 (帧率: {帧率:.1f})，已降低检测频率")
        self._脱困提示.setStyleSheet(f"""
            QFrame {{
                background-color: {颜色.错误};
                border-radius: {布局常量.卡片圆角}px;
                border: none;
            }}
        """)
        self._脱困提示.show()
        self._运行日志卡片.添加日志(f"性能警告: 帧率 {帧率:.1f} FPS", "error")
        
        # 5秒后自动隐藏
        QTimer.singleShot(5000, self._脱困提示.隐藏提示)
    
    def 添加日志(self, 消息: str, 级别: str = "info") -> None:
        """添加运行日志"""
        self._运行日志卡片.添加日志(消息, 级别)
    
    def 处理快捷键暂停(self) -> None:
        """处理快捷键T暂停/继续"""
        if self._运行中:
            self._处理暂停()
    
    def 处理快捷键停止(self) -> None:
        """处理快捷键ESC停止"""
        if self._运行中 or self._倒计时 > 0:
            self._处理停止()
    
    def 是否运行中(self) -> bool:
        """返回是否正在运行"""
        return self._运行中
    
    def 是否已暂停(self) -> bool:
        """返回是否已暂停"""
        return self._已暂停

    def 获取运行模式卡片(self) -> 运行模式卡片:
        """获取运行模式卡片组件"""
        return self._运行模式卡片
    
    def 获取运行状态卡片(self) -> 运行状态卡片:
        """获取运行状态卡片组件"""
        return self._运行状态卡片
    
    def 获取增强模块状态卡片(self) -> 增强模块状态卡片:
        """获取增强模块状态卡片组件"""
        return self._增强模块状态卡片
    
    def 获取运行日志卡片(self) -> 运行日志卡片:
        """获取运行日志卡片组件"""
        return self._运行日志卡片
    
    # 兼容旧接口
    def 获取控制面板(self):
        """获取控制面板组件（兼容旧接口）"""
        return self._运行模式卡片
    
    def 获取状态监控(self):
        """获取状态监控组件（兼容旧接口）"""
        return self._运行状态卡片
    
    def 获取增强模块状态(self):
        """获取增强模块状态组件（兼容旧接口）"""
        return self._增强模块状态卡片


# 兼容旧代码的别名
运行控制面板 = 运行模式卡片
运行状态监控 = 运行状态卡片
增强模块状态 = 增强模块状态卡片
