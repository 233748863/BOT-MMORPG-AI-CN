# -*- coding: utf-8 -*-
"""
导航栏组件

实现左侧导航栏，包含导航项列表、选中状态高亮和页面切换信号。
优化后的导航栏宽度为100px，导航项具有统一的高度、间距和内边距，
选中项有明显的左侧指示条样式。

Requirements: 8.1, 8.2, 8.4, 8.5
"""

from PySide6.QtWidgets import QListWidget, QListWidgetItem
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont

from 界面.样式.布局常量 import 布局常量
from 界面.样式.主题 import 颜色


class NavigationBar(QListWidget):
    """
    左侧导航栏组件
    
    显示所有功能模块的导航项，支持选中状态高亮和点击切换页面。
    
    样式规范:
    - 固定宽度: 100px (Requirements 8.1)
    - 导航项垂直居中显示图标和文字 (Requirements 8.2)
    - 导航项垂直间距: 4px (Requirements 8.4)
    - 选中项有背景色和左侧指示条 (Requirements 8.5)
    """
    
    # 信号定义
    导航项点击 = Signal(str)  # 发送被点击的页面名称
    
    # 导航项配置: (图标, 名称)
    导航项配置 = [
        ("", "首页"),
        ("", "数据收集"),
        ("", "训练"),
        ("", "运行"),
        ("", "配置"),
        ("", "数据管理"),
    ]
    
    def __init__(self, parent=None):
        """
        初始化导航栏
        
        参数:
            parent: 父部件
        """
        super().__init__(parent)
        
        # 设置对象名称，用于QSS样式
        self.setObjectName("导航栏")
        
        # 设置固定宽度为100px (Requirements 8.1)
        self.setFixedWidth(布局常量.导航栏宽度)
        
        # 设置字体
        字体 = QFont()
        字体.setPointSize(11)
        self.setFont(字体)
        
        # 禁用水平滚动条
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # 应用优化后的样式
        self._应用样式()
        
        # 初始化导航项
        self._初始化导航项()
        
        # 连接信号
        self.currentRowChanged.connect(self._处理选中变化)
        
        # 默认选中首页
        self.setCurrentRow(0)
    
    def _应用样式(self) -> None:
        """
        应用优化后的导航栏样式
        
        样式包括:
        - 导航栏背景和边框
        - 导航项高度、间距、内边距
        - 选中项背景色和左侧指示条
        - 悬停效果
        """
        self.setStyleSheet(f"""
            QListWidget#导航栏 {{
                background-color: {颜色.卡片背景};
                border: none;
                border-right: 1px solid {颜色.边框};
                font-size: 12px;
                outline: none;
                padding: 8px 0;
            }}
            
            QListWidget#导航栏::item {{
                height: {布局常量.导航项高度}px;
                padding: 0 {布局常量.导航项内边距}px;
                border-radius: {布局常量.导航项圆角}px;
                margin: {布局常量.导航项间距}px 6px;
            }}
            
            QListWidget#导航栏::item:selected {{
                background-color: {颜色.选中背景};
                color: {颜色.主色};
                border-left: {布局常量.导航项左侧指示条宽度}px solid {颜色.主色};
            }}
            
            QListWidget#导航栏::item:hover:!selected {{
                background-color: {颜色.悬停背景};
            }}
        """)
    
    def _初始化导航项(self) -> None:
        """初始化导航项列表"""
        for 图标, 名称 in self.导航项配置:
            # 如果图标为空，只显示名称
            显示文本 = f"{图标}  {名称}" if 图标 else 名称
            item = QListWidgetItem(显示文本)
            item.setData(Qt.UserRole, 名称)  # 存储页面名称
            item.setSizeHint(item.sizeHint())
            self.addItem(item)
    
    def _处理选中变化(self, 行号: int) -> None:
        """
        处理导航项选中变化
        
        参数:
            行号: 当前选中的行号
        """
        if 行号 >= 0:
            item = self.item(行号)
            if item:
                页面名称 = item.data(Qt.UserRole)
                self.导航项点击.emit(页面名称)
    
    def 设置选中项(self, 页面名称: str) -> None:
        """
        设置当前选中的导航项
        
        参数:
            页面名称: 要选中的页面名称
        """
        for i in range(self.count()):
            item = self.item(i)
            if item and item.data(Qt.UserRole) == 页面名称:
                self.setCurrentRow(i)
                break
    
    def 获取当前选中项(self) -> str:
        """
        获取当前选中的页面名称
        
        返回:
            当前选中的页面名称，如果没有选中则返回空字符串
        """
        当前项 = self.currentItem()
        if 当前项:
            return 当前项.data(Qt.UserRole)
        return ""
    
    def 获取所有页面名称(self) -> list:
        """
        获取所有页面名称列表
        
        返回:
            页面名称列表
        """
        return [名称 for _, 名称 in self.导航项配置]
    
    def 获取导航栏宽度(self) -> int:
        """
        获取导航栏的固定宽度
        
        返回:
            导航栏宽度（像素）
        """
        return self.width()
    
    def 获取导航项高度(self) -> int:
        """
        获取导航项的高度
        
        返回:
            导航项高度（像素）
        """
        return 布局常量.导航项高度
    
    def 获取导航项间距(self) -> int:
        """
        获取导航项之间的垂直间距
        
        返回:
            导航项间距（像素）
        """
        return 布局常量.导航项间距
    
    def 获取导航项内边距(self) -> int:
        """
        获取导航项的内边距
        
        返回:
            导航项内边距（像素）
        """
        return 布局常量.导航项内边距
    
    def 获取左侧指示条宽度(self) -> int:
        """
        获取选中项左侧指示条的宽度
        
        返回:
            左侧指示条宽度（像素）
        """
        return 布局常量.导航项左侧指示条宽度
