# -*- coding: utf-8 -*-
"""
组件模块 - 可复用的UI组件

包含:
- 导航栏
- 控制面板
- 状态监控
- 日志查看器
- 通知服务
- 配置编辑器
- 错误处理
- 通用组件（卡片、动画管理器）
- 性能优化（延迟加载、状态节流、性能监控）
"""

from 界面.组件.导航栏 import NavigationBar
from 界面.组件.日志查看器 import LogViewer
from 界面.组件.通知服务 import NotificationService, ToastNotification
from 界面.组件.状态监控 import StatusMonitor, StatusIndicator, ImagePreview
from 界面.组件.错误处理 import (
    ErrorHandler, 
    SafeThread, 
    获取错误处理器, 
    记录错误, 
    记录警告,
    安全执行
)
from 界面.组件.通用组件 import Card, CardWithAction, 动画管理器, 页面切换管理器
from 界面.组件.性能优化 import (
    延迟加载页面管理器,
    状态更新节流器,
    性能监控器,
    异步初始化管理器
)

__all__ = [
    "NavigationBar", 
    "LogViewer", 
    "NotificationService", 
    "ToastNotification",
    "StatusMonitor",
    "StatusIndicator",
    "ImagePreview",
    "ErrorHandler",
    "SafeThread",
    "获取错误处理器",
    "记录错误",
    "记录警告",
    "安全执行",
    "Card",
    "CardWithAction",
    "动画管理器",
    "页面切换管理器",
    "延迟加载页面管理器",
    "状态更新节流器",
    "性能监控器",
    "异步初始化管理器",
]
