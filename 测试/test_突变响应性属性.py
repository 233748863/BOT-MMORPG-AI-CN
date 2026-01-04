"""
突变响应性属性测试模块

使用 Hypothesis 进行属性测试，验证平滑器的突变响应性。

**属性 3: 突变响应性**
*对于任意* 血量显著变化（>10%），检测器应在下一帧立即反映

验证: 需求 4.3
"""

import pytest
import numpy as np
from hypothesis import given, strategies as st, settings, assume
from typing import List, Tuple

from 核心.状态检测 import 平滑器


# ==================== 策略定义 ====================

@st.composite
def 有效平滑值(draw):
    """生成有效的平滑输入值 [0.0, 1.0]"""
    return draw(st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False))


@st.composite
def 突变值对(draw, 最小变化: float = 0.15):
    """
    生成突变值对（变化超过突变阈值）
    
    参数:
        最小变化: 最小变化量，默认 0.15（超过默认阈值 0.1）
    
    返回:
        (初始值, 突变后值) 元组
    """
    # 生成初始值，留出足够空间进行突变
    初始值 = draw(st.floats(min_value=0.2, max_value=0.8, allow_nan=False, allow_infinity=False))
    
    # 生成变化量，确保超过阈值
    变化量 = draw(st.floats(min_value=最小变化, max_value=0.5, allow_nan=False, allow_infinity=False))
    
    # 随机选择增加或减少
    方向 = draw(st.sampled_from([1, -1]))
    
    突变值 = 初始值 + 方向 * 变化量
    # 确保在有效范围内
    突变值 = max(0.0, min(1.0, 突变值))
    
    # 确保实际变化超过阈值
    assume(abs(突变值 - 初始值) > 0.1)
    
    return (初始值, 突变值)


@st.composite
def 稳定后突变序列(draw):
    """
    生成先稳定后突变的值序列
    
    返回:
        (稳定值列表, 突变值) 元组
    """
    # 生成稳定值
    稳定值 = draw(st.floats(min_value=0.2, max_value=0.8, allow_nan=False, allow_infinity=False))
    稳定帧数 = draw(st.integers(min_value=5, max_value=10))
    
    # 生成小幅波动的稳定序列
    稳定序列 = []
    for _ in range(稳定帧数):
        波动 = draw(st.floats(min_value=-0.02, max_value=0.02, allow_nan=False, allow_infinity=False))
        值 = max(0.0, min(1.0, 稳定值 + 波动))
        稳定序列.append(值)
    
    # 生成突变值
    变化量 = draw(st.floats(min_value=0.15, max_value=0.5, allow_nan=False, allow_infinity=False))
    方向 = draw(st.sampled_from([1, -1]))
    突变值 = 稳定值 + 方向 * 变化量
    突变值 = max(0.0, min(1.0, 突变值))
    
    # 确保突变足够大
    assume(abs(突变值 - 稳定值) > 0.1)
    
    return (稳定序列, 突变值)


# ==================== 属性 3: 突变响应性 ====================

class Test突变响应性属性:
    """
    属性测试: 突变响应性
    
    Feature: health-mana-detection, Property 3: 突变响应性
    *对于任意* 血量显著变化（>10%），检测器应在下一帧立即反映
    
    **验证: 需求 4.3**
    """

    @settings(max_examples=100, deadline=10000)
    @given(值对=突变值对(最小变化=0.15))
    def test_突变立即反映(self, 值对: Tuple[float, float]):
        """
        属性测试: 显著变化（>10%）应在下一帧立即反映
        
        Feature: health-mana-detection, Property 3: 突变响应性
        **验证: 需求 4.3**
        """
        初始值, 突变值 = 值对
        平滑器实例 = 平滑器(窗口大小=5, 突变阈值=0.1)
        
        # 初始化平滑器
        平滑器实例.平滑(初始值)
        
        # 输入突变值
        结果 = 平滑器实例.平滑(突变值)
        
        # 突变应立即反映，结果应等于突变值
        assert 结果 == 突变值, \
            f"突变应立即反映，初始: {初始值}，突变: {突变值}，结果: {结果}"

    @settings(max_examples=100, deadline=10000)
    @given(数据=稳定后突变序列())
    def test_稳定后突变立即响应(self, 数据: Tuple[List[float], float]):
        """
        属性测试: 经过稳定期后的突变应立即响应
        
        Feature: health-mana-detection, Property 3: 突变响应性
        **验证: 需求 4.3**
        """
        稳定序列, 突变值 = 数据
        平滑器实例 = 平滑器(窗口大小=5, 突变阈值=0.1)
        
        # 输入稳定序列
        for 值 in 稳定序列:
            平滑器实例.平滑(值)
        
        # 获取稳定后的输出值
        稳定输出 = 平滑器实例.获取上次值()
        
        # 输入突变值
        结果 = 平滑器实例.平滑(突变值)
        
        # 突变应立即反映
        assert 结果 == 突变值, \
            f"稳定后突变应立即反映，稳定输出: {稳定输出}，突变: {突变值}，结果: {结果}"

    @settings(max_examples=100, deadline=10000)
    @given(
        初始值=st.floats(min_value=0.6, max_value=0.9, allow_nan=False, allow_infinity=False),
        低血量=st.floats(min_value=0.0, max_value=0.3, allow_nan=False, allow_infinity=False)
    )
    def test_血量骤降立即响应(self, 初始值: float, 低血量: float):
        """
        属性测试: 血量骤降（如受到大伤害）应立即响应
        
        Feature: health-mana-detection, Property 3: 突变响应性
        **验证: 需求 4.3**
        """
        # 确保变化超过阈值
        assume(初始值 - 低血量 > 0.1)
        
        平滑器实例 = 平滑器(窗口大小=5, 突变阈值=0.1)
        
        # 模拟正常血量
        for _ in range(5):
            平滑器实例.平滑(初始值)
        
        # 血量骤降
        结果 = 平滑器实例.平滑(低血量)
        
        # 应立即反映低血量
        assert 结果 == 低血量, \
            f"血量骤降应立即反映，从 {初始值} 降到 {低血量}，结果: {结果}"

    @settings(max_examples=100, deadline=10000)
    @given(
        初始值=st.floats(min_value=0.1, max_value=0.4, allow_nan=False, allow_infinity=False),
        恢复值=st.floats(min_value=0.7, max_value=1.0, allow_nan=False, allow_infinity=False)
    )
    def test_血量恢复立即响应(self, 初始值: float, 恢复值: float):
        """
        属性测试: 血量恢复（如使用药水）应立即响应
        
        Feature: health-mana-detection, Property 3: 突变响应性
        **验证: 需求 4.3**
        """
        # 确保变化超过阈值
        assume(恢复值 - 初始值 > 0.1)
        
        平滑器实例 = 平滑器(窗口大小=5, 突变阈值=0.1)
        
        # 模拟低血量
        for _ in range(5):
            平滑器实例.平滑(初始值)
        
        # 血量恢复
        结果 = 平滑器实例.平滑(恢复值)
        
        # 应立即反映恢复后的血量
        assert 结果 == 恢复值, \
            f"血量恢复应立即反映，从 {初始值} 恢复到 {恢复值}，结果: {结果}"

    @settings(max_examples=100, deadline=10000)
    @given(
        窗口大小=st.integers(min_value=2, max_value=15),
        突变阈值=st.floats(min_value=0.05, max_value=0.3, allow_nan=False, allow_infinity=False)
    )
    def test_不同配置下突变响应(self, 窗口大小: int, 突变阈值: float):
        """
        属性测试: 不同平滑器配置下突变应立即响应
        
        Feature: health-mana-detection, Property 3: 突变响应性
        **验证: 需求 4.3**
        """
        平滑器实例 = 平滑器(窗口大小=窗口大小, 突变阈值=突变阈值)
        
        初始值 = 0.5
        # 生成超过阈值的变化
        变化量 = 突变阈值 + 0.1
        突变值 = min(1.0, 初始值 + 变化量)
        
        # 初始化
        for _ in range(窗口大小):
            平滑器实例.平滑(初始值)
        
        # 突变
        结果 = 平滑器实例.平滑(突变值)
        
        # 应立即反映
        assert 结果 == 突变值, \
            f"配置({窗口大小}, {突变阈值})下突变应立即反映，结果: {结果}"

    @settings(max_examples=100, deadline=10000)
    @given(值对=突变值对(最小变化=0.15))
    def test_突变检测方法正确(self, 值对: Tuple[float, float]):
        """
        属性测试: 是否突变方法应正确检测显著变化
        
        Feature: health-mana-detection, Property 3: 突变响应性
        **验证: 需求 4.3**
        """
        初始值, 突变值 = 值对
        平滑器实例 = 平滑器(窗口大小=5, 突变阈值=0.1)
        
        # 初始化
        平滑器实例.平滑(初始值)
        
        # 检测是否为突变
        是突变 = 平滑器实例.是否突变(突变值)
        
        assert 是突变, \
            f"变化 {abs(突变值 - 初始值):.3f} 超过阈值 0.1，应检测为突变"

    @settings(max_examples=100, deadline=10000)
    @given(
        初始值=st.floats(min_value=0.3, max_value=0.7, allow_nan=False, allow_infinity=False),
        突变次数=st.integers(min_value=2, max_value=5)
    )
    def test_连续突变都能响应(self, 初始值: float, 突变次数: int):
        """
        属性测试: 连续多次突变都应能立即响应
        
        Feature: health-mana-detection, Property 3: 突变响应性
        **验证: 需求 4.3**
        """
        平滑器实例 = 平滑器(窗口大小=5, 突变阈值=0.1)
        
        当前值 = 初始值
        平滑器实例.平滑(当前值)
        
        for i in range(突变次数):
            # 生成突变值（交替增减）
            if i % 2 == 0:
                新值 = min(1.0, 当前值 + 0.2)
            else:
                新值 = max(0.0, 当前值 - 0.2)
            
            # 确保是突变
            if abs(新值 - 当前值) > 0.1:
                结果 = 平滑器实例.平滑(新值)
                assert 结果 == 新值, \
                    f"第 {i+1} 次突变应立即反映，从 {当前值} 到 {新值}，结果: {结果}"
            
            当前值 = 新值


# ==================== 边界情况测试 ====================

class Test突变响应性边界情况:
    """突变响应性边界情况测试"""

    def test_恰好超过阈值的变化(self):
        """测试恰好超过阈值的变化应触发突变响应"""
        平滑器实例 = 平滑器(窗口大小=5, 突变阈值=0.1)
        
        初始值 = 0.5
        平滑器实例.平滑(初始值)
        
        # 恰好超过阈值（0.1 + 小量）
        突变值 = 初始值 + 0.101
        结果 = 平滑器实例.平滑(突变值)
        
        assert 结果 == 突变值, \
            f"恰好超过阈值的变化应触发突变响应，结果: {结果}"

    def test_恰好等于阈值的变化不触发(self):
        """测试恰好等于阈值的变化不应触发突变响应"""
        平滑器实例 = 平滑器(窗口大小=5, 突变阈值=0.1)
        
        初始值 = 0.5
        平滑器实例.平滑(初始值)
        
        # 恰好等于阈值
        新值 = 初始值 + 0.1
        是突变 = 平滑器实例.是否突变(新值)
        
        # 等于阈值不应触发（需要超过）
        assert not 是突变, \
            f"恰好等于阈值的变化不应触发突变检测"

    def test_从0到大值的突变(self):
        """测试从 0 到大值的突变"""
        平滑器实例 = 平滑器(窗口大小=5, 突变阈值=0.1)
        
        # 从 0 开始
        平滑器实例.平滑(0.0)
        
        # 突变到 0.5
        结果 = 平滑器实例.平滑(0.5)
        
        assert 结果 == 0.5, \
            f"从 0 到 0.5 的突变应立即反映，结果: {结果}"

    def test_从1到小值的突变(self):
        """测试从 1 到小值的突变"""
        平滑器实例 = 平滑器(窗口大小=5, 突变阈值=0.1)
        
        # 从 1 开始
        平滑器实例.平滑(1.0)
        
        # 突变到 0.5
        结果 = 平滑器实例.平滑(0.5)
        
        assert 结果 == 0.5, \
            f"从 1 到 0.5 的突变应立即反映，结果: {结果}"

    def test_突变后历史被清空(self):
        """测试突变后历史记录被清空"""
        平滑器实例 = 平滑器(窗口大小=5, 突变阈值=0.1)
        
        # 填充历史
        for _ in range(5):
            平滑器实例.平滑(0.5)
        
        assert 平滑器实例.历史长度 == 5, "历史应已填满"
        
        # 触发突变
        平滑器实例.平滑(0.8)
        
        # 历史应被清空并只包含新值
        assert 平滑器实例.历史长度 == 1, \
            f"突变后历史应只包含新值，实际长度: {平滑器实例.历史长度}"

    def test_突变后继续平滑正常工作(self):
        """测试突变后继续输入时平滑正常工作"""
        平滑器实例 = 平滑器(窗口大小=5, 突变阈值=0.1)
        
        # 初始化
        for _ in range(5):
            平滑器实例.平滑(0.5)
        
        # 触发突变
        平滑器实例.平滑(0.8)
        
        # 继续输入相似值，应正常平滑
        结果列表 = []
        for _ in range(5):
            结果 = 平滑器实例.平滑(0.8)
            结果列表.append(结果)
        
        # 最终应稳定在 0.8
        assert 结果列表[-1] == 0.8, \
            f"突变后继续输入相同值应稳定，结果: {结果列表[-1]}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])
