# -*- coding: utf-8 -*-
"""
导航栏样式一致性属性测试模块

使用Hypothesis进行属性测试，验证导航栏样式一致性。

**Property 4: 导航栏样式一致性**
*对于任意* 导航栏组件，其固定宽度应为100px；
*对于任意* 导航项，其垂直间距应为指定值，选中项应有明显的视觉区分样式

**Validates: Requirements 8.1, 8.2, 8.4, 8.5**
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from hypothesis import given, strategies as st, settings

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

# 导入布局常量
from 界面.样式.布局常量 import 布局常量
from 界面.样式.主题 import 颜色

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
def 导航栏(应用实例):
    """创建导航栏实例"""
    from 界面.组件.导航栏 import NavigationBar
    导航栏实例 = NavigationBar()
    yield 导航栏实例
    导航栏实例.close()


class Test导航栏样式一致性属性测试:
    """
    导航栏样式一致性属性测试类
    
    **Feature: ui-layout-adaptation, Property 4: 导航栏样式一致性**
    **Validates: Requirements 8.1, 8.2, 8.4, 8.5**
    """
    
    def test_导航栏固定宽度为100px(self, 导航栏):
        """
        属性测试: 导航栏固定宽度应为100px
        
        **Feature: ui-layout-adaptation, Property 4: 导航栏样式一致性**
        **Validates: Requirements 8.1**
        """
        # 验证导航栏宽度为100px
        期望宽度 = 布局常量.导航栏宽度
        assert 期望宽度 == 100, f"布局常量中导航栏宽度应为100px，实际为{期望宽度}px"
        
        # 验证导航栏实际宽度
        实际宽度 = 导航栏.获取导航栏宽度()
        assert 实际宽度 == 期望宽度, \
            f"导航栏实际宽度应为{期望宽度}px，实际为{实际宽度}px"
    
    def test_导航项高度符合规范(self, 导航栏):
        """
        属性测试: 导航项高度应符合布局常量定义
        
        **Feature: ui-layout-adaptation, Property 4: 导航栏样式一致性**
        **Validates: Requirements 8.2**
        """
        期望高度 = 布局常量.导航项高度
        实际高度 = 导航栏.获取导航项高度()
        
        assert 实际高度 == 期望高度, \
            f"导航项高度应为{期望高度}px，实际为{实际高度}px"
        
        # 验证高度在合理范围内（32-48px）
        assert 32 <= 实际高度 <= 48, \
            f"导航项高度应在32-48px范围内，实际为{实际高度}px"
    
    def test_导航项垂直间距符合规范(self, 导航栏):
        """
        属性测试: 导航项垂直间距应符合布局常量定义
        
        **Feature: ui-layout-adaptation, Property 4: 导航栏样式一致性**
        **Validates: Requirements 8.4**
        """
        期望间距 = 布局常量.导航项间距
        实际间距 = 导航栏.获取导航项间距()
        
        assert 实际间距 == 期望间距, \
            f"导航项间距应为{期望间距}px，实际为{实际间距}px"
        
        # 验证间距在合理范围内（2-8px）
        assert 2 <= 实际间距 <= 8, \
            f"导航项间距应在2-8px范围内，实际为{实际间距}px"
    
    def test_导航项内边距符合规范(self, 导航栏):
        """
        属性测试: 导航项内边距应符合布局常量定义
        
        **Feature: ui-layout-adaptation, Property 4: 导航栏样式一致性**
        **Validates: Requirements 8.2**
        """
        期望内边距 = 布局常量.导航项内边距
        实际内边距 = 导航栏.获取导航项内边距()
        
        assert 实际内边距 == 期望内边距, \
            f"导航项内边距应为{期望内边距}px，实际为{实际内边距}px"
        
        # 验证内边距在合理范围内（4-16px）
        assert 4 <= 实际内边距 <= 16, \
            f"导航项内边距应在4-16px范围内，实际为{实际内边距}px"
    
    def test_选中项左侧指示条宽度符合规范(self, 导航栏):
        """
        属性测试: 选中项左侧指示条宽度应符合布局常量定义
        
        **Feature: ui-layout-adaptation, Property 4: 导航栏样式一致性**
        **Validates: Requirements 8.5**
        """
        期望宽度 = 布局常量.导航项左侧指示条宽度
        实际宽度 = 导航栏.获取左侧指示条宽度()
        
        assert 实际宽度 == 期望宽度, \
            f"左侧指示条宽度应为{期望宽度}px，实际为{实际宽度}px"
        
        # 验证指示条宽度在合理范围内（2-5px）
        assert 2 <= 实际宽度 <= 5, \
            f"左侧指示条宽度应在2-5px范围内，实际为{实际宽度}px"
    
    @given(页面名称=st.sampled_from(有效页面列表))
    @settings(max_examples=100, deadline=None)
    def test_任意页面选中后样式属性一致(self, 应用实例, 页面名称):
        """
        属性测试: 对于任意页面，选中后导航栏样式属性应保持一致
        
        **Feature: ui-layout-adaptation, Property 4: 导航栏样式一致性**
        **Validates: Requirements 8.1, 8.2, 8.4, 8.5**
        """
        from 界面.组件.导航栏 import NavigationBar
        
        导航栏 = NavigationBar()
        
        try:
            # 设置选中项
            导航栏.设置选中项(页面名称)
            
            # 验证选中后，样式属性仍然符合规范
            assert 导航栏.获取导航栏宽度() == 布局常量.导航栏宽度, \
                f"选中'{页面名称}'后，导航栏宽度应保持为{布局常量.导航栏宽度}px"
            
            assert 导航栏.获取导航项高度() == 布局常量.导航项高度, \
                f"选中'{页面名称}'后，导航项高度应保持为{布局常量.导航项高度}px"
            
            assert 导航栏.获取导航项间距() == 布局常量.导航项间距, \
                f"选中'{页面名称}'后，导航项间距应保持为{布局常量.导航项间距}px"
            
            assert 导航栏.获取左侧指示条宽度() == 布局常量.导航项左侧指示条宽度, \
                f"选中'{页面名称}'后，左侧指示条宽度应保持为{布局常量.导航项左侧指示条宽度}px"
        finally:
            导航栏.close()
    
    @given(页面序列=st.lists(st.sampled_from(有效页面列表), min_size=2, max_size=10))
    @settings(max_examples=100, deadline=None)
    def test_连续切换后样式属性一致(self, 应用实例, 页面序列):
        """
        属性测试: 对于任意页面切换序列，样式属性应始终保持一致
        
        **Feature: ui-layout-adaptation, Property 4: 导航栏样式一致性**
        **Validates: Requirements 8.1, 8.2, 8.4, 8.5**
        """
        from 界面.组件.导航栏 import NavigationBar
        
        导航栏 = NavigationBar()
        
        try:
            for 页面名称 in 页面序列:
                # 切换页面
                导航栏.设置选中项(页面名称)
                
                # 验证每次切换后，样式属性仍然符合规范
                assert 导航栏.获取导航栏宽度() == 布局常量.导航栏宽度, \
                    f"切换到'{页面名称}'后，导航栏宽度应保持一致"
                
                assert 导航栏.获取导航项高度() == 布局常量.导航项高度, \
                    f"切换到'{页面名称}'后，导航项高度应保持一致"
                
                assert 导航栏.获取导航项间距() == 布局常量.导航项间距, \
                    f"切换到'{页面名称}'后，导航项间距应保持一致"
        finally:
            导航栏.close()
    
    def test_导航栏样式表包含必要属性(self, 导航栏):
        """
        测试: 导航栏样式表应包含所有必要的样式属性
        
        **Feature: ui-layout-adaptation, Property 4: 导航栏样式一致性**
        **Validates: Requirements 8.1, 8.2, 8.4, 8.5**
        """
        样式表 = 导航栏.styleSheet()
        
        # 验证样式表包含导航项高度
        assert f"height: {布局常量.导航项高度}px" in 样式表, \
            "样式表应包含导航项高度定义"
        
        # 验证样式表包含导航项内边距
        assert f"padding: 0 {布局常量.导航项内边距}px" in 样式表, \
            "样式表应包含导航项内边距定义"
        
        # 验证样式表包含导航项间距
        assert f"margin: {布局常量.导航项间距}px" in 样式表, \
            "样式表应包含导航项间距定义"
        
        # 验证样式表包含左侧指示条宽度
        assert f"border-left: {布局常量.导航项左侧指示条宽度}px" in 样式表, \
            "样式表应包含左侧指示条宽度定义"
        
        # 验证样式表包含选中项背景色
        assert 颜色.选中背景 in 样式表, \
            "样式表应包含选中项背景色定义"
        
        # 验证样式表包含主色（用于指示条和选中文字）
        assert 颜色.主色 in 样式表, \
            "样式表应包含主色定义"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
