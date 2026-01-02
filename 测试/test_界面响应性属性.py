# -*- coding: utf-8 -*-
"""
界面响应性属性测试模块

使用Hypothesis进行属性测试，验证后台任务界面响应性。

**Property 11: 后台任务界面响应性**
*对于任意* 耗时操作（数据收集/训练/运行），操作期间主界面应保持响应，
不阻塞用户交互

**Validates: Requirements 9.1, 9.2, 9.3**
"""

import sys
import os
import time
from typing import Optional, List
from unittest.mock import MagicMock, patch

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from hypothesis import given, strategies as st, settings, assume

# 检查PySide6是否可用
try:
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import Qt, QThread, QTimer, QEventLoop
    from PySide6.QtTest import QTest
    PYSIDE6_AVAILABLE = True
except ImportError:
    PYSIDE6_AVAILABLE = False

# 如果PySide6不可用，跳过所有测试
pytestmark = pytest.mark.skipif(
    not PYSIDE6_AVAILABLE,
    reason="PySide6未安装，跳过GUI测试"
)


@pytest.fixture(scope="module")
def 应用实例():
    """创建QApplication实例（整个模块共享）"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def 模拟数据收集线程(应用实例):
    """创建模拟的数据收集线程用于测试"""
    from 界面.线程.数据收集线程 import 数据收集线程
    
    线程 = 数据收集线程()
    yield 线程
    
    # 清理
    if 线程.isRunning():
        线程.请求停止()
        线程.wait(1000)


@pytest.fixture
def 模拟训练线程(应用实例):
    """创建模拟的训练线程用于测试"""
    from 界面.线程.训练线程 import 训练线程
    
    线程 = 训练线程()
    yield 线程
    
    # 清理
    if 线程.isRunning():
        线程.请求停止()
        线程.wait(1000)


@pytest.fixture
def 模拟运行线程(应用实例):
    """创建模拟的运行线程用于测试"""
    from 界面.线程.运行线程 import 运行线程
    
    线程 = 运行线程()
    yield 线程
    
    # 清理
    if 线程.isRunning():
        线程.请求停止()
        线程.wait(1000)


class Test界面响应性属性测试:
    """
    界面响应性属性测试类
    
    **Feature: modern-ui, Property 11: 后台任务界面响应性**
    **Validates: Requirements 9.1, 9.2, 9.3**
    """

    def test_数据收集线程继承QThread(self, 应用实例):
        """
        测试: 数据收集线程应继承自QThread，确保在后台运行
        
        **Feature: modern-ui, Property 11: 后台任务界面响应性**
        **Validates: Requirements 9.1**
        """
        from 界面.线程.数据收集线程 import 数据收集线程
        
        线程 = 数据收集线程()
        
        # 验证线程继承自QThread
        assert isinstance(线程, QThread), \
            "数据收集线程应继承自QThread以确保后台运行"
        
        线程.deleteLater()

    def test_训练线程继承QThread(self, 应用实例):
        """
        测试: 训练线程应继承自QThread，确保在后台运行
        
        **Feature: modern-ui, Property 11: 后台任务界面响应性**
        **Validates: Requirements 9.2**
        """
        from 界面.线程.训练线程 import 训练线程
        
        线程 = 训练线程()
        
        # 验证线程继承自QThread
        assert isinstance(线程, QThread), \
            "训练线程应继承自QThread以确保后台运行"
        
        线程.deleteLater()

    def test_运行线程继承QThread(self, 应用实例):
        """
        测试: 运行线程应继承自QThread，确保在后台运行
        
        **Feature: modern-ui, Property 11: 后台任务界面响应性**
        **Validates: Requirements 9.3**
        """
        from 界面.线程.运行线程 import 运行线程
        
        线程 = 运行线程()
        
        # 验证线程继承自QThread
        assert isinstance(线程, QThread), \
            "运行线程应继承自QThread以确保后台运行"
        
        线程.deleteLater()


    def test_数据收集线程具有必要信号(self, 应用实例):
        """
        测试: 数据收集线程应具有必要的信号用于与界面通信
        
        **Feature: modern-ui, Property 11: 后台任务界面响应性**
        **Validates: Requirements 9.1**
        """
        from 界面.线程.数据收集线程 import 数据收集线程
        
        线程 = 数据收集线程()
        
        # 验证必要的信号存在
        assert hasattr(线程, '进度更新'), "数据收集线程应有进度更新信号"
        assert hasattr(线程, '状态更新'), "数据收集线程应有状态更新信号"
        assert hasattr(线程, '样本收集'), "数据收集线程应有样本收集信号"
        assert hasattr(线程, '帧更新'), "数据收集线程应有帧更新信号"
        assert hasattr(线程, '任务完成'), "数据收集线程应有任务完成信号"
        assert hasattr(线程, '错误发生'), "数据收集线程应有错误发生信号"
        
        线程.deleteLater()

    def test_训练线程具有必要信号(self, 应用实例):
        """
        测试: 训练线程应具有必要的信号用于与界面通信
        
        **Feature: modern-ui, Property 11: 后台任务界面响应性**
        **Validates: Requirements 9.2**
        """
        from 界面.线程.训练线程 import 训练线程
        
        线程 = 训练线程()
        
        # 验证必要的信号存在
        assert hasattr(线程, '进度更新'), "训练线程应有进度更新信号"
        assert hasattr(线程, '轮次完成'), "训练线程应有轮次完成信号"
        assert hasattr(线程, '日志消息'), "训练线程应有日志消息信号"
        assert hasattr(线程, '任务完成'), "训练线程应有任务完成信号"
        assert hasattr(线程, '错误发生'), "训练线程应有错误发生信号"
        
        线程.deleteLater()

    def test_运行线程具有必要信号(self, 应用实例):
        """
        测试: 运行线程应具有必要的信号用于与界面通信
        
        **Feature: modern-ui, Property 11: 后台任务界面响应性**
        **Validates: Requirements 9.3**
        """
        from 界面.线程.运行线程 import 运行线程
        
        线程 = 运行线程()
        
        # 验证必要的信号存在
        assert hasattr(线程, '进度更新'), "运行线程应有进度更新信号"
        assert hasattr(线程, '状态更新'), "运行线程应有状态更新信号"
        assert hasattr(线程, '脱困提示'), "运行线程应有脱困提示信号"
        assert hasattr(线程, '性能警告'), "运行线程应有性能警告信号"
        assert hasattr(线程, '任务完成'), "运行线程应有任务完成信号"
        assert hasattr(线程, '错误发生'), "运行线程应有错误发生信号"
        
        线程.deleteLater()


    def test_数据收集线程可停止(self, 应用实例):
        """
        测试: 数据收集线程应支持停止操作
        
        **Feature: modern-ui, Property 11: 后台任务界面响应性**
        **Validates: Requirements 9.1**
        """
        from 界面.线程.数据收集线程 import 数据收集线程
        
        线程 = 数据收集线程()
        
        # 验证停止方法存在
        assert hasattr(线程, '请求停止'), "数据收集线程应有请求停止方法"
        assert callable(getattr(线程, '请求停止')), "请求停止应是可调用的方法"
        
        # 验证暂停方法存在
        assert hasattr(线程, '切换暂停'), "数据收集线程应有切换暂停方法"
        assert callable(getattr(线程, '切换暂停')), "切换暂停应是可调用的方法"
        
        线程.deleteLater()

    def test_训练线程可停止(self, 应用实例):
        """
        测试: 训练线程应支持停止操作
        
        **Feature: modern-ui, Property 11: 后台任务界面响应性**
        **Validates: Requirements 9.2**
        """
        from 界面.线程.训练线程 import 训练线程
        
        线程 = 训练线程()
        
        # 验证停止方法存在
        assert hasattr(线程, '请求停止'), "训练线程应有请求停止方法"
        assert callable(getattr(线程, '请求停止')), "请求停止应是可调用的方法"
        
        线程.deleteLater()

    def test_运行线程可停止(self, 应用实例):
        """
        测试: 运行线程应支持停止操作
        
        **Feature: modern-ui, Property 11: 后台任务界面响应性**
        **Validates: Requirements 9.3**
        """
        from 界面.线程.运行线程 import 运行线程
        
        线程 = 运行线程()
        
        # 验证停止方法存在
        assert hasattr(线程, '请求停止'), "运行线程应有请求停止方法"
        assert callable(getattr(线程, '请求停止')), "请求停止应是可调用的方法"
        
        # 验证暂停方法存在
        assert hasattr(线程, '切换暂停'), "运行线程应有切换暂停方法"
        assert callable(getattr(线程, '切换暂停')), "切换暂停应是可调用的方法"
        
        线程.deleteLater()


    @given(模式=st.sampled_from(["主线任务", "自动战斗", "通用模式"]))
    @settings(max_examples=100, deadline=None)
    def test_数据收集线程模式设置(self, 应用实例, 模式):
        """
        属性测试: 对于任意训练模式，数据收集线程应能正确设置
        
        **Feature: modern-ui, Property 11: 后台任务界面响应性**
        **Validates: Requirements 9.1**
        """
        from 界面.线程.数据收集线程 import 数据收集线程
        
        线程 = 数据收集线程()
        
        try:
            # 设置训练模式
            线程.设置训练模式(模式)
            
            # 验证模式已设置（通过内部属性）
            assert 线程._训练模式 == 模式, \
                f"训练模式应为'{模式}'，实际为'{线程._训练模式}'"
        finally:
            线程.deleteLater()

    @given(模式=st.sampled_from(["主线任务", "自动战斗"]))
    @settings(max_examples=100, deadline=None)
    def test_训练线程模式设置(self, 应用实例, 模式):
        """
        属性测试: 对于任意训练模式，训练线程应能正确设置
        
        **Feature: modern-ui, Property 11: 后台任务界面响应性**
        **Validates: Requirements 9.2**
        """
        from 界面.线程.训练线程 import 训练线程
        
        线程 = 训练线程()
        
        try:
            # 设置训练模式
            线程.设置训练模式(模式)
            
            # 验证模式已设置（通过内部属性）
            assert 线程._训练模式 == 模式, \
                f"训练模式应为'{模式}'，实际为'{线程._训练模式}'"
        finally:
            线程.deleteLater()

    @given(
        子模式=st.sampled_from(["主线任务", "自动战斗"]),
        启用增强=st.booleans()
    )
    @settings(max_examples=100, deadline=None)
    def test_运行线程模式设置(self, 应用实例, 子模式, 启用增强):
        """
        属性测试: 对于任意运行模式组合，运行线程应能正确设置
        
        **Feature: modern-ui, Property 11: 后台任务界面响应性**
        **Validates: Requirements 9.3**
        """
        from 界面.线程.运行线程 import 运行线程
        
        线程 = 运行线程()
        
        try:
            # 设置子模式
            线程.设置子模式(子模式)
            
            # 设置增强模式
            线程.设置增强模式(启用增强)
            
            # 验证模式已设置
            assert 线程._子模式 == 子模式, \
                f"子模式应为'{子模式}'，实际为'{线程._子模式}'"
            assert 线程._启用增强 == 启用增强, \
                f"增强模式应为'{启用增强}'，实际为'{线程._启用增强}'"
        finally:
            线程.deleteLater()


    def test_界面在后台线程创建时保持响应(self, 应用实例):
        """
        测试: 创建后台线程时界面应保持响应
        
        **Feature: modern-ui, Property 11: 后台任务界面响应性**
        **Validates: Requirements 9.1, 9.2, 9.3**
        """
        from 界面.线程.数据收集线程 import 数据收集线程
        from 界面.线程.训练线程 import 训练线程
        from 界面.线程.运行线程 import 运行线程
        
        # 记录开始时间
        开始时间 = time.time()
        
        # 创建多个线程实例
        线程列表 = []
        for _ in range(5):
            线程列表.append(数据收集线程())
            线程列表.append(训练线程())
            线程列表.append(运行线程())
        
        # 验证创建时间不会阻塞太久（应该在1秒内完成）
        创建时间 = time.time() - 开始时间
        assert 创建时间 < 1.0, \
            f"创建线程不应阻塞界面，实际耗时{创建时间:.2f}秒"
        
        # 处理事件循环，确保界面响应
        应用实例.processEvents()
        
        # 清理
        for 线程 in 线程列表:
            线程.deleteLater()

    def test_数据收集线程暂停状态切换(self, 应用实例):
        """
        测试: 数据收集线程暂停状态应能正确切换
        
        **Feature: modern-ui, Property 11: 后台任务界面响应性**
        **Validates: Requirements 9.1**
        """
        from 界面.线程.数据收集线程 import 数据收集线程
        
        线程 = 数据收集线程()
        
        try:
            # 初始状态应为未暂停
            assert 线程.是否暂停() == False, "初始状态应为未暂停"
            
            # 切换暂停
            线程.切换暂停()
            assert 线程.是否暂停() == True, "切换后应为暂停状态"
            
            # 再次切换
            线程.切换暂停()
            assert 线程.是否暂停() == False, "再次切换后应为未暂停状态"
        finally:
            线程.deleteLater()

    def test_运行线程暂停状态切换(self, 应用实例):
        """
        测试: 运行线程暂停状态应能正确切换
        
        **Feature: modern-ui, Property 11: 后台任务界面响应性**
        **Validates: Requirements 9.3**
        """
        from 界面.线程.运行线程 import 运行线程
        
        线程 = 运行线程()
        
        try:
            # 初始状态应为未暂停
            assert 线程.是否暂停() == False, "初始状态应为未暂停"
            
            # 切换暂停
            线程.切换暂停()
            assert 线程.是否暂停() == True, "切换后应为暂停状态"
            
            # 再次切换
            线程.切换暂停()
            assert 线程.是否暂停() == False, "再次切换后应为未暂停状态"
        finally:
            线程.deleteLater()


    @given(切换次数=st.integers(min_value=1, max_value=50))
    @settings(max_examples=100, deadline=None)
    def test_数据收集线程多次暂停切换一致性(self, 应用实例, 切换次数):
        """
        属性测试: 对于任意次数的暂停切换，最终状态应与切换次数奇偶性一致
        
        **Feature: modern-ui, Property 11: 后台任务界面响应性**
        **Validates: Requirements 9.1**
        """
        from 界面.线程.数据收集线程 import 数据收集线程
        
        线程 = 数据收集线程()
        
        try:
            # 执行多次切换
            for _ in range(切换次数):
                线程.切换暂停()
            
            # 验证最终状态
            期望状态 = (切换次数 % 2) == 1  # 奇数次切换后应为暂停
            assert 线程.是否暂停() == 期望状态, \
                f"切换{切换次数}次后，暂停状态应为{期望状态}，实际为{线程.是否暂停()}"
        finally:
            线程.deleteLater()

    @given(切换次数=st.integers(min_value=1, max_value=50))
    @settings(max_examples=100, deadline=None)
    def test_运行线程多次暂停切换一致性(self, 应用实例, 切换次数):
        """
        属性测试: 对于任意次数的暂停切换，最终状态应与切换次数奇偶性一致
        
        **Feature: modern-ui, Property 11: 后台任务界面响应性**
        **Validates: Requirements 9.3**
        """
        from 界面.线程.运行线程 import 运行线程
        
        线程 = 运行线程()
        
        try:
            # 执行多次切换
            for _ in range(切换次数):
                线程.切换暂停()
            
            # 验证最终状态
            期望状态 = (切换次数 % 2) == 1  # 奇数次切换后应为暂停
            assert 线程.是否暂停() == 期望状态, \
                f"切换{切换次数}次后，暂停状态应为{期望状态}，实际为{线程.是否暂停()}"
        finally:
            线程.deleteLater()


    def test_数据收集线程信号可连接(self, 应用实例):
        """
        测试: 数据收集线程的信号应能正确连接到槽函数
        
        **Feature: modern-ui, Property 11: 后台任务界面响应性**
        **Validates: Requirements 9.1**
        """
        from 界面.线程.数据收集线程 import 数据收集线程
        
        线程 = 数据收集线程()
        
        # 创建接收器
        接收到的信号 = []
        
        def 进度接收器(进度, 消息):
            接收到的信号.append(('进度', 进度, 消息))
        
        def 状态接收器(状态):
            接收到的信号.append(('状态', 状态))
        
        def 错误接收器(错误):
            接收到的信号.append(('错误', 错误))
        
        try:
            # 连接信号
            线程.进度更新.connect(进度接收器)
            线程.状态更新.connect(状态接收器)
            线程.错误发生.connect(错误接收器)
            
            # 验证连接成功（不抛出异常即为成功）
            assert True, "信号连接应成功"
        finally:
            线程.deleteLater()

    def test_训练线程信号可连接(self, 应用实例):
        """
        测试: 训练线程的信号应能正确连接到槽函数
        
        **Feature: modern-ui, Property 11: 后台任务界面响应性**
        **Validates: Requirements 9.2**
        """
        from 界面.线程.训练线程 import 训练线程
        
        线程 = 训练线程()
        
        # 创建接收器
        接收到的信号 = []
        
        def 进度接收器(进度, 消息):
            接收到的信号.append(('进度', 进度, 消息))
        
        def 轮次接收器(当前, 总数, 损失):
            接收到的信号.append(('轮次', 当前, 总数, 损失))
        
        def 日志接收器(消息, 级别):
            接收到的信号.append(('日志', 消息, 级别))
        
        try:
            # 连接信号
            线程.进度更新.connect(进度接收器)
            线程.轮次完成.connect(轮次接收器)
            线程.日志消息.connect(日志接收器)
            
            # 验证连接成功
            assert True, "信号连接应成功"
        finally:
            线程.deleteLater()

    def test_运行线程信号可连接(self, 应用实例):
        """
        测试: 运行线程的信号应能正确连接到槽函数
        
        **Feature: modern-ui, Property 11: 后台任务界面响应性**
        **Validates: Requirements 9.3**
        """
        from 界面.线程.运行线程 import 运行线程
        
        线程 = 运行线程()
        
        # 创建接收器
        接收到的信号 = []
        
        def 状态接收器(状态):
            接收到的信号.append(('状态', 状态))
        
        def 脱困接收器(提示):
            接收到的信号.append(('脱困', 提示))
        
        def 性能接收器(帧率):
            接收到的信号.append(('性能', 帧率))
        
        try:
            # 连接信号
            线程.状态更新.connect(状态接收器)
            线程.脱困提示.connect(脱困接收器)
            线程.性能警告.connect(性能接收器)
            
            # 验证连接成功
            assert True, "信号连接应成功"
        finally:
            线程.deleteLater()


    def test_数据收集线程初始状态正确(self, 应用实例):
        """
        测试: 数据收集线程初始状态应正确
        
        **Feature: modern-ui, Property 11: 后台任务界面响应性**
        **Validates: Requirements 9.1**
        """
        from 界面.线程.数据收集线程 import 数据收集线程
        
        线程 = 数据收集线程()
        
        try:
            # 验证初始状态
            assert 线程.isRunning() == False, "初始状态应为未运行"
            assert 线程.是否暂停() == False, "初始状态应为未暂停"
            assert 线程.获取样本数量() == 0, "初始样本数量应为0"
            assert 线程.获取文件编号() == 1, "初始文件编号应为1"
        finally:
            线程.deleteLater()

    def test_训练线程初始状态正确(self, 应用实例):
        """
        测试: 训练线程初始状态应正确
        
        **Feature: modern-ui, Property 11: 后台任务界面响应性**
        **Validates: Requirements 9.2**
        """
        from 界面.线程.训练线程 import 训练线程
        
        线程 = 训练线程()
        
        try:
            # 验证初始状态
            assert 线程.isRunning() == False, "初始状态应为未运行"
            assert 线程.获取当前轮次() == 0, "初始轮次应为0"
            assert 线程.获取当前损失() == 0.0, "初始损失应为0.0"
            assert len(线程.获取损失历史()) == 0, "初始损失历史应为空"
        finally:
            线程.deleteLater()

    def test_运行线程初始状态正确(self, 应用实例):
        """
        测试: 运行线程初始状态应正确
        
        **Feature: modern-ui, Property 11: 后台任务界面响应性**
        **Validates: Requirements 9.3**
        """
        from 界面.线程.运行线程 import 运行线程
        
        线程 = 运行线程()
        
        try:
            # 验证初始状态
            assert 线程.isRunning() == False, "初始状态应为未运行"
            assert 线程.是否暂停() == False, "初始状态应为未暂停"
            assert 线程.是否增强模式() == False, "初始状态应为非增强模式"
            
            # 验证增强模块状态
            模块状态 = 线程.获取增强模块状态()
            assert isinstance(模块状态, dict), "增强模块状态应为字典"
            assert "YOLO" in 模块状态, "应包含YOLO状态"
            assert "状态识别" in 模块状态, "应包含状态识别状态"
            assert "决策引擎" in 模块状态, "应包含决策引擎状态"
        finally:
            线程.deleteLater()


    @given(
        线程数量=st.integers(min_value=1, max_value=10),
        操作序列=st.lists(
            st.sampled_from(["创建", "设置模式", "暂停切换"]),
            min_size=1,
            max_size=20
        )
    )
    @settings(max_examples=100, deadline=None)
    def test_多线程操作界面响应性(self, 应用实例, 线程数量, 操作序列):
        """
        属性测试: 对于任意数量的线程和操作序列，界面应保持响应
        
        **Feature: modern-ui, Property 11: 后台任务界面响应性**
        **Validates: Requirements 9.1, 9.2, 9.3**
        """
        from 界面.线程.数据收集线程 import 数据收集线程
        from 界面.线程.训练线程 import 训练线程
        from 界面.线程.运行线程 import 运行线程
        
        线程列表 = []
        
        try:
            # 创建线程
            for i in range(线程数量):
                if i % 3 == 0:
                    线程列表.append(数据收集线程())
                elif i % 3 == 1:
                    线程列表.append(训练线程())
                else:
                    线程列表.append(运行线程())
            
            # 记录开始时间
            开始时间 = time.time()
            
            # 执行操作序列
            for 操作 in 操作序列:
                for 线程 in 线程列表:
                    if 操作 == "设置模式":
                        if hasattr(线程, '设置训练模式'):
                            线程.设置训练模式("主线任务")
                        if hasattr(线程, '设置子模式'):
                            线程.设置子模式("主线任务")
                    elif 操作 == "暂停切换":
                        if hasattr(线程, '切换暂停'):
                            线程.切换暂停()
                
                # 处理事件循环
                应用实例.processEvents()
            
            # 验证操作时间不会阻塞太久
            操作时间 = time.time() - 开始时间
            assert 操作时间 < 5.0, \
                f"操作不应阻塞界面太久，实际耗时{操作时间:.2f}秒"
        finally:
            # 清理
            for 线程 in 线程列表:
                if 线程.isRunning():
                    线程.请求停止()
                    线程.wait(500)
                线程.deleteLater()


    def test_线程停止标志设置(self, 应用实例):
        """
        测试: 请求停止后线程停止标志应被设置
        
        **Feature: modern-ui, Property 11: 后台任务界面响应性**
        **Validates: Requirements 9.1, 9.2, 9.3**
        """
        from 界面.线程.数据收集线程 import 数据收集线程
        from 界面.线程.训练线程 import 训练线程
        from 界面.线程.运行线程 import 运行线程
        
        # 测试数据收集线程
        数据线程 = 数据收集线程()
        assert 数据线程._停止标志 == False, "初始停止标志应为False"
        数据线程.请求停止()
        assert 数据线程._停止标志 == True, "请求停止后停止标志应为True"
        数据线程.deleteLater()
        
        # 测试训练线程
        训练线程实例 = 训练线程()
        assert 训练线程实例._停止标志 == False, "初始停止标志应为False"
        训练线程实例.请求停止()
        assert 训练线程实例._停止标志 == True, "请求停止后停止标志应为True"
        训练线程实例.deleteLater()
        
        # 测试运行线程
        运行线程实例 = 运行线程()
        assert 运行线程实例._停止标志 == False, "初始停止标志应为False"
        运行线程实例.请求停止()
        assert 运行线程实例._停止标志 == True, "请求停止后停止标志应为True"
        运行线程实例.deleteLater()

    def test_训练线程状态获取方法(self, 应用实例):
        """
        测试: 训练线程应提供状态获取方法
        
        **Feature: modern-ui, Property 11: 后台任务界面响应性**
        **Validates: Requirements 9.2**
        """
        from 界面.线程.训练线程 import 训练线程
        
        线程 = 训练线程()
        
        try:
            # 验证状态获取方法存在且可调用
            assert hasattr(线程, '获取当前轮次'), "应有获取当前轮次方法"
            assert hasattr(线程, '获取总轮次'), "应有获取总轮次方法"
            assert hasattr(线程, '获取当前损失'), "应有获取当前损失方法"
            assert hasattr(线程, '获取损失历史'), "应有获取损失历史方法"
            
            # 验证返回类型
            assert isinstance(线程.获取当前轮次(), int), "当前轮次应为整数"
            assert isinstance(线程.获取总轮次(), int), "总轮次应为整数"
            assert isinstance(线程.获取当前损失(), float), "当前损失应为浮点数"
            assert isinstance(线程.获取损失历史(), list), "损失历史应为列表"
        finally:
            线程.deleteLater()

    def test_运行线程状态获取方法(self, 应用实例):
        """
        测试: 运行线程应提供状态获取方法
        
        **Feature: modern-ui, Property 11: 后台任务界面响应性**
        **Validates: Requirements 9.3**
        """
        from 界面.线程.运行线程 import 运行线程
        
        线程 = 运行线程()
        
        try:
            # 验证状态获取方法存在且可调用
            assert hasattr(线程, '获取当前帧率'), "应有获取当前帧率方法"
            assert hasattr(线程, '是否增强模式'), "应有是否增强模式方法"
            assert hasattr(线程, '获取增强模块状态'), "应有获取增强模块状态方法"
            
            # 验证返回类型
            assert isinstance(线程.获取当前帧率(), float), "当前帧率应为浮点数"
            assert isinstance(线程.是否增强模式(), bool), "是否增强模式应为布尔值"
            assert isinstance(线程.获取增强模块状态(), dict), "增强模块状态应为字典"
        finally:
            线程.deleteLater()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
