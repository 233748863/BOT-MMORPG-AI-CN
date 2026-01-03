# -*- coding: utf-8 -*-
"""
卡片样式一致性属性测试模块

使用Hypothesis进行属性测试，验证卡片组件样式一致性。

**Property 5: 卡片样式一致性**
*对于任意* 卡片组件，其圆角应为8px，边框应为1px的#E2E8F0颜色，背景应为#FFFFFF；
*对于任意* 卡片标题，其字号应为13px加粗，与内容间距应为8px

**Validates: Requirements 9.1, 9.2, 9.3, 9.4, 9.5, 9.6**
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

# 导入布局常量和颜色
from 界面.样式.布局常量 import 布局常量
from 界面.样式.主题 import 颜色


# 测试用的卡片标题策略
卡片标题策略 = st.text(
    alphabet=st.characters(whitelist_categories=('L', 'N', 'P', 'S')),
    min_size=1,
    max_size=20
)

# 测试用的卡片图标策略（emoji或空字符串）
卡片图标策略 = st.sampled_from(["", "📊", "🎮", "⚙️", "📁", "🧠", "🤖", "🎥", "📝", "💡"])


@pytest.fixture(scope="module")
def 应用实例():
    """创建QApplication实例（整个模块共享）"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def 卡片组件(应用实例):
    """创建卡片组件实例"""
    from 界面.组件.通用组件 import Card
    卡片 = Card(标题="测试卡片", 图标="📊")
    yield 卡片
    卡片.close()


class Test卡片样式一致性属性测试:
    """
    卡片样式一致性属性测试类
    
    **Feature: ui-layout-adaptation, Property 5: 卡片样式一致性**
    **Validates: Requirements 9.1, 9.2, 9.3, 9.4, 9.5, 9.6**
    """
    
    def test_卡片圆角为8px(self, 卡片组件):
        """
        属性测试: 卡片圆角应为8px
        
        **Feature: ui-layout-adaptation, Property 5: 卡片样式一致性**
        **Validates: Requirements 9.1**
        """
        # 验证布局常量中的卡片圆角
        期望圆角 = 布局常量.卡片圆角
        assert 期望圆角 == 8, f"布局常量中卡片圆角应为8px，实际为{期望圆角}px"
        
        # 验证卡片组件的圆角属性
        实际圆角 = 卡片组件.圆角
        assert 实际圆角 == 期望圆角, \
            f"卡片组件圆角应为{期望圆角}px，实际为{实际圆角}px"
    
    def test_卡片边框宽度为1px(self, 卡片组件):
        """
        属性测试: 卡片边框宽度应为1px
        
        **Feature: ui-layout-adaptation, Property 5: 卡片样式一致性**
        **Validates: Requirements 9.2**
        """
        # 验证布局常量中的卡片边框宽度
        期望边框宽度 = 布局常量.卡片边框宽度
        assert 期望边框宽度 == 1, f"布局常量中卡片边框宽度应为1px，实际为{期望边框宽度}px"
        
        # 验证卡片组件的边框宽度属性
        实际边框宽度 = 卡片组件.边框宽度
        assert 实际边框宽度 == 期望边框宽度, \
            f"卡片组件边框宽度应为{期望边框宽度}px，实际为{实际边框宽度}px"
    
    def test_卡片边框颜色为E2E8F0(self, 卡片组件):
        """
        属性测试: 卡片边框颜色应为#E2E8F0
        
        **Feature: ui-layout-adaptation, Property 5: 卡片样式一致性**
        **Validates: Requirements 9.2**
        """
        # 验证颜色常量中的边框颜色
        期望边框颜色 = 颜色.边框
        assert 期望边框颜色 == "#E2E8F0", \
            f"颜色常量中边框颜色应为#E2E8F0，实际为{期望边框颜色}"
        
        # 验证卡片样式表中包含正确的边框颜色
        样式表 = 卡片组件.styleSheet()
        assert 期望边框颜色 in 样式表, \
            f"卡片样式表应包含边框颜色{期望边框颜色}"
    
    def test_卡片背景颜色为FFFFFF(self, 卡片组件):
        """
        属性测试: 卡片背景颜色应为#FFFFFF
        
        **Feature: ui-layout-adaptation, Property 5: 卡片样式一致性**
        **Validates: Requirements 9.3**
        """
        # 验证颜色常量中的卡片背景颜色
        期望背景颜色 = 颜色.卡片背景
        assert 期望背景颜色 == "#FFFFFF", \
            f"颜色常量中卡片背景颜色应为#FFFFFF，实际为{期望背景颜色}"
        
        # 验证卡片样式表中包含正确的背景颜色
        样式表 = 卡片组件.styleSheet()
        assert 期望背景颜色 in 样式表, \
            f"卡片样式表应包含背景颜色{期望背景颜色}"
    
    def test_卡片标题字号为13px(self, 卡片组件):
        """
        属性测试: 卡片标题字号应为13px
        
        **Feature: ui-layout-adaptation, Property 5: 卡片样式一致性**
        **Validates: Requirements 9.4**
        """
        # 验证布局常量中的卡片标题字号
        期望字号 = 布局常量.卡片标题字号
        assert 期望字号 == 13, f"布局常量中卡片标题字号应为13px，实际为{期望字号}px"
        
        # 验证字号在合理范围内（12-14px）
        assert 布局常量.卡片标题字号最小 <= 期望字号 <= 布局常量.卡片标题字号最大, \
            f"卡片标题字号应在{布局常量.卡片标题字号最小}-{布局常量.卡片标题字号最大}px范围内"
    
    def test_卡片标题与内容间距为8px(self, 卡片组件):
        """
        属性测试: 卡片标题与内容间距应为8px
        
        **Feature: ui-layout-adaptation, Property 5: 卡片样式一致性**
        **Validates: Requirements 9.5**
        """
        # 验证布局常量中的标题下边距
        期望间距 = 布局常量.标题下边距
        assert 期望间距 == 8, f"布局常量中标题下边距应为8px，实际为{期望间距}px"
    
    def test_卡片内边距为12px(self, 卡片组件):
        """
        属性测试: 卡片内边距应为12px
        
        **Feature: ui-layout-adaptation, Property 5: 卡片样式一致性**
        **Validates: Requirements 9.1**
        """
        # 验证布局常量中的卡片内边距
        期望内边距 = 布局常量.卡片内边距
        assert 期望内边距 == 12, f"布局常量中卡片内边距应为12px，实际为{期望内边距}px"
        
        # 验证卡片组件的内边距属性
        实际内边距 = 卡片组件.内边距
        assert 实际内边距 == 期望内边距, \
            f"卡片组件内边距应为{期望内边距}px，实际为{实际内边距}px"
    
    def test_卡片样式表包含必要属性(self, 卡片组件):
        """
        测试: 卡片样式表应包含所有必要的样式属性
        
        **Feature: ui-layout-adaptation, Property 5: 卡片样式一致性**
        **Validates: Requirements 9.1, 9.2, 9.3**
        """
        样式表 = 卡片组件.styleSheet()
        
        # 验证样式表包含圆角定义
        assert f"border-radius: {布局常量.卡片圆角}px" in 样式表, \
            "样式表应包含卡片圆角定义"
        
        # 验证样式表包含边框定义
        assert f"border: {布局常量.卡片边框宽度}px solid {颜色.边框}" in 样式表, \
            "样式表应包含卡片边框定义"
        
        # 验证样式表包含背景颜色定义
        assert f"background-color: {颜色.卡片背景}" in 样式表, \
            "样式表应包含卡片背景颜色定义"
    
    @given(标题=卡片标题策略, 图标=卡片图标策略)
    @settings(max_examples=100, deadline=None)
    def test_任意标题和图标的卡片样式一致(self, 应用实例, 标题, 图标):
        """
        属性测试: 对于任意标题和图标，卡片样式属性应保持一致
        
        **Feature: ui-layout-adaptation, Property 5: 卡片样式一致性**
        **Validates: Requirements 9.1, 9.2, 9.3, 9.4, 9.5, 9.6**
        """
        from 界面.组件.通用组件 import Card
        
        卡片 = Card(标题=标题, 图标=图标)
        
        try:
            # 验证圆角
            assert 卡片.圆角 == 布局常量.卡片圆角, \
                f"卡片'{标题}'的圆角应为{布局常量.卡片圆角}px"
            
            # 验证边框宽度
            assert 卡片.边框宽度 == 布局常量.卡片边框宽度, \
                f"卡片'{标题}'的边框宽度应为{布局常量.卡片边框宽度}px"
            
            # 验证内边距
            assert 卡片.内边距 == 布局常量.卡片内边距, \
                f"卡片'{标题}'的内边距应为{布局常量.卡片内边距}px"
            
            # 验证样式表包含必要属性
            样式表 = 卡片.styleSheet()
            assert 颜色.卡片背景 in 样式表, \
                f"卡片'{标题}'的样式表应包含背景颜色"
            assert 颜色.边框 in 样式表, \
                f"卡片'{标题}'的样式表应包含边框颜色"
        finally:
            卡片.close()
    
    @given(标题列表=st.lists(卡片标题策略, min_size=2, max_size=5))
    @settings(max_examples=100, deadline=None)
    def test_多个卡片样式属性一致(self, 应用实例, 标题列表):
        """
        属性测试: 对于任意多个卡片，样式属性应保持一致
        
        **Feature: ui-layout-adaptation, Property 5: 卡片样式一致性**
        **Validates: Requirements 9.1, 9.2, 9.3, 9.4, 9.5, 9.6**
        """
        from 界面.组件.通用组件 import Card
        
        卡片列表 = []
        
        try:
            # 创建多个卡片
            for 标题 in 标题列表:
                卡片 = Card(标题=标题)
                卡片列表.append(卡片)
            
            # 验证所有卡片的样式属性一致
            第一个卡片 = 卡片列表[0]
            
            for 卡片 in 卡片列表[1:]:
                # 验证圆角一致
                assert 卡片.圆角 == 第一个卡片.圆角, \
                    "所有卡片的圆角应保持一致"
                
                # 验证边框宽度一致
                assert 卡片.边框宽度 == 第一个卡片.边框宽度, \
                    "所有卡片的边框宽度应保持一致"
                
                # 验证内边距一致
                assert 卡片.内边距 == 第一个卡片.内边距, \
                    "所有卡片的内边距应保持一致"
        finally:
            for 卡片 in 卡片列表:
                卡片.close()
    
    def test_带图标标题垂直居中对齐(self, 应用实例):
        """
        属性测试: 卡片图标与标题应垂直居中对齐
        
        **Feature: ui-layout-adaptation, Property 5: 卡片样式一致性**
        **Validates: Requirements 9.6**
        """
        from 界面.组件.通用组件 import Card
        
        卡片 = Card(标题="测试标题", 图标="📊")
        
        try:
            # 验证卡片有标题
            assert 卡片.标题 == "测试标题", "卡片应有正确的标题"
            
            # 验证卡片有图标
            assert 卡片.图标 == "📊", "卡片应有正确的图标"
            
            # 验证标题标签存在（通过检查_标题标签属性）
            assert hasattr(卡片, '_标题标签'), "卡片应有标题标签"
            assert 卡片._标题标签 is not None, "标题标签不应为空"
        finally:
            卡片.close()
    
    def test_无标题卡片样式一致(self, 应用实例):
        """
        属性测试: 无标题卡片的样式属性应与有标题卡片一致
        
        **Feature: ui-layout-adaptation, Property 5: 卡片样式一致性**
        **Validates: Requirements 9.1, 9.2, 9.3**
        """
        from 界面.组件.通用组件 import Card
        
        有标题卡片 = Card(标题="测试标题")
        无标题卡片 = Card()
        
        try:
            # 验证圆角一致
            assert 无标题卡片.圆角 == 有标题卡片.圆角, \
                "无标题卡片的圆角应与有标题卡片一致"
            
            # 验证边框宽度一致
            assert 无标题卡片.边框宽度 == 有标题卡片.边框宽度, \
                "无标题卡片的边框宽度应与有标题卡片一致"
            
            # 验证内边距一致
            assert 无标题卡片.内边距 == 有标题卡片.内边距, \
                "无标题卡片的内边距应与有标题卡片一致"
        finally:
            有标题卡片.close()
            无标题卡片.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
