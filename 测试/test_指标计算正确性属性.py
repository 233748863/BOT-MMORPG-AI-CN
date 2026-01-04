"""
模型评估指标计算正确性属性测试
使用hypothesis进行属性测试，验证评估指标的数学正确性

Property 1: 指标计算正确性
*对于任意* 混淆矩阵，计算的指标应满足数学定义

**Validates: Requirements 1.1, 1.2, 1.3, 1.4**
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import numpy as np
from hypothesis import given, strategies as st, settings, assume

from 工具.模型评估 import 模型评估器, 评估结果, 类别指标


# ==================== 策略定义 ====================

# 类别数量策略 (2-10个类别)
类别数量策略 = st.integers(min_value=2, max_value=10)

# 样本数量策略 (每个类别10-100个样本)
样本数量策略 = st.integers(min_value=10, max_value=100)


def 生成混淆矩阵策略(类别数: int):
    """生成随机混淆矩阵的策略"""
    return st.lists(
        st.lists(
            st.integers(min_value=0, max_value=50),
            min_size=类别数,
            max_size=类别数
        ),
        min_size=类别数,
        max_size=类别数
    )


# 预测和真实标签策略
def 生成预测真实对策略(类别数: int, 样本数: int):
    """生成预测和真实标签对的策略"""
    return st.tuples(
        st.lists(st.integers(min_value=0, max_value=类别数-1), min_size=样本数, max_size=样本数),
        st.lists(st.integers(min_value=0, max_value=类别数-1), min_size=样本数, max_size=样本数)
    )


# ==================== Property 1: 指标计算正确性 ====================

class Test指标计算正确性属性:
    """
    Property 1: 指标计算正确性
    
    *对于任意* 混淆矩阵，计算的精确率、召回率和 F1 分数应满足数学定义
    
    **Validates: Requirements 1.1, 1.2, 1.3, 1.4**
    """
    
    @given(类别数=类别数量策略)
    @settings(max_examples=100)
    def test_准确率范围有效(self, 类别数: int):
        """
        **Feature: model-evaluation-tools, Property 1: 指标计算正确性**
        
        对于任意混淆矩阵，总体准确率应在 [0, 1] 范围内
        **Validates: Requirements 1.1**
        """
        # 生成随机混淆矩阵
        混淆矩阵 = np.random.randint(0, 50, size=(类别数, 类别数))
        
        # 确保至少有一个样本
        assume(np.sum(混淆矩阵) > 0)
        
        动作定义 = {i: f"动作{i}" for i in range(类别数)}
        评估器 = 模型评估器(动作定义=动作定义)
        
        结果 = 评估器.计算指标(混淆矩阵)
        
        assert 0.0 <= 结果.总体准确率 <= 1.0, \
            f"准确率 {结果.总体准确率} 应在 [0, 1] 范围内"
    
    @given(类别数=类别数量策略)
    @settings(max_examples=100)
    def test_准确率计算公式正确(self, 类别数: int):
        """
        **Feature: model-evaluation-tools, Property 1: 指标计算正确性**
        
        准确率应等于对角线元素之和除以总样本数
        **Validates: Requirements 1.1**
        """
        混淆矩阵 = np.random.randint(0, 50, size=(类别数, 类别数))
        
        总样本数 = np.sum(混淆矩阵)
        assume(总样本数 > 0)
        
        动作定义 = {i: f"动作{i}" for i in range(类别数)}
        评估器 = 模型评估器(动作定义=动作定义)
        
        结果 = 评估器.计算指标(混淆矩阵)
        
        # 手动计算准确率
        期望准确率 = np.trace(混淆矩阵) / 总样本数
        
        assert abs(结果.总体准确率 - 期望准确率) < 1e-10, \
            f"准确率 {结果.总体准确率} 应等于 {期望准确率}"
    
    @given(类别数=类别数量策略)
    @settings(max_examples=100)
    def test_精确率范围有效(self, 类别数: int):
        """
        **Feature: model-evaluation-tools, Property 1: 指标计算正确性**
        
        对于任意混淆矩阵，每个类别的精确率应在 [0, 1] 范围内
        **Validates: Requirements 1.2**
        """
        混淆矩阵 = np.random.randint(0, 50, size=(类别数, 类别数))
        
        动作定义 = {i: f"动作{i}" for i in range(类别数)}
        评估器 = 模型评估器(动作定义=动作定义)
        
        结果 = 评估器.计算指标(混淆矩阵)
        
        for 类别名, 指标 in 结果.类别指标.items():
            assert 0.0 <= 指标.精确率 <= 1.0, \
                f"类别 {类别名} 的精确率 {指标.精确率} 应在 [0, 1] 范围内"
    
    @given(类别数=类别数量策略)
    @settings(max_examples=100)
    def test_精确率计算公式正确(self, 类别数: int):
        """
        **Feature: model-evaluation-tools, Property 1: 指标计算正确性**
        
        精确率应等于 TP / (TP + FP)
        **Validates: Requirements 1.2**
        """
        混淆矩阵 = np.random.randint(0, 50, size=(类别数, 类别数))
        
        动作定义 = {i: f"动作{i}" for i in range(类别数)}
        评估器 = 模型评估器(动作定义=动作定义)
        
        结果 = 评估器.计算指标(混淆矩阵)
        
        for i in range(类别数):
            类别名 = f"动作{i}"
            TP = 混淆矩阵[i, i]
            FP = np.sum(混淆矩阵[:, i]) - TP
            
            期望精确率 = TP / (TP + FP) if (TP + FP) > 0 else 0.0
            实际精确率 = 结果.类别指标[类别名].精确率
            
            assert abs(实际精确率 - 期望精确率) < 1e-10, \
                f"类别 {类别名} 的精确率 {实际精确率} 应等于 {期望精确率}"
    
    @given(类别数=类别数量策略)
    @settings(max_examples=100)
    def test_召回率范围有效(self, 类别数: int):
        """
        **Feature: model-evaluation-tools, Property 1: 指标计算正确性**
        
        对于任意混淆矩阵，每个类别的召回率应在 [0, 1] 范围内
        **Validates: Requirements 1.3**
        """
        混淆矩阵 = np.random.randint(0, 50, size=(类别数, 类别数))
        
        动作定义 = {i: f"动作{i}" for i in range(类别数)}
        评估器 = 模型评估器(动作定义=动作定义)
        
        结果 = 评估器.计算指标(混淆矩阵)
        
        for 类别名, 指标 in 结果.类别指标.items():
            assert 0.0 <= 指标.召回率 <= 1.0, \
                f"类别 {类别名} 的召回率 {指标.召回率} 应在 [0, 1] 范围内"
    
    @given(类别数=类别数量策略)
    @settings(max_examples=100)
    def test_召回率计算公式正确(self, 类别数: int):
        """
        **Feature: model-evaluation-tools, Property 1: 指标计算正确性**
        
        召回率应等于 TP / (TP + FN)
        **Validates: Requirements 1.3**
        """
        混淆矩阵 = np.random.randint(0, 50, size=(类别数, 类别数))
        
        动作定义 = {i: f"动作{i}" for i in range(类别数)}
        评估器 = 模型评估器(动作定义=动作定义)
        
        结果 = 评估器.计算指标(混淆矩阵)
        
        for i in range(类别数):
            类别名 = f"动作{i}"
            TP = 混淆矩阵[i, i]
            FN = np.sum(混淆矩阵[i, :]) - TP
            
            期望召回率 = TP / (TP + FN) if (TP + FN) > 0 else 0.0
            实际召回率 = 结果.类别指标[类别名].召回率
            
            assert abs(实际召回率 - 期望召回率) < 1e-10, \
                f"类别 {类别名} 的召回率 {实际召回率} 应等于 {期望召回率}"
    
    @given(类别数=类别数量策略)
    @settings(max_examples=100)
    def test_F1分数范围有效(self, 类别数: int):
        """
        **Feature: model-evaluation-tools, Property 1: 指标计算正确性**
        
        对于任意混淆矩阵，每个类别的 F1 分数应在 [0, 1] 范围内
        **Validates: Requirements 1.4**
        """
        混淆矩阵 = np.random.randint(0, 50, size=(类别数, 类别数))
        
        动作定义 = {i: f"动作{i}" for i in range(类别数)}
        评估器 = 模型评估器(动作定义=动作定义)
        
        结果 = 评估器.计算指标(混淆矩阵)
        
        for 类别名, 指标 in 结果.类别指标.items():
            assert 0.0 <= 指标.F1分数 <= 1.0, \
                f"类别 {类别名} 的 F1 分数 {指标.F1分数} 应在 [0, 1] 范围内"
    
    @given(类别数=类别数量策略)
    @settings(max_examples=100)
    def test_F1分数计算公式正确(self, 类别数: int):
        """
        **Feature: model-evaluation-tools, Property 1: 指标计算正确性**
        
        F1 分数应等于 2 * 精确率 * 召回率 / (精确率 + 召回率)
        **Validates: Requirements 1.4**
        """
        混淆矩阵 = np.random.randint(0, 50, size=(类别数, 类别数))
        
        动作定义 = {i: f"动作{i}" for i in range(类别数)}
        评估器 = 模型评估器(动作定义=动作定义)
        
        结果 = 评估器.计算指标(混淆矩阵)
        
        for 类别名, 指标 in 结果.类别指标.items():
            精确率 = 指标.精确率
            召回率 = 指标.召回率
            
            期望F1 = 2 * 精确率 * 召回率 / (精确率 + 召回率) if (精确率 + 召回率) > 0 else 0.0
            实际F1 = 指标.F1分数
            
            assert abs(实际F1 - 期望F1) < 1e-10, \
                f"类别 {类别名} 的 F1 分数 {实际F1} 应等于 {期望F1}"
    
    @given(类别数=类别数量策略)
    @settings(max_examples=100)
    def test_宏平均计算正确(self, 类别数: int):
        """
        **Feature: model-evaluation-tools, Property 1: 指标计算正确性**
        
        宏平均应等于各类别指标的简单平均
        **Validates: Requirements 1.5**
        """
        混淆矩阵 = np.random.randint(1, 50, size=(类别数, 类别数))  # 确保每个类别有样本
        
        动作定义 = {i: f"动作{i}" for i in range(类别数)}
        评估器 = 模型评估器(动作定义=动作定义)
        
        结果 = 评估器.计算指标(混淆矩阵)
        
        # 收集有样本的类别指标
        精确率列表 = []
        召回率列表 = []
        F1列表 = []
        
        for 指标 in 结果.类别指标.values():
            if 指标.支持数 > 0:
                精确率列表.append(指标.精确率)
                召回率列表.append(指标.召回率)
                F1列表.append(指标.F1分数)
        
        if 精确率列表:
            期望宏平均精确率 = np.mean(精确率列表)
            期望宏平均召回率 = np.mean(召回率列表)
            期望宏平均F1 = np.mean(F1列表)
            
            assert abs(结果.宏平均.get('精确率', 0) - 期望宏平均精确率) < 1e-10, \
                f"宏平均精确率 {结果.宏平均.get('精确率', 0)} 应等于 {期望宏平均精确率}"
            assert abs(结果.宏平均.get('召回率', 0) - 期望宏平均召回率) < 1e-10, \
                f"宏平均召回率 {结果.宏平均.get('召回率', 0)} 应等于 {期望宏平均召回率}"
            assert abs(结果.宏平均.get('F1分数', 0) - 期望宏平均F1) < 1e-10, \
                f"宏平均 F1 {结果.宏平均.get('F1分数', 0)} 应等于 {期望宏平均F1}"
    
    @given(类别数=类别数量策略)
    @settings(max_examples=100)
    def test_加权平均计算正确(self, 类别数: int):
        """
        **Feature: model-evaluation-tools, Property 1: 指标计算正确性**
        
        加权平均应等于各类别指标按支持数加权的平均
        **Validates: Requirements 1.5**
        """
        混淆矩阵 = np.random.randint(1, 50, size=(类别数, 类别数))  # 确保每个类别有样本
        
        动作定义 = {i: f"动作{i}" for i in range(类别数)}
        评估器 = 模型评估器(动作定义=动作定义)
        
        结果 = 评估器.计算指标(混淆矩阵)
        
        # 收集有样本的类别指标
        精确率列表 = []
        召回率列表 = []
        F1列表 = []
        支持数列表 = []
        
        for 指标 in 结果.类别指标.values():
            if 指标.支持数 > 0:
                精确率列表.append(指标.精确率)
                召回率列表.append(指标.召回率)
                F1列表.append(指标.F1分数)
                支持数列表.append(指标.支持数)
        
        if 支持数列表:
            总支持数 = sum(支持数列表)
            期望加权精确率 = sum(p * s for p, s in zip(精确率列表, 支持数列表)) / 总支持数
            期望加权召回率 = sum(r * s for r, s in zip(召回率列表, 支持数列表)) / 总支持数
            期望加权F1 = sum(f * s for f, s in zip(F1列表, 支持数列表)) / 总支持数
            
            assert abs(结果.加权平均.get('精确率', 0) - 期望加权精确率) < 1e-10, \
                f"加权平均精确率 {结果.加权平均.get('精确率', 0)} 应等于 {期望加权精确率}"
            assert abs(结果.加权平均.get('召回率', 0) - 期望加权召回率) < 1e-10, \
                f"加权平均召回率 {结果.加权平均.get('召回率', 0)} 应等于 {期望加权召回率}"
            assert abs(结果.加权平均.get('F1分数', 0) - 期望加权F1) < 1e-10, \
                f"加权平均 F1 {结果.加权平均.get('F1分数', 0)} 应等于 {期望加权F1}"
    
    @given(类别数=类别数量策略)
    @settings(max_examples=100)
    def test_支持数等于行和(self, 类别数: int):
        """
        **Feature: model-evaluation-tools, Property 1: 指标计算正确性**
        
        每个类别的支持数应等于混淆矩阵对应行的和（实际样本数）
        **Validates: Requirements 1.1**
        """
        混淆矩阵 = np.random.randint(0, 50, size=(类别数, 类别数))
        
        动作定义 = {i: f"动作{i}" for i in range(类别数)}
        评估器 = 模型评估器(动作定义=动作定义)
        
        结果 = 评估器.计算指标(混淆矩阵)
        
        for i in range(类别数):
            类别名 = f"动作{i}"
            期望支持数 = np.sum(混淆矩阵[i, :])
            实际支持数 = 结果.类别指标[类别名].支持数
            
            assert 实际支持数 == 期望支持数, \
                f"类别 {类别名} 的支持数 {实际支持数} 应等于 {期望支持数}"
    
    def test_完美预测准确率为1(self):
        """
        **Feature: model-evaluation-tools, Property 1: 指标计算正确性**
        
        完美预测（对角矩阵）的准确率应为 1.0
        **Validates: Requirements 1.1**
        """
        类别数 = 5
        混淆矩阵 = np.diag([10, 20, 15, 25, 30])  # 对角矩阵
        
        动作定义 = {i: f"动作{i}" for i in range(类别数)}
        评估器 = 模型评估器(动作定义=动作定义)
        
        结果 = 评估器.计算指标(混淆矩阵)
        
        assert abs(结果.总体准确率 - 1.0) < 1e-10, \
            f"完美预测的准确率应为 1.0，实际为 {结果.总体准确率}"
        
        # 所有类别的精确率、召回率、F1 都应为 1.0
        for 类别名, 指标 in 结果.类别指标.items():
            if 指标.支持数 > 0:
                assert abs(指标.精确率 - 1.0) < 1e-10, \
                    f"完美预测的类别 {类别名} 精确率应为 1.0"
                assert abs(指标.召回率 - 1.0) < 1e-10, \
                    f"完美预测的类别 {类别名} 召回率应为 1.0"
                assert abs(指标.F1分数 - 1.0) < 1e-10, \
                    f"完美预测的类别 {类别名} F1 分数应为 1.0"
    
    def test_空混淆矩阵处理(self):
        """
        **Feature: model-evaluation-tools, Property 1: 指标计算正确性**
        
        空混淆矩阵（全零）应返回零准确率
        **Validates: Requirements 1.1**
        """
        类别数 = 3
        混淆矩阵 = np.zeros((类别数, 类别数), dtype=np.int32)
        
        动作定义 = {i: f"动作{i}" for i in range(类别数)}
        评估器 = 模型评估器(动作定义=动作定义)
        
        结果 = 评估器.计算指标(混淆矩阵)
        
        assert 结果.总体准确率 == 0.0, \
            f"空混淆矩阵的准确率应为 0.0，实际为 {结果.总体准确率}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
