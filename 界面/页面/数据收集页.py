# -*- coding: utf-8 -*-
"""
数据收集页面

提供数据收集功能的图形界面，包括控制面板、状态监控和游戏画面预览。
"""

from typing import Optional
import numpy as np

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QGridLayout, QComboBox,
    QSizePolicy
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
        布局.setContentsMargins(20, 16, 20, 16)
        布局.setSpacing(12)
        
        # 标题
        标题 = QLabel("🖥️ 游戏画面预览")
        标题.setStyleSheet(f"""
            font-size: 16px;
            font-weight: bold;
            color: {颜色.标题};
        """)
        布局.addWidget(标题)
        
        # 预览区域
        self._预览标签 = QLabel()
        self._预览标签.setFixedSize(320, 180)
        self._预览标签.setAlignment(Qt.AlignCenter)
        self._预览标签.setStyleSheet(f"""
            background-color: #1E293B;
            border-radius: 8px;
            color: {颜色.次要文字};
            font-size: 13px;
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
                320, 180, 
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



class 数据收集页(QWidget):
    """
    数据收集页面
    
    提供数据收集功能的完整界面，包括控制面板、状态监控和游戏画面预览。
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
        主布局.setSpacing(20)
        
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
        内容布局.setSpacing(20)
        
        # 左侧: 控制面板和状态监控
        左侧容器 = QWidget()
        左侧布局 = QVBoxLayout(左侧容器)
        左侧布局.setContentsMargins(0, 0, 0, 0)
        左侧布局.setSpacing(16)
        
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
            "4. 进行游戏操作 → 5. 按T暂停/继续，ESC停止"
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
