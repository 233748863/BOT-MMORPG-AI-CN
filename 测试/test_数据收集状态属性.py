# -*- coding: utf-8 -*-
"""
数据收集状态属性测试模块

使用Hypothesis进行属性测试，验证数据收集状态显示一致性。

**Property 2: 数据收集状态显示一致性**
*对于任意* 数据收集过程中的状态变化，Status_Monitor显示的录制状态、
样本数量和文件编号应与实际数据收集状态一致

**Validates: Requirements 2.2, 2.3**
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


@pytest.fixture(scope="module")
def 应用实例():
    """创建QApplication实例（整个模块共享）"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def 数据收集页(应用实例):
    """创建数据收集页面实例"""
    from 界面.页面.数据收集页 import 数据收集页
    页面 = 数据收集页()
    yield 页面
    页面.close()


@pytest.fixture
def 状态监控组件(应用实例):
    """创建状态监控组件实例"""
    from 界面.页面.数据收集页 import 状态监控
    组件 = 状态监控()
    yield 组件
    组件.close()


class Test数据收集状态属性测试:
    """
    数据收集状态属性测试类
    
    **Feature: modern-ui, Property 2: 数据收集状态显示一致性**
    **Validates: Requirements 2.2, 2.3**
    """
    
    @given(样本数量=st.integers(min_value=0, max_value=100000))
    @settings(max_examples=100, deadline=None)
    def test_样本数量显示一致性(self, 应用实例, 样本数量):
        """
        属性测试: 对于任意样本数量，更新后显示应与输入一致
        
        **Feature: modern-ui, Property 2: 数据收集状态显示一致性**
        **Validates: Requirements 2.3**
        """
        from 界面.页面.数据收集页 import 状态监控
        
        # 创建状态监控组件
        组件 = 状态监控()
        
        try:
            # 更新样本数量
            组件.更新样本数量(样本数量)
            
            # 验证显示的样本数量与输入一致
            显示文本 = 组件._样本数量标签.text()
            assert 显示文本 == str(样本数量), \
                f"样本数量显示应为'{样本数量}'，实际为'{显示文本}'"
        finally:
            组件.close()
    
    @given(文件编号=st.integers(min_value=1, max_value=10000))
    @settings(max_examples=100, deadline=None)
    def test_文件编号显示一致性(self, 应用实例, 文件编号):
        """
        属性测试: 对于任意文件编号，更新后显示应与输入一致
        
        **Feature: modern-ui, Property 2: 数据收集状态显示一致性**
        **Validates: Requirements 2.3**
        """
        from 界面.页面.数据收集页 import 状态监控
        
        # 创建状态监控组件
        组件 = 状态监控()
        
        try:
            # 更新文件编号
            组件.更新文件编号(文件编号)
            
            # 验证显示的文件编号与输入一致
            显示文本 = 组件._文件编号标签.text()
            assert 显示文本 == str(文件编号), \
                f"文件编号显示应为'{文件编号}'，实际为'{显示文本}'"
        finally:
            组件.close()
    
    @given(录制状态=st.sampled_from(["录制中", "已暂停", "已停止", "倒计时"]))
    @settings(max_examples=100, deadline=None)
    def test_录制状态显示一致性(self, 应用实例, 录制状态):
        """
        属性测试: 对于任意录制状态，更新后显示应与输入一致
        
        **Feature: modern-ui, Property 2: 数据收集状态显示一致性**
        **Validates: Requirements 2.2**
        """
        from 界面.页面.数据收集页 import 状态监控
        
        # 创建状态监控组件
        组件 = 状态监控()
        
        try:
            # 更新录制状态
            组件.更新录制状态(录制状态)
            
            # 验证显示的录制状态与输入一致
            显示文本 = 组件._录制状态标签.text()
            assert 显示文本 == 录制状态, \
                f"录制状态显示应为'{录制状态}'，实际为'{显示文本}'"
        finally:
            组件.close()
    
    @given(
        样本数量=st.integers(min_value=0, max_value=100000),
        文件编号=st.integers(min_value=1, max_value=10000),
        帧率=st.floats(min_value=0.0, max_value=120.0, allow_nan=False, allow_infinity=False),
        当前动作=st.text(min_size=0, max_size=50)
    )
    @settings(max_examples=100, deadline=None)
    def test_状态数据更新一致性(self, 应用实例, 样本数量, 文件编号, 帧率, 当前动作):
        """
        属性测试: 对于任意状态数据组合，通过更新状态方法更新后，各字段显示应一致
        
        **Feature: modern-ui, Property 2: 数据收集状态显示一致性**
        **Validates: Requirements 2.2, 2.3**
        """
        from 界面.页面.数据收集页 import 数据收集页
        
        # 创建数据收集页面
        页面 = 数据收集页()
        
        try:
            # 构造状态数据
            状态数据 = {
                "样本数量": 样本数量,
                "文件编号": 文件编号,
                "帧率": 帧率,
                "当前动作": 当前动作,
            }
            
            # 更新状态
            页面.更新状态(状态数据)
            
            # 验证各字段显示一致
            assert 页面._状态监控._样本数量标签.text() == str(样本数量), \
                f"样本数量显示不一致: 期望'{样本数量}'，实际'{页面._状态监控._样本数量标签.text()}'"
            
            assert 页面._状态监控._文件编号标签.text() == str(文件编号), \
                f"文件编号显示不一致: 期望'{文件编号}'，实际'{页面._状态监控._文件编号标签.text()}'"
            
            assert 页面._状态监控._帧率标签.text() == f"{帧率:.1f} FPS", \
                f"帧率显示不一致: 期望'{帧率:.1f} FPS'，实际'{页面._状态监控._帧率标签.text()}'"
            
            assert 页面._状态监控._当前动作标签.text() == 当前动作, \
                f"当前动作显示不一致: 期望'{当前动作}'，实际'{页面._状态监控._当前动作标签.text()}'"
        finally:
            页面.close()
    
    @given(
        状态序列=st.lists(
            st.tuples(
                st.integers(min_value=0, max_value=10000),  # 样本数量
                st.integers(min_value=1, max_value=100)     # 文件编号
            ),
            min_size=2,
            max_size=20
        )
    )
    @settings(max_examples=100, deadline=None)
    def test_连续状态更新一致性(self, 应用实例, 状态序列):
        """
        属性测试: 对于任意状态更新序列，每次更新后显示应与最新状态一致
        
        **Feature: modern-ui, Property 2: 数据收集状态显示一致性**
        **Validates: Requirements 2.2, 2.3**
        """
        from 界面.页面.数据收集页 import 数据收集页
        
        # 创建数据收集页面
        页面 = 数据收集页()
        
        try:
            for 样本数量, 文件编号 in 状态序列:
                # 更新状态
                状态数据 = {
                    "样本数量": 样本数量,
                    "文件编号": 文件编号,
                }
                页面.更新状态(状态数据)
                
                # 验证每次更新后显示与最新状态一致
                assert 页面._状态监控._样本数量标签.text() == str(样本数量), \
                    f"连续更新后样本数量显示不一致"
                assert 页面._状态监控._文件编号标签.text() == str(文件编号), \
                    f"连续更新后文件编号显示不一致"
        finally:
            页面.close()
    
    def test_初始状态正确(self, 数据收集页):
        """
        测试: 数据收集页面初始状态应正确
        
        **Feature: modern-ui, Property 2: 数据收集状态显示一致性**
        **Validates: Requirements 2.2**
        """
        # 验证初始录制状态
        assert 数据收集页.是否录制中() == False, "初始状态应为未录制"
        assert 数据收集页.是否已暂停() == False, "初始状态应为未暂停"
        
        # 验证初始显示
        assert 数据收集页._状态监控._录制状态标签.text() == "已停止", \
            "初始录制状态显示应为'已停止'"
        assert 数据收集页._状态监控._样本数量标签.text() == "0", \
            "初始样本数量显示应为'0'"
        assert 数据收集页._状态监控._文件编号标签.text() == "1", \
            "初始文件编号显示应为'1'"
    
    def test_部分状态更新不影响其他字段(self, 数据收集页):
        """
        测试: 部分状态更新不应影响其他字段的显示
        
        **Feature: modern-ui, Property 2: 数据收集状态显示一致性**
        **Validates: Requirements 2.2, 2.3**
        """
        # 先设置初始状态
        初始状态 = {
            "样本数量": 100,
            "文件编号": 5,
            "帧率": 30.0,
            "当前动作": "前进",
        }
        数据收集页.更新状态(初始状态)
        
        # 只更新样本数量
        数据收集页.更新状态({"样本数量": 200})
        
        # 验证样本数量已更新
        assert 数据收集页._状态监控._样本数量标签.text() == "200"
        
        # 验证其他字段未受影响
        assert 数据收集页._状态监控._文件编号标签.text() == "5"
        assert 数据收集页._状态监控._帧率标签.text() == "30.0 FPS"
        assert 数据收集页._状态监控._当前动作标签.text() == "前进"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
