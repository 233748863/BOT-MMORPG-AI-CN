# -*- coding: utf-8 -*-
"""
主程序模块

包含应用程序的主窗口类，实现固定尺寸800x600窗口，
左侧导航栏 + 右侧内容区域布局，以及页面切换功能。
"""

from typing import Optional

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, 
    QVBoxLayout, QStackedWidget, QStatusBar, QLabel
)
from PySide6.QtCore import Signal, Slot, Qt
from PySide6.QtGui import QShortcut, QKeySequence

from 界面.样式.主题 import LIGHT_THEME_QSS, 颜色
from 界面.组件.导航栏 import NavigationBar
from 界面.页面.首页 import 首页
from 界面.页面.数据收集页 import 数据收集页
from 界面.页面.训练页 import 训练页
from 界面.页面.配置页 import 配置页
from 界面.页面.数据管理页 import 数据管理页
from 界面.线程.数据收集线程 import 数据收集线程
from 界面.线程.训练线程 import 训练线程


class MainWindow(QMainWindow):
    """
    主窗口类
    
    实现固定尺寸800x600窗口，包含左侧导航栏和右侧内容区域，
    支持页面切换和全局快捷键。
    """
    
    # 信号定义
    页面切换信号 = Signal(str)
    通知信号 = Signal(str, str, str)  # 标题, 内容, 类型
    暂停继续信号 = Signal()
    停止信号 = Signal()
    
    def __init__(self):
        """初始化主窗口，设置固定尺寸800x600"""
        super().__init__()
        
        # 设置窗口属性
        self.setWindowTitle("🎮 MMORPG游戏AI助手")
        self.setFixedSize(800, 600)
        
        # 应用样式
        self.setStyleSheet(LIGHT_THEME_QSS)
        
        # 页面映射
        self._页面映射 = {}
        self._当前页面 = "首页"
        
        # 后台线程
        self._数据收集线程: Optional[数据收集线程] = None
        self._训练线程: Optional[训练线程] = None
        
        # 初始化界面
        self._初始化界面()
        self._绑定快捷键()
    
    def _初始化界面(self) -> None:
        """初始化界面布局"""
        # 创建中央部件
        中央部件 = QWidget()
        self.setCentralWidget(中央部件)
        
        # 创建主布局 (水平布局: 导航栏 + 内容区域)
        主布局 = QHBoxLayout(中央部件)
        主布局.setContentsMargins(0, 0, 0, 0)
        主布局.setSpacing(0)
        
        # 创建导航栏
        self._导航栏 = NavigationBar()
        self._导航栏.导航项点击.connect(self.切换页面)
        主布局.addWidget(self._导航栏)
        
        # 创建右侧内容区域
        右侧容器 = QWidget()
        右侧容器.setStyleSheet(f"background-color: {颜色.背景};")
        右侧布局 = QVBoxLayout(右侧容器)
        右侧布局.setContentsMargins(0, 0, 0, 0)
        右侧布局.setSpacing(0)
        
        # 创建页面堆栈
        self._页面堆栈 = QStackedWidget()
        右侧布局.addWidget(self._页面堆栈)
        
        主布局.addWidget(右侧容器)
        
        # 创建状态栏
        self._状态栏 = QStatusBar()
        self.setStatusBar(self._状态栏)
        self._状态栏.showMessage("就绪")
        
        # 添加占位页面
        self._添加占位页面()
        
        # 注册首页
        self._注册首页()
        
        # 注册数据收集页
        self._注册数据收集页()
        
        # 注册训练页
        self._注册训练页()
        
        # 注册配置页
        self._注册配置页()
        
        # 注册数据管理页
        self._注册数据管理页()
    
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
        self._首页 = 首页()
        
        # 连接首页快捷按钮信号
        self._首页.快速运行点击.connect(lambda: self.切换页面("运行"))
        self._首页.开始录制点击.connect(lambda: self.切换页面("数据收集"))
        self._首页.训练模型点击.connect(lambda: self.切换页面("训练"))
        self._首页.数据管理点击.connect(lambda: self.切换页面("数据管理"))
        
        # 注册到页面堆栈
        self.注册页面("首页", self._首页)
    
    def _注册数据收集页(self) -> None:
        """注册数据收集页面组件"""
        self._数据收集页 = 数据收集页()
        
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
        self.显示通知("文件已保存", f"保存了 {样本数} 个样本到 {文件路径}", "success")
    
    def _处理数据收集错误(self, 错误消息: str) -> None:
        """处理数据收集错误"""
        self.显示通知("数据收集错误", 错误消息, "error")
    
    def _处理数据收集完成(self, 成功: bool, 消息: str) -> None:
        """处理数据收集完成"""
        if 成功:
            self.显示通知("数据收集完成", 消息, "success")
        else:
            self.显示通知("数据收集失败", 消息, "error")
    
    def _注册训练页(self) -> None:
        """注册训练页面组件"""
        self._训练页 = 训练页()
        
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
        self.显示通知("训练错误", 错误消息, "error")
    
    def _处理训练完成(self, 成功: bool, 消息: str) -> None:
        """处理训练完成"""
        self._训练页.训练完成(成功, 消息)
        if 成功:
            self.显示通知("训练完成", 消息, "success")
        else:
            self.显示通知("训练停止", 消息, "warning")
    
    def _注册配置页(self) -> None:
        """注册配置页面组件"""
        self._配置页 = 配置页()
        
        # 连接配置页信号
        self._配置页.配置已保存.connect(self._处理配置保存)
        self._配置页.配置已重置.connect(self._处理配置重置)
        
        # 注册到页面堆栈
        self.注册页面("配置", self._配置页)
    
    def _处理配置保存(self) -> None:
        """处理配置保存完成"""
        self._状态栏.showMessage("配置已保存", 3000)
    
    def _处理配置重置(self) -> None:
        """处理配置重置完成"""
        self._状态栏.showMessage("配置已重置", 3000)
    
    def _注册数据管理页(self) -> None:
        """注册数据管理页面组件"""
        self._数据管理页 = 数据管理页()
        
        # 连接数据管理页信号
        self._数据管理页.刷新请求.connect(self._处理数据管理刷新)
        
        # 注册到页面堆栈
        self.注册页面("数据管理", self._数据管理页)
    
    def _处理数据管理刷新(self) -> None:
        """处理数据管理页刷新请求"""
        self._状态栏.showMessage("正在刷新数据文件列表...", 2000)
    
    @Slot(str)
    def 切换页面(self, 页面名称: str) -> None:
        """
        切换到指定功能页面
        
        参数:
            页面名称: 要切换到的页面名称
        """
        if 页面名称 in self._页面映射:
            self._页面堆栈.setCurrentIndex(self._页面映射[页面名称])
            self._当前页面 = 页面名称
            self._状态栏.showMessage(f"当前页面: {页面名称}")
            self.页面切换信号.emit(页面名称)
    
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
    
    def _处理暂停继续(self) -> None:
        """处理暂停/继续快捷键"""
        self.暂停继续信号.emit()
        
        # 如果当前在数据收集页面且正在录制，处理暂停
        if self._当前页面 == "数据收集" and self._数据收集页.是否录制中():
            self._数据收集页.处理快捷键暂停()
        
        self._状态栏.showMessage("快捷键: 暂停/继续", 2000)
    
    def _处理停止(self) -> None:
        """处理停止快捷键"""
        self.停止信号.emit()
        
        # 如果当前在数据收集页面且正在录制，处理停止
        if self._当前页面 == "数据收集":
            self._数据收集页.处理快捷键停止()
        
        # 如果当前在训练页面且正在训练，处理停止
        if self._当前页面 == "训练" and self._训练页.是否训练中():
            self._停止训练()
        
        self._状态栏.showMessage("快捷键: 停止", 2000)
    
    def _处理保存配置(self) -> None:
        """处理保存配置快捷键"""
        # 如果当前在配置页面，触发保存
        if self._当前页面 == "配置":
            self._配置页._保存配置()
        else:
            self._状态栏.showMessage("快捷键: 请先切换到配置页面", 2000)
    
    def 获取当前页面(self) -> str:
        """获取当前显示的页面名称"""
        return self._当前页面
    
    def 获取导航栏(self) -> NavigationBar:
        """获取导航栏组件"""
        return self._导航栏


def 创建应用() -> tuple:
    """
    创建并返回应用程序和主窗口实例
    
    返回:
        (QApplication, MainWindow) 元组
    """
    import sys
    应用 = QApplication(sys.argv)
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
