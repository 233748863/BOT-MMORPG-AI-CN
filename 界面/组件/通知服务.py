# -*- coding: utf-8 -*-
"""
通知服务组件

实现弹出通知功能（右下角Toast）和错误通知详情查看。
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QGraphicsOpacityEffect,
    QDialog, QTextEdit, QApplication
)
from PySide6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve,
    Signal, QPoint, QSize
)
from PySide6.QtGui import QFont, QColor
from typing import Optional, List
from dataclasses import dataclass
from datetime import datetime


@dataclass
class 通知数据:
    """通知数据类"""
    标题: str
    内容: str
    类型: str  # "info", "success", "warning", "error"
    时间戳: str
    详情: Optional[str] = None


class ToastNotification(QFrame):
    """
    Toast通知弹窗组件
    
    在屏幕右下角显示的临时通知，自动消失。
    """
    
    # 信号定义
    关闭信号 = Signal()
    查看详情信号 = Signal(str)
    
    # 类型配置
    类型配置 = {
        "info": {
            "图标": "ℹ️",
            "背景色": "#EFF6FF",
            "边框色": "#3B82F6",
            "文字色": "#1E40AF"
        },
        "success": {
            "图标": "✅",
            "背景色": "#ECFDF5",
            "边框色": "#10B981",
            "文字色": "#065F46"
        },
        "warning": {
            "图标": "⚠️",
            "背景色": "#FFFBEB",
            "边框色": "#F59E0B",
            "文字色": "#92400E"
        },
        "error": {
            "图标": "❌",
            "背景色": "#FEF2F2",
            "边框色": "#EF4444",
            "文字色": "#991B1B"
        }
    }
    
    def __init__(self, 通知: 通知数据, parent=None):
        """
        初始化Toast通知
        
        参数:
            通知: 通知数据
            parent: 父部件
        """
        super().__init__(parent)
        
        self._通知 = 通知
        self._配置 = self.类型配置.get(通知.类型, self.类型配置["info"])
        
        # 设置窗口属性
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.Tool |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        
        # 设置固定宽度
        self.setFixedWidth(320)
        
        # 初始化界面
        self._初始化界面()
        
        # 设置自动关闭定时器
        self._关闭定时器 = QTimer(self)
        self._关闭定时器.setSingleShot(True)
        self._关闭定时器.timeout.connect(self._开始淡出动画)
    
    def _初始化界面(self) -> None:
        """初始化界面布局"""
        # 设置样式
        self.setStyleSheet(f"""
            ToastNotification {{
                background-color: {self._配置['背景色']};
                border: 1px solid {self._配置['边框色']};
                border-radius: 8px;
                border-left: 4px solid {self._配置['边框色']};
            }}
        """)
        
        布局 = QVBoxLayout(self)
        布局.setContentsMargins(12, 10, 12, 10)
        布局.setSpacing(6)
        
        # 标题行
        标题行 = QHBoxLayout()
        标题行.setSpacing(8)
        
        # 图标
        图标标签 = QLabel(self._配置['图标'])
        图标标签.setFont(QFont("Segoe UI Emoji", 14))
        标题行.addWidget(图标标签)
        
        # 标题
        标题标签 = QLabel(self._通知.标题)
        标题标签.setStyleSheet(f"color: {self._配置['文字色']}; font-weight: bold;")
        标题行.addWidget(标题标签, 1)
        
        # 关闭按钮
        关闭按钮 = QPushButton("×")
        关闭按钮.setFixedSize(20, 20)
        关闭按钮.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                color: {self._配置['文字色']};
                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: rgba(0, 0, 0, 0.1);
                border-radius: 4px;
            }}
        """)
        关闭按钮.clicked.connect(self._关闭)
        标题行.addWidget(关闭按钮)
        
        布局.addLayout(标题行)
        
        # 内容
        内容标签 = QLabel(self._通知.内容)
        内容标签.setStyleSheet(f"color: {self._配置['文字色']};")
        内容标签.setWordWrap(True)
        布局.addWidget(内容标签)
        
        # 如果有详情，添加查看详情按钮
        if self._通知.详情:
            详情按钮 = QPushButton("查看详情")
            详情按钮.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    border: none;
                    color: {self._配置['边框色']};
                    text-decoration: underline;
                    padding: 0;
                    text-align: left;
                }}
                QPushButton:hover {{
                    color: {self._配置['文字色']};
                }}
            """)
            详情按钮.setCursor(Qt.CursorShape.PointingHandCursor)
            详情按钮.clicked.connect(lambda: self.查看详情信号.emit(self._通知.详情))
            布局.addWidget(详情按钮)
    
    def 显示(self, 持续时间: int = 5000) -> None:
        """
        显示通知
        
        参数:
            持续时间: 显示持续时间（毫秒）
        """
        self.show()
        self._关闭定时器.start(持续时间)
    
    def _开始淡出动画(self) -> None:
        """开始淡出动画"""
        self._透明度效果 = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._透明度效果)
        
        self._淡出动画 = QPropertyAnimation(self._透明度效果, b"opacity")
        self._淡出动画.setDuration(300)
        self._淡出动画.setStartValue(1.0)
        self._淡出动画.setEndValue(0.0)
        self._淡出动画.setEasingCurve(QEasingCurve.Type.OutQuad)
        self._淡出动画.finished.connect(self._关闭)
        self._淡出动画.start()
    
    def _关闭(self) -> None:
        """关闭通知"""
        self._关闭定时器.stop()
        self.关闭信号.emit()
        self.close()
        self.deleteLater()


class ErrorDetailDialog(QDialog):
    """错误详情对话框"""
    
    def __init__(self, 详情: str, parent=None):
        """
        初始化错误详情对话框
        
        参数:
            详情: 错误详情内容
            parent: 父部件
        """
        super().__init__(parent)
        
        self.setWindowTitle("错误详情")
        self.setMinimumSize(500, 300)
        self.setModal(True)
        
        布局 = QVBoxLayout(self)
        布局.setContentsMargins(16, 16, 16, 16)
        布局.setSpacing(12)
        
        # 详情文本
        详情文本 = QTextEdit()
        详情文本.setReadOnly(True)
        详情文本.setPlainText(详情)
        详情文本.setFont(QFont("Consolas", 10))
        布局.addWidget(详情文本)
        
        # 按钮行
        按钮行 = QHBoxLayout()
        按钮行.addStretch()
        
        复制按钮 = QPushButton("复制")
        复制按钮.clicked.connect(lambda: QApplication.clipboard().setText(详情))
        按钮行.addWidget(复制按钮)
        
        关闭按钮 = QPushButton("关闭")
        关闭按钮.clicked.connect(self.close)
        按钮行.addWidget(关闭按钮)
        
        布局.addLayout(按钮行)


class NotificationService(QWidget):
    """
    通知服务
    
    管理应用程序的通知显示，支持:
    - 右下角Toast弹出通知
    - 错误通知详情查看
    - 通知队列管理
    """
    
    # 最大同时显示的通知数量
    最大通知数 = 3
    
    # 通知间距
    通知间距 = 10
    
    def __init__(self, parent=None):
        """
        初始化通知服务
        
        参数:
            parent: 父部件（通常是主窗口）
        """
        super().__init__(parent)
        
        # 当前显示的通知列表
        self._当前通知: List[ToastNotification] = []
        
        # 通知历史记录
        self._通知历史: List[通知数据] = []
        
        # 隐藏自身（服务组件不需要显示）
        self.hide()
    
    def 显示通知(
        self, 
        标题: str, 
        内容: str, 
        类型: str = "info",
        详情: Optional[str] = None,
        持续时间: int = 5000
    ) -> None:
        """
        显示通知
        
        参数:
            标题: 通知标题
            内容: 通知内容
            类型: 通知类型 ("info", "success", "warning", "error")
            详情: 详细信息（可选，用于错误通知）
            持续时间: 显示持续时间（毫秒）
        """
        # 创建通知数据
        通知 = 通知数据(
            标题=标题,
            内容=内容,
            类型=类型,
            时间戳=datetime.now().strftime("%H:%M:%S"),
            详情=详情
        )
        
        # 添加到历史记录
        self._通知历史.append(通知)
        
        # 如果已达到最大数量，移除最早的通知
        if len(self._当前通知) >= self.最大通知数:
            最早通知 = self._当前通知[0]
            最早通知._关闭()
        
        # 创建Toast通知
        toast = ToastNotification(通知)
        toast.关闭信号.connect(lambda: self._移除通知(toast))
        toast.查看详情信号.connect(self._显示错误详情)
        
        # 添加到当前通知列表
        self._当前通知.append(toast)
        
        # 计算位置并显示
        self._更新通知位置()
        toast.显示(持续时间)
    
    def 显示信息(self, 标题: str, 内容: str) -> None:
        """显示信息通知"""
        self.显示通知(标题, 内容, "info")
    
    def 显示成功(self, 标题: str, 内容: str) -> None:
        """显示成功通知"""
        self.显示通知(标题, 内容, "success")
    
    def 显示警告(self, 标题: str, 内容: str) -> None:
        """显示警告通知"""
        self.显示通知(标题, 内容, "warning")
    
    def 显示错误(self, 标题: str, 内容: str, 详情: Optional[str] = None) -> None:
        """
        显示错误通知
        
        参数:
            标题: 错误标题
            内容: 错误简要描述
            详情: 详细错误信息（如堆栈跟踪）
        """
        self.显示通知(标题, 内容, "error", 详情, 持续时间=8000)
    
    def _移除通知(self, toast: ToastNotification) -> None:
        """
        从当前通知列表中移除通知
        
        参数:
            toast: 要移除的通知
        """
        if toast in self._当前通知:
            self._当前通知.remove(toast)
            self._更新通知位置()
    
    def _更新通知位置(self) -> None:
        """更新所有通知的位置"""
        # 获取屏幕尺寸
        屏幕 = QApplication.primaryScreen()
        if not 屏幕:
            return
        
        屏幕几何 = 屏幕.availableGeometry()
        
        # 从底部向上排列通知
        当前Y = 屏幕几何.bottom() - self.通知间距
        
        for toast in reversed(self._当前通知):
            toast.adjustSize()
            通知高度 = toast.sizeHint().height()
            当前Y -= 通知高度
            
            X = 屏幕几何.right() - toast.width() - self.通知间距
            toast.move(X, 当前Y)
            
            当前Y -= self.通知间距
    
    def _显示错误详情(self, 详情: str) -> None:
        """
        显示错误详情对话框
        
        参数:
            详情: 错误详情内容
        """
        对话框 = ErrorDetailDialog(详情, self.parent())
        对话框.exec()
    
    def 获取通知历史(self) -> List[通知数据]:
        """
        获取通知历史记录
        
        返回:
            通知数据列表的副本
        """
        return self._通知历史.copy()
    
    def 清空历史(self) -> None:
        """清空通知历史记录"""
        self._通知历史.clear()
