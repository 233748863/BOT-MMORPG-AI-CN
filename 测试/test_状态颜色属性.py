# -*- coding: utf-8 -*-
"""
状态颜色属性测试模块

使用Hypothesis进行属性测试，验证状态颜色编码功能。

**Property 14: 状态颜色编码**
*对于任意* 状态类型（正常/警告/错误），应使用对应的颜色（绿色/黄色/红色）显示

**Validates: Requirements 10.6**
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


@pytest.fixture(scope="module")
def 应用实例():
    """创建QApplication实例（整个模块共享）"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def 状态监控组件(应用实例):
    """创建状态监控组件实例"""
    from 界面.组件.状态监控 import StatusMonitor
    组件 = StatusMonitor()
    # 添加一些测试用的状态项
    组件.添加状态项("测试项1", "测试标签1")
    组件.添加状态项("测试项2", "测试标签2")
    组件.添加状态项("测试项3", "测试标签3")
    yield 组件
    组件.close()


@pytest.fixture
def 状态指示器(应用实例):
    """创建状态指示器组件实例"""
    from 界面.组件.状态监控 import StatusIndicator
    组件 = StatusIndicator("测试标签")
    yield 组件
    组件.close()


class Test状态颜色属性测试:
    """
    状态颜色属性测试类
    
    **Feature: modern-ui, Property 14: 状态颜色编码**
    **Validates: Requirements 10.6**
    """

    @given(状态类型=st.sampled_from(["正常", "警告", "错误"]))
    @settings(max_examples=100, deadline=None)
    def test_状态颜色映射一致性(self, 应用实例, 状态类型):
        """
        属性测试: 对于任意状态类型，获取状态颜色函数应返回正确的颜色值
        
        **Feature: modern-ui, Property 14: 状态颜色编码**
        **Validates: Requirements 10.6**
        """
        from 界面.样式.主题 import 获取状态颜色, 颜色
        
        # 期望的颜色映射
        期望颜色映射 = {
            "正常": 颜色.成功,  # 绿色 #10B981
            "警告": 颜色.警告,  # 黄色 #F59E0B
            "错误": 颜色.错误,  # 红色 #EF4444
        }
        
        # 获取状态颜色
        实际颜色 = 获取状态颜色(状态类型)
        期望颜色 = 期望颜色映射[状态类型]
        
        assert 实际颜色 == 期望颜色, \
            f"状态类型'{状态类型}'的颜色应为'{期望颜色}'，实际为'{实际颜色}'"

    @given(状态类型=st.sampled_from(["正常", "警告", "错误"]))
    @settings(max_examples=100, deadline=None)
    def test_状态指示器颜色更新(self, 应用实例, 状态类型):
        """
        属性测试: 对于任意状态类型，状态指示器应正确更新颜色
        
        **Feature: modern-ui, Property 14: 状态颜色编码**
        **Validates: Requirements 10.6**
        """
        from 界面.组件.状态监控 import StatusIndicator
        from 界面.样式.主题 import 获取状态颜色
        
        # 创建状态指示器
        指示器 = StatusIndicator("测试")
        
        try:
            # 设置状态
            指示器.设置状态(状态类型)
            
            # 验证状态类型已正确存储
            assert 指示器.获取状态() == 状态类型, \
                f"状态类型应为'{状态类型}'，实际为'{指示器.获取状态()}'"
            
            # 验证指示点样式包含正确的颜色
            期望颜色 = 获取状态颜色(状态类型)
            样式表 = 指示器._指示点.styleSheet()
            assert 期望颜色 in 样式表, \
                f"状态指示点样式应包含颜色'{期望颜色}'，实际样式为'{样式表}'"
        finally:
            指示器.close()

    @given(状态类型=st.sampled_from(["正常", "警告", "错误"]))
    @settings(max_examples=100, deadline=None)
    def test_状态监控组件颜色更新(self, 应用实例, 状态类型):
        """
        属性测试: 对于任意状态类型，状态监控组件应正确更新状态项颜色
        
        **Feature: modern-ui, Property 14: 状态颜色编码**
        **Validates: Requirements 10.6**
        """
        from 界面.组件.状态监控 import StatusMonitor
        from 界面.样式.主题 import 获取状态颜色
        
        # 创建状态监控组件
        组件 = StatusMonitor()
        组件.添加状态项("测试键", "测试标签")
        
        try:
            # 设置状态颜色
            组件.设置状态颜色("测试键", 状态类型)
            
            # 获取状态指示器
            指示器 = 组件.获取状态项("测试键")
            assert 指示器 is not None, "状态指示器应存在"
            
            # 验证状态类型已正确存储
            assert 指示器.获取状态() == 状态类型, \
                f"状态类型应为'{状态类型}'，实际为'{指示器.获取状态()}'"
            
            # 验证指示点样式包含正确的颜色
            期望颜色 = 获取状态颜色(状态类型)
            样式表 = 指示器._指示点.styleSheet()
            assert 期望颜色 in 样式表, \
                f"状态指示点样式应包含颜色'{期望颜色}'，实际样式为'{样式表}'"
        finally:
            组件.close()

    @given(
        状态序列=st.lists(
            st.sampled_from(["正常", "警告", "错误"]),
            min_size=2,
            max_size=20
        )
    )
    @settings(max_examples=100, deadline=None)
    def test_连续状态颜色切换(self, 应用实例, 状态序列):
        """
        属性测试: 对于任意状态切换序列，每次切换后颜色应正确更新
        
        **Feature: modern-ui, Property 14: 状态颜色编码**
        **Validates: Requirements 10.6**
        """
        from 界面.组件.状态监控 import StatusIndicator
        from 界面.样式.主题 import 获取状态颜色
        
        # 创建状态指示器
        指示器 = StatusIndicator("测试")
        
        try:
            for 状态类型 in 状态序列:
                # 设置状态
                指示器.设置状态(状态类型)
                
                # 验证状态类型已正确存储
                assert 指示器.获取状态() == 状态类型, \
                    f"连续切换后状态类型应为'{状态类型}'，实际为'{指示器.获取状态()}'"
                
                # 验证指示点样式包含正确的颜色
                期望颜色 = 获取状态颜色(状态类型)
                样式表 = 指示器._指示点.styleSheet()
                assert 期望颜色 in 样式表, \
                    f"连续切换后状态指示点样式应包含颜色'{期望颜色}'"
        finally:
            指示器.close()

    @given(
        状态项数量=st.integers(min_value=1, max_value=10),
        状态类型=st.sampled_from(["正常", "警告", "错误"])
    )
    @settings(max_examples=100, deadline=None)
    def test_多状态项颜色独立性(self, 应用实例, 状态项数量, 状态类型):
        """
        属性测试: 对于任意数量的状态项，设置一个状态项的颜色不应影响其他状态项
        
        **Feature: modern-ui, Property 14: 状态颜色编码**
        **Validates: Requirements 10.6**
        """
        from 界面.组件.状态监控 import StatusMonitor
        from 界面.样式.主题 import 获取状态颜色, 颜色
        
        # 创建状态监控组件
        组件 = StatusMonitor()
        
        # 添加多个状态项
        状态项键列表 = [f"状态项{i}" for i in range(状态项数量)]
        for 键 in 状态项键列表:
            组件.添加状态项(键, f"标签{键}")
        
        try:
            # 只修改第一个状态项的颜色
            if 状态项数量 > 0:
                组件.设置状态颜色(状态项键列表[0], 状态类型)
                
                # 验证第一个状态项颜色已更新
                第一个指示器 = 组件.获取状态项(状态项键列表[0])
                assert 第一个指示器.获取状态() == 状态类型, \
                    f"第一个状态项的状态类型应为'{状态类型}'"
                
                # 验证其他状态项颜色未受影响（应保持默认的"正常"状态）
                for 键 in 状态项键列表[1:]:
                    指示器 = 组件.获取状态项(键)
                    assert 指示器.获取状态() == "正常", \
                        f"其他状态项'{键}'的状态类型应保持为'正常'，实际为'{指示器.获取状态()}'"
        finally:
            组件.close()

    def test_颜色常量正确性(self, 应用实例):
        """
        测试: 颜色常量应符合设计规范
        
        **Feature: modern-ui, Property 14: 状态颜色编码**
        **Validates: Requirements 10.6**
        """
        from 界面.样式.主题 import 颜色
        
        # 验证成功/正常状态颜色为绿色
        assert 颜色.成功 == "#10B981", \
            f"成功状态颜色应为'#10B981'（绿色），实际为'{颜色.成功}'"
        
        # 验证警告状态颜色为黄色
        assert 颜色.警告 == "#F59E0B", \
            f"警告状态颜色应为'#F59E0B'（黄色），实际为'{颜色.警告}'"
        
        # 验证错误状态颜色为红色
        assert 颜色.错误 == "#EF4444", \
            f"错误状态颜色应为'#EF4444'（红色），实际为'{颜色.错误}'"

    def test_未知状态类型处理(self, 应用实例):
        """
        测试: 对于未知状态类型，应返回默认颜色
        
        **Feature: modern-ui, Property 14: 状态颜色编码**
        **Validates: Requirements 10.6**
        """
        from 界面.样式.主题 import 获取状态颜色, 颜色
        
        # 测试未知状态类型
        未知状态列表 = ["未知", "其他", "测试", "", "invalid"]
        
        for 未知状态 in 未知状态列表:
            实际颜色 = 获取状态颜色(未知状态)
            # 未知状态应返回默认文字颜色
            assert 实际颜色 == 颜色.文字, \
                f"未知状态类型'{未知状态}'应返回默认颜色'{颜色.文字}'，实际为'{实际颜色}'"

    def test_状态指示器初始状态(self, 状态指示器):
        """
        测试: 状态指示器初始状态应为"正常"
        
        **Feature: modern-ui, Property 14: 状态颜色编码**
        **Validates: Requirements 10.6**
        """
        from 界面.样式.主题 import 颜色
        
        # 验证初始状态类型
        assert 状态指示器.获取状态() == "正常", \
            f"初始状态类型应为'正常'，实际为'{状态指示器.获取状态()}'"
        
        # 验证初始颜色为绿色
        样式表 = 状态指示器._指示点.styleSheet()
        assert 颜色.成功 in 样式表, \
            f"初始状态指示点样式应包含绿色'{颜色.成功}'"

    @given(
        值=st.text(min_size=0, max_size=50),
        状态类型=st.sampled_from(["正常", "警告", "错误"])
    )
    @settings(max_examples=100, deadline=None)
    def test_状态项更新值和颜色(self, 应用实例, 值, 状态类型):
        """
        属性测试: 对于任意值和状态类型组合，更新状态项后值和颜色应正确
        
        **Feature: modern-ui, Property 14: 状态颜色编码**
        **Validates: Requirements 10.6**
        """
        from 界面.组件.状态监控 import StatusMonitor
        from 界面.样式.主题 import 获取状态颜色
        
        # 创建状态监控组件
        组件 = StatusMonitor()
        组件.添加状态项("测试键", "测试标签")
        
        try:
            # 更新状态项（值和状态类型）
            组件.更新状态项("测试键", 值, 状态类型)
            
            # 获取状态指示器
            指示器 = 组件.获取状态项("测试键")
            
            # 验证值已正确更新
            assert 指示器._值标签.text() == 值, \
                f"状态项值应为'{值}'，实际为'{指示器._值标签.text()}'"
            
            # 验证状态类型已正确更新
            assert 指示器.获取状态() == 状态类型, \
                f"状态类型应为'{状态类型}'，实际为'{指示器.获取状态()}'"
            
            # 验证颜色已正确更新
            期望颜色 = 获取状态颜色(状态类型)
            样式表 = 指示器._指示点.styleSheet()
            assert 期望颜色 in 样式表, \
                f"状态指示点样式应包含颜色'{期望颜色}'"
        finally:
            组件.close()

    @given(
        状态数据=st.dictionaries(
            keys=st.text(min_size=1, max_size=10, alphabet="abcdefghijklmnopqrstuvwxyz"),
            values=st.tuples(
                st.text(min_size=0, max_size=20),
                st.sampled_from(["正常", "警告", "错误"])
            ),
            min_size=1,
            max_size=5
        )
    )
    @settings(max_examples=100, deadline=None)
    def test_批量状态更新颜色一致性(self, 应用实例, 状态数据):
        """
        属性测试: 对于任意批量状态数据，更新后各状态项颜色应正确
        
        **Feature: modern-ui, Property 14: 状态颜色编码**
        **Validates: Requirements 10.6**
        """
        from 界面.组件.状态监控 import StatusMonitor
        from 界面.样式.主题 import 获取状态颜色
        
        # 创建状态监控组件
        组件 = StatusMonitor()
        
        # 先添加所有状态项
        for 键 in 状态数据.keys():
            组件.添加状态项(键, f"标签{键}")
        
        try:
            # 批量更新状态
            组件.更新状态(状态数据)
            
            # 验证每个状态项的颜色
            for 键, (值, 状态类型) in 状态数据.items():
                指示器 = 组件.获取状态项(键)
                
                # 验证状态类型
                assert 指示器.获取状态() == 状态类型, \
                    f"状态项'{键}'的状态类型应为'{状态类型}'，实际为'{指示器.获取状态()}'"
                
                # 验证颜色
                期望颜色 = 获取状态颜色(状态类型)
                样式表 = 指示器._指示点.styleSheet()
                assert 期望颜色 in 样式表, \
                    f"状态项'{键}'的指示点样式应包含颜色'{期望颜色}'"
        finally:
            组件.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
