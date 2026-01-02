# -*- coding: utf-8 -*-
"""
训练进度属性测试模块

使用Hypothesis进行属性测试，验证训练进度显示一致性。

**Property 4: 训练进度显示一致性**
*对于任意* 训练过程中的进度更新，进度条和轮次显示应与实际训练进度一致

**Validates: Requirements 3.3**
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
def 训练页(应用实例):
    """创建训练页面实例"""
    from 界面.页面.训练页 import 训练页
    页面 = 训练页()
    yield 页面
    页面.close()


@pytest.fixture
def 进度面板(应用实例):
    """创建训练进度面板实例"""
    from 界面.页面.训练页 import 训练进度面板
    面板 = 训练进度面板()
    yield 面板
    面板.close()


class Test训练进度属性测试:
    """
    训练进度属性测试类
    
    **Feature: modern-ui, Property 4: 训练进度显示一致性**
    **Validates: Requirements 3.3**
    """
    
    @given(
        当前轮次=st.integers(min_value=0, max_value=1000),
        总轮次=st.integers(min_value=1, max_value=1000)
    )
    @settings(max_examples=100, deadline=None)
    def test_轮次显示一致性(self, 应用实例, 当前轮次, 总轮次):
        """
        属性测试: 对于任意轮次值，更新后显示应与输入一致
        
        **Feature: modern-ui, Property 4: 训练进度显示一致性**
        **Validates: Requirements 3.3**
        """
        # 确保当前轮次不超过总轮次
        assume(当前轮次 <= 总轮次)
        
        from 界面.页面.训练页 import 训练进度面板
        
        # 创建进度面板
        面板 = 训练进度面板()
        
        try:
            # 更新进度
            面板.更新进度(当前轮次, 总轮次)
            
            # 验证轮次显示与输入一致
            期望文本 = f"{当前轮次} / {总轮次}"
            实际文本 = 面板._轮次标签.text()
            assert 实际文本 == 期望文本, \
                f"轮次显示应为'{期望文本}'，实际为'{实际文本}'"
        finally:
            面板.close()
    
    @given(
        当前轮次=st.integers(min_value=0, max_value=1000),
        总轮次=st.integers(min_value=1, max_value=1000)
    )
    @settings(max_examples=100, deadline=None)
    def test_进度条值一致性(self, 应用实例, 当前轮次, 总轮次):
        """
        属性测试: 对于任意轮次值，进度条百分比应正确计算
        
        **Feature: modern-ui, Property 4: 训练进度显示一致性**
        **Validates: Requirements 3.3**
        """
        # 确保当前轮次不超过总轮次
        assume(当前轮次 <= 总轮次)
        
        from 界面.页面.训练页 import 训练进度面板
        
        # 创建进度面板
        面板 = 训练进度面板()
        
        try:
            # 更新进度
            面板.更新进度(当前轮次, 总轮次)
            
            # 计算期望的进度百分比
            期望进度 = int((当前轮次 / 总轮次) * 100) if 总轮次 > 0 else 0
            实际进度 = 面板._进度条.value()
            
            assert 实际进度 == 期望进度, \
                f"进度条值应为{期望进度}%，实际为{实际进度}%"
        finally:
            面板.close()
    
    @given(损失值=st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False))
    @settings(max_examples=100, deadline=None)
    def test_损失值显示一致性(self, 应用实例, 损失值):
        """
        属性测试: 对于任意损失值，更新后显示应与输入一致（保留4位小数）
        
        **Feature: modern-ui, Property 4: 训练进度显示一致性**
        **Validates: Requirements 3.3**
        """
        from 界面.页面.训练页 import 训练进度面板
        
        # 创建进度面板
        面板 = 训练进度面板()
        
        try:
            # 更新损失值
            面板.更新损失(损失值)
            
            # 验证损失值显示与输入一致（保留4位小数）
            期望文本 = f"{损失值:.4f}"
            实际文本 = 面板._损失标签.text()
            assert 实际文本 == 期望文本, \
                f"损失值显示应为'{期望文本}'，实际为'{实际文本}'"
        finally:
            面板.close()

    
    @given(状态=st.sampled_from(["训练中", "已暂停", "已停止", "已完成", "未开始", "准备中"]))
    @settings(max_examples=100, deadline=None)
    def test_训练状态显示一致性(self, 应用实例, 状态):
        """
        属性测试: 对于任意训练状态，更新后显示应与输入一致
        
        **Feature: modern-ui, Property 4: 训练进度显示一致性**
        **Validates: Requirements 3.3**
        """
        from 界面.页面.训练页 import 训练进度面板
        
        # 创建进度面板
        面板 = 训练进度面板()
        
        try:
            # 更新状态
            面板.更新状态(状态)
            
            # 验证状态显示与输入一致
            实际文本 = 面板._状态标签.text()
            assert 实际文本 == 状态, \
                f"训练状态显示应为'{状态}'，实际为'{实际文本}'"
        finally:
            面板.close()
    
    @given(
        当前轮次=st.integers(min_value=1, max_value=100),
        总轮次=st.integers(min_value=1, max_value=100),
        损失值=st.floats(min_value=0.0, max_value=10.0, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100, deadline=None)
    def test_训练页面进度更新一致性(self, 应用实例, 当前轮次, 总轮次, 损失值):
        """
        属性测试: 对于任意进度更新，通过训练页面更新后，各字段显示应一致
        
        **Feature: modern-ui, Property 4: 训练进度显示一致性**
        **Validates: Requirements 3.3**
        """
        # 确保当前轮次不超过总轮次
        assume(当前轮次 <= 总轮次)
        
        from 界面.页面.训练页 import 训练页
        
        # 创建训练页面
        页面 = 训练页()
        
        try:
            # 通过训练页面更新进度
            页面.更新训练进度(当前轮次, 总轮次, 损失值)
            
            # 获取进度面板
            进度面板 = 页面.获取进度面板()
            
            # 验证轮次显示
            期望轮次文本 = f"{当前轮次} / {总轮次}"
            实际轮次文本 = 进度面板._轮次标签.text()
            assert 实际轮次文本 == 期望轮次文本, \
                f"轮次显示不一致: 期望'{期望轮次文本}'，实际'{实际轮次文本}'"
            
            # 验证损失值显示
            期望损失文本 = f"{损失值:.4f}"
            实际损失文本 = 进度面板._损失标签.text()
            assert 实际损失文本 == 期望损失文本, \
                f"损失值显示不一致: 期望'{期望损失文本}'，实际'{实际损失文本}'"
            
            # 验证进度条值
            期望进度 = int((当前轮次 / 总轮次) * 100) if 总轮次 > 0 else 0
            实际进度 = 进度面板._进度条.value()
            assert 实际进度 == 期望进度, \
                f"进度条值不一致: 期望{期望进度}%，实际{实际进度}%"
            
            # 验证状态显示为"训练中"
            实际状态 = 进度面板._状态标签.text()
            assert 实际状态 == "训练中", \
                f"训练状态应为'训练中'，实际为'{实际状态}'"
        finally:
            页面.close()
    
    @given(
        进度序列=st.lists(
            st.tuples(
                st.integers(min_value=1, max_value=100),  # 当前轮次
                st.integers(min_value=1, max_value=100),  # 总轮次
                st.floats(min_value=0.0, max_value=10.0, allow_nan=False, allow_infinity=False)  # 损失值
            ),
            min_size=2,
            max_size=20
        )
    )
    @settings(max_examples=100, deadline=None)
    def test_连续进度更新一致性(self, 应用实例, 进度序列):
        """
        属性测试: 对于任意进度更新序列，每次更新后显示应与最新进度一致
        
        **Feature: modern-ui, Property 4: 训练进度显示一致性**
        **Validates: Requirements 3.3**
        """
        from 界面.页面.训练页 import 训练页
        
        # 创建训练页面
        页面 = 训练页()
        
        try:
            for 当前轮次, 总轮次, 损失值 in 进度序列:
                # 确保当前轮次不超过总轮次
                if 当前轮次 > 总轮次:
                    当前轮次 = 总轮次
                
                # 更新进度
                页面.更新训练进度(当前轮次, 总轮次, 损失值)
                
                # 获取进度面板
                进度面板 = 页面.获取进度面板()
                
                # 验证每次更新后显示与最新进度一致
                期望轮次文本 = f"{当前轮次} / {总轮次}"
                assert 进度面板._轮次标签.text() == 期望轮次文本, \
                    f"连续更新后轮次显示不一致"
                
                期望损失文本 = f"{损失值:.4f}"
                assert 进度面板._损失标签.text() == 期望损失文本, \
                    f"连续更新后损失值显示不一致"
        finally:
            页面.close()
    
    def test_初始状态正确(self, 进度面板):
        """
        测试: 训练进度面板初始状态应正确
        
        **Feature: modern-ui, Property 4: 训练进度显示一致性**
        **Validates: Requirements 3.3**
        """
        # 验证初始进度条值
        assert 进度面板._进度条.value() == 0, "初始进度条值应为0"
        
        # 验证初始轮次显示
        assert 进度面板._轮次标签.text() == "0 / 0", \
            "初始轮次显示应为'0 / 0'"
        
        # 验证初始损失值显示
        assert 进度面板._损失标签.text() == "0.0000", \
            "初始损失值显示应为'0.0000'"
        
        # 验证初始状态显示
        assert 进度面板._状态标签.text() == "未开始", \
            "初始训练状态显示应为'未开始'"
        
        # 验证初始剩余时间显示
        assert 进度面板._剩余时间标签.text() == "--:--", \
            "初始剩余时间显示应为'--:--'"
    
    def test_重置功能(self, 进度面板):
        """
        测试: 重置后进度面板应恢复初始状态
        
        **Feature: modern-ui, Property 4: 训练进度显示一致性**
        **Validates: Requirements 3.3**
        """
        # 先设置一些值
        进度面板.更新进度(50, 100)
        进度面板.更新损失(0.5678)
        进度面板.更新状态("训练中")
        进度面板.更新剩余时间("05:30")
        
        # 重置
        进度面板.重置()
        
        # 验证重置后的状态
        assert 进度面板._进度条.value() == 0, "重置后进度条值应为0"
        assert 进度面板._轮次标签.text() == "0 / 0", "重置后轮次显示应为'0 / 0'"
        assert 进度面板._损失标签.text() == "0.0000", "重置后损失值显示应为'0.0000'"
        assert 进度面板._状态标签.text() == "未开始", "重置后训练状态显示应为'未开始'"
        assert 进度面板._剩余时间标签.text() == "--:--", "重置后剩余时间显示应为'--:--'"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
