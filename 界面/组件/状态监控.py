# -*- coding: utf-8 -*-
"""
状态监控组件

实现状态颜色编码（绿色/黄色/红色）和游戏画面预览功能。
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QFrame, QGridLayout, QSizePolicy
)
from PySide6.QtCore import Qt, Slot, QSize
from PySide6.QtGui import QImage, QPixmap, QFont, QPainter, QColor
from typing import Dict, Optional, Any
import numpy as np

from 界面.样式.主题 import 颜色, 获取状态颜色


class StatusIndicator(QWidget):
    """
    状态指示器组件
    
    显示单个状态项，包含标签和状态值，支持颜色编码。
    """
    
    def __init__(self, 标签: str, parent=None):
        """
        初始化状态指示器
        
        参数:
            标签: 状态项标签
            parent: 父部件
        """
        super().__init__(parent)
        
        self._标签 = 标签
        self._值 = "--"
        self._状态类型 = "正常"
        
        self._初始化界面()
    
    def _初始化界面(self) -> None:
        """初始化界面布局"""
        布局 = QHBoxLayout(self)
        布局.setContentsMargins(0, 4, 0, 4)
        布局.setSpacing(8)
        
        # 状态指示点
        self._指示点 = QLabel("●")
        self._指示点.setFixedWidth(16)
        self._指示点.setStyleSheet(f"color: {颜色.成功};")
        布局.addWidget(self._指示点)
        
        # 标签
        标签控件 = QLabel(f"{self._标签}:")
        标签控件.setStyleSheet(f"color: {颜色.次要文字};")
        布局.addWidget(标签控件)
        
        # 值
        self._值标签 = QLabel(self._值)
        self._值标签.setStyleSheet(f"color: {颜色.文字}; font-weight: 500;")
        布局.addWidget(self._值标签, 1)
    
    def 设置值(self, 值: str) -> None:
        """
        设置状态值
        
        参数:
            值: 状态值文本
        """
        self._值 = 值
        self._值标签.setText(值)
    
    def 设置状态(self, 状态类型: str) -> None:
        """
        设置状态类型，更新颜色编码
        
        参数:
            状态类型: "正常", "警告", "错误"
        """
        self._状态类型 = 状态类型
        颜色值 = 获取状态颜色(状态类型)
        self._指示点.setStyleSheet(f"color: {颜色值};")
    
    def 获取状态(self) -> str:
        """
        获取当前状态类型
        
        返回:
            状态类型字符串
        """
        return self._状态类型


class ImagePreview(QLabel):
    """
    图像预览组件
    
    显示游戏画面预览，支持numpy数组输入。
    """
    
    def __init__(self, parent=None):
        """
        初始化图像预览
        
        参数:
            parent: 父部件
        """
        super().__init__(parent)
        
        # 设置默认大小
        self.setMinimumSize(160, 90)
        self.setMaximumSize(320, 180)
        
        # 设置样式
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {颜色.背景};
                border: 1px solid {颜色.边框};
                border-radius: 6px;
            }}
        """)
        
        # 设置对齐方式
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 设置缩放策略
        self.setScaledContents(False)
        
        # 显示占位文本
        self.setText("暂无画面")
        self.setStyleSheet(self.styleSheet() + f"color: {颜色.次要文字};")
    
    def 更新图像(self, 图像: np.ndarray) -> None:
        """
        更新预览图像
        
        参数:
            图像: numpy数组格式的图像 (BGR或RGB格式)
        """
        if 图像 is None or 图像.size == 0:
            self.setText("暂无画面")
            return
        
        try:
            # 获取图像尺寸
            高度, 宽度 = 图像.shape[:2]
            
            # 确定图像格式
            if len(图像.shape) == 2:
                # 灰度图
                格式 = QImage.Format.Format_Grayscale8
                字节数 = 宽度
            elif 图像.shape[2] == 3:
                # BGR转RGB
                图像 = 图像[:, :, ::-1].copy()
                格式 = QImage.Format.Format_RGB888
                字节数 = 宽度 * 3
            elif 图像.shape[2] == 4:
                # BGRA转RGBA
                图像 = 图像[:, :, [2, 1, 0, 3]].copy()
                格式 = QImage.Format.Format_RGBA8888
                字节数 = 宽度 * 4
            else:
                return
            
            # 创建QImage
            q图像 = QImage(图像.data, 宽度, 高度, 字节数, 格式)
            
            # 缩放到适合的大小
            缩放后 = q图像.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            
            # 设置图像
            self.setPixmap(QPixmap.fromImage(缩放后))
            
        except Exception as e:
            self.setText(f"图像错误: {str(e)}")
    
    def 清空(self) -> None:
        """清空预览图像"""
        self.clear()
        self.setText("暂无画面")


class StatusMonitor(QWidget):
    """
    状态监控组件
    
    显示实时状态信息，包含:
    - 多个状态指示器（带颜色编码）
    - 游戏画面预览
    """
    
    def __init__(self, parent=None):
        """
        初始化状态监控
        
        参数:
            parent: 父部件
        """
        super().__init__(parent)
        
        # 状态指示器字典
        self._状态指示器: Dict[str, StatusIndicator] = {}
        
        # 初始化界面
        self._初始化界面()
    
    def _初始化界面(self) -> None:
        """初始化界面布局"""
        布局 = QVBoxLayout(self)
        布局.setContentsMargins(0, 0, 0, 0)
        布局.setSpacing(12)
        
        # 状态卡片
        状态卡片 = QFrame()
        状态卡片.setProperty("class", "card")
        状态卡片布局 = QVBoxLayout(状态卡片)
        状态卡片布局.setContentsMargins(16, 12, 16, 12)
        状态卡片布局.setSpacing(4)
        
        # 标题
        标题 = QLabel("📊 状态监控")
        标题.setProperty("class", "subtitle")
        状态卡片布局.addWidget(标题)
        
        # 状态网格
        self._状态网格 = QGridLayout()
        self._状态网格.setSpacing(8)
        状态卡片布局.addLayout(self._状态网格)
        
        布局.addWidget(状态卡片)
        
        # 画面预览卡片
        预览卡片 = QFrame()
        预览卡片.setProperty("class", "card")
        预览卡片布局 = QVBoxLayout(预览卡片)
        预览卡片布局.setContentsMargins(16, 12, 16, 12)
        预览卡片布局.setSpacing(8)
        
        # 预览标题
        预览标题 = QLabel("🎮 画面预览")
        预览标题.setProperty("class", "subtitle")
        预览卡片布局.addWidget(预览标题)
        
        # 图像预览
        self._图像预览 = ImagePreview()
        预览卡片布局.addWidget(self._图像预览, 1)
        
        布局.addWidget(预览卡片, 1)
    
    def 添加状态项(self, 键: str, 标签: str, 初始值: str = "--") -> None:
        """
        添加状态项
        
        参数:
            键: 状态项唯一标识
            标签: 状态项显示标签
            初始值: 初始值
        """
        if 键 in self._状态指示器:
            return
        
        指示器 = StatusIndicator(标签)
        指示器.设置值(初始值)
        
        # 计算位置
        行 = len(self._状态指示器) // 2
        列 = len(self._状态指示器) % 2
        
        self._状态网格.addWidget(指示器, 行, 列)
        self._状态指示器[键] = 指示器
    
    def 更新状态项(self, 键: str, 值: str, 状态类型: str = "正常") -> None:
        """
        更新状态项
        
        参数:
            键: 状态项唯一标识
            值: 新的状态值
            状态类型: 状态类型 ("正常", "警告", "错误")
        """
        if 键 in self._状态指示器:
            self._状态指示器[键].设置值(值)
            self._状态指示器[键].设置状态(状态类型)
    
    @Slot(dict)
    def 更新状态(self, 状态数据: dict) -> None:
        """
        批量更新状态
        
        参数:
            状态数据: 状态数据字典，格式为 {键: (值, 状态类型)} 或 {键: 值}
        """
        for 键, 数据 in 状态数据.items():
            if isinstance(数据, tuple):
                值, 状态类型 = 数据
            else:
                值 = str(数据)
                状态类型 = "正常"
            
            self.更新状态项(键, 值, 状态类型)
    
    def 更新预览图像(self, 图像: np.ndarray) -> None:
        """
        更新游戏画面预览
        
        参数:
            图像: numpy数组格式的图像
        """
        self._图像预览.更新图像(图像)
    
    def 清空预览(self) -> None:
        """清空画面预览"""
        self._图像预览.清空()
    
    def 设置状态颜色(self, 键: str, 状态类型: str) -> None:
        """
        设置状态项的颜色编码
        
        参数:
            键: 状态项唯一标识
            状态类型: "正常" (绿色), "警告" (黄色), "错误" (红色)
        """
        if 键 in self._状态指示器:
            self._状态指示器[键].设置状态(状态类型)
    
    def 获取状态项(self, 键: str) -> Optional[StatusIndicator]:
        """
        获取状态指示器
        
        参数:
            键: 状态项唯一标识
            
        返回:
            状态指示器实例，如果不存在则返回None
        """
        return self._状态指示器.get(键)
    
    def 获取所有状态(self) -> Dict[str, str]:
        """
        获取所有状态项的当前状态类型
        
        返回:
            状态字典 {键: 状态类型}
        """
        return {键: 指示器.获取状态() for 键, 指示器 in self._状态指示器.items()}
