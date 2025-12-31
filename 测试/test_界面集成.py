# -*- coding: utf-8 -*-
"""
界面集成测试模块

测试GUI界面的完整功能流程，包括：
- 页面切换流程
- 数据收集流程
- 训练流程
- 机器人运行流程
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

# 检查PySide6是否可用
try:
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import Qt, QTimer
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
    # 检查是否已有应用实例
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
    # 不要关闭应用，让pytest-qt处理


@pytest.fixture
def 主窗口(应用实例):
    """创建主窗口实例"""
    from 界面.主程序 import MainWindow
    窗口 = MainWindow()
    yield 窗口
    窗口.close()


class Test页面切换流程:
    """测试完整的页面切换流程"""
    
    def test_窗口初始化(self, 主窗口):
        """测试窗口正确初始化"""
        assert 主窗口 is not None
        assert 主窗口.width() == 800
        assert 主窗口.height() == 600
        assert 主窗口.windowTitle() == "🎮 MMORPG游戏AI助手"
    
    def test_默认显示首页(self, 主窗口):
        """测试默认显示首页"""
        assert 主窗口.获取当前页面() == "首页"
    
    def test_切换到数据收集页(self, 主窗口):
        """测试切换到数据收集页面"""
        主窗口.切换页面("数据收集")
        assert 主窗口.获取当前页面() == "数据收集"
    
    def test_切换到训练页(self, 主窗口):
        """测试切换到训练页面"""
        主窗口.切换页面("训练")
        assert 主窗口.获取当前页面() == "训练"
    
    def test_切换到运行页(self, 主窗口):
        """测试切换到运行页面"""
        主窗口.切换页面("运行")
        assert 主窗口.获取当前页面() == "运行"
    
    def test_切换到配置页(self, 主窗口):
        """测试切换到配置页面"""
        主窗口.切换页面("配置")
        assert 主窗口.获取当前页面() == "配置"
    
    def test_切换到数据管理页(self, 主窗口):
        """测试切换到数据管理页面"""
        主窗口.切换页面("数据管理")
        assert 主窗口.获取当前页面() == "数据管理"
    
    def test_完整页面切换循环(self, 主窗口):
        """测试完整的页面切换循环"""
        页面列表 = ["首页", "数据收集", "训练", "运行", "配置", "数据管理"]
        
        for 页面 in 页面列表:
            主窗口.切换页面(页面)
            assert 主窗口.获取当前页面() == 页面
        
        # 返回首页
        主窗口.切换页面("首页")
        assert 主窗口.获取当前页面() == "首页"
    
    def test_导航栏存在(self, 主窗口):
        """测试导航栏组件存在"""
        导航栏 = 主窗口.获取导航栏()
        assert 导航栏 is not None
        assert 导航栏.count() == 6  # 6个导航项


class Test数据收集页面:
    """测试数据收集页面功能"""
    
    def test_数据收集页面组件(self, 主窗口):
        """测试数据收集页面组件存在"""
        主窗口.切换页面("数据收集")
        
        # 验证页面已切换
        assert 主窗口.获取当前页面() == "数据收集"
        
        # 验证数据收集页面实例存在
        assert hasattr(主窗口, '_数据收集页')
        assert 主窗口._数据收集页 is not None
    
    def test_数据收集页面初始状态(self, 主窗口):
        """测试数据收集页面初始状态"""
        主窗口.切换页面("数据收集")
        
        # 初始状态应该不在录制中
        assert not 主窗口._数据收集页.是否录制中()


class Test训练页面:
    """测试训练页面功能"""
    
    def test_训练页面组件(self, 主窗口):
        """测试训练页面组件存在"""
        主窗口.切换页面("训练")
        
        # 验证页面已切换
        assert 主窗口.获取当前页面() == "训练"
        
        # 验证训练页面实例存在
        assert hasattr(主窗口, '_训练页')
        assert 主窗口._训练页 is not None
    
    def test_训练页面初始状态(self, 主窗口):
        """测试训练页面初始状态"""
        主窗口.切换页面("训练")
        
        # 初始状态应该不在训练中
        assert not 主窗口._训练页.是否训练中()


class Test运行页面:
    """测试运行页面功能"""
    
    def test_运行页面组件(self, 主窗口):
        """测试运行页面组件存在"""
        主窗口.切换页面("运行")
        
        # 验证页面已切换
        assert 主窗口.获取当前页面() == "运行"
        
        # 验证运行页面实例存在
        assert hasattr(主窗口, '_运行页')
        assert 主窗口._运行页 is not None
    
    def test_运行页面初始状态(self, 主窗口):
        """测试运行页面初始状态"""
        主窗口.切换页面("运行")
        
        # 初始状态应该不在运行中
        assert not 主窗口._运行页.是否运行中()


class Test配置页面:
    """测试配置页面功能"""
    
    def test_配置页面组件(self, 主窗口):
        """测试配置页面组件存在"""
        主窗口.切换页面("配置")
        
        # 验证页面已切换
        assert 主窗口.获取当前页面() == "配置"
        
        # 验证配置页面实例存在
        assert hasattr(主窗口, '_配置页')
        assert 主窗口._配置页 is not None


class Test数据管理页面:
    """测试数据管理页面功能"""
    
    def test_数据管理页面组件(self, 主窗口):
        """测试数据管理页面组件存在"""
        主窗口.切换页面("数据管理")
        
        # 验证页面已切换
        assert 主窗口.获取当前页面() == "数据管理"
        
        # 验证数据管理页面实例存在
        assert hasattr(主窗口, '_数据管理页')
        assert 主窗口._数据管理页 is not None


class Test首页功能:
    """测试首页功能"""
    
    def test_首页组件(self, 主窗口):
        """测试首页组件存在"""
        主窗口.切换页面("首页")
        
        # 验证首页实例存在
        assert hasattr(主窗口, '_首页')
        assert 主窗口._首页 is not None
    
    def test_首页快捷按钮信号(self, 主窗口):
        """测试首页快捷按钮能触发页面切换"""
        主窗口.切换页面("首页")
        
        # 模拟点击快速运行按钮（通过信号）
        主窗口._首页.快速运行点击.emit()
        assert 主窗口.获取当前页面() == "运行"
        
        # 返回首页
        主窗口.切换页面("首页")
        
        # 模拟点击开始录制按钮
        主窗口._首页.开始录制点击.emit()
        assert 主窗口.获取当前页面() == "数据收集"
        
        # 返回首页
        主窗口.切换页面("首页")
        
        # 模拟点击训练模型按钮
        主窗口._首页.训练模型点击.emit()
        assert 主窗口.获取当前页面() == "训练"
        
        # 返回首页
        主窗口.切换页面("首页")
        
        # 模拟点击数据管理按钮
        主窗口._首页.数据管理点击.emit()
        assert 主窗口.获取当前页面() == "数据管理"


class Test通知服务:
    """测试通知服务功能"""
    
    def test_通知服务存在(self, 主窗口):
        """测试通知服务组件存在"""
        assert hasattr(主窗口, '_通知服务')
        assert 主窗口._通知服务 is not None
    
    def test_显示通知方法(self, 主窗口):
        """测试显示通知方法可调用"""
        # 测试各种类型的通知
        主窗口.显示通知("测试标题", "测试内容", "info")
        主窗口.显示通知("成功标题", "成功内容", "success")
        主窗口.显示通知("警告标题", "警告内容", "warning")
        主窗口.显示通知("错误标题", "错误内容", "error")
        
        # 如果没有抛出异常，测试通过


class Test错误处理:
    """测试错误处理功能"""
    
    def test_错误处理器存在(self, 主窗口):
        """测试错误处理器组件存在"""
        assert hasattr(主窗口, '_错误处理器')
        assert 主窗口._错误处理器 is not None


class Test状态栏:
    """测试状态栏功能"""
    
    def test_状态栏存在(self, 主窗口):
        """测试状态栏存在"""
        assert hasattr(主窗口, '_状态栏')
        assert 主窗口._状态栏 is not None
    
    def test_更新状态栏(self, 主窗口):
        """测试更新状态栏消息"""
        主窗口.更新状态栏("测试消息")
        # 如果没有抛出异常，测试通过
        
        主窗口.更新状态栏("带超时的消息", 3000)
        # 如果没有抛出异常，测试通过


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
