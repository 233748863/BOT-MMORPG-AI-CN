# -*- coding: utf-8 -*-
"""
快捷按钮内容完整性属性测试模块

使用Hypothesis进行属性测试，验证快捷按钮内容完整性。

**Property 7: 快捷按钮内容完整性**
*对于任意* 首页快捷操作按钮，其应包含图标、标题和描述信息

**Validates: Requirements 6.4**
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


# 生成有效的图标字符串（emoji或文字图标）
图标策略 = st.sampled_from(["▶️", "🎥", "🧠", "📁", "⚙️", "🎮", "📊", "💡", "⌨️", "🔧"])

# 生成有效的标题字符串（非空，长度1-10）
标题策略 = st.text(
    alphabet=st.characters(whitelist_categories=('L', 'N'), min_codepoint=0x4E00, max_codepoint=0x9FFF),
    min_size=1,
    max_size=10
).filter(lambda x: len(x.strip()) > 0)

# 生成有效的描述字符串（非空，长度1-20）
描述策略 = st.text(
    alphabet=st.characters(whitelist_categories=('L', 'N'), min_codepoint=0x4E00, max_codepoint=0x9FFF),
    min_size=1,
    max_size=20
).filter(lambda x: len(x.strip()) > 0)


@pytest.fixture(scope="module")
def 应用实例():
    """创建QApplication实例（整个模块共享）"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def 首页(应用实例):
    """创建首页实例"""
    from 界面.页面.首页 import 首页 as 首页类
    首页实例 = 首页类()
    yield 首页实例
    首页实例.close()


class Test快捷按钮内容完整性属性测试:
    """
    快捷按钮内容完整性属性测试类
    
    **Feature: ui-layout-adaptation, Property 7: 快捷按钮内容完整性**
    **Validates: Requirements 6.4**
    """
    
    def test_首页快捷按钮包含图标(self, 首页):
        """
        属性测试: 首页所有快捷按钮应包含图标
        
        **Feature: ui-layout-adaptation, Property 7: 快捷按钮内容完整性**
        **Validates: Requirements 6.4**
        """
        快捷按钮列表 = 首页.获取快捷按钮列表()
        
        for 按钮 in 快捷按钮列表:
            图标 = 按钮.图标
            assert 图标 is not None and len(图标) > 0, \
                f"快捷按钮'{按钮.标题}'应包含图标"
    
    def test_首页快捷按钮包含标题(self, 首页):
        """
        属性测试: 首页所有快捷按钮应包含标题
        
        **Feature: ui-layout-adaptation, Property 7: 快捷按钮内容完整性**
        **Validates: Requirements 6.4**
        """
        快捷按钮列表 = 首页.获取快捷按钮列表()
        
        for 按钮 in 快捷按钮列表:
            标题 = 按钮.标题
            assert 标题 is not None and len(标题) > 0, \
                f"快捷按钮应包含标题，实际图标为'{按钮.图标}'"
    
    def test_首页快捷按钮包含描述(self, 首页):
        """
        属性测试: 首页所有快捷按钮应包含描述
        
        **Feature: ui-layout-adaptation, Property 7: 快捷按钮内容完整性**
        **Validates: Requirements 6.4**
        """
        快捷按钮列表 = 首页.获取快捷按钮列表()
        
        for 按钮 in 快捷按钮列表:
            描述 = 按钮.描述
            assert 描述 is not None and len(描述) > 0, \
                f"快捷按钮'{按钮.标题}'应包含描述"
    
    def test_首页快捷按钮尺寸在规定范围内(self, 首页):
        """
        属性测试: 首页所有快捷按钮尺寸应在规定范围内
        宽度: 120-140px，高度: 80-90px
        
        **Feature: ui-layout-adaptation, Property 7: 快捷按钮内容完整性**
        **Validates: Requirements 6.4**
        """
        快捷按钮列表 = 首页.获取快捷按钮列表()
        
        for 按钮 in 快捷按钮列表:
            宽度 = 按钮.获取宽度()
            高度 = 按钮.获取高度()
            
            # 验证宽度在120-140px范围内
            assert 布局常量.快捷按钮宽度最小 <= 宽度 <= 布局常量.快捷按钮宽度最大, \
                f"快捷按钮'{按钮.标题}'宽度应在{布局常量.快捷按钮宽度最小}-{布局常量.快捷按钮宽度最大}px范围内，实际为{宽度}px"
            
            # 验证高度在80-90px范围内
            assert 布局常量.快捷按钮高度最小 <= 高度 <= 布局常量.快捷按钮高度最大, \
                f"快捷按钮'{按钮.标题}'高度应在{布局常量.快捷按钮高度最小}-{布局常量.快捷按钮高度最大}px范围内，实际为{高度}px"
    
    def test_首页快捷按钮文本包含所有内容(self, 首页):
        """
        属性测试: 首页所有快捷按钮的显示文本应包含图标、标题和描述
        
        **Feature: ui-layout-adaptation, Property 7: 快捷按钮内容完整性**
        **Validates: Requirements 6.4**
        """
        快捷按钮列表 = 首页.获取快捷按钮列表()
        
        for 按钮 in 快捷按钮列表:
            按钮文本 = 按钮.text()
            
            # 验证按钮文本包含图标
            assert 按钮.图标 in 按钮文本, \
                f"快捷按钮'{按钮.标题}'的显示文本应包含图标'{按钮.图标}'"
            
            # 验证按钮文本包含标题
            assert 按钮.标题 in 按钮文本, \
                f"快捷按钮的显示文本应包含标题'{按钮.标题}'"
            
            # 验证按钮文本包含描述
            assert 按钮.描述 in 按钮文本, \
                f"快捷按钮'{按钮.标题}'的显示文本应包含描述'{按钮.描述}'"
    
    @given(图标=图标策略, 标题=标题策略, 描述=描述策略)
    @settings(max_examples=100, deadline=None)
    def test_任意快捷按钮创建后包含完整内容(self, 应用实例, 图标, 标题, 描述):
        """
        属性测试: 对于任意图标、标题和描述，创建的快捷按钮应包含完整内容
        
        **Feature: ui-layout-adaptation, Property 7: 快捷按钮内容完整性**
        **Validates: Requirements 6.4**
        """
        from 界面.页面.首页 import 快捷按钮
        
        按钮 = 快捷按钮(图标, 标题, 描述)
        
        try:
            # 验证按钮包含图标
            assert 按钮.图标 == 图标, \
                f"快捷按钮图标应为'{图标}'，实际为'{按钮.图标}'"
            
            # 验证按钮包含标题
            assert 按钮.标题 == 标题, \
                f"快捷按钮标题应为'{标题}'，实际为'{按钮.标题}'"
            
            # 验证按钮包含描述
            assert 按钮.描述 == 描述, \
                f"快捷按钮描述应为'{描述}'，实际为'{按钮.描述}'"
            
            # 验证按钮文本包含所有内容
            按钮文本 = 按钮.text()
            assert 图标 in 按钮文本, \
                f"快捷按钮显示文本应包含图标'{图标}'"
            assert 标题 in 按钮文本, \
                f"快捷按钮显示文本应包含标题'{标题}'"
            assert 描述 in 按钮文本, \
                f"快捷按钮显示文本应包含描述'{描述}'"
        finally:
            按钮.close()
    
    @given(图标=图标策略, 标题=标题策略, 描述=描述策略)
    @settings(max_examples=100, deadline=None)
    def test_任意快捷按钮尺寸在规定范围内(self, 应用实例, 图标, 标题, 描述):
        """
        属性测试: 对于任意创建的快捷按钮，尺寸应在规定范围内
        
        **Feature: ui-layout-adaptation, Property 7: 快捷按钮内容完整性**
        **Validates: Requirements 6.4**
        """
        from 界面.页面.首页 import 快捷按钮
        
        按钮 = 快捷按钮(图标, 标题, 描述)
        
        try:
            宽度 = 按钮.获取宽度()
            高度 = 按钮.获取高度()
            
            # 验证宽度在120-140px范围内
            assert 布局常量.快捷按钮宽度最小 <= 宽度 <= 布局常量.快捷按钮宽度最大, \
                f"快捷按钮宽度应在{布局常量.快捷按钮宽度最小}-{布局常量.快捷按钮宽度最大}px范围内，实际为{宽度}px"
            
            # 验证高度在80-90px范围内
            assert 布局常量.快捷按钮高度最小 <= 高度 <= 布局常量.快捷按钮高度最大, \
                f"快捷按钮高度应在{布局常量.快捷按钮高度最小}-{布局常量.快捷按钮高度最大}px范围内，实际为{高度}px"
        finally:
            按钮.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
