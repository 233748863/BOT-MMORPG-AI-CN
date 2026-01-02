# -*- coding: utf-8 -*-
"""
错误处理属性测试模块

使用Hypothesis进行属性测试，验证错误处理安全性。

**Property 13: 错误处理安全性**
*对于任意* 后台操作中发生的错误，应安全地显示错误信息而不导致程序崩溃

**Validates: Requirements 9.5**
"""

import sys
import os
import time
from typing import Optional, List
from unittest.mock import MagicMock, patch

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck

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
def 错误处理器(应用实例):
    """创建错误处理器实例用于测试"""
    from 界面.组件.错误处理 import ErrorHandler
    
    # 重置单例以确保测试隔离
    ErrorHandler._实例 = None
    处理器 = ErrorHandler()
    处理器.清空历史()
    
    yield 处理器
    
    # 清理
    处理器.清空历史()



class Test错误处理属性测试:
    """
    错误处理属性测试类
    
    **Feature: modern-ui, Property 13: 错误处理安全性**
    **Validates: Requirements 9.5**
    """

    def test_错误处理器单例模式(self, 应用实例):
        """
        测试: 错误处理器应为单例模式
        
        **Feature: modern-ui, Property 13: 错误处理安全性**
        **Validates: Requirements 9.5**
        """
        from 界面.组件.错误处理 import ErrorHandler, 获取错误处理器
        
        # 获取两个实例
        实例1 = ErrorHandler.获取实例()
        实例2 = 获取错误处理器()
        
        # 验证是同一个实例
        assert 实例1 is 实例2, "错误处理器应为单例模式"

    def test_错误处理器具有必要信号(self, 错误处理器):
        """
        测试: 错误处理器应具有必要的信号用于通知界面
        
        **Feature: modern-ui, Property 13: 错误处理安全性**
        **Validates: Requirements 9.5**
        """
        # 验证必要的信号存在
        assert hasattr(错误处理器, '错误发生'), "错误处理器应有错误发生信号"
        assert hasattr(错误处理器, '警告发生'), "错误处理器应有警告发生信号"
        assert hasattr(错误处理器, '日志记录'), "错误处理器应有日志记录信号"

    def test_处理异常不崩溃(self, 错误处理器):
        """
        测试: 处理异常时不应导致程序崩溃
        
        **Feature: modern-ui, Property 13: 错误处理安全性**
        **Validates: Requirements 9.5**
        """
        # 创建各种类型的异常
        异常列表 = [
            ValueError("测试值错误"),
            TypeError("测试类型错误"),
            RuntimeError("测试运行时错误"),
            KeyError("测试键错误"),
            IndexError("测试索引错误"),
            FileNotFoundError("测试文件未找到"),
            PermissionError("测试权限错误"),
            Exception("通用异常"),
        ]
        
        # 处理每个异常，验证不崩溃
        for 异常 in 异常列表:
            try:
                记录 = 错误处理器.处理错误(异常, "测试", "错误", 显示通知=False)
                assert 记录 is not None, f"处理{type(异常).__name__}应返回错误记录"
            except Exception as e:
                pytest.fail(f"处理{type(异常).__name__}时崩溃: {str(e)}")

    def test_错误记录包含必要信息(self, 错误处理器):
        """
        测试: 错误记录应包含必要的信息
        
        **Feature: modern-ui, Property 13: 错误处理安全性**
        **Validates: Requirements 9.5**
        """
        # 创建测试异常
        测试异常 = ValueError("测试错误消息")
        
        # 处理异常
        记录 = 错误处理器.处理错误(测试异常, "测试来源", "错误", 显示通知=False)
        
        # 验证记录包含必要信息
        assert 记录.时间戳 is not None, "错误记录应包含时间戳"
        assert 记录.错误类型 == "ValueError", "错误记录应包含正确的错误类型"
        assert 记录.错误消息 == "测试错误消息", "错误记录应包含正确的错误消息"
        assert 记录.来源 == "测试来源", "错误记录应包含正确的来源"
        assert 记录.严重级别 == "错误", "错误记录应包含正确的严重级别"
        assert 记录.堆栈跟踪 is not None, "错误记录应包含堆栈跟踪"

    def test_错误历史记录管理(self, 错误处理器):
        """
        测试: 错误历史记录应正确管理
        
        **Feature: modern-ui, Property 13: 错误处理安全性**
        **Validates: Requirements 9.5**
        """
        # 清空历史
        错误处理器.清空历史()
        assert len(错误处理器.获取错误历史()) == 0, "清空后历史应为空"
        
        # 添加错误
        for i in range(5):
            错误处理器.处理错误(ValueError(f"错误{i}"), "测试", "错误", 显示通知=False)
        
        # 验证历史记录
        历史 = 错误处理器.获取错误历史()
        assert len(历史) == 5, "应有5条错误记录"
        
        # 验证最近错误
        最近错误 = 错误处理器.获取最近错误(3)
        assert len(最近错误) == 3, "应返回3条最近错误"

    @given(错误消息=st.text(min_size=1, max_size=200))
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_任意错误消息处理安全性(self, 错误处理器, 错误消息):
        """
        属性测试: 对于任意错误消息，处理时不应崩溃
        
        **Feature: modern-ui, Property 13: 错误处理安全性**
        **Validates: Requirements 9.5**
        """
        # 过滤掉空白字符串
        assume(错误消息.strip())
        
        try:
            # 使用异常处理
            异常 = ValueError(错误消息)
            记录 = 错误处理器.处理错误(异常, "测试", "错误", 显示通知=False)
            
            # 验证记录有效
            assert 记录 is not None, "应返回错误记录"
            assert 记录.错误消息 == 错误消息, "错误消息应正确保存"
        except Exception as e:
            pytest.fail(f"处理错误消息'{错误消息[:50]}...'时崩溃: {str(e)}")

    @given(来源=st.text(min_size=1, max_size=50))
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_任意来源处理安全性(self, 错误处理器, 来源):
        """
        属性测试: 对于任意错误来源，处理时不应崩溃
        
        **Feature: modern-ui, Property 13: 错误处理安全性**
        **Validates: Requirements 9.5**
        """
        assume(来源.strip())
        
        try:
            异常 = ValueError("测试错误")
            记录 = 错误处理器.处理错误(异常, 来源, "错误", 显示通知=False)
            
            assert 记录 is not None, "应返回错误记录"
            assert 记录.来源 == 来源, "来源应正确保存"
        except Exception as e:
            pytest.fail(f"处理来源'{来源[:30]}...'时崩溃: {str(e)}")

    @given(严重级别=st.sampled_from(["警告", "错误", "严重"]))
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_任意严重级别处理安全性(self, 错误处理器, 严重级别):
        """
        属性测试: 对于任意严重级别，处理时不应崩溃
        
        **Feature: modern-ui, Property 13: 错误处理安全性**
        **Validates: Requirements 9.5**
        """
        try:
            异常 = ValueError("测试错误")
            记录 = 错误处理器.处理错误(异常, "测试", 严重级别, 显示通知=False)
            
            assert 记录 is not None, "应返回错误记录"
            assert 记录.严重级别 == 严重级别, "严重级别应正确保存"
        except Exception as e:
            pytest.fail(f"处理严重级别'{严重级别}'时崩溃: {str(e)}")


    def test_记录错误消息功能(self, 错误处理器):
        """
        测试: 记录错误消息（非异常）功能应正常工作
        
        **Feature: modern-ui, Property 13: 错误处理安全性**
        **Validates: Requirements 9.5**
        """
        错误处理器.清空历史()
        
        # 记录错误消息
        记录 = 错误处理器.记录错误消息("测试消息", "测试来源", "警告", 显示通知=False)
        
        # 验证记录
        assert 记录 is not None, "应返回错误记录"
        assert 记录.错误类型 == "消息", "错误类型应为'消息'"
        assert 记录.错误消息 == "测试消息", "错误消息应正确"
        assert 记录.堆栈跟踪 is None, "非异常记录不应有堆栈跟踪"
        
        # 验证历史记录
        历史 = 错误处理器.获取错误历史()
        assert len(历史) == 1, "应有1条记录"

    def test_错误记录格式化(self, 错误处理器):
        """
        测试: 错误记录格式化功能应正常工作
        
        **Feature: modern-ui, Property 13: 错误处理安全性**
        **Validates: Requirements 9.5**
        """
        异常 = ValueError("测试错误")
        记录 = 错误处理器.处理错误(异常, "测试", "错误", 显示通知=False)
        
        # 测试完整格式化
        完整格式 = 记录.格式化()
        assert "测试错误" in 完整格式, "格式化应包含错误消息"
        assert "ValueError" in 完整格式, "格式化应包含错误类型"
        assert "测试" in 完整格式, "格式化应包含来源"
        
        # 测试简短格式化
        简短格式 = 记录.简短格式()
        assert "测试错误" in 简短格式, "简短格式应包含错误消息"

    def test_历史记录数量限制(self, 错误处理器):
        """
        测试: 错误历史记录应有数量限制
        
        **Feature: modern-ui, Property 13: 错误处理安全性**
        **Validates: Requirements 9.5**
        """
        错误处理器.清空历史()
        
        # 添加超过限制的错误
        最大数量 = 错误处理器._最大历史数
        for i in range(最大数量 + 50):
            错误处理器.记录错误消息(f"错误{i}", "测试", "错误", 显示通知=False)
        
        # 验证历史记录不超过限制
        历史 = 错误处理器.获取错误历史()
        assert len(历史) <= 最大数量, f"历史记录不应超过{最大数量}条"


class Test安全执行装饰器测试:
    """
    安全执行装饰器测试类
    
    **Feature: modern-ui, Property 13: 错误处理安全性**
    **Validates: Requirements 9.5**
    """

    def test_安全执行装饰器捕获异常(self, 应用实例, 错误处理器):
        """
        测试: 安全执行装饰器应捕获异常而不崩溃
        
        **Feature: modern-ui, Property 13: 错误处理安全性**
        **Validates: Requirements 9.5**
        """
        from 界面.组件.错误处理 import 安全执行
        
        @安全执行("测试函数", 显示通知=False)
        def 会抛出异常的函数():
            raise ValueError("测试异常")
        
        # 调用函数，不应崩溃
        try:
            结果 = 会抛出异常的函数()
            assert 结果 is None, "异常时应返回None"
        except Exception as e:
            pytest.fail(f"安全执行装饰器未能捕获异常: {str(e)}")

    def test_安全执行装饰器正常返回(self, 应用实例, 错误处理器):
        """
        测试: 安全执行装饰器在无异常时应正常返回
        
        **Feature: modern-ui, Property 13: 错误处理安全性**
        **Validates: Requirements 9.5**
        """
        from 界面.组件.错误处理 import 安全执行
        
        @安全执行("测试函数", 显示通知=False)
        def 正常函数():
            return "成功"
        
        结果 = 正常函数()
        assert 结果 == "成功", "正常执行应返回正确结果"

    @given(返回值=st.one_of(st.integers(), st.text(), st.booleans(), st.none()))
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_安全执行装饰器保留返回值(self, 应用实例, 错误处理器, 返回值):
        """
        属性测试: 对于任意返回值，安全执行装饰器应正确保留
        
        **Feature: modern-ui, Property 13: 错误处理安全性**
        **Validates: Requirements 9.5**
        """
        from 界面.组件.错误处理 import 安全执行
        
        @安全执行("测试函数", 显示通知=False)
        def 返回指定值():
            return 返回值
        
        结果 = 返回指定值()
        assert 结果 == 返回值, f"应返回{返回值}，实际返回{结果}"


class Test安全线程测试:
    """
    安全线程测试类
    
    **Feature: modern-ui, Property 13: 错误处理安全性**
    **Validates: Requirements 9.5**
    """

    def test_安全线程基类存在(self, 应用实例):
        """
        测试: SafeThread基类应存在
        
        **Feature: modern-ui, Property 13: 错误处理安全性**
        **Validates: Requirements 9.5**
        """
        from 界面.组件.错误处理 import SafeThread
        
        assert SafeThread is not None, "SafeThread类应存在"

    def test_安全线程具有必要信号(self, 应用实例):
        """
        测试: SafeThread应具有必要的信号
        
        **Feature: modern-ui, Property 13: 错误处理安全性**
        **Validates: Requirements 9.5**
        """
        from 界面.组件.错误处理 import SafeThread
        
        # 创建测试子类
        class 测试线程(SafeThread):
            def _执行任务(self):
                pass
        
        线程 = 测试线程("测试")
        
        try:
            assert hasattr(线程, '进度更新'), "应有进度更新信号"
            assert hasattr(线程, '任务完成'), "应有任务完成信号"
            assert hasattr(线程, '错误发生'), "应有错误发生信号"
        finally:
            线程.deleteLater()

    def test_安全线程错误捕获(self, 应用实例, 错误处理器):
        """
        测试: SafeThread应捕获执行中的错误
        
        **Feature: modern-ui, Property 13: 错误处理安全性**
        **Validates: Requirements 9.5**
        """
        from 界面.组件.错误处理 import SafeThread
        
        # 创建会抛出异常的测试线程
        class 异常线程(SafeThread):
            def _执行任务(self):
                raise ValueError("测试线程异常")
        
        线程 = 异常线程("测试任务")
        
        # 记录信号
        错误信号收到 = []
        完成信号收到 = []
        
        线程.错误发生.connect(lambda msg, trace: 错误信号收到.append((msg, trace)))
        线程.任务完成.connect(lambda success, msg: 完成信号收到.append((success, msg)))
        
        try:
            # 启动线程
            线程.start()
            
            # 等待线程完成，同时处理事件循环
            等待次数 = 0
            while 线程.isRunning() and 等待次数 < 20:
                应用实例.processEvents()
                time.sleep(0.1)
                等待次数 += 1
            
            # 再处理一次事件循环以确保信号被处理
            应用实例.processEvents()
            time.sleep(0.1)
            应用实例.processEvents()
            
            # 验证错误被捕获并通过信号发送
            assert len(错误信号收到) > 0, "应收到错误信号"
            assert "测试线程异常" in 错误信号收到[0][0], "错误消息应包含异常信息"
            
            # 验证任务完成信号
            assert len(完成信号收到) > 0, "应收到任务完成信号"
            assert 完成信号收到[0][0] == False, "任务应标记为失败"
        finally:
            if 线程.isRunning():
                线程.请求停止()
                线程.wait(1000)
            线程.deleteLater()

    def test_安全线程停止功能(self, 应用实例):
        """
        测试: SafeThread应支持停止功能
        
        **Feature: modern-ui, Property 13: 错误处理安全性**
        **Validates: Requirements 9.5**
        """
        from 界面.组件.错误处理 import SafeThread
        
        class 测试线程(SafeThread):
            def _执行任务(self):
                pass
        
        线程 = 测试线程("测试")
        
        try:
            assert hasattr(线程, '请求停止'), "应有请求停止方法"
            assert hasattr(线程, '是否应该停止'), "应有是否应该停止方法"
            
            # 测试停止标志
            assert 线程.是否应该停止() == False, "初始停止标志应为False"
            线程.请求停止()
            assert 线程.是否应该停止() == True, "请求停止后标志应为True"
        finally:
            线程.deleteLater()



class Test后台线程错误处理测试:
    """
    后台线程错误处理测试类
    
    **Feature: modern-ui, Property 13: 错误处理安全性**
    **Validates: Requirements 9.5**
    """

    def test_数据收集线程具有错误信号(self, 应用实例):
        """
        测试: 数据收集线程应具有错误发生信号
        
        **Feature: modern-ui, Property 13: 错误处理安全性**
        **Validates: Requirements 9.5**
        """
        from 界面.线程.数据收集线程 import 数据收集线程
        
        线程 = 数据收集线程()
        
        try:
            assert hasattr(线程, '错误发生'), "数据收集线程应有错误发生信号"
        finally:
            线程.deleteLater()

    def test_训练线程具有错误信号(self, 应用实例):
        """
        测试: 训练线程应具有错误发生信号
        
        **Feature: modern-ui, Property 13: 错误处理安全性**
        **Validates: Requirements 9.5**
        """
        from 界面.线程.训练线程 import 训练线程
        
        线程 = 训练线程()
        
        try:
            assert hasattr(线程, '错误发生'), "训练线程应有错误发生信号"
        finally:
            线程.deleteLater()

    def test_运行线程具有错误信号(self, 应用实例):
        """
        测试: 运行线程应具有错误发生信号
        
        **Feature: modern-ui, Property 13: 错误处理安全性**
        **Validates: Requirements 9.5**
        """
        from 界面.线程.运行线程 import 运行线程
        
        线程 = 运行线程()
        
        try:
            assert hasattr(线程, '错误发生'), "运行线程应有错误发生信号"
        finally:
            线程.deleteLater()

    def test_数据收集线程错误信号可连接(self, 应用实例):
        """
        测试: 数据收集线程的错误信号应能正确连接
        
        **Feature: modern-ui, Property 13: 错误处理安全性**
        **Validates: Requirements 9.5**
        """
        from 界面.线程.数据收集线程 import 数据收集线程
        
        线程 = 数据收集线程()
        接收到的错误 = []
        
        def 错误接收器(错误消息):
            接收到的错误.append(错误消息)
        
        try:
            # 连接信号
            线程.错误发生.connect(错误接收器)
            
            # 验证连接成功（不抛出异常即为成功）
            assert True, "错误信号连接应成功"
        finally:
            线程.deleteLater()

    def test_训练线程错误信号可连接(self, 应用实例):
        """
        测试: 训练线程的错误信号应能正确连接
        
        **Feature: modern-ui, Property 13: 错误处理安全性**
        **Validates: Requirements 9.5**
        """
        from 界面.线程.训练线程 import 训练线程
        
        线程 = 训练线程()
        接收到的错误 = []
        
        def 错误接收器(错误消息, 堆栈跟踪):
            接收到的错误.append((错误消息, 堆栈跟踪))
        
        try:
            # 连接信号
            线程.错误发生.connect(错误接收器)
            
            # 验证连接成功
            assert True, "错误信号连接应成功"
        finally:
            线程.deleteLater()

    def test_运行线程错误信号可连接(self, 应用实例):
        """
        测试: 运行线程的错误信号应能正确连接
        
        **Feature: modern-ui, Property 13: 错误处理安全性**
        **Validates: Requirements 9.5**
        """
        from 界面.线程.运行线程 import 运行线程
        
        线程 = 运行线程()
        接收到的错误 = []
        
        def 错误接收器(错误消息, 堆栈跟踪):
            接收到的错误.append((错误消息, 堆栈跟踪))
        
        try:
            # 连接信号
            线程.错误发生.connect(错误接收器)
            
            # 验证连接成功
            assert True, "错误信号连接应成功"
        finally:
            线程.deleteLater()


class Test便捷函数测试:
    """
    便捷函数测试类
    
    **Feature: modern-ui, Property 13: 错误处理安全性**
    **Validates: Requirements 9.5**
    """

    def test_获取错误处理器函数(self, 应用实例):
        """
        测试: 获取错误处理器便捷函数应正常工作
        
        **Feature: modern-ui, Property 13: 错误处理安全性**
        **Validates: Requirements 9.5**
        """
        from 界面.组件.错误处理 import 获取错误处理器, ErrorHandler
        
        处理器 = 获取错误处理器()
        
        assert 处理器 is not None, "应返回错误处理器实例"
        assert isinstance(处理器, ErrorHandler), "应返回ErrorHandler实例"

    def test_记录错误便捷函数(self, 应用实例, 错误处理器):
        """
        测试: 记录错误便捷函数应正常工作
        
        **Feature: modern-ui, Property 13: 错误处理安全性**
        **Validates: Requirements 9.5**
        """
        from 界面.组件.错误处理 import 记录错误
        
        错误处理器.清空历史()
        
        # 使用便捷函数记录错误
        try:
            记录错误("测试错误消息", "测试来源")
        except Exception as e:
            pytest.fail(f"记录错误便捷函数失败: {str(e)}")
        
        # 验证记录已添加
        历史 = 错误处理器.获取错误历史()
        assert len(历史) >= 1, "应有错误记录"

    def test_记录警告便捷函数(self, 应用实例, 错误处理器):
        """
        测试: 记录警告便捷函数应正常工作
        
        **Feature: modern-ui, Property 13: 错误处理安全性**
        **Validates: Requirements 9.5**
        """
        from 界面.组件.错误处理 import 记录警告
        
        错误处理器.清空历史()
        
        # 使用便捷函数记录警告
        try:
            记录警告("测试警告消息", "测试来源")
        except Exception as e:
            pytest.fail(f"记录警告便捷函数失败: {str(e)}")
        
        # 验证记录已添加
        历史 = 错误处理器.获取错误历史()
        assert len(历史) >= 1, "应有警告记录"
        assert 历史[-1].严重级别 == "警告", "严重级别应为警告"


    @given(
        错误数量=st.integers(min_value=1, max_value=20),
        错误类型=st.sampled_from([ValueError, TypeError, RuntimeError, KeyError])
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_多个错误处理安全性(self, 应用实例, 错误处理器, 错误数量, 错误类型):
        """
        属性测试: 对于任意数量和类型的错误，处理时不应崩溃
        
        **Feature: modern-ui, Property 13: 错误处理安全性**
        **Validates: Requirements 9.5**
        """
        错误处理器.清空历史()
        
        try:
            # 处理多个错误
            for i in range(错误数量):
                异常 = 错误类型(f"错误{i}")
                记录 = 错误处理器.处理错误(异常, "测试", "错误", 显示通知=False)
                assert 记录 is not None, f"第{i}个错误应返回记录"
            
            # 验证历史记录
            历史 = 错误处理器.获取错误历史()
            assert len(历史) == 错误数量, f"应有{错误数量}条记录"
        except Exception as e:
            pytest.fail(f"处理{错误数量}个{错误类型.__name__}错误时崩溃: {str(e)}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
