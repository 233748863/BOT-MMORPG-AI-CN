# -*- coding: utf-8 -*-
"""
导航栏组件

实现左侧导航栏，包含导航项列表、选中状态高亮和页面切换信号。
"""

from PySide6.QtWidgets import QListWidget, QListWidgetItem
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont


class NavigationBar(QListWidget):
    """
    左侧导航栏组件
    
    显示所有功能模块的导航项，支持选中状态高亮和点击切换页面。
    """
    
    # 信号定义
    导航项点击 = Signal(str)  # 发送被点击的页面名称
    
    # 导航项配置: (图标, 名称)
    导航项配置 = [
        ("🏠", "首页"),
        ("🎥", "数据收集"),
        ("🧠", "训练"),
        ("🤖", "运行"),
        ("⚙️", "配置"),
        ("📁", "数据管理"),
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
        
        # 设置固定宽度
        self.setFixedWidth(130)
        
        # 设置字体
        字体 = QFont()
        字体.setPointSize(11)
        self.setFont(字体)
        
        # 禁用水平滚动条
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # 初始化导航项
        self._初始化导航项()
        
        # 连接信号
        self.currentRowChanged.connect(self._处理选中变化)
        
        # 默认选中首页
        self.setCurrentRow(0)
    
    def _初始化导航项(self) -> None:
        """初始化导航项列表"""
        for 图标, 名称 in self.导航项配置:
            item = QListWidgetItem(f"{图标}  {名称}")
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
