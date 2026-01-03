# -*- coding: utf-8 -*-
"""
通用组件模块

提供可复用的通用UI组件，包括:
- Card: 通用卡片组件，带标题、图标的内容容器
- 动画管理器: 统一的动画效果管理

符合设计规范:
- 卡片圆角: 8px (Requirements 9.1)
- 卡片边框: 1px #E2E8F0 (Requirements 9.2)
- 卡片背景: #FFFFFF (Requirements 9.3)
- 卡片标题: 13px加粗 (Requirements 9.4)
- 标题与内容间距: 8px (Requirements 9.5)
- 图标与标题垂直居中 (Requirements 9.6)
"""

from typing import Optional
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, 
    QWidget, QLayout, QSizePolicy, QGraphicsOpacityEffect
)
from PySide6.QtCore import (
    Qt, QPropertyAnimation, QEasingCurve, 
    QParallelAnimationGroup, QSequentialAnimationGroup
)
from PySide6.QtGui import QFont

from 界面.样式.布局常量 import 布局常量
from 界面.样式.主题 import 颜色


class Card(QFrame):
    """
    通用卡片组件
    
    提供统一样式的卡片容器，支持:
    - 可选的标题和图标
    - 统一的圆角、边框、内边距样式
    - 灵活的内容添加方式
    
    样式规范:
    - 圆角: 8px (Requirements 9.1)
    - 边框: 1px #E2E8F0 (Requirements 9.2)
    - 背景: #FFFFFF (Requirements 9.3)
    - 标题字号: 13px加粗 (Requirements 9.4)
    - 标题与内容间距: 8px (Requirements 9.5)
    """
    
    def __init__(
        self, 
        标题: str = "", 
        图标: str = "", 
        parent: Optional[QWidget] = None
    ):
        """
        初始化卡片组件
        
        参数:
            标题: 卡片标题文字
            图标: 卡片标题图标（emoji或图标字符）
            parent: 父组件
        """
        super().__init__(parent)
        self._标题 = 标题
        self._图标 = 图标
        self._标题标签: Optional[QLabel] = None
        self._内容布局: Optional[QVBoxLayout] = None
        
        self._初始化样式()
        self._初始化布局()
    
    def _初始化样式(self) -> None:
        """初始化卡片样式"""
        # 设置对象名称用于QSS选择器
        self.setObjectName("Card")
        
        # 应用卡片样式
        self.setStyleSheet(f"""
            QFrame#Card {{
                background-color: {颜色.卡片背景};
                border-radius: {布局常量.卡片圆角}px;
                border: {布局常量.卡片边框宽度}px solid {颜色.边框};
            }}
        """)
        
        # 设置最小高度
        self.setMinimumHeight(布局常量.卡片最小高度)
        
        # 设置大小策略
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
    
    def _初始化布局(self) -> None:
        """初始化卡片布局"""
        self._主布局 = QVBoxLayout(self)
        self._主布局.setContentsMargins(
            布局常量.卡片内边距,
            布局常量.卡片内边距,
            布局常量.卡片内边距,
            布局常量.卡片内边距
        )
        self._主布局.setSpacing(布局常量.标题下边距)
        
        # 如果有标题，创建标题区域
        if self._标题:
            self._创建标题区域()
        
        # 创建内容区域
        self._内容容器 = QWidget()
        self._内容布局 = QVBoxLayout(self._内容容器)
        self._内容布局.setContentsMargins(0, 0, 0, 0)
        self._内容布局.setSpacing(8)
        self._主布局.addWidget(self._内容容器)
    
    def _创建标题区域(self) -> None:
        """创建标题区域，包含图标和标题文字"""
        标题容器 = QWidget()
        标题布局 = QHBoxLayout(标题容器)
        标题布局.setContentsMargins(0, 0, 0, 0)
        标题布局.setSpacing(6)
        
        # 组合图标和标题
        if self._图标:
            标题文本 = f"{self._图标} {self._标题}"
        else:
            标题文本 = self._标题
        
        self._标题标签 = QLabel(标题文本)
        self._标题标签.setObjectName("CardTitle")
        
        # 设置标题样式 (Requirements 9.4, 9.5)
        字体 = QFont()
        字体.setPointSize(布局常量.卡片标题字号)
        字体.setBold(True)
        self._标题标签.setFont(字体)
        
        self._标题标签.setStyleSheet(f"""
            QLabel#CardTitle {{
                color: {颜色.标题};
                padding-bottom: 4px;
            }}
        """)
        
        # 垂直居中对齐 (Requirements 9.6)
        标题布局.addWidget(self._标题标签, alignment=Qt.AlignVCenter)
        标题布局.addStretch()
        
        self._主布局.addWidget(标题容器)
    
    def 添加内容(self, widget: QWidget) -> None:
        """
        添加内容组件到卡片
        
        参数:
            widget: 要添加的组件
        """
        if self._内容布局:
            self._内容布局.addWidget(widget)
    
    def 添加布局(self, layout: QLayout) -> None:
        """
        添加布局到卡片
        
        参数:
            layout: 要添加的布局
        """
        if self._内容布局:
            self._内容布局.addLayout(layout)
    
    def 添加伸展(self, stretch: int = 1) -> None:
        """
        添加伸展空间
        
        参数:
            stretch: 伸展因子
        """
        if self._内容布局:
            self._内容布局.addStretch(stretch)
    
    def 设置标题(self, 标题: str, 图标: str = "") -> None:
        """
        更新卡片标题
        
        参数:
            标题: 新的标题文字
            图标: 新的图标（可选）
        """
        self._标题 = 标题
        if 图标:
            self._图标 = 图标
        
        if self._标题标签:
            if self._图标:
                self._标题标签.setText(f"{self._图标} {self._标题}")
            else:
                self._标题标签.setText(self._标题)
    
    def 获取内容布局(self) -> Optional[QVBoxLayout]:
        """
        获取内容区域的布局
        
        返回:
            内容区域的QVBoxLayout
        """
        return self._内容布局
    
    @property
    def 标题(self) -> str:
        """获取卡片标题"""
        return self._标题
    
    @property
    def 图标(self) -> str:
        """获取卡片图标"""
        return self._图标
    
    @property
    def 圆角(self) -> int:
        """获取卡片圆角值"""
        return 布局常量.卡片圆角
    
    @property
    def 边框宽度(self) -> int:
        """获取卡片边框宽度"""
        return 布局常量.卡片边框宽度
    
    @property
    def 内边距(self) -> int:
        """获取卡片内边距"""
        return 布局常量.卡片内边距


class CardWithAction(Card):
    """
    带操作按钮的卡片组件
    
    在标题栏右侧提供操作按钮区域
    """
    
    def __init__(
        self, 
        标题: str = "", 
        图标: str = "", 
        parent: Optional[QWidget] = None
    ):
        self._操作区域: Optional[QHBoxLayout] = None
        super().__init__(标题, 图标, parent)
    
    def _创建标题区域(self) -> None:
        """创建带操作区域的标题"""
        标题容器 = QWidget()
        标题布局 = QHBoxLayout(标题容器)
        标题布局.setContentsMargins(0, 0, 0, 0)
        标题布局.setSpacing(6)
        
        # 组合图标和标题
        if self._图标:
            标题文本 = f"{self._图标} {self._标题}"
        else:
            标题文本 = self._标题
        
        self._标题标签 = QLabel(标题文本)
        self._标题标签.setObjectName("CardTitle")
        
        # 设置标题样式
        字体 = QFont()
        字体.setPointSize(布局常量.卡片标题字号)
        字体.setBold(True)
        self._标题标签.setFont(字体)
        
        self._标题标签.setStyleSheet(f"""
            QLabel#CardTitle {{
                color: {颜色.标题};
                padding-bottom: 4px;
            }}
        """)
        
        标题布局.addWidget(self._标题标签, alignment=Qt.AlignVCenter)
        标题布局.addStretch()
        
        # 创建操作区域
        self._操作区域 = QHBoxLayout()
        self._操作区域.setSpacing(布局常量.按钮间距)
        标题布局.addLayout(self._操作区域)
        
        self._主布局.addWidget(标题容器)
    
    def 添加操作按钮(self, widget: QWidget) -> None:
        """
        添加操作按钮到标题栏
        
        参数:
            widget: 要添加的按钮组件
        """
        if self._操作区域:
            self._操作区域.addWidget(widget)


class 动画管理器:
    """
    统一的动画管理器
    
    提供各种UI动画效果，包括:
    - 淡入淡出动画
    - 页面切换动画
    - 滑动动画
    
    动画时长规范:
    - 快速动画: 150ms
    - 标准动画: 200ms
    - 慢速动画: 300ms
    - 所有动画时长在100-300ms范围内
    """
    
    # 动画时长常量（毫秒）
    快速动画 = 布局常量.动画时长快速  # 150ms
    标准动画 = 布局常量.动画时长标准  # 200ms
    慢速动画 = 布局常量.动画时长慢速  # 300ms
    
    @staticmethod
    def 创建淡入动画(
        widget: QWidget, 
        时长: int = None,
        起始透明度: float = 0.0,
        结束透明度: float = 1.0
    ) -> QPropertyAnimation:
        """
        创建淡入动画
        
        参数:
            widget: 目标组件
            时长: 动画时长（毫秒），默认使用标准动画时长
            起始透明度: 起始透明度值 (0.0-1.0)
            结束透明度: 结束透明度值 (0.0-1.0)
        
        返回:
            QPropertyAnimation 动画对象
        """
        if 时长 is None:
            时长 = 动画管理器.标准动画
        
        # 确保时长在合理范围内
        时长 = max(布局常量.动画时长最小, min(时长, 布局常量.动画时长最大))
        
        # 创建透明度效果
        效果 = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(效果)
        
        # 创建动画
        动画 = QPropertyAnimation(效果, b"opacity")
        动画.setDuration(时长)
        动画.setStartValue(起始透明度)
        动画.setEndValue(结束透明度)
        动画.setEasingCurve(QEasingCurve.OutCubic)
        
        return 动画
    
    @staticmethod
    def 创建淡出动画(
        widget: QWidget, 
        时长: int = None,
        起始透明度: float = 1.0,
        结束透明度: float = 0.0
    ) -> QPropertyAnimation:
        """
        创建淡出动画
        
        参数:
            widget: 目标组件
            时长: 动画时长（毫秒），默认使用标准动画时长
            起始透明度: 起始透明度值 (0.0-1.0)
            结束透明度: 结束透明度值 (0.0-1.0)
        
        返回:
            QPropertyAnimation 动画对象
        """
        if 时长 is None:
            时长 = 动画管理器.标准动画
        
        # 确保时长在合理范围内
        时长 = max(布局常量.动画时长最小, min(时长, 布局常量.动画时长最大))
        
        # 创建透明度效果
        效果 = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(效果)
        
        # 创建动画
        动画 = QPropertyAnimation(效果, b"opacity")
        动画.setDuration(时长)
        动画.setStartValue(起始透明度)
        动画.setEndValue(结束透明度)
        动画.setEasingCurve(QEasingCurve.InCubic)
        
        return 动画
    
    @staticmethod
    def 创建页面切换动画(
        旧页面: QWidget, 
        新页面: QWidget, 
        时长: int = None
    ) -> QParallelAnimationGroup:
        """
        创建页面切换动画组
        
        同时执行旧页面淡出和新页面淡入动画
        
        参数:
            旧页面: 要隐藏的页面
            新页面: 要显示的页面
            时长: 动画时长（毫秒），默认使用标准动画时长
        
        返回:
            QParallelAnimationGroup 动画组对象
        """
        if 时长 is None:
            时长 = 动画管理器.标准动画
        
        # 确保时长在合理范围内
        时长 = max(布局常量.动画时长最小, min(时长, 布局常量.动画时长最大))
        
        动画组 = QParallelAnimationGroup()
        
        # 旧页面淡出
        淡出动画 = 动画管理器.创建淡出动画(旧页面, 时长)
        动画组.addAnimation(淡出动画)
        
        # 新页面淡入
        淡入动画 = 动画管理器.创建淡入动画(新页面, 时长)
        动画组.addAnimation(淡入动画)
        
        return 动画组
    
    @staticmethod
    def 创建顺序动画(
        动画列表: list,
    ) -> QSequentialAnimationGroup:
        """
        创建顺序执行的动画组
        
        参数:
            动画列表: QPropertyAnimation 对象列表
        
        返回:
            QSequentialAnimationGroup 动画组对象
        """
        动画组 = QSequentialAnimationGroup()
        
        for 动画 in 动画列表:
            动画组.addAnimation(动画)
        
        return 动画组
    
    @staticmethod
    def 创建并行动画(
        动画列表: list,
    ) -> QParallelAnimationGroup:
        """
        创建并行执行的动画组
        
        参数:
            动画列表: QPropertyAnimation 对象列表
        
        返回:
            QParallelAnimationGroup 动画组对象
        """
        动画组 = QParallelAnimationGroup()
        
        for 动画 in 动画列表:
            动画组.addAnimation(动画)
        
        return 动画组
    
    @staticmethod
    def 验证动画时长(时长: int) -> bool:
        """
        验证动画时长是否在合理范围内
        
        参数:
            时长: 动画时长（毫秒）
        
        返回:
            是否在100-300ms范围内
        """
        return 布局常量.动画时长最小 <= 时长 <= 布局常量.动画时长最大
    
    @staticmethod
    def 获取安全时长(时长: int) -> int:
        """
        获取安全的动画时长（限制在合理范围内）
        
        参数:
            时长: 期望的动画时长（毫秒）
        
        返回:
            限制在100-300ms范围内的时长
        """
        return max(布局常量.动画时长最小, min(时长, 布局常量.动画时长最大))


class 页面切换管理器:
    """
    页面切换管理器
    
    管理页面切换动画和状态
    """
    
    def __init__(self):
        self._当前动画: Optional[QParallelAnimationGroup] = None
        self._当前页面: Optional[QWidget] = None
    
    def 切换页面(
        self, 
        旧页面: QWidget, 
        新页面: QWidget, 
        时长: int = None,
        完成回调: callable = None
    ) -> None:
        """
        执行页面切换
        
        参数:
            旧页面: 要隐藏的页面
            新页面: 要显示的页面
            时长: 动画时长（毫秒）
            完成回调: 动画完成后的回调函数
        """
        # 如果有正在进行的动画，先停止
        if self._当前动画 and self._当前动画.state() == QParallelAnimationGroup.Running:
            self._当前动画.stop()
        
        # 创建切换动画
        self._当前动画 = 动画管理器.创建页面切换动画(旧页面, 新页面, 时长)
        
        # 连接完成信号
        if 完成回调:
            self._当前动画.finished.connect(完成回调)
        
        # 显示新页面并开始动画
        新页面.show()
        self._当前动画.start()
        self._当前页面 = 新页面
    
    def 停止动画(self) -> None:
        """停止当前动画"""
        if self._当前动画:
            self._当前动画.stop()
    
    @property
    def 当前页面(self) -> Optional[QWidget]:
        """获取当前显示的页面"""
        return self._当前页面
