# -*- coding: utf-8 -*-
"""
配置界面模块

提供图形化配置编辑界面，支持:
- 分区配置编辑 (窗口设置、模型设置、训练设置、运行设置)
- 实时验证和错误高亮
- 档案管理
- 窗口区域预览
- 工具提示显示

需求: 1.1, 1.2, 1.3, 1.4, 2.1, 2.2, 2.3, 2.4
"""

import os
import sys
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea,
    QFrame, QLabel, QPushButton, QLineEdit, QSpinBox,
    QDoubleSpinBox, QComboBox, QCheckBox, QSlider,
    QFormLayout, QMessageBox, QSizePolicy, QGroupBox,
    QFileDialog, QInputDialog, QTabWidget, QDialog,
    QDialogButtonBox, QGridLayout, QToolTip, QApplication
)
from PySide6.QtCore import Qt, Signal, QTimer, QPoint
from PySide6.QtGui import QFont, QPainter, QColor, QPen, QBrush

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from 界面.样式.主题 import 颜色
from 界面.样式.布局常量 import 布局常量
from 界面.组件.通用组件 import 确认对话框, 提示对话框


@dataclass
class 控件信息:
    """控件信息数据类"""
    控件: QWidget
    参数名: str
    分区名: str
    参数定义: Dict[str, Any]
    错误标签: Optional[QLabel] = None


class 窗口预览控件(QWidget):
    """窗口区域预览控件
    
    显示游戏窗口区域的可视化预览
    需求: 2.1, 2.4
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._窗口X = 0
        self._窗口Y = 0
        self._窗口宽度 = 1920
        self._窗口高度 = 1080
        self._屏幕宽度 = 1920
        self._屏幕高度 = 1080
        
        self.setMinimumSize(200, 120)
        self.setMaximumSize(300, 180)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    
    def 设置窗口区域(self, x: int, y: int, 宽度: int, 高度: int):
        """设置窗口区域参数"""
        self._窗口X = x
        self._窗口Y = y
        self._窗口宽度 = 宽度
        self._窗口高度 = 高度
        self.update()
    
    def 设置屏幕尺寸(self, 宽度: int, 高度: int):
        """设置屏幕尺寸"""
        self._屏幕宽度 = 宽度
        self._屏幕高度 = 高度
        self.update()
    
    def paintEvent(self, event):
        """绘制预览"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 计算缩放比例
        控件宽度 = self.width() - 20
        控件高度 = self.height() - 20
        
        比例X = 控件宽度 / max(self._屏幕宽度, 1)
        比例Y = 控件高度 / max(self._屏幕高度, 1)
        比例 = min(比例X, 比例Y)
        
        # 计算偏移使其居中
        偏移X = (self.width() - self._屏幕宽度 * 比例) / 2
        偏移Y = (self.height() - self._屏幕高度 * 比例) / 2
        
        # 绘制屏幕背景
        painter.setPen(QPen(QColor(颜色.边框), 1))
        painter.setBrush(QBrush(QColor("#F1F5F9")))
        painter.drawRect(
            int(偏移X), int(偏移Y),
            int(self._屏幕宽度 * 比例), int(self._屏幕高度 * 比例)
        )
        
        # 绘制窗口区域
        窗口X = int(偏移X + self._窗口X * 比例)
        窗口Y = int(偏移Y + self._窗口Y * 比例)
        窗口宽 = int(self._窗口宽度 * 比例)
        窗口高 = int(self._窗口高度 * 比例)
        
        painter.setPen(QPen(QColor(颜色.主色), 2))
        painter.setBrush(QBrush(QColor(颜色.主色 + "40")))  # 半透明
        painter.drawRect(窗口X, 窗口Y, 窗口宽, 窗口高)
        
        # 绘制标签
        painter.setPen(QColor(颜色.文字))
        painter.setFont(QFont("Microsoft YaHei", 9))
        painter.drawText(
            窗口X + 5, 窗口Y + 15,
            f"{self._窗口宽度}x{self._窗口高度}"
        )
        
        painter.end()


class 配置界面(QWidget):
    """图形化配置编辑界面
    
    提供完整的配置管理功能:
    - 分区配置编辑
    - 实时验证
    - 档案管理
    - 窗口区域预览
    
    支持两种模式:
    - 独立模式: 作为独立窗口运行 (嵌入模式=False)
    - 嵌入模式: 作为页面嵌入主界面 (嵌入模式=True)
    
    需求: 1.1, 1.2, 1.3, 1.4, 2.1, 2.2, 2.3, 2.4
    """
    
    # 信号定义
    配置已保存 = Signal(dict)
    配置已重置 = Signal()
    
    def __init__(self, 配置管理器=None, parent=None, 嵌入模式=False):
        super().__init__(parent)
        
        # 嵌入模式标志
        self._嵌入模式 = 嵌入模式
        
        # 初始化配置管理器
        self._配置管理器 = 配置管理器
        if self._配置管理器 is None:
            self._初始化配置管理器()
        
        # 控件字典
        self._控件字典: Dict[str, 控件信息] = {}
        self._已修改 = False
        self._验证定时器 = QTimer()
        self._验证定时器.setSingleShot(True)
        self._验证定时器.timeout.connect(self._执行验证)
        
        # 初始化界面
        self._初始化界面()
        self._加载配置到界面()
    
    def _初始化配置管理器(self):
        """初始化配置管理器"""
        try:
            from 核心.配置管理 import ConfigManager
            self._配置管理器 = ConfigManager(auto_load_last=False)
        except Exception as e:
            print(f"初始化配置管理器失败: {e}")
            self._配置管理器 = None
    
    def _初始化界面(self):
        """初始化界面布局
        
        需求: 1.1, 1.2
        """
        # 嵌入模式下不设置窗口标题和尺寸
        if not self._嵌入模式:
            self.setWindowTitle("⚙️ 配置管理")
            self.setMinimumSize(700, 550)
            self.resize(750, 600)
        else:
            # 嵌入模式下使用扩展尺寸策略
            self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # 应用样式 - 使用 QWidget 而非 QDialog
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {颜色.背景};
            }}
            QLabel {{
                color: {颜色.文字};
                font-size: {布局常量.正文字号}px;
            }}
            QGroupBox {{
                font-weight: bold;
                font-size: {布局常量.卡片标题字号}px;
                color: {颜色.标题};
                border: 1px solid {颜色.边框};
                border-radius: {布局常量.卡片圆角}px;
                margin-top: 12px;
                padding-top: 8px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 12px;
                padding: 0 6px;
            }}
        """)
        
        主布局 = QVBoxLayout(self)
        主布局.setContentsMargins(16, 16, 16, 16)
        主布局.setSpacing(12)
        
        # 标签页容器
        self._标签页 = QTabWidget()
        self._标签页.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {颜色.边框};
                border-radius: {布局常量.卡片圆角}px;
                background-color: {颜色.卡片背景};
                padding: 8px;
            }}
            QTabBar::tab {{
                background-color: {颜色.卡片背景};
                border: 1px solid {颜色.边框};
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                padding: 8px 16px;
                margin-right: 2px;
                font-size: {布局常量.正文字号}px;
            }}
            QTabBar::tab:selected {{
                background-color: {颜色.主色};
                color: white;
                font-weight: bold;
            }}
            QTabBar::tab:hover:!selected {{
                background-color: {颜色.悬停背景};
            }}
        """)
        
        # 添加配置分区标签页
        self._标签页.addTab(self._创建窗口设置标签页(), "🖥️ 窗口设置")
        self._标签页.addTab(self._创建模型设置标签页(), "🧠 模型设置")
        self._标签页.addTab(self._创建训练设置标签页(), "📚 训练设置")
        self._标签页.addTab(self._创建运行设置标签页(), "🚀 运行设置")
        
        主布局.addWidget(self._标签页, 1)
        
        # 底部按钮区域
        主布局.addWidget(self._创建底部按钮区域())
    
    def _创建滚动区域(self, 内容布局: QVBoxLayout) -> QScrollArea:
        """创建带滚动条的内容区域
        
        需求: 1.5
        """
        滚动区域 = QScrollArea()
        滚动区域.setWidgetResizable(True)
        滚动区域.setFrameShape(QFrame.NoFrame)
        滚动区域.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        内容容器 = QWidget()
        内容容器.setLayout(内容布局)
        滚动区域.setWidget(内容容器)
        
        return 滚动区域

    def _创建窗口设置标签页(self) -> QWidget:
        """创建窗口设置标签页
        
        需求: 1.1, 1.2, 1.3, 2.1, 5.1
        """
        布局 = QVBoxLayout()
        布局.setSpacing(12)
        布局.setContentsMargins(8, 8, 8, 8)
        
        # 窗口区域设置组
        窗口组 = QGroupBox("📐 窗口区域")
        窗口组布局 = QGridLayout(窗口组)
        窗口组布局.setSpacing(8)
        
        # 窗口X
        窗口组布局.addWidget(QLabel("窗口X:"), 0, 0)
        窗口X = self._创建数字输入框("窗口设置", "窗口X", 0, 0, 7680)
        窗口组布局.addWidget(窗口X, 0, 1)
        
        # 窗口Y
        窗口组布局.addWidget(QLabel("窗口Y:"), 0, 2)
        窗口Y = self._创建数字输入框("窗口设置", "窗口Y", 0, 0, 4320)
        窗口组布局.addWidget(窗口Y, 0, 3)
        
        # 窗口宽度
        窗口组布局.addWidget(QLabel("宽度:"), 1, 0)
        窗口宽度 = self._创建数字输入框("窗口设置", "窗口宽度", 1920, 100, 7680)
        窗口组布局.addWidget(窗口宽度, 1, 1)
        
        # 窗口高度
        窗口组布局.addWidget(QLabel("高度:"), 1, 2)
        窗口高度 = self._创建数字输入框("窗口设置", "窗口高度", 1080, 100, 4320)
        窗口组布局.addWidget(窗口高度, 1, 3)
        
        # 选择窗口按钮 (需求 1.1, 1.2, 1.3)
        选择窗口按钮 = QPushButton("🎯 选择窗口")
        选择窗口按钮.setFixedSize(100, 28)
        选择窗口按钮.setStyleSheet(f"""
            QPushButton {{
                background-color: {颜色.成功};
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: #059669;
            }}
        """)
        选择窗口按钮.setToolTip("从运行中的窗口列表中选择目标窗口")
        选择窗口按钮.clicked.connect(self._打开窗口选择对话框)
        窗口组布局.addWidget(选择窗口按钮, 2, 0, 1, 2)
        
        # 分区重置按钮 (需求 5.1)
        重置按钮 = self._创建分区重置按钮("窗口设置")
        窗口组布局.addWidget(重置按钮, 2, 3, alignment=Qt.AlignRight)
        
        布局.addWidget(窗口组)
        
        # 窗口预览组 (需求 2.1)
        预览组 = QGroupBox("👁️ 窗口预览")
        预览组布局 = QVBoxLayout(预览组)
        
        self._窗口预览 = 窗口预览控件()
        预览组布局.addWidget(self._窗口预览, alignment=Qt.AlignCenter)
        
        # 连接窗口参数变化到预览更新
        self._连接预览更新()
        
        布局.addWidget(预览组)
        布局.addStretch()
        
        return self._创建滚动区域(布局)
    
    def _连接预览更新(self):
        """连接窗口参数控件到预览更新"""
        def 更新预览():
            try:
                x = self._控件字典.get("窗口设置.窗口X")
                y = self._控件字典.get("窗口设置.窗口Y")
                宽 = self._控件字典.get("窗口设置.窗口宽度")
                高 = self._控件字典.get("窗口设置.窗口高度")
                
                if all([x, y, 宽, 高]):
                    self._窗口预览.设置窗口区域(
                        x.控件.value(),
                        y.控件.value(),
                        宽.控件.value(),
                        高.控件.value()
                    )
            except Exception:
                pass
        
        # 延迟连接，等控件创建完成
        QTimer.singleShot(100, lambda: self._绑定预览更新(更新预览))
    
    def _绑定预览更新(self, 更新函数):
        """绑定预览更新函数到控件"""
        for 键 in ["窗口设置.窗口X", "窗口设置.窗口Y", "窗口设置.窗口宽度", "窗口设置.窗口高度"]:
            信息 = self._控件字典.get(键)
            if 信息 and isinstance(信息.控件, QSpinBox):
                信息.控件.valueChanged.connect(更新函数)
    
    def _创建模型设置标签页(self) -> QWidget:
        """创建模型设置标签页
        
        需求: 1.2, 5.1
        """
        布局 = QVBoxLayout()
        布局.setSpacing(12)
        布局.setContentsMargins(8, 8, 8, 8)
        
        # 模型路径组
        路径组 = QGroupBox("📂 模型路径")
        路径组布局 = QFormLayout(路径组)
        路径组布局.setSpacing(8)
        
        模型路径 = self._创建路径输入框("模型设置", "模型路径", "模型/决策模型.pth")
        路径组布局.addRow("决策模型:", self._创建带说明控件(模型路径, "决策模型文件路径"))
        
        YOLO模型 = self._创建路径输入框("模型设置", "YOLO模型", "模型/yolo.pt")
        路径组布局.addRow("YOLO模型:", self._创建带说明控件(YOLO模型, "YOLO检测模型路径"))
        
        布局.addWidget(路径组)
        
        # 检测参数组
        检测组 = QGroupBox("🎯 检测参数")
        检测组布局 = QFormLayout(检测组)
        检测组布局.setSpacing(8)
        
        置信度 = self._创建浮点输入框("模型设置", "置信度阈值", 0.5, 0.0, 1.0, 0.01)
        检测组布局.addRow("置信度阈值:", self._创建带说明控件(置信度, "检测置信度阈值 (0.0-1.0)"))
        
        布局.addWidget(检测组)
        
        # 分区重置按钮 (需求 5.1)
        重置按钮容器 = QWidget()
        重置按钮布局 = QHBoxLayout(重置按钮容器)
        重置按钮布局.setContentsMargins(0, 8, 0, 0)
        重置按钮布局.addStretch()
        重置按钮布局.addWidget(self._创建分区重置按钮("模型设置"))
        布局.addWidget(重置按钮容器)
        
        布局.addStretch()
        
        return self._创建滚动区域(布局)
    
    def _创建训练设置标签页(self) -> QWidget:
        """创建训练设置标签页
        
        需求: 1.2, 5.1
        """
        布局 = QVBoxLayout()
        布局.setSpacing(12)
        布局.setContentsMargins(8, 8, 8, 8)
        
        # 训练参数组
        训练组 = QGroupBox("⚙️ 训练参数")
        训练组布局 = QFormLayout(训练组)
        训练组布局.setSpacing(8)
        
        批次大小 = self._创建数字输入框("训练设置", "批次大小", 32, 1, 256)
        训练组布局.addRow("批次大小:", self._创建带说明控件(批次大小, "训练批次大小 (1-256)"))
        
        学习率 = self._创建浮点输入框("训练设置", "学习率", 0.001, 0.0001, 0.1, 0.0001)
        训练组布局.addRow("学习率:", self._创建带说明控件(学习率, "学习率 (0.0001-0.1)"))
        
        训练轮次 = self._创建数字输入框("训练设置", "训练轮次", 100, 1, 10000)
        训练组布局.addRow("训练轮次:", self._创建带说明控件(训练轮次, "训练轮次数"))
        
        布局.addWidget(训练组)
        
        # 分区重置按钮 (需求 5.1)
        重置按钮容器 = QWidget()
        重置按钮布局 = QHBoxLayout(重置按钮容器)
        重置按钮布局.setContentsMargins(0, 8, 0, 0)
        重置按钮布局.addStretch()
        重置按钮布局.addWidget(self._创建分区重置按钮("训练设置"))
        布局.addWidget(重置按钮容器)
        
        布局.addStretch()
        
        return self._创建滚动区域(布局)
    
    def _创建运行设置标签页(self) -> QWidget:
        """创建运行设置标签页
        
        需求: 1.2, 1.3, 5.1
        """
        布局 = QVBoxLayout()
        布局.setSpacing(12)
        布局.setContentsMargins(8, 8, 8, 8)
        
        # 运行选项组
        选项组 = QGroupBox("🔧 运行选项")
        选项组布局 = QFormLayout(选项组)
        选项组布局.setSpacing(8)
        
        启用YOLO = self._创建复选框("运行设置", "启用YOLO", True)
        选项组布局.addRow("", self._创建带说明控件(启用YOLO, "是否启用YOLO检测"))
        
        显示调试 = self._创建复选框("运行设置", "显示调试", False)
        选项组布局.addRow("", self._创建带说明控件(显示调试, "是否显示调试信息"))
        
        布局.addWidget(选项组)
        
        # 日志设置组
        日志组 = QGroupBox("📝 日志设置")
        日志组布局 = QFormLayout(日志组)
        日志组布局.setSpacing(8)
        
        日志级别 = self._创建下拉框("运行设置", "日志级别", "INFO", 
                                ["DEBUG", "INFO", "WARNING", "ERROR"])
        日志组布局.addRow("日志级别:", self._创建带说明控件(日志级别, "日志输出级别"))
        
        布局.addWidget(日志组)
        
        # 分区重置按钮 (需求 5.1)
        重置按钮容器 = QWidget()
        重置按钮布局 = QHBoxLayout(重置按钮容器)
        重置按钮布局.setContentsMargins(0, 8, 0, 0)
        重置按钮布局.addStretch()
        重置按钮布局.addWidget(self._创建分区重置按钮("运行设置"))
        布局.addWidget(重置按钮容器)
        
        布局.addStretch()
        
        return self._创建滚动区域(布局)
    
    def _创建底部按钮区域(self) -> QWidget:
        """创建底部按钮区域"""
        按钮容器 = QWidget()
        按钮布局 = QHBoxLayout(按钮容器)
        按钮布局.setContentsMargins(0, 8, 0, 0)
        按钮布局.setSpacing(8)
        
        # 状态标签
        self._状态标签 = QLabel("就绪")
        self._状态标签.setStyleSheet(f"color: {颜色.次要文字};")
        按钮布局.addWidget(self._状态标签)
        
        按钮布局.addStretch()
        
        # 重置按钮
        self._重置按钮 = QPushButton("🔄 重置默认")
        self._重置按钮.setFixedSize(100, 32)
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
        self._重置按钮.clicked.connect(self._重置配置)
        按钮布局.addWidget(self._重置按钮)
        
        # 取消按钮 - 仅在非嵌入模式下显示
        if not self._嵌入模式:
            self._取消按钮 = QPushButton("取消")
            self._取消按钮.setFixedSize(80, 32)
            self._取消按钮.setStyleSheet(f"""
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
            self._取消按钮.clicked.connect(self._关闭窗口)
            按钮布局.addWidget(self._取消按钮)
        
        # 保存按钮
        self._保存按钮 = QPushButton("💾 保存")
        self._保存按钮.setFixedSize(80, 32)
        self._保存按钮.setStyleSheet(f"""
            QPushButton {{
                background-color: {颜色.主色};
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #2563EB;
            }}
        """)
        self._保存按钮.clicked.connect(self._保存配置)
        按钮布局.addWidget(self._保存按钮)
        
        return 按钮容器

    # ==================== 控件创建方法 ====================
    
    def _创建分区重置按钮(self, 分区名: str) -> QPushButton:
        """创建分区重置按钮
        
        需求: 5.1
        
        Args:
            分区名: 要重置的分区名称
            
        Returns:
            重置按钮控件
        """
        按钮 = QPushButton("🔄 重置此分区")
        按钮.setFixedSize(100, 28)
        按钮.setStyleSheet(f"""
            QPushButton {{
                background-color: {颜色.卡片背景};
                color: {颜色.次要文字};
                border: 1px solid {颜色.边框};
                border-radius: 4px;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background-color: {颜色.悬停背景};
                color: {颜色.文字};
            }}
        """)
        按钮.setToolTip(f"将 {分区名} 的所有参数重置为默认值")
        按钮.clicked.connect(lambda: self._重置分区(分区名))
        return 按钮
    
    def _重置分区(self, 分区名: str):
        """重置指定分区的配置到默认值
        
        需求: 5.1
        
        Args:
            分区名: 要重置的分区名称
        """
        # 确认对话框
        回复 = 确认对话框.询问(
            self, "确认重置",
            f"确定要将「{分区名}」的所有参数重置为默认值吗？",
            "重置", "取消"
        )
        
        if 回复 != 确认对话框.确认:
            return
        
        # 获取分区默认值
        if self._配置管理器 is not None:
            try:
                分区默认值 = self._配置管理器.重置为默认(分区名)
                if 分区名 in 分区默认值:
                    # 设置分区内的所有控件为默认值
                    for 参数名, 默认值 in 分区默认值[分区名].items():
                        键 = f"{分区名}.{参数名}"
                        信息 = self._控件字典.get(键)
                        if 信息:
                            self._设置控件值(信息.控件, 默认值)
                            # 清除错误状态
                            self._显示错误(信息, True, "")
                    
                    # 更新状态
                    self._状态标签.setText(f"✓ {分区名} 已重置")
                    self._状态标签.setStyleSheet(f"color: {颜色.成功};")
                    self._标记已修改()
                    
                    # 如果是窗口设置，更新预览
                    if 分区名 == "窗口设置":
                        self.更新预览()
            except Exception as e:
                提示对话框.警告提示(self, "重置失败", f"重置分区失败: {e}")
        else:
            # 没有配置管理器时，使用硬编码的默认值
            self._重置分区到硬编码默认值(分区名)
    
    def _重置分区到硬编码默认值(self, 分区名: str):
        """使用硬编码默认值重置分区
        
        当配置管理器不可用时的备用方案
        
        Args:
            分区名: 要重置的分区名称
        """
        硬编码默认值 = {
            "窗口设置": {
                "窗口X": 0,
                "窗口Y": 0,
                "窗口宽度": 1920,
                "窗口高度": 1080,
            },
            "模型设置": {
                "模型路径": "模型/决策模型.pth",
                "YOLO模型": "模型/yolo.pt",
                "置信度阈值": 0.5,
            },
            "训练设置": {
                "批次大小": 32,
                "学习率": 0.001,
                "训练轮次": 100,
            },
            "运行设置": {
                "启用YOLO": True,
                "显示调试": False,
                "日志级别": "INFO",
            },
        }
        
        if 分区名 in 硬编码默认值:
            for 参数名, 默认值 in 硬编码默认值[分区名].items():
                键 = f"{分区名}.{参数名}"
                信息 = self._控件字典.get(键)
                if 信息:
                    self._设置控件值(信息.控件, 默认值)
                    self._显示错误(信息, True, "")
            
            self._状态标签.setText(f"✓ {分区名} 已重置")
            self._状态标签.setStyleSheet(f"color: {颜色.成功};")
            self._标记已修改()
            
            if 分区名 == "窗口设置":
                self.更新预览()
    
    def _创建数字输入框(self, 分区名: str, 参数名: str, 默认值: int, 
                      最小值: int = 0, 最大值: int = 10000) -> QSpinBox:
        """创建数字输入框
        
        需求: 1.3
        """
        控件 = QSpinBox()
        控件.setRange(最小值, 最大值)
        控件.setValue(默认值)
        控件.setFixedWidth(120)
        控件.setFixedHeight(28)
        
        # 获取参数定义
        参数定义 = self._获取参数定义(分区名, 参数名)
        if 参数定义:
            描述 = 参数定义.get("描述", "")
            if 描述:
                控件.setToolTip(描述)  # 需求: 1.4
        
        # 创建错误标签
        错误标签 = self._创建错误标签()
        
        # 注册控件
        键 = f"{分区名}.{参数名}"
        self._控件字典[键] = 控件信息(
            控件=控件,
            参数名=参数名,
            分区名=分区名,
            参数定义=参数定义 or {},
            错误标签=错误标签
        )
        
        # 连接值变化信号到验证
        控件.valueChanged.connect(lambda: self._触发验证(键))
        控件.valueChanged.connect(self._标记已修改)
        
        return 控件
    
    def _创建浮点输入框(self, 分区名: str, 参数名: str, 默认值: float,
                      最小值: float = 0.0, 最大值: float = 1.0, 
                      步长: float = 0.01) -> QDoubleSpinBox:
        """创建浮点数输入框
        
        需求: 1.3
        """
        控件 = QDoubleSpinBox()
        控件.setRange(最小值, 最大值)
        控件.setValue(默认值)
        控件.setSingleStep(步长)
        控件.setDecimals(4)
        控件.setFixedWidth(120)
        控件.setFixedHeight(28)
        
        # 获取参数定义
        参数定义 = self._获取参数定义(分区名, 参数名)
        if 参数定义:
            描述 = 参数定义.get("描述", "")
            if 描述:
                控件.setToolTip(描述)
        
        # 创建错误标签
        错误标签 = self._创建错误标签()
        
        # 注册控件
        键 = f"{分区名}.{参数名}"
        self._控件字典[键] = 控件信息(
            控件=控件,
            参数名=参数名,
            分区名=分区名,
            参数定义=参数定义 or {},
            错误标签=错误标签
        )
        
        # 连接值变化信号到验证
        控件.valueChanged.connect(lambda: self._触发验证(键))
        控件.valueChanged.connect(self._标记已修改)
        
        return 控件
    
    def _创建路径输入框(self, 分区名: str, 参数名: str, 默认值: str) -> QWidget:
        """创建路径输入框（带浏览按钮）
        
        需求: 1.3
        """
        容器 = QWidget()
        布局 = QHBoxLayout(容器)
        布局.setContentsMargins(0, 0, 0, 0)
        布局.setSpacing(4)
        
        输入框 = QLineEdit()
        输入框.setText(默认值)
        输入框.setFixedHeight(28)
        输入框.setMinimumWidth(200)
        
        浏览按钮 = QPushButton("...")
        浏览按钮.setFixedSize(28, 28)
        浏览按钮.setStyleSheet(f"""
            QPushButton {{
                background-color: {颜色.卡片背景};
                border: 1px solid {颜色.边框};
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {颜色.悬停背景};
            }}
        """)
        浏览按钮.clicked.connect(lambda: self._浏览文件(输入框))
        
        布局.addWidget(输入框)
        布局.addWidget(浏览按钮)
        
        # 获取参数定义
        参数定义 = self._获取参数定义(分区名, 参数名)
        if 参数定义:
            描述 = 参数定义.get("描述", "")
            if 描述:
                输入框.setToolTip(描述)
        
        # 创建错误标签
        错误标签 = self._创建错误标签()
        
        # 注册控件（使用输入框作为主控件）
        键 = f"{分区名}.{参数名}"
        self._控件字典[键] = 控件信息(
            控件=输入框,
            参数名=参数名,
            分区名=分区名,
            参数定义=参数定义 or {},
            错误标签=错误标签
        )
        
        输入框.textChanged.connect(lambda: self._触发验证(键))
        输入框.textChanged.connect(self._标记已修改)
        
        return 容器
    
    def _创建复选框(self, 分区名: str, 参数名: str, 默认值: bool) -> QCheckBox:
        """创建复选框
        
        需求: 1.3
        """
        # 获取参数定义
        参数定义 = self._获取参数定义(分区名, 参数名)
        描述 = 参数定义.get("描述", 参数名) if 参数定义 else 参数名
        
        控件 = QCheckBox(描述)
        控件.setChecked(默认值)
        
        # 注册控件
        键 = f"{分区名}.{参数名}"
        self._控件字典[键] = 控件信息(
            控件=控件,
            参数名=参数名,
            分区名=分区名,
            参数定义=参数定义 or {}
        )
        
        控件.stateChanged.connect(self._标记已修改)
        
        return 控件
    
    def _创建下拉框(self, 分区名: str, 参数名: str, 默认值: str, 
                  选项列表: List[str]) -> QComboBox:
        """创建下拉框
        
        需求: 1.3
        """
        控件 = QComboBox()
        控件.addItems(选项列表)
        控件.setCurrentText(默认值)
        控件.setFixedWidth(120)
        控件.setFixedHeight(28)
        
        # 获取参数定义
        参数定义 = self._获取参数定义(分区名, 参数名)
        if 参数定义:
            描述 = 参数定义.get("描述", "")
            if 描述:
                控件.setToolTip(描述)
        
        # 注册控件
        键 = f"{分区名}.{参数名}"
        self._控件字典[键] = 控件信息(
            控件=控件,
            参数名=参数名,
            分区名=分区名,
            参数定义=参数定义 or {}
        )
        
        控件.currentTextChanged.connect(self._标记已修改)
        
        return 控件
    
    def _创建错误标签(self) -> QLabel:
        """创建错误提示标签
        
        需求: 2.3
        """
        标签 = QLabel()
        标签.setStyleSheet(f"""
            color: {颜色.错误};
            font-size: {布局常量.次要文字字号}px;
        """)
        标签.setVisible(False)
        return 标签
    
    def _创建带说明控件(self, 控件: QWidget, 说明: str) -> QWidget:
        """创建带说明文字的控件容器
        
        需求: 1.4
        """
        容器 = QWidget()
        布局 = QVBoxLayout(容器)
        布局.setContentsMargins(0, 0, 0, 0)
        布局.setSpacing(2)
        
        布局.addWidget(控件)
        
        说明标签 = QLabel(说明)
        说明标签.setStyleSheet(f"""
            color: {颜色.次要文字};
            font-size: {布局常量.次要文字字号}px;
        """)
        说明标签.setWordWrap(True)
        布局.addWidget(说明标签)
        
        return 容器
    
    def _获取参数定义(self, 分区名: str, 参数名: str) -> Optional[Dict[str, Any]]:
        """从配置管理器获取参数定义"""
        if self._配置管理器 is None:
            return None
        
        try:
            分区参数 = self._配置管理器.获取分区参数(分区名)
            return 分区参数.get(参数名)
        except Exception:
            return None
    
    def _浏览文件(self, 输入框: QLineEdit):
        """浏览文件对话框"""
        文件路径, _ = QFileDialog.getOpenFileName(
            self, "选择文件", "",
            "所有文件 (*.*);;模型文件 (*.pt *.pth *.onnx)"
        )
        if 文件路径:
            输入框.setText(文件路径)

    # ==================== 验证方法 ====================
    
    def _触发验证(self, 键: str):
        """触发延迟验证
        
        需求: 2.2
        """
        self._待验证键 = 键
        self._验证定时器.start(300)  # 300ms 延迟
    
    def _执行验证(self):
        """执行实时验证
        
        需求: 2.2, 2.3
        """
        if not hasattr(self, '_待验证键'):
            return
        
        键 = self._待验证键
        信息 = self._控件字典.get(键)
        
        if not 信息:
            return
        
        # 获取当前值
        值 = self._获取控件值(信息.控件)
        
        # 执行验证
        有效, 错误信息 = self._验证单个值(信息.分区名, 信息.参数名, 值, 信息.参数定义)
        
        # 更新错误显示
        self._显示错误(信息, 有效, 错误信息)
    
    def _验证单个值(self, 分区名: str, 参数名: str, 值: Any, 
                  参数定义: Dict[str, Any]) -> tuple:
        """验证单个参数值
        
        需求: 2.2
        
        返回:
            (是否有效, 错误信息)
        """
        if not 参数定义:
            return True, ""
        
        类型 = 参数定义.get("类型", "str")
        
        # 类型验证
        if 类型 == "int":
            if not isinstance(值, int):
                return False, f"期望整数类型"
        elif 类型 == "float":
            if not isinstance(值, (int, float)):
                return False, f"期望浮点数类型"
        
        # 范围验证
        最小值 = 参数定义.get("最小值")
        最大值 = 参数定义.get("最大值")
        
        if 最小值 is not None and 值 < 最小值:
            return False, f"值不能小于 {最小值}"
        
        if 最大值 is not None and 值 > 最大值:
            return False, f"值不能大于 {最大值}"
        
        # 必需验证
        if 参数定义.get("必需", False) and (值 is None or 值 == ""):
            return False, "此参数为必需项"
        
        return True, ""
    
    def _显示错误(self, 信息: 控件信息, 有效: bool, 错误信息: str):
        """显示或隐藏错误信息
        
        需求: 2.3
        """
        控件 = 信息.控件
        
        # 更新控件样式
        if 有效:
            控件.setStyleSheet("")
        else:
            控件.setStyleSheet(f"border: 1px solid {颜色.错误};")
        
        # 更新错误标签
        if 信息.错误标签:
            if 有效:
                信息.错误标签.setVisible(False)
            else:
                信息.错误标签.setText(f"⚠️ {错误信息}")
                信息.错误标签.setVisible(True)
    
    def _验证所有配置(self) -> tuple:
        """验证所有配置值
        
        返回:
            (是否全部有效, 错误列表)
        """
        错误列表 = []
        
        for 键, 信息 in self._控件字典.items():
            值 = self._获取控件值(信息.控件)
            有效, 错误信息 = self._验证单个值(
                信息.分区名, 信息.参数名, 值, 信息.参数定义
            )
            
            if not 有效:
                错误列表.append(f"{信息.分区名}.{信息.参数名}: {错误信息}")
                self._显示错误(信息, False, 错误信息)
            else:
                self._显示错误(信息, True, "")
        
        return len(错误列表) == 0, 错误列表
    
    # ==================== 配置操作方法 ====================
    
    def _获取控件值(self, 控件: QWidget) -> Any:
        """获取控件的当前值"""
        if isinstance(控件, QSpinBox):
            return 控件.value()
        elif isinstance(控件, QDoubleSpinBox):
            return 控件.value()
        elif isinstance(控件, QLineEdit):
            return 控件.text()
        elif isinstance(控件, QCheckBox):
            return 控件.isChecked()
        elif isinstance(控件, QComboBox):
            return 控件.currentText()
        return None
    
    def _设置控件值(self, 控件: QWidget, 值: Any):
        """设置控件的值"""
        if isinstance(控件, QSpinBox):
            控件.setValue(int(值) if 值 is not None else 0)
        elif isinstance(控件, QDoubleSpinBox):
            控件.setValue(float(值) if 值 is not None else 0.0)
        elif isinstance(控件, QLineEdit):
            控件.setText(str(值) if 值 is not None else "")
        elif isinstance(控件, QCheckBox):
            控件.setChecked(bool(值) if 值 is not None else False)
        elif isinstance(控件, QComboBox):
            控件.setCurrentText(str(值) if 值 is not None else "")
    
    def 获取当前值(self) -> Dict[str, Dict[str, Any]]:
        """获取界面上的当前配置值"""
        配置 = {}
        
        for 键, 信息 in self._控件字典.items():
            分区名 = 信息.分区名
            参数名 = 信息.参数名
            
            if 分区名 not in 配置:
                配置[分区名] = {}
            
            配置[分区名][参数名] = self._获取控件值(信息.控件)
        
        return 配置
    
    def 设置值(self, 配置: Dict[str, Dict[str, Any]]):
        """设置界面上的配置值"""
        for 分区名, 分区配置 in 配置.items():
            for 参数名, 值 in 分区配置.items():
                键 = f"{分区名}.{参数名}"
                信息 = self._控件字典.get(键)
                if 信息:
                    self._设置控件值(信息.控件, 值)
    
    def _加载配置到界面(self):
        """从配置管理器加载配置到界面"""
        if self._配置管理器 is None:
            return
        
        try:
            默认值 = self._配置管理器.获取默认值()
            if 默认值:
                self.设置值(默认值)
        except Exception as e:
            print(f"加载配置失败: {e}")
    
    def _标记已修改(self):
        """标记配置已修改"""
        self._已修改 = True
        self._状态标签.setText("● 已修改")
        self._状态标签.setStyleSheet(f"color: {颜色.警告};")
    
    def _保存配置(self):
        """保存配置"""
        # 验证所有配置
        有效, 错误列表 = self._验证所有配置()
        
        if not 有效:
            错误信息 = "\n".join(f"• {错误}" for 错误 in 错误列表)
            提示对话框.警告提示(
                self, "验证失败",
                f"以下配置项存在问题:\n\n{错误信息}"
            )
            return
        
        # 获取当前配置
        配置 = self.获取当前值()
        
        # 发送信号
        self.配置已保存.emit(配置)
        
        # 更新状态
        self._已修改 = False
        self._状态标签.setText("✓ 已保存")
        self._状态标签.setStyleSheet(f"color: {颜色.成功};")
        
        提示对话框.信息提示(self, "成功", "配置已保存！")
    
    def _重置配置(self):
        """重置所有配置到默认值
        
        需求: 5.2, 5.3
        """
        # 重置前确认 (需求 5.3)
        回复 = 确认对话框.询问(
            self, "确认全部重置",
            "⚠️ 确定要将所有配置重置为默认值吗？\n\n"
            "此操作将重置以下分区的所有参数:\n"
            "• 窗口设置\n"
            "• 模型设置\n"
            "• 训练设置\n"
            "• 运行设置\n\n"
            "此操作不可撤销！",
            "重置", "取消"
        )
        
        if 回复 != 确认对话框.确认:
            return
        
        # 执行全部重置
        self._执行全部重置()
    
    def _执行全部重置(self):
        """执行全部重置操作
        
        需求: 5.2
        """
        try:
            if self._配置管理器 is not None:
                # 使用配置管理器获取所有默认值
                所有默认值 = self._配置管理器.重置为默认(None)
                self.设置值(所有默认值)
            else:
                # 没有配置管理器时，使用硬编码默认值重置所有分区
                for 分区名 in ["窗口设置", "模型设置", "训练设置", "运行设置"]:
                    self._重置分区到硬编码默认值(分区名)
            
            # 清除所有错误状态
            for 键, 信息 in self._控件字典.items():
                self._显示错误(信息, True, "")
            
            # 更新状态
            self._已修改 = False
            self._状态标签.setText("✓ 已全部重置")
            self._状态标签.setStyleSheet(f"color: {颜色.成功};")
            
            # 更新窗口预览
            self.更新预览()
            
            # 发送重置信号
            self.配置已重置.emit()
            
        except Exception as e:
            提示对话框.警告提示(self, "重置失败", f"全部重置失败: {e}")
    
    def _关闭窗口(self):
        """关闭窗口
        
        需求: 3.4 - 关闭前提示保存未保存的更改
        
        注意: 仅在非嵌入模式下执行对话框关闭逻辑
        """
        # 嵌入模式下不执行关闭逻辑（由主窗口管理）
        if self._嵌入模式:
            return
        
        if self._处理未保存更改():
            self.close()
    
    def closeEvent(self, event):
        """窗口关闭事件
        
        需求: 3.4 - 关闭前提示保存未保存的更改
        
        注意: 仅在非嵌入模式下处理关闭事件
        """
        # 嵌入模式下直接接受关闭事件（由主窗口管理）
        if self._嵌入模式:
            event.accept()
            return
        
        if self._处理未保存更改():
            event.accept()
        else:
            event.ignore()
    
    def _处理未保存更改(self) -> bool:
        """处理未保存的更改
        
        需求: 3.4 - 检测未保存的更改，关闭前提示保存
        
        返回:
            True: 可以继续关闭
            False: 取消关闭操作
        """
        if not self._已修改:
            return True
        
        # 使用自定义三按钮对话框
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
        
        对话框 = QDialog(self)
        对话框.setWindowTitle("未保存的更改")
        对话框.setFixedWidth(400)
        对话框.setStyleSheet(f"""
            QDialog {{
                background-color: {颜色.卡片背景};
            }}
            QLabel {{
                color: {颜色.文字};
                font-family: "Microsoft YaHei UI", "Segoe UI Emoji", sans-serif;
                font-size: 13px;
            }}
            QLabel#标题 {{
                color: {颜色.标题};
                font-size: 15px;
                font-weight: bold;
            }}
        """)
        
        布局 = QVBoxLayout(对话框)
        布局.setContentsMargins(20, 20, 20, 20)
        布局.setSpacing(16)
        
        # 标题
        标题标签 = QLabel("⚠️ 未保存的更改")
        标题标签.setObjectName("标题")
        布局.addWidget(标题标签)
        
        # 内容
        内容标签 = QLabel("配置已修改但尚未保存。\n是否要在关闭前保存更改？")
        内容标签.setWordWrap(True)
        布局.addWidget(内容标签)
        
        # 按钮区域
        按钮容器 = QWidget()
        按钮布局 = QHBoxLayout(按钮容器)
        按钮布局.setContentsMargins(0, 0, 0, 0)
        按钮布局.setSpacing(12)
        按钮布局.addStretch()
        
        # 结果变量
        结果 = {"选择": "取消"}
        
        取消按钮 = QPushButton("取消")
        取消按钮.setFixedSize(80, 32)
        取消按钮.setStyleSheet(f"""
            QPushButton {{
                background-color: {颜色.卡片背景};
                color: {颜色.文字};
                border: 1px solid {颜色.边框};
                border-radius: 6px;
                font-family: "Microsoft YaHei UI", "Segoe UI Emoji", sans-serif;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {颜色.悬停背景};
            }}
        """)
        def 点击取消():
            结果["选择"] = "取消"
            对话框.reject()
        取消按钮.clicked.connect(点击取消)
        按钮布局.addWidget(取消按钮)
        
        不保存按钮 = QPushButton("不保存")
        不保存按钮.setFixedSize(80, 32)
        不保存按钮.setStyleSheet(f"""
            QPushButton {{
                background-color: {颜色.错误};
                color: white;
                border: none;
                border-radius: 6px;
                font-family: "Microsoft YaHei UI", "Segoe UI Emoji", sans-serif;
                font-size: 13px;
            }}
            QPushButton:hover {{
                opacity: 0.9;
            }}
        """)
        def 点击不保存():
            结果["选择"] = "不保存"
            对话框.accept()
        不保存按钮.clicked.connect(点击不保存)
        按钮布局.addWidget(不保存按钮)
        
        保存按钮 = QPushButton("保存")
        保存按钮.setFixedSize(80, 32)
        保存按钮.setStyleSheet(f"""
            QPushButton {{
                background-color: {颜色.主色};
                color: white;
                border: none;
                border-radius: 6px;
                font-family: "Microsoft YaHei UI", "Segoe UI Emoji", sans-serif;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {颜色.主色悬停};
            }}
        """)
        def 点击保存():
            结果["选择"] = "保存"
            对话框.accept()
        保存按钮.clicked.connect(点击保存)
        按钮布局.addWidget(保存按钮)
        
        布局.addWidget(按钮容器)
        
        对话框.exec()
        
        if 结果["选择"] == "保存":
            # 尝试保存配置
            return self._尝试保存并关闭()
        elif 结果["选择"] == "不保存":
            # 放弃更改，直接关闭
            self._已修改 = False
            return True
        else:
            # 取消关闭
            return False
    
    def _尝试保存并关闭(self) -> bool:
        """尝试保存配置并关闭
        
        需求: 3.4 - 保存未保存的更改
        
        返回:
            True: 保存成功，可以关闭
            False: 保存失败或取消，不关闭
        """
        # 验证所有配置
        有效, 错误列表 = self._验证所有配置()
        
        if not 有效:
            错误信息 = "\n".join(f"• {错误}" for 错误 in 错误列表)
            回复 = 确认对话框.询问(
                self, "验证失败",
                f"以下配置项存在问题:\n\n{错误信息}\n\n"
                "是否仍要关闭（不保存更改）？",
                "关闭", "取消"
            )
            if 回复 == 确认对话框.确认:
                self._已修改 = False
                return True
            return False
        
        # 获取当前配置并发送保存信号
        配置 = self.获取当前值()
        self.配置已保存.emit(配置)
        
        # 更新状态
        self._已修改 = False
        return True
    
    def 有未保存更改(self) -> bool:
        """检查是否有未保存的更改
        
        需求: 3.4 - 检测未保存的更改
        
        返回:
            True: 有未保存的更改
            False: 没有未保存的更改
        """
        return self._已修改
    
    def 重置修改状态(self):
        """重置修改状态为未修改
        
        用于外部保存配置后重置状态
        """
        self._已修改 = False
        self._状态标签.setText("就绪")
        self._状态标签.setStyleSheet(f"color: {颜色.次要文字};")
    
    def 显示错误(self, 参数名: str, 错误信息: str):
        """显示指定参数的错误信息
        
        需求: 2.3
        """
        # 查找对应的控件
        for 键, 信息 in self._控件字典.items():
            if 信息.参数名 == 参数名 or 键.endswith(f".{参数名}"):
                self._显示错误(信息, False, 错误信息)
                break
    
    def 更新预览(self):
        """更新窗口预览
        
        需求: 2.4
        """
        try:
            x = self._控件字典.get("窗口设置.窗口X")
            y = self._控件字典.get("窗口设置.窗口Y")
            宽 = self._控件字典.get("窗口设置.窗口宽度")
            高 = self._控件字典.get("窗口设置.窗口高度")
            
            if all([x, y, 宽, 高]):
                self._窗口预览.设置窗口区域(
                    x.控件.value(),
                    y.控件.value(),
                    宽.控件.value(),
                    高.控件.value()
                )
        except Exception:
            pass
    
    def _打开窗口选择对话框(self):
        """打开窗口选择对话框
        
        需求: 1.2 - 点击选择窗口按钮打开窗口选择对话框
        """
        try:
            from 界面.组件.窗口选择器 import 窗口选择对话框
            from 核心.窗口检测 import 窗口查找器
            
            # 创建窗口查找器和对话框
            查找器 = 窗口查找器()
            对话框 = 窗口选择对话框(查找器, self)
            
            # 连接信号
            对话框.窗口已选择.connect(self._处理窗口选择)
            
            # 显示对话框
            对话框.exec()
            
        except Exception as e:
            提示对话框.警告提示(self, "错误", f"打开窗口选择对话框失败: {e}")
    
    def _处理窗口选择(self, 句柄: int):
        """处理窗口选择信号
        
        需求: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6
        
        参数:
            句柄: 选中的窗口句柄
        """
        try:
            from 核心.窗口检测 import 窗口查找器
            
            查找器 = 窗口查找器()
            窗口信息 = 查找器.获取窗口信息(句柄)
            
            if 窗口信息:
                self._填充窗口参数(窗口信息)
            else:
                提示对话框.警告提示(self, "错误", "无法获取窗口信息，窗口可能已关闭")
                
        except Exception as e:
            提示对话框.警告提示(self, "错误", f"处理窗口选择失败: {e}")
    
    def _填充窗口参数(self, 窗口信息):
        """填充窗口参数到界面
        
        需求: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6
        
        参数:
            窗口信息: 窗口信息对象，包含位置和大小属性
        """
        try:
            # 设置窗口X坐标 (需求 5.1)
            x信息 = self._控件字典.get("窗口设置.窗口X")
            if x信息:
                self._设置控件值(x信息.控件, 窗口信息.位置[0])
            
            # 设置窗口Y坐标 (需求 5.2)
            y信息 = self._控件字典.get("窗口设置.窗口Y")
            if y信息:
                self._设置控件值(y信息.控件, 窗口信息.位置[1])
            
            # 设置窗口宽度 (需求 5.3)
            宽度信息 = self._控件字典.get("窗口设置.窗口宽度")
            if 宽度信息:
                self._设置控件值(宽度信息.控件, 窗口信息.大小[0])
            
            # 设置窗口高度 (需求 5.4)
            高度信息 = self._控件字典.get("窗口设置.窗口高度")
            if 高度信息:
                self._设置控件值(高度信息.控件, 窗口信息.大小[1])
            
            # 更新窗口预览 (需求 5.5)
            self.更新预览()
            
            # 标记配置为已修改状态 (需求 5.6)
            self._标记已修改()
            
            # 更新状态提示
            self._状态标签.setText(f"✓ 已选择窗口: {窗口信息.标题[:20]}...")
            self._状态标签.setStyleSheet(f"color: {颜色.成功};")
            
        except Exception as e:
            提示对话框.警告提示(self, "错误", f"填充窗口参数失败: {e}")


def 启动配置界面(配置管理器=None):
    """启动配置界面（独立窗口模式）
    
    参数:
        配置管理器: 可选的配置管理器实例
    """
    from 界面.样式.主题 import 应用全局字体
    
    app = QApplication.instance()
    新创建应用 = False
    if app is None:
        app = QApplication(sys.argv)
        新创建应用 = True
        # 应用支持 emoji 的全局字体（需求: 1.4, 3.2）
        应用全局字体(app)
    
    # 创建独立模式的配置界面（嵌入模式=False）
    界面 = 配置界面(配置管理器, 嵌入模式=False)
    界面.show()
    
    # 如果是新创建的应用，启动事件循环
    if 新创建应用 and not QApplication.instance().closingDown():
        app.exec()


if __name__ == "__main__":
    启动配置界面()
