# -*- coding: utf-8 -*-
"""
配置页面

提供图形化的配置管理界面，支持:
- 标签页形式组织配置项 (游戏窗口/模型设置/训练参数/增强模块)
- 各类型输入控件 (滑块/输入框/下拉框/开关)
- 配置说明文字
- 保存和重置功能
- 实时验证输入有效性
- 多游戏配置档案管理 (需求 6.1, 6.3, 6.5)

布局优化 (Requirements 5.1, 5.2, 5.3, 5.5):
- 采用标签页形式组织不同类别的配置
- 包含4个标签页：游戏窗口、模型设置、训练参数、增强模块
- 每个标签页使用表单布局，标签在左，控件在右
- 保存和重置按钮固定在页面底部
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea,
    QFrame, QLabel, QPushButton, QLineEdit, QSpinBox,
    QDoubleSpinBox, QComboBox, QCheckBox, QSlider,
    QFormLayout, QMessageBox, QSizePolicy,
    QFileDialog, QInputDialog, QTabWidget
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from 界面.样式.主题 import 颜色
from 界面.样式.布局常量 import 布局常量
from 界面.组件.通用组件 import Card, 确认对话框, 提示对话框


class 配置页(QWidget):
    """配置管理页面 - 标签页形式布局"""
    
    # 信号定义
    配置已保存 = Signal()
    配置已重置 = Signal()
    档案已切换 = Signal(str)  # 档案切换信号，参数为档案名称
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._配置控件 = {}  # 存储所有配置控件的引用
        self._原始值 = {}    # 存储原始配置值用于重置
        self._配置管理器 = None  # 配置管理器实例
        self._初始化配置管理器()
        self._初始化界面()
        self._加载配置()
    
    def _初始化配置管理器(self):
        """初始化配置管理器"""
        try:
            from 核心.配置管理 import ConfigManager
            self._配置管理器 = ConfigManager(auto_load_last=True)
        except Exception as e:
            print(f"初始化配置管理器失败: {e}")
            self._配置管理器 = None
    
    def _初始化界面(self):
        """初始化界面布局 - 标签页形式 (Requirements 5.1)"""
        主布局 = QVBoxLayout(self)
        主布局.setContentsMargins(
            布局常量.内容区外边距,
            布局常量.内容区外边距,
            布局常量.内容区外边距,
            布局常量.内容区外边距
        )
        主布局.setSpacing(布局常量.卡片间距)
        
        # 页面标题
        标题 = QLabel("配置管理")
        标题.setStyleSheet(f"""
            font-size: {布局常量.页面标题字号}px;
            font-weight: bold;
            color: {颜色.标题};
        """)
        主布局.addWidget(标题)
        
        # 档案管理区域 (需求 6.1, 6.3, 6.5)
        主布局.addWidget(self._创建档案管理卡片())
        
        # 标签页容器 (Requirements 5.1, 5.2)
        self._标签页 = QTabWidget()
        self._标签页.setStyleSheet(f"""
            QTabWidget::pane {{
                border: {布局常量.卡片边框宽度}px solid {颜色.边框};
                border-radius: {布局常量.卡片圆角}px;
                background-color: {颜色.卡片背景};
                padding: {布局常量.卡片内边距}px;
            }}
            QTabBar::tab {{
                background-color: {颜色.卡片背景};
                border: 1px solid {颜色.边框};
                border-bottom: none;
                border-top-left-radius: {布局常量.按钮圆角}px;
                border-top-right-radius: {布局常量.按钮圆角}px;
                padding: 8px 16px;
                margin-right: 2px;
                font-size: {布局常量.正文字号}px;
                color: {颜色.文字};
            }}
            QTabBar::tab:selected {{
                background-color: {颜色.主色};
                color: white;
                font-weight: bold;
            }}
            QTabBar::tab:hover:!selected {{
                background-color: {颜色.悬停背景};
            }}
        """)
        
        # 添加4个标签页 (Requirements 5.2)
        self._标签页.addTab(self._创建游戏窗口标签页(), "游戏窗口")
        self._标签页.addTab(self._创建模型设置标签页(), "模型设置")
        self._标签页.addTab(self._创建训练参数标签页(), "训练参数")
        self._标签页.addTab(self._创建增强模块标签页(), "增强模块")
        
        主布局.addWidget(self._标签页, 1)
        
        # 底部按钮区域 (Requirements 5.5)
        主布局.addWidget(self._创建底部按钮区域())
    
    def _创建档案管理卡片(self) -> Card:
        """创建档案管理卡片 (需求 6.1, 6.3, 6.5)"""
        卡片 = Card("配置档案")
        
        # 档案管理布局
        档案布局 = QHBoxLayout()
        档案布局.setSpacing(布局常量.按钮间距)
        
        # 档案选择下拉框 (需求 6.1)
        self._档案选择 = QComboBox()
        self._档案选择.setFixedWidth(160)
        self._档案选择.setFixedHeight(布局常量.表单控件高度)
        self._档案选择.currentTextChanged.connect(self._切换档案)
        档案布局.addWidget(self._档案选择)
        
        # 新建档案按钮
        self._新建档案按钮 = QPushButton("+ 新建")
        self._新建档案按钮.setFixedSize(70, 布局常量.按钮高度)
        self._新建档案按钮.setStyleSheet(f"""
            QPushButton {{
                background-color: {颜色.成功};
                color: white;
                border: none;
                border-radius: {布局常量.按钮圆角}px;
                font-size: {布局常量.按钮文字字号}px;
            }}
            QPushButton:hover {{
                background-color: #059669;
            }}
        """)
        self._新建档案按钮.clicked.connect(self._新建档案)
        档案布局.addWidget(self._新建档案按钮)
        
        # 导入按钮 (需求 6.5)
        self._导入按钮 = QPushButton("导入")
        self._导入按钮.setFixedSize(70, 布局常量.按钮高度)
        self._导入按钮.setStyleSheet(f"""
            QPushButton {{
                background-color: {颜色.卡片背景};
                color: {颜色.文字};
                border: 1px solid {颜色.边框};
                border-radius: {布局常量.按钮圆角}px;
                font-size: {布局常量.按钮文字字号}px;
            }}
            QPushButton:hover {{
                background-color: {颜色.悬停背景};
            }}
        """)
        self._导入按钮.clicked.connect(self._导入档案)
        档案布局.addWidget(self._导入按钮)
        
        # 导出按钮 (需求 6.3)
        self._导出按钮 = QPushButton("导出")
        self._导出按钮.setFixedSize(70, 布局常量.按钮高度)
        self._导出按钮.setStyleSheet(f"""
            QPushButton {{
                background-color: {颜色.卡片背景};
                color: {颜色.文字};
                border: 1px solid {颜色.边框};
                border-radius: {布局常量.按钮圆角}px;
                font-size: {布局常量.按钮文字字号}px;
            }}
            QPushButton:hover {{
                background-color: {颜色.悬停背景};
            }}
        """)
        self._导出按钮.clicked.connect(self._导出档案)
        档案布局.addWidget(self._导出按钮)
        
        # 删除按钮 (需求 4.1, 4.2, 4.3, 4.4)
        self._删除档案按钮 = QPushButton("删除")
        self._删除档案按钮.setFixedSize(60, 布局常量.按钮高度)
        self._删除档案按钮.setStyleSheet(f"""
            QPushButton {{
                background-color: {颜色.卡片背景};
                color: {颜色.错误};
                border: 1px solid {颜色.边框};
                border-radius: {布局常量.按钮圆角}px;
                font-size: {布局常量.按钮文字字号}px;
            }}
            QPushButton:hover {{
                background-color: #FEE2E2;
                border-color: {颜色.错误};
            }}
        """)
        self._删除档案按钮.clicked.connect(self._删除档案)
        档案布局.addWidget(self._删除档案按钮)
        
        档案布局.addStretch()
        
        卡片.添加布局(档案布局)
        
        # 刷新档案列表
        self._刷新档案列表()
        
        return 卡片
    
    def _创建标签页内容(self, 表单布局: QFormLayout) -> QWidget:
        """创建标签页内容容器，支持滚动 (Requirements 5.6)"""
        # 滚动区域
        滚动区域 = QScrollArea()
        滚动区域.setWidgetResizable(True)
        滚动区域.setFrameShape(QFrame.NoFrame)
        滚动区域.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # 内容容器
        内容容器 = QWidget()
        内容布局 = QVBoxLayout(内容容器)
        内容布局.setContentsMargins(布局常量.卡片内边距, 布局常量.卡片内边距,
                                  布局常量.卡片内边距, 布局常量.卡片内边距)
        内容布局.setSpacing(布局常量.表单行间距)
        
        内容布局.addLayout(表单布局)
        内容布局.addStretch()
        
        滚动区域.setWidget(内容容器)
        return 滚动区域
    
    def _创建游戏窗口标签页(self) -> QWidget:
        """创建游戏窗口配置标签页 (Requirements 5.3)"""
        表单布局 = QFormLayout()
        表单布局.setSpacing(布局常量.表单行间距)
        表单布局.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        # 快捷选择分组 - 从进程获取窗口
        分组标题0 = QLabel("快捷选择")
        分组标题0.setStyleSheet(f"""
            font-size: {布局常量.卡片标题字号}px;
            font-weight: bold;
            color: {颜色.标题};
            padding: 8px 0 4px 0;
        """)
        表单布局.addRow(分组标题0)
        
        # 进程选择区域
        进程选择容器 = QWidget()
        进程选择布局 = QHBoxLayout(进程选择容器)
        进程选择布局.setContentsMargins(0, 0, 0, 0)
        进程选择布局.setSpacing(8)
        
        # 进程下拉框
        self._进程选择 = QComboBox()
        self._进程选择.setFixedWidth(280)
        self._进程选择.setFixedHeight(布局常量.表单控件高度)
        self._进程选择.setPlaceholderText("选择游戏窗口...")
        进程选择布局.addWidget(self._进程选择)
        
        # 刷新按钮
        self._刷新进程按钮 = QPushButton("刷新")
        self._刷新进程按钮.setFixedSize(32, 布局常量.表单控件高度)
        self._刷新进程按钮.setToolTip("刷新窗口列表")
        self._刷新进程按钮.setStyleSheet(f"""
            QPushButton {{
                background-color: {颜色.卡片背景};
                color: {颜色.文字};
                border: 1px solid {颜色.边框};
                border-radius: {布局常量.按钮圆角}px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {颜色.悬停背景};
            }}
        """)
        self._刷新进程按钮.clicked.connect(self._刷新窗口列表)
        进程选择布局.addWidget(self._刷新进程按钮)
        
        # 应用按钮
        self._应用窗口按钮 = QPushButton("应用")
        self._应用窗口按钮.setFixedSize(60, 布局常量.表单控件高度)
        self._应用窗口按钮.setToolTip("将选中窗口的位置应用到配置")
        self._应用窗口按钮.setStyleSheet(f"""
            QPushButton {{
                background-color: {颜色.成功};
                color: white;
                border: none;
                border-radius: {布局常量.按钮圆角}px;
                font-size: {布局常量.按钮文字字号}px;
            }}
            QPushButton:hover {{
                background-color: #059669;
            }}
        """)
        self._应用窗口按钮.clicked.connect(self._应用选中窗口)
        进程选择布局.addWidget(self._应用窗口按钮)
        
        进程选择布局.addStretch()
        
        表单布局.addRow("游戏窗口:", self._创建带说明的控件(进程选择容器, "选择游戏进程，自动获取窗口位置"))
        
        # 初始化时刷新窗口列表
        self._刷新窗口列表()
        
        # 窗口区域设置分组
        分组标题1 = QLabel("窗口区域")
        分组标题1.setStyleSheet(f"""
            font-size: {布局常量.卡片标题字号}px;
            font-weight: bold;
            color: {颜色.标题};
            padding: 8px 0 4px 0;
        """)
        表单布局.addRow(分组标题1)
        
        # 游戏窗口区域 - 左
        左边界 = QSpinBox()
        左边界.setRange(0, 3840)
        左边界.setSuffix(" px")
        左边界.setFixedWidth(布局常量.表单控件最小宽度 + 40)
        左边界.setFixedHeight(布局常量.表单控件高度)
        self._配置控件["游戏窗口_左"] = 左边界
        表单布局.addRow("窗口左边界:", self._创建带说明的控件(左边界, "游戏窗口左侧起始位置"))
        
        # 游戏窗口区域 - 上
        上边界 = QSpinBox()
        上边界.setRange(0, 2160)
        上边界.setSuffix(" px")
        上边界.setFixedWidth(布局常量.表单控件最小宽度 + 40)
        上边界.setFixedHeight(布局常量.表单控件高度)
        self._配置控件["游戏窗口_上"] = 上边界
        表单布局.addRow("窗口上边界:", self._创建带说明的控件(上边界, "游戏窗口顶部起始位置"))
        
        # 游戏窗口区域 - 右
        右边界 = QSpinBox()
        右边界.setRange(0, 3840)
        右边界.setSuffix(" px")
        右边界.setFixedWidth(布局常量.表单控件最小宽度 + 40)
        右边界.setFixedHeight(布局常量.表单控件高度)
        self._配置控件["游戏窗口_右"] = 右边界
        表单布局.addRow("窗口右边界:", self._创建带说明的控件(右边界, "游戏窗口右侧结束位置"))
        
        # 游戏窗口区域 - 下
        下边界 = QSpinBox()
        下边界.setRange(0, 2160)
        下边界.setSuffix(" px")
        下边界.setFixedWidth(布局常量.表单控件最小宽度 + 40)
        下边界.setFixedHeight(布局常量.表单控件高度)
        self._配置控件["游戏窗口_下"] = 下边界
        表单布局.addRow("窗口下边界:", self._创建带说明的控件(下边界, "游戏窗口底部结束位置"))
        
        # 分辨率设置分组
        分组标题2 = QLabel("分辨率设置")
        分组标题2.setStyleSheet(f"""
            font-size: {布局常量.卡片标题字号}px;
            font-weight: bold;
            color: {颜色.标题};
            padding: 12px 0 4px 0;
        """)
        表单布局.addRow(分组标题2)
        
        # 游戏分辨率 - 宽度
        游戏宽度 = QSpinBox()
        游戏宽度.setRange(640, 3840)
        游戏宽度.setSuffix(" px")
        游戏宽度.setFixedWidth(布局常量.表单控件最小宽度 + 40)
        游戏宽度.setFixedHeight(布局常量.表单控件高度)
        self._配置控件["游戏宽度"] = 游戏宽度
        表单布局.addRow("游戏宽度:", self._创建带说明的控件(游戏宽度, "游戏画面的水平分辨率"))
        
        # 游戏分辨率 - 高度
        游戏高度 = QSpinBox()
        游戏高度.setRange(480, 2160)
        游戏高度.setSuffix(" px")
        游戏高度.setFixedWidth(布局常量.表单控件最小宽度 + 40)
        游戏高度.setFixedHeight(布局常量.表单控件高度)
        self._配置控件["游戏高度"] = 游戏高度
        表单布局.addRow("游戏高度:", self._创建带说明的控件(游戏高度, "游戏画面的垂直分辨率"))
        
        return self._创建标签页内容(表单布局)
    
    def _刷新窗口列表(self):
        """刷新可用窗口列表"""
        self._进程选择.clear()
        self._窗口信息缓存 = {}  # 缓存窗口信息
        
        try:
            import ctypes
            from ctypes import wintypes
            
            # Windows API
            user32 = ctypes.windll.user32
            
            # 枚举窗口回调函数
            窗口列表 = []
            
            def 枚举窗口回调(hwnd, lParam):
                # 检查窗口是否可见
                if not user32.IsWindowVisible(hwnd):
                    return True
                
                # 获取窗口标题
                长度 = user32.GetWindowTextLengthW(hwnd)
                if 长度 == 0:
                    return True
                
                缓冲区 = ctypes.create_unicode_buffer(长度 + 1)
                user32.GetWindowTextW(hwnd, 缓冲区, 长度 + 1)
                标题 = 缓冲区.value
                
                # 过滤掉一些系统窗口
                排除列表 = ['Program Manager', 'MSCTFIME UI', 'Default IME', 
                          'Windows Input Experience', 'Settings', '']
                if 标题 in 排除列表:
                    return True
                
                # 获取窗口位置
                rect = wintypes.RECT()
                user32.GetWindowRect(hwnd, ctypes.byref(rect))
                
                # 过滤掉太小的窗口
                宽度 = rect.right - rect.left
                高度 = rect.bottom - rect.top
                if 宽度 < 200 or 高度 < 200:
                    return True
                
                窗口列表.append({
                    'hwnd': hwnd,
                    '标题': 标题,
                    '左': rect.left,
                    '上': rect.top,
                    '右': rect.right,
                    '下': rect.bottom,
                    '宽度': 宽度,
                    '高度': 高度
                })
                return True
            
            # 定义回调类型
            WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
            枚举回调 = WNDENUMPROC(枚举窗口回调)
            
            # 枚举所有窗口
            user32.EnumWindows(枚举回调, 0)
            
            # 添加到下拉框
            for 窗口 in 窗口列表:
                显示文本 = f"{窗口['标题'][:30]}... ({窗口['宽度']}x{窗口['高度']})" if len(窗口['标题']) > 30 else f"{窗口['标题']} ({窗口['宽度']}x{窗口['高度']})"
                self._进程选择.addItem(显示文本)
                self._窗口信息缓存[显示文本] = 窗口
            
            if not 窗口列表:
                self._进程选择.addItem("(未找到可用窗口)")
                
        except Exception as e:
            print(f"刷新窗口列表失败: {e}")
            self._进程选择.addItem("(获取窗口列表失败)")
    
    def _应用选中窗口(self):
        """将选中窗口的位置应用到配置"""
        当前选择 = self._进程选择.currentText()
        
        if not 当前选择 or 当前选择.startswith("("):
            提示对话框.警告提示(self, "提示", "请先选择一个有效的游戏窗口")
            return
        
        if 当前选择 not in self._窗口信息缓存:
            提示对话框.警告提示(self, "提示", "窗口信息已失效，请刷新列表后重试")
            return
        
        窗口信息 = self._窗口信息缓存[当前选择]
        
        # 应用窗口位置
        self._配置控件["游戏窗口_左"].setValue(max(0, 窗口信息['左']))
        self._配置控件["游戏窗口_上"].setValue(max(0, 窗口信息['上']))
        self._配置控件["游戏窗口_右"].setValue(窗口信息['右'])
        self._配置控件["游戏窗口_下"].setValue(窗口信息['下'])
        
        # 同步更新分辨率
        self._配置控件["游戏宽度"].setValue(窗口信息['宽度'])
        self._配置控件["游戏高度"].setValue(窗口信息['高度'])
        
        提示对话框.信息提示(
            self, "成功", 
            f"已应用窗口 \"{窗口信息['标题'][:20]}...\" 的位置\n"
            f"区域: ({窗口信息['左']}, {窗口信息['上']}, {窗口信息['右']}, {窗口信息['下']})\n"
            f"分辨率: {窗口信息['宽度']} x {窗口信息['高度']}"
        )
    
    def _创建模型设置标签页(self) -> QWidget:
        """创建模型设置配置标签页 (Requirements 5.3)"""
        表单布局 = QFormLayout()
        表单布局.setSpacing(布局常量.表单行间距)
        表单布局.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        # 输入尺寸分组
        分组标题1 = QLabel("输入尺寸")
        分组标题1.setStyleSheet(f"""
            font-size: {布局常量.卡片标题字号}px;
            font-weight: bold;
            color: {颜色.标题};
            padding: 8px 0 4px 0;
        """)
        表单布局.addRow(分组标题1)
        
        # 模型输入宽度
        输入宽度 = QSpinBox()
        输入宽度.setRange(120, 960)
        输入宽度.setSingleStep(10)
        输入宽度.setSuffix(" px")
        输入宽度.setFixedWidth(布局常量.表单控件最小宽度 + 40)
        输入宽度.setFixedHeight(布局常量.表单控件高度)
        self._配置控件["模型输入宽度"] = 输入宽度
        表单布局.addRow("输入宽度:", self._创建带说明的控件(输入宽度, "模型输入图像的宽度，影响处理速度"))
        
        # 模型输入高度
        输入高度 = QSpinBox()
        输入高度.setRange(68, 540)
        输入高度.setSingleStep(10)
        输入高度.setSuffix(" px")
        输入高度.setFixedWidth(布局常量.表单控件最小宽度 + 40)
        输入高度.setFixedHeight(布局常量.表单控件高度)
        self._配置控件["模型输入高度"] = 输入高度
        表单布局.addRow("输入高度:", self._创建带说明的控件(输入高度, "模型输入图像的高度，影响处理速度"))
        
        # 路径设置分组
        分组标题2 = QLabel("路径设置")
        分组标题2.setStyleSheet(f"""
            font-size: {布局常量.卡片标题字号}px;
            font-weight: bold;
            color: {颜色.标题};
            padding: 12px 0 4px 0;
        """)
        表单布局.addRow(分组标题2)
        
        # 模型保存路径
        模型路径 = QLineEdit()
        模型路径.setPlaceholderText("模型/游戏AI")
        模型路径.setFixedWidth(布局常量.表单控件最大宽度)
        模型路径.setFixedHeight(布局常量.表单控件高度)
        self._配置控件["模型保存路径"] = 模型路径
        表单布局.addRow("模型路径:", self._创建带说明的控件(模型路径, "训练后模型的保存位置"))
        
        # 预训练模型路径
        预训练路径 = QLineEdit()
        预训练路径.setPlaceholderText("模型/预训练模型/test")
        预训练路径.setFixedWidth(布局常量.表单控件最大宽度)
        预训练路径.setFixedHeight(布局常量.表单控件高度)
        self._配置控件["预训练模型路径"] = 预训练路径
        表单布局.addRow("预训练模型:", self._创建带说明的控件(预训练路径, "预训练模型的加载路径"))
        
        return self._创建标签页内容(表单布局)
    
    def _创建训练参数标签页(self) -> QWidget:
        """创建训练参数配置标签页 (Requirements 5.3)"""
        表单布局 = QFormLayout()
        表单布局.setSpacing(布局常量.表单行间距)
        表单布局.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        # 训练设置分组
        分组标题1 = QLabel("训练设置")
        分组标题1.setStyleSheet(f"""
            font-size: {布局常量.卡片标题字号}px;
            font-weight: bold;
            color: {颜色.标题};
            padding: 8px 0 4px 0;
        """)
        表单布局.addRow(分组标题1)
        
        # 学习率 - 使用滑块和输入框组合
        学习率容器 = QWidget()
        学习率布局 = QHBoxLayout(学习率容器)
        学习率布局.setContentsMargins(0, 0, 0, 0)
        学习率布局.setSpacing(8)
        
        学习率滑块 = QSlider(Qt.Horizontal)
        学习率滑块.setRange(1, 100)  # 0.0001 到 0.01
        学习率滑块.setValue(10)  # 默认 0.001
        学习率滑块.setFixedWidth(100)
        
        学习率输入 = QDoubleSpinBox()
        学习率输入.setRange(0.0001, 0.01)
        学习率输入.setDecimals(4)
        学习率输入.setSingleStep(0.0001)
        学习率输入.setFixedWidth(80)
        学习率输入.setFixedHeight(布局常量.表单控件高度)
        
        # 滑块和输入框联动
        def 滑块更新输入(值):
            学习率输入.setValue(值 / 10000)
        
        def 输入更新滑块(值):
            学习率滑块.setValue(int(值 * 10000))
        
        学习率滑块.valueChanged.connect(滑块更新输入)
        学习率输入.valueChanged.connect(输入更新滑块)
        
        学习率布局.addWidget(学习率滑块)
        学习率布局.addWidget(学习率输入)
        
        self._配置控件["学习率"] = 学习率输入
        self._配置控件["学习率_滑块"] = 学习率滑块
        表单布局.addRow("学习率:", self._创建带说明的控件(学习率容器, "模型训练的学习率，建议范围 0.0001-0.01"))
        
        # 训练轮数
        训练轮数 = QSpinBox()
        训练轮数.setRange(1, 100)
        训练轮数.setSuffix(" 轮")
        训练轮数.setFixedWidth(布局常量.表单控件最小宽度 + 40)
        训练轮数.setFixedHeight(布局常量.表单控件高度)
        self._配置控件["训练轮数"] = 训练轮数
        表单布局.addRow("训练轮数:", self._创建带说明的控件(训练轮数, "模型训练的总轮数"))
        
        # 数据设置分组
        分组标题2 = QLabel("数据设置")
        分组标题2.setStyleSheet(f"""
            font-size: {布局常量.卡片标题字号}px;
            font-weight: bold;
            color: {颜色.标题};
            padding: 12px 0 4px 0;
        """)
        表单布局.addRow(分组标题2)
        
        # 每文件样本数
        样本数 = QSpinBox()
        样本数.setRange(100, 5000)
        样本数.setSingleStep(100)
        样本数.setSuffix(" 个")
        样本数.setFixedWidth(布局常量.表单控件最小宽度 + 40)
        样本数.setFixedHeight(布局常量.表单控件高度)
        self._配置控件["每文件样本数"] = 样本数
        表单布局.addRow("每文件样本数:", self._创建带说明的控件(样本数, "每个数据文件保存的样本数量"))
        
        # 数据保存路径
        数据路径 = QLineEdit()
        数据路径.setPlaceholderText("数据/")
        数据路径.setFixedWidth(布局常量.表单控件最大宽度)
        数据路径.setFixedHeight(布局常量.表单控件高度)
        self._配置控件["数据保存路径"] = 数据路径
        表单布局.addRow("数据路径:", self._创建带说明的控件(数据路径, "训练数据的保存目录"))
        
        # 运动检测阈值
        运动阈值 = QSpinBox()
        运动阈值.setRange(100, 5000)
        运动阈值.setSingleStep(100)
        运动阈值.setFixedWidth(布局常量.表单控件最小宽度 + 40)
        运动阈值.setFixedHeight(布局常量.表单控件高度)
        self._配置控件["运动检测阈值"] = 运动阈值
        表单布局.addRow("运动检测阈值:", self._创建带说明的控件(运动阈值, "低于此值认为角色卡住"))
        
        return self._创建标签页内容(表单布局)

    def _创建增强模块标签页(self) -> QWidget:
        """创建增强模块配置标签页 (Requirements 5.3)"""
        表单布局 = QFormLayout()
        表单布局.setSpacing(布局常量.表单行间距)
        表单布局.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        # YOLO检测器分组
        分组标题1 = QLabel("YOLO检测器")
        分组标题1.setStyleSheet(f"""
            font-size: {布局常量.卡片标题字号}px;
            font-weight: bold;
            color: {颜色.标题};
            padding: 8px 0 4px 0;
        """)
        表单布局.addRow(分组标题1)
        
        # YOLO检测器开关
        yolo启用 = QCheckBox("启用YOLO目标检测")
        yolo启用.setStyleSheet("QCheckBox { spacing: 8px; }")
        self._配置控件["YOLO启用"] = yolo启用
        表单布局.addRow("", self._创建带说明的控件(yolo启用, "启用后可检测游戏中的怪物、NPC等实体"))
        
        # YOLO置信度阈值
        yolo置信度容器 = QWidget()
        yolo置信度布局 = QHBoxLayout(yolo置信度容器)
        yolo置信度布局.setContentsMargins(0, 0, 0, 0)
        yolo置信度布局.setSpacing(8)
        
        yolo置信度滑块 = QSlider(Qt.Horizontal)
        yolo置信度滑块.setRange(10, 90)
        yolo置信度滑块.setValue(50)
        yolo置信度滑块.setFixedWidth(100)
        
        yolo置信度标签 = QLabel("0.50")
        yolo置信度标签.setFixedWidth(40)
        
        def 更新置信度标签(值):
            yolo置信度标签.setText(f"{值/100:.2f}")
        
        yolo置信度滑块.valueChanged.connect(更新置信度标签)
        
        yolo置信度布局.addWidget(yolo置信度滑块)
        yolo置信度布局.addWidget(yolo置信度标签)
        
        self._配置控件["YOLO置信度"] = yolo置信度滑块
        表单布局.addRow("YOLO置信度:", self._创建带说明的控件(yolo置信度容器, "检测置信度阈值，越高越严格"))
        
        # YOLO检测间隔
        yolo间隔 = QSpinBox()
        yolo间隔.setRange(1, 10)
        yolo间隔.setSuffix(" 帧")
        yolo间隔.setFixedWidth(布局常量.表单控件最小宽度 + 40)
        yolo间隔.setFixedHeight(布局常量.表单控件高度)
        self._配置控件["YOLO检测间隔"] = yolo间隔
        表单布局.addRow("检测间隔:", self._创建带说明的控件(yolo间隔, "每N帧执行一次检测，值越大性能越好"))
        
        # 状态识别器分组
        分组标题2 = QLabel("状态识别器")
        分组标题2.setStyleSheet(f"""
            font-size: {布局常量.卡片标题字号}px;
            font-weight: bold;
            color: {颜色.标题};
            padding: 12px 0 4px 0;
        """)
        表单布局.addRow(分组标题2)
        
        # 状态识别器开关
        状态识别启用 = QCheckBox("启用状态识别")
        状态识别启用.setStyleSheet("QCheckBox { spacing: 8px; }")
        self._配置控件["状态识别启用"] = 状态识别启用
        表单布局.addRow("", self._创建带说明的控件(状态识别启用, "启用后可识别当前游戏状态（战斗/对话等）"))
        
        # 决策引擎分组
        分组标题3 = QLabel("决策引擎")
        分组标题3.setStyleSheet(f"""
            font-size: {布局常量.卡片标题字号}px;
            font-weight: bold;
            color: {颜色.标题};
            padding: 12px 0 4px 0;
        """)
        表单布局.addRow(分组标题3)
        
        # 决策引擎开关
        决策引擎启用 = QCheckBox("启用决策引擎")
        决策引擎启用.setStyleSheet("QCheckBox { spacing: 8px; }")
        self._配置控件["决策引擎启用"] = 决策引擎启用
        表单布局.addRow("", self._创建带说明的控件(决策引擎启用, "启用后使用规则+模型混合决策"))
        
        # 决策策略选择
        决策策略 = QComboBox()
        决策策略.addItems(["规则优先", "模型优先", "混合加权"])
        决策策略.setFixedWidth(布局常量.表单控件最小宽度 + 40)
        决策策略.setFixedHeight(布局常量.表单控件高度)
        self._配置控件["决策策略"] = 决策策略
        表单布局.addRow("决策策略:", self._创建带说明的控件(决策策略, "选择决策引擎的工作模式"))
        
        # 规则权重
        规则权重容器 = QWidget()
        规则权重布局 = QHBoxLayout(规则权重容器)
        规则权重布局.setContentsMargins(0, 0, 0, 0)
        规则权重布局.setSpacing(8)
        
        规则权重滑块 = QSlider(Qt.Horizontal)
        规则权重滑块.setRange(0, 100)
        规则权重滑块.setValue(60)
        规则权重滑块.setFixedWidth(100)
        
        规则权重标签 = QLabel("0.60")
        规则权重标签.setFixedWidth(40)
        
        def 更新规则权重标签(值):
            规则权重标签.setText(f"{值/100:.2f}")
        
        规则权重滑块.valueChanged.connect(更新规则权重标签)
        
        规则权重布局.addWidget(规则权重滑块)
        规则权重布局.addWidget(规则权重标签)
        
        self._配置控件["规则权重"] = 规则权重滑块
        表单布局.addRow("规则权重:", self._创建带说明的控件(规则权重容器, "混合模式下规则的权重（模型权重=1-规则权重）"))
        
        # 性能配置分组
        分组标题4 = QLabel("性能配置")
        分组标题4.setStyleSheet(f"""
            font-size: {布局常量.卡片标题字号}px;
            font-weight: bold;
            color: {颜色.标题};
            padding: 12px 0 4px 0;
        """)
        表单布局.addRow(分组标题4)
        
        # 性能配置 - 自动降级
        自动降级 = QCheckBox("启用自动性能降级")
        自动降级.setStyleSheet("QCheckBox { spacing: 8px; }")
        self._配置控件["自动降级"] = 自动降级
        表单布局.addRow("", self._创建带说明的控件(自动降级, "帧率过低时自动降低检测频率"))
        
        # 帧率阈值
        帧率阈值 = QSpinBox()
        帧率阈值.setRange(5, 60)
        帧率阈值.setSuffix(" FPS")
        帧率阈值.setFixedWidth(布局常量.表单控件最小宽度 + 40)
        帧率阈值.setFixedHeight(布局常量.表单控件高度)
        self._配置控件["帧率阈值"] = 帧率阈值
        表单布局.addRow("帧率阈值:", self._创建带说明的控件(帧率阈值, "低于此帧率进入低性能模式"))
        
        return self._创建标签页内容(表单布局)
    
    def _创建底部按钮区域(self) -> QWidget:
        """创建底部固定的保存和重置按钮区域 (Requirements 5.5)"""
        按钮容器 = QWidget()
        按钮布局 = QHBoxLayout(按钮容器)
        按钮布局.setContentsMargins(0, 布局常量.卡片间距, 0, 0)
        按钮布局.setSpacing(布局常量.按钮间距)
        
        按钮布局.addStretch()
        
        # 重置按钮
        self._重置按钮 = QPushButton("重置默认")
        self._重置按钮.setFixedSize(100, 布局常量.按钮高度)
        self._重置按钮.setStyleSheet(f"""
            QPushButton {{
                background-color: {颜色.卡片背景};
                color: {颜色.文字};
                border: 1px solid {颜色.边框};
                border-radius: {布局常量.按钮圆角}px;
                font-size: {布局常量.按钮文字字号}px;
                padding: 0 {布局常量.按钮水平内边距}px;
            }}
            QPushButton:hover {{
                background-color: {颜色.悬停背景};
            }}
        """)
        self._重置按钮.clicked.connect(self._重置配置)
        按钮布局.addWidget(self._重置按钮)
        
        # 保存按钮
        self._保存按钮 = QPushButton("保存配置")
        self._保存按钮.setFixedSize(100, 布局常量.按钮高度)
        self._保存按钮.setStyleSheet(f"""
            QPushButton {{
                background-color: {颜色.主色};
                color: white;
                border: none;
                border-radius: {布局常量.按钮圆角}px;
                font-size: {布局常量.按钮文字字号}px;
                font-weight: bold;
                padding: 0 {布局常量.按钮水平内边距}px;
            }}
            QPushButton:hover {{
                background-color: #2563EB;
            }}
        """)
        self._保存按钮.clicked.connect(self._保存配置)
        按钮布局.addWidget(self._保存按钮)
        
        return 按钮容器
    
    def _创建带说明的控件(self, 控件: QWidget, 说明: str) -> QWidget:
        """创建带说明文字的控件容器"""
        容器 = QWidget()
        布局 = QVBoxLayout(容器)
        布局.setContentsMargins(0, 0, 0, 0)
        布局.setSpacing(2)
        
        布局.addWidget(控件)
        
        说明标签 = QLabel(说明)
        说明标签.setStyleSheet(f"""
            color: {颜色.次要文字};
            font-size: {布局常量.次要文字字号}px;
        """)
        说明标签.setWordWrap(True)
        布局.addWidget(说明标签)
        
        return 容器
    
    # ==================== 档案管理方法 ====================
    
    def _刷新档案列表(self):
        """刷新档案列表"""
        if not self._配置管理器:
            return
        
        # 保存当前选择
        当前选择 = self._档案选择.currentText()
        
        # 阻止信号触发
        self._档案选择.blockSignals(True)
        
        # 清空并重新加载
        self._档案选择.clear()
        档案列表 = self._配置管理器.list_profiles()
        
        if 档案列表:
            self._档案选择.addItems(档案列表)
            
            # 恢复选择或选择当前档案
            当前档案 = self._配置管理器.get_current_profile()
            if 当前档案 and 当前档案.name in 档案列表:
                self._档案选择.setCurrentText(当前档案.name)
            elif 当前选择 in 档案列表:
                self._档案选择.setCurrentText(当前选择)
        else:
            self._档案选择.addItem("(无档案)")
        
        # 恢复信号
        self._档案选择.blockSignals(False)
    
    def _切换档案(self, 档案名称: str):
        """切换配置档案 (需求 6.1)"""
        if not self._配置管理器 or not 档案名称 or 档案名称 == "(无档案)":
            return
        
        try:
            self._配置管理器.switch_profile(档案名称)
            self.档案已切换.emit(档案名称)
        except FileNotFoundError:
            提示对话框.警告提示(self, "切换失败", f"档案 '{档案名称}' 不存在")
        except Exception as e:
            提示对话框.警告提示(self, "切换失败", f"切换档案时发生错误:\n{str(e)}")
    
    def _新建档案(self):
        """新建配置档案"""
        if not self._配置管理器:
            提示对话框.警告提示(self, "错误", "配置管理器未初始化")
            return
        
        # 获取档案名称
        档案名称, 确认 = QInputDialog.getText(
            self, "新建档案", "请输入档案名称:",
            QLineEdit.Normal, ""
        )
        
        if not 确认 or not 档案名称.strip():
            return
        
        # 获取游戏名称
        游戏名称, 确认 = QInputDialog.getText(
            self, "新建档案", "请输入游戏名称:",
            QLineEdit.Normal, "未命名游戏"
        )
        
        if not 确认:
            return
        
        游戏名称 = 游戏名称.strip() or "未命名游戏"
        
        try:
            # 创建新档案
            新档案 = self._配置管理器.create_profile(档案名称.strip(), 游戏名称)
            # 保存档案
            self._配置管理器.save_profile(新档案)
            # 刷新列表
            self._刷新档案列表()
            # 选择新档案
            self._档案选择.setCurrentText(档案名称.strip())
            
            提示对话框.信息提示(self, "成功", f"档案 '{档案名称}' 创建成功！")
        except FileExistsError:
            提示对话框.警告提示(self, "创建失败", f"档案 '{档案名称}' 已存在")
        except Exception as e:
            提示对话框.警告提示(self, "创建失败", f"创建档案时发生错误:\n{str(e)}")
    
    def _导入档案(self):
        """导入配置档案 (需求 6.5)"""
        if not self._配置管理器:
            提示对话框.警告提示(self, "错误", "配置管理器未初始化")
            return
        
        # 选择文件
        文件路径, _ = QFileDialog.getOpenFileName(
            self, "导入配置档案", "",
            "JSON文件 (*.json);;所有文件 (*.*)"
        )
        
        if not 文件路径:
            return
        
        # 询问是否使用新名称
        新名称, 确认 = QInputDialog.getText(
            self, "导入档案", 
            "请输入导入后的档案名称 (留空使用原名称):",
            QLineEdit.Normal, ""
        )
        
        if not 确认:
            return
        
        try:
            # 导入档案
            导入的档案 = self._配置管理器.import_profile(
                文件路径, 
                新名称.strip() if 新名称.strip() else None
            )
            # 保存档案
            self._配置管理器.save_profile(导入的档案)
            # 刷新列表
            self._刷新档案列表()
            # 选择导入的档案
            self._档案选择.setCurrentText(导入的档案.name)
            
            提示对话框.信息提示(self, "成功", f"档案 '{导入的档案.name}' 导入成功！")
        except FileExistsError:
            提示对话框.警告提示(self, "导入失败", "同名档案已存在，请使用其他名称")
        except ValueError as e:
            提示对话框.警告提示(self, "导入失败", f"文件格式无效:\n{str(e)}")
        except Exception as e:
            提示对话框.警告提示(self, "导入失败", f"导入档案时发生错误:\n{str(e)}")
    
    def _导出档案(self):
        """导出配置档案 (需求 6.3)"""
        if not self._配置管理器:
            提示对话框.警告提示(self, "错误", "配置管理器未初始化")
            return
        
        当前档案名 = self._档案选择.currentText()
        if not 当前档案名 or 当前档案名 == "(无档案)":
            提示对话框.警告提示(self, "导出失败", "请先选择要导出的档案")
            return
        
        # 选择保存路径
        文件路径, _ = QFileDialog.getSaveFileName(
            self, "导出配置档案", f"{当前档案名}.json",
            "JSON文件 (*.json);;所有文件 (*.*)"
        )
        
        if not 文件路径:
            return
        
        try:
            self._配置管理器.export_profile(当前档案名, 文件路径)
            提示对话框.信息提示(self, "成功", f"档案已导出到:\n{文件路径}")
        except FileNotFoundError:
            提示对话框.警告提示(self, "导出失败", f"档案 '{当前档案名}' 不存在")
        except Exception as e:
            提示对话框.警告提示(self, "导出失败", f"导出档案时发生错误:\n{str(e)}")
    
    def _删除档案(self):
        """删除配置档案"""
        if not self._配置管理器:
            提示对话框.警告提示(self, "错误", "配置管理器未初始化")
            return
        
        当前档案名 = self._档案选择.currentText()
        if not 当前档案名 or 当前档案名 == "(无档案)":
            提示对话框.警告提示(self, "删除失败", "请先选择要删除的档案")
            return
        
        # 确认删除
        回复 = 确认对话框.询问(
            self, "确认删除",
            f"确定要删除档案 '{当前档案名}' 吗？\n此操作不可撤销！",
            "删除", "取消"
        )
        
        if 回复 != 确认对话框.确认:
            return
        
        try:
            self._配置管理器.delete_profile(当前档案名)
            self._刷新档案列表()
            提示对话框.信息提示(self, "成功", f"档案 '{当前档案名}' 已删除")
        except FileNotFoundError:
            提示对话框.警告提示(self, "删除失败", f"档案 '{当前档案名}' 不存在")
        except Exception as e:
            提示对话框.警告提示(self, "删除失败", f"删除档案时发生错误:\n{str(e)}")

    # ==================== 配置加载和保存方法 ====================
    
    def _加载配置(self):
        """从配置文件加载配置值到控件"""
        try:
            # 导入配置模块
            from 配置 import 设置
            from 配置 import 增强设置
            
            # 游戏窗口配置
            窗口区域 = getattr(设置, '游戏窗口区域', (0, 40, 1920, 1120))
            self._配置控件["游戏窗口_左"].setValue(窗口区域[0])
            self._配置控件["游戏窗口_上"].setValue(窗口区域[1])
            self._配置控件["游戏窗口_右"].setValue(窗口区域[2])
            self._配置控件["游戏窗口_下"].setValue(窗口区域[3])
            
            self._配置控件["游戏宽度"].setValue(getattr(设置, '游戏宽度', 1920))
            self._配置控件["游戏高度"].setValue(getattr(设置, '游戏高度', 1080))
            
            # 模型配置
            self._配置控件["模型输入宽度"].setValue(getattr(设置, '模型输入宽度', 480))
            self._配置控件["模型输入高度"].setValue(getattr(设置, '模型输入高度', 270))
            self._配置控件["模型保存路径"].setText(getattr(设置, '模型保存路径', '模型/游戏AI'))
            self._配置控件["预训练模型路径"].setText(getattr(设置, '预训练模型路径', '模型/预训练模型/test'))
            
            # 训练配置
            学习率值 = getattr(设置, '学习率', 0.001)
            self._配置控件["学习率"].setValue(学习率值)
            self._配置控件["学习率_滑块"].setValue(int(学习率值 * 10000))
            
            self._配置控件["训练轮数"].setValue(getattr(设置, '训练轮数', 10))
            self._配置控件["每文件样本数"].setValue(getattr(设置, '每文件样本数', 500))
            self._配置控件["数据保存路径"].setText(getattr(设置, '数据保存路径', '数据/'))
            self._配置控件["运动检测阈值"].setValue(getattr(设置, '运动检测阈值', 800))
            
            # 增强模块配置
            yolo配置 = getattr(增强设置, 'YOLO配置', {})
            self._配置控件["YOLO启用"].setChecked(yolo配置.get('启用', True))
            self._配置控件["YOLO置信度"].setValue(int(yolo配置.get('置信度阈值', 0.5) * 100))
            self._配置控件["YOLO检测间隔"].setValue(yolo配置.get('检测间隔', 3))
            
            状态配置 = getattr(增强设置, '状态识别配置', {})
            self._配置控件["状态识别启用"].setChecked(状态配置.get('启用', True))
            
            决策配置 = getattr(增强设置, '决策引擎配置', {})
            self._配置控件["决策引擎启用"].setChecked(决策配置.get('启用', True))
            
            # 决策策略
            策略映射 = {
                增强设置.决策策略枚举.规则优先: 0,
                增强设置.决策策略枚举.模型优先: 1,
                增强设置.决策策略枚举.混合加权: 2,
            }
            当前策略 = 决策配置.get('策略', 增强设置.决策策略枚举.混合加权)
            self._配置控件["决策策略"].setCurrentIndex(策略映射.get(当前策略, 2))
            
            self._配置控件["规则权重"].setValue(int(决策配置.get('规则权重', 0.6) * 100))
            
            性能配置 = getattr(增强设置, '性能配置', {})
            self._配置控件["自动降级"].setChecked(性能配置.get('自动降级', True))
            self._配置控件["帧率阈值"].setValue(性能配置.get('帧率阈值', 15))
            
            # 保存原始值用于重置
            self._保存原始值()
            
        except Exception as e:
            print(f"加载配置失败: {e}")
            # 使用默认值
            self._使用默认值()
    
    def _使用默认值(self):
        """使用默认配置值"""
        # 游戏窗口默认值
        self._配置控件["游戏窗口_左"].setValue(0)
        self._配置控件["游戏窗口_上"].setValue(40)
        self._配置控件["游戏窗口_右"].setValue(1920)
        self._配置控件["游戏窗口_下"].setValue(1120)
        self._配置控件["游戏宽度"].setValue(1920)
        self._配置控件["游戏高度"].setValue(1080)
        
        # 模型默认值
        self._配置控件["模型输入宽度"].setValue(480)
        self._配置控件["模型输入高度"].setValue(270)
        self._配置控件["模型保存路径"].setText("模型/游戏AI")
        self._配置控件["预训练模型路径"].setText("模型/预训练模型/test")
        
        # 训练默认值
        self._配置控件["学习率"].setValue(0.001)
        self._配置控件["学习率_滑块"].setValue(10)
        self._配置控件["训练轮数"].setValue(10)
        self._配置控件["每文件样本数"].setValue(500)
        self._配置控件["数据保存路径"].setText("数据/")
        self._配置控件["运动检测阈值"].setValue(800)
        
        # 增强模块默认值
        self._配置控件["YOLO启用"].setChecked(True)
        self._配置控件["YOLO置信度"].setValue(50)
        self._配置控件["YOLO检测间隔"].setValue(3)
        self._配置控件["状态识别启用"].setChecked(True)
        self._配置控件["决策引擎启用"].setChecked(True)
        self._配置控件["决策策略"].setCurrentIndex(2)
        self._配置控件["规则权重"].setValue(60)
        self._配置控件["自动降级"].setChecked(True)
        self._配置控件["帧率阈值"].setValue(15)
        
        self._保存原始值()
    
    def _保存原始值(self):
        """保存当前控件值作为原始值"""
        self._原始值 = self._获取当前配置()
    
    def _获取当前配置(self) -> dict:
        """获取当前所有配置值"""
        return {
            # 游戏窗口
            "游戏窗口_左": self._配置控件["游戏窗口_左"].value(),
            "游戏窗口_上": self._配置控件["游戏窗口_上"].value(),
            "游戏窗口_右": self._配置控件["游戏窗口_右"].value(),
            "游戏窗口_下": self._配置控件["游戏窗口_下"].value(),
            "游戏宽度": self._配置控件["游戏宽度"].value(),
            "游戏高度": self._配置控件["游戏高度"].value(),
            # 模型
            "模型输入宽度": self._配置控件["模型输入宽度"].value(),
            "模型输入高度": self._配置控件["模型输入高度"].value(),
            "模型保存路径": self._配置控件["模型保存路径"].text(),
            "预训练模型路径": self._配置控件["预训练模型路径"].text(),
            # 训练
            "学习率": self._配置控件["学习率"].value(),
            "训练轮数": self._配置控件["训练轮数"].value(),
            "每文件样本数": self._配置控件["每文件样本数"].value(),
            "数据保存路径": self._配置控件["数据保存路径"].text(),
            "运动检测阈值": self._配置控件["运动检测阈值"].value(),
            # 增强模块
            "YOLO启用": self._配置控件["YOLO启用"].isChecked(),
            "YOLO置信度": self._配置控件["YOLO置信度"].value() / 100,
            "YOLO检测间隔": self._配置控件["YOLO检测间隔"].value(),
            "状态识别启用": self._配置控件["状态识别启用"].isChecked(),
            "决策引擎启用": self._配置控件["决策引擎启用"].isChecked(),
            "决策策略": self._配置控件["决策策略"].currentIndex(),
            "规则权重": self._配置控件["规则权重"].value() / 100,
            "自动降级": self._配置控件["自动降级"].isChecked(),
            "帧率阈值": self._配置控件["帧率阈值"].value(),
        }

    def _验证配置(self) -> tuple:
        """
        验证当前配置值的有效性
        
        返回:
            (是否有效, 错误信息列表)
        """
        错误列表 = []
        配置 = self._获取当前配置()
        
        # 验证游戏窗口区域
        if 配置["游戏窗口_左"] >= 配置["游戏窗口_右"]:
            错误列表.append("游戏窗口: 左边界必须小于右边界")
        
        if 配置["游戏窗口_上"] >= 配置["游戏窗口_下"]:
            错误列表.append("游戏窗口: 上边界必须小于下边界")
        
        # 验证分辨率
        窗口宽度 = 配置["游戏窗口_右"] - 配置["游戏窗口_左"]
        窗口高度 = 配置["游戏窗口_下"] - 配置["游戏窗口_上"]
        
        if 窗口宽度 < 640:
            错误列表.append("游戏窗口: 宽度不能小于640像素")
        
        if 窗口高度 < 480:
            错误列表.append("游戏窗口: 高度不能小于480像素")
        
        # 验证模型输入尺寸
        if 配置["模型输入宽度"] > 配置["游戏宽度"]:
            错误列表.append("模型输入宽度不能大于游戏宽度")
        
        if 配置["模型输入高度"] > 配置["游戏高度"]:
            错误列表.append("模型输入高度不能大于游戏高度")
        
        # 验证路径
        if not 配置["模型保存路径"].strip():
            错误列表.append("模型保存路径不能为空")
        
        if not 配置["数据保存路径"].strip():
            错误列表.append("数据保存路径不能为空")
        
        # 验证学习率
        if 配置["学习率"] <= 0:
            错误列表.append("学习率必须大于0")
        
        # 验证权重
        if not (0 <= 配置["规则权重"] <= 1):
            错误列表.append("规则权重必须在0到1之间")
        
        return len(错误列表) == 0, 错误列表
    
    def _保存配置(self):
        """保存配置到文件"""
        # 先验证配置
        有效, 错误列表 = self._验证配置()
        
        if not 有效:
            错误信息 = "\n".join(f"• {错误}" for 错误 in 错误列表)
            提示对话框.警告提示(
                self,
                "配置验证失败",
                f"以下配置项存在问题:\n\n{错误信息}"
            )
            return
        
        try:
            配置 = self._获取当前配置()
            
            # 生成设置.py内容
            设置内容 = self._生成设置文件内容(配置)
            
            # 写入设置.py
            with open("配置/设置.py", "w", encoding="utf-8") as f:
                f.write(设置内容)
            
            # 生成增强设置.py内容
            增强设置内容 = self._生成增强设置文件内容(配置)
            
            # 写入增强设置.py
            with open("配置/增强设置.py", "w", encoding="utf-8") as f:
                f.write(增强设置内容)
            
            # 更新原始值
            self._保存原始值()
            
            # 发送信号
            self.配置已保存.emit()
            
            提示对话框.信息提示(
                self,
                "保存成功",
                "配置已成功保存！\n\n部分配置可能需要重启程序后生效。"
            )
            
        except Exception as e:
            提示对话框.错误提示(
                self,
                "保存失败",
                f"保存配置时发生错误:\n\n{str(e)}"
            )
    
    def _重置配置(self):
        """重置配置到原始值"""
        回复 = 确认对话框.询问(
            self,
            "确认重置",
            "确定要重置所有配置到上次保存的状态吗？",
            "重置", "取消"
        )
        
        if 回复 == 确认对话框.确认:
            self._恢复原始值()
            self.配置已重置.emit()
    
    def _恢复原始值(self):
        """从原始值恢复控件状态"""
        if not self._原始值:
            return
        
        配置 = self._原始值
        
        # 游戏窗口
        self._配置控件["游戏窗口_左"].setValue(配置.get("游戏窗口_左", 0))
        self._配置控件["游戏窗口_上"].setValue(配置.get("游戏窗口_上", 40))
        self._配置控件["游戏窗口_右"].setValue(配置.get("游戏窗口_右", 1920))
        self._配置控件["游戏窗口_下"].setValue(配置.get("游戏窗口_下", 1120))
        self._配置控件["游戏宽度"].setValue(配置.get("游戏宽度", 1920))
        self._配置控件["游戏高度"].setValue(配置.get("游戏高度", 1080))
        
        # 模型
        self._配置控件["模型输入宽度"].setValue(配置.get("模型输入宽度", 480))
        self._配置控件["模型输入高度"].setValue(配置.get("模型输入高度", 270))
        self._配置控件["模型保存路径"].setText(配置.get("模型保存路径", "模型/游戏AI"))
        self._配置控件["预训练模型路径"].setText(配置.get("预训练模型路径", "模型/预训练模型/test"))
        
        # 训练
        学习率 = 配置.get("学习率", 0.001)
        self._配置控件["学习率"].setValue(学习率)
        self._配置控件["学习率_滑块"].setValue(int(学习率 * 10000))
        self._配置控件["训练轮数"].setValue(配置.get("训练轮数", 10))
        self._配置控件["每文件样本数"].setValue(配置.get("每文件样本数", 500))
        self._配置控件["数据保存路径"].setText(配置.get("数据保存路径", "数据/"))
        self._配置控件["运动检测阈值"].setValue(配置.get("运动检测阈值", 800))
        
        # 增强模块
        self._配置控件["YOLO启用"].setChecked(配置.get("YOLO启用", True))
        self._配置控件["YOLO置信度"].setValue(int(配置.get("YOLO置信度", 0.5) * 100))
        self._配置控件["YOLO检测间隔"].setValue(配置.get("YOLO检测间隔", 3))
        self._配置控件["状态识别启用"].setChecked(配置.get("状态识别启用", True))
        self._配置控件["决策引擎启用"].setChecked(配置.get("决策引擎启用", True))
        self._配置控件["决策策略"].setCurrentIndex(配置.get("决策策略", 2))
        self._配置控件["规则权重"].setValue(int(配置.get("规则权重", 0.6) * 100))
        self._配置控件["自动降级"].setChecked(配置.get("自动降级", True))
        self._配置控件["帧率阈值"].setValue(配置.get("帧率阈值", 15))

    # ==================== 配置文件生成方法 ====================
    
    def _生成设置文件内容(self, 配置: dict) -> str:
        """生成设置.py文件内容"""
        # 读取原始文件获取动作定义等不变的部分
        try:
            with open("配置/设置.py", "r", encoding="utf-8") as f:
                原始内容 = f.read()
        except:
            原始内容 = ""
        
        # 提取动作定义部分（从 "# ==================== 动作定义" 开始到文件末尾）
        动作定义开始 = 原始内容.find("# ==================== 动作定义")
        if 动作定义开始 > 0:
            动作定义部分 = 原始内容[动作定义开始:]
        else:
            动作定义部分 = ""
        
        内容 = f'''"""
全局配置设置
"""

# ==================== 游戏窗口设置 ====================
# 游戏窗口区域 (左, 上, 右, 下)
游戏窗口区域 = ({配置["游戏窗口_左"]}, {配置["游戏窗口_上"]}, {配置["游戏窗口_右"]}, {配置["游戏窗口_下"]})

# 游戏分辨率
游戏宽度 = {配置["游戏宽度"]}
游戏高度 = {配置["游戏高度"]}

# ==================== 模型设置 ====================
# 输入图像尺寸 (缩放后)
模型输入宽度 = {配置["模型输入宽度"]}
模型输入高度 = {配置["模型输入高度"]}

# 学习率
学习率 = {配置["学习率"]}

# 训练轮数
训练轮数 = {配置["训练轮数"]}

# 模型保存路径
模型保存路径 = "{配置["模型保存路径"]}"

# 预训练模型路径 (原项目的模型)
预训练模型路径 = "{配置["预训练模型路径"]}"

# ==================== 数据收集设置 ====================
# 每个文件保存的样本数
每文件样本数 = {配置["每文件样本数"]}

# 数据保存路径
数据保存路径 = "{配置["数据保存路径"]}"

# ==================== 运动检测设置 ====================
# 运动检测阈值 (低于此值认为卡住)
运动检测阈值 = {配置["运动检测阈值"]}

# 运动检测日志长度
运动日志长度 = 25

'''
        
        # 添加动作定义部分
        if 动作定义部分:
            内容 += 动作定义部分
        else:
            # 如果没有找到原始动作定义，使用默认的
            内容 += self._获取默认动作定义()
        
        return 内容
    
    def _获取默认动作定义(self) -> str:
        """获取默认的动作定义内容"""
        return '''# ==================== 动作定义 ====================
# 完整动作列表 (32个动作)
动作定义 = {
    # 移动动作 (0-8)
    0: {"名称": "前进", "按键": "W", "类型": "移动"},
    1: {"名称": "后退", "按键": "S", "类型": "移动"},
    2: {"名称": "左移", "按键": "A", "类型": "移动"},
    3: {"名称": "右移", "按键": "D", "类型": "移动"},
    4: {"名称": "前进+左移", "按键": "W+A", "类型": "移动"},
    5: {"名称": "前进+右移", "按键": "W+D", "类型": "移动"},
    6: {"名称": "后退+左移", "按键": "S+A", "类型": "移动"},
    7: {"名称": "后退+右移", "按键": "S+D", "类型": "移动"},
    8: {"名称": "无操作", "按键": "无", "类型": "移动"},
    
    # 技能动作 (9-18)
    9: {"名称": "技能1", "按键": "1", "类型": "技能"},
    10: {"名称": "技能2", "按键": "2", "类型": "技能"},
    11: {"名称": "技能3", "按键": "3", "类型": "技能"},
    12: {"名称": "技能4", "按键": "4", "类型": "技能"},
    13: {"名称": "技能5", "按键": "5", "类型": "技能"},
    14: {"名称": "技能6", "按键": "6", "类型": "技能"},
    15: {"名称": "技能Q", "按键": "Q", "类型": "技能"},
    16: {"名称": "技能E", "按键": "E", "类型": "技能"},
    17: {"名称": "技能R", "按键": "R", "类型": "技能"},
    18: {"名称": "技能F", "按键": "F", "类型": "技能"},
    
    # 特殊动作 (19-23)
    19: {"名称": "跳跃/闪避", "按键": "空格", "类型": "特殊"},
    20: {"名称": "切换目标", "按键": "Tab", "类型": "特殊"},
    21: {"名称": "交互", "按键": "F", "类型": "特殊"},
    
    # 鼠标动作 (22-24)
    22: {"名称": "鼠标左键", "按键": "鼠标左", "类型": "鼠标"},
    23: {"名称": "鼠标右键", "按键": "鼠标右", "类型": "鼠标"},
    24: {"名称": "鼠标中键", "按键": "鼠标中", "类型": "鼠标"},
    
    # Shift组合技能 (25-28)
    25: {"名称": "Shift+1", "按键": "Shift+1", "类型": "组合"},
    26: {"名称": "Shift+2", "按键": "Shift+2", "类型": "组合"},
    27: {"名称": "Shift+Q", "按键": "Shift+Q", "类型": "组合"},
    28: {"名称": "Shift+E", "按键": "Shift+E", "类型": "组合"},
    
    # Ctrl组合技能 (29-31)
    29: {"名称": "Ctrl+1", "按键": "Ctrl+1", "类型": "组合"},
    30: {"名称": "Ctrl+2", "按键": "Ctrl+2", "类型": "组合"},
    31: {"名称": "Ctrl+Q", "按键": "Ctrl+Q", "类型": "组合"},
}

# 总动作数
总动作数 = len(动作定义)

# ==================== 训练模式设置 ====================
class 训练模式:
    """训练模式配置"""
    
    # 主线任务模式 - 侧重移动和交互
    主线任务 = {
        "名称": "主线任务练级",
        "描述": "学习做主线任务的操作习惯",
        "启用动作": list(range(9)) + [21, 22, 23],
        "动作权重": [
            4.0, 0.5, 0.5, 0.5, 2.0, 2.0, 0.5, 0.5, 0.2,
            0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1,
            0.5, 0.3, 1.0,
            1.5, 1.5, 0.1,
            0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1,
        ],
    }
    
    # 自动战斗模式 - 侧重技能和走位
    自动战斗 = {
        "名称": "自动战斗",
        "描述": "学习战斗技能释放和走位",
        "启用动作": list(range(32)),
        "动作权重": [
            2.0, 0.5, 1.0, 1.0, 1.5, 1.5, 0.5, 0.5, 0.1,
            2.0, 2.0, 2.0, 2.0, 1.5, 1.5, 2.0, 2.0, 1.5, 1.5,
            2.0, 1.5, 1.0,
            2.5, 2.0, 0.5,
            1.5, 1.5, 1.5, 1.5, 1.0, 1.0, 1.0,
        ],
    }

# ==================== 按键扫描码 ====================
按键码 = {
    "W": 0x11, "A": 0x1E, "S": 0x1F, "D": 0x20,
    "Q": 0x10, "E": 0x12, "R": 0x13, "F": 0x21,
    "1": 0x02, "2": 0x03, "3": 0x04, "4": 0x05,
    "5": 0x06, "6": 0x07, "7": 0x08, "8": 0x09,
    "9": 0x0A, "0": 0x0B,
    "空格": 0x39, "Tab": 0x0F,
    "Shift": 0x2A, "Ctrl": 0x1D, "Alt": 0x38,
}
'''

    def _生成增强设置文件内容(self, 配置: dict) -> str:
        """生成增强设置.py文件内容"""
        # 决策策略映射
        策略名称 = ["规则优先", "模型优先", "混合加权"][配置["决策策略"]]
        策略枚举 = f"决策策略枚举.{策略名称}"
        
        内容 = f'''"""
增强模块配置设置
定义YOLO检测器、状态识别器、决策引擎的配置项
"""

from enum import Enum

# ==================== 实体类型枚举 ====================
class 实体类型枚举(Enum):
    """游戏中可识别的实体类型"""
    怪物 = "monster"
    NPC = "npc"
    玩家 = "player"
    物品 = "item"
    技能特效 = "skill_effect"
    未知 = "unknown"


# ==================== 游戏状态枚举 ====================
class 游戏状态枚举(Enum):
    """游戏状态枚举"""
    战斗 = "combat"
    对话 = "dialogue"
    菜单 = "menu"
    移动 = "moving"
    拾取 = "looting"
    采集 = "gathering"
    死亡 = "dead"
    加载 = "loading"
    空闲 = "idle"
    未知 = "unknown"


# ==================== YOLO检测器设置 ====================
YOLO配置 = {{
    "模型路径": "模型/yolo/game_detector.pt",
    "置信度阈值": {配置["YOLO置信度"]},
    "NMS阈值": 0.4,
    "输入尺寸": (640, 640),
    "启用": {配置["YOLO启用"]},
    "检测间隔": {配置["YOLO检测间隔"]},
}}

# 实体类型映射 (YOLO类别ID -> 实体类型)
实体类型映射 = {{
    0: 实体类型枚举.怪物,
    1: 实体类型枚举.NPC,
    2: 实体类型枚举.玩家,
    3: 实体类型枚举.物品,
    4: 实体类型枚举.技能特效,
}}


# ==================== 状态识别器设置 ====================
状态识别配置 = {{
    "历史长度": 10,
    "置信度累积系数": 0.1,
    "UI检测启用": True,
    "启用": {配置["状态识别启用"]},
}}

# UI元素模板路径
UI模板路径 = {{
    "对话框": "资源/ui/dialogue_box.png",
    "菜单": "资源/ui/menu.png",
    "血条": "资源/ui/health_bar.png",
    "死亡界面": "资源/ui/death_screen.png",
    "加载界面": "资源/ui/loading.png",
}}

# 状态判定阈值
状态判定阈值 = {{
    "战斗_敌人距离": 200,
    "战斗_敌人数量": 1,
    "拾取_物品距离": 100,
}}


# ==================== 决策引擎设置 ====================
class 决策策略枚举(Enum):
    """决策策略类型"""
    规则优先 = "rule_first"
    模型优先 = "model_first"
    混合加权 = "weighted_mix"


决策引擎配置 = {{
    "策略": {策略枚举},
    "规则权重": {配置["规则权重"]},
    "模型权重": {1 - 配置["规则权重"]:.2f},
    "启用日志": True,
    "日志长度": 100,
    "启用": {配置["决策引擎启用"]},
}}

# 状态-动作权重映射
状态动作权重 = {{
    游戏状态枚举.战斗: {{
        "移动": 1.5,
        "技能": 2.5,
        "特殊": 2.0,
        "鼠标": 2.0,
        "组合": 1.5,
    }},
    游戏状态枚举.对话: {{
        "移动": 0.1,
        "技能": 0.0,
        "特殊": 0.5,
        "鼠标": 2.5,
        "组合": 0.0,
    }},
    游戏状态枚举.菜单: {{
        "移动": 0.0,
        "技能": 0.0,
        "特殊": 0.3,
        "鼠标": 3.0,
        "组合": 0.0,
    }},
    游戏状态枚举.移动: {{
        "移动": 3.0,
        "技能": 0.2,
        "特殊": 0.5,
        "鼠标": 1.0,
        "组合": 0.1,
    }},
    游戏状态枚举.拾取: {{
        "移动": 1.0,
        "技能": 0.0,
        "特殊": 1.0,
        "鼠标": 2.0,
        "组合": 0.0,
    }},
    游戏状态枚举.采集: {{
        "移动": 0.1,
        "技能": 0.0,
        "特殊": 0.3,
        "鼠标": 1.5,
        "组合": 0.0,
    }},
    游戏状态枚举.死亡: {{
        "移动": 0.0,
        "技能": 0.0,
        "特殊": 0.5,
        "鼠标": 2.0,
        "组合": 0.0,
    }},
    游戏状态枚举.加载: {{
        "移动": 0.0,
        "技能": 0.0,
        "特殊": 0.0,
        "鼠标": 0.0,
        "组合": 0.0,
    }},
    游戏状态枚举.空闲: {{
        "移动": 1.0,
        "技能": 0.5,
        "特殊": 1.0,
        "鼠标": 1.5,
        "组合": 0.5,
    }},
    游戏状态枚举.未知: {{
        "移动": 1.0,
        "技能": 0.5,
        "特殊": 0.5,
        "鼠标": 1.0,
        "组合": 0.5,
    }},
}}

# 动作冷却时间 (秒)
动作冷却时间 = {{
    9: 1.0,
    10: 1.5,
    11: 2.0,
    12: 2.5,
    13: 3.0,
    14: 3.0,
    15: 1.0,
    16: 1.0,
    17: 2.0,
    18: 2.0,
    19: 0.5,
    20: 1.0,
}}

# 紧急规则配置
紧急规则配置 = {{
    "低血量阈值": 0.3,
    "被围攻阈值": 3,
    "紧急动作": 19,
}}


# ==================== 模块启用配置 ====================
模块启用配置 = {{
    "YOLO检测器": {配置["YOLO启用"]},
    "状态识别器": {配置["状态识别启用"]},
    "决策引擎": {配置["决策引擎启用"]},
}}

# ==================== 性能配置 ====================
性能配置 = {{
    "低性能模式检测间隔": 5,
    "帧率阈值": {配置["帧率阈值"]},
    "自动降级": {配置["自动降级"]},
}}
'''
        return 内容
