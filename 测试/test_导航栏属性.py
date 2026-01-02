# -*- coding: utf-8 -*-
"""
导航栏属性测试模块

使用Hypothesis进行属性测试，验证导航切换一致性。

**Property 1: 导航切换一致性**
*对于任意* 导航项点击操作，点击后主内容区域应显示对应的功能页面，
且导航栏应正确标识当前选中项

**Validates: Requirements 1.4, 1.6**
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from hypothesis import given, strategies as st, settings, assume

# 检查PySide6是否可用
try:
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import Qt
    PYSIDE6_AVAILABLE = True
except ImportError:
    PYSIDE6_AVAILABLE = False

# 如果PySide6不可用，跳过所有测试
pytestmark = pytest.mark.skipif(
    not PYSIDE6_AVAILABLE,
    reason="PySide6未安装，跳过GUI测试"
)

# 所有有效的页面名称
有效页面列表 = ["首页", "数据收集", "训练", "运行", "配置", "数据管理"]


@pytest.fixture(scope="module")
def 应用实例():
    """创建QApplication实例（整个模块共享）"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def 主窗口(应用实例):
    """创建主窗口实例"""
    from 界面.主程序 import MainWindow
    窗口 = MainWindow()
    yield 窗口
    窗口.close()


class Test导航栏属性测试:
    """
    导航栏属性测试类
    
    **Feature: modern-ui, Property 1: 导航切换一致性**
    **Validates: Requirements 1.4, 1.6**
    """
    
    @given(页面名称=st.sampled_from(有效页面列表))
    @settings(max_examples=100, deadline=None)
    def test_导航切换一致性_单次切换(self, 应用实例, 页面名称):
        """
        属性测试: 对于任意有效页面，切换后应正确显示
        
        **Feature: modern-ui, Property 1: 导航切换一致性**
        **Validates: Requirements 1.4, 1.6**
        """
        from 界面.主程序 import MainWindow
        
        # 创建主窗口
        主窗口 = MainWindow()
        
        try:
            # 执行页面切换
            主窗口.切换页面(页面名称)
            
            # 验证1: 当前页面应与请求的页面一致
            assert 主窗口.获取当前页面() == 页面名称, \
                f"页面切换后，当前页面应为'{页面名称}'，实际为'{主窗口.获取当前页面()}'"
            
            # 验证2: 导航栏选中项应与当前页面一致
            导航栏 = 主窗口.获取导航栏()
            导航栏选中项 = 导航栏.获取当前选中项()
            assert 导航栏选中项 == 页面名称, \
                f"导航栏选中项应为'{页面名称}'，实际为'{导航栏选中项}'"
            
            # 验证3: 页面堆栈的当前索引应正确
            页面索引 = 主窗口._页面映射.get(页面名称)
            assert 页面索引 is not None, f"页面'{页面名称}'应在页面映射中"
            assert 主窗口._页面堆栈.currentIndex() == 页面索引, \
                f"页面堆栈索引应为{页面索引}，实际为{主窗口._页面堆栈.currentIndex()}"
        finally:
            主窗口.close()
    
    @given(页面序列=st.lists(st.sampled_from(有效页面列表), min_size=2, max_size=10))
    @settings(max_examples=100, deadline=None)
    def test_导航切换一致性_连续切换(self, 应用实例, 页面序列):
        """
        属性测试: 对于任意页面切换序列，每次切换后状态应保持一致
        
        **Feature: modern-ui, Property 1: 导航切换一致性**
        **Validates: Requirements 1.4, 1.6**
        """
        from 界面.主程序 import MainWindow
        
        # 创建主窗口
        主窗口 = MainWindow()
        
        try:
            for 页面名称 in 页面序列:
                # 执行页面切换
                主窗口.切换页面(页面名称)
                
                # 验证: 每次切换后，当前页面和导航栏选中项应一致
                assert 主窗口.获取当前页面() == 页面名称, \
                    f"连续切换时，当前页面应为'{页面名称}'"
                
                导航栏 = 主窗口.获取导航栏()
                assert 导航栏.获取当前选中项() == 页面名称, \
                    f"连续切换时，导航栏选中项应为'{页面名称}'"
        finally:
            主窗口.close()
    
    @given(
        起始页面=st.sampled_from(有效页面列表),
        目标页面=st.sampled_from(有效页面列表)
    )
    @settings(max_examples=100, deadline=None)
    def test_导航切换一致性_任意两页面切换(self, 应用实例, 起始页面, 目标页面):
        """
        属性测试: 从任意页面切换到任意页面，状态应正确
        
        **Feature: modern-ui, Property 1: 导航切换一致性**
        **Validates: Requirements 1.4, 1.6**
        """
        from 界面.主程序 import MainWindow
        
        # 创建主窗口
        主窗口 = MainWindow()
        
        try:
            # 先切换到起始页面
            主窗口.切换页面(起始页面)
            assert 主窗口.获取当前页面() == 起始页面
            
            # 再切换到目标页面
            主窗口.切换页面(目标页面)
            
            # 验证最终状态
            assert 主窗口.获取当前页面() == 目标页面, \
                f"从'{起始页面}'切换到'{目标页面}'后，当前页面应为'{目标页面}'"
            
            导航栏 = 主窗口.获取导航栏()
            assert 导航栏.获取当前选中项() == 目标页面, \
                f"从'{起始页面}'切换到'{目标页面}'后，导航栏选中项应为'{目标页面}'"
        finally:
            主窗口.close()
    
    def test_导航栏点击触发页面切换(self, 主窗口):
        """
        测试: 通过导航栏设置选中项应触发页面切换
        
        **Feature: modern-ui, Property 1: 导航切换一致性**
        **Validates: Requirements 1.6**
        """
        导航栏 = 主窗口.获取导航栏()
        
        for 页面名称 in 有效页面列表:
            # 通过导航栏设置选中项
            导航栏.设置选中项(页面名称)
            
            # 验证导航栏选中项正确
            assert 导航栏.获取当前选中项() == 页面名称, \
                f"设置导航栏选中项后，应为'{页面名称}'"
    
    def test_所有页面都可访问(self, 主窗口):
        """
        测试: 所有定义的页面都应该可以访问
        
        **Feature: modern-ui, Property 1: 导航切换一致性**
        **Validates: Requirements 1.4**
        """
        for 页面名称 in 有效页面列表:
            # 切换到页面
            主窗口.切换页面(页面名称)
            
            # 验证页面存在于映射中
            assert 页面名称 in 主窗口._页面映射, \
                f"页面'{页面名称}'应在页面映射中"
            
            # 验证可以成功切换
            assert 主窗口.获取当前页面() == 页面名称, \
                f"应能成功切换到页面'{页面名称}'"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
