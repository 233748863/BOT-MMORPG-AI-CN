# -*- coding: utf-8 -*-
"""
自定义标题栏组件

实现无边框窗口的自定义标题栏，包含:
- 应用图标和标题
- 配置按钮（打开配置界面对话框）
- 最小化、最大化、关闭按钮
- 窗口拖动功能

设计规范:
- 标题栏高度: 36px
- 背景颜色: 深蓝色 #1E3A5F (与UI风格搭配)
- 按钮宽度: 46px
- 按钮悬停: 半透明白色
- 关闭按钮悬停: 红色 #E81123

需求: 1.1 - 配置界面入口
"""

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QPushButton, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtGui import QMouseEvent, QFont, QPainter, QColor


class 自定义标题栏(QWidget):
    """
    自定义标题栏组件
    
    提供窗口拖动、最小化、最大化/还原、关闭功能
    以及配置界面入口按钮
    """
    
    # 信号定义
    最小化请求 = Signal()
    最大化请求 = Signal()
    关闭请求 = Signal()
    配置请求 = Signal()  # 打开配置界面的信号
    
    def __init__(self, 父窗口: QWidget = None):
        """
        初始化自定义标题栏
        
        参数:
            父窗口: 父窗口组件（通常是主窗口）
        """
        super().__init__(父窗口)
        
        self._父窗口 = 父窗口
        self._拖动中 = False
        self._拖动起始位置 = QPoint()
        self._是否最大化 = False
        
        self._初始化UI()
        self._应用样式()
    
    def _初始化UI(self) -> None:
        """初始化UI布局"""
        # 设置固定高度
        self.setFixedHeight(36)
        
        # 设置对象名称用于样式选择器
        self.setObjectName("CustomTitleBar")
        
        # 主布局
        布局 = QHBoxLayout(self)
        布局.setContentsMargins(12, 0, 0, 0)
        布局.setSpacing(0)
        
        # 应用图标 - 使用游戏手柄 emoji
        self._图标标签 = QLabel()
        self._图标标签.setFixedSize(24, 24)
        self._图标标签.setAlignment(Qt.AlignCenter)
        self._图标标签.setText("🎮")
        图标字体 = QFont("Segoe UI Emoji", 14)
        self._图标标签.setFont(图标字体)
        self._图标标签.setStyleSheet("""
            background: transparent;
        """)
        布局.addWidget(self._图标标签)
        
        # 标题文字 - 使用明确的白色，确保在深蓝背景上可见
        self._标题标签 = QLabel("MMORPG游戏AI助手")
        self._标题标签.setObjectName("标题栏标题")
        标题字体 = QFont("Microsoft YaHei UI", 11)
        标题字体.setBold(True)
        self._标题标签.setFont(标题字体)
        self._标题标签.setStyleSheet("""
            QLabel {
                color: white;
                padding-left: 8px;
                background: transparent;
            }
        """)
        布局.addWidget(self._标题标签)
        
        # 弹性空间
        布局.addStretch()
        
        # 窗口控制按钮
        self._最小化按钮 = self._创建控制按钮("─", "最小化")
        self._最大化按钮 = self._创建控制按钮("□", "最大化")
        self._关闭按钮 = self._创建控制按钮("✕", "关闭")
        # 关闭按钮特殊样式：悬停时红色
        self._关闭按钮.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: #FFFFFF;
                font-family: "Microsoft YaHei UI", sans-serif;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #E81123;
            }
            QPushButton:pressed {
                background-color: #C50F1F;
            }
        """)
        
        布局.addWidget(self._最小化按钮)
        布局.addWidget(self._最大化按钮)
        布局.addWidget(self._关闭按钮)
        
        # 连接信号
        self._最小化按钮.clicked.connect(self._处理最小化)
        self._最大化按钮.clicked.connect(self._处理最大化)
        self._关闭按钮.clicked.connect(self._处理关闭)
    
    def _创建控制按钮(self, 文字: str, 提示: str) -> QPushButton:
        """
        创建窗口控制按钮
        
        参数:
            文字: 按钮显示的文字
            提示: 按钮的工具提示
        
        返回:
            QPushButton实例
        """
        按钮 = QPushButton(文字)
        按钮.setFixedSize(46, 36)
        按钮.setToolTip(提示)
        按钮.setCursor(Qt.ArrowCursor)
        按钮.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: #FFFFFF;
                font-family: "Microsoft YaHei UI", sans-serif;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.15);
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.25);
            }
        """)
        return 按钮
    
    def _创建功能按钮(self, 文字: str, 提示: str) -> QPushButton:
        """
        创建功能按钮（如配置按钮）
        
        参数:
            文字: 按钮显示的文字
            提示: 按钮的工具提示
        
        返回:
            QPushButton实例
        """
        按钮 = QPushButton(文字)
        按钮.setFixedSize(46, 36)
        按钮.setToolTip(提示)
        按钮.setCursor(Qt.ArrowCursor)
        按钮.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: #FFFFFF;
                font-family: "Microsoft YaHei UI", sans-serif;
                font-size: 12px;
                margin-right: 8px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.2);
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.3);
            }
        """)
        return 按钮
    
    def _应用样式(self) -> None:
        """应用样式表"""
        # 注意：背景色通过 paintEvent 绘制，确保不被全局样式覆盖
        pass
    
    def paintEvent(self, event) -> None:
        """绘制事件 - 强制绘制深蓝色背景"""
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#1E3A5F"))
        painter.end()
    
    def _处理最小化(self) -> None:
        """处理最小化按钮点击"""
        self.最小化请求.emit()
        if self._父窗口:
            self._父窗口.showMinimized()
    
    def _处理配置(self) -> None:
        """处理配置按钮点击 (需求 1.1)"""
        self.配置请求.emit()
    
    def _处理最大化(self) -> None:
        """处理最大化/还原按钮点击"""
        self.最大化请求.emit()
        # 注意：当前窗口是固定尺寸，不支持最大化
        # 如果需要支持最大化，需要修改主窗口的setFixedSize为setMinimumSize
    
    def _处理关闭(self) -> None:
        """处理关闭按钮点击"""
        self.关闭请求.emit()
        if self._父窗口:
            self._父窗口.close()
    
    def 设置标题(self, 标题: str) -> None:
        """
        设置标题栏标题
        
        参数:
            标题: 新的标题文字
        """
        self._标题标签.setText(标题)
    
    def 获取标题(self) -> str:
        """
        获取当前标题
        
        返回:
            当前标题文字
        """
        return self._标题标签.text()
    
    # 鼠标事件处理 - 实现窗口拖动
    def mousePressEvent(self, event: QMouseEvent) -> None:
        """鼠标按下事件"""
        if event.button() == Qt.LeftButton:
            self._拖动中 = True
            self._拖动起始位置 = event.globalPosition().toPoint() - self._父窗口.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """鼠标移动事件"""
        if self._拖动中 and self._父窗口:
            self._父窗口.move(event.globalPosition().toPoint() - self._拖动起始位置)
            event.accept()
    
    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """鼠标释放事件"""
        self._拖动中 = False
        event.accept()
    
    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        """鼠标双击事件 - 可用于最大化/还原"""
        # 当前窗口是固定尺寸，双击不做处理
        event.accept()
