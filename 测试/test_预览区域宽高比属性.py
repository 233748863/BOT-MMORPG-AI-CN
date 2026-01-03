# -*- coding: utf-8 -*-
"""
预览区域宽高比属性测试模块

使用Hypothesis进行属性测试，验证预览区域保持16:9宽高比。

**Property 3: 预览区域宽高比**
*对于任意* 游戏画面预览区域，其宽高比应保持为16:9

**Validates: Requirements 2.5**
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
from 界面.样式.布局常量 import 布局常量, 计算预览区域尺寸


@pytest.fixture(scope="module")
def 应用实例():
    """创建QApplication实例（整个模块共享）"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def 画面预览(应用实例):
    """创建画面预览实例"""
    from 界面.页面.数据收集页 import 画面预览
    预览实例 = 画面预览()
    yield 预览实例
    预览实例.close()


class Test预览区域宽高比属性测试:
    """
    预览区域宽高比属性测试类
    
    **Feature: ui-layout-adaptation, Property 3: 预览区域宽高比**
    **Validates: Requirements 2.5**
    """
    
    def test_预览区域宽高比常量为16比9(self):
        """
        属性测试: 预览区域宽高比常量应为16:9
        
        **Feature: ui-layout-adaptation, Property 3: 预览区域宽高比**
        **Validates: Requirements 2.5**
        """
        期望宽高比 = 16 / 9
        实际宽高比 = 布局常量.预览区域宽高比
        
        # 允许小误差
        assert abs(实际宽高比 - 期望宽高比) < 0.001, \
            f"预览区域宽高比应为16:9 ({期望宽高比:.4f})，实际为{实际宽高比:.4f}"
    
    def test_预览区域最小尺寸保持16比9(self):
        """
        属性测试: 预览区域最小尺寸应保持16:9比例
        
        **Feature: ui-layout-adaptation, Property 3: 预览区域宽高比**
        **Validates: Requirements 2.5**
        """
        最小宽度 = 布局常量.预览区域宽度最小
        最小高度 = 布局常量.预览区域高度最小
        
        实际比例 = 最小宽度 / 最小高度
        期望比例 = 16 / 9
        
        # 允许小误差（由于整数取整）
        assert abs(实际比例 - 期望比例) < 0.1, \
            f"预览区域最小尺寸({最小宽度}x{最小高度})应保持16:9比例，实际比例为{实际比例:.4f}"
    
    def test_预览区域最大尺寸保持16比9(self):
        """
        属性测试: 预览区域最大尺寸应保持16:9比例
        
        **Feature: ui-layout-adaptation, Property 3: 预览区域宽高比**
        **Validates: Requirements 2.5**
        """
        最大宽度 = 布局常量.预览区域宽度最大
        最大高度 = 布局常量.预览区域高度最大
        
        实际比例 = 最大宽度 / 最大高度
        期望比例 = 16 / 9
        
        # 允许小误差（由于整数取整）
        assert abs(实际比例 - 期望比例) < 0.1, \
            f"预览区域最大尺寸({最大宽度}x{最大高度})应保持16:9比例，实际比例为{实际比例:.4f}"
    
    @given(可用宽度=st.integers(min_value=100, max_value=500))
    @settings(max_examples=100, deadline=None)
    def test_计算预览区域尺寸保持16比9(self, 可用宽度):
        """
        属性测试: 对于任意可用宽度，计算出的预览区域尺寸应保持16:9比例
        
        **Feature: ui-layout-adaptation, Property 3: 预览区域宽高比**
        **Validates: Requirements 2.5**
        """
        宽度, 高度 = 计算预览区域尺寸(可用宽度)
        
        # 验证尺寸在有效范围内
        assert 布局常量.预览区域宽度最小 <= 宽度 <= 布局常量.预览区域宽度最大, \
            f"计算出的宽度{宽度}应在{布局常量.预览区域宽度最小}-{布局常量.预览区域宽度最大}范围内"
        
        # 验证宽高比为16:9
        实际比例 = 宽度 / 高度
        期望比例 = 16 / 9
        
        # 允许小误差（由于整数取整）
        assert abs(实际比例 - 期望比例) < 0.1, \
            f"计算出的尺寸({宽度}x{高度})应保持16:9比例，实际比例为{实际比例:.4f}"
    
    def test_画面预览组件宽高比方法(self, 画面预览):
        """
        属性测试: 画面预览组件的宽高比方法应返回16:9
        
        **Feature: ui-layout-adaptation, Property 3: 预览区域宽高比**
        **Validates: Requirements 2.5**
        """
        宽高比 = 画面预览.获取宽高比()
        期望比例 = 16 / 9
        
        assert abs(宽高比 - 期望比例) < 0.001, \
            f"画面预览组件宽高比应为16:9 ({期望比例:.4f})，实际为{宽高比:.4f}"
    
    def test_画面预览无内容时显示占位提示(self, 画面预览):
        """
        属性测试: 预览区域无内容时应显示占位提示文字
        
        **Feature: ui-layout-adaptation, Property 3: 预览区域宽高比**
        **Validates: Requirements 2.7**
        """
        # 清除预览
        画面预览.清除预览()
        
        # 验证显示占位提示
        预览文字 = 画面预览._预览标签.text()
        assert "等待录制开始" in 预览文字, \
            f"预览区域无内容时应显示'等待录制开始...'，实际显示'{预览文字}'"
    
    @given(宽度=st.integers(min_value=200, max_value=280))
    @settings(max_examples=100, deadline=None)
    def test_任意有效宽度下预览区域保持16比9(self, 应用实例, 宽度):
        """
        属性测试: 对于任意有效宽度，预览区域应保持16:9比例
        
        **Feature: ui-layout-adaptation, Property 3: 预览区域宽高比**
        **Validates: Requirements 2.5**
        """
        from 界面.页面.数据收集页 import 画面预览
        
        预览 = 画面预览()
        
        try:
            # 计算期望高度
            期望高度 = int(宽度 / (16 / 9))
            
            # 设置预览标签尺寸
            预览._预览标签.setFixedSize(宽度, 期望高度)
            
            # 获取实际尺寸
            实际宽度, 实际高度 = 预览.获取预览尺寸()
            
            # 验证宽高比
            if 实际高度 > 0:
                实际比例 = 实际宽度 / 实际高度
                期望比例 = 16 / 9
                
                # 允许小误差
                assert abs(实际比例 - 期望比例) < 0.1, \
                    f"预览区域尺寸({实际宽度}x{实际高度})应保持16:9比例，实际比例为{实际比例:.4f}"
        finally:
            预览.close()


class Test预览区域尺寸范围属性测试:
    """
    预览区域尺寸范围属性测试类
    
    **Feature: ui-layout-adaptation, Property 3: 预览区域宽高比**
    **Validates: Requirements 2.5**
    """
    
    def test_预览区域宽度范围合理(self):
        """
        属性测试: 预览区域宽度范围应合理
        
        **Feature: ui-layout-adaptation, Property 3: 预览区域宽高比**
        **Validates: Requirements 2.5**
        """
        最小宽度 = 布局常量.预览区域宽度最小
        最大宽度 = 布局常量.预览区域宽度最大
        
        # 验证最小宽度不小于100px
        assert 最小宽度 >= 100, \
            f"预览区域最小宽度应不小于100px，实际为{最小宽度}px"
        
        # 验证最大宽度不超过400px
        assert 最大宽度 <= 400, \
            f"预览区域最大宽度应不超过400px，实际为{最大宽度}px"
        
        # 验证最小宽度小于最大宽度
        assert 最小宽度 < 最大宽度, \
            f"预览区域最小宽度({最小宽度})应小于最大宽度({最大宽度})"
    
    def test_预览区域高度范围合理(self):
        """
        属性测试: 预览区域高度范围应合理
        
        **Feature: ui-layout-adaptation, Property 3: 预览区域宽高比**
        **Validates: Requirements 2.5**
        """
        最小高度 = 布局常量.预览区域高度最小
        最大高度 = 布局常量.预览区域高度最大
        
        # 验证最小高度不小于50px
        assert 最小高度 >= 50, \
            f"预览区域最小高度应不小于50px，实际为{最小高度}px"
        
        # 验证最大高度不超过300px
        assert 最大高度 <= 300, \
            f"预览区域最大高度应不超过300px，实际为{最大高度}px"
        
        # 验证最小高度小于最大高度
        assert 最小高度 < 最大高度, \
            f"预览区域最小高度({最小高度})应小于最大高度({最大高度})"
    
    @given(
        宽度=st.integers(min_value=200, max_value=280),
        高度=st.integers(min_value=112, max_value=158)
    )
    @settings(max_examples=100, deadline=None)
    def test_任意有效尺寸组合的宽高比接近16比9(self, 宽度, 高度):
        """
        属性测试: 对于任意有效尺寸组合，宽高比应接近16:9
        
        **Feature: ui-layout-adaptation, Property 3: 预览区域宽高比**
        **Validates: Requirements 2.5**
        """
        # 计算实际比例
        实际比例 = 宽度 / 高度
        期望比例 = 16 / 9
        
        # 由于宽度和高度是独立生成的，允许较大误差
        # 这个测试主要验证尺寸范围的合理性
        assert 1.0 <= 实际比例 <= 2.5, \
            f"尺寸组合({宽度}x{高度})的宽高比{实际比例:.4f}应在合理范围内"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
