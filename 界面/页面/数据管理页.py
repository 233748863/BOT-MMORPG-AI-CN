# -*- coding: utf-8 -*-
"""
数据管理页面

提供训练数据文件的管理功能:
- 文件列表显示 (文件名/大小/时间/样本数)
- 文件详细信息显示
- 数据分布统计图表
- 预处理和清洗快捷按钮
- 删除确认对话框

布局规范:
- 左右两栏布局，左栏65%，右栏35% (Requirements 7.1)
- 左栏：操作按钮 + 数据文件列表 (Requirements 7.2, 7.5)
- 右栏上部：文件详细信息 (Requirements 7.3)
- 右栏下部：数据分布统计 (Requirements 7.4)
"""

import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

import numpy as np
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QProgressDialog, QSizePolicy, QScrollArea
)
from PySide6.QtCore import Qt, Signal, QThread, Slot
from PySide6.QtGui import QColor

from 界面.样式.主题 import 颜色
from 界面.样式.布局常量 import 布局常量
from 界面.组件.通用组件 import Card, 确认对话框, 提示对话框


class 数据文件信息:
    """数据文件信息类"""
    
    def __init__(self, 文件路径: str):
        self.文件路径 = 文件路径
        self.文件名 = os.path.basename(文件路径)
        self.文件大小 = 0
        self.创建时间 = None
        self.样本数量 = 0
        self.动作分布 = {}
        self._加载信息()
    
    def _加载信息(self) -> None:
        """加载文件信息"""
        try:
            路径 = Path(self.文件路径)
            if 路径.exists():
                统计信息 = 路径.stat()
                self.文件大小 = 统计信息.st_size
                self.创建时间 = datetime.fromtimestamp(统计信息.st_mtime)
                
                # 加载样本数量和动作分布
                self._加载样本信息()
        except Exception as e:
            print(f"加载文件信息失败: {e}")
    
    def _加载样本信息(self) -> None:
        """加载样本数量和动作分布"""
        try:
            if self.文件路径.endswith('.npy'):
                数据 = np.load(self.文件路径, allow_pickle=True)
                self.样本数量 = len(数据)
                
                # 统计动作分布
                for 样本 in 数据:
                    if len(样本) >= 2:
                        动作 = 样本[1]
                        if isinstance(动作, (list, np.ndarray)):
                            动作索引 = int(np.argmax(动作))
                        else:
                            动作索引 = int(动作)
                        self.动作分布[动作索引] = self.动作分布.get(动作索引, 0) + 1
                        
            elif self.文件路径.endswith('.npz'):
                数据 = np.load(self.文件路径, allow_pickle=True)
                if 'images' in 数据:
                    self.样本数量 = len(数据['images'])
                elif 'frames' in 数据:
                    self.样本数量 = len(数据['frames'])
                    
                # 尝试获取动作分布
                if 'actions' in 数据 or 'labels' in 数据:
                    动作数据 = 数据.get('actions', 数据.get('labels', []))
                    for 动作 in 动作数据:
                        if isinstance(动作, (list, np.ndarray)):
                            动作索引 = int(np.argmax(动作))
                        else:
                            动作索引 = int(动作)
                        self.动作分布[动作索引] = self.动作分布.get(动作索引, 0) + 1
        except Exception as e:
            print(f"加载样本信息失败: {e}")
    
    def 格式化大小(self) -> str:
        """格式化文件大小"""
        if self.文件大小 < 1024:
            return f"{self.文件大小} B"
        elif self.文件大小 < 1024 * 1024:
            return f"{self.文件大小 / 1024:.1f} KB"
        elif self.文件大小 < 1024 * 1024 * 1024:
            return f"{self.文件大小 / (1024 * 1024):.1f} MB"
        else:
            return f"{self.文件大小 / (1024 * 1024 * 1024):.2f} GB"
    
    def 格式化时间(self) -> str:
        """格式化创建时间"""
        if self.创建时间:
            return self.创建时间.strftime("%Y-%m-%d %H:%M")
        return "未知"


class 数据扫描线程(QThread):
    """后台扫描数据文件的线程"""
    
    扫描完成 = Signal(list)  # 文件信息列表
    扫描进度 = Signal(int, int)  # 当前, 总数
    
    def __init__(self, 数据目录: str, parent=None):
        super().__init__(parent)
        self.数据目录 = 数据目录
    
    def run(self):
        """执行扫描"""
        文件列表 = []
        
        try:
            目录 = Path(self.数据目录)
            if not 目录.exists():
                self.扫描完成.emit([])
                return
            
            # 获取所有数据文件
            数据文件 = list(目录.glob("*.npy")) + list(目录.glob("*.npz"))
            总数 = len(数据文件)
            
            for 索引, 文件路径 in enumerate(数据文件):
                self.扫描进度.emit(索引 + 1, 总数)
                文件信息 = 数据文件信息(str(文件路径))
                文件列表.append(文件信息)
            
            # 按修改时间排序（最新的在前）
            文件列表.sort(key=lambda x: x.创建时间 or datetime.min, reverse=True)
            
        except Exception as e:
            print(f"扫描数据文件失败: {e}")
        
        self.扫描完成.emit(文件列表)


class 数据处理线程(QThread):
    """后台数据处理线程"""
    
    处理完成 = Signal(bool, str)  # 是否成功, 消息
    处理进度 = Signal(int, str)  # 进度百分比, 状态消息
    
    def __init__(self, 操作类型: str, 文件列表: List[str], parent=None):
        super().__init__(parent)
        self.操作类型 = 操作类型
        self.文件列表 = 文件列表
    
    def run(self):
        """执行处理"""
        try:
            if self.操作类型 == "预处理":
                self._执行预处理()
            elif self.操作类型 == "清洗":
                self._执行清洗()
            elif self.操作类型 == "删除":
                self._执行删除()
        except Exception as e:
            self.处理完成.emit(False, f"处理失败: {str(e)}")
    
    def _执行预处理(self):
        """执行数据预处理"""
        from 工具.数据预处理 import 预处理数据文件
        
        总数 = len(self.文件列表)
        for 索引, 文件路径 in enumerate(self.文件列表):
            进度 = int((索引 + 1) / 总数 * 100)
            self.处理进度.emit(进度, f"预处理: {os.path.basename(文件路径)}")
            预处理数据文件(文件路径, 增强=True, 增强倍数=2)
        
        self.处理完成.emit(True, f"预处理完成，共处理 {总数} 个文件")
    
    def _执行清洗(self):
        """执行数据清洗"""
        from 工具.数据清洗 import 清洗数据文件
        
        总数 = len(self.文件列表)
        for 索引, 文件路径 in enumerate(self.文件列表):
            进度 = int((索引 + 1) / 总数 * 100)
            self.处理进度.emit(进度, f"清洗: {os.path.basename(文件路径)}")
            清洗数据文件(文件路径)
        
        self.处理完成.emit(True, f"清洗完成，共处理 {总数} 个文件")
    
    def _执行删除(self):
        """执行文件删除"""
        总数 = len(self.文件列表)
        删除成功 = 0
        
        for 索引, 文件路径 in enumerate(self.文件列表):
            进度 = int((索引 + 1) / 总数 * 100)
            self.处理进度.emit(进度, f"删除: {os.path.basename(文件路径)}")
            try:
                os.remove(文件路径)
                删除成功 += 1
            except Exception as e:
                print(f"删除文件失败: {e}")
        
        self.处理完成.emit(True, f"删除完成，成功删除 {删除成功}/{总数} 个文件")


class 文件详情卡片(Card):
    """文件详细信息卡片组件 (Requirements 7.3)"""
    
    def __init__(self, parent=None):
        super().__init__("📋 文件详情", "", parent)
        self._初始化内容()
    
    def _初始化内容(self) -> None:
        """初始化内容区域"""
        # 文件名
        self._文件名标签 = self._创建信息行("文件名:", "未选择")
        self.添加内容(self._文件名标签)
        
        # 文件大小
        self._大小标签 = self._创建信息行("文件大小:", "-")
        self.添加内容(self._大小标签)
        
        # 修改时间
        self._时间标签 = self._创建信息行("修改时间:", "-")
        self.添加内容(self._时间标签)
        
        # 样本数量
        self._样本标签 = self._创建信息行("样本数量:", "-")
        self.添加内容(self._样本标签)
        
        # 动作类别
        self._类别标签 = self._创建信息行("动作类别:", "-")
        self.添加内容(self._类别标签)
        
        self.添加伸展()
    
    def _创建信息行(self, 标题: str, 初始值: str) -> QWidget:
        """创建信息行"""
        容器 = QWidget()
        布局 = QHBoxLayout(容器)
        布局.setContentsMargins(0, 2, 0, 2)
        布局.setSpacing(8)
        
        标题标签 = QLabel(标题)
        标题标签.setFixedWidth(70)
        标题标签.setStyleSheet(f"color: {颜色.次要文字}; font-size: 11px;")
        布局.addWidget(标题标签)
        
        值标签 = QLabel(初始值)
        值标签.setStyleSheet(f"color: {颜色.文字}; font-size: 12px;")
        值标签.setWordWrap(True)
        布局.addWidget(值标签, 1)
        
        # 保存值标签引用
        容器.值标签 = 值标签
        
        return 容器
    
    def 更新详情(self, 文件信息: Optional[数据文件信息] = None, 
                 选中数量: int = 0, 汇总信息: Dict = None) -> None:
        """
        更新文件详情显示
        
        参数:
            文件信息: 单个文件信息（选中单个文件时）
            选中数量: 选中的文件数量
            汇总信息: 多选时的汇总信息
        """
        if 选中数量 == 0:
            # 未选择文件
            self._文件名标签.值标签.setText("未选择")
            self._大小标签.值标签.setText("-")
            self._时间标签.值标签.setText("-")
            self._样本标签.值标签.setText("-")
            self._类别标签.值标签.setText("-")
        elif 选中数量 == 1 and 文件信息:
            # 选中单个文件
            self._文件名标签.值标签.setText(文件信息.文件名)
            self._大小标签.值标签.setText(文件信息.格式化大小())
            self._时间标签.值标签.setText(文件信息.格式化时间())
            self._样本标签.值标签.setText(f"{文件信息.样本数量:,}")
            self._类别标签.值标签.setText(str(len(文件信息.动作分布)))
        elif 选中数量 > 1 and 汇总信息:
            # 选中多个文件 (Requirements 7.6)
            self._文件名标签.值标签.setText(f"已选择 {选中数量} 个文件")
            self._大小标签.值标签.setText(汇总信息.get("总大小", "-"))
            self._时间标签.值标签.setText("-")
            self._样本标签.值标签.setText(f"{汇总信息.get('总样本', 0):,}")
            self._类别标签.值标签.setText(str(汇总信息.get("类别数", 0)))


class 数据分布卡片(Card):
    """数据分布统计卡片组件 (Requirements 7.4)"""
    
    def __init__(self, parent=None):
        super().__init__("📊 数据分布", "", parent)
        self._初始化内容()
    
    def _初始化内容(self) -> None:
        """初始化内容区域"""
        # 统计概览
        概览容器 = QWidget()
        概览布局 = QHBoxLayout(概览容器)
        概览布局.setContentsMargins(0, 0, 0, 8)
        概览布局.setSpacing(16)
        
        self._文件数标签 = self._创建统计项("📁", "0", "文件")
        概览布局.addWidget(self._文件数标签)
        
        self._样本数标签 = self._创建统计项("📝", "0", "样本")
        概览布局.addWidget(self._样本数标签)
        
        self._总大小标签 = self._创建统计项("💾", "0", "大小")
        概览布局.addWidget(self._总大小标签)
        
        概览布局.addStretch()
        self.添加内容(概览容器)
        
        # 分隔线
        分隔线 = QFrame()
        分隔线.setFrameShape(QFrame.HLine)
        分隔线.setStyleSheet(f"background-color: {颜色.边框};")
        分隔线.setFixedHeight(1)
        self.添加内容(分隔线)
        
        # 动作分布标题
        分布标题 = QLabel("动作分布")
        分布标题.setStyleSheet(f"color: {颜色.次要文字}; font-size: 11px; margin-top: 4px;")
        self.添加内容(分布标题)
        
        # 条形图容器（使用滚动区域）
        滚动区域 = QScrollArea()
        滚动区域.setWidgetResizable(True)
        滚动区域.setFrameShape(QFrame.NoFrame)
        滚动区域.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        滚动区域.setMaximumHeight(150)
        
        self._条形图容器 = QWidget()
        self._条形图布局 = QVBoxLayout(self._条形图容器)
        self._条形图布局.setContentsMargins(0, 4, 0, 0)
        self._条形图布局.setSpacing(2)
        
        滚动区域.setWidget(self._条形图容器)
        self.添加内容(滚动区域)
        
        self.添加伸展()
    
    def _创建统计项(self, 图标: str, 值: str, 标签: str) -> QWidget:
        """创建统计项"""
        容器 = QWidget()
        布局 = QVBoxLayout(容器)
        布局.setContentsMargins(0, 0, 0, 0)
        布局.setSpacing(2)
        
        # 图标和值
        值容器 = QWidget()
        值布局 = QHBoxLayout(值容器)
        值布局.setContentsMargins(0, 0, 0, 0)
        值布局.setSpacing(4)
        
        图标标签 = QLabel(图标)
        图标标签.setStyleSheet("font-size: 14px;")
        值布局.addWidget(图标标签)
        
        值标签 = QLabel(值)
        值标签.setStyleSheet(f"color: {颜色.标题}; font-size: 14px; font-weight: bold;")
        值布局.addWidget(值标签)
        值布局.addStretch()
        
        布局.addWidget(值容器)
        
        # 标签
        标签标签 = QLabel(标签)
        标签标签.setStyleSheet(f"color: {颜色.次要文字}; font-size: 10px;")
        布局.addWidget(标签标签)
        
        # 保存值标签引用
        容器.值标签 = 值标签
        
        return 容器
    
    def 更新统计(self, 文件列表: List[数据文件信息]) -> None:
        """更新统计信息"""
        文件数 = len(文件列表)
        总样本数 = sum(f.样本数量 for f in 文件列表)
        总大小 = sum(f.文件大小 for f in 文件列表)
        
        # 合并所有文件的动作分布
        总动作分布 = {}
        for 文件 in 文件列表:
            for 动作, 数量 in 文件.动作分布.items():
                总动作分布[动作] = 总动作分布.get(动作, 0) + 数量
        
        # 更新标签
        self._文件数标签.值标签.setText(str(文件数))
        self._样本数标签.值标签.setText(f"{总样本数:,}")
        self._总大小标签.值标签.setText(self._格式化大小(总大小))
        
        # 更新分布图
        self._更新分布图(总动作分布)
    
    def _格式化大小(self, 字节数: int) -> str:
        """格式化文件大小"""
        if 字节数 < 1024:
            return f"{字节数}B"
        elif 字节数 < 1024 * 1024:
            return f"{字节数 / 1024:.1f}K"
        elif 字节数 < 1024 * 1024 * 1024:
            return f"{字节数 / (1024 * 1024):.1f}M"
        else:
            return f"{字节数 / (1024 * 1024 * 1024):.1f}G"
    
    def _更新分布图(self, 动作分布: Dict[int, int]) -> None:
        """更新动作分布条形图"""
        # 清除旧的条形图
        while self._条形图布局.count():
            子项 = self._条形图布局.takeAt(0)
            if 子项.widget():
                子项.widget().deleteLater()
        
        if not 动作分布:
            无数据标签 = QLabel("暂无数据")
            无数据标签.setStyleSheet(f"color: {颜色.次要文字}; font-size: 11px;")
            self._条形图布局.addWidget(无数据标签)
            return
        
        # 获取动作定义
        try:
            from 配置.设置 import 动作定义
        except:
            动作定义 = {}
        
        # 计算最大值用于归一化
        最大值 = max(动作分布.values()) if 动作分布 else 1
        
        # 按数量排序，取前8个
        排序后分布 = sorted(动作分布.items(), key=lambda x: x[1], reverse=True)[:8]
        
        # 颜色列表
        颜色列表 = [
            "#3B82F6", "#10B981", "#F59E0B", "#EF4444", 
            "#8B5CF6", "#EC4899", "#06B6D4", "#84CC16"
        ]
        
        for 索引, (动作索引, 数量) in enumerate(排序后分布):
            动作名 = 动作定义.get(动作索引, {}).get("名称", f"动作{动作索引}")
            百分比 = (数量 / 最大值) * 100
            
            # 创建条形项
            条形项 = self._创建条形项(动作名, 数量, 百分比, 颜色列表[索引 % len(颜色列表)])
            self._条形图布局.addWidget(条形项)
        
        self._条形图布局.addStretch()
    
    def _创建条形项(self, 名称: str, 数量: int, 百分比: float, 颜色值: str) -> QWidget:
        """创建单个条形项"""
        容器 = QWidget()
        容器.setFixedHeight(18)
        布局 = QHBoxLayout(容器)
        布局.setContentsMargins(0, 0, 0, 0)
        布局.setSpacing(6)
        
        # 动作名称
        名称标签 = QLabel(名称)
        名称标签.setFixedWidth(60)
        名称标签.setStyleSheet(f"color: {颜色.文字}; font-size: 10px;")
        布局.addWidget(名称标签)
        
        # 条形背景
        条形背景 = QFrame()
        条形背景.setFixedHeight(10)
        条形背景.setStyleSheet(f"""
            background-color: {颜色.悬停背景};
            border-radius: 5px;
        """)
        
        # 条形填充
        条形填充 = QFrame(条形背景)
        条形填充.setFixedHeight(10)
        宽度 = max(int(百分比 * 0.8), 4)  # 最小宽度4px
        条形填充.setFixedWidth(宽度)
        条形填充.setStyleSheet(f"""
            background-color: {颜色值};
            border-radius: 5px;
        """)
        
        布局.addWidget(条形背景, 1)
        
        # 数量标签
        数量标签 = QLabel(f"{数量:,}")
        数量标签.setFixedWidth(45)
        数量标签.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        数量标签.setStyleSheet(f"color: {颜色.次要文字}; font-size: 10px;")
        布局.addWidget(数量标签)
        
        return 容器



class 数据管理页(QWidget):
    """
    数据管理页面
    
    提供训练数据文件的管理功能，包括:
    - 文件列表显示 (Requirements 7.2)
    - 文件详细信息 (Requirements 7.3)
    - 数据分布统计 (Requirements 7.4)
    - 预处理和清洗操作 (Requirements 7.5)
    - 文件删除
    
    布局规范:
    - 左右两栏布局，左栏65%，右栏35% (Requirements 7.1)
    """
    
    # 信号定义
    刷新请求 = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._文件列表: List[数据文件信息] = []
        self._扫描线程: Optional[数据扫描线程] = None
        self._处理线程: Optional[数据处理线程] = None
        self._初始化界面()
    
    def _初始化界面(self) -> None:
        """初始化界面布局"""
        主布局 = QVBoxLayout(self)
        主布局.setContentsMargins(
            布局常量.内容区外边距,
            布局常量.内容区外边距,
            布局常量.内容区外边距,
            布局常量.内容区外边距
        )
        主布局.setSpacing(布局常量.卡片间距)
        
        # 页面标题
        标题 = QLabel("📁 数据管理")
        标题.setStyleSheet(f"""
            font-size: {布局常量.页面标题字号}px;
            font-weight: bold;
            color: {颜色.标题};
        """)
        主布局.addWidget(标题)
        
        # 内容区域 - 左右两栏 (Requirements 7.1: 65:35)
        内容容器 = QWidget()
        内容布局 = QHBoxLayout(内容容器)
        内容布局.setContentsMargins(0, 0, 0, 0)
        内容布局.setSpacing(布局常量.卡片间距)
        
        # 左栏 (65%) - 操作按钮 + 文件列表 (Requirements 7.2, 7.5)
        左栏 = self._创建左栏()
        内容布局.addWidget(左栏, 布局常量.数据管理页左栏比例)
        
        # 右栏 (35%) - 文件详情 + 数据分布 (Requirements 7.3, 7.4)
        右栏 = self._创建右栏()
        内容布局.addWidget(右栏, 布局常量.数据管理页右栏比例)
        
        主布局.addWidget(内容容器, 1)
    
    def _创建左栏(self) -> QWidget:
        """创建左栏：操作按钮 + 文件列表"""
        左栏 = QWidget()
        左栏布局 = QVBoxLayout(左栏)
        左栏布局.setContentsMargins(0, 0, 0, 0)
        左栏布局.setSpacing(布局常量.卡片间距)
        
        # 操作按钮区域 (Requirements 7.5)
        操作区域 = self._创建操作按钮区域()
        左栏布局.addWidget(操作区域)
        
        # 文件列表卡片 (Requirements 7.2)
        文件列表卡片 = Card("📄 数据文件", "", self)
        self._文件表格 = self._创建文件表格()
        文件列表卡片.添加内容(self._文件表格)
        左栏布局.addWidget(文件列表卡片, 1)
        
        return 左栏
    
    def _创建右栏(self) -> QWidget:
        """创建右栏：文件详情 + 数据分布"""
        右栏 = QWidget()
        右栏布局 = QVBoxLayout(右栏)
        右栏布局.setContentsMargins(0, 0, 0, 0)
        右栏布局.setSpacing(布局常量.卡片间距)
        
        # 文件详情卡片 (Requirements 7.3)
        self._文件详情卡片 = 文件详情卡片(self)
        右栏布局.addWidget(self._文件详情卡片)
        
        # 数据分布卡片 (Requirements 7.4)
        self._数据分布卡片 = 数据分布卡片(self)
        右栏布局.addWidget(self._数据分布卡片, 1)
        
        return 右栏
    
    def _创建操作按钮区域(self) -> QWidget:
        """创建操作按钮区域"""
        容器 = QWidget()
        布局 = QHBoxLayout(容器)
        布局.setContentsMargins(0, 0, 0, 0)
        布局.setSpacing(布局常量.按钮间距)
        
        # 刷新按钮
        self._刷新按钮 = QPushButton("🔄 刷新")
        self._刷新按钮.setProperty("class", "secondary")
        self._刷新按钮.setFixedWidth(70)
        self._刷新按钮.clicked.connect(self.刷新文件列表)
        布局.addWidget(self._刷新按钮)
        
        # 全选按钮
        self._全选按钮 = QPushButton("☑️ 全选")
        self._全选按钮.setProperty("class", "secondary")
        self._全选按钮.setFixedWidth(70)
        self._全选按钮.clicked.connect(self._切换全选)
        布局.addWidget(self._全选按钮)
        
        布局.addStretch()
        
        # 预处理按钮
        self._预处理按钮 = QPushButton("🔧 预处理")
        self._预处理按钮.setProperty("class", "secondary")
        self._预处理按钮.setFixedWidth(80)
        self._预处理按钮.setToolTip("对选中的文件进行数据增强")
        self._预处理按钮.clicked.connect(self._执行预处理)
        布局.addWidget(self._预处理按钮)
        
        # 清洗按钮
        self._清洗按钮 = QPushButton("🧹 清洗")
        self._清洗按钮.setProperty("class", "secondary")
        self._清洗按钮.setFixedWidth(70)
        self._清洗按钮.setToolTip("平衡选中文件的动作类别分布")
        self._清洗按钮.clicked.connect(self._执行清洗)
        布局.addWidget(self._清洗按钮)
        
        # 删除按钮 - 使用和其他按钮一致的样式
        self._删除按钮 = QPushButton("删除")
        self._删除按钮.setFixedWidth(60)
        self._删除按钮.setFixedHeight(32)
        self._删除按钮.setStyleSheet(f"""
            QPushButton {{
                background-color: #EF4444;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: #DC2626;
            }}
        """)
        self._删除按钮.clicked.connect(self._执行删除)
        布局.addWidget(self._删除按钮)
        
        return 容器
    
    def _创建文件表格(self) -> QTableWidget:
        """创建文件列表表格"""
        表格 = QTableWidget()
        表格.setColumnCount(5)
        表格.setHorizontalHeaderLabels(["", "文件名", "大小", "时间", "样本"])
        
        # 设置列宽
        表头 = 表格.horizontalHeader()
        表头.setSectionResizeMode(0, QHeaderView.Fixed)  # 复选框列
        表头.setSectionResizeMode(1, QHeaderView.Stretch)  # 文件名
        表头.setSectionResizeMode(2, QHeaderView.Fixed)  # 大小
        表头.setSectionResizeMode(3, QHeaderView.Fixed)  # 时间
        表头.setSectionResizeMode(4, QHeaderView.Fixed)  # 样本数
        
        表格.setColumnWidth(0, 30)
        表格.setColumnWidth(2, 65)
        表格.setColumnWidth(3, 100)
        表格.setColumnWidth(4, 60)
        
        # 设置样式
        表格.setStyleSheet(f"""
            QTableWidget {{
                border: 1px solid {颜色.边框};
                border-radius: {布局常量.卡片圆角}px;
                background-color: {颜色.卡片背景};
                gridline-color: {颜色.边框};
                font-size: 11px;
            }}
            QTableWidget::item {{
                padding: 6px;
            }}
            QTableWidget::item:selected {{
                background-color: {颜色.选中背景};
                color: {颜色.主色};
            }}
            QHeaderView::section {{
                background-color: {颜色.背景};
                border: none;
                border-bottom: 1px solid {颜色.边框};
                padding: 8px 4px;
                font-weight: 500;
                font-size: 11px;
                color: {颜色.标题};
            }}
        """)
        
        # 隐藏行号
        表格.verticalHeader().setVisible(False)
        
        # 设置选择模式
        表格.setSelectionBehavior(QTableWidget.SelectRows)
        表格.setSelectionMode(QTableWidget.MultiSelection)
        
        # 连接选择变化信号
        表格.itemSelectionChanged.connect(self._处理选择变化)
        
        return 表格
    
    def _处理选择变化(self) -> None:
        """处理文件选择变化，更新详情显示"""
        选中文件 = self._获取选中文件信息()
        选中数量 = len(选中文件)
        
        if 选中数量 == 0:
            self._文件详情卡片.更新详情()
        elif 选中数量 == 1:
            self._文件详情卡片.更新详情(选中文件[0], 1)
        else:
            # 多选时显示汇总信息 (Requirements 7.6)
            总大小 = sum(f.文件大小 for f in 选中文件)
            总样本 = sum(f.样本数量 for f in 选中文件)
            
            # 合并动作分布
            总动作分布 = {}
            for 文件 in 选中文件:
                for 动作, 数量 in 文件.动作分布.items():
                    总动作分布[动作] = 总动作分布.get(动作, 0) + 数量
            
            汇总信息 = {
                "总大小": self._格式化大小(总大小),
                "总样本": 总样本,
                "类别数": len(总动作分布)
            }
            self._文件详情卡片.更新详情(None, 选中数量, 汇总信息)
    
    def _格式化大小(self, 字节数: int) -> str:
        """格式化文件大小"""
        if 字节数 < 1024:
            return f"{字节数} B"
        elif 字节数 < 1024 * 1024:
            return f"{字节数 / 1024:.1f} KB"
        elif 字节数 < 1024 * 1024 * 1024:
            return f"{字节数 / (1024 * 1024):.1f} MB"
        else:
            return f"{字节数 / (1024 * 1024 * 1024):.2f} GB"
    
    def _获取选中文件信息(self) -> List[数据文件信息]:
        """获取选中的文件信息列表"""
        选中文件 = []
        for 行 in range(self._文件表格.rowCount()):
            复选框项 = self._文件表格.item(行, 0)
            if 复选框项 and 复选框项.checkState() == Qt.Checked:
                if 行 < len(self._文件列表):
                    选中文件.append(self._文件列表[行])
        return 选中文件
    
    def 刷新文件列表(self) -> None:
        """刷新文件列表"""
        try:
            from 配置.设置 import 数据保存路径
        except:
            数据保存路径 = "数据/"
        
        # 禁用刷新按钮
        self._刷新按钮.setEnabled(False)
        self._刷新按钮.setText("扫描中...")
        
        # 启动扫描线程
        self._扫描线程 = 数据扫描线程(数据保存路径)
        self._扫描线程.扫描完成.connect(self._处理扫描结果)
        self._扫描线程.start()
    
    @Slot(list)
    def _处理扫描结果(self, 文件列表: List[数据文件信息]) -> None:
        """处理扫描结果"""
        self._文件列表 = 文件列表
        
        # 更新表格
        self._更新文件表格()
        
        # 更新数据分布统计
        self._数据分布卡片.更新统计(文件列表)
        
        # 清空详情
        self._文件详情卡片.更新详情()
        
        # 恢复刷新按钮
        self._刷新按钮.setEnabled(True)
        self._刷新按钮.setText("🔄 刷新")
    
    def _更新文件表格(self) -> None:
        """更新文件表格"""
        self._文件表格.setRowCount(len(self._文件列表))
        
        for 行, 文件信息 in enumerate(self._文件列表):
            # 复选框
            复选框项 = QTableWidgetItem()
            复选框项.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            复选框项.setCheckState(Qt.Unchecked)
            self._文件表格.setItem(行, 0, 复选框项)
            
            # 文件名
            文件名项 = QTableWidgetItem(文件信息.文件名)
            文件名项.setData(Qt.UserRole, 文件信息.文件路径)  # 存储完整路径
            self._文件表格.setItem(行, 1, 文件名项)
            
            # 大小
            大小项 = QTableWidgetItem(文件信息.格式化大小())
            大小项.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self._文件表格.setItem(行, 2, 大小项)
            
            # 修改时间
            时间项 = QTableWidgetItem(文件信息.格式化时间())
            self._文件表格.setItem(行, 3, 时间项)
            
            # 样本数
            样本项 = QTableWidgetItem(f"{文件信息.样本数量:,}")
            样本项.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self._文件表格.setItem(行, 4, 样本项)
    
    def _获取选中文件(self) -> List[str]:
        """获取选中的文件路径列表"""
        选中文件 = []
        for 行 in range(self._文件表格.rowCount()):
            复选框项 = self._文件表格.item(行, 0)
            if 复选框项 and 复选框项.checkState() == Qt.Checked:
                文件名项 = self._文件表格.item(行, 1)
                if 文件名项:
                    文件路径 = 文件名项.data(Qt.UserRole)
                    if 文件路径:
                        选中文件.append(文件路径)
        return 选中文件
    
    def _切换全选(self) -> None:
        """切换全选/取消全选"""
        # 检查当前是否全选
        全部选中 = True
        for 行 in range(self._文件表格.rowCount()):
            复选框项 = self._文件表格.item(行, 0)
            if 复选框项 and 复选框项.checkState() != Qt.Checked:
                全部选中 = False
                break
        
        # 切换状态
        新状态 = Qt.Unchecked if 全部选中 else Qt.Checked
        for 行 in range(self._文件表格.rowCount()):
            复选框项 = self._文件表格.item(行, 0)
            if 复选框项:
                复选框项.setCheckState(新状态)
        
        # 更新按钮文字
        self._全选按钮.setText("☐ 取消" if not 全部选中 else "☑️ 全选")
        
        # 触发选择变化
        self._处理选择变化()
    
    def _执行预处理(self) -> None:
        """执行数据预处理"""
        选中文件 = self._获取选中文件()
        
        if not 选中文件:
            提示对话框.警告提示(self, "提示", "请先选择要预处理的文件")
            return
        
        回复 = 确认对话框.询问(
            self,
            "确认预处理",
            f"确定要对选中的 {len(选中文件)} 个文件进行数据增强吗？\n\n"
            "这将创建新的增强数据文件。",
            "确定", "取消"
        )
        
        if 回复 == 确认对话框.确认:
            self._启动处理("预处理", 选中文件)
    
    def _执行清洗(self) -> None:
        """执行数据清洗"""
        选中文件 = self._获取选中文件()
        
        if not 选中文件:
            提示对话框.警告提示(self, "提示", "请先选择要清洗的文件")
            return
        
        回复 = 确认对话框.询问(
            self,
            "确认清洗",
            f"确定要对选中的 {len(选中文件)} 个文件进行数据清洗吗？\n\n"
            "这将平衡各动作类别的样本数量，创建新的清洗后文件。",
            "确定", "取消"
        )
        
        if 回复 == 确认对话框.确认:
            self._启动处理("清洗", 选中文件)
    
    def _执行删除(self) -> None:
        """执行文件删除"""
        选中文件 = self._获取选中文件()
        
        if not 选中文件:
            提示对话框.警告提示(self, "提示", "请先选择要删除的文件")
            return
        
        回复 = 确认对话框.询问(
            self,
            "确认删除",
            f"确定要删除选中的 {len(选中文件)} 个文件吗？\n\n"
            "⚠️ 此操作不可恢复！",
            "删除", "取消"
        )
        
        if 回复 == 确认对话框.确认:
            self._启动处理("删除", 选中文件)
    
    def _启动处理(self, 操作类型: str, 文件列表: List[str]) -> None:
        """启动后台处理"""
        # 禁用操作按钮
        self._设置按钮状态(False)
        
        # 创建进度对话框
        self._进度对话框 = QProgressDialog(
            f"正在{操作类型}...",
            "取消",
            0, 100,
            self
        )
        self._进度对话框.setWindowTitle(操作类型)
        self._进度对话框.setWindowModality(Qt.WindowModal)
        self._进度对话框.setMinimumDuration(0)
        self._进度对话框.setValue(0)
        
        # 启动处理线程
        self._处理线程 = 数据处理线程(操作类型, 文件列表)
        self._处理线程.处理进度.connect(self._更新处理进度)
        self._处理线程.处理完成.connect(self._处理完成回调)
        self._处理线程.start()
    
    @Slot(int, str)
    def _更新处理进度(self, 进度: int, 消息: str) -> None:
        """更新处理进度"""
        if hasattr(self, '_进度对话框') and self._进度对话框:
            self._进度对话框.setValue(进度)
            self._进度对话框.setLabelText(消息)
    
    @Slot(bool, str)
    def _处理完成回调(self, 成功: bool, 消息: str) -> None:
        """处理完成回调"""
        # 关闭进度对话框
        if hasattr(self, '_进度对话框') and self._进度对话框:
            self._进度对话框.close()
        
        # 恢复按钮状态
        self._设置按钮状态(True)
        
        # 显示结果
        if 成功:
            提示对话框.信息提示(self, "完成", 消息)
        else:
            提示对话框.错误提示(self, "错误", 消息)
        
        # 刷新文件列表
        self.刷新文件列表()
    
    def _设置按钮状态(self, 启用: bool) -> None:
        """设置操作按钮状态"""
        self._预处理按钮.setEnabled(启用)
        self._清洗按钮.setEnabled(启用)
        self._删除按钮.setEnabled(启用)
        self._全选按钮.setEnabled(启用)
        self._刷新按钮.setEnabled(启用)
    
    def showEvent(self, event) -> None:
        """页面显示时自动刷新"""
        super().showEvent(event)
        # 首次显示时刷新文件列表
        if not self._文件列表:
            self.刷新文件列表()
