# -*- coding: utf-8 -*-
"""
布局间距一致性属性测试模块

使用Hypothesis进行属性测试，验证布局间距一致性。

**Property 1: 布局间距一致性**
*对于任意* 页面的内容区域，其外边距应为16px；
*对于任意* 卡片组件，其内边距应为12px，卡片之间的间距应为12px

**Validates: Requirements 1.2, 1.3, 1.4**
- 1.2: 内容区域使用16px的统一外边距
- 1.3: 卡片组件使用12px的统一内边距
- 1.4: 卡片组件之间保持12px的统一间距
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from hypothesis import given, strategies as st, settings, assume

# 检查PySide6是否可用
try:
    from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout
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


# 测试用的页面名称策略
页面名称策略 = st.sampled_from([
    "数据收集页", "训练页", "运行页", "配置页", "首页", "数据管理页"
])

# 测试用的卡片标题策略
卡片标题策略 = st.text(
    alphabet=st.characters(whitelist_categories=('L', 'N', 'P', 'S')),
    min_size=1,
    max_size=20
)


@pytest.fixture(scope="module")
def 应用实例():
    """创建QApplication实例（整个模块共享）"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


class Test布局间距一致性属性测试:
    """
    布局间距一致性属性测试类
    
    **Feature: ui-layout-adaptation, Property 1: 布局间距一致性**
    **Validates: Requirements 1.2, 1.3, 1.4**
    """
    
    def test_内容区外边距常量为16px(self):
        """
        属性测试: 内容区域外边距常量应为16px
        
        **Feature: ui-layout-adaptation, Property 1: 布局间距一致性**
        **Validates: Requirements 1.2**
        """
        期望外边距 = 16
        实际外边距 = 布局常量.内容区外边距
        
        assert 实际外边距 == 期望外边距, \
            f"内容区外边距应为{期望外边距}px，实际为{实际外边距}px"
    
    def test_卡片内边距常量为12px(self):
        """
        属性测试: 卡片组件内边距常量应为12px
        
        **Feature: ui-layout-adaptation, Property 1: 布局间距一致性**
        **Validates: Requirements 1.3**
        """
        期望内边距 = 12
        实际内边距 = 布局常量.卡片内边距
        
        assert 实际内边距 == 期望内边距, \
            f"卡片内边距应为{期望内边距}px，实际为{实际内边距}px"
    
    def test_卡片间距常量为12px(self):
        """
        属性测试: 卡片组件之间间距常量应为12px
        
        **Feature: ui-layout-adaptation, Property 1: 布局间距一致性**
        **Validates: Requirements 1.4**
        """
        期望间距 = 12
        实际间距 = 布局常量.卡片间距
        
        assert 实际间距 == 期望间距, \
            f"卡片间距应为{期望间距}px，实际为{实际间距}px"
    
    def test_数据收集页内容区外边距(self, 应用实例):
        """
        属性测试: 数据收集页内容区域外边距应为16px
        
        **Feature: ui-layout-adaptation, Property 1: 布局间距一致性**
        **Validates: Requirements 1.2**
        """
        from 界面.页面.数据收集页 import 数据收集页
        
        页面 = 数据收集页()
        
        try:
            # 获取页面主布局
            主布局 = 页面.layout()
            assert 主布局 is not None, "页面应有主布局"
            
            # 获取布局边距
            左边距, 上边距, 右边距, 下边距 = 主布局.getContentsMargins()
            
            期望外边距 = 布局常量.内容区外边距
            
            # 验证所有边距都为16px
            assert 左边距 == 期望外边距, \
                f"数据收集页左边距应为{期望外边距}px，实际为{左边距}px"
            assert 上边距 == 期望外边距, \
                f"数据收集页上边距应为{期望外边距}px，实际为{上边距}px"
            assert 右边距 == 期望外边距, \
                f"数据收集页右边距应为{期望外边距}px，实际为{右边距}px"
            assert 下边距 == 期望外边距, \
                f"数据收集页下边距应为{期望外边距}px，实际为{下边距}px"
        finally:
            页面.close()
    
    def test_训练页内容区外边距(self, 应用实例):
        """
        属性测试: 训练页内容区域外边距应为16px
        
        **Feature: ui-layout-adaptation, Property 1: 布局间距一致性**
        **Validates: Requirements 1.2**
        """
        from 界面.页面.训练页 import 训练页
        
        页面 = 训练页()
        
        try:
            # 获取页面主布局
            主布局 = 页面.layout()
            assert 主布局 is not None, "页面应有主布局"
            
            # 获取布局边距
            左边距, 上边距, 右边距, 下边距 = 主布局.getContentsMargins()
            
            期望外边距 = 布局常量.内容区外边距
            
            # 验证所有边距都为16px
            assert 左边距 == 期望外边距, \
                f"训练页左边距应为{期望外边距}px，实际为{左边距}px"
            assert 上边距 == 期望外边距, \
                f"训练页上边距应为{期望外边距}px，实际为{上边距}px"
            assert 右边距 == 期望外边距, \
                f"训练页右边距应为{期望外边距}px，实际为{右边距}px"
            assert 下边距 == 期望外边距, \
                f"训练页下边距应为{期望外边距}px，实际为{下边距}px"
        finally:
            页面.close()
    
    def test_首页内容区外边距(self, 应用实例):
        """
        属性测试: 首页内容区域外边距应为16px
        
        **Feature: ui-layout-adaptation, Property 1: 布局间距一致性**
        **Validates: Requirements 1.2**
        """
        from 界面.页面.首页 import 首页
        
        页面 = 首页()
        
        try:
            # 获取页面主布局
            主布局 = 页面.layout()
            assert 主布局 is not None, "页面应有主布局"
            
            # 获取布局边距
            左边距, 上边距, 右边距, 下边距 = 主布局.getContentsMargins()
            
            期望外边距 = 布局常量.内容区外边距
            
            # 验证所有边距都为16px
            assert 左边距 == 期望外边距, \
                f"首页左边距应为{期望外边距}px，实际为{左边距}px"
            assert 上边距 == 期望外边距, \
                f"首页上边距应为{期望外边距}px，实际为{上边距}px"
            assert 右边距 == 期望外边距, \
                f"首页右边距应为{期望外边距}px，实际为{右边距}px"
            assert 下边距 == 期望外边距, \
                f"首页下边距应为{期望外边距}px，实际为{下边距}px"
        finally:
            页面.close()
    
    def test_配置页内容区外边距(self, 应用实例):
        """
        属性测试: 配置页内容区域外边距应为16px
        
        **Feature: ui-layout-adaptation, Property 1: 布局间距一致性**
        **Validates: Requirements 1.2**
        """
        from 界面.页面.配置页 import 配置页
        
        页面 = 配置页()
        
        try:
            # 获取页面主布局
            主布局 = 页面.layout()
            assert 主布局 is not None, "页面应有主布局"
            
            # 获取布局边距
            左边距, 上边距, 右边距, 下边距 = 主布局.getContentsMargins()
            
            期望外边距 = 布局常量.内容区外边距
            
            # 验证所有边距都为16px
            assert 左边距 == 期望外边距, \
                f"配置页左边距应为{期望外边距}px，实际为{左边距}px"
            assert 上边距 == 期望外边距, \
                f"配置页上边距应为{期望外边距}px，实际为{上边距}px"
            assert 右边距 == 期望外边距, \
                f"配置页右边距应为{期望外边距}px，实际为{右边距}px"
            assert 下边距 == 期望外边距, \
                f"配置页下边距应为{期望外边距}px，实际为{下边距}px"
        finally:
            页面.close()
    
    def test_数据管理页内容区外边距(self, 应用实例):
        """
        属性测试: 数据管理页内容区域外边距应为16px
        
        **Feature: ui-layout-adaptation, Property 1: 布局间距一致性**
        **Validates: Requirements 1.2**
        """
        from 界面.页面.数据管理页 import 数据管理页
        
        页面 = 数据管理页()
        
        try:
            # 获取页面主布局
            主布局 = 页面.layout()
            assert 主布局 is not None, "页面应有主布局"
            
            # 获取布局边距
            左边距, 上边距, 右边距, 下边距 = 主布局.getContentsMargins()
            
            期望外边距 = 布局常量.内容区外边距
            
            # 验证所有边距都为16px
            assert 左边距 == 期望外边距, \
                f"数据管理页左边距应为{期望外边距}px，实际为{左边距}px"
            assert 上边距 == 期望外边距, \
                f"数据管理页上边距应为{期望外边距}px，实际为{上边距}px"
            assert 右边距 == 期望外边距, \
                f"数据管理页右边距应为{期望外边距}px，实际为{右边距}px"
            assert 下边距 == 期望外边距, \
                f"数据管理页下边距应为{期望外边距}px，实际为{下边距}px"
        finally:
            页面.close()
    
    def test_卡片组件内边距(self, 应用实例):
        """
        属性测试: 卡片组件内边距应为12px
        
        **Feature: ui-layout-adaptation, Property 1: 布局间距一致性**
        **Validates: Requirements 1.3**
        """
        from 界面.组件.通用组件 import Card
        
        卡片 = Card(标题="测试卡片")
        
        try:
            # 获取卡片主布局
            主布局 = 卡片.layout()
            assert 主布局 is not None, "卡片应有主布局"
            
            # 获取布局边距
            左边距, 上边距, 右边距, 下边距 = 主布局.getContentsMargins()
            
            期望内边距 = 布局常量.卡片内边距
            
            # 验证所有边距都为12px
            assert 左边距 == 期望内边距, \
                f"卡片左内边距应为{期望内边距}px，实际为{左边距}px"
            assert 上边距 == 期望内边距, \
                f"卡片上内边距应为{期望内边距}px，实际为{上边距}px"
            assert 右边距 == 期望内边距, \
                f"卡片右内边距应为{期望内边距}px，实际为{右边距}px"
            assert 下边距 == 期望内边距, \
                f"卡片下内边距应为{期望内边距}px，实际为{下边距}px"
        finally:
            卡片.close()
    
    def test_数据收集页卡片间距(self, 应用实例):
        """
        属性测试: 数据收集页卡片之间间距应为12px
        
        **Feature: ui-layout-adaptation, Property 1: 布局间距一致性**
        **Validates: Requirements 1.4**
        """
        from 界面.页面.数据收集页 import 数据收集页
        
        页面 = 数据收集页()
        
        try:
            # 获取页面主布局
            主布局 = 页面.layout()
            assert 主布局 is not None, "页面应有主布局"
            
            # 获取布局间距
            实际间距 = 主布局.spacing()
            期望间距 = 布局常量.卡片间距
            
            assert 实际间距 == 期望间距, \
                f"数据收集页卡片间距应为{期望间距}px，实际为{实际间距}px"
        finally:
            页面.close()
    
    def test_训练页卡片间距(self, 应用实例):
        """
        属性测试: 训练页卡片之间间距应为12px
        
        **Feature: ui-layout-adaptation, Property 1: 布局间距一致性**
        **Validates: Requirements 1.4**
        """
        from 界面.页面.训练页 import 训练页
        
        页面 = 训练页()
        
        try:
            # 获取页面主布局
            主布局 = 页面.layout()
            assert 主布局 is not None, "页面应有主布局"
            
            # 获取布局间距
            实际间距 = 主布局.spacing()
            期望间距 = 布局常量.卡片间距
            
            assert 实际间距 == 期望间距, \
                f"训练页卡片间距应为{期望间距}px，实际为{实际间距}px"
        finally:
            页面.close()
    
    def test_首页卡片间距(self, 应用实例):
        """
        属性测试: 首页卡片之间间距应为12px
        
        **Feature: ui-layout-adaptation, Property 1: 布局间距一致性**
        **Validates: Requirements 1.4**
        """
        from 界面.页面.首页 import 首页
        
        页面 = 首页()
        
        try:
            # 获取页面主布局
            主布局 = 页面.layout()
            assert 主布局 is not None, "页面应有主布局"
            
            # 获取布局间距
            实际间距 = 主布局.spacing()
            期望间距 = 布局常量.卡片间距
            
            assert 实际间距 == 期望间距, \
                f"首页卡片间距应为{期望间距}px，实际为{实际间距}px"
        finally:
            页面.close()
    
    @given(标题=卡片标题策略)
    @settings(max_examples=100, deadline=None)
    def test_任意标题卡片内边距一致(self, 应用实例, 标题):
        """
        属性测试: 对于任意标题的卡片，内边距应保持为12px
        
        **Feature: ui-layout-adaptation, Property 1: 布局间距一致性**
        **Validates: Requirements 1.3**
        """
        from 界面.组件.通用组件 import Card
        
        卡片 = Card(标题=标题)
        
        try:
            # 获取卡片主布局
            主布局 = 卡片.layout()
            assert 主布局 is not None, f"卡片'{标题}'应有主布局"
            
            # 获取布局边距
            左边距, 上边距, 右边距, 下边距 = 主布局.getContentsMargins()
            
            期望内边距 = 布局常量.卡片内边距
            
            # 验证所有边距都为12px
            assert 左边距 == 期望内边距, \
                f"卡片'{标题}'左内边距应为{期望内边距}px，实际为{左边距}px"
            assert 上边距 == 期望内边距, \
                f"卡片'{标题}'上内边距应为{期望内边距}px，实际为{上边距}px"
            assert 右边距 == 期望内边距, \
                f"卡片'{标题}'右内边距应为{期望内边距}px，实际为{右边距}px"
            assert 下边距 == 期望内边距, \
                f"卡片'{标题}'下内边距应为{期望内边距}px，实际为{下边距}px"
        finally:
            卡片.close()
    
    @given(标题列表=st.lists(卡片标题策略, min_size=2, max_size=5))
    @settings(max_examples=100, deadline=None)
    def test_多个卡片内边距一致(self, 应用实例, 标题列表):
        """
        属性测试: 对于任意多个卡片，内边距应保持一致为12px
        
        **Feature: ui-layout-adaptation, Property 1: 布局间距一致性**
        **Validates: Requirements 1.3**
        """
        from 界面.组件.通用组件 import Card
        
        卡片列表 = []
        
        try:
            # 创建多个卡片
            for 标题 in 标题列表:
                卡片 = Card(标题=标题)
                卡片列表.append(卡片)
            
            期望内边距 = 布局常量.卡片内边距
            
            # 验证所有卡片的内边距一致
            for 卡片 in 卡片列表:
                主布局 = 卡片.layout()
                assert 主布局 is not None, "卡片应有主布局"
                
                左边距, 上边距, 右边距, 下边距 = 主布局.getContentsMargins()
                
                assert 左边距 == 期望内边距, \
                    f"所有卡片左内边距应为{期望内边距}px"
                assert 上边距 == 期望内边距, \
                    f"所有卡片上内边距应为{期望内边距}px"
                assert 右边距 == 期望内边距, \
                    f"所有卡片右内边距应为{期望内边距}px"
                assert 下边距 == 期望内边距, \
                    f"所有卡片下内边距应为{期望内边距}px"
        finally:
            for 卡片 in 卡片列表:
                卡片.close()
    
    def test_所有页面外边距一致性(self, 应用实例):
        """
        属性测试: 所有页面的内容区域外边距应保持一致为16px
        
        **Feature: ui-layout-adaptation, Property 1: 布局间距一致性**
        **Validates: Requirements 1.2**
        """
        from 界面.页面.数据收集页 import 数据收集页
        from 界面.页面.训练页 import 训练页
        from 界面.页面.首页 import 首页
        from 界面.页面.配置页 import 配置页
        from 界面.页面.数据管理页 import 数据管理页
        
        页面类列表 = [
            ("数据收集页", 数据收集页),
            ("训练页", 训练页),
            ("首页", 首页),
            ("配置页", 配置页),
            ("数据管理页", 数据管理页),
        ]
        
        期望外边距 = 布局常量.内容区外边距
        页面实例列表 = []
        
        try:
            for 页面名称, 页面类 in 页面类列表:
                页面 = 页面类()
                页面实例列表.append(页面)
                
                主布局 = 页面.layout()
                assert 主布局 is not None, f"{页面名称}应有主布局"
                
                左边距, 上边距, 右边距, 下边距 = 主布局.getContentsMargins()
                
                assert 左边距 == 期望外边距, \
                    f"{页面名称}左边距应为{期望外边距}px，实际为{左边距}px"
                assert 上边距 == 期望外边距, \
                    f"{页面名称}上边距应为{期望外边距}px，实际为{上边距}px"
                assert 右边距 == 期望外边距, \
                    f"{页面名称}右边距应为{期望外边距}px，实际为{右边距}px"
                assert 下边距 == 期望外边距, \
                    f"{页面名称}下边距应为{期望外边距}px，实际为{下边距}px"
        finally:
            for 页面 in 页面实例列表:
                页面.close()
    
    def test_所有页面卡片间距一致性(self, 应用实例):
        """
        属性测试: 所有页面的卡片间距应保持一致为12px
        
        **Feature: ui-layout-adaptation, Property 1: 布局间距一致性**
        **Validates: Requirements 1.4**
        """
        from 界面.页面.数据收集页 import 数据收集页
        from 界面.页面.训练页 import 训练页
        from 界面.页面.首页 import 首页
        from 界面.页面.数据管理页 import 数据管理页
        
        页面类列表 = [
            ("数据收集页", 数据收集页),
            ("训练页", 训练页),
            ("首页", 首页),
            ("数据管理页", 数据管理页),
        ]
        
        期望间距 = 布局常量.卡片间距
        页面实例列表 = []
        
        try:
            for 页面名称, 页面类 in 页面类列表:
                页面 = 页面类()
                页面实例列表.append(页面)
                
                主布局 = 页面.layout()
                assert 主布局 is not None, f"{页面名称}应有主布局"
                
                实际间距 = 主布局.spacing()
                
                assert 实际间距 == 期望间距, \
                    f"{页面名称}卡片间距应为{期望间距}px，实际为{实际间距}px"
        finally:
            for 页面 in 页面实例列表:
                页面.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
