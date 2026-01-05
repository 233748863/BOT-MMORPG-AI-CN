# -*- coding: utf-8 -*-
"""
首页组件 (状态仪表盘)

显示系统状态概览、快捷操作按钮和使用提示。
采用仪表盘风格布局：
- 顶部：系统状态卡片（横跨整个宽度）
- 中部：快捷操作按钮（水平排列）
- 底部：提示卡片 + 快捷键卡片

符合设计规范:
- Requirements 6.1: 仪表盘风格布局
- Requirements 6.2: 系统状态卡片位于顶部，横跨整个宽度
- Requirements 6.3: 快捷操作按钮以2x2网格形式排列在中部
- Requirements 6.4: 每个快捷按钮包含图标、标题和简短描述
- Requirements 6.5: 提示信息位于页面底部
"""

import os
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QGridLayout, QSizePolicy
)
from PySide6.QtCore import Signal, Qt, QTimer
from PySide6.QtGui import QFont

from 界面.样式.主题 import 颜色, 获取状态颜色
from 界面.样式.布局常量 import 布局常量
from 界面.组件.通用组件 import Card


class 状态卡片(Card):
    """
    系统状态卡片组件
    
    显示模型状态、GPU状态、数据文件和上次训练信息。
    横跨整个宽度 (Requirements 6.2)
    """
    
    def __init__(self, parent=None):
        super().__init__("系统状态", "", parent)
        self._初始化状态显示()
    
    def _初始化状态显示(self) -> None:
        """初始化状态显示区域"""
        # 状态网格
        状态网格 = QGridLayout()
        状态网格.setSpacing(布局常量.卡片间距)
        状态网格.setContentsMargins(0, 4, 0, 0)
        
        # 模型状态
        self._模型状态标签 = self._创建状态项("模型状态:", "检测中...", 状态网格, 0, 0)
        
        # GPU状态
        self._GPU状态标签 = self._创建状态项("GPU:", "检测中...", 状态网格, 0, 1)
        
        # 数据文件
        self._数据文件标签 = self._创建状态项("数据文件:", "检测中...", 状态网格, 1, 0)
        
        # 上次训练
        self._上次训练标签 = self._创建状态项("上次训练:", "检测中...", 状态网格, 1, 1)
        
        self.添加布局(状态网格)
    
    def _创建状态项(self, 标题: str, 初始值: str, 网格: QGridLayout, 行: int, 列: int) -> QLabel:
        """创建状态项"""
        容器 = QWidget()
        容器布局 = QHBoxLayout(容器)
        容器布局.setContentsMargins(0, 0, 0, 0)
        容器布局.setSpacing(8)
        
        标题标签 = QLabel(标题)
        标题标签.setStyleSheet(f"color: {颜色.次要文字}; font-size: {布局常量.正文字号}px;")
        容器布局.addWidget(标题标签)
        
        值标签 = QLabel(初始值)
        值标签.setStyleSheet(f"color: {颜色.文字}; font-size: {布局常量.正文字号}px; font-weight: 500;")
        容器布局.addWidget(值标签)
        容器布局.addStretch()
        
        网格.addWidget(容器, 行, 列)
        return 值标签
    
    def 更新模型状态(self, 已加载: bool, 路径: str = "") -> None:
        """更新模型状态显示"""
        if 已加载:
            self._模型状态标签.setText("[OK] 已加载")
            self._模型状态标签.setStyleSheet(f"color: {颜色.成功}; font-size: {布局常量.正文字号}px; font-weight: 500;")
        else:
            self._模型状态标签.setText("[X] 未加载")
            self._模型状态标签.setStyleSheet(f"color: {颜色.错误}; font-size: {布局常量.正文字号}px; font-weight: 500;")
    
    def 更新GPU状态(self, 可用: bool, 设备名: str = "") -> None:
        """更新GPU状态显示"""
        if 可用:
            显示文本 = f"[OK] 可用"
            if 设备名:
                显示文本 = f"[OK] {设备名}"
            self._GPU状态标签.setText(显示文本)
            self._GPU状态标签.setStyleSheet(f"color: {颜色.成功}; font-size: {布局常量.正文字号}px; font-weight: 500;")
        else:
            self._GPU状态标签.setText("[!] 仅CPU")
            self._GPU状态标签.setStyleSheet(f"color: {颜色.警告}; font-size: {布局常量.正文字号}px; font-weight: 500;")
    
    def 更新数据文件状态(self, 文件数: int, 样本数: int) -> None:
        """更新数据文件状态显示"""
        if 文件数 > 0:
            self._数据文件标签.setText(f"{文件数}个文件 ({样本数}样本)")
            self._数据文件标签.setStyleSheet(f"color: {颜色.成功}; font-size: {布局常量.正文字号}px; font-weight: 500;")
        else:
            self._数据文件标签.setText("无数据")
            self._数据文件标签.setStyleSheet(f"color: {颜色.警告}; font-size: {布局常量.正文字号}px; font-weight: 500;")
    
    def 更新训练状态(self, 上次训练时间: Optional[datetime], 损失值: Optional[float] = None) -> None:
        """更新上次训练状态显示"""
        if 上次训练时间:
            时间字符串 = 上次训练时间.strftime("%Y-%m-%d %H:%M")
            if 损失值 is not None:
                self._上次训练标签.setText(f"{时间字符串} (损失: {损失值:.4f})")
            else:
                self._上次训练标签.setText(时间字符串)
            self._上次训练标签.setStyleSheet(f"color: {颜色.文字}; font-size: {布局常量.正文字号}px; font-weight: 500;")
        else:
            self._上次训练标签.setText("暂无记录")
            self._上次训练标签.setStyleSheet(f"color: {颜色.次要文字}; font-size: {布局常量.正文字号}px; font-weight: 500;")


class 快捷按钮(QPushButton):
    """
    快捷操作按钮组件
    
    每个按钮包含图标、标题和描述 (Requirements 6.4)
    尺寸: 120-140px宽，80-90px高
    """
    
    def __init__(self, 图标: str, 标题: str, 描述: str, parent=None):
        super().__init__(parent)
        self._图标 = 图标
        self._标题 = 标题
        self._描述 = 描述
        self._初始化样式()
    
    def _初始化样式(self) -> None:
        """初始化按钮样式
        
        按钮文字居中显示 (Requirements 1.1, 1.2, 1.3):
        - 使用单行文本，避免多行对齐问题
        - QPushButton 默认居中显示文本
        - 描述信息通过 ToolTip 显示
        """
        # 设置尺寸在规定范围内 (120-140px宽，80-90px高)
        self.setFixedSize(130, 85)
        self.setCursor(Qt.PointingHandCursor)
        
        # 设置按钮文本：只显示标题（单行文本，确保居中）
        self.setText(self._标题)
        self.setToolTip(f"{self._标题}: {self._描述}")
        
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {颜色.卡片背景};
                border: {布局常量.卡片边框宽度}px solid {颜色.边框};
                border-radius: {布局常量.卡片圆角}px;
                font-size: {布局常量.正文字号}px;
                font-weight: 500;
                color: {颜色.标题};
                padding: 8px;
            }}
            QPushButton:hover {{
                background-color: {颜色.选中背景};
                border-color: {颜色.主色};
            }}
            QPushButton:pressed {{
                background-color: {颜色.悬停背景};
            }}
        """)
    
    @property
    def 图标(self) -> str:
        """获取按钮图标"""
        return self._图标
    
    @property
    def 标题(self) -> str:
        """获取按钮标题"""
        return self._标题
    
    @property
    def 描述(self) -> str:
        """获取按钮描述"""
        return self._描述
    
    def 获取宽度(self) -> int:
        """获取按钮宽度"""
        return self.width()
    
    def 获取高度(self) -> int:
        """获取按钮高度"""
        return self.height()


class 提示卡片(Card):
    """
    使用提示卡片组件
    
    位于页面底部 (Requirements 6.5)
    """
    
    def __init__(self, parent=None):
        super().__init__("", "", parent)
        self._初始化提示显示()
    
    def _初始化提示显示(self) -> None:
        """初始化提示显示"""
        # 使用特殊背景色
        self.setStyleSheet(f"""
            QFrame#Card {{
                background-color: {颜色.选中背景};
                border-radius: {布局常量.卡片圆角}px;
                border: {布局常量.卡片边框宽度}px solid {颜色.边框};
            }}
        """)
        
        提示容器 = QWidget()
        提示布局 = QHBoxLayout(提示容器)
        提示布局.setContentsMargins(0, 0, 0, 0)
        提示布局.setSpacing(8)
        
        图标 = QLabel("[提示]")
        图标.setStyleSheet(f"font-size: {布局常量.页面标题字号}px;")
        提示布局.addWidget(图标)
        
        self._提示文本 = QLabel("提示: 首次使用请先收集训练数据")
        self._提示文本.setStyleSheet(f"color: {颜色.主色}; font-size: {布局常量.正文字号}px;")
        self._提示文本.setWordWrap(True)
        提示布局.addWidget(self._提示文本, 1)
        
        self.添加内容(提示容器)
    
    def 设置提示(self, 文本: str) -> None:
        """设置提示文本"""
        self._提示文本.setText(f"提示: {文本}")


class 快捷键卡片(Card):
    """
    快捷键提示卡片组件
    
    位于页面底部 (Requirements 6.5)
    """
    
    def __init__(self, parent=None):
        super().__init__("快捷键", "", parent)
        self._初始化快捷键显示()
    
    def _初始化快捷键显示(self) -> None:
        """初始化快捷键显示"""
        快捷键内容 = QLabel(
            "T - 暂停/继续  |  ESC - 停止  |  Ctrl+S - 保存配置  |  F1 - 帮助"
        )
        快捷键内容.setStyleSheet(f"color: {颜色.次要文字}; font-size: {布局常量.次要文字字号}px;")
        self.添加内容(快捷键内容)


class 首页(QWidget):
    """
    首页组件 (状态仪表盘)
    
    采用仪表盘风格布局 (Requirements 6.1):
    - 顶部：系统状态卡片（横跨整个宽度）(Requirements 6.2)
    - 中部：快捷操作按钮（水平排列）(Requirements 6.3)
    - 底部：提示卡片 + 快捷键卡片 (Requirements 6.5)
    """
    
    # 信号定义
    快速运行点击 = Signal()
    开始录制点击 = Signal()
    训练模型点击 = Signal()
    数据管理点击 = Signal()
    
    def __init__(self, parent=None):
        """初始化首页"""
        super().__init__(parent)
        self._初始化界面()
        
        # 延迟检测系统状态（不包括GPU）
        QTimer.singleShot(100, self._检测系统状态)
        
        # 后台线程检测GPU（避免阻塞UI）
        QTimer.singleShot(500, self._后台检测GPU)
    
    def _初始化界面(self) -> None:
        """
        初始化界面布局
        
        仪表盘风格布局:
        - 顶部：页面标题 + 系统状态卡片
        - 中部：快捷操作按钮
        - 底部：提示卡片 + 快捷键卡片
        """
        主布局 = QVBoxLayout(self)
        主布局.setContentsMargins(
            布局常量.内容区外边距,
            布局常量.内容区外边距,
            布局常量.内容区外边距,
            布局常量.内容区外边距
        )
        主布局.setSpacing(布局常量.卡片间距)
        
        # ==================== 顶部：页面标题 ====================
        标题 = QLabel("MMORPG游戏AI助手")
        标题.setStyleSheet(f"""
            font-size: {布局常量.页面标题字号}px;
            font-weight: bold;
            color: {颜色.标题};
        """)
        主布局.addWidget(标题)
        
        # ==================== 顶部：系统状态卡片（横跨整个宽度）====================
        self._状态卡片 = 状态卡片()
        主布局.addWidget(self._状态卡片)
        
        # ==================== 中部：快捷操作区域 ====================
        快捷操作标题 = QLabel("快捷操作")
        快捷操作标题.setStyleSheet(f"""
            font-size: {布局常量.卡片标题字号}px;
            font-weight: 500;
            color: {颜色.标题};
            margin-top: 4px;
        """)
        主布局.addWidget(快捷操作标题)
        
        # 快捷按钮容器（水平排列）
        按钮容器 = QWidget()
        按钮布局 = QHBoxLayout(按钮容器)
        按钮布局.setContentsMargins(0, 0, 0, 0)
        按钮布局.setSpacing(布局常量.卡片间距)
        
        # 创建4个快捷按钮 (Requirements 6.4: 每个按钮包含图标、标题和描述)
        self._快速运行按钮 = 快捷按钮("", "快速运行", "启动AI")
        self._快速运行按钮.clicked.connect(self.快速运行点击.emit)
        按钮布局.addWidget(self._快速运行按钮)
        
        self._开始录制按钮 = 快捷按钮("", "开始录制", "收集数据")
        self._开始录制按钮.clicked.connect(self.开始录制点击.emit)
        按钮布局.addWidget(self._开始录制按钮)
        
        self._训练模型按钮 = 快捷按钮("", "训练模型", "训练AI")
        self._训练模型按钮.clicked.connect(self.训练模型点击.emit)
        按钮布局.addWidget(self._训练模型按钮)
        
        self._数据管理按钮 = 快捷按钮("", "数据管理", "管理数据")
        self._数据管理按钮.clicked.connect(self.数据管理点击.emit)
        按钮布局.addWidget(self._数据管理按钮)
        
        按钮布局.addStretch()
        主布局.addWidget(按钮容器)
        
        # ==================== 底部：提示卡片 + 快捷键卡片 ====================
        # 使用提示卡片
        self._提示卡片 = 提示卡片()
        主布局.addWidget(self._提示卡片)
        
        # 快捷键卡片
        self._快捷键卡片 = 快捷键卡片()
        主布局.addWidget(self._快捷键卡片)
        
        # 添加弹性空间
        主布局.addStretch()
    
    def _检测系统状态(self) -> None:
        """检测并更新系统状态"""
        状态 = 检测系统状态()
        
        # 更新模型状态
        self._状态卡片.更新模型状态(状态["模型已加载"], 状态.get("模型路径", ""))
        
        # 更新GPU状态
        self._状态卡片.更新GPU状态(状态["GPU可用"], 状态.get("GPU设备名", ""))
        
        # 更新数据文件状态
        self._状态卡片.更新数据文件状态(状态["数据文件数"], 状态["样本总数"])
        
        # 更新训练状态
        self._状态卡片.更新训练状态(状态.get("上次训练时间"), 状态.get("上次损失值"))
        
        # 更新提示
        self._更新提示(状态)
    
    def _更新提示(self, 状态: Dict[str, Any]) -> None:
        """根据系统状态更新提示"""
        if 状态["数据文件数"] == 0:
            self._提示卡片.设置提示("首次使用请先收集训练数据")
        elif not 状态["模型已加载"]:
            self._提示卡片.设置提示("已有训练数据，可以开始训练模型了")
        elif not 状态["GPU可用"]:
            self._提示卡片.设置提示("未检测到GPU，将使用CPU运行（速度较慢）")
        else:
            self._提示卡片.设置提示("系统就绪，可以启动AI机器人了")
    
    def 刷新状态(self) -> None:
        """手动刷新系统状态"""
        self._检测系统状态()
        self._后台检测GPU()
    
    def _后台检测GPU(self) -> None:
        """在后台线程中检测GPU，避免阻塞UI"""
        import threading
        
        def 检测任务():
            可用, 设备名 = _检测GPU_后台()
            # 使用 QTimer 在主线程更新 UI
            QTimer.singleShot(0, lambda: self._更新GPU状态(可用, 设备名))
        
        线程 = threading.Thread(target=检测任务, daemon=True)
        线程.start()
    
    def _更新GPU状态(self, 可用: bool, 设备名: str) -> None:
        """更新GPU状态显示"""
        self._状态卡片.更新GPU状态(可用, 设备名)
        
        # 更新提示
        状态 = 检测系统状态()
        状态["GPU可用"] = 可用
        状态["GPU设备名"] = 设备名
        self._更新提示(状态)
    
    def 获取状态卡片(self) -> 状态卡片:
        """获取状态卡片组件"""
        return self._状态卡片
    
    def 获取快捷按钮列表(self) -> list:
        """获取所有快捷按钮列表"""
        return [
            self._快速运行按钮,
            self._开始录制按钮,
            self._训练模型按钮,
            self._数据管理按钮
        ]



def 检测系统状态() -> Dict[str, Any]:
    """
    检测系统状态
    
    返回:
        包含系统状态信息的字典
    """
    状态 = {
        "模型已加载": False,
        "模型路径": "",
        "GPU可用": False,
        "GPU设备名": "",
        "数据文件数": 0,
        "样本总数": 0,
        "上次训练时间": None,
        "上次损失值": None,
    }
    
    # 检测模型文件
    状态["模型已加载"], 状态["模型路径"] = _检测模型文件()
    
    # 检测GPU
    状态["GPU可用"], 状态["GPU设备名"] = _检测GPU()
    
    # 统计数据文件
    状态["数据文件数"], 状态["样本总数"] = _统计数据文件()
    
    # 检测上次训练信息
    状态["上次训练时间"], 状态["上次损失值"] = _检测训练记录()
    
    return 状态


def _检测模型文件() -> tuple:
    """
    检测模型文件是否存在
    
    返回:
        (是否存在, 模型路径)
    """
    try:
        from 配置.设置 import 模型保存路径, 预训练模型路径
        
        # 检查训练后的模型
        模型目录 = Path(模型保存路径)
        if 模型目录.exists():
            # 检查是否有模型文件
            模型文件 = list(模型目录.glob("*.index")) + list(模型目录.glob("*.h5")) + list(模型目录.glob("*.pt"))
            if 模型文件:
                return True, str(模型目录)
        
        # 检查预训练模型
        预训练目录 = Path(预训练模型路径).parent
        if 预训练目录.exists():
            索引文件 = Path(f"{预训练模型路径}.index")
            if 索引文件.exists():
                return True, str(预训练目录)
        
        return False, ""
    except Exception:
        return False, ""


def _检测GPU() -> tuple:
    """
    检测GPU是否可用
    
    注意：此函数会延迟导入 TensorFlow/PyTorch，避免启动时阻塞
    
    返回:
        (是否可用, 设备名称)
    """
    # 先返回未知状态，实际检测在后台进行
    return False, "检测中..."


def _检测GPU_后台() -> tuple:
    """
    后台检测GPU（实际执行导入和检测）
    
    返回:
        (是否可用, 设备名称)
    """
    try:
        import tensorflow as tf
        gpus = tf.config.list_physical_devices('GPU')
        if gpus:
            # 获取第一个GPU的名称
            设备名 = gpus[0].name.split('/')[-1] if gpus else ""
            return True, 设备名
        return False, ""
    except Exception:
        pass
    
    # 尝试PyTorch
    try:
        import torch
        if torch.cuda.is_available():
            设备名 = torch.cuda.get_device_name(0)
            return True, 设备名
        return False, ""
    except Exception:
        pass
    
    return False, ""


def _统计数据文件() -> tuple:
    """
    统计数据文件数量和样本数
    
    返回:
        (文件数, 样本总数)
    """
    try:
        from 配置.设置 import 数据保存路径, 每文件样本数
        import numpy as np
        
        数据目录 = Path(数据保存路径)
        if not 数据目录.exists():
            return 0, 0
        
        # 查找所有npz文件
        数据文件列表 = list(数据目录.glob("*.npz"))
        文件数 = len(数据文件列表)
        
        if 文件数 == 0:
            return 0, 0
        
        # 统计样本数
        样本总数 = 0
        for 文件路径 in 数据文件列表:
            try:
                数据 = np.load(str(文件路径), allow_pickle=True)
                if 'images' in 数据:
                    样本总数 += len(数据['images'])
                elif 'frames' in 数据:
                    样本总数 += len(数据['frames'])
                else:
                    # 估算样本数
                    样本总数 += 每文件样本数
            except Exception:
                样本总数 += 每文件样本数
        
        return 文件数, 样本总数
    except Exception:
        return 0, 0


def _检测训练记录() -> tuple:
    """
    检测上次训练记录
    
    返回:
        (上次训练时间, 上次损失值)
    """
    try:
        from 配置.设置 import 模型保存路径
        
        模型目录 = Path(模型保存路径)
        if not 模型目录.exists():
            return None, None
        
        # 查找最新的模型文件
        模型文件列表 = list(模型目录.glob("*.index")) + list(模型目录.glob("*.h5")) + list(模型目录.glob("*.pt"))
        
        if not 模型文件列表:
            return None, None
        
        # 获取最新文件的修改时间
        最新文件 = max(模型文件列表, key=lambda f: f.stat().st_mtime)
        修改时间 = datetime.fromtimestamp(最新文件.stat().st_mtime)
        
        # 尝试读取训练日志获取损失值
        日志文件 = 模型目录 / "training_log.txt"
        损失值 = None
        if 日志文件.exists():
            try:
                with open(日志文件, 'r', encoding='utf-8') as f:
                    行列表 = f.readlines()
                    if 行列表:
                        最后一行 = 行列表[-1]
                        # 尝试解析损失值
                        if "loss" in 最后一行.lower():
                            import re
                            匹配 = re.search(r'loss[:\s]+([0-9.]+)', 最后一行.lower())
                            if 匹配:
                                损失值 = float(匹配.group(1))
            except Exception:
                pass
        
        return 修改时间, 损失值
    except Exception:
        return None, None
