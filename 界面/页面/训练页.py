# -*- coding: utf-8 -*-
"""
训练页面

提供模型训练功能的图形界面，包括模式选择、控制面板、进度显示、损失曲线和日志区域。

布局结构（上下两区 60:40）:
- 上区（60%）：左栏训练设置卡片 + 右栏训练进度卡片
- 下区（40%）：训练日志卡片

Requirements: 3.1, 3.2, 3.3, 3.4, 3.5
"""

from typing import Optional, List
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QGridLayout, QComboBox,
    QProgressBar, QTextEdit, QSplitter, QSizePolicy,
    QSpinBox, QDoubleSpinBox, QScrollArea
)
from PySide6.QtCore import Signal, Slot, Qt, QTimer
from PySide6.QtGui import QTextCursor, QColor

from 界面.样式.主题 import 颜色
from 界面.样式.布局常量 import 布局常量
from 界面.组件.通用组件 import Card, CardWithAction

# 尝试导入pyqtgraph用于绘制损失曲线
try:
    import pyqtgraph as pg
    HAS_PYQTGRAPH = True
except ImportError:
    HAS_PYQTGRAPH = False


class 训练设置卡片(Card):
    """
    训练设置卡片组件
    
    包含训练模式选择、参数设置和控制按钮
    Requirements: 3.2, 3.3
    """
    
    # 信号定义
    开始训练点击 = Signal()
    停止训练点击 = Signal()
    模式改变 = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__("训练设置", "", parent)
        self._初始化内容()
    
    def _初始化内容(self) -> None:
        """初始化卡片内容"""
        内容布局 = self.获取内容布局()
        
        # 模式选择区域
        模式容器 = QWidget()
        模式布局 = QHBoxLayout(模式容器)
        模式布局.setContentsMargins(0, 0, 0, 0)
        模式布局.setSpacing(布局常量.按钮间距)
        
        模式标签 = QLabel("训练模式:")
        模式标签.setStyleSheet(f"color: {颜色.文字}; font-size: {布局常量.正文字号}px;")
        模式布局.addWidget(模式标签)
        
        self._模式选择 = QComboBox()
        self._模式选择.addItems(["主线任务", "自动战斗"])
        self._模式选择.setFixedWidth(120)
        self._模式选择.setFixedHeight(布局常量.表单控件高度)
        self._模式选择.currentTextChanged.connect(self.模式改变.emit)
        模式布局.addWidget(self._模式选择)
        模式布局.addStretch()
        
        内容布局.addWidget(模式容器)
        
        # 参数设置区域
        参数容器 = QWidget()
        参数布局 = QGridLayout(参数容器)
        参数布局.setContentsMargins(0, 0, 0, 0)
        参数布局.setSpacing(布局常量.表单行间距)
        
        # 训练轮次
        轮次标签 = QLabel("训练轮次:")
        轮次标签.setStyleSheet(f"color: {颜色.文字}; font-size: {布局常量.正文字号}px;")
        参数布局.addWidget(轮次标签, 0, 0)
        
        self._轮次输入 = QSpinBox()
        self._轮次输入.setRange(1, 1000)
        self._轮次输入.setValue(10)
        self._轮次输入.setFixedWidth(80)
        self._轮次输入.setFixedHeight(布局常量.表单控件高度)
        参数布局.addWidget(self._轮次输入, 0, 1)
        
        # 批次大小
        批次标签 = QLabel("批次大小:")
        批次标签.setStyleSheet(f"color: {颜色.文字}; font-size: {布局常量.正文字号}px;")
        参数布局.addWidget(批次标签, 0, 2)
        
        self._批次输入 = QSpinBox()
        self._批次输入.setRange(1, 256)
        self._批次输入.setValue(32)
        self._批次输入.setFixedWidth(80)
        self._批次输入.setFixedHeight(布局常量.表单控件高度)
        参数布局.addWidget(self._批次输入, 0, 3)
        
        # 学习率
        学习率标签 = QLabel("学习率:")
        学习率标签.setStyleSheet(f"color: {颜色.文字}; font-size: {布局常量.正文字号}px;")
        参数布局.addWidget(学习率标签, 1, 0)
        
        self._学习率输入 = QDoubleSpinBox()
        self._学习率输入.setRange(0.0001, 0.1)
        self._学习率输入.setValue(0.001)
        self._学习率输入.setDecimals(4)
        self._学习率输入.setSingleStep(0.0001)
        self._学习率输入.setFixedWidth(80)
        self._学习率输入.setFixedHeight(布局常量.表单控件高度)
        参数布局.addWidget(self._学习率输入, 1, 1)
        
        参数布局.setColumnStretch(4, 1)
        内容布局.addWidget(参数容器)
        
        # 分隔线
        分隔线 = QFrame()
        分隔线.setFrameShape(QFrame.HLine)
        分隔线.setStyleSheet(f"background-color: {颜色.边框};")
        分隔线.setFixedHeight(1)
        内容布局.addWidget(分隔线)
        
        # 按钮容器
        按钮容器 = QWidget()
        按钮布局 = QHBoxLayout(按钮容器)
        按钮布局.setContentsMargins(0, 0, 0, 0)
        按钮布局.setSpacing(布局常量.按钮间距)
        
        # 开始训练按钮
        self._开始按钮 = QPushButton("开始训练")
        self._开始按钮.setFixedHeight(布局常量.按钮高度)
        self._开始按钮.setMinimumWidth(布局常量.按钮最小宽度)
        self._开始按钮.setCursor(Qt.PointingHandCursor)
        self._开始按钮.setStyleSheet(f"""
            QPushButton {{
                background-color: {颜色.成功};
                color: white;
                border: none;
                border-radius: {布局常量.按钮圆角}px;
                font-size: {布局常量.按钮文字字号}px;
                padding: 0 {布局常量.按钮水平内边距}px;
            }}
            QPushButton:hover {{
                background-color: #059669;
            }}
            QPushButton:disabled {{
                background-color: {颜色.按钮禁用};
                color: {颜色.禁用文字};
            }}
        """)
        self._开始按钮.clicked.connect(self.开始训练点击.emit)
        按钮布局.addWidget(self._开始按钮)
        
        # 停止训练按钮
        self._停止按钮 = QPushButton("停止训练")
        self._停止按钮.setFixedHeight(布局常量.按钮高度)
        self._停止按钮.setMinimumWidth(布局常量.按钮最小宽度)
        self._停止按钮.setCursor(Qt.PointingHandCursor)
        self._停止按钮.setEnabled(False)
        self._停止按钮.setStyleSheet(f"""
            QPushButton {{
                background-color: {颜色.错误};
                color: white;
                border: none;
                border-radius: {布局常量.按钮圆角}px;
                font-size: {布局常量.按钮文字字号}px;
                padding: 0 {布局常量.按钮水平内边距}px;
            }}
            QPushButton:hover {{
                background-color: #DC2626;
            }}
            QPushButton:disabled {{
                background-color: {颜色.按钮禁用};
                color: {颜色.禁用文字};
            }}
        """)
        self._停止按钮.clicked.connect(self.停止训练点击.emit)
        按钮布局.addWidget(self._停止按钮)
        
        按钮布局.addStretch()
        内容布局.addWidget(按钮容器)
    
    def 设置训练状态(self, 训练中: bool) -> None:
        """设置训练状态，更新按钮和控件状态"""
        self._开始按钮.setEnabled(not 训练中)
        self._停止按钮.setEnabled(训练中)
        self._模式选择.setEnabled(not 训练中)
        self._轮次输入.setEnabled(not 训练中)
        self._批次输入.setEnabled(not 训练中)
        self._学习率输入.setEnabled(not 训练中)
    
    def 获取当前模式(self) -> str:
        """获取当前选择的训练模式"""
        return self._模式选择.currentText()
    
    def 获取训练轮次(self) -> int:
        """获取训练轮次"""
        return self._轮次输入.value()
    
    def 获取批次大小(self) -> int:
        """获取批次大小"""
        return self._批次输入.value()
    
    def 获取学习率(self) -> float:
        """获取学习率"""
        return self._学习率输入.value()


class 训练进度卡片(Card):
    """
    训练进度卡片组件
    
    显示进度条、当前轮次、损失值、预计时间和损失曲线
    Requirements: 3.4
    """
    
    def __init__(self, parent=None):
        super().__init__("训练进度", "📈", parent)
        self._损失历史: List[float] = []
        self._初始化内容()
    
    def _初始化内容(self) -> None:
        """初始化卡片内容"""
        内容布局 = self.获取内容布局()
        
        # 进度条
        self._进度条 = QProgressBar()
        self._进度条.setFixedHeight(布局常量.进度条高度最大)
        self._进度条.setMinimumHeight(布局常量.进度条高度最大)
        self._进度条.setValue(0)
        self._进度条.setTextVisible(True)
        self._进度条.setFormat("%p%")
        self._进度条.setStyleSheet(f"""
            QProgressBar {{
                border: none;
                border-radius: {布局常量.进度条圆角}px;
                background-color: {颜色.边框};
                text-align: center;
                font-size: {布局常量.正文字号}px;
                color: {颜色.文字};
                min-height: {布局常量.进度条高度最大}px;
            }}
            QProgressBar::chunk {{
                background-color: {颜色.成功};
                border-radius: {布局常量.进度条圆角}px;
            }}
        """)
        内容布局.addWidget(self._进度条)
        
        # 状态信息网格
        状态容器 = QWidget()
        状态网格 = QGridLayout(状态容器)
        状态网格.setContentsMargins(0, 0, 0, 0)
        状态网格.setSpacing(布局常量.表单行间距)
        
        # 当前轮次
        self._轮次标签 = self._创建状态项("当前轮次:", "0 / 0", 状态网格, 0, 0)
        
        # 当前损失
        self._损失标签 = self._创建状态项("当前损失:", "0.0000", 状态网格, 0, 1)
        
        # 训练状态
        self._状态标签 = self._创建状态项("训练状态:", "未开始", 状态网格, 1, 0)
        
        # 预计剩余时间
        self._剩余时间标签 = self._创建状态项("剩余时间:", "--:--", 状态网格, 1, 1)
        
        内容布局.addWidget(状态容器)
        
        # 分隔线
        分隔线 = QFrame()
        分隔线.setFrameShape(QFrame.HLine)
        分隔线.setStyleSheet(f"background-color: {颜色.边框};")
        分隔线.setFixedHeight(1)
        内容布局.addWidget(分隔线)
        
        # 损失曲线标题
        曲线标题 = QLabel("损失曲线")
        曲线标题.setStyleSheet(f"""
            font-size: {布局常量.正文字号}px;
            font-weight: bold;
            color: {颜色.标题};
        """)
        内容布局.addWidget(曲线标题)
        
        # 损失曲线图
        if HAS_PYQTGRAPH:
            self._绘图控件 = pg.PlotWidget()
            self._绘图控件.setBackground('w')
            self._绘图控件.setMinimumHeight(100)
            self._绘图控件.showGrid(x=True, y=True, alpha=0.3)
            self._绘图控件.setLabel('left', '损失值')
            self._绘图控件.setLabel('bottom', '迭代次数')
            
            # 创建曲线
            self._曲线 = self._绘图控件.plot(
                pen=pg.mkPen(color=颜色.主色, width=2)
            )
            
            内容布局.addWidget(self._绘图控件, 1)
        else:
            self._占位标签 = QLabel("损失曲线需要安装 pyqtgraph 库\npip install pyqtgraph")
            self._占位标签.setAlignment(Qt.AlignCenter)
            self._占位标签.setMinimumHeight(80)
            self._占位标签.setStyleSheet(f"""
                color: {颜色.次要文字};
                font-size: {布局常量.次要文字字号}px;
                background-color: {颜色.悬停背景};
                border-radius: {布局常量.卡片圆角}px;
            """)
            内容布局.addWidget(self._占位标签, 1)
    
    def _创建状态项(self, 标题: str, 初始值: str, 网格: QGridLayout, 
                   行: int, 列: int) -> QLabel:
        """创建状态项"""
        容器 = QWidget()
        容器布局 = QHBoxLayout(容器)
        容器布局.setContentsMargins(0, 0, 0, 0)
        容器布局.setSpacing(4)
        
        标题标签 = QLabel(标题)
        标题标签.setStyleSheet(f"color: {颜色.次要文字}; font-size: {布局常量.次要文字字号}px;")
        容器布局.addWidget(标题标签)
        
        值标签 = QLabel(初始值)
        值标签.setStyleSheet(f"color: {颜色.文字}; font-size: {布局常量.次要文字字号}px; font-weight: 500;")
        容器布局.addWidget(值标签)
        容器布局.addStretch()
        
        网格.addWidget(容器, 行, 列)
        return 值标签
    
    def 更新进度(self, 当前轮次: int, 总轮次: int) -> None:
        """更新进度显示"""
        if 总轮次 > 0:
            进度 = int((当前轮次 / 总轮次) * 100)
            self._进度条.setValue(进度)
        self._轮次标签.setText(f"{当前轮次} / {总轮次}")
    
    def 更新损失(self, 损失值: float) -> None:
        """更新损失值显示"""
        self._损失标签.setText(f"{损失值:.4f}")
    
    def 更新状态(self, 状态: str) -> None:
        """更新训练状态显示"""
        颜色映射 = {
            "训练中": 颜色.成功,
            "已暂停": 颜色.警告,
            "已停止": 颜色.次要文字,
            "已完成": 颜色.主色,
            "未开始": 颜色.次要文字,
            "准备中": 颜色.主色,
        }
        状态颜色 = 颜色映射.get(状态, 颜色.文字)
        self._状态标签.setText(状态)
        self._状态标签.setStyleSheet(f"color: {状态颜色}; font-size: {布局常量.次要文字字号}px; font-weight: 500;")
    
    def 更新剩余时间(self, 时间字符串: str) -> None:
        """更新预计剩余时间"""
        self._剩余时间标签.setText(时间字符串)
    
    def 添加损失值(self, 损失值: float) -> None:
        """添加新的损失值到曲线"""
        self._损失历史.append(损失值)
        
        if HAS_PYQTGRAPH:
            self._曲线.setData(range(len(self._损失历史)), self._损失历史)
    
    def 清除曲线(self) -> None:
        """清除曲线数据"""
        self._损失历史.clear()
        
        if HAS_PYQTGRAPH:
            self._曲线.setData([], [])
    
    def 重置(self) -> None:
        """重置进度显示"""
        self._进度条.setValue(0)
        self._轮次标签.setText("0 / 0")
        self._损失标签.setText("0.0000")
        self._状态标签.setText("未开始")
        self._剩余时间标签.setText("--:--")
        self.清除曲线()
    
    def 获取损失历史(self) -> List[float]:
        """获取损失历史数据"""
        return self._损失历史.copy()


class 训练日志卡片(CardWithAction):
    """
    训练日志卡片组件
    
    显示训练日志，支持滚动查看
    Requirements: 3.5
    """
    
    def __init__(self, parent=None):
        super().__init__("训练日志", "", parent)
        self._初始化内容()
    
    def _初始化内容(self) -> None:
        """初始化卡片内容"""
        # 添加清除按钮到标题栏
        清除按钮 = QPushButton("清除")
        清除按钮.setFixedSize(50, 24)
        清除按钮.setCursor(Qt.PointingHandCursor)
        清除按钮.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {颜色.次要文字};
                border: 1px solid {颜色.边框};
                border-radius: 4px;
                font-size: {布局常量.次要文字字号}px;
            }}
            QPushButton:hover {{
                background-color: {颜色.悬停背景};
            }}
        """)
        清除按钮.clicked.connect(self.清除日志)
        self.添加操作按钮(清除按钮)
        
        内容布局 = self.获取内容布局()
        
        # 日志文本框
        self._日志文本 = QTextEdit()
        self._日志文本.setReadOnly(True)
        self._日志文本.setStyleSheet(f"""
            QTextEdit {{
                background-color: {颜色.悬停背景};
                border: none;
                border-radius: {布局常量.卡片圆角}px;
                padding: {布局常量.卡片内边距}px;
                font-family: "Consolas", "Microsoft YaHei";
                font-size: {布局常量.次要文字字号}px;
                color: {颜色.文字};
            }}
        """)
        内容布局.addWidget(self._日志文本, 1)
    
    def 添加日志(self, 消息: str, 级别: str = "信息") -> None:
        """
        添加日志消息
        
        参数:
            消息: 日志内容
            级别: 日志级别 (信息/警告/错误/成功)
        """
        时间戳 = datetime.now().strftime("%H:%M:%S")
        
        颜色映射 = {
            "信息": 颜色.文字,
            "警告": 颜色.警告,
            "错误": 颜色.错误,
            "成功": 颜色.成功,
        }
        
        图标映射 = {
            "信息": "ℹ️",
            "警告": "⚠️",
            "错误": "[X]",
            "成功": "[OK]",
        }
        
        日志颜色 = 颜色映射.get(级别, 颜色.文字)
        图标 = 图标映射.get(级别, "ℹ️")
        
        格式化消息 = f'<span style="color: {颜色.次要文字}">[{时间戳}]</span> ' \
                    f'{图标} <span style="color: {日志颜色}">{消息}</span>'
        
        self._日志文本.append(格式化消息)
        
        # 滚动到底部
        光标 = self._日志文本.textCursor()
        光标.movePosition(QTextCursor.End)
        self._日志文本.setTextCursor(光标)
    
    def 清除日志(self) -> None:
        """清除所有日志"""
        self._日志文本.clear()




class 训练页(QWidget):
    """
    训练页面
    
    提供模型训练功能的完整界面。
    
    布局结构（上下两区 60:40）:
    - 上区（60%）：左栏训练设置卡片 + 右栏训练进度卡片
    - 下区（40%）：训练日志卡片
    
    Requirements: 3.1, 3.2, 3.3, 3.4, 3.5
    """
    
    # 信号定义
    开始训练 = Signal(str)  # 训练模式
    停止训练 = Signal()
    
    def __init__(self, parent=None):
        """初始化训练页面"""
        super().__init__(parent)
        
        # 状态
        self._训练中 = False
        self._开始时间: Optional[datetime] = None
        
        self._初始化界面()
    
    def _初始化界面(self) -> None:
        """
        初始化界面布局
        
        采用上下两区布局（60:40）:
        - 上区: 左栏训练设置 + 右栏训练进度
        - 下区: 训练日志
        
        Requirements: 3.1
        """
        主布局 = QVBoxLayout(self)
        主布局.setContentsMargins(
            布局常量.内容区外边距,
            布局常量.内容区外边距,
            布局常量.内容区外边距,
            布局常量.内容区外边距
        )
        主布局.setSpacing(布局常量.卡片间距)
        
        # 页面标题
        标题 = QLabel("模型训练")
        标题.setStyleSheet(f"""
            font-size: {布局常量.页面标题字号}px;
            font-weight: bold;
            color: {颜色.标题};
        """)
        主布局.addWidget(标题)
        
        # 使用分割器实现上下两区布局
        分割器 = QSplitter(Qt.Vertical)
        分割器.setHandleWidth(布局常量.卡片间距)
        分割器.setStyleSheet("""
            QSplitter::handle {
                background-color: transparent;
            }
        """)
        
        # ==================== 上区（60%）====================
        上区容器 = QWidget()
        上区布局 = QHBoxLayout(上区容器)
        上区布局.setContentsMargins(0, 0, 0, 0)
        上区布局.setSpacing(布局常量.卡片间距)
        
        # 左栏：训练设置卡片 (Requirements: 3.2, 3.3)
        self._训练设置 = 训练设置卡片()
        self._训练设置.开始训练点击.connect(self._处理开始训练)
        self._训练设置.停止训练点击.connect(self._处理停止训练)
        上区布局.addWidget(self._训练设置, 1)
        
        # 右栏：训练进度卡片 (Requirements: 3.4)
        self._训练进度 = 训练进度卡片()
        上区布局.addWidget(self._训练进度, 1)
        
        分割器.addWidget(上区容器)
        
        # ==================== 下区（40%）====================
        # 训练日志卡片 (Requirements: 3.5)
        self._训练日志 = 训练日志卡片()
        分割器.addWidget(self._训练日志)
        
        # 设置上下区比例 60:40
        分割器.setSizes([
            int(布局常量.内容区高度 * 布局常量.训练页上区比例 / 100),
            int(布局常量.内容区高度 * 布局常量.训练页下区比例 / 100)
        ])
        
        主布局.addWidget(分割器, 1)
        
        # 底部提示
        提示卡片 = Card()
        提示卡片.setStyleSheet(f"""
            QFrame#Card {{
                background-color: {颜色.选中背景};
                border-radius: {布局常量.卡片圆角}px;
                border: 1px solid {颜色.边框};
            }}
        """)
        提示布局 = QHBoxLayout()
        提示布局.setContentsMargins(0, 0, 0, 0)
        提示布局.setSpacing(8)
        
        提示图标 = QLabel("💡")
        提示图标.setStyleSheet(f"font-size: {布局常量.页面标题字号}px;")
        提示布局.addWidget(提示图标)
        
        提示文本 = QLabel("训练前请确保已收集足够的训练数据。训练过程中可随时停止，模型会自动保存检查点。")
        提示文本.setStyleSheet(f"color: {颜色.主色}; font-size: {布局常量.次要文字字号}px;")
        提示文本.setWordWrap(True)
        提示布局.addWidget(提示文本, 1)
        
        提示卡片.添加布局(提示布局)
        提示卡片.setMaximumHeight(60)
        
        主布局.addWidget(提示卡片)
    
    def _处理开始训练(self) -> None:
        """处理开始训练"""
        self._训练中 = True
        self._开始时间 = datetime.now()
        
        self._训练设置.设置训练状态(True)
        self._训练进度.更新状态("准备中")
        self._训练进度.清除曲线()
        
        # 添加日志
        模式 = self._训练设置.获取当前模式()
        轮次 = self._训练设置.获取训练轮次()
        批次 = self._训练设置.获取批次大小()
        学习率 = self._训练设置.获取学习率()
        
        self._训练日志.添加日志(f"开始训练 - 模式: {模式}", "信息")
        self._训练日志.添加日志(f"参数: 轮次={轮次}, 批次={批次}, 学习率={学习率}", "信息")
        
        # 发送开始训练信号
        self.开始训练.emit(模式)
    
    def _处理停止训练(self) -> None:
        """处理停止训练"""
        self._训练中 = False
        
        self._训练设置.设置训练状态(False)
        self._训练进度.更新状态("已停止")
        
        # 添加日志
        self._训练日志.添加日志("训练已停止", "警告")
        
        # 发送停止训练信号
        self.停止训练.emit()
    
    @Slot(int, int, float)
    def 更新训练进度(self, 当前轮次: int, 总轮次: int, 损失值: float) -> None:
        """
        更新训练进度
        
        参数:
            当前轮次: 当前训练轮次
            总轮次: 总训练轮次
            损失值: 当前损失值
        """
        self._训练进度.更新进度(当前轮次, 总轮次)
        self._训练进度.更新损失(损失值)
        self._训练进度.更新状态("训练中")
        
        # 添加损失值到曲线
        self._训练进度.添加损失值(损失值)
        
        # 计算预计剩余时间
        if self._开始时间 and 当前轮次 > 0:
            已用时间 = (datetime.now() - self._开始时间).total_seconds()
            每轮时间 = 已用时间 / 当前轮次
            剩余轮次 = 总轮次 - 当前轮次
            剩余秒数 = int(每轮时间 * 剩余轮次)
            
            分钟 = 剩余秒数 // 60
            秒 = 剩余秒数 % 60
            self._训练进度.更新剩余时间(f"{分钟:02d}:{秒:02d}")
        
        # 添加日志
        self._训练日志.添加日志(f"轮次 {当前轮次}/{总轮次}, 损失: {损失值:.4f}", "信息")
    
    @Slot(str)
    def 添加日志(self, 消息: str, 级别: str = "信息") -> None:
        """添加训练日志"""
        self._训练日志.添加日志(消息, 级别)
    
    @Slot(bool, str)
    def 训练完成(self, 成功: bool, 消息: str) -> None:
        """
        训练完成回调
        
        参数:
            成功: 是否成功完成
            消息: 完成消息
        """
        self._训练中 = False
        self._训练设置.设置训练状态(False)
        
        if 成功:
            self._训练进度.更新状态("已完成")
            self._训练日志.添加日志(消息, "成功")
        else:
            self._训练进度.更新状态("已停止")
            self._训练日志.添加日志(消息, "错误")
    
    @Slot(str)
    def 处理错误(self, 错误消息: str) -> None:
        """处理训练错误"""
        self._训练日志.添加日志(错误消息, "错误")
    
    def 是否训练中(self) -> bool:
        """返回是否正在训练"""
        return self._训练中
    
    # ==================== 兼容性方法 ====================
    # 保持与旧版本的兼容性
    
    def 获取控制面板(self) -> 训练设置卡片:
        """获取训练设置卡片（兼容旧版本）"""
        return self._训练设置
    
    def 获取进度面板(self) -> 训练进度卡片:
        """获取训练进度卡片（兼容旧版本）"""
        return self._训练进度
    
    def 获取损失曲线(self) -> 训练进度卡片:
        """获取损失曲线（现在集成在进度卡片中）"""
        return self._训练进度
    
    def 获取训练日志(self) -> 训练日志卡片:
        """获取训练日志卡片"""
        return self._训练日志


# ==================== 兼容性别名 ====================
# 保持与旧版本的兼容性

训练控制面板 = 训练设置卡片
训练进度面板 = 训练进度卡片
训练日志 = 训练日志卡片
损失曲线图 = 训练进度卡片
