"""
平滑稳定性属性测试模块

使用 Hypothesis 进行属性测试，验证平滑器的稳定性。

**属性 2: 平滑稳定性**
*对于任意* 连续相似输入，平滑后输出变化应小于突变阈值

验证: 需求 4.1, 4.2
"""

import pytest
import numpy as np
from hypothesis import given, strategies as st, settings, assume
from typing import List

from 核心.状态检测 import 平滑器


# ==================== 策略定义 ====================

@st.composite
def 有效平滑值(draw):
    """生成有效的平滑输入值 [0.0, 1.0]"""
    return draw(st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False))


@st.composite
def 相似值序列(draw, 基准值=None, 最大偏差=0.05, 长度=None, 最大累积偏差=0.08):
    """
    生成相似值序列（变化小于突变阈值）
    
    参数:
        基准值: 基准值，None 则随机生成
        最大偏差: 每个值与前一个值的最大偏差
        长度: 序列长度，None 则随机生成
        最大累积偏差: 与基准值的最大累积偏差，确保不触发突变
    """
    if 长度 is None:
        长度 = draw(st.integers(min_value=3, max_value=20))
    
    if 基准值 is None:
        基准值 = draw(st.floats(min_value=0.1, max_value=0.9, allow_nan=False, allow_infinity=False))
    
    序列 = [基准值]
    当前值 = 基准值
    
    for _ in range(长度 - 1):
        # 生成小偏差
        偏差 = draw(st.floats(min_value=-最大偏差, max_value=最大偏差, allow_nan=False, allow_infinity=False))
        新值 = 当前值 + 偏差
        # 确保在有效范围内
        新值 = max(0.0, min(1.0, 新值))
        # 确保累积偏差不超过最大累积偏差（避免触发突变）
        if abs(新值 - 基准值) > 最大累积偏差:
            新值 = 基准值 + (最大累积偏差 if 新值 > 基准值 else -最大累积偏差)
        序列.append(新值)
        当前值 = 新值
    
    return 序列


@st.composite
def 平滑器配置(draw):
    """生成有效的平滑器配置"""
    窗口大小 = draw(st.integers(min_value=1, max_value=20))
    突变阈值 = draw(st.floats(min_value=0.05, max_value=0.5, allow_nan=False, allow_infinity=False))
    return (窗口大小, 突变阈值)


# ==================== 属性 2: 平滑稳定性 ====================

class Test平滑稳定性属性:
    """
    属性测试: 平滑稳定性
    
    Feature: health-mana-detection, Property 2: 平滑稳定性
    *对于任意* 连续相似输入，平滑后输出变化应小于突变阈值
    
    **验证: 需求 4.1, 4.2**
    """

    @settings(max_examples=100, deadline=10000)
    @given(值序列=相似值序列(最大偏差=0.05, 长度=10))
    def test_相似输入平滑后变化小于阈值(self, 值序列: List[float]):
        """
        属性测试: 连续相似输入时，平滑后输出变化应小于突变阈值
        
        Feature: health-mana-detection, Property 2: 平滑稳定性
        **验证: 需求 4.1, 4.2**
        """
        # 使用默认突变阈值 0.1
        平滑器实例 = 平滑器(窗口大小=5, 突变阈值=0.1)
        
        平滑结果 = []
        for 值 in 值序列:
            平滑值 = 平滑器实例.平滑(值)
            平滑结果.append(平滑值)
        
        # 检查连续平滑输出之间的变化
        for i in range(1, len(平滑结果)):
            变化 = abs(平滑结果[i] - 平滑结果[i-1])
            # 由于输入相似（变化 < 0.05），平滑后变化应小于突变阈值
            assert 变化 < 0.1, \
                f"相似输入时平滑输出变化应小于突变阈值，第 {i} 帧变化: {变化}"

    @settings(max_examples=100, deadline=10000)
    @given(
        基准值=st.floats(min_value=0.2, max_value=0.8, allow_nan=False, allow_infinity=False),
        帧数=st.integers(min_value=5, max_value=15)
    )
    def test_恒定输入平滑后稳定(self, 基准值: float, 帧数: int):
        """
        属性测试: 恒定输入时，平滑后输出应趋于稳定
        
        Feature: health-mana-detection, Property 2: 平滑稳定性
        **验证: 需求 4.1, 4.2**
        """
        平滑器实例 = 平滑器(窗口大小=5, 突变阈值=0.1)
        
        平滑结果 = []
        for _ in range(帧数):
            平滑值 = 平滑器实例.平滑(基准值)
            平滑结果.append(平滑值)
        
        # 窗口填满后，输出应等于输入
        if 帧数 >= 5:
            最后值 = 平滑结果[-1]
            assert abs(最后值 - 基准值) < 0.001, \
                f"恒定输入 {基准值} 经过 {帧数} 帧后应稳定，实际: {最后值}"

    @settings(max_examples=100, deadline=10000)
    @given(
        窗口大小=st.integers(min_value=2, max_value=10),
        突变阈值=st.floats(min_value=0.1, max_value=0.5, allow_nan=False, allow_infinity=False)
    )
    def test_不同配置下相似输入稳定性(self, 窗口大小: int, 突变阈值: float):
        """
        属性测试: 不同平滑器配置下，相似输入的平滑输出应保持稳定
        
        Feature: health-mana-detection, Property 2: 平滑稳定性
        **验证: 需求 4.1, 4.2**
        """
        平滑器实例 = 平滑器(窗口大小=窗口大小, 突变阈值=突变阈值)
        
        # 生成相似值序列，确保每帧变化远小于突变阈值
        # 使用突变阈值的 1/10 作为最大偏差，确保不会触发突变
        最大偏差 = 突变阈值 / 10
        基准值 = 0.5
        值序列 = [基准值]
        当前值 = 基准值
        
        np.random.seed(42)  # 固定种子以保证可重复性
        for _ in range(7):
            偏差 = np.random.uniform(-最大偏差, 最大偏差)
            新值 = max(0.0, min(1.0, 当前值 + 偏差))
            值序列.append(新值)
            当前值 = 新值
        
        平滑结果 = []
        for 值 in 值序列:
            平滑值 = 平滑器实例.平滑(值)
            平滑结果.append(平滑值)
        
        # 检查连续平滑输出之间的变化
        # 由于输入变化远小于突变阈值，不应触发突变
        for i in range(1, len(平滑结果)):
            变化 = abs(平滑结果[i] - 平滑结果[i-1])
            # 平滑后变化应小于突变阈值
            assert 变化 < 突变阈值, \
                f"配置({窗口大小}, {突变阈值})下，相似输入平滑变化应小于阈值，第 {i} 帧变化: {变化}"

    @settings(max_examples=100, deadline=10000)
    @given(
        窗口大小=st.integers(min_value=2, max_value=10),
        噪声幅度=st.floats(min_value=0.01, max_value=0.05, allow_nan=False, allow_infinity=False)
    )
    def test_移动平均平滑噪声(self, 窗口大小: int, 噪声幅度: float):
        """
        属性测试: 移动平均应能平滑小幅噪声
        
        Feature: health-mana-detection, Property 2: 平滑稳定性
        **验证: 需求 4.1, 4.2**
        """
        平滑器实例 = 平滑器(窗口大小=窗口大小, 突变阈值=0.1)
        
        # 生成带噪声的恒定信号
        基准值 = 0.5
        np.random.seed(42)  # 固定种子以保证可重复性
        噪声序列 = [基准值 + np.random.uniform(-噪声幅度, 噪声幅度) for _ in range(20)]
        
        平滑结果 = []
        for 值 in 噪声序列:
            平滑值 = 平滑器实例.平滑(值)
            平滑结果.append(平滑值)
        
        # 平滑后的值应更接近基准值
        # 取后半部分（窗口已填满）
        后半部分 = 平滑结果[窗口大小:]
        if len(后半部分) > 0:
            平均偏差 = np.mean([abs(v - 基准值) for v in 后半部分])
            原始偏差 = np.mean([abs(v - 基准值) for v in 噪声序列[窗口大小:]])
            
            # 平滑后偏差应小于或等于原始偏差
            assert 平均偏差 <= 原始偏差 + 0.01, \
                f"平滑后偏差 {平均偏差} 应小于原始偏差 {原始偏差}"

    @settings(max_examples=100, deadline=10000)
    @given(值序列=st.lists(有效平滑值(), min_size=5, max_size=15))
    def test_平滑输出在有效范围内(self, 值序列: List[float]):
        """
        属性测试: 平滑输出应始终在 [0.0, 1.0] 范围内
        
        Feature: health-mana-detection, Property 2: 平滑稳定性
        **验证: 需求 4.1**
        """
        平滑器实例 = 平滑器(窗口大小=5, 突变阈值=0.1)
        
        for i, 值 in enumerate(值序列):
            平滑值 = 平滑器实例.平滑(值)
            assert 0.0 <= 平滑值 <= 1.0, \
                f"第 {i+1} 帧平滑值应在 [0.0, 1.0] 范围内，实际: {平滑值}"

    @settings(max_examples=100, deadline=10000)
    @given(
        初始值=st.floats(min_value=0.3, max_value=0.7, allow_nan=False, allow_infinity=False),
        微小变化=st.floats(min_value=0.001, max_value=0.02, allow_nan=False, allow_infinity=False)
    )
    def test_微小变化不触发突变(self, 初始值: float, 微小变化: float):
        """
        属性测试: 微小变化不应触发突变响应
        
        Feature: health-mana-detection, Property 2: 平滑稳定性
        **验证: 需求 4.1, 4.2**
        """
        平滑器实例 = 平滑器(窗口大小=5, 突变阈值=0.1)
        
        # 初始化
        平滑器实例.平滑(初始值)
        
        # 微小变化
        新值 = 初始值 + 微小变化
        新值 = max(0.0, min(1.0, 新值))
        
        # 不应检测为突变
        是突变 = 平滑器实例.是否突变(新值)
        assert not 是突变, \
            f"微小变化 {微小变化} 不应触发突变检测"


# ==================== 边界情况测试 ====================

class Test平滑稳定性边界情况:
    """平滑稳定性边界情况测试"""

    def test_首次输入直接返回(self):
        """测试首次输入直接返回原值"""
        平滑器实例 = 平滑器(窗口大小=5, 突变阈值=0.1)
        
        首次值 = 0.7
        结果 = 平滑器实例.平滑(首次值)
        
        assert 结果 == 首次值, f"首次输入应直接返回，期望: {首次值}，实际: {结果}"

    def test_窗口大小为1时无平滑(self):
        """测试窗口大小为 1 时无平滑效果"""
        平滑器实例 = 平滑器(窗口大小=1, 突变阈值=0.1)
        
        值序列 = [0.5, 0.6, 0.55, 0.58]
        for 值 in 值序列:
            结果 = 平滑器实例.平滑(值)
            assert 结果 == 值, f"窗口大小为 1 时应直接返回输入值"

    def test_重置后状态清空(self):
        """测试重置后平滑器状态清空"""
        平滑器实例 = 平滑器(窗口大小=5, 突变阈值=0.1)
        
        # 添加一些值
        for 值 in [0.5, 0.6, 0.55]:
            平滑器实例.平滑(值)
        
        # 重置
        平滑器实例.重置()
        
        # 验证状态已清空
        assert 平滑器实例.历史长度 == 0, "重置后历史应为空"
        assert 平滑器实例.获取上次值() == 1.0, "重置后上次值应为默认值 1.0"

    def test_边界值0和1的稳定性(self):
        """测试边界值 0 和 1 的平滑稳定性"""
        平滑器实例 = 平滑器(窗口大小=5, 突变阈值=0.1)
        
        # 测试 0
        for _ in range(10):
            结果 = 平滑器实例.平滑(0.0)
        assert 结果 == 0.0, f"连续输入 0 后应稳定在 0，实际: {结果}"
        
        # 重置并测试 1
        平滑器实例.重置()
        for _ in range(10):
            结果 = 平滑器实例.平滑(1.0)
        assert 结果 == 1.0, f"连续输入 1 后应稳定在 1，实际: {结果}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])
