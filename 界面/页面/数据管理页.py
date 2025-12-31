# -*- coding: utf-8 -*-
"""
数据管理页面

提供训练数据文件的管理功能:
- 文件列表显示 (文件名/大小/时间/样本数)
- 数据分布统计图表
- 预处理和清洗快捷按钮
- 删除确认对话框
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



class 统计卡片(QFrame):
    """数据统计卡片组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("class", "card")
        self._初始化界面()
    
    def _初始化界面(self) -> None:
        """初始化界面"""
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {颜色.卡片背景};
                border-radius: 12px;
                border: 1px solid {颜色.边框};
            }}
        """)
        
        布局 = QVBoxLayout(self)
        布局.setContentsMargins(16, 12, 16, 12)
        布局.setSpacing(12)
        
        # 标题
        标题 = QLabel("📊 数据统计")
        标题.setStyleSheet(f"""
            font-size: 15px;
            font-weight: bold;
            color: {颜色.标题};
        """)
        布局.addWidget(标题)
        
        # 统计信息网格
        统计容器 = QWidget()
        统计布局 = QHBoxLayout(统计容器)
        统计布局.setContentsMargins(0, 0, 0, 0)
        统计布局.setSpacing(24)
        
        # 文件数量
        self._文件数标签 = self._创建统计项("📁 文件数", "0", 统计布局)
        
        # 总样本数
        self._样本数标签 = self._创建统计项("📝 总样本", "0", 统计布局)
        
        # 总大小
        self._总大小标签 = self._创建统计项("💾 总大小", "0 B", 统计布局)
        
        # 动作类别数
        self._类别数标签 = self._创建统计项("🎯 动作类别", "0", 统计布局)
        
        统计布局.addStretch()
        布局.addWidget(统计容器)
        
        # 动作分布条形图区域
        self._分布容器 = QWidget()
        self._分布布局 = QVBoxLayout(self._分布容器)
        self._分布布局.setContentsMargins(0, 8, 0, 0)
        self._分布布局.setSpacing(4)
        
        分布标题 = QLabel("动作分布")
        分布标题.setStyleSheet(f"color: {颜色.次要文字}; font-size: 12px;")
        self._分布布局.addWidget(分布标题)
        
        # 分布条形图容器
        self._条形图容器 = QWidget()
        self._条形图布局 = QVBoxLayout(self._条形图容器)
        self._条形图布局.setContentsMargins(0, 0, 0, 0)
        self._条形图布局.setSpacing(2)
        self._分布布局.addWidget(self._条形图容器)
        
        布局.addWidget(self._分布容器)
    
    def _创建统计项(self, 标题: str, 初始值: str, 父布局) -> QLabel:
        """创建统计项"""
        容器 = QWidget()
        布局 = QVBoxLayout(容器)
        布局.setContentsMargins(0, 0, 0, 0)
        布局.setSpacing(2)
        
        标题标签 = QLabel(标题)
        标题标签.setStyleSheet(f"color: {颜色.次要文字}; font-size: 11px;")
        布局.addWidget(标题标签)
        
        值标签 = QLabel(初始值)
        值标签.setStyleSheet(f"color: {颜色.标题}; font-size: 18px; font-weight: bold;")
        布局.addWidget(值标签)
        
        父布局.addWidget(容器)
        return 值标签
    
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
        
        类别数 = len(总动作分布)
        
        # 更新标签
        self._文件数标签.setText(str(文件数))
        self._样本数标签.setText(f"{总样本数:,}")
        self._总大小标签.setText(self._格式化大小(总大小))
        self._类别数标签.setText(str(类别数))
        
        # 更新分布图
        self._更新分布图(总动作分布)
    
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
    
    def _更新分布图(self, 动作分布: Dict[int, int]) -> None:
        """更新动作分布条形图"""
        # 清除旧的条形图
        while self._条形图布局.count():
            子项 = self._条形图布局.takeAt(0)
            if 子项.widget():
                子项.widget().deleteLater()
        
        if not 动作分布:
            无数据标签 = QLabel("暂无数据")
            无数据标签.setStyleSheet(f"color: {颜色.次要文字}; font-size: 12px;")
            self._条形图布局.addWidget(无数据标签)
            return
        
        # 获取动作定义
        try:
            from 配置.设置 import 动作定义
        except:
            动作定义 = {}
        
        # 计算最大值用于归一化
        最大值 = max(动作分布.values()) if 动作分布 else 1
        
        # 按数量排序，取前10个
        排序后分布 = sorted(动作分布.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # 颜色列表
        颜色列表 = [
            "#3B82F6", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6",
            "#EC4899", "#06B6D4", "#84CC16", "#F97316", "#6366F1"
        ]
        
        for 索引, (动作索引, 数量) in enumerate(排序后分布):
            动作名 = 动作定义.get(动作索引, {}).get("名称", f"动作{动作索引}")
            百分比 = (数量 / 最大值) * 100
            
            # 创建条形项
            条形项 = self._创建条形项(动作名, 数量, 百分比, 颜色列表[索引 % len(颜色列表)])
            self._条形图布局.addWidget(条形项)
    
    def _创建条形项(self, 名称: str, 数量: int, 百分比: float, 颜色值: str) -> QWidget:
        """创建单个条形项"""
        容器 = QWidget()
        容器.setFixedHeight(20)
        布局 = QHBoxLayout(容器)
        布局.setContentsMargins(0, 0, 0, 0)
        布局.setSpacing(8)
        
        # 动作名称
        名称标签 = QLabel(名称)
        名称标签.setFixedWidth(80)
        名称标签.setStyleSheet(f"color: {颜色.文字}; font-size: 11px;")
        布局.addWidget(名称标签)
        
        # 条形背景
        条形背景 = QFrame()
        条形背景.setFixedHeight(12)
        条形背景.setStyleSheet(f"""
            background-color: {颜色.悬停背景};
            border-radius: 6px;
        """)
        
        # 条形填充
        条形填充 = QFrame(条形背景)
        条形填充.setFixedHeight(12)
        宽度 = max(int(百分比 * 2), 4)  # 最小宽度4px
        条形填充.setFixedWidth(宽度)
        条形填充.setStyleSheet(f"""
            background-color: {颜色值};
            border-radius: 6px;
        """)
        
        布局.addWidget(条形背景, 1)
        
        # 数量标签
        数量标签 = QLabel(f"{数量:,}")
        数量标签.setFixedWidth(60)
        数量标签.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        数量标签.setStyleSheet(f"color: {颜色.次要文字}; font-size: 11px;")
        布局.addWidget(数量标签)
        
        return 容器



class 数据管理页(QWidget):
    """
    数据管理页面
    
    提供训练数据文件的管理功能，包括:
    - 文件列表显示
    - 数据分布统计
    - 预处理和清洗操作
    - 文件删除
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
        主布局.setContentsMargins(20, 20, 20, 20)
        主布局.setSpacing(16)
        
        # 标题和操作按钮区域
        标题区域 = self._创建标题区域()
        主布局.addWidget(标题区域)
        
        # 统计卡片
        self._统计卡片 = 统计卡片()
        主布局.addWidget(self._统计卡片)
        
        # 文件列表
        self._文件表格 = self._创建文件表格()
        主布局.addWidget(self._文件表格, 1)
        
        # 底部操作区域
        底部区域 = self._创建底部区域()
        主布局.addWidget(底部区域)
    
    def _创建标题区域(self) -> QWidget:
        """创建标题和操作按钮区域"""
        容器 = QWidget()
        布局 = QHBoxLayout(容器)
        布局.setContentsMargins(0, 0, 0, 0)
        
        # 标题
        标题 = QLabel("📁 数据管理")
        标题.setStyleSheet(f"""
            font-size: 18px;
            font-weight: bold;
            color: {颜色.标题};
        """)
        布局.addWidget(标题)
        
        布局.addStretch()
        
        # 刷新按钮
        self._刷新按钮 = QPushButton("🔄 刷新")
        self._刷新按钮.setProperty("class", "secondary")
        self._刷新按钮.setFixedWidth(80)
        self._刷新按钮.clicked.connect(self.刷新文件列表)
        布局.addWidget(self._刷新按钮)
        
        return 容器
    
    def _创建文件表格(self) -> QTableWidget:
        """创建文件列表表格"""
        表格 = QTableWidget()
        表格.setColumnCount(5)
        表格.setHorizontalHeaderLabels(["", "文件名", "大小", "修改时间", "样本数"])
        
        # 设置列宽
        表头 = 表格.horizontalHeader()
        表头.setSectionResizeMode(0, QHeaderView.Fixed)  # 复选框列
        表头.setSectionResizeMode(1, QHeaderView.Stretch)  # 文件名
        表头.setSectionResizeMode(2, QHeaderView.Fixed)  # 大小
        表头.setSectionResizeMode(3, QHeaderView.Fixed)  # 时间
        表头.setSectionResizeMode(4, QHeaderView.Fixed)  # 样本数
        
        表格.setColumnWidth(0, 40)
        表格.setColumnWidth(2, 80)
        表格.setColumnWidth(3, 130)
        表格.setColumnWidth(4, 80)
        
        # 设置样式
        表格.setStyleSheet(f"""
            QTableWidget {{
                border: 1px solid {颜色.边框};
                border-radius: 8px;
                background-color: {颜色.卡片背景};
                gridline-color: {颜色.边框};
            }}
            QTableWidget::item {{
                padding: 8px;
            }}
            QTableWidget::item:selected {{
                background-color: {颜色.选中背景};
                color: {颜色.主色};
            }}
            QHeaderView::section {{
                background-color: {颜色.背景};
                border: none;
                border-bottom: 1px solid {颜色.边框};
                padding: 10px;
                font-weight: 500;
                color: {颜色.标题};
            }}
        """)
        
        # 隐藏行号
        表格.verticalHeader().setVisible(False)
        
        # 设置选择模式
        表格.setSelectionBehavior(QTableWidget.SelectRows)
        表格.setSelectionMode(QTableWidget.MultiSelection)
        
        return 表格
    
    def _创建底部区域(self) -> QWidget:
        """创建底部操作区域"""
        容器 = QWidget()
        布局 = QHBoxLayout(容器)
        布局.setContentsMargins(0, 0, 0, 0)
        布局.setSpacing(12)
        
        # 全选/取消全选
        self._全选按钮 = QPushButton("☑️ 全选")
        self._全选按钮.setProperty("class", "secondary")
        self._全选按钮.setFixedWidth(80)
        self._全选按钮.clicked.connect(self._切换全选)
        布局.addWidget(self._全选按钮)
        
        布局.addStretch()
        
        # 预处理按钮
        self._预处理按钮 = QPushButton("🔧 预处理")
        self._预处理按钮.setProperty("class", "secondary")
        self._预处理按钮.setFixedWidth(90)
        self._预处理按钮.setToolTip("对选中的文件进行数据增强")
        self._预处理按钮.clicked.connect(self._执行预处理)
        布局.addWidget(self._预处理按钮)
        
        # 清洗按钮
        self._清洗按钮 = QPushButton("🧹 清洗")
        self._清洗按钮.setProperty("class", "secondary")
        self._清洗按钮.setFixedWidth(80)
        self._清洗按钮.setToolTip("平衡选中文件的动作类别分布")
        self._清洗按钮.clicked.connect(self._执行清洗)
        布局.addWidget(self._清洗按钮)
        
        # 删除按钮
        self._删除按钮 = QPushButton("🗑️ 删除")
        self._删除按钮.setProperty("class", "danger")
        self._删除按钮.setFixedWidth(80)
        self._删除按钮.clicked.connect(self._执行删除)
        布局.addWidget(self._删除按钮)
        
        return 容器
    
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
        
        # 更新统计
        self._统计卡片.更新统计(文件列表)
        
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
    
    def _执行预处理(self) -> None:
        """执行数据预处理"""
        选中文件 = self._获取选中文件()
        
        if not 选中文件:
            QMessageBox.warning(self, "提示", "请先选择要预处理的文件")
            return
        
        回复 = QMessageBox.question(
            self,
            "确认预处理",
            f"确定要对选中的 {len(选中文件)} 个文件进行数据增强吗？\n\n"
            "这将创建新的增强数据文件。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if 回复 == QMessageBox.Yes:
            self._启动处理("预处理", 选中文件)
    
    def _执行清洗(self) -> None:
        """执行数据清洗"""
        选中文件 = self._获取选中文件()
        
        if not 选中文件:
            QMessageBox.warning(self, "提示", "请先选择要清洗的文件")
            return
        
        回复 = QMessageBox.question(
            self,
            "确认清洗",
            f"确定要对选中的 {len(选中文件)} 个文件进行数据清洗吗？\n\n"
            "这将平衡各动作类别的样本数量，创建新的清洗后文件。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if 回复 == QMessageBox.Yes:
            self._启动处理("清洗", 选中文件)
    
    def _执行删除(self) -> None:
        """执行文件删除"""
        选中文件 = self._获取选中文件()
        
        if not 选中文件:
            QMessageBox.warning(self, "提示", "请先选择要删除的文件")
            return
        
        回复 = QMessageBox.warning(
            self,
            "确认删除",
            f"确定要删除选中的 {len(选中文件)} 个文件吗？\n\n"
            "⚠️ 此操作不可恢复！",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if 回复 == QMessageBox.Yes:
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
            QMessageBox.information(self, "完成", 消息)
        else:
            QMessageBox.critical(self, "错误", 消息)
        
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
