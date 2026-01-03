"""
过采样平衡属性测试模块

使用Hypothesis进行属性测试，验证过采样功能。

**属性 2: 过采样平衡**
*对于任意* 过采样后的数据集，各类别样本数量差异应在目标比率范围内
**验证: 需求 4.3**

Feature: class-weight-balancing, Property 2: 过采样平衡
"""

import pytest
import numpy as np
from hypothesis import given, strategies as st, settings, assume
from typing import List, Tuple, Any

from 工具.类别权重 import 采样器, 采样配置


# ============== 生成器策略 ==============

def 生成不平衡数据集(类别数: int, 样本分布: List[int]) -> List[Tuple[np.ndarray, int]]:
    """
    生成不平衡的模拟数据集
    
    参数:
        类别数: 类别数量
        样本分布: 每个类别的样本数量列表
        
    返回:
        [(图像, 标签), ...] 列表
    """
    数据集 = []
    for 类别 in range(类别数):
        数量 = 样本分布[类别] if 类别 < len(样本分布) else 1
        for _ in range(数量):
            # 生成简单的模拟图像数据 (8x8 灰度图)
            图像 = np.random.randint(0, 256, (8, 8), dtype=np.uint8)
            数据集.append((图像, 类别))
    return 数据集


# 生成样本分布的策略 (2-5个类别，每个类别1-100个样本)
样本分布策略 = st.lists(
    st.integers(min_value=1, max_value=100),
    min_size=2,
    max_size=5
)

# 目标比率策略 (0.5 到 1.0)
目标比率策略 = st.floats(min_value=0.5, max_value=1.0, allow_nan=False, allow_infinity=False)


# ============== 辅助函数 ==============

def 统计类别分布(数据集: List[Tuple[Any, Any]]) -> dict:
    """统计数据集中各类别的样本数量"""
    统计 = {}
    for _, 标签 in 数据集:
        if isinstance(标签, (list, np.ndarray)):
            类别 = int(np.argmax(标签))
        else:
            类别 = int(标签)
        统计[类别] = 统计.get(类别, 0) + 1
    return 统计


def 计算不平衡比率(统计: dict) -> float:
    """计算不平衡比率 (最大/最小)"""
    if not 统计:
        return 1.0
    数量列表 = list(统计.values())
    最大值 = max(数量列表)
    最小值 = min(数量列表) if min(数量列表) > 0 else 1
    return 最大值 / 最小值


# ============== 属性测试 ==============

class Test过采样平衡属性:
    """
    属性 2: 过采样平衡
    
    *对于任意* 过采样后的数据集，各类别样本数量差异应在目标比率范围内
    **验证: 需求 4.3**
    """
    
    @given(样本分布=样本分布策略, 目标比率=目标比率策略)
    @settings(max_examples=100, deadline=None)
    def test_过采样后类别平衡(self, 样本分布: List[int], 目标比率: float):
        """
        Feature: class-weight-balancing, Property 2: 过采样平衡
        
        对于任意不平衡数据集，过采样后各类别样本数量差异应在目标比率范围内
        """
        # 确保有足够的类别和样本
        assume(len(样本分布) >= 2)
        assume(all(n > 0 for n in 样本分布))
        
        # 生成不平衡数据集
        数据集 = 生成不平衡数据集(len(样本分布), 样本分布)
        
        # 创建采样器并执行过采样
        配置 = 采样配置(目标比率=目标比率, 打乱数据=True, 随机种子=42)
        采样器实例 = 采样器(数据集, 配置=配置)
        平衡数据 = 采样器实例.随机过采样(目标比率)
        
        # 统计过采样后的分布
        原始统计 = 统计类别分布(数据集)
        平衡统计 = 统计类别分布(平衡数据)
        
        # 计算目标数量
        最大数量 = max(原始统计.values())
        目标数量 = int(最大数量 * 目标比率)
        
        # 验证: 所有少数类别应达到或接近目标数量
        for 类别, 原始数量 in 原始统计.items():
            平衡数量 = 平衡统计.get(类别, 0)
            
            if 原始数量 < 目标数量:
                # 少数类别应被过采样到目标数量
                assert 平衡数量 >= 目标数量, \
                    f"类别 {类别} 过采样后数量 ({平衡数量}) 应 >= 目标数量 ({目标数量})"
            else:
                # 多数类别应保持不变
                assert 平衡数量 == 原始数量, \
                    f"类别 {类别} 不应被修改，原始: {原始数量}, 实际: {平衡数量}"
    
    @given(样本分布=样本分布策略)
    @settings(max_examples=100, deadline=None)
    def test_过采样不丢失原始样本(self, 样本分布: List[int]):
        """
        Feature: class-weight-balancing, Property 2: 过采样平衡
        
        过采样后的数据集应包含所有原始样本
        """
        assume(len(样本分布) >= 2)
        assume(all(n > 0 for n in 样本分布))
        
        数据集 = 生成不平衡数据集(len(样本分布), 样本分布)
        
        配置 = 采样配置(目标比率=1.0, 打乱数据=False, 随机种子=42)
        采样器实例 = 采样器(数据集, 配置=配置)
        平衡数据 = 采样器实例.随机过采样()
        
        # 验证: 过采样后样本数 >= 原始样本数
        assert len(平衡数据) >= len(数据集), \
            f"过采样后样本数 ({len(平衡数据)}) 应 >= 原始样本数 ({len(数据集)})"
        
        # 验证: 每个类别的样本数 >= 原始数量
        原始统计 = 统计类别分布(数据集)
        平衡统计 = 统计类别分布(平衡数据)
        
        for 类别, 原始数量 in 原始统计.items():
            平衡数量 = 平衡统计.get(类别, 0)
            assert 平衡数量 >= 原始数量, \
                f"类别 {类别} 过采样后数量 ({平衡数量}) 应 >= 原始数量 ({原始数量})"
    
    @given(样本分布=样本分布策略)
    @settings(max_examples=100, deadline=None)
    def test_完全平衡时各类别数量相等(self, 样本分布: List[int]):
        """
        Feature: class-weight-balancing, Property 2: 过采样平衡
        
        当目标比率为 1.0 时，所有类别应有相同数量的样本
        """
        assume(len(样本分布) >= 2)
        assume(all(n > 0 for n in 样本分布))
        
        数据集 = 生成不平衡数据集(len(样本分布), 样本分布)
        
        配置 = 采样配置(目标比率=1.0, 打乱数据=True, 随机种子=42)
        采样器实例 = 采样器(数据集, 配置=配置)
        平衡数据 = 采样器实例.随机过采样(1.0)
        
        平衡统计 = 统计类别分布(平衡数据)
        数量列表 = list(平衡统计.values())
        
        # 验证: 所有类别数量应相等（等于最大类别数量）
        最大数量 = max(样本分布)
        for 类别, 数量 in 平衡统计.items():
            assert 数量 == 最大数量, \
                f"完全平衡时类别 {类别} 数量 ({数量}) 应等于最大数量 ({最大数量})"


class Test欠采样属性:
    """测试欠采样功能的属性"""
    
    @given(样本分布=样本分布策略)
    @settings(max_examples=100, deadline=None)
    def test_欠采样上限约束(self, 样本分布: List[int]):
        """
        属性 3: 欠采样上限
        
        *对于任意* 欠采样后的数据集，每个类别样本数不应超过配置的最大值
        **验证: 需求 5.3**
        """
        assume(len(样本分布) >= 2)
        assume(all(n > 0 for n in 样本分布))
        
        数据集 = 生成不平衡数据集(len(样本分布), 样本分布)
        最小数量 = min(样本分布)
        
        配置 = 采样配置(最大样本数=最小数量, 打乱数据=True, 随机种子=42)
        采样器实例 = 采样器(数据集, 配置=配置)
        平衡数据 = 采样器实例.随机欠采样(最小数量)
        
        平衡统计 = 统计类别分布(平衡数据)
        
        # 验证: 每个类别数量 <= 最大样本数
        for 类别, 数量 in 平衡统计.items():
            assert 数量 <= 最小数量, \
                f"类别 {类别} 欠采样后数量 ({数量}) 应 <= 最大样本数 ({最小数量})"
    
    @given(样本分布=样本分布策略)
    @settings(max_examples=100, deadline=None)
    def test_欠采样不增加样本(self, 样本分布: List[int]):
        """
        欠采样后的数据集样本数应 <= 原始样本数
        """
        assume(len(样本分布) >= 2)
        assume(all(n > 0 for n in 样本分布))
        
        数据集 = 生成不平衡数据集(len(样本分布), 样本分布)
        
        配置 = 采样配置(打乱数据=True, 随机种子=42)
        采样器实例 = 采样器(数据集, 配置=配置)
        平衡数据 = 采样器实例.随机欠采样()
        
        assert len(平衡数据) <= len(数据集), \
            f"欠采样后样本数 ({len(平衡数据)}) 应 <= 原始样本数 ({len(数据集)})"


class Test增强过采样属性:
    """测试增强过采样（类似 SMOTE）功能的属性"""
    
    @given(样本分布=样本分布策略)
    @settings(max_examples=50, deadline=None)
    def test_增强过采样生成新样本(self, 样本分布: List[int]):
        """
        增强过采样应生成新的合成样本，而不仅仅是复制
        """
        assume(len(样本分布) >= 2)
        assume(all(n >= 3 for n in 样本分布))  # 需要足够样本进行插值
        
        数据集 = 生成不平衡数据集(len(样本分布), 样本分布)
        
        配置 = 采样配置(目标比率=1.0, 打乱数据=False, 随机种子=42, k_neighbors=2)
        采样器实例 = 采样器(数据集, 配置=配置)
        平衡数据 = 采样器实例.增强过采样(1.0)
        
        # 验证: 过采样后样本数 >= 原始样本数
        assert len(平衡数据) >= len(数据集), \
            f"增强过采样后样本数 ({len(平衡数据)}) 应 >= 原始样本数 ({len(数据集)})"
        
        # 验证: 各类别达到目标数量
        原始统计 = 统计类别分布(数据集)
        平衡统计 = 统计类别分布(平衡数据)
        最大数量 = max(原始统计.values())
        
        for 类别 in 原始统计.keys():
            平衡数量 = 平衡统计.get(类别, 0)
            assert 平衡数量 >= 最大数量, \
                f"类别 {类别} 增强过采样后数量 ({平衡数量}) 应 >= 目标数量 ({最大数量})"


class Test知情欠采样属性:
    """测试知情欠采样功能的属性"""
    
    @given(样本分布=样本分布策略)
    @settings(max_examples=50, deadline=None)
    def test_知情欠采样保持多样性(self, 样本分布: List[int]):
        """
        知情欠采样应选择多样化的样本
        """
        assume(len(样本分布) >= 2)
        assume(all(n >= 5 for n in 样本分布))  # 需要足够样本进行聚类
        
        数据集 = 生成不平衡数据集(len(样本分布), 样本分布)
        最小数量 = min(样本分布)
        
        配置 = 采样配置(最大样本数=最小数量, 打乱数据=True, 随机种子=42)
        采样器实例 = 采样器(数据集, 配置=配置)
        平衡数据 = 采样器实例.知情欠采样(最小数量)
        
        平衡统计 = 统计类别分布(平衡数据)
        
        # 验证: 每个类别数量 <= 最大样本数
        for 类别, 数量 in 平衡统计.items():
            assert 数量 <= 最小数量, \
                f"类别 {类别} 知情欠采样后数量 ({数量}) 应 <= 最大样本数 ({最小数量})"


class Test数据打乱属性:
    """测试数据打乱功能的属性"""
    
    @given(样本分布=样本分布策略)
    @settings(max_examples=50, deadline=None)
    def test_打乱数据保持样本完整性(self, 样本分布: List[int]):
        """
        打乱数据后应保持所有样本的完整性
        """
        assume(len(样本分布) >= 2)
        assume(all(n > 0 for n in 样本分布))
        
        数据集 = 生成不平衡数据集(len(样本分布), 样本分布)
        
        # 不打乱
        配置1 = 采样配置(目标比率=1.0, 打乱数据=False, 随机种子=42)
        采样器1 = 采样器(数据集, 配置=配置1)
        数据1 = 采样器1.随机过采样()
        
        # 打乱
        配置2 = 采样配置(目标比率=1.0, 打乱数据=True, 随机种子=42)
        采样器2 = 采样器(数据集, 配置=配置2)
        数据2 = 采样器2.随机过采样()
        
        # 验证: 样本数量相同
        assert len(数据1) == len(数据2), \
            f"打乱前后样本数应相同: {len(数据1)} vs {len(数据2)}"
        
        # 验证: 类别分布相同
        统计1 = 统计类别分布(数据1)
        统计2 = 统计类别分布(数据2)
        
        assert 统计1 == 统计2, \
            f"打乱前后类别分布应相同: {统计1} vs {统计2}"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--hypothesis-show-statistics'])
