# -*- coding: utf-8 -*-
"""
界面模块 - MMORPG游戏AI助手的现代化图形用户界面

基于PySide6框架构建，提供明亮、清新的视觉风格。
"""

__version__ = "1.0.0"

from 界面.主程序 import MainWindow, 创建应用, 启动应用
from 界面.组件.导航栏 import NavigationBar

__all__ = ["MainWindow", "创建应用", "启动应用", "NavigationBar"]
