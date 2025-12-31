# -*- coding: utf-8 -*-
"""
日志查看器组件

实现带时间戳的日志显示、级别过滤、搜索和导出功能。
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, 
    QLineEdit, QComboBox, QPushButton, QLabel, QFileDialog
)
from PySide6.QtCore import Slot, Qt
from PySide6.QtGui import QTextCharFormat, QColor, QFont
from datetime import datetime
from typing import List, Optional
from dataclasses import dataclass


@dataclass
class 日志条目:
    """日志条目数据类"""
    时间戳: str
    级别: str
    消息: str
    
    def 格式化(self) -> str:
        """格式化为显示字符串"""
        return f"[{self.时间戳}] [{self.级别}] {self.消息}"


class LogViewer(QWidget):
    """
    日志查看器组件
    
    功能:
    - 显示带时间戳的日志消息
    - 支持按日志级别（信息/警告/错误）过滤
    - 支持搜索日志内容
    - 支持导出日志到文件
    """
    
    # 日志级别配置
    日志级别 = ["全部", "信息", "警告", "错误"]
    
    # 级别颜色映射
    级别颜色 = {
        "信息": "#334155",   # 深灰色
        "警告": "#F59E0B",   # 黄色
        "错误": "#EF4444",   # 红色
    }
    
    def __init__(self, parent=None):
        """
        初始化日志查看器
        
        参数:
            parent: 父部件
        """
        super().__init__(parent)
        
        # 日志存储列表
        self._日志列表: List[日志条目] = []
        
        # 当前过滤条件
        self._当前级别过滤 = "全部"
        self._当前搜索关键词 = ""
        
        # 初始化界面
        self._初始化界面()
    
    def _初始化界面(self) -> None:
        """初始化界面布局"""
        布局 = QVBoxLayout(self)
        布局.setContentsMargins(0, 0, 0, 0)
        布局.setSpacing(8)
        
        # 工具栏
        工具栏 = self._创建工具栏()
        布局.addLayout(工具栏)
        
        # 日志显示区域
        self._日志显示 = QTextEdit()
        self._日志显示.setReadOnly(True)
        self._日志显示.setFont(QFont("Consolas", 10))
        self._日志显示.setPlaceholderText("暂无日志...")
        布局.addWidget(self._日志显示)
    
    def _创建工具栏(self) -> QHBoxLayout:
        """创建工具栏布局"""
        工具栏 = QHBoxLayout()
        工具栏.setSpacing(8)
        
        # 级别过滤下拉框
        级别标签 = QLabel("级别:")
        工具栏.addWidget(级别标签)
        
        self._级别选择 = QComboBox()
        self._级别选择.addItems(self.日志级别)
        self._级别选择.setFixedWidth(80)
        self._级别选择.currentTextChanged.connect(self._处理级别过滤)
        工具栏.addWidget(self._级别选择)
        
        # 搜索框
        搜索标签 = QLabel("搜索:")
        工具栏.addWidget(搜索标签)
        
        self._搜索框 = QLineEdit()
        self._搜索框.setPlaceholderText("输入关键词...")
        self._搜索框.textChanged.connect(self._处理搜索)
        self._搜索框.setClearButtonEnabled(True)
        工具栏.addWidget(self._搜索框, 1)
        
        # 清空按钮
        清空按钮 = QPushButton("清空")
        清空按钮.setProperty("class", "secondary")
        清空按钮.setFixedWidth(60)
        清空按钮.clicked.connect(self.清空日志)
        工具栏.addWidget(清空按钮)
        
        # 导出按钮
        导出按钮 = QPushButton("导出")
        导出按钮.setProperty("class", "secondary")
        导出按钮.setFixedWidth(60)
        导出按钮.clicked.connect(self._处理导出)
        工具栏.addWidget(导出按钮)
        
        return 工具栏
    
    def 添加日志(self, 级别: str, 消息: str) -> None:
        """
        添加日志条目，自动添加时间戳
        
        参数:
            级别: 日志级别 ("信息", "警告", "错误")
            消息: 日志消息内容
        """
        时间戳 = datetime.now().strftime("%H:%M:%S")
        条目 = 日志条目(时间戳=时间戳, 级别=级别, 消息=消息)
        self._日志列表.append(条目)
        
        # 如果符合当前过滤条件，则显示
        if self._符合过滤条件(条目):
            self._追加日志显示(条目)
    
    def _符合过滤条件(self, 条目: 日志条目) -> bool:
        """
        检查日志条目是否符合当前过滤条件
        
        参数:
            条目: 日志条目
            
        返回:
            是否符合过滤条件
        """
        # 检查级别过滤
        if self._当前级别过滤 != "全部" and 条目.级别 != self._当前级别过滤:
            return False
        
        # 检查搜索关键词
        if self._当前搜索关键词:
            关键词 = self._当前搜索关键词.lower()
            if 关键词 not in 条目.消息.lower():
                return False
        
        return True
    
    def _追加日志显示(self, 条目: 日志条目) -> None:
        """
        追加日志到显示区域
        
        参数:
            条目: 日志条目
        """
        # 设置文本颜色
        格式 = QTextCharFormat()
        颜色 = self.级别颜色.get(条目.级别, "#334155")
        格式.setForeground(QColor(颜色))
        
        # 移动光标到末尾
        光标 = self._日志显示.textCursor()
        光标.movePosition(光标.MoveOperation.End)
        
        # 插入格式化文本
        光标.insertText(条目.格式化() + "\n", 格式)
        
        # 滚动到底部
        self._日志显示.verticalScrollBar().setValue(
            self._日志显示.verticalScrollBar().maximum()
        )
    
    def _刷新日志显示(self) -> None:
        """根据当前过滤条件刷新日志显示"""
        self._日志显示.clear()
        
        for 条目 in self._日志列表:
            if self._符合过滤条件(条目):
                self._追加日志显示(条目)
    
    @Slot(str)
    def _处理级别过滤(self, 级别: str) -> None:
        """
        处理级别过滤变化
        
        参数:
            级别: 选中的级别
        """
        self._当前级别过滤 = 级别
        self._刷新日志显示()
    
    @Slot(str)
    def _处理搜索(self, 关键词: str) -> None:
        """
        处理搜索关键词变化
        
        参数:
            关键词: 搜索关键词
        """
        self._当前搜索关键词 = 关键词
        self._刷新日志显示()
    
    def 过滤日志(self, 级别: str) -> List[日志条目]:
        """
        按级别过滤日志
        
        参数:
            级别: 日志级别 ("全部", "信息", "警告", "错误")
            
        返回:
            符合条件的日志条目列表
        """
        if 级别 == "全部":
            return self._日志列表.copy()
        return [条目 for 条目 in self._日志列表 if 条目.级别 == 级别]
    
    def 搜索日志(self, 关键词: str) -> List[日志条目]:
        """
        搜索日志内容
        
        参数:
            关键词: 搜索关键词
            
        返回:
            包含关键词的日志条目列表
        """
        if not 关键词:
            return self._日志列表.copy()
        
        关键词 = 关键词.lower()
        return [条目 for 条目 in self._日志列表 if 关键词 in 条目.消息.lower()]
    
    def 导出日志(self, 文件路径: str) -> bool:
        """
        导出日志到文件
        
        参数:
            文件路径: 导出文件路径
            
        返回:
            是否导出成功
        """
        try:
            with open(文件路径, 'w', encoding='utf-8') as f:
                for 条目 in self._日志列表:
                    f.write(条目.格式化() + "\n")
            return True
        except Exception as e:
            self.添加日志("错误", f"导出日志失败: {str(e)}")
            return False
    
    def _处理导出(self) -> None:
        """处理导出按钮点击"""
        文件路径, _ = QFileDialog.getSaveFileName(
            self,
            "导出日志",
            f"日志_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "文本文件 (*.txt);;所有文件 (*.*)"
        )
        
        if 文件路径:
            if self.导出日志(文件路径):
                self.添加日志("信息", f"日志已导出到: {文件路径}")
    
    def 清空日志(self) -> None:
        """清空所有日志"""
        self._日志列表.clear()
        self._日志显示.clear()
    
    def 获取日志数量(self) -> int:
        """
        获取日志总数量
        
        返回:
            日志条目数量
        """
        return len(self._日志列表)
    
    def 获取所有日志(self) -> List[日志条目]:
        """
        获取所有日志条目
        
        返回:
            日志条目列表的副本
        """
        return self._日志列表.copy()
