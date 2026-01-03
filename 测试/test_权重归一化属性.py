"""
权重归一化属性测试模块

使用Hypothesis进行属性测试，验证权重归一化功能。

**属性 1: 权重归一化**
*对于任意* 类别权重集合，归一化后平均权重应等于 1.0
**验证: 需求 2.3**

Feature: class-weight-balancing, Property 1: 权重归一化
"""

import pytest
import numpy as np
from hypothesis import given, strategies as st, settings, assume

from 工具.类别权重 import 权重计算器, 权重策略


# ============== 生成器策略 ==============

# 生成类别统计字典的策略
# 类别索引: 0-9, 样本数量: 1-10000
类别统计策略 = st.dictionaries(
    keys=st.integers(min_value=0, max_value=9),
    values=st.integers(min_value=1, max_value=10000),
    min_size=1,
    max_size=10
)

# 权重策略枚举
权重策略选项 = st.sampled_from([
    权重策略.逆频率,
    权重策略.平方根逆频率,
    权重策略.有效样本数
])


# ============== 属性测试 ==============

class Test权重归一化属性:
    """
    属性 1: 权重归一化
    
    *对于任意* 类别权重集合，归一化后平均权重应等于 1.0
    **验证: 需求 2.3**
    """
    
    @given(类别统计=类别统计策略, 策略=权重策略选项)
    @settings(max_examples=100, deadline=None)
    def test_归一化后平均权重为1(self, 类别统计: dict, 策略: 权重策略):
        """
        Feature: class-weight-balancing, Property 1: 权重归一化
        
        对于任意类别统计和权重策略，归一化后的平均权重应等于 1.0
        """
        # 确保至少有一个类别
        assume(len(类别统计) > 0)
        assume(all(v > 0 for v in 类别统计.values()))
        
        # 创建权重计算器
        计算器 = 权重计算器(类别统计, 策略)
        
        # 计算并归一化权重
        原始权重 = 计算器.计算权重()
        归一化权重 = 计算器.归一化权重()
        
        # 验证归一化后平均值为 1.0
        平均值 = np.mean(list(归一化权重.values()))
        
        # 使用近似相等，允许浮点误差
        assert abs(平均值 - 1.0) < 1e-6, \
            f"归一化后平均权重应为 1.0，实际为 {平均值}"
    
    @given(类别统计=类别统计策略, 策略=权重策略选项)
    @settings(max_examples=100, deadline=None)
    def test_归一化保持权重比例(self, 类别统计: dict, 策略: 权重策略):
        """
        Feature: class-weight-balancing, Property 1: 权重归一化
        
        归一化应保持各类别权重之间的相对比例
        """
        assume(len(类别统计) >= 2)
        assume(all(v > 0 for v in 类别统计.values()))
        
        计算器 = 权重计算器(类别统计, 策略)
        原始权重 = 计算器.计算权重()
        归一化权重 = 计算器.归一化权重()
        
        # 获取两个类别
        类别列表 = list(类别统计.keys())
        类别A, 类别B = 类别列表[0], 类别列表[1]
        
        # 验证比例保持不变
        if 原始权重[类别B] != 0:
            原始比例 = 原始权重[类别A] / 原始权重[类别B]
            归一化比例 = 归一化权重[类别A] / 归一化权重[类别B]
            
            assert abs(原始比例 - 归一化比例) < 1e-6, \
                f"归一化应保持权重比例，原始比例: {原始比例}, 归一化比例: {归一化比例}"
    
    @given(类别统计=类别统计策略, 策略=权重策略选项)
    @settings(max_examples=100, deadline=None)
    def test_所有权重为正数(self, 类别统计: dict, 策略: 权重策略):
        """
        Feature: class-weight-balancing, Property 1: 权重归一化
        
        所有归一化后的权重应为正数
        """
        assume(len(类别统计) > 0)
        assume(all(v > 0 for v in 类别统计.values()))
        
        计算器 = 权重计算器(类别统计, 策略)
        计算器.计算权重()
        归一化权重 = 计算器.归一化权重()
        
        for 类别, 权重 in 归一化权重.items():
            assert 权重 > 0, f"类别 {类别} 的权重应为正数，实际为 {权重}"
    
    @given(类别统计=类别统计策略, 策略=权重策略选项)
    @settings(max_examples=100, deadline=None)
    def test_稀有类别权重更高(self, 类别统计: dict, 策略: 权重策略):
        """
        Feature: class-weight-balancing, Property 1: 权重归一化
        
        样本数量较少的类别应获得较高的权重
        """
        assume(len(类别统计) >= 2)
        assume(all(v > 0 for v in 类别统计.values()))
        
        # 找出样本数量最多和最少的类别
        最大类别 = max(类别统计, key=类别统计.get)
        最小类别 = min(类别统计, key=类别统计.get)
        
        # 如果样本数量相同，跳过测试
        assume(类别统计[最大类别] > 类别统计[最小类别])
        
        计算器 = 权重计算器(类别统计, 策略)
        计算器.计算权重()
        归一化权重 = 计算器.归一化权重()
        
        # 稀有类别（样本少）应有更高权重
        assert 归一化权重[最小类别] > 归一化权重[最大类别], \
            f"稀有类别权重 ({归一化权重[最小类别]}) 应大于多数类别权重 ({归一化权重[最大类别]})"


class Test权重计算策略:
    """测试不同权重计算策略的正确性"""
    
    @given(类别统计=类别统计策略)
    @settings(max_examples=50, deadline=None)
    def test_逆频率权重公式(self, 类别统计: dict):
        """验证逆频率权重计算公式: w_i = N / (K * n_i)"""
        assume(len(类别统计) > 0)
        assume(all(v > 0 for v in 类别统计.values()))
        
        计算器 = 权重计算器(类别统计, 权重策略.逆频率)
        权重 = 计算器.计算权重()
        
        总样本数 = sum(类别统计.values())
        类别数 = len(类别统计)
        
        for 类别, 数量 in 类别统计.items():
            期望权重 = 总样本数 / (类别数 * 数量)
            assert abs(权重[类别] - 期望权重) < 1e-6, \
                f"逆频率权重计算错误: 期望 {期望权重}, 实际 {权重[类别]}"
    
    @given(类别统计=类别统计策略)
    @settings(max_examples=50, deadline=None)
    def test_平方根逆频率权重公式(self, 类别统计: dict):
        """验证平方根逆频率权重计算公式: w_i = sqrt(N / (K * n_i))"""
        assume(len(类别统计) > 0)
        assume(all(v > 0 for v in 类别统计.values()))
        
        计算器 = 权重计算器(类别统计, 权重策略.平方根逆频率)
        权重 = 计算器.计算权重()
        
        总样本数 = sum(类别统计.values())
        类别数 = len(类别统计)
        
        for 类别, 数量 in 类别统计.items():
            期望权重 = np.sqrt(总样本数 / (类别数 * 数量))
            assert abs(权重[类别] - 期望权重) < 1e-6, \
                f"平方根逆频率权重计算错误: 期望 {期望权重}, 实际 {权重[类别]}"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--hypothesis-show-statistics'])
