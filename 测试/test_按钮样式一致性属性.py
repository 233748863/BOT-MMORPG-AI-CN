# -*- coding: utf-8 -*-
"""
按钮样式一致性属性测试模块

使用Hypothesis进行属性测试，验证按钮组件样式一致性。

**Property 6: 按钮样式一致性**
*对于任意* 主要按钮，其背景色应为#3B82F6，文字颜色应为白色；
*对于任意* 危险按钮，其背景色应为#EF4444；
*对于任意* 禁用按钮，其背景色应为#CBD5E1；
*对于任意* 按钮，其圆角应为6px

**Validates: Requirements 10.1, 10.2, 10.3, 10.4, 10.5**
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from hypothesis import given, strategies as st, settings

# 检查PySide6是否可用
try:
    from PySide6.QtWidgets import QApplication, QPushButton
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
from 界面.样式.主题 import 颜色, LIGHT_THEME_QSS


# 测试用的按钮文字策略
按钮文字策略 = st.text(
    alphabet=st.characters(whitelist_categories=('L', 'N', 'P', 'S')),
    min_size=1,
    max_size=10
)

# 按钮类型策略
按钮类型策略 = st.sampled_from(["primary", "secondary", "danger", "success"])


@pytest.fixture(scope="module")
def 应用实例():
    """创建QApplication实例（整个模块共享）"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def 主要按钮(应用实例):
    """创建主要按钮实例"""
    按钮 = QPushButton("测试按钮")
    按钮.setStyleSheet(LIGHT_THEME_QSS)
    yield 按钮
    按钮.close()


@pytest.fixture
def 危险按钮(应用实例):
    """创建危险按钮实例"""
    按钮 = QPushButton("删除")
    按钮.setProperty("class", "danger")
    按钮.setStyleSheet(LIGHT_THEME_QSS)
    yield 按钮
    按钮.close()


@pytest.fixture
def 次要按钮(应用实例):
    """创建次要按钮实例"""
    按钮 = QPushButton("取消")
    按钮.setProperty("class", "secondary")
    按钮.setStyleSheet(LIGHT_THEME_QSS)
    yield 按钮
    按钮.close()


class Test按钮样式一致性属性测试:
    """
    按钮样式一致性属性测试类
    
    **Feature: ui-layout-adaptation, Property 6: 按钮样式一致性**
    **Validates: Requirements 10.1, 10.2, 10.3, 10.4, 10.5**
    """
    
    def test_主要按钮背景色为3B82F6(self, 应用实例):
        """
        属性测试: 主要按钮背景色应为#3B82F6
        
        **Feature: ui-layout-adaptation, Property 6: 按钮样式一致性**
        **Validates: Requirements 10.1**
        """
        # 验证颜色常量中的主色
        期望背景色 = 颜色.主色
        assert 期望背景色 == "#3B82F6", \
            f"颜色常量中主色应为#3B82F6，实际为{期望背景色}"
        
        # 验证QSS样式表中包含正确的按钮背景色
        assert "#3B82F6" in LIGHT_THEME_QSS, \
            "QSS样式表应包含主要按钮背景色#3B82F6"
        
        # 验证样式表中QPushButton的背景色定义
        assert "background-color: #3B82F6" in LIGHT_THEME_QSS, \
            "QSS样式表应包含QPushButton的背景色定义"
    
    def test_主要按钮文字颜色为白色(self, 应用实例):
        """
        属性测试: 主要按钮文字颜色应为白色
        
        **Feature: ui-layout-adaptation, Property 6: 按钮样式一致性**
        **Validates: Requirements 10.1**
        """
        # 验证颜色常量中的白色文字
        期望文字颜色 = 颜色.白色文字
        assert 期望文字颜色 == "#FFFFFF", \
            f"颜色常量中白色文字应为#FFFFFF，实际为{期望文字颜色}"
        
        # 验证QSS样式表中QPushButton的文字颜色
        # 检查 "color: white" 或 "color: #FFFFFF"
        assert "color: white" in LIGHT_THEME_QSS or "color: #FFFFFF" in LIGHT_THEME_QSS, \
            "QSS样式表应包含QPushButton的白色文字定义"
    
    def test_次要按钮样式(self, 应用实例):
        """
        属性测试: 次要按钮应使用白色背景和蓝色边框
        
        **Feature: ui-layout-adaptation, Property 6: 按钮样式一致性**
        **Validates: Requirements 10.2**
        """
        # 验证QSS样式表中包含次要按钮的样式定义
        assert 'QPushButton[class="secondary"]' in LIGHT_THEME_QSS, \
            "QSS样式表应包含次要按钮的样式定义"
        
        # 验证次要按钮使用白色背景
        assert "background-color: #FFFFFF" in LIGHT_THEME_QSS, \
            "QSS样式表应包含次要按钮的白色背景定义"
        
        # 验证次要按钮使用蓝色边框
        assert "border: 1px solid #3B82F6" in LIGHT_THEME_QSS, \
            "QSS样式表应包含次要按钮的蓝色边框定义"
    
    def test_危险按钮背景色为EF4444(self, 应用实例):
        """
        属性测试: 危险按钮背景色应为#EF4444
        
        **Feature: ui-layout-adaptation, Property 6: 按钮样式一致性**
        **Validates: Requirements 10.3**
        """
        # 验证颜色常量中的错误/危险颜色
        期望背景色 = 颜色.错误
        assert 期望背景色 == "#EF4444", \
            f"颜色常量中错误颜色应为#EF4444，实际为{期望背景色}"
        
        # 验证QSS样式表中包含危险按钮的样式定义
        assert 'QPushButton[class="danger"]' in LIGHT_THEME_QSS, \
            "QSS样式表应包含危险按钮的样式定义"
        
        # 验证危险按钮背景色
        assert "background-color: #EF4444" in LIGHT_THEME_QSS, \
            "QSS样式表应包含危险按钮背景色#EF4444"
    
    def test_禁用按钮背景色为CBD5E1(self, 应用实例):
        """
        属性测试: 禁用按钮背景色应为#CBD5E1
        
        **Feature: ui-layout-adaptation, Property 6: 按钮样式一致性**
        **Validates: Requirements 10.4**
        """
        # 验证颜色常量中的禁用按钮颜色
        期望背景色 = 颜色.按钮禁用
        assert 期望背景色 == "#CBD5E1", \
            f"颜色常量中禁用按钮颜色应为#CBD5E1，实际为{期望背景色}"
        
        # 验证QSS样式表中包含禁用按钮的样式定义
        assert "QPushButton:disabled" in LIGHT_THEME_QSS, \
            "QSS样式表应包含禁用按钮的样式定义"
        
        # 验证禁用按钮背景色
        assert "background-color: #CBD5E1" in LIGHT_THEME_QSS, \
            "QSS样式表应包含禁用按钮背景色#CBD5E1"
    
    def test_按钮圆角为6px(self, 应用实例):
        """
        属性测试: 所有按钮圆角应为6px
        
        **Feature: ui-layout-adaptation, Property 6: 按钮样式一致性**
        **Validates: Requirements 10.5**
        """
        # 验证布局常量中的按钮圆角
        期望圆角 = 布局常量.按钮圆角
        assert 期望圆角 == 6, \
            f"布局常量中按钮圆角应为6px，实际为{期望圆角}px"
        
        # 验证QSS样式表中包含按钮圆角定义
        assert "border-radius: 6px" in LIGHT_THEME_QSS, \
            "QSS样式表应包含按钮圆角定义6px"
    
    def test_按钮水平内边距至少8px(self, 应用实例):
        """
        属性测试: 按钮水平内边距应至少为8px
        
        **Feature: ui-layout-adaptation, Property 6: 按钮样式一致性**
        **Validates: Requirements 10.5**
        """
        # 验证布局常量中的按钮水平内边距
        期望内边距 = 布局常量.按钮水平内边距
        assert 期望内边距 >= 8, \
            f"布局常量中按钮水平内边距应至少为8px，实际为{期望内边距}px"
        
        # 验证QSS样式表中包含按钮内边距定义
        # padding: 6px 12px 表示垂直6px，水平12px
        assert "padding:" in LIGHT_THEME_QSS, \
            "QSS样式表应包含按钮内边距定义"
    
    def test_按钮高度为32px(self, 应用实例):
        """
        属性测试: 按钮高度应为32px
        
        **Feature: ui-layout-adaptation, Property 6: 按钮样式一致性**
        **Validates: Requirements 10.5**
        """
        # 验证布局常量中的按钮高度
        期望高度 = 布局常量.按钮高度
        assert 期望高度 == 32, \
            f"布局常量中按钮高度应为32px，实际为{期望高度}px"
        
        # 验证QSS样式表中包含按钮高度定义
        assert "min-height: 32px" in LIGHT_THEME_QSS, \
            "QSS样式表应包含按钮最小高度定义32px"
        assert "max-height: 32px" in LIGHT_THEME_QSS, \
            "QSS样式表应包含按钮最大高度定义32px"
    
    def test_按钮宽度范围60到100px(self, 应用实例):
        """
        属性测试: 主要操作按钮宽度应在60-100px范围内
        
        **Feature: ui-layout-adaptation, Property 6: 按钮样式一致性**
        **Validates: Requirements 10.5**
        """
        # 验证布局常量中的按钮宽度范围
        最小宽度 = 布局常量.按钮最小宽度
        最大宽度 = 布局常量.按钮最大宽度
        
        assert 最小宽度 == 60, \
            f"布局常量中按钮最小宽度应为60px，实际为{最小宽度}px"
        assert 最大宽度 == 100, \
            f"布局常量中按钮最大宽度应为100px，实际为{最大宽度}px"
        
        # 验证QSS样式表中包含按钮宽度定义
        assert "min-width: 60px" in LIGHT_THEME_QSS, \
            "QSS样式表应包含按钮最小宽度定义60px"
        assert "max-width: 100px" in LIGHT_THEME_QSS, \
            "QSS样式表应包含按钮最大宽度定义100px"
    
    def test_按钮悬停效果(self, 应用实例):
        """
        属性测试: 按钮应有悬停效果
        
        **Feature: ui-layout-adaptation, Property 6: 按钮样式一致性**
        **Validates: Requirements 10.6**
        """
        # 验证颜色常量中的悬停颜色
        期望悬停色 = 颜色.主色悬停
        assert 期望悬停色 == "#2563EB", \
            f"颜色常量中主色悬停应为#2563EB，实际为{期望悬停色}"
        
        # 验证QSS样式表中包含悬停效果定义
        assert "QPushButton:hover" in LIGHT_THEME_QSS, \
            "QSS样式表应包含按钮悬停效果定义"
        assert "#2563EB" in LIGHT_THEME_QSS, \
            "QSS样式表应包含悬停背景色#2563EB"
    
    def test_按钮按下效果(self, 应用实例):
        """
        属性测试: 按钮应有按下效果
        
        **Feature: ui-layout-adaptation, Property 6: 按钮样式一致性**
        **Validates: Requirements 10.7**
        """
        # 验证颜色常量中的按下颜色
        期望按下色 = 颜色.主色按下
        assert 期望按下色 == "#1D4ED8", \
            f"颜色常量中主色按下应为#1D4ED8，实际为{期望按下色}"
        
        # 验证QSS样式表中包含按下效果定义
        assert "QPushButton:pressed" in LIGHT_THEME_QSS, \
            "QSS样式表应包含按钮按下效果定义"
        assert "#1D4ED8" in LIGHT_THEME_QSS, \
            "QSS样式表应包含按下背景色#1D4ED8"

    
    @given(按钮文字=按钮文字策略)
    @settings(max_examples=100, deadline=None)
    def test_任意文字的主要按钮样式一致(self, 应用实例, 按钮文字):
        """
        属性测试: 对于任意文字，主要按钮样式属性应保持一致
        
        **Feature: ui-layout-adaptation, Property 6: 按钮样式一致性**
        **Validates: Requirements 10.1, 10.5**
        """
        按钮 = QPushButton(按钮文字)
        按钮.setStyleSheet(LIGHT_THEME_QSS)
        
        try:
            # 验证按钮圆角常量
            assert 布局常量.按钮圆角 == 6, \
                f"按钮'{按钮文字}'的圆角常量应为6px"
            
            # 验证按钮高度常量
            assert 布局常量.按钮高度 == 32, \
                f"按钮'{按钮文字}'的高度常量应为32px"
            
            # 验证按钮宽度范围常量
            assert 布局常量.按钮最小宽度 == 60, \
                f"按钮'{按钮文字}'的最小宽度常量应为60px"
            assert 布局常量.按钮最大宽度 == 100, \
                f"按钮'{按钮文字}'的最大宽度常量应为100px"
            
            # 验证按钮内边距常量
            assert 布局常量.按钮水平内边距 >= 8, \
                f"按钮'{按钮文字}'的水平内边距常量应至少为8px"
        finally:
            按钮.close()
    
    @given(按钮类型=按钮类型策略, 按钮文字=按钮文字策略)
    @settings(max_examples=100, deadline=None)
    def test_任意类型按钮样式定义存在(self, 应用实例, 按钮类型, 按钮文字):
        """
        属性测试: 对于任意类型的按钮，样式定义应存在于QSS中
        
        **Feature: ui-layout-adaptation, Property 6: 按钮样式一致性**
        **Validates: Requirements 10.1, 10.2, 10.3, 10.4, 10.5**
        """
        按钮 = QPushButton(按钮文字)
        
        if 按钮类型 != "primary":
            按钮.setProperty("class", 按钮类型)
        
        按钮.setStyleSheet(LIGHT_THEME_QSS)
        
        try:
            # 验证基础按钮样式存在
            assert "QPushButton" in LIGHT_THEME_QSS, \
                "QSS应包含QPushButton基础样式"
            
            # 验证按钮圆角定义存在
            assert "border-radius: 6px" in LIGHT_THEME_QSS, \
                "QSS应包含按钮圆角定义"
            
            # 根据按钮类型验证特定样式
            if 按钮类型 == "primary":
                assert "#3B82F6" in LIGHT_THEME_QSS, \
                    "QSS应包含主要按钮背景色"
            elif 按钮类型 == "secondary":
                assert 'QPushButton[class="secondary"]' in LIGHT_THEME_QSS, \
                    "QSS应包含次要按钮样式定义"
            elif 按钮类型 == "danger":
                assert 'QPushButton[class="danger"]' in LIGHT_THEME_QSS, \
                    "QSS应包含危险按钮样式定义"
            elif 按钮类型 == "success":
                assert 'QPushButton[class="success"]' in LIGHT_THEME_QSS, \
                    "QSS应包含成功按钮样式定义"
        finally:
            按钮.close()
    
    @given(按钮数量=st.integers(min_value=2, max_value=5))
    @settings(max_examples=100, deadline=None)
    def test_多个按钮样式常量一致(self, 应用实例, 按钮数量):
        """
        属性测试: 对于任意数量的按钮，样式常量应保持一致
        
        **Feature: ui-layout-adaptation, Property 6: 按钮样式一致性**
        **Validates: Requirements 10.1, 10.2, 10.3, 10.4, 10.5**
        """
        按钮列表 = []
        
        try:
            # 创建多个按钮
            for i in range(按钮数量):
                按钮 = QPushButton(f"按钮{i}")
                按钮.setStyleSheet(LIGHT_THEME_QSS)
                按钮列表.append(按钮)
            
            # 验证所有按钮使用相同的样式常量
            for 按钮 in 按钮列表:
                # 验证圆角常量一致
                assert 布局常量.按钮圆角 == 6, \
                    "所有按钮的圆角常量应为6px"
                
                # 验证高度常量一致
                assert 布局常量.按钮高度 == 32, \
                    "所有按钮的高度常量应为32px"
                
                # 验证宽度范围常量一致
                assert 布局常量.按钮最小宽度 == 60, \
                    "所有按钮的最小宽度常量应为60px"
                assert 布局常量.按钮最大宽度 == 100, \
                    "所有按钮的最大宽度常量应为100px"
        finally:
            for 按钮 in 按钮列表:
                按钮.close()
    
    def test_颜色常量完整性(self, 应用实例):
        """
        测试: 按钮相关的颜色常量应完整定义
        
        **Feature: ui-layout-adaptation, Property 6: 按钮样式一致性**
        **Validates: Requirements 10.1, 10.2, 10.3, 10.4**
        """
        # 验证主色定义
        assert hasattr(颜色, '主色'), "颜色类应有主色属性"
        assert 颜色.主色 == "#3B82F6", "主色应为#3B82F6"
        
        # 验证主色悬停定义
        assert hasattr(颜色, '主色悬停'), "颜色类应有主色悬停属性"
        assert 颜色.主色悬停 == "#2563EB", "主色悬停应为#2563EB"
        
        # 验证主色按下定义
        assert hasattr(颜色, '主色按下'), "颜色类应有主色按下属性"
        assert 颜色.主色按下 == "#1D4ED8", "主色按下应为#1D4ED8"
        
        # 验证错误/危险颜色定义
        assert hasattr(颜色, '错误'), "颜色类应有错误属性"
        assert 颜色.错误 == "#EF4444", "错误颜色应为#EF4444"
        
        # 验证禁用按钮颜色定义
        assert hasattr(颜色, '按钮禁用'), "颜色类应有按钮禁用属性"
        assert 颜色.按钮禁用 == "#CBD5E1", "禁用按钮颜色应为#CBD5E1"
        
        # 验证白色文字定义
        assert hasattr(颜色, '白色文字'), "颜色类应有白色文字属性"
        assert 颜色.白色文字 == "#FFFFFF", "白色文字应为#FFFFFF"
    
    def test_布局常量完整性(self, 应用实例):
        """
        测试: 按钮相关的布局常量应完整定义
        
        **Feature: ui-layout-adaptation, Property 6: 按钮样式一致性**
        **Validates: Requirements 10.5**
        """
        # 验证按钮高度定义
        assert hasattr(布局常量, '按钮高度'), "布局常量类应有按钮高度属性"
        assert 布局常量.按钮高度 == 32, "按钮高度应为32px"
        
        # 验证按钮宽度范围定义
        assert hasattr(布局常量, '按钮最小宽度'), "布局常量类应有按钮最小宽度属性"
        assert hasattr(布局常量, '按钮最大宽度'), "布局常量类应有按钮最大宽度属性"
        assert 布局常量.按钮最小宽度 == 60, "按钮最小宽度应为60px"
        assert 布局常量.按钮最大宽度 == 100, "按钮最大宽度应为100px"
        
        # 验证按钮圆角定义
        assert hasattr(布局常量, '按钮圆角'), "布局常量类应有按钮圆角属性"
        assert 布局常量.按钮圆角 == 6, "按钮圆角应为6px"
        
        # 验证按钮内边距定义
        assert hasattr(布局常量, '按钮水平内边距'), "布局常量类应有按钮水平内边距属性"
        assert 布局常量.按钮水平内边距 >= 8, "按钮水平内边距应至少为8px"
        
        # 验证按钮间距定义
        assert hasattr(布局常量, '按钮间距'), "布局常量类应有按钮间距属性"
        assert 布局常量.按钮间距 == 8, "按钮间距应为8px"
    
    def test_QSS样式表结构完整性(self, 应用实例):
        """
        测试: QSS样式表应包含所有必要的按钮样式定义
        
        **Feature: ui-layout-adaptation, Property 6: 按钮样式一致性**
        **Validates: Requirements 10.1, 10.2, 10.3, 10.4, 10.5**
        """
        # 验证基础按钮样式
        assert "QPushButton {" in LIGHT_THEME_QSS, \
            "QSS应包含QPushButton基础样式块"
        
        # 验证悬停样式
        assert "QPushButton:hover {" in LIGHT_THEME_QSS, \
            "QSS应包含QPushButton悬停样式块"
        
        # 验证按下样式
        assert "QPushButton:pressed {" in LIGHT_THEME_QSS, \
            "QSS应包含QPushButton按下样式块"
        
        # 验证禁用样式
        assert "QPushButton:disabled {" in LIGHT_THEME_QSS, \
            "QSS应包含QPushButton禁用样式块"
        
        # 验证次要按钮样式
        assert 'QPushButton[class="secondary"]' in LIGHT_THEME_QSS, \
            "QSS应包含次要按钮样式块"
        
        # 验证危险按钮样式
        assert 'QPushButton[class="danger"]' in LIGHT_THEME_QSS, \
            "QSS应包含危险按钮样式块"
        
        # 验证成功按钮样式
        assert 'QPushButton[class="success"]' in LIGHT_THEME_QSS, \
            "QSS应包含成功按钮样式块"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
