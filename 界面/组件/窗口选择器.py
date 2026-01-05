# -*- coding: utf-8 -*-
"""
窗口选择器组件

提供 GUI 版本的窗口选择功能，包括:
- 窗口列表界面（带缩略图）
- 关键词过滤
- 点击选择模式（倒计时、捕获、确认）

需求:
- 2.1: 显示窗口列表界面
- 2.3: 关键词过滤
- 2.4: 点击列表选择窗口
- 5.1: 点击选择模式
- 5.2: 捕获用户点击的窗口
- 5.3: 倒计时显示
- 5.4: 确认选择
"""

import time
from typing import Optional, List
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QListWidget, QListWidgetItem, QWidget,
    QMessageBox, QFrame, QSizePolicy, QApplication
)
from PySide6.QtCore import Qt, Signal, QTimer, QSize
from PySide6.QtGui import QPixmap, QImage, QFont

from 界面.样式.主题 import 颜色
from 界面.样式.布局常量 import 布局常量
from 界面.组件.通用组件 import 确认对话框, 提示对话框

# 导入窗口检测模块
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from 核心.窗口检测 import 窗口查找器, 窗口信息


class 窗口列表项(QWidget):
    """窗口列表项组件，显示窗口缩略图和信息"""
    
    def __init__(self, 窗口: 窗口信息, 缩略图: Optional[any] = None, parent=None):
        super().__init__(parent)
        self._窗口 = 窗口
        self._缩略图 = 缩略图
        self._初始化界面()
    
    def _初始化界面(self):
        """初始化界面"""
        布局 = QHBoxLayout(self)
        布局.setContentsMargins(8, 8, 8, 8)
        布局.setSpacing(12)
        
        # 缩略图
        缩略图标签 = QLabel()
        缩略图标签.setFixedSize(120, 90)
        缩略图标签.setStyleSheet(f"""
            background-color: {颜色.背景};
            border: 1px solid {颜色.边框};
            border-radius: 4px;
        """)
        缩略图标签.setAlignment(Qt.AlignCenter)
        
        if self._缩略图 is not None:
            try:
                import numpy as np
                # 将 numpy 数组转换为 QPixmap
                高度, 宽度, 通道 = self._缩略图.shape
                字节数 = 通道 * 宽度
                图像 = QImage(self._缩略图.data, 宽度, 高度, 字节数, QImage.Format_RGB888)
                像素图 = QPixmap.fromImage(图像)
                缩略图标签.setPixmap(像素图.scaled(
                    120, 90, Qt.KeepAspectRatio, Qt.SmoothTransformation
                ))
            except Exception:
                缩略图标签.setText("[图片]")
        else:
            缩略图标签.setText("[图片]")
        
        布局.addWidget(缩略图标签)
        
        # 窗口信息
        信息容器 = QWidget()
        信息布局 = QVBoxLayout(信息容器)
        信息布局.setContentsMargins(0, 0, 0, 0)
        信息布局.setSpacing(4)
        
        # 标题
        标题标签 = QLabel(self._窗口.标题[:40] + ("..." if len(self._窗口.标题) > 40 else ""))
        标题标签.setStyleSheet(f"""
            font-size: 13px;
            font-weight: bold;
            color: {颜色.标题};
        """)
        信息布局.addWidget(标题标签)
        
        # 进程名
        进程标签 = QLabel(f"进程: {self._窗口.进程名}")
        进程标签.setStyleSheet(f"font-size: 11px; color: {颜色.次要文字};")
        信息布局.addWidget(进程标签)
        
        # 大小和状态
        状态文字 = "[最小化]" if self._窗口.是否最小化 else "[正常]"
        状态标签 = QLabel(f"大小: {self._窗口.大小[0]}x{self._窗口.大小[1]} | {状态文字}")
        状态标签.setStyleSheet(f"font-size: 11px; color: {颜色.次要文字};")
        信息布局.addWidget(状态标签)
        
        信息布局.addStretch()
        布局.addWidget(信息容器, 1)
    
    @property
    def 窗口(self) -> 窗口信息:
        """获取窗口信息"""
        return self._窗口


class 窗口选择对话框(QDialog):
    """
    窗口选择对话框
    
    提供 GUI 界面选择窗口，支持:
    - 窗口列表显示（带缩略图）
    - 关键词过滤
    - 点击选择模式
    """
    
    # 信号
    窗口已选择 = Signal(int)  # 发送选中的窗口句柄
    
    def __init__(self, 查找器: 窗口查找器 = None, parent=None):
        super().__init__(parent)
        self._查找器 = 查找器 or 窗口查找器()
        self._窗口列表: List[窗口信息] = []
        self._选中句柄: Optional[int] = None
        self._倒计时定时器: Optional[QTimer] = None
        self._倒计时剩余: int = 0
        
        self._初始化界面()
        self._刷新窗口列表()
    
    def _初始化界面(self):
        """初始化界面"""
        self.setWindowTitle("选择游戏窗口")
        self.setFixedSize(600, 500)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {颜色.背景};
            }}
        """)
        
        主布局 = QVBoxLayout(self)
        主布局.setContentsMargins(16, 16, 16, 16)
        主布局.setSpacing(12)
        
        # 标题
        标题标签 = QLabel("选择游戏窗口")
        标题标签.setStyleSheet(f"""
            font-size: 18px;
            font-weight: bold;
            color: {颜色.标题};
        """)
        主布局.addWidget(标题标签)
        
        # 搜索栏
        搜索容器 = QWidget()
        搜索布局 = QHBoxLayout(搜索容器)
        搜索布局.setContentsMargins(0, 0, 0, 0)
        搜索布局.setSpacing(8)
        
        self._搜索框 = QLineEdit()
        self._搜索框.setPlaceholderText("输入关键词过滤窗口...")
        self._搜索框.setStyleSheet(f"""
            QLineEdit {{
                border: 1px solid {颜色.边框};
                border-radius: 6px;
                padding: 8px 12px;
                background-color: {颜色.卡片背景};
                font-size: 12px;
                min-height: 32px;
                max-height: 32px;
            }}
            QLineEdit:focus {{
                border-color: {颜色.主色};
            }}
        """)
        self._搜索框.textChanged.connect(self._过滤窗口列表)
        搜索布局.addWidget(self._搜索框, 1)
        
        刷新按钮 = QPushButton("刷新")
        刷新按钮.setStyleSheet(f"""
            QPushButton {{
                background-color: {颜色.卡片背景};
                color: {颜色.文字};
                border: 1px solid {颜色.边框};
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 12px;
                min-height: 32px;
                max-height: 32px;
            }}
            QPushButton:hover {{
                background-color: {颜色.悬停背景};
            }}
        """)
        刷新按钮.clicked.connect(self._刷新窗口列表)
        搜索布局.addWidget(刷新按钮)
        
        主布局.addWidget(搜索容器)
        
        # 窗口列表
        self._列表控件 = QListWidget()
        self._列表控件.setStyleSheet(f"""
            QListWidget {{
                background-color: {颜色.卡片背景};
                border: 1px solid {颜色.边框};
                border-radius: 8px;
                outline: none;
            }}
            QListWidget::item {{
                border-bottom: 1px solid {颜色.边框};
                padding: 4px;
            }}
            QListWidget::item:selected {{
                background-color: {颜色.选中背景};
                border-left: 3px solid {颜色.主色};
            }}
            QListWidget::item:hover:!selected {{
                background-color: {颜色.悬停背景};
            }}
        """)
        self._列表控件.itemDoubleClicked.connect(self._确认选择)
        self._列表控件.itemClicked.connect(self._选择项目)
        主布局.addWidget(self._列表控件, 1)
        
        # 点击选择模式区域
        点击选择容器 = QFrame()
        点击选择容器.setStyleSheet(f"""
            QFrame {{
                background-color: {颜色.卡片背景};
                border: 1px solid {颜色.边框};
                border-radius: 8px;
            }}
        """)
        点击选择布局 = QHBoxLayout(点击选择容器)
        点击选择布局.setContentsMargins(12, 12, 12, 12)
        
        点击选择说明 = QLabel("或者使用点击选择模式:")
        点击选择说明.setStyleSheet(f"color: {颜色.次要文字}; font-size: 12px;")
        点击选择布局.addWidget(点击选择说明)
        
        点击选择布局.addStretch()
        
        self._倒计时标签 = QLabel("")
        self._倒计时标签.setStyleSheet(f"""
            font-size: 14px;
            font-weight: bold;
            color: {颜色.主色};
        """)
        self._倒计时标签.hide()
        点击选择布局.addWidget(self._倒计时标签)
        
        self._点击选择按钮 = QPushButton("点击选择")
        self._点击选择按钮.setStyleSheet(f"""
            QPushButton {{
                background-color: {颜色.成功};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 12px;
                min-height: 32px;
            }}
            QPushButton:hover {{
                background-color: #059669;
            }}
            QPushButton:disabled {{
                background-color: {颜色.按钮禁用};
            }}
        """)
        self._点击选择按钮.clicked.connect(self._启动点击选择模式)
        点击选择布局.addWidget(self._点击选择按钮)
        
        主布局.addWidget(点击选择容器)
        
        # 按钮区域
        按钮容器 = QWidget()
        按钮布局 = QHBoxLayout(按钮容器)
        按钮布局.setContentsMargins(0, 0, 0, 0)
        按钮布局.setSpacing(12)
        
        按钮布局.addStretch()
        
        取消按钮 = QPushButton("取消")
        取消按钮.setStyleSheet(f"""
            QPushButton {{
                background-color: {颜色.卡片背景};
                color: {颜色.文字};
                border: 1px solid {颜色.边框};
                border-radius: 6px;
                padding: 8px 24px;
                font-size: 12px;
                min-height: 32px;
            }}
            QPushButton:hover {{
                background-color: {颜色.悬停背景};
            }}
        """)
        取消按钮.clicked.connect(self.reject)
        按钮布局.addWidget(取消按钮)
        
        self._确认按钮 = QPushButton("确认选择")
        self._确认按钮.setEnabled(False)
        self._确认按钮.setStyleSheet(f"""
            QPushButton {{
                background-color: {颜色.主色};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 24px;
                font-size: 12px;
                min-height: 32px;
            }}
            QPushButton:hover {{
                background-color: {颜色.主色悬停};
            }}
            QPushButton:disabled {{
                background-color: {颜色.按钮禁用};
                color: {颜色.禁用文字};
            }}
        """)
        self._确认按钮.clicked.connect(self._确认选择)
        按钮布局.addWidget(self._确认按钮)
        
        主布局.addWidget(按钮容器)
    
    def _刷新窗口列表(self):
        """刷新窗口列表"""
        self._窗口列表 = self._查找器.获取所有窗口()
        self._更新列表显示()
    
    def _过滤窗口列表(self, 关键词: str):
        """根据关键词过滤窗口列表"""
        self._更新列表显示(关键词)
    
    def _更新列表显示(self, 过滤关键词: str = None):
        """更新列表显示"""
        self._列表控件.clear()
        
        显示列表 = self._窗口列表
        
        # 过滤
        if 过滤关键词:
            关键词小写 = 过滤关键词.lower()
            显示列表 = [w for w in 显示列表 
                       if 关键词小写 in w.标题.lower() or 关键词小写 in w.进程名.lower()]
        
        for 窗口 in 显示列表:
            # 获取缩略图
            缩略图 = self._查找器.获取窗口缩略图(窗口.句柄, (120, 90))
            
            # 创建列表项
            项目 = QListWidgetItem()
            项目.setSizeHint(QSize(0, 110))
            项目.setData(Qt.UserRole, 窗口.句柄)
            
            # 创建自定义组件
            组件 = 窗口列表项(窗口, 缩略图)
            
            self._列表控件.addItem(项目)
            self._列表控件.setItemWidget(项目, 组件)
        
        if not 显示列表:
            项目 = QListWidgetItem("未找到匹配的窗口")
            项目.setFlags(Qt.NoItemFlags)
            self._列表控件.addItem(项目)
    
    def _选择项目(self, 项目: QListWidgetItem):
        """选择列表项"""
        句柄 = 项目.data(Qt.UserRole)
        if 句柄:
            self._选中句柄 = 句柄
            self._确认按钮.setEnabled(True)
    
    def _确认选择(self, 项目: QListWidgetItem = None):
        """确认选择"""
        if 项目:
            句柄 = 项目.data(Qt.UserRole)
            if 句柄:
                self._选中句柄 = 句柄
        
        if self._选中句柄:
            # 获取窗口信息进行确认
            信息 = self._查找器.获取窗口信息(self._选中句柄)
            if 信息:
                确认结果 = 确认对话框.询问(
                    self,
                    "确认选择",
                    f"确认选择以下窗口?\n\n"
                    f"标题: {信息.标题}\n"
                    f"进程: {信息.进程名}\n"
                    f"大小: {信息.大小[0]}x{信息.大小[1]}",
                    "确定",
                    "取消"
                )
                
                if 确认结果 == 确认对话框.确认:
                    self.窗口已选择.emit(self._选中句柄)
                    self.accept()
            else:
                提示对话框.警告提示(self, "错误", "窗口已不存在，请重新选择")
                self._刷新窗口列表()
    
    def _启动点击选择模式(self):
        """启动点击选择模式"""
        self._点击选择按钮.setEnabled(False)
        self._倒计时剩余 = 3
        self._倒计时标签.show()
        self._更新倒计时显示()
        
        # 启动倒计时定时器
        self._倒计时定时器 = QTimer(self)
        self._倒计时定时器.timeout.connect(self._倒计时更新)
        self._倒计时定时器.start(1000)
    
    def _倒计时更新(self):
        """倒计时更新"""
        self._倒计时剩余 -= 1
        
        if self._倒计时剩余 > 0:
            self._更新倒计时显示()
        else:
            self._倒计时定时器.stop()
            self._倒计时标签.setText("请点击目标窗口!")
            
            # 最小化当前窗口
            self.showMinimized()
            
            # 延迟捕获前台窗口
            QTimer.singleShot(500, self._捕获点击窗口)
    
    def _更新倒计时显示(self):
        """更新倒计时显示"""
        self._倒计时标签.setText(f"{self._倒计时剩余} 秒后请点击目标窗口...")
    
    def _捕获点击窗口(self):
        """捕获用户点击的窗口"""
        # 恢复窗口
        self.showNormal()
        self.activateWindow()
        
        # 获取前台窗口
        窗口 = self._查找器.获取前台窗口()
        
        self._倒计时标签.hide()
        self._点击选择按钮.setEnabled(True)
        
        if 窗口 and 窗口.句柄 != int(self.winId()):
            self._选中句柄 = 窗口.句柄
            
            # 显示确认对话框
            确认结果 = 确认对话框.询问(
                self,
                "确认选择",
                f"已捕获窗口:\n\n"
                f"标题: {窗口.标题}\n"
                f"进程: {窗口.进程名}\n"
                f"大小: {窗口.大小[0]}x{窗口.大小[1]}\n\n"
                f"确认选择此窗口?",
                "确定",
                "取消"
            )
            
            if 确认结果 == 确认对话框.确认:
                self.窗口已选择.emit(self._选中句柄)
                self.accept()
        else:
            提示对话框.警告提示(self, "提示", "未能捕获到有效窗口，请重试")
    
    def 获取选中句柄(self) -> Optional[int]:
        """获取选中的窗口句柄"""
        return self._选中句柄


class GUI窗口选择器:
    """
    GUI 版本的窗口选择器
    
    提供与命令行版本相同的接口，但使用 GUI 对话框
    """
    
    def __init__(self, 查找器: 窗口查找器 = None):
        self._查找器 = 查找器 or 窗口查找器()
    
    def 显示列表(self, 过滤关键词: str = None, parent=None) -> Optional[int]:
        """
        显示窗口列表供用户选择
        
        参数:
            过滤关键词: 过滤窗口的关键词
            parent: 父窗口
            
        返回:
            选中的窗口句柄，取消返回 None
        """
        对话框 = 窗口选择对话框(self._查找器, parent)
        
        if 过滤关键词:
            对话框._搜索框.setText(过滤关键词)
        
        if 对话框.exec() == QDialog.Accepted:
            return 对话框.获取选中句柄()
        
        return None
    
    def 点击选择模式(self, 倒计时: int = 3, parent=None) -> Optional[int]:
        """
        启动点击选择模式
        
        参数:
            倒计时: 进入选择模式前的倒计时秒数
            parent: 父窗口
            
        返回:
            选中的窗口句柄
        """
        对话框 = 窗口选择对话框(self._查找器, parent)
        
        # 自动启动点击选择模式
        QTimer.singleShot(100, 对话框._启动点击选择模式)
        
        if 对话框.exec() == QDialog.Accepted:
            return 对话框.获取选中句柄()
        
        return None
    
    def 确认选择(self, 句柄: int, parent=None) -> bool:
        """
        确认窗口选择
        
        参数:
            句柄: 窗口句柄
            parent: 父窗口
            
        返回:
            用户是否确认
        """
        信息 = self._查找器.获取窗口信息(句柄)
        
        if not 信息:
            提示对话框.警告提示(parent, "错误", "窗口不存在")
            return False
        
        确认结果 = 确认对话框.询问(
            parent,
            "确认选择",
            f"确认选择以下窗口?\n\n"
            f"标题: {信息.标题}\n"
            f"进程: {信息.进程名}\n"
            f"大小: {信息.大小[0]}x{信息.大小[1]}",
            "确定",
            "取消"
        )
        
        return 确认结果 == 确认对话框.确认
