"""
混淆矩阵行和正确性属性测试
使用hypothesis进行属性测试，验证混淆矩阵的行和等于各类别实际样本数

Property 2: 混淆矩阵对称性
*对于任意* 预测结果，混淆矩阵行和应等于各类别实际样本数

**Validates: Requirements 2.1**
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import numpy as np
from hypothesis import given, strategies as st, settings, assume
from collections import Counter

from 工具.模型评估 import 模型评估器, 可视化器


# ==================== 策略定义 ====================

# 类别数量策略 (2-10个类别)
类别数量策略 = st.integers(min_value=2, max_value=10)

# 样本数量策略 (10-200个样本)
样本数量策略 = st.integers(min_value=10, max_value=200)


@st.composite
def 预测真实标签策略(draw, 类别数: int = None, 样本数: int = None):
    """
    生成预测和真实标签对的策略
    
    参数:
        类别数: 类别数量，None 则随机生成
        样本数: 样本数量，None 则随机生成
        
    返回:
        (预测列表, 真实列表, 类别数)
    """
    if 类别数 is None:
        类别数 = draw(st.integers(min_value=2, max_value=10))
    if 样本数 is None:
        样本数 = draw(st.integers(min_value=10, max_value=200))
    
    预测列表 = draw(st.lists(
        st.integers(min_value=0, max_value=类别数-1),
        min_size=样本数,
        max_size=样本数
    ))
    真实列表 = draw(st.lists(
        st.integers(min_value=0, max_value=类别数-1),
        min_size=样本数,
        max_size=样本数
    ))
    
    return 预测列表, 真实列表, 类别数


# ==================== Property 2: 混淆矩阵行和正确性 ====================

class Test混淆矩阵行和正确性属性:
    """
    Property 2: 混淆矩阵对称性
    
    *对于任意* 预测结果，混淆矩阵行和应等于各类别实际样本数
    
    **Validates: Requirements 2.1**
    """
    
    @given(data=st.data())
    @settings(max_examples=100)
    def test_行和等于实际样本数(self, data):
        """
        **Feature: model-evaluation-tools, Property 2: 混淆矩阵行和正确性**
        
        对于任意预测结果，混淆矩阵的每一行之和应等于该类别的实际样本数
        **Validates: Requirements 2.1**
        """
        预测列表, 真实列表, 类别数 = data.draw(预测真实标签策略())
        
        动作定义 = {i: f"动作{i}" for i in range(类别数)}
        评估器 = 模型评估器(动作定义=动作定义)
        
        混淆矩阵 = 评估器.生成混淆矩阵(预测列表, 真实列表)
        
        # 统计每个类别的实际样本数
        真实计数 = Counter(真实列表)
        
        # 验证每一行的和等于该类别的实际样本数
        for i in range(类别数):
            行和 = np.sum(混淆矩阵[i, :])
            期望样本数 = 真实计数.get(i, 0)
            
            assert 行和 == 期望样本数, \
                f"类别 {i} 的行和 {行和} 应等于实际样本数 {期望样本数}"
    
    @given(data=st.data())
    @settings(max_examples=100)
    def test_列和等于预测样本数(self, data):
        """
        **Feature: model-evaluation-tools, Property 2: 混淆矩阵行和正确性**
        
        对于任意预测结果，混淆矩阵的每一列之和应等于该类别的预测样本数
        **Validates: Requirements 2.1**
        """
        预测列表, 真实列表, 类别数 = data.draw(预测真实标签策略())
        
        动作定义 = {i: f"动作{i}" for i in range(类别数)}
        评估器 = 模型评估器(动作定义=动作定义)
        
        混淆矩阵 = 评估器.生成混淆矩阵(预测列表, 真实列表)
        
        # 统计每个类别的预测样本数
        预测计数 = Counter(预测列表)
        
        # 验证每一列的和等于该类别的预测样本数
        for j in range(类别数):
            列和 = np.sum(混淆矩阵[:, j])
            期望预测数 = 预测计数.get(j, 0)
            
            assert 列和 == 期望预测数, \
                f"类别 {j} 的列和 {列和} 应等于预测样本数 {期望预测数}"
    
    @given(data=st.data())
    @settings(max_examples=100)
    def test_总和等于样本总数(self, data):
        """
        **Feature: model-evaluation-tools, Property 2: 混淆矩阵行和正确性**
        
        对于任意预测结果，混淆矩阵的总和应等于样本总数
        **Validates: Requirements 2.1**
        """
        预测列表, 真实列表, 类别数 = data.draw(预测真实标签策略())
        
        动作定义 = {i: f"动作{i}" for i in range(类别数)}
        评估器 = 模型评估器(动作定义=动作定义)
        
        混淆矩阵 = 评估器.生成混淆矩阵(预测列表, 真实列表)
        
        总和 = np.sum(混淆矩阵)
        样本总数 = len(预测列表)
        
        assert 总和 == 样本总数, \
            f"混淆矩阵总和 {总和} 应等于样本总数 {样本总数}"
    
    @given(data=st.data())
    @settings(max_examples=100)
    def test_对角线元素为正确预测数(self, data):
        """
        **Feature: model-evaluation-tools, Property 2: 混淆矩阵行和正确性**
        
        对于任意预测结果，混淆矩阵对角线元素应等于正确预测的样本数
        **Validates: Requirements 2.1**
        """
        预测列表, 真实列表, 类别数 = data.draw(预测真实标签策略())
        
        动作定义 = {i: f"动作{i}" for i in range(类别数)}
        评估器 = 模型评估器(动作定义=动作定义)
        
        混淆矩阵 = 评估器.生成混淆矩阵(预测列表, 真实列表)
        
        # 统计每个类别的正确预测数
        for i in range(类别数):
            正确预测数 = sum(1 for p, t in zip(预测列表, 真实列表) if p == i and t == i)
            对角线值 = 混淆矩阵[i, i]
            
            assert 对角线值 == 正确预测数, \
                f"类别 {i} 的对角线值 {对角线值} 应等于正确预测数 {正确预测数}"
    
    @given(data=st.data())
    @settings(max_examples=100)
    def test_非对角线元素为错误预测数(self, data):
        """
        **Feature: model-evaluation-tools, Property 2: 混淆矩阵行和正确性**
        
        对于任意预测结果，混淆矩阵非对角线元素应等于错误预测的样本数
        **Validates: Requirements 2.1**
        """
        预测列表, 真实列表, 类别数 = data.draw(预测真实标签策略())
        
        动作定义 = {i: f"动作{i}" for i in range(类别数)}
        评估器 = 模型评估器(动作定义=动作定义)
        
        混淆矩阵 = 评估器.生成混淆矩阵(预测列表, 真实列表)
        
        # 验证非对角线元素
        for i in range(类别数):
            for j in range(类别数):
                if i != j:
                    # 统计真实为 i 但预测为 j 的样本数
                    错误预测数 = sum(1 for p, t in zip(预测列表, 真实列表) if t == i and p == j)
                    矩阵值 = 混淆矩阵[i, j]
                    
                    assert 矩阵值 == 错误预测数, \
                        f"混淆矩阵[{i},{j}] = {矩阵值} 应等于错误预测数 {错误预测数}"
    
    @given(data=st.data())
    @settings(max_examples=100)
    def test_混淆矩阵元素非负(self, data):
        """
        **Feature: model-evaluation-tools, Property 2: 混淆矩阵行和正确性**
        
        对于任意预测结果，混淆矩阵的所有元素应为非负整数
        **Validates: Requirements 2.1**
        """
        预测列表, 真实列表, 类别数 = data.draw(预测真实标签策略())
        
        动作定义 = {i: f"动作{i}" for i in range(类别数)}
        评估器 = 模型评估器(动作定义=动作定义)
        
        混淆矩阵 = 评估器.生成混淆矩阵(预测列表, 真实列表)
        
        assert np.all(混淆矩阵 >= 0), \
            f"混淆矩阵所有元素应为非负数"
        
        # 验证是整数类型
        assert np.issubdtype(混淆矩阵.dtype, np.integer), \
            f"混淆矩阵元素应为整数类型，实际为 {混淆矩阵.dtype}"
    
    @given(data=st.data())
    @settings(max_examples=100)
    def test_混淆矩阵形状正确(self, data):
        """
        **Feature: model-evaluation-tools, Property 2: 混淆矩阵行和正确性**
        
        对于任意预测结果，混淆矩阵应为方阵，大小等于类别数
        **Validates: Requirements 2.1**
        """
        预测列表, 真实列表, 类别数 = data.draw(预测真实标签策略())
        
        动作定义 = {i: f"动作{i}" for i in range(类别数)}
        评估器 = 模型评估器(动作定义=动作定义)
        
        混淆矩阵 = 评估器.生成混淆矩阵(预测列表, 真实列表)
        
        assert 混淆矩阵.shape == (类别数, 类别数), \
            f"混淆矩阵形状 {混淆矩阵.shape} 应为 ({类别数}, {类别数})"
    
    def test_空预测列表(self):
        """
        **Feature: model-evaluation-tools, Property 2: 混淆矩阵行和正确性**
        
        空预测列表应生成全零混淆矩阵
        **Validates: Requirements 2.1**
        """
        类别数 = 3
        动作定义 = {i: f"动作{i}" for i in range(类别数)}
        评估器 = 模型评估器(动作定义=动作定义)
        
        混淆矩阵 = 评估器.生成混淆矩阵([], [])
        
        assert np.sum(混淆矩阵) == 0, \
            f"空预测列表的混淆矩阵总和应为 0"
    
    def test_完美预测混淆矩阵(self):
        """
        **Feature: model-evaluation-tools, Property 2: 混淆矩阵行和正确性**
        
        完美预测应生成对角矩阵
        **Validates: Requirements 2.1**
        """
        类别数 = 4
        动作定义 = {i: f"动作{i}" for i in range(类别数)}
        评估器 = 模型评估器(动作定义=动作定义)
        
        # 完美预测：预测 == 真实
        真实列表 = [0, 0, 1, 1, 1, 2, 2, 3, 3, 3, 3]
        预测列表 = 真实列表.copy()
        
        混淆矩阵 = 评估器.生成混淆矩阵(预测列表, 真实列表)
        
        # 验证非对角线元素全为 0
        for i in range(类别数):
            for j in range(类别数):
                if i != j:
                    assert 混淆矩阵[i, j] == 0, \
                        f"完美预测的混淆矩阵[{i},{j}] 应为 0"
        
        # 验证对角线元素等于各类别样本数
        期望对角线 = [2, 3, 2, 4]
        for i in range(类别数):
            assert 混淆矩阵[i, i] == 期望对角线[i], \
                f"完美预测的混淆矩阵[{i},{i}] 应为 {期望对角线[i]}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
