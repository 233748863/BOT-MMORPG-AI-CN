# -*- coding: utf-8 -*-
"""
主程序模块

包含应用程序的主窗口类，实现固定尺寸800x600窗口，
左侧导航栏 + 右侧内容区域布局，以及页面切换功能。

性能优化:
- 延迟加载: 页面按需创建，已创建的从缓存获取
- 异步初始化: 主窗口先显示基础框架，延迟初始化其他组件
- 状态更新节流: 避免过于频繁的UI更新
- 页面切换动画: 淡入淡出效果，时长200ms

布局规范:
- 窗口尺寸: 800x600 (固定)
- 导航栏宽度: 100px
- 内容区外边距: 16px
- 卡片间距: 12px
- 状态栏高度: 24px
"""

import time
from typing import Optional

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, 
    QVBoxLayout, QStackedWidget, QStatusBar, QLabel,
    QGraphicsOpacityEffect
)
from PySide6.QtCore import Signal, Slot, Qt, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QShortcut, QKeySequence

from 界面.样式.主题 import LIGHT_THEME_QSS, 颜色
from 界面.样式.布局常量 import 布局常量
from 界面.组件.导航栏 import NavigationBar
from 界面.组件.自定义标题栏 import 自定义标题栏
from 界面.组件.通知服务 import NotificationService
from 界面.组件.错误处理 import ErrorHandler, 获取错误处理器
from 界面.组件.通用组件 import 动画管理器, 页面切换管理器
from 界面.组件.性能优化 import (
    延迟加载页面管理器,
    异步初始化管理器,
    性能监控器,
    状态更新节流器
)
from 界面.页面.首页 import 首页
from 界面.页面.数据收集页 import 数据收集页
from 界面.页面.训练页 import 训练页
from 界面.页面.运行页 import 运行页
from 界面.配置界面 import 配置界面  # 使用完整配置界面替代简化配置页
from 界面.页面.数据管理页 import 数据管理页
from 界面.线程.数据收集线程 import 数据收集线程
from 界面.线程.训练线程 import 训练线程
from 界面.线程.运行线程 import 运行线程


class MainWindow(QMainWindow):
    """
    主窗口类
    
    实现固定尺寸800x600窗口，包含左侧导航栏和右侧内容区域，
    支持页面切换和全局快捷键。
    
    性能优化:
    - 延迟加载: 页面按需创建
    - 异步初始化: 先显示基础框架，延迟初始化其他组件
    - 页面切换动画: 淡入淡出效果
    - 状态更新节流: 避免过于频繁的UI更新
    
    布局规范:
    - 窗口尺寸: 800x600 (布局常量.窗口宽度 x 布局常量.窗口高度)
    - 导航栏宽度: 100px (布局常量.导航栏宽度)
    - 内容区外边距: 16px (布局常量.内容区外边距)
    - 状态栏高度: 24px (布局常量.状态栏高度)
    """
    
    # 信号定义
    页面切换信号 = Signal(str)
    通知信号 = Signal(str, str, str)  # 标题, 内容, 类型
    暂停继续信号 = Signal()
    停止信号 = Signal()
    
    def __init__(self):
        """初始化主窗口，设置固定尺寸800x600"""
        super().__init__()
        
        # 记录启动时间（用于统计总加载时间）
        self._启动时间 = time.time()
        
        # 设置无边框窗口
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        
        # 设置窗口属性，使用布局常量
        # 高度增加36px用于自定义标题栏
        self.setWindowTitle("🎮 MMORPG游戏AI助手")
        self.setFixedSize(布局常量.窗口宽度, 布局常量.窗口高度 + 36)
        
        # 应用样式
        self.setStyleSheet(LIGHT_THEME_QSS)
        
        # 页面映射
        self._页面映射 = {}
        self._当前页面 = "首页"
        self._上一页面 = None
        
        # 后台线程
        self._数据收集线程: Optional[数据收集线程] = None
        self._训练线程: Optional[训练线程] = None
        self._运行线程: Optional[运行线程] = None
        
        # 性能优化组件
        self._页面管理器 = 延迟加载页面管理器()
        self._异步初始化器 = 异步初始化管理器()
        self._性能监控器 = 性能监控器()
        self._状态更新节流器 = 状态更新节流器(布局常量.状态更新最小间隔)
        
        # 页面切换动画管理
        self._页面切换管理器 = 页面切换管理器()
        self._当前动画: Optional[QPropertyAnimation] = None
        self._启用页面切换动画 = True
        
        # 页面实例引用（用于信号连接）
        self._首页: Optional[首页] = None
        self._数据收集页: Optional[数据收集页] = None
        self._训练页: Optional[训练页] = None
        self._运行页: Optional[运行页] = None
        self._配置页: Optional[配置界面] = None  # 使用完整配置界面
        self._数据管理页: Optional[数据管理页] = None
        
        # 初始化错误处理服务
        self._初始化错误处理服务()
        
        # 初始化基础框架（同步，快速）
        self._初始化基础框架()
        
        # 延迟初始化其他组件（异步）
        QTimer.singleShot(0, self._延迟初始化)
    
    def _初始化错误处理服务(self) -> None:
        """初始化错误处理服务"""
        # 获取错误处理器单例
        self._错误处理器 = 获取错误处理器()
        
        # 安装全局异常处理
        self._错误处理器.安装全局异常处理()
        
        # 创建通知服务
        self._通知服务 = NotificationService(self)
        
        # 连接错误处理器信号到通知服务
        self._错误处理器.错误发生.connect(self._处理全局错误)
        self._错误处理器.警告发生.connect(self._处理全局警告)
        self._错误处理器.日志记录.connect(self._处理日志记录)
    
    def _处理全局错误(self, 标题: str, 内容: str, 详情: str) -> None:
        """
        处理全局错误
        
        参数:
            标题: 错误标题
            内容: 错误内容
            详情: 错误详情（堆栈跟踪）
        """
        self._通知服务.显示错误(标题, 内容, 详情 if 详情 else None)
        self._状态栏.showMessage(f"❌ {标题}: {内容}", 5000)
    
    def _处理全局警告(self, 标题: str, 内容: str) -> None:
        """
        处理全局警告
        
        参数:
            标题: 警告标题
            内容: 警告内容
        """
        self._通知服务.显示警告(标题, 内容)
        self._状态栏.showMessage(f"⚠️ {标题}: {内容}", 3000)
    
    def _处理日志记录(self, 级别: str, 消息: str) -> None:
        """
        处理日志记录
        
        参数:
            级别: 日志级别
            消息: 日志消息
        """
        # 如果训练页面存在且有日志查看器，添加日志
        if hasattr(self, '_训练页') and self._训练页:
            self._训练页.添加日志(消息, 级别)
    
    def _初始化基础框架(self) -> None:
        """
        初始化基础框架（同步，快速）
        
        只创建导航栏和页面堆栈的基本结构，
        页面内容延迟加载。
        
        布局规范:
        - 自定义标题栏高度: 36px
        - 导航栏宽度: 100px (布局常量.导航栏宽度)
        - 内容区域: 剩余宽度
        - 状态栏高度: 24px (布局常量.状态栏高度)
        """
        # 创建中央部件
        中央部件 = QWidget()
        self.setCentralWidget(中央部件)
        
        # 创建主垂直布局 (标题栏 + 内容区)
        主垂直布局 = QVBoxLayout(中央部件)
        主垂直布局.setContentsMargins(0, 0, 0, 0)
        主垂直布局.setSpacing(0)
        
        # 创建自定义标题栏
        self._标题栏 = 自定义标题栏(self)
        self._标题栏.配置请求.connect(self._打开配置界面)  # 连接配置按钮信号
        主垂直布局.addWidget(self._标题栏)
        
        # 创建内容区容器
        内容容器 = QWidget()
        内容布局 = QHBoxLayout(内容容器)
        内容布局.setContentsMargins(0, 0, 0, 0)
        内容布局.setSpacing(0)
        
        # 创建导航栏（使用布局常量中的宽度）
        self._导航栏 = NavigationBar()
        self._导航栏.导航项点击.connect(self.切换页面)
        内容布局.addWidget(self._导航栏)
        
        # 创建右侧内容区域
        右侧容器 = QWidget()
        右侧容器.setStyleSheet(f"background-color: {颜色.背景};")
        右侧布局 = QVBoxLayout(右侧容器)
        右侧布局.setContentsMargins(0, 0, 0, 0)
        右侧布局.setSpacing(0)
        
        # 创建页面堆栈
        self._页面堆栈 = QStackedWidget()
        右侧布局.addWidget(self._页面堆栈)
        
        内容布局.addWidget(右侧容器)
        主垂直布局.addWidget(内容容器)
        
        # 创建状态栏（使用布局常量中的高度）
        self._状态栏 = QStatusBar()
        self._状态栏.setFixedHeight(布局常量.状态栏高度)
        self.setStatusBar(self._状态栏)
        self._状态栏.showMessage("正在初始化...")
        
        # 添加占位页面
        self._添加占位页面()
    
    def _延迟初始化(self) -> None:
        """
        延迟初始化其他组件（异步）
        
        使用异步初始化管理器按优先级初始化各个组件
        """
        # 注册页面类到延迟加载管理器
        self._注册页面类()
        
        # 配置异步初始化任务
        self._异步初始化器.添加任务("首页", self._注册首页, 优先级=0, 延迟ms=0)
        self._异步初始化器.添加任务("数据收集页", self._注册数据收集页, 优先级=1, 延迟ms=10)
        self._异步初始化器.添加任务("训练页", self._注册训练页, 优先级=2, 延迟ms=20)
        self._异步初始化器.添加任务("配置页", self._注册配置页, 优先级=3, 延迟ms=30)
        self._异步初始化器.添加任务("数据管理页", self._注册数据管理页, 优先级=4, 延迟ms=40)
        self._异步初始化器.添加任务("运行页", self._注册运行页, 优先级=5, 延迟ms=50)
        self._异步初始化器.添加任务("快捷键", self._绑定快捷键, 优先级=6, 延迟ms=60)
        
        # 设置进度回调
        self._异步初始化器.设置进度回调(self._更新初始化进度)
        
        # 设置完成回调
        self._异步初始化器.设置完成回调(self._初始化完成)
        
        # 开始执行
        self._异步初始化器.开始执行()
    
    def _注册页面类(self) -> None:
        """注册页面类到延迟加载管理器"""
        self._页面管理器.注册页面类("首页", 首页)
        self._页面管理器.注册页面类("数据收集", 数据收集页)
        self._页面管理器.注册页面类("训练", 训练页)
        self._页面管理器.注册页面类("运行", 运行页)
        # 配置页面使用嵌入模式的配置界面，需要特殊处理
        self._页面管理器.注册页面类("数据管理", 数据管理页)
    
    def _更新初始化进度(self, 任务名称: str, 当前: int, 总数: int) -> None:
        """
        更新初始化进度
        
        参数:
            任务名称: 当前任务名称
            当前: 当前任务索引
            总数: 总任务数
        """
        self._状态栏.showMessage(f"正在初始化: {任务名称} ({当前}/{总数})")
    
    def _初始化完成(self) -> None:
        """
        初始化完成回调
        
        输出性能统计信息，包括:
        - 总加载时间（从启动到完全加载）
        - 页面加载时间
        - 总创建时间
        - 平均创建时间
        """
        self._状态栏.showMessage("就绪", 3000)
        
        # 计算总加载时间
        总加载时间 = (time.time() - self._启动时间) * 1000  # 转换为毫秒
        
        # 输出性能统计
        统计 = self._页面管理器.获取性能统计()
        print(f"[性能统计] 页面加载完成:")
        print(f"  - 总加载时间: {总加载时间:.2f}ms ({总加载时间/1000:.2f}秒)")
        print(f"  - 已注册页面数: {统计['已注册页面数']}")
        print(f"  - 已缓存页面数: {统计['已缓存页面数']}")
        print(f"  - 页面创建总时间: {统计['总创建时间_ms']:.2f}ms")
        print(f"  - 页面平均创建时间: {统计['平均创建时间_ms']:.2f}ms")
        
        # 输出各页面创建时间
        if 统计['各页面创建时间']:
            print(f"  - 各页面创建时间:")
            for 页面名称, 创建时间 in 统计['各页面创建时间'].items():
                状态 = "✓" if 创建时间 < 布局常量.页面切换最大时间 else "⚠"
                print(f"    {状态} {页面名称}: {创建时间:.2f}ms")
    
    def _添加占位页面(self) -> None:
        """添加占位页面，后续会被实际页面替换"""
        页面列表 = ["首页", "数据收集", "训练", "运行", "配置", "数据管理"]
        
        for 页面名称 in 页面列表:
            占位页面 = QWidget()
            占位布局 = QVBoxLayout(占位页面)
            占位布局.setAlignment(Qt.AlignCenter)
            
            标签 = QLabel(f"📄 {页面名称}")
            标签.setStyleSheet(f"""
                font-size: 24px;
                font-weight: bold;
                color: {颜色.标题};
            """)
            标签.setAlignment(Qt.AlignCenter)
            占位布局.addWidget(标签)
            
            说明标签 = QLabel("页面开发中...")
            说明标签.setStyleSheet(f"color: {颜色.次要文字}; font-size: 14px;")
            说明标签.setAlignment(Qt.AlignCenter)
            占位布局.addWidget(说明标签)
            
            self._页面映射[页面名称] = self._页面堆栈.addWidget(占位页面)
    
    def _注册首页(self) -> None:
        """注册首页组件"""
        # 通过页面管理器获取页面（会记录创建时间）
        self._首页 = self._页面管理器.获取页面("首页")
        
        # 连接首页快捷按钮信号
        self._首页.快速运行点击.connect(lambda: self.切换页面("运行"))
        self._首页.开始录制点击.connect(lambda: self.切换页面("数据收集"))
        self._首页.训练模型点击.connect(lambda: self.切换页面("训练"))
        self._首页.数据管理点击.connect(lambda: self.切换页面("数据管理"))
        
        # 注册到页面堆栈
        self.注册页面("首页", self._首页)
    
    def _注册数据收集页(self) -> None:
        """注册数据收集页面组件"""
        # 通过页面管理器获取页面（会记录创建时间）
        self._数据收集页 = self._页面管理器.获取页面("数据收集")
        
        # 连接数据收集页信号
        self._数据收集页.开始录制.connect(self._开始数据收集)
        self._数据收集页.暂停录制.connect(self._暂停数据收集)
        self._数据收集页.停止录制.connect(self._停止数据收集)
        
        # 注册到页面堆栈
        self.注册页面("数据收集", self._数据收集页)
    
    def _开始数据收集(self, 模式: str) -> None:
        """开始数据收集"""
        if self._数据收集线程 is not None and self._数据收集线程.isRunning():
            return
        
        # 创建并启动线程
        self._数据收集线程 = 数据收集线程()
        self._数据收集线程.设置训练模式(模式)
        
        # 连接信号
        self._数据收集线程.状态更新.connect(self._数据收集页.更新状态)
        self._数据收集线程.文件保存.connect(self._处理文件保存)
        self._数据收集线程.错误发生.connect(self._处理数据收集错误)
        self._数据收集线程.任务完成.connect(self._处理数据收集完成)
        
        self._数据收集线程.start()
        self._状态栏.showMessage(f"数据收集已开始 - 模式: {模式}")
    
    def _暂停数据收集(self) -> None:
        """暂停/继续数据收集"""
        if self._数据收集线程 is not None and self._数据收集线程.isRunning():
            self._数据收集线程.切换暂停()
            状态 = "已暂停" if self._数据收集线程.是否暂停() else "继续录制"
            self._状态栏.showMessage(f"数据收集{状态}")
    
    def _停止数据收集(self) -> None:
        """停止数据收集"""
        if self._数据收集线程 is not None and self._数据收集线程.isRunning():
            self._数据收集线程.请求停止()
            self._数据收集线程.wait(5000)  # 等待最多5秒
            self._状态栏.showMessage("数据收集已停止")
    
    def _处理文件保存(self, 文件路径: str, 样本数: int) -> None:
        """处理文件保存通知"""
        self._通知服务.显示成功("文件已保存", f"保存了 {样本数} 个样本到 {文件路径}")
    
    def _处理数据收集错误(self, 错误消息: str) -> None:
        """处理数据收集错误"""
        self._错误处理器.记录错误消息(错误消息, "数据收集", "错误", 显示通知=False)
        self._通知服务.显示错误("数据收集错误", 错误消息)
    
    def _处理数据收集完成(self, 成功: bool, 消息: str) -> None:
        """处理数据收集完成"""
        if 成功:
            self._通知服务.显示成功("数据收集完成", 消息)
        else:
            self._通知服务.显示错误("数据收集失败", 消息)
    
    def _注册训练页(self) -> None:
        """注册训练页面组件"""
        # 通过页面管理器获取页面（会记录创建时间）
        self._训练页 = self._页面管理器.获取页面("训练")
        
        # 连接训练页信号
        self._训练页.开始训练.connect(self._开始训练)
        self._训练页.停止训练.connect(self._停止训练)
        
        # 注册到页面堆栈
        self.注册页面("训练", self._训练页)
    
    def _开始训练(self, 模式: str) -> None:
        """开始模型训练"""
        if self._训练线程 is not None and self._训练线程.isRunning():
            return
        
        # 创建并启动线程
        self._训练线程 = 训练线程()
        self._训练线程.设置训练模式(模式)
        
        # 连接信号
        self._训练线程.轮次完成.connect(self._训练页.更新训练进度)
        self._训练线程.日志消息.connect(self._训练页.添加日志)
        self._训练线程.错误发生.connect(self._处理训练错误)
        self._训练线程.任务完成.connect(self._处理训练完成)
        
        self._训练线程.start()
        self._状态栏.showMessage(f"模型训练已开始 - 模式: {模式}")
    
    def _停止训练(self) -> None:
        """停止模型训练"""
        if self._训练线程 is not None and self._训练线程.isRunning():
            self._训练线程.请求停止()
            self._训练线程.wait(5000)  # 等待最多5秒
            self._状态栏.showMessage("模型训练已停止")
    
    def _处理训练错误(self, 错误消息: str) -> None:
        """处理训练错误"""
        self._错误处理器.记录错误消息(错误消息, "模型训练", "错误", 显示通知=False)
        self._通知服务.显示错误("训练错误", 错误消息)
    
    def _处理训练完成(self, 成功: bool, 消息: str) -> None:
        """处理训练完成"""
        self._训练页.训练完成(成功, 消息)
        if 成功:
            self._通知服务.显示成功("训练完成", 消息)
        else:
            self._通知服务.显示警告("训练停止", 消息)
    
    def _注册配置页(self) -> None:
        """注册配置页面组件（使用完整配置界面的嵌入模式）"""
        # 直接创建嵌入模式的配置界面实例
        self._配置页 = 配置界面(嵌入模式=True)
        
        # 连接配置页信号
        self._配置页.配置已保存.connect(self._处理配置保存_嵌入)
        self._配置页.配置已重置.connect(self._处理配置重置)
        
        # 注册到页面堆栈
        self.注册页面("配置", self._配置页)
    
    def _处理配置保存_嵌入(self, 配置: dict) -> None:
        """处理嵌入式配置界面的保存完成"""
        self._状态栏.showMessage("配置已保存", 3000)
        self._通知服务.显示成功("配置已保存", "配置已成功保存")
    
    def _处理配置保存(self) -> None:
        """处理配置保存完成"""
        self._状态栏.showMessage("配置已保存", 3000)
    
    def _处理配置重置(self) -> None:
        """处理配置重置完成"""
        self._状态栏.showMessage("配置已重置", 3000)
    
    def _打开配置界面(self) -> None:
        """打开配置界面
        
        需求: 1.1 - 配置界面入口
        
        修改: 现在切换到配置页面，而不是打开独立对话框
        """
        self.切换页面("配置")
    
    def _注册数据管理页(self) -> None:
        """注册数据管理页面组件"""
        # 通过页面管理器获取页面（会记录创建时间）
        self._数据管理页 = self._页面管理器.获取页面("数据管理")
        
        # 连接数据管理页信号
        self._数据管理页.刷新请求.connect(self._处理数据管理刷新)
        
        # 注册到页面堆栈
        self.注册页面("数据管理", self._数据管理页)
    
    def _处理数据管理刷新(self) -> None:
        """处理数据管理页刷新请求"""
        self._状态栏.showMessage("正在刷新数据文件列表...", 2000)
    
    def _注册运行页(self) -> None:
        """注册运行页面组件"""
        # 通过页面管理器获取页面（会记录创建时间）
        self._运行页 = self._页面管理器.获取页面("运行")
        
        # 连接运行页信号
        self._运行页.启动运行.connect(self._开始运行)
        self._运行页.暂停运行.connect(self._暂停运行)
        self._运行页.停止运行.connect(self._停止运行)
        
        # 注册到页面堆栈
        self.注册页面("运行", self._运行页)
    
    def _开始运行(self, 子模式: str, 运行模式: str, 是否增强: bool) -> None:
        """开始机器人运行"""
        if self._运行线程 is not None and self._运行线程.isRunning():
            return
        
        # 创建并启动线程
        self._运行线程 = 运行线程()
        self._运行线程.设置子模式(子模式)
        self._运行线程.设置增强模式(是否增强)
        
        # 连接信号
        self._运行线程.状态更新.connect(self._运行页.更新状态)
        self._运行线程.脱困提示.connect(self._运行页.显示脱困提示)
        self._运行线程.性能警告.connect(self._运行页.显示性能警告)
        self._运行线程.错误发生.connect(self._处理运行错误)
        self._运行线程.任务完成.connect(self._处理运行完成)
        
        self._运行线程.start()
        self._状态栏.showMessage(f"机器人运行已开始 - 模式: {运行模式} ({子模式})")
    
    def _暂停运行(self) -> None:
        """暂停/继续机器人运行"""
        if self._运行线程 is not None and self._运行线程.isRunning():
            self._运行线程.切换暂停()
            状态 = "已暂停" if self._运行线程.是否暂停() else "继续运行"
            self._状态栏.showMessage(f"机器人{状态}")
    
    def _停止运行(self) -> None:
        """停止机器人运行"""
        if self._运行线程 is not None and self._运行线程.isRunning():
            self._运行线程.请求停止()
            self._运行线程.wait(5000)  # 等待最多5秒
            self._状态栏.showMessage("机器人运行已停止")
    
    def _处理运行错误(self, 错误消息: str) -> None:
        """处理运行错误"""
        self._错误处理器.记录错误消息(错误消息, "机器人运行", "错误", 显示通知=False)
        self._通知服务.显示错误("运行错误", 错误消息)
    
    def _处理运行完成(self, 成功: bool, 消息: str) -> None:
        """处理运行完成"""
        if 成功:
            self._通知服务.显示成功("运行完成", 消息)
        else:
            self._通知服务.显示警告("运行停止", 消息)
    
    @Slot(str)
    def 切换页面(self, 页面名称: str) -> None:
        """
        切换到指定功能页面，带淡入淡出动画效果
        
        参数:
            页面名称: 要切换到的页面名称
            
        动画规范:
        - 动画时长: 200ms (布局常量.动画时长标准)
        - 动画类型: 淡入淡出
        - 缓动函数: OutCubic
        """
        if 页面名称 not in self._页面映射:
            return
        
        # 如果切换到同一页面，不执行动画
        if 页面名称 == self._当前页面:
            return
        
        # 记录页面切换开始时间（用于性能监控）
        切换开始时间 = time.time()
        
        # 获取旧页面和新页面
        旧页面索引 = self._页面映射.get(self._当前页面)
        新页面索引 = self._页面映射[页面名称]
        
        旧页面 = self._页面堆栈.widget(旧页面索引) if 旧页面索引 is not None else None
        新页面 = self._页面堆栈.widget(新页面索引)
        
        # 更新状态
        self._上一页面 = self._当前页面
        self._当前页面 = 页面名称
        
        # 同步更新导航栏选中项，保持导航切换一致性
        self._导航栏.blockSignals(True)  # 阻止信号避免循环触发
        self._导航栏.设置选中项(页面名称)
        self._导航栏.blockSignals(False)
        
        # 执行页面切换（带动画或不带动画）
        if self._启用页面切换动画 and 旧页面 and 新页面:
            self._执行页面切换动画(旧页面, 新页面, 新页面索引)
        else:
            # 直接切换，不带动画
            self._页面堆栈.setCurrentIndex(新页面索引)
        
        # 记录页面切换时间
        切换时间 = (time.time() - 切换开始时间) * 1000
        self._性能监控器.记录页面切换(页面名称, 切换时间)
        
        # 更新状态栏
        self._状态栏.showMessage(f"当前页面: {页面名称}")
        self.页面切换信号.emit(页面名称)
    
    def _执行页面切换动画(
        self, 
        旧页面: QWidget, 
        新页面: QWidget, 
        新页面索引: int
    ) -> None:
        """
        执行页面切换淡入淡出动画
        
        参数:
            旧页面: 要隐藏的页面
            新页面: 要显示的页面
            新页面索引: 新页面在堆栈中的索引
        """
        # 如果有正在进行的动画，先停止
        if self._当前动画 and self._当前动画.state() == QPropertyAnimation.Running:
            self._当前动画.stop()
        
        # 创建新页面的淡入动画
        效果 = QGraphicsOpacityEffect(新页面)
        新页面.setGraphicsEffect(效果)
        
        self._当前动画 = QPropertyAnimation(效果, b"opacity")
        self._当前动画.setDuration(布局常量.动画时长标准)
        self._当前动画.setStartValue(0.0)
        self._当前动画.setEndValue(1.0)
        self._当前动画.setEasingCurve(QEasingCurve.OutCubic)
        
        # 切换页面并开始动画
        self._页面堆栈.setCurrentIndex(新页面索引)
        self._当前动画.start()
    
    def 设置页面切换动画(self, 启用: bool) -> None:
        """
        设置是否启用页面切换动画
        
        参数:
            启用: True启用动画，False禁用动画
        """
        self._启用页面切换动画 = 启用
    
    def 获取页面切换动画状态(self) -> bool:
        """
        获取页面切换动画是否启用
        
        返回:
            是否启用页面切换动画
        """
        return self._启用页面切换动画
    
    def 注册页面(self, 页面名称: str, 页面部件: QWidget) -> None:
        """
        注册实际的功能页面，替换占位页面
        
        参数:
            页面名称: 页面名称
            页面部件: 页面QWidget实例
        """
        if 页面名称 in self._页面映射:
            # 获取旧的索引
            旧索引 = self._页面映射[页面名称]
            旧部件 = self._页面堆栈.widget(旧索引)
            
            # 移除旧部件并插入新部件
            self._页面堆栈.removeWidget(旧部件)
            旧部件.deleteLater()
            
            self._页面堆栈.insertWidget(旧索引, 页面部件)
            self._页面映射[页面名称] = 旧索引
    
    def 显示通知(self, 标题: str, 内容: str, 类型: str = "info") -> None:
        """
        显示弹出通知
        
        参数:
            标题: 通知标题
            内容: 通知内容
            类型: 通知类型 ("info", "success", "warning", "error")
        """
        self.通知信号.emit(标题, 内容, 类型)
        
        # 使用通知服务显示通知
        if 类型 == "success":
            self._通知服务.显示成功(标题, 内容)
        elif 类型 == "warning":
            self._通知服务.显示警告(标题, 内容)
        elif 类型 == "error":
            self._通知服务.显示错误(标题, 内容)
        else:
            self._通知服务.显示信息(标题, 内容)
        
        # 同时在状态栏显示
        self._状态栏.showMessage(f"{标题}: {内容}", 5000)
    
    def 更新状态栏(self, 消息: str, 超时: int = 0) -> None:
        """
        更新状态栏消息
        
        参数:
            消息: 要显示的消息
            超时: 消息显示时间(毫秒)，0表示永久显示
        """
        self._状态栏.showMessage(消息, 超时)
    
    def _绑定快捷键(self) -> None:
        """绑定全局快捷键"""
        # T键 - 暂停/继续
        暂停快捷键 = QShortcut(QKeySequence("T"), self)
        暂停快捷键.activated.connect(self._处理暂停继续)
        
        # ESC键 - 停止
        停止快捷键 = QShortcut(QKeySequence("Escape"), self)
        停止快捷键.activated.connect(self._处理停止)
        
        # Ctrl+S - 保存配置
        保存快捷键 = QShortcut(QKeySequence("Ctrl+S"), self)
        保存快捷键.activated.connect(self._处理保存配置)
        
        # F1键 - 显示快捷键列表
        帮助快捷键 = QShortcut(QKeySequence("F1"), self)
        帮助快捷键.activated.connect(self._显示快捷键列表)
    
    def _处理暂停继续(self) -> None:
        """处理暂停/继续快捷键"""
        self.暂停继续信号.emit()
        
        已处理 = False
        
        # 如果当前在数据收集页面且正在录制，处理暂停
        if self._当前页面 == "数据收集" and self._数据收集页 is not None and self._数据收集页.是否录制中():
            self._数据收集页.处理快捷键暂停()
            已处理 = True
        
        # 如果当前在运行页面且正在运行，处理暂停
        if self._当前页面 == "运行" and self._运行页 is not None and self._运行页.是否运行中():
            self._运行页.处理快捷键暂停()
            已处理 = True
        
        # 如果有后台数据收集线程在运行，也处理暂停
        if self._数据收集线程 is not None and self._数据收集线程.isRunning():
            self._暂停数据收集()
            已处理 = True
        
        # 如果有后台运行线程在运行，也处理暂停
        if self._运行线程 is not None and self._运行线程.isRunning():
            self._暂停运行()
            已处理 = True
        
        if 已处理:
            self._状态栏.showMessage("快捷键: 暂停/继续", 2000)
        else:
            self._状态栏.showMessage("快捷键: 当前没有可暂停的任务", 2000)
    
    def _处理停止(self) -> None:
        """处理停止快捷键"""
        self.停止信号.emit()
        
        已处理 = False
        
        # 如果当前在数据收集页面，处理停止
        if self._当前页面 == "数据收集" and self._数据收集页 is not None:
            self._数据收集页.处理快捷键停止()
            已处理 = True
        
        # 如果当前在训练页面且正在训练，处理停止
        if self._当前页面 == "训练" and self._训练页 is not None and self._训练页.是否训练中():
            self._停止训练()
            已处理 = True
        
        # 如果当前在运行页面，处理停止
        if self._当前页面 == "运行" and self._运行页 is not None:
            self._运行页.处理快捷键停止()
            已处理 = True
        
        # 如果有后台数据收集线程在运行，也处理停止
        if self._数据收集线程 is not None and self._数据收集线程.isRunning():
            self._停止数据收集()
            已处理 = True
        
        # 如果有后台训练线程在运行，也处理停止
        if self._训练线程 is not None and self._训练线程.isRunning():
            self._停止训练()
            已处理 = True
        
        # 如果有后台运行线程在运行，也处理停止
        if self._运行线程 is not None and self._运行线程.isRunning():
            self._停止运行()
            已处理 = True
        
        if 已处理:
            self._状态栏.showMessage("快捷键: 停止", 2000)
        else:
            self._状态栏.showMessage("快捷键: 当前没有可停止的任务", 2000)
    
    def _处理保存配置(self) -> None:
        """处理保存配置快捷键"""
        # 如果当前在配置页面，触发保存
        if self._当前页面 == "配置":
            if self._配置页 is not None:
                self._配置页._保存配置()
                self._状态栏.showMessage("快捷键: 保存配置", 2000)
            else:
                self._状态栏.showMessage("快捷键: 配置页面未初始化", 2000)
        else:
            self._状态栏.showMessage("快捷键: 请先切换到配置页面", 2000)
    
    def _显示快捷键列表(self) -> None:
        """显示快捷键列表对话框"""
        快捷键信息 = """
<h3>🎮 全局快捷键列表</h3>
<table style="border-collapse: collapse; width: 100%;">
<tr style="background-color: #f0f0f0;">
    <th style="padding: 8px; text-align: left; border-bottom: 1px solid #ddd;">快捷键</th>
    <th style="padding: 8px; text-align: left; border-bottom: 1px solid #ddd;">功能</th>
    <th style="padding: 8px; text-align: left; border-bottom: 1px solid #ddd;">说明</th>
</tr>
<tr>
    <td style="padding: 8px; border-bottom: 1px solid #ddd;"><b>T</b></td>
    <td style="padding: 8px; border-bottom: 1px solid #ddd;">暂停/继续</td>
    <td style="padding: 8px; border-bottom: 1px solid #ddd;">暂停或继续当前运行的任务</td>
</tr>
<tr>
    <td style="padding: 8px; border-bottom: 1px solid #ddd;"><b>ESC</b></td>
    <td style="padding: 8px; border-bottom: 1px solid #ddd;">停止</td>
    <td style="padding: 8px; border-bottom: 1px solid #ddd;">停止当前运行的任务</td>
</tr>
<tr>
    <td style="padding: 8px; border-bottom: 1px solid #ddd;"><b>Ctrl+S</b></td>
    <td style="padding: 8px; border-bottom: 1px solid #ddd;">保存配置</td>
    <td style="padding: 8px; border-bottom: 1px solid #ddd;">在配置页面保存当前配置</td>
</tr>
<tr>
    <td style="padding: 8px; border-bottom: 1px solid #ddd;"><b>F1</b></td>
    <td style="padding: 8px; border-bottom: 1px solid #ddd;">帮助</td>
    <td style="padding: 8px; border-bottom: 1px solid #ddd;">显示此快捷键列表</td>
</tr>
</table>
<br>
<p style="color: #666;">💡 提示: 快捷键在任何页面都可使用</p>
"""
        
        from 界面.组件.通用组件 import 提示对话框
        提示对话框.信息提示(self, "快捷键帮助", 快捷键信息)
        
        self._状态栏.showMessage("快捷键: 显示帮助", 2000)
    
    def 获取当前页面(self) -> str:
        """获取当前显示的页面名称"""
        return self._当前页面
    
    def 获取上一页面(self) -> Optional[str]:
        """获取上一个显示的页面名称"""
        return self._上一页面
    
    def 获取导航栏(self) -> NavigationBar:
        """获取导航栏组件"""
        return self._导航栏
    
    def 获取性能监控器(self) -> 性能监控器:
        """获取性能监控器实例"""
        return self._性能监控器
    
    def 获取页面管理器(self) -> 延迟加载页面管理器:
        """获取页面管理器实例"""
        return self._页面管理器
    
    def 获取状态更新节流器(self) -> 状态更新节流器:
        """获取状态更新节流器实例"""
        return self._状态更新节流器
    
    def 获取布局信息(self) -> dict:
        """
        获取当前窗口的布局信息
        
        返回:
            包含布局信息的字典
        """
        return {
            "窗口宽度": self.width(),
            "窗口高度": self.height(),
            "导航栏宽度": self._导航栏.width(),
            "内容区宽度": self.width() - self._导航栏.width(),
            "状态栏高度": self._状态栏.height(),
            "布局常量": {
                "窗口宽度": 布局常量.窗口宽度,
                "窗口高度": 布局常量.窗口高度,
                "导航栏宽度": 布局常量.导航栏宽度,
                "内容区外边距": 布局常量.内容区外边距,
                "卡片间距": 布局常量.卡片间距,
                "状态栏高度": 布局常量.状态栏高度,
            }
        }
    
    def 获取性能报告(self) -> dict:
        """
        获取完整的性能报告
        
        返回:
            包含性能指标的字典
        """
        页面统计 = self._页面管理器.获取性能统计()
        性能报告 = self._性能监控器.获取性能报告()
        
        return {
            "页面加载": 页面统计,
            "运行时性能": 性能报告,
            "页面切换动画": self._启用页面切换动画,
            "动画时长": 布局常量.动画时长标准,
        }


def 创建应用() -> tuple:
    """
    创建并返回应用程序和主窗口实例
    
    返回:
        (QApplication, MainWindow) 元组
    """
    import sys
    from 界面.样式.主题 import 应用全局字体
    
    应用 = QApplication(sys.argv)
    
    # 应用支持 emoji 的全局字体（需求: 1.4, 3.2）
    应用全局字体(应用)
    
    主窗口 = MainWindow()
    return 应用, 主窗口


def 启动应用() -> int:
    """
    启动GUI应用程序
    
    返回:
        应用程序退出代码
    """
    import sys
    应用, 主窗口 = 创建应用()
    主窗口.show()
    return 应用.exec()


if __name__ == "__main__":
    import sys
    sys.exit(启动应用())
