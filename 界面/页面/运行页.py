# -*- coding: utf-8 -*-
"""
运行页面

提供机器人运行功能的图形界面，包括模式选择、控制面板和状态监控。
支持基础模式和增强模式运行。
"""

from typing import Optional, Dict
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QGridLayout, QComboBox,
    QSizePolicy, QGroupBox, QCheckBox
)
from PySide6.QtCore import Signal, Slot, Qt, QTimer
from PySide6.QtGui import QImage, QPixmap

import numpy as np

from 界面.样式.主题 import 颜色


class 运行控制面板(QFrame):
    """运行控制面板组件"""
    
    # 信号定义
    启动点击 = Signal()
    暂停点击 = Signal()
    停止点击 = Signal()
    运行模式改变 = Signal(str)
    子模式改变 = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("class", "card")
        self.setMinimumWidth(380)  # 设置最小宽度确保内容不被截断
        self._初始化界面()
    
    def _初始化界面(self) -> None:
        """初始化界面"""
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {颜色.卡片背景};
                border-radius: 12px;
                border: 1px solid {颜色.边框};
            }}
            QComboBox {{
                padding: 8px 12px;
                min-width: 160px;
            }}
        """)
        
        布局 = QVBoxLayout(self)
        布局.setContentsMargins(20, 16, 20, 16)
        布局.setSpacing(16)
        
        # 标题
        标题 = QLabel("🎮 运行控制")
        标题.setStyleSheet(f"""
            font-size: 16px;
            font-weight: bold;
            color: {颜色.标题};
        """)
        布局.addWidget(标题)
        
        # 运行模式选择
        运行模式容器 = QWidget()
        运行模式布局 = QHBoxLayout(运行模式容器)
        运行模式布局.setContentsMargins(0, 0, 0, 0)
        运行模式布局.setSpacing(12)
        
        运行模式标签 = QLabel("运行模式:")
        运行模式标签.setStyleSheet(f"color: {颜色.文字}; font-size: 13px;")
        运行模式标签.setFixedWidth(70)
        运行模式布局.addWidget(运行模式标签)
        
        self._运行模式选择 = QComboBox()
        self._运行模式选择.addItems(["基础模式", "增强模式"])
        self._运行模式选择.setFixedWidth(200)
        self._运行模式选择.setFixedHeight(36)
        self._运行模式选择.setStyleSheet(f"""
            QComboBox {{
                padding-left: 12px;
                padding-right: 30px;
                font-size: 13px;
            }}
        """)
        self._运行模式选择.currentTextChanged.connect(self.运行模式改变.emit)
        运行模式布局.addWidget(self._运行模式选择)
        运行模式布局.addStretch()
        
        布局.addWidget(运行模式容器)
        
        # 子模式选择
        子模式容器 = QWidget()
        子模式布局 = QHBoxLayout(子模式容器)
        子模式布局.setContentsMargins(0, 0, 0, 0)
        子模式布局.setSpacing(12)
        
        子模式标签 = QLabel("任务模式:")
        子模式标签.setStyleSheet(f"color: {颜色.文字}; font-size: 13px;")
        子模式标签.setFixedWidth(70)
        子模式布局.addWidget(子模式标签)
        
        self._子模式选择 = QComboBox()
        self._子模式选择.addItems(["主线任务", "自动战斗"])
        self._子模式选择.setFixedWidth(200)
        self._子模式选择.setFixedHeight(36)
        self._子模式选择.setStyleSheet(f"""
            QComboBox {{
                padding-left: 12px;
                padding-right: 30px;
                font-size: 13px;
            }}
        """)
        self._子模式选择.currentTextChanged.connect(self.子模式改变.emit)
        子模式布局.addWidget(self._子模式选择)
        子模式布局.addStretch()
        
        布局.addWidget(子模式容器)
        
        # 按钮容器
        按钮容器 = QWidget()
        按钮布局 = QHBoxLayout(按钮容器)
        按钮布局.setContentsMargins(0, 0, 0, 0)
        按钮布局.setSpacing(8)
        
        # 启动按钮
        self._启动按钮 = QPushButton("🚀 启动")
        self._启动按钮.setFixedSize(80, 36)
        self._启动按钮.setCursor(Qt.PointingHandCursor)
        self._启动按钮.setStyleSheet(f"""
            QPushButton {{
                background-color: {颜色.成功};
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 13px;
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
        self._暂停按钮.setFixedSize(80, 36)
        self._暂停按钮.setCursor(Qt.PointingHandCursor)
        self._暂停按钮.setEnabled(False)
        self._暂停按钮.setStyleSheet(f"""
            QPushButton {{
                background-color: {颜色.警告};
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 13px;
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
        self._停止按钮.setFixedSize(80, 36)
        self._停止按钮.setCursor(Qt.PointingHandCursor)
        self._停止按钮.setEnabled(False)
        self._停止按钮.setStyleSheet(f"""
            QPushButton {{
                background-color: {颜色.错误};
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 13px;
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
        布局.addWidget(按钮容器)
        
        # 快捷键提示
        提示 = QLabel("💡 快捷键: T 暂停/继续, ESC 停止")
        提示.setStyleSheet(f"color: {颜色.次要文字}; font-size: 12px;")
        布局.addWidget(提示)
    
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



class 运行状态监控(QFrame):
    """运行状态监控组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("class", "card")
        self._初始化界面()
    
    def _初始化界面(self) -> None:
        """初始化界面"""
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {颜色.卡片背景};
                border-radius: 12px;
                border: 1px solid {颜色.边框};
            }}
        """)
        
        布局 = QVBoxLayout(self)
        布局.setContentsMargins(16, 12, 16, 12)
        布局.setSpacing(8)
        
        # 标题
        标题 = QLabel("📊 状态监控")
        标题.setStyleSheet(f"""
            font-size: 14px;
            font-weight: bold;
            color: {颜色.标题};
        """)
        布局.addWidget(标题)
        
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
        
        布局.addLayout(状态网格)
    
    def _创建状态项(self, 标题: str, 初始值: str, 网格: QGridLayout, 
                   行: int, 列: int) -> QLabel:
        """创建状态项"""
        容器 = QWidget()
        容器布局 = QHBoxLayout(容器)
        容器布局.setContentsMargins(0, 0, 0, 0)
        容器布局.setSpacing(4)
        
        标题标签 = QLabel(标题)
        标题标签.setStyleSheet(f"color: {颜色.次要文字}; font-size: 12px;")
        容器布局.addWidget(标题标签)
        
        值标签 = QLabel(初始值)
        值标签.setStyleSheet(f"color: {颜色.文字}; font-size: 12px; font-weight: 500;")
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
        self._运行状态标签.setStyleSheet(f"color: {状态颜色}; font-size: 13px; font-weight: 500;")
    
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
        self._游戏状态标签.setStyleSheet(f"color: {状态颜色}; font-size: 13px; font-weight: 500;")
    
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
        self._帧率标签.setStyleSheet(f"color: {帧率颜色}; font-size: 13px; font-weight: 500;")
    
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


class 增强模块状态(QFrame):
    """增强模块状态显示组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("class", "card")
        self._初始化界面()
    
    def _初始化界面(self) -> None:
        """初始化界面"""
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {颜色.卡片背景};
                border-radius: 12px;
                border: 1px solid {颜色.边框};
            }}
        """)
        
        布局 = QVBoxLayout(self)
        布局.setContentsMargins(16, 12, 16, 12)
        布局.setSpacing(8)
        
        # 标题
        标题 = QLabel("🔧 增强模块状态")
        标题.setStyleSheet(f"""
            font-size: 14px;
            font-weight: bold;
            color: {颜色.标题};
        """)
        布局.addWidget(标题)
        
        # 模块状态网格
        模块网格 = QGridLayout()
        模块网格.setSpacing(6)
        
        # YOLO检测器
        self._YOLO状态 = self._创建模块状态项("YOLO检测器:", 模块网格, 0)
        
        # 状态识别器
        self._状态识别状态 = self._创建模块状态项("状态识别器:", 模块网格, 1)
        
        # 决策引擎
        self._决策引擎状态 = self._创建模块状态项("决策引擎:", 模块网格, 2)
        
        布局.addLayout(模块网格)
        
        # 性能模式
        性能容器 = QWidget()
        性能布局 = QHBoxLayout(性能容器)
        性能布局.setContentsMargins(0, 4, 0, 0)
        性能布局.setSpacing(6)
        
        性能标签 = QLabel("性能模式:")
        性能标签.setStyleSheet(f"color: {颜色.次要文字}; font-size: 12px;")
        性能布局.addWidget(性能标签)
        
        self._性能模式标签 = QLabel("正常")
        self._性能模式标签.setStyleSheet(f"color: {颜色.成功}; font-size: 12px; font-weight: 500;")
        性能布局.addWidget(self._性能模式标签)
        性能布局.addStretch()
        
        布局.addWidget(性能容器)
    
    def _创建模块状态项(self, 标题: str, 网格: QGridLayout, 行: int) -> QLabel:
        """创建模块状态项"""
        容器 = QWidget()
        容器布局 = QHBoxLayout(容器)
        容器布局.setContentsMargins(0, 0, 0, 0)
        容器布局.setSpacing(8)
        
        标题标签 = QLabel(标题)
        标题标签.setStyleSheet(f"color: {颜色.次要文字}; font-size: 13px;")
        标题标签.setFixedWidth(90)
        容器布局.addWidget(标题标签)
        
        状态标签 = QLabel("未加载")
        状态标签.setStyleSheet(f"color: {颜色.次要文字}; font-size: 13px;")
        容器布局.addWidget(状态标签)
        容器布局.addStretch()
        
        网格.addWidget(容器, 行, 0)
        return 状态标签
    
    def 更新YOLO状态(self, 可用: bool) -> None:
        """更新YOLO检测器状态"""
        if 可用:
            self._YOLO状态.setText("✅ 已加载")
            self._YOLO状态.setStyleSheet(f"color: {颜色.成功}; font-size: 13px;")
        else:
            self._YOLO状态.setText("❌ 不可用")
            self._YOLO状态.setStyleSheet(f"color: {颜色.错误}; font-size: 13px;")
    
    def 更新状态识别状态(self, 可用: bool) -> None:
        """更新状态识别器状态"""
        if 可用:
            self._状态识别状态.setText("✅ 已加载")
            self._状态识别状态.setStyleSheet(f"color: {颜色.成功}; font-size: 13px;")
        else:
            self._状态识别状态.setText("❌ 不可用")
            self._状态识别状态.setStyleSheet(f"color: {颜色.错误}; font-size: 13px;")
    
    def 更新决策引擎状态(self, 可用: bool) -> None:
        """更新决策引擎状态"""
        if 可用:
            self._决策引擎状态.setText("✅ 已加载")
            self._决策引擎状态.setStyleSheet(f"color: {颜色.成功}; font-size: 13px;")
        else:
            self._决策引擎状态.setText("❌ 不可用")
            self._决策引擎状态.setStyleSheet(f"color: {颜色.错误}; font-size: 13px;")
    
    def 更新性能模式(self, 低性能: bool) -> None:
        """更新性能模式显示"""
        if 低性能:
            self._性能模式标签.setText("⚠️ 低性能")
            self._性能模式标签.setStyleSheet(f"color: {颜色.警告}; font-size: 13px; font-weight: 500;")
        else:
            self._性能模式标签.setText("✅ 正常")
            self._性能模式标签.setStyleSheet(f"color: {颜色.成功}; font-size: 13px; font-weight: 500;")
    
    def 更新模块状态(self, 状态数据: Dict[str, bool]) -> None:
        """批量更新模块状态"""
        if "YOLO" in 状态数据:
            self.更新YOLO状态(状态数据["YOLO"])
        if "状态识别" in 状态数据:
            self.更新状态识别状态(状态数据["状态识别"])
        if "决策引擎" in 状态数据:
            self.更新决策引擎状态(状态数据["决策引擎"])
        if "低性能" in 状态数据:
            self.更新性能模式(状态数据["低性能"])
    
    def 重置(self) -> None:
        """重置所有状态"""
        self._YOLO状态.setText("未加载")
        self._YOLO状态.setStyleSheet(f"color: {颜色.次要文字}; font-size: 13px;")
        self._状态识别状态.setText("未加载")
        self._状态识别状态.setStyleSheet(f"color: {颜色.次要文字}; font-size: 13px;")
        self._决策引擎状态.setText("未加载")
        self._决策引擎状态.setStyleSheet(f"color: {颜色.次要文字}; font-size: 13px;")
        self._性能模式标签.setText("正常")
        self._性能模式标签.setStyleSheet(f"color: {颜色.成功}; font-size: 13px; font-weight: 500;")


class 自动调参面板(QFrame):
    """自动调参控制面板组件 (需求 9.1, 9.2)
    
    提供自动调参功能的控制界面，包括：
    - 启用/禁用开关 (需求 9.1)
    - 激进程度选择 (需求 9.2)
    - 参数锁定控件
    - 重置为默认值按钮
    """
    
    # 信号定义
    启用状态改变 = Signal(bool)
    激进程度改变 = Signal(str)
    参数锁定改变 = Signal(str, bool)  # 参数名, 是否锁定
    重置参数 = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("class", "card")
        self._自动调参器 = None
        self._参数锁定控件 = {}  # 存储参数锁定复选框
        self._初始化自动调参器()
        self._初始化界面()
    
    def _初始化自动调参器(self):
        """初始化自动调参器"""
        try:
            from 核心.自动调参 import AutoTuner, AggressivenessLevel
            self._自动调参器 = AutoTuner(enabled=False)
            self._激进程度枚举 = AggressivenessLevel
        except Exception as e:
            print(f"初始化自动调参器失败: {e}")
            self._自动调参器 = None
            self._激进程度枚举 = None
    
    def _初始化界面(self) -> None:
        """初始化界面"""
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {颜色.卡片背景};
                border-radius: 12px;
                border: 1px solid {颜色.边框};
            }}
        """)
        
        布局 = QVBoxLayout(self)
        布局.setContentsMargins(16, 12, 16, 12)
        布局.setSpacing(10)
        
        # 标题行
        标题行 = QHBoxLayout()
        标题 = QLabel("🎯 自动调参")
        标题.setStyleSheet(f"""
            font-size: 14px;
            font-weight: bold;
            color: {颜色.标题};
        """)
        标题行.addWidget(标题)
        标题行.addStretch()
        
        # 启用/禁用开关 (需求 9.1)
        self._启用开关 = QCheckBox("启用")
        self._启用开关.setStyleSheet(f"""
            QCheckBox {{
                color: {颜色.文字};
                font-size: 12px;
                spacing: 6px;
            }}
        """)
        self._启用开关.stateChanged.connect(self._处理启用状态改变)
        标题行.addWidget(self._启用开关)
        
        布局.addLayout(标题行)
        
        # 激进程度选择 (需求 9.2)
        激进程度容器 = QWidget()
        激进程度布局 = QHBoxLayout(激进程度容器)
        激进程度布局.setContentsMargins(0, 0, 0, 0)
        激进程度布局.setSpacing(8)
        
        激进程度标签 = QLabel("调参力度:")
        激进程度标签.setStyleSheet(f"color: {颜色.次要文字}; font-size: 12px;")
        激进程度标签.setFixedWidth(60)
        激进程度布局.addWidget(激进程度标签)
        
        self._激进程度选择 = QComboBox()
        self._激进程度选择.addItems(["保守", "平衡", "激进"])
        self._激进程度选择.setCurrentIndex(1)  # 默认平衡
        self._激进程度选择.setFixedHeight(28)
        self._激进程度选择.setStyleSheet(f"""
            QComboBox {{
                padding-left: 8px;
                font-size: 12px;
            }}
        """)
        self._激进程度选择.currentTextChanged.connect(self._处理激进程度改变)
        激进程度布局.addWidget(self._激进程度选择, 1)
        
        布局.addWidget(激进程度容器)
        
        # 参数锁定区域
        锁定标签 = QLabel("参数锁定:")
        锁定标签.setStyleSheet(f"color: {颜色.次要文字}; font-size: 12px; margin-top: 4px;")
        布局.addWidget(锁定标签)
        
        # 参数锁定网格
        锁定网格 = QGridLayout()
        锁定网格.setSpacing(4)
        锁定网格.setContentsMargins(0, 0, 0, 0)
        
        # 创建参数锁定复选框
        参数列表 = [
            ("action_cooldown", "动作冷却"),
            ("state_switch_threshold", "状态切换"),
            ("rule_priority_weight", "规则权重"),
            ("detection_confidence_threshold", "检测置信度"),
        ]
        
        for 索引, (参数名, 显示名) in enumerate(参数列表):
            行 = 索引 // 2
            列 = 索引 % 2
            
            锁定框 = QCheckBox(显示名)
            锁定框.setStyleSheet(f"""
                QCheckBox {{
                    color: {颜色.文字};
                    font-size: 11px;
                    spacing: 4px;
                }}
            """)
            锁定框.stateChanged.connect(
                lambda state, name=参数名: self._处理参数锁定改变(name, state)
            )
            锁定网格.addWidget(锁定框, 行, 列)
            self._参数锁定控件[参数名] = 锁定框
        
        布局.addLayout(锁定网格)
        
        # 重置按钮
        self._重置按钮 = QPushButton("🔄 重置为默认值")
        self._重置按钮.setFixedHeight(28)
        self._重置按钮.setStyleSheet(f"""
            QPushButton {{
                background-color: {颜色.卡片背景};
                color: {颜色.文字};
                border: 1px solid {颜色.边框};
                border-radius: 6px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {颜色.悬停背景};
            }}
        """)
        self._重置按钮.clicked.connect(self._处理重置参数)
        布局.addWidget(self._重置按钮)
        
        # 初始化状态
        self._更新控件状态()
    
    def _处理启用状态改变(self, state: int) -> None:
        """处理启用状态改变"""
        启用 = state == Qt.Checked
        
        if self._自动调参器:
            self._自动调参器.enabled = 启用
        
        self._更新控件状态()
        self.启用状态改变.emit(启用)
    
    def _处理激进程度改变(self, 程度文本: str) -> None:
        """处理激进程度改变"""
        if not self._自动调参器 or not self._激进程度枚举:
            return
        
        程度映射 = {
            "保守": self._激进程度枚举.CONSERVATIVE,
            "平衡": self._激进程度枚举.BALANCED,
            "激进": self._激进程度枚举.AGGRESSIVE,
        }
        
        if 程度文本 in 程度映射:
            self._自动调参器.aggressiveness = 程度映射[程度文本]
            self.激进程度改变.emit(程度文本)
    
    def _处理参数锁定改变(self, 参数名: str, state: int) -> None:
        """处理参数锁定状态改变"""
        锁定 = state == Qt.Checked
        
        if self._自动调参器:
            try:
                if 锁定:
                    self._自动调参器.lock_parameter(参数名)
                else:
                    self._自动调参器.unlock_parameter(参数名)
            except ValueError as e:
                print(f"参数锁定操作失败: {e}")
        
        self.参数锁定改变.emit(参数名, 锁定)
    
    def _处理重置参数(self) -> None:
        """处理重置参数"""
        if self._自动调参器:
            self._自动调参器.reset_to_defaults()
        
        self.重置参数.emit()
    
    def _更新控件状态(self) -> None:
        """根据启用状态更新控件可用性"""
        启用 = self._启用开关.isChecked()
        
        self._激进程度选择.setEnabled(启用)
        self._重置按钮.setEnabled(启用)
        
        for 控件 in self._参数锁定控件.values():
            控件.setEnabled(启用)
    
    def 获取启用状态(self) -> bool:
        """获取自动调参是否启用"""
        return self._启用开关.isChecked()
    
    def 设置启用状态(self, 启用: bool) -> None:
        """设置自动调参启用状态"""
        self._启用开关.setChecked(启用)
    
    def 获取激进程度(self) -> str:
        """获取当前激进程度"""
        return self._激进程度选择.currentText()
    
    def 设置激进程度(self, 程度: str) -> None:
        """设置激进程度"""
        索引 = self._激进程度选择.findText(程度)
        if 索引 >= 0:
            self._激进程度选择.setCurrentIndex(索引)
    
    def 获取锁定参数列表(self) -> list:
        """获取所有被锁定的参数名称列表"""
        锁定列表 = []
        for 参数名, 控件 in self._参数锁定控件.items():
            if 控件.isChecked():
                锁定列表.append(参数名)
        return 锁定列表
    
    def 获取自动调参器(self):
        """获取自动调参器实例"""
        return self._自动调参器
    
    def 重置(self) -> None:
        """重置面板状态"""
        self._启用开关.setChecked(False)
        self._激进程度选择.setCurrentIndex(1)  # 平衡
        for 控件 in self._参数锁定控件.values():
            控件.setChecked(False)
        self._更新控件状态()



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
                border-radius: 8px;
                border: none;
            }}
        """)
        
        布局 = QHBoxLayout(self)
        布局.setContentsMargins(16, 10, 16, 10)
        布局.setSpacing(8)
        
        图标 = QLabel("⚠️")
        图标.setStyleSheet("font-size: 16px;")
        布局.addWidget(图标)
        
        self._提示文本 = QLabel("检测到角色可能卡住，正在执行脱困动作...")
        self._提示文本.setStyleSheet("color: white; font-size: 13px; font-weight: 500;")
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
    运行页面
    
    提供机器人运行功能的完整界面，包括模式选择、控制面板和状态监控。
    支持基础模式和增强模式运行。
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
        
        self._初始化界面()
    
    def _初始化界面(self) -> None:
        """初始化界面布局"""
        主布局 = QVBoxLayout(self)
        主布局.setContentsMargins(24, 24, 24, 24)
        主布局.setSpacing(16)
        
        # 页面标题
        标题 = QLabel("🤖 机器人运行")
        标题.setStyleSheet(f"""
            font-size: 22px;
            font-weight: bold;
            color: {颜色.标题};
        """)
        主布局.addWidget(标题)
        
        # 脱困提示 (默认隐藏)
        self._脱困提示 = 脱困提示()
        主布局.addWidget(self._脱困提示)
        
        # 内容区域 (左右布局)
        内容容器 = QWidget()
        内容布局 = QHBoxLayout(内容容器)
        内容布局.setContentsMargins(0, 0, 0, 0)
        内容布局.setSpacing(16)
        
        # 左侧: 控制面板和状态监控
        左侧容器 = QWidget()
        左侧布局 = QVBoxLayout(左侧容器)
        左侧布局.setContentsMargins(0, 0, 0, 0)
        左侧布局.setSpacing(12)
        
        # 控制面板（包含状态监控）
        self._控制面板 = 运行控制面板()
        self._控制面板.启动点击.connect(self._处理启动)
        self._控制面板.暂停点击.connect(self._处理暂停)
        self._控制面板.停止点击.connect(self._处理停止)
        左侧布局.addWidget(self._控制面板)
        
        # 状态监控（紧凑版）
        self._状态监控 = 运行状态监控()
        左侧布局.addWidget(self._状态监控)
        
        左侧布局.addStretch()
        内容布局.addWidget(左侧容器, 2)  # 左侧占2份
        
        # 右侧: 增强模块状态和自动调参面板
        右侧容器 = QWidget()
        右侧布局 = QVBoxLayout(右侧容器)
        右侧布局.setContentsMargins(0, 0, 0, 0)
        右侧布局.setSpacing(12)
        
        # 增强模块状态
        self._增强模块状态 = 增强模块状态()
        右侧布局.addWidget(self._增强模块状态)
        
        # 自动调参面板 (需求 9.1, 9.2)
        self._自动调参面板 = 自动调参面板()
        右侧布局.addWidget(self._自动调参面板)
        
        右侧布局.addStretch()
        右侧容器.setFixedWidth(200)  # 固定右侧宽度
        内容布局.addWidget(右侧容器)
        
        主布局.addWidget(内容容器, 1)
        
        # 底部提示卡片
        提示卡片 = QFrame()
        提示卡片.setStyleSheet(f"""
            QFrame {{
                background-color: {颜色.选中背景};
                border-radius: 12px;
                border: 1px solid {颜色.边框};
            }}
        """)
        提示布局 = QVBoxLayout(提示卡片)
        提示布局.setContentsMargins(16, 12, 16, 12)
        提示布局.setSpacing(8)
        
        提示标题 = QLabel("📋 运行说明")
        提示标题.setStyleSheet(f"color: {颜色.标题}; font-size: 14px; font-weight: 500;")
        提示布局.addWidget(提示标题)
        
        提示内容 = QLabel(
            "• 基础模式: 使用训练好的模型进行模仿学习\n"
            "• 增强模式: 集成YOLO检测、状态识别和智能决策引擎\n"
            "• 自动调参: 根据运行表现自动优化参数\n"
            "• 运行前请确保已训练好模型，并切换到游戏窗口"
        )
        提示内容.setStyleSheet(f"color: {颜色.文字}; font-size: 12px;")
        提示内容.setWordWrap(True)
        提示布局.addWidget(提示内容)
        
        主布局.addWidget(提示卡片)
    
    def _处理启动(self) -> None:
        """处理启动运行"""
        # 开始倒计时
        self._倒计时 = 4
        self._状态监控.更新运行状态(f"倒计时 {self._倒计时}...")
        self._控制面板.设置运行状态(True, False)
        
        # 创建倒计时定时器
        self._倒计时定时器 = QTimer(self)
        self._倒计时定时器.timeout.connect(self._更新倒计时)
        self._倒计时定时器.start(1000)
    
    def _更新倒计时(self) -> None:
        """更新倒计时"""
        self._倒计时 -= 1
        
        if self._倒计时 > 0:
            self._状态监控.更新运行状态(f"倒计时 {self._倒计时}...")
        else:
            # 倒计时结束，开始运行
            if self._倒计时定时器:
                self._倒计时定时器.stop()
                self._倒计时定时器 = None
            
            self._运行中 = True
            self._已暂停 = False
            self._状态监控.更新运行状态("运行中")
            
            # 发送启动运行信号
            子模式 = self._控制面板.获取子模式()
            运行模式 = self._控制面板.获取运行模式()
            是否增强 = self._控制面板.是否增强模式()
            self.启动运行.emit(子模式, 运行模式, 是否增强)
    
    def _处理暂停(self) -> None:
        """处理暂停/继续"""
        if self._运行中:
            self._已暂停 = not self._已暂停
            self._控制面板.设置运行状态(True, self._已暂停)
            
            if self._已暂停:
                self._状态监控.更新运行状态("已暂停")
            else:
                self._状态监控.更新运行状态("运行中")
            
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
        
        self._控制面板.设置运行状态(False, False)
        self._状态监控.重置()
        self._增强模块状态.重置()
        self._自动调参面板.重置()
        self._脱困提示.隐藏提示()
        
        self.停止运行.emit()
    
    @Slot(dict)
    def 更新状态(self, 状态数据: dict) -> None:
        """
        更新状态显示
        
        参数:
            状态数据: 包含状态信息的字典
                - 当前动作: str
                - 动作来源: str (model/rule/mixed/fallback)
                - 游戏状态: str
                - 帧率: float
                - 运动量: float
                - 增强模块: dict (YOLO/状态识别/决策引擎/低性能)
        """
        if "当前动作" in 状态数据:
            self._状态监控.更新当前动作(状态数据["当前动作"])
        
        if "动作来源" in 状态数据:
            self._状态监控.更新动作来源(状态数据["动作来源"])
        
        if "游戏状态" in 状态数据:
            self._状态监控.更新游戏状态(状态数据["游戏状态"])
        
        if "帧率" in 状态数据:
            self._状态监控.更新帧率(状态数据["帧率"])
        
        if "运动量" in 状态数据:
            self._状态监控.更新运动量(状态数据["运动量"])
        
        if "增强模块" in 状态数据:
            self._增强模块状态.更新模块状态(状态数据["增强模块"])
    
    def 显示脱困提示(self, 消息: str = None) -> None:
        """显示脱困提示"""
        self._脱困提示.显示提示(消息)
        
        # 3秒后自动隐藏
        QTimer.singleShot(3000, self._脱困提示.隐藏提示)
    
    def 显示性能警告(self, 帧率: float) -> None:
        """显示性能警告"""
        self._脱困提示._提示文本.setText(f"⚠️ 性能不足 (帧率: {帧率:.1f})，已降低检测频率")
        self._脱困提示.setStyleSheet(f"""
            QFrame {{
                background-color: {颜色.错误};
                border-radius: 8px;
                border: none;
            }}
        """)
        self._脱困提示.show()
        
        # 5秒后自动隐藏
        QTimer.singleShot(5000, self._脱困提示.隐藏提示)
    
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
    
    def 获取控制面板(self) -> 运行控制面板:
        """获取控制面板组件"""
        return self._控制面板
    
    def 获取状态监控(self) -> 运行状态监控:
        """获取状态监控组件"""
        return self._状态监控
    
    def 获取增强模块状态(self) -> 增强模块状态:
        """获取增强模块状态组件"""
        return self._增强模块状态
    
    def 获取自动调参面板(self) -> 自动调参面板:
        """获取自动调参面板组件"""
        return self._自动调参面板
