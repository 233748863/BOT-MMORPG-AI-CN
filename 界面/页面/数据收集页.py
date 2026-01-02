# -*- coding: utf-8 -*-
"""
数据收集页面

提供数据收集功能的图形界面，包括控制面板、状态监控、游戏画面预览和智能录制控制。
"""

from typing import Optional, Dict, Any
import numpy as np

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QGridLayout, QComboBox,
    QSizePolicy, QCheckBox, QProgressBar
)
from PySide6.QtCore import Signal, Slot, Qt, QTimer
from PySide6.QtGui import QImage, QPixmap

from 界面.样式.主题 import 颜色


class 控制面板(QFrame):
    """数据收集控制面板组件"""
    
    # 信号定义
    开始点击 = Signal()
    暂停点击 = Signal()
    停止点击 = Signal()
    模式改变 = Signal(str)
    
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
        布局.setContentsMargins(20, 16, 20, 16)
        布局.setSpacing(16)
        
        # 标题
        标题 = QLabel("🎮 控制面板")
        标题.setStyleSheet(f"""
            font-size: 16px;
            font-weight: bold;
            color: {颜色.标题};
        """)
        布局.addWidget(标题)
        
        # 模式选择
        模式容器 = QWidget()
        模式布局 = QHBoxLayout(模式容器)
        模式布局.setContentsMargins(0, 0, 0, 0)
        模式布局.setSpacing(12)
        
        模式标签 = QLabel("训练模式:")
        模式标签.setStyleSheet(f"color: {颜色.文字}; font-size: 13px;")
        模式布局.addWidget(模式标签)
        
        self._模式选择 = QComboBox()
        self._模式选择.addItems(["主线任务", "自动战斗", "通用模式"])
        self._模式选择.setFixedWidth(150)
        self._模式选择.currentTextChanged.connect(self.模式改变.emit)
        模式布局.addWidget(self._模式选择)
        模式布局.addStretch()
        
        布局.addWidget(模式容器)
        
        # 按钮容器
        按钮容器 = QWidget()
        按钮布局 = QHBoxLayout(按钮容器)
        按钮布局.setContentsMargins(0, 0, 0, 0)
        按钮布局.setSpacing(12)
        
        # 开始按钮
        self._开始按钮 = QPushButton("▶️ 开始录制")
        self._开始按钮.setFixedHeight(40)
        self._开始按钮.setCursor(Qt.PointingHandCursor)
        self._开始按钮.setStyleSheet(f"""
            QPushButton {{
                background-color: {颜色.成功};
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 500;
                padding: 0 20px;
            }}
            QPushButton:hover {{
                background-color: #059669;
            }}
            QPushButton:disabled {{
                background-color: {颜色.按钮禁用};
                color: {颜色.禁用文字};
            }}
        """)
        self._开始按钮.clicked.connect(self.开始点击.emit)
        按钮布局.addWidget(self._开始按钮)
        
        # 暂停按钮
        self._暂停按钮 = QPushButton("⏸️ 暂停")
        self._暂停按钮.setFixedHeight(40)
        self._暂停按钮.setCursor(Qt.PointingHandCursor)
        self._暂停按钮.setEnabled(False)
        self._暂停按钮.setStyleSheet(f"""
            QPushButton {{
                background-color: {颜色.警告};
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 500;
                padding: 0 20px;
            }}
            QPushButton:hover {{
                background-color: #D97706;
            }}
            QPushButton:disabled {{
                background-color: {颜色.按钮禁用};
                color: {颜色.禁用文字};
            }}
        """)
        self._暂停按钮.clicked.connect(self.暂停点击.emit)
        按钮布局.addWidget(self._暂停按钮)
        
        # 停止按钮
        self._停止按钮 = QPushButton("⏹️ 停止")
        self._停止按钮.setFixedHeight(40)
        self._停止按钮.setCursor(Qt.PointingHandCursor)
        self._停止按钮.setEnabled(False)
        self._停止按钮.setStyleSheet(f"""
            QPushButton {{
                background-color: {颜色.错误};
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 500;
                padding: 0 20px;
            }}
            QPushButton:hover {{
                background-color: #DC2626;
            }}
            QPushButton:disabled {{
                background-color: {颜色.按钮禁用};
                color: {颜色.禁用文字};
            }}
        """)
        self._停止按钮.clicked.connect(self.停止点击.emit)
        按钮布局.addWidget(self._停止按钮)
        
        按钮布局.addStretch()
        布局.addWidget(按钮容器)
        
        # 快捷键提示
        提示 = QLabel("💡 快捷键: T 暂停/继续, ESC 停止")
        提示.setStyleSheet(f"color: {颜色.次要文字}; font-size: 12px;")
        布局.addWidget(提示)
    
    def 设置录制状态(self, 录制中: bool, 已暂停: bool = False) -> None:
        """设置录制状态，更新按钮状态"""
        self._开始按钮.setEnabled(not 录制中)
        self._暂停按钮.setEnabled(录制中)
        self._停止按钮.setEnabled(录制中)
        self._模式选择.setEnabled(not 录制中)
        
        if 录制中:
            if 已暂停:
                self._暂停按钮.setText("▶️ 继续")
            else:
                self._暂停按钮.setText("⏸️ 暂停")
    
    def 获取当前模式(self) -> str:
        """获取当前选择的训练模式"""
        return self._模式选择.currentText()


class 状态监控(QFrame):
    """数据收集状态监控组件"""
    
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
        布局.setContentsMargins(20, 16, 20, 16)
        布局.setSpacing(12)
        
        # 标题
        标题 = QLabel("📊 状态监控")
        标题.setStyleSheet(f"""
            font-size: 16px;
            font-weight: bold;
            color: {颜色.标题};
        """)
        布局.addWidget(标题)
        
        # 状态网格
        状态网格 = QGridLayout()
        状态网格.setSpacing(16)
        
        # 录制状态
        self._录制状态标签 = self._创建状态项("录制状态:", "已停止", 状态网格, 0, 0)
        
        # 样本数量
        self._样本数量标签 = self._创建状态项("样本数量:", "0", 状态网格, 0, 1)
        
        # 文件编号
        self._文件编号标签 = self._创建状态项("文件编号:", "1", 状态网格, 1, 0)
        
        # 帧率
        self._帧率标签 = self._创建状态项("帧率:", "0 FPS", 状态网格, 1, 1)
        
        # 当前动作
        self._当前动作标签 = self._创建状态项("当前动作:", "无", 状态网格, 2, 0, colspan=2)
        
        布局.addLayout(状态网格)
    
    def _创建状态项(self, 标题: str, 初始值: str, 网格: QGridLayout, 
                   行: int, 列: int, colspan: int = 1) -> QLabel:
        """创建状态项"""
        容器 = QWidget()
        容器布局 = QHBoxLayout(容器)
        容器布局.setContentsMargins(0, 0, 0, 0)
        容器布局.setSpacing(8)
        
        标题标签 = QLabel(标题)
        标题标签.setStyleSheet(f"color: {颜色.次要文字}; font-size: 13px;")
        容器布局.addWidget(标题标签)
        
        值标签 = QLabel(初始值)
        值标签.setStyleSheet(f"color: {颜色.文字}; font-size: 13px; font-weight: 500;")
        容器布局.addWidget(值标签)
        容器布局.addStretch()
        
        网格.addWidget(容器, 行, 列, 1, colspan)
        return 值标签
    
    def 更新录制状态(self, 状态: str) -> None:
        """更新录制状态显示"""
        颜色映射 = {
            "录制中": 颜色.成功,
            "已暂停": 颜色.警告,
            "已停止": 颜色.次要文字,
            "倒计时": 颜色.主色,
        }
        状态颜色 = 颜色映射.get(状态, 颜色.文字)
        self._录制状态标签.setText(状态)
        self._录制状态标签.setStyleSheet(f"color: {状态颜色}; font-size: 13px; font-weight: 500;")
    
    def 更新样本数量(self, 数量: int) -> None:
        """更新样本数量显示"""
        self._样本数量标签.setText(str(数量))
    
    def 更新文件编号(self, 编号: int) -> None:
        """更新文件编号显示"""
        self._文件编号标签.setText(str(编号))
    
    def 更新帧率(self, 帧率: float) -> None:
        """更新帧率显示"""
        self._帧率标签.setText(f"{帧率:.1f} FPS")
    
    def 更新当前动作(self, 动作: str) -> None:
        """更新当前动作显示"""
        self._当前动作标签.setText(动作)


class 画面预览(QFrame):
    """游戏画面预览组件"""
    
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
        布局.setSpacing(8)
        
        # 标题
        标题 = QLabel("🖥️ 游戏画面预览")
        标题.setStyleSheet(f"""
            font-size: 14px;
            font-weight: bold;
            color: {颜色.标题};
        """)
        布局.addWidget(标题)
        
        # 预览区域
        self._预览标签 = QLabel()
        self._预览标签.setFixedSize(280, 160)
        self._预览标签.setAlignment(Qt.AlignCenter)
        self._预览标签.setStyleSheet(f"""
            background-color: #1E293B;
            border-radius: 8px;
            color: {颜色.次要文字};
            font-size: 12px;
        """)
        self._预览标签.setText("等待录制开始...")
        布局.addWidget(self._预览标签, alignment=Qt.AlignCenter)
    
    def 更新预览(self, 图像: np.ndarray) -> None:
        """
        更新预览图像
        
        参数:
            图像: RGB格式的numpy数组
        """
        try:
            高度, 宽度, 通道 = 图像.shape
            字节数 = 通道 * 宽度
            
            # 转换为QImage
            q图像 = QImage(图像.data, 宽度, 高度, 字节数, QImage.Format_RGB888)
            
            # 缩放到预览尺寸
            像素图 = QPixmap.fromImage(q图像)
            缩放像素图 = 像素图.scaled(
                280, 160, 
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            )
            
            self._预览标签.setPixmap(缩放像素图)
        except Exception as e:
            self._预览标签.setText(f"预览错误: {str(e)}")
    
    def 清除预览(self) -> None:
        """清除预览图像"""
        self._预览标签.clear()
        self._预览标签.setText("等待录制开始...")


class 智能录制面板(QFrame):
    """智能录制控制面板组件
    
    显示实时价值评分和过滤选项控件。
    需求: 2.6, 3.1
    """
    
    # 信号定义
    过滤选项改变 = Signal(str)  # 过滤选项: "全部", "仅高价值", "自动过滤"
    
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
        布局.setSpacing(10)
        
        # 标题
        标题 = QLabel("🎯 智能录制")
        标题.setStyleSheet(f"""
            font-size: 14px;
            font-weight: bold;
            color: {颜色.标题};
        """)
        布局.addWidget(标题)
        
        # 实时价值评分显示 (需求 3.1)
        评分容器 = QWidget()
        评分布局 = QVBoxLayout(评分容器)
        评分布局.setContentsMargins(0, 0, 0, 0)
        评分布局.setSpacing(4)
        
        评分标题行 = QWidget()
        评分标题布局 = QHBoxLayout(评分标题行)
        评分标题布局.setContentsMargins(0, 0, 0, 0)
        
        评分标签 = QLabel("当前价值评分:")
        评分标签.setStyleSheet(f"color: {颜色.次要文字}; font-size: 12px;")
        评分标题布局.addWidget(评分标签)
        
        self._评分值标签 = QLabel("--")
        self._评分值标签.setStyleSheet(f"color: {颜色.文字}; font-size: 14px; font-weight: bold;")
        评分标题布局.addWidget(self._评分值标签)
        评分标题布局.addStretch()
        
        评分布局.addWidget(评分标题行)
        
        # 价值评分进度条
        self._评分进度条 = QProgressBar()
        self._评分进度条.setRange(0, 100)
        self._评分进度条.setValue(0)
        self._评分进度条.setFixedHeight(8)
        self._评分进度条.setTextVisible(False)
        self._评分进度条.setStyleSheet(f"""
            QProgressBar {{
                border: none;
                border-radius: 4px;
                background-color: {颜色.边框};
            }}
            QProgressBar::chunk {{
                border-radius: 4px;
                background-color: {颜色.成功};
            }}
        """)
        评分布局.addWidget(self._评分进度条)
        
        # 价值等级标签
        self._价值等级标签 = QLabel("等级: --")
        self._价值等级标签.setStyleSheet(f"color: {颜色.次要文字}; font-size: 11px;")
        评分布局.addWidget(self._价值等级标签)
        
        布局.addWidget(评分容器)
        
        # 分隔线
        分隔线 = QFrame()
        分隔线.setFrameShape(QFrame.HLine)
        分隔线.setStyleSheet(f"background-color: {颜色.边框};")
        分隔线.setFixedHeight(1)
        布局.addWidget(分隔线)
        
        # 片段统计
        统计容器 = QWidget()
        统计布局 = QGridLayout(统计容器)
        统计布局.setContentsMargins(0, 0, 0, 0)
        统计布局.setSpacing(6)
        
        # 高价值片段
        高价值标签 = QLabel("🟢 高价值:")
        高价值标签.setStyleSheet(f"color: {颜色.次要文字}; font-size: 11px;")
        统计布局.addWidget(高价值标签, 0, 0)
        
        self._高价值数量 = QLabel("0")
        self._高价值数量.setStyleSheet(f"color: {颜色.成功}; font-size: 12px; font-weight: 500;")
        统计布局.addWidget(self._高价值数量, 0, 1)
        
        # 中价值片段
        中价值标签 = QLabel("🟡 中价值:")
        中价值标签.setStyleSheet(f"color: {颜色.次要文字}; font-size: 11px;")
        统计布局.addWidget(中价值标签, 0, 2)
        
        self._中价值数量 = QLabel("0")
        self._中价值数量.setStyleSheet(f"color: {颜色.警告}; font-size: 12px; font-weight: 500;")
        统计布局.addWidget(self._中价值数量, 0, 3)
        
        # 低价值片段
        低价值标签 = QLabel("🔴 低价值:")
        低价值标签.setStyleSheet(f"color: {颜色.次要文字}; font-size: 11px;")
        统计布局.addWidget(低价值标签, 1, 0)
        
        self._低价值数量 = QLabel("0")
        self._低价值数量.setStyleSheet(f"color: {颜色.错误}; font-size: 12px; font-weight: 500;")
        统计布局.addWidget(self._低价值数量, 1, 1)
        
        # 总片段数
        总数标签 = QLabel("📊 总计:")
        总数标签.setStyleSheet(f"color: {颜色.次要文字}; font-size: 11px;")
        统计布局.addWidget(总数标签, 1, 2)
        
        self._总片段数量 = QLabel("0")
        self._总片段数量.setStyleSheet(f"color: {颜色.文字}; font-size: 12px; font-weight: 500;")
        统计布局.addWidget(self._总片段数量, 1, 3)
        
        布局.addWidget(统计容器)
        
        # 分隔线
        分隔线2 = QFrame()
        分隔线2.setFrameShape(QFrame.HLine)
        分隔线2.setStyleSheet(f"background-color: {颜色.边框};")
        分隔线2.setFixedHeight(1)
        布局.addWidget(分隔线2)
        
        # 过滤选项 (需求 2.6)
        过滤容器 = QWidget()
        过滤布局 = QVBoxLayout(过滤容器)
        过滤布局.setContentsMargins(0, 0, 0, 0)
        过滤布局.setSpacing(6)
        
        过滤标签 = QLabel("保存选项:")
        过滤标签.setStyleSheet(f"color: {颜色.次要文字}; font-size: 12px;")
        过滤布局.addWidget(过滤标签)
        
        self._过滤选择 = QComboBox()
        self._过滤选择.addItems(["保留全部", "仅保留高价值", "自动过滤低价值"])
        self._过滤选择.setFixedHeight(28)
        self._过滤选择.setStyleSheet(f"""
            QComboBox {{
                padding: 4px 8px;
                font-size: 12px;
            }}
        """)
        self._过滤选择.currentTextChanged.connect(self.过滤选项改变.emit)
        过滤布局.addWidget(self._过滤选择)
        
        布局.addWidget(过滤容器)
    
    def 更新价值评分(self, 评分: float) -> None:
        """更新实时价值评分显示
        
        需求 3.1: 实时显示当前片段的Value_Score
        
        Args:
            评分: 价值评分 (0-100)
        """
        # 更新评分值
        self._评分值标签.setText(f"{评分:.1f}")
        self._评分进度条.setValue(int(评分))
        
        # 根据评分设置颜色和等级
        if 评分 >= 70:
            等级 = "高价值"
            颜色值 = 颜色.成功
        elif 评分 >= 40:
            等级 = "中价值"
            颜色值 = 颜色.警告
        else:
            等级 = "低价值"
            颜色值 = 颜色.错误
        
        self._评分值标签.setStyleSheet(f"color: {颜色值}; font-size: 14px; font-weight: bold;")
        self._价值等级标签.setText(f"等级: {等级}")
        self._价值等级标签.setStyleSheet(f"color: {颜色值}; font-size: 11px;")
        
        # 更新进度条颜色
        self._评分进度条.setStyleSheet(f"""
            QProgressBar {{
                border: none;
                border-radius: 4px;
                background-color: {颜色.边框};
            }}
            QProgressBar::chunk {{
                border-radius: 4px;
                background-color: {颜色值};
            }}
        """)
    
    def 更新片段统计(self, 高价值: int, 中价值: int, 低价值: int) -> None:
        """更新片段统计显示
        
        需求 3.2: 显示本次录制的高/中/低价值片段数量统计
        
        Args:
            高价值: 高价值片段数量
            中价值: 中价值片段数量
            低价值: 低价值片段数量
        """
        self._高价值数量.setText(str(高价值))
        self._中价值数量.setText(str(中价值))
        self._低价值数量.setText(str(低价值))
        self._总片段数量.setText(str(高价值 + 中价值 + 低价值))
    
    def 获取过滤选项(self) -> str:
        """获取当前选择的过滤选项
        
        Returns:
            过滤选项文本
        """
        return self._过滤选择.currentText()
    
    def 重置(self) -> None:
        """重置所有显示"""
        self._评分值标签.setText("--")
        self._评分值标签.setStyleSheet(f"color: {颜色.文字}; font-size: 14px; font-weight: bold;")
        self._评分进度条.setValue(0)
        self._评分进度条.setStyleSheet(f"""
            QProgressBar {{
                border: none;
                border-radius: 4px;
                background-color: {颜色.边框};
            }}
            QProgressBar::chunk {{
                border-radius: 4px;
                background-color: {颜色.成功};
            }}
        """)
        self._价值等级标签.setText("等级: --")
        self._价值等级标签.setStyleSheet(f"color: {颜色.次要文字}; font-size: 11px;")
        self._高价值数量.setText("0")
        self._中价值数量.setText("0")
        self._低价值数量.setText("0")
        self._总片段数量.setText("0")



class 数据收集页(QWidget):
    """
    数据收集页面
    
    提供数据收集功能的完整界面，包括控制面板、状态监控、游戏画面预览和智能录制控制。
    """
    
    # 信号定义
    开始录制 = Signal(str)  # 训练模式
    暂停录制 = Signal()
    停止录制 = Signal()
    
    def __init__(self, parent=None):
        """初始化数据收集页面"""
        super().__init__(parent)
        
        # 状态
        self._录制中 = False
        self._已暂停 = False
        self._倒计时 = 0
        self._倒计时定时器: Optional[QTimer] = None
        
        self._初始化界面()
    
    def _初始化界面(self) -> None:
        """初始化界面布局"""
        主布局 = QVBoxLayout(self)
        主布局.setContentsMargins(24, 24, 24, 24)
        主布局.setSpacing(16)
        
        # 页面标题
        标题 = QLabel("🎥 数据收集")
        标题.setStyleSheet(f"""
            font-size: 22px;
            font-weight: bold;
            color: {颜色.标题};
        """)
        主布局.addWidget(标题)
        
        # 内容区域 (左右布局)
        内容容器 = QWidget()
        内容布局 = QHBoxLayout(内容容器)
        内容布局.setContentsMargins(0, 0, 0, 0)
        内容布局.setSpacing(16)
        
        # 左侧: 控制面板和状态监控
        左侧容器 = QWidget()
        左侧布局 = QVBoxLayout(左侧容器)
        左侧布局.setContentsMargins(0, 0, 0, 0)
        左侧布局.setSpacing(12)
        
        # 控制面板
        self._控制面板 = 控制面板()
        self._控制面板.开始点击.connect(self._处理开始)
        self._控制面板.暂停点击.connect(self._处理暂停)
        self._控制面板.停止点击.connect(self._处理停止)
        左侧布局.addWidget(self._控制面板)
        
        # 状态监控
        self._状态监控 = 状态监控()
        左侧布局.addWidget(self._状态监控)
        
        左侧布局.addStretch()
        内容布局.addWidget(左侧容器, 1)
        
        # 中间: 智能录制面板
        self._智能录制面板 = 智能录制面板()
        self._智能录制面板.setFixedWidth(200)
        内容布局.addWidget(self._智能录制面板)
        
        # 右侧: 游戏画面预览
        self._画面预览 = 画面预览()
        内容布局.addWidget(self._画面预览)
        
        主布局.addWidget(内容容器, 1)
        
        # 操作说明
        说明卡片 = QFrame()
        说明卡片.setStyleSheet(f"""
            QFrame {{
                background-color: {颜色.选中背景};
                border-radius: 12px;
                border: 1px solid {颜色.边框};
            }}
        """)
        说明布局 = QVBoxLayout(说明卡片)
        说明布局.setContentsMargins(16, 12, 16, 12)
        说明布局.setSpacing(8)
        
        说明标题 = QLabel("📋 操作说明")
        说明标题.setStyleSheet(f"color: {颜色.标题}; font-size: 14px; font-weight: 500;")
        说明布局.addWidget(说明标题)
        
        说明内容 = QLabel(
            "1. 选择训练模式 → 2. 点击开始录制 → 3. 切换到游戏窗口 → "
            "4. 进行游戏操作 → 5. 按T暂停/继续，ESC停止 | "
            "💡 智能录制会自动评估片段价值，可选择保存策略"
        )
        说明内容.setStyleSheet(f"color: {颜色.文字}; font-size: 12px;")
        说明内容.setWordWrap(True)
        说明布局.addWidget(说明内容)
        
        主布局.addWidget(说明卡片)
    
    def _处理开始(self) -> None:
        """处理开始录制"""
        # 开始倒计时
        self._倒计时 = 4
        self._状态监控.更新录制状态(f"倒计时 {self._倒计时}...")
        self._控制面板.设置录制状态(True, False)
        
        # 创建倒计时定时器
        self._倒计时定时器 = QTimer(self)
        self._倒计时定时器.timeout.connect(self._更新倒计时)
        self._倒计时定时器.start(1000)
    
    def _更新倒计时(self) -> None:
        """更新倒计时"""
        self._倒计时 -= 1
        
        if self._倒计时 > 0:
            self._状态监控.更新录制状态(f"倒计时 {self._倒计时}...")
        else:
            # 倒计时结束，开始录制
            if self._倒计时定时器:
                self._倒计时定时器.stop()
                self._倒计时定时器 = None
            
            self._录制中 = True
            self._已暂停 = False
            self._状态监控.更新录制状态("录制中")
            
            # 发送开始录制信号
            模式 = self._控制面板.获取当前模式()
            self.开始录制.emit(模式)
    
    def _处理暂停(self) -> None:
        """处理暂停/继续"""
        if self._录制中:
            self._已暂停 = not self._已暂停
            self._控制面板.设置录制状态(True, self._已暂停)
            
            if self._已暂停:
                self._状态监控.更新录制状态("已暂停")
            else:
                self._状态监控.更新录制状态("录制中")
            
            self.暂停录制.emit()
    
    def _处理停止(self) -> None:
        """处理停止录制"""
        # 停止倒计时定时器
        if self._倒计时定时器:
            self._倒计时定时器.stop()
            self._倒计时定时器 = None
        
        self._录制中 = False
        self._已暂停 = False
        self._倒计时 = 0
        
        self._控制面板.设置录制状态(False, False)
        self._状态监控.更新录制状态("已停止")
        self._画面预览.清除预览()
        self._智能录制面板.重置()
        
        self.停止录制.emit()
    
    @Slot(dict)
    def 更新状态(self, 状态数据: dict) -> None:
        """
        更新状态显示
        
        参数:
            状态数据: 包含状态信息的字典
                - 样本数量: int
                - 文件编号: int
                - 帧率: float
                - 当前动作: str
                - 帧图像: np.ndarray (可选)
                - 价值评分: float (可选) - 智能录制价值评分
                - 高价值片段: int (可选) - 高价值片段数量
                - 中价值片段: int (可选) - 中价值片段数量
                - 低价值片段: int (可选) - 低价值片段数量
        """
        if "样本数量" in 状态数据:
            self._状态监控.更新样本数量(状态数据["样本数量"])
        
        if "文件编号" in 状态数据:
            self._状态监控.更新文件编号(状态数据["文件编号"])
        
        if "帧率" in 状态数据:
            self._状态监控.更新帧率(状态数据["帧率"])
        
        if "当前动作" in 状态数据:
            self._状态监控.更新当前动作(状态数据["当前动作"])
        
        if "帧图像" in 状态数据 and 状态数据["帧图像"] is not None:
            self._画面预览.更新预览(状态数据["帧图像"])
        
        # 智能录制相关状态更新
        if "价值评分" in 状态数据:
            self._智能录制面板.更新价值评分(状态数据["价值评分"])
        
        if all(key in 状态数据 for key in ["高价值片段", "中价值片段", "低价值片段"]):
            self._智能录制面板.更新片段统计(
                状态数据["高价值片段"],
                状态数据["中价值片段"],
                状态数据["低价值片段"]
            )
    
    def 显示文件保存通知(self, 文件路径: str, 样本数: int) -> None:
        """显示文件保存通知"""
        # 这里可以通过主窗口的通知系统显示
        pass
    
    def 处理快捷键暂停(self) -> None:
        """处理快捷键T暂停/继续"""
        if self._录制中:
            self._处理暂停()
    
    def 处理快捷键停止(self) -> None:
        """处理快捷键ESC停止"""
        if self._录制中 or self._倒计时 > 0:
            self._处理停止()
    
    def 是否录制中(self) -> bool:
        """返回是否正在录制"""
        return self._录制中
    
    def 是否已暂停(self) -> bool:
        """返回是否已暂停"""
        return self._已暂停
    
    def 获取智能录制面板(self) -> 智能录制面板:
        """获取智能录制面板组件"""
        return self._智能录制面板
    
    def 获取过滤选项(self) -> str:
        """获取当前选择的过滤选项
        
        Returns:
            过滤选项文本: "保留全部", "仅保留高价值", "自动过滤低价值"
        """
        return self._智能录制面板.获取过滤选项()
