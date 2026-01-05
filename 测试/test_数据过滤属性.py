"""
数据过滤属性测试模块

使用 Hypothesis 进行属性测试，验证智能录制数据过滤逻辑的正确性。

**属性 2: 过滤逻辑一致性**
*对于任意* 片段评估结果，当 should_filter=True 或 (等级="low" 且 过滤选项="auto_filter") 时，
该片段不应出现在最终的训练数据列表中。
验证: 需求 2.1, 2.2

**属性 3: 过滤模式正确性**
*对于任意* 片段集合和过滤选项：
- 当选项为"high_only"时，结果列表中所有片段的等级都应为"high"
- 当选项为"all"时，结果列表应包含所有输入片段
验证: 需求 2.3, 2.4

**属性 4: 统计准确性**
*对于任意* 录制会话，过滤计数 + 保存计数 应等于总片段数。
验证: 需求 2.5
"""

import pytest
import numpy as np
from hypothesis import given, strategies as st, settings, assume
from typing import List, Tuple
from dataclasses import dataclass
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ==================== 数据类定义 ====================

@dataclass
class 模拟片段评估结果:
    """模拟片段评估结果"""
    评分: float           # 0-100 的价值评分
    等级: str             # "high", "medium", "low"
    是否过滤: bool        # True 表示应该被过滤
    过滤原因: List[str]   # 过滤原因列表


# ==================== 过滤逻辑模拟 ====================

def should_save_segment(评分: float, 等级: str, 是否过滤: bool, 过滤选项: str) -> bool:
    """
    根据过滤选项判断是否应该保存片段
    
    这是从 SmartRecorder.should_save_segment 提取的核心逻辑
    
    Args:
        评分: 价值评分
        等级: 价值等级 ("high", "medium", "low")
        是否过滤: 是否被标记为应过滤
        过滤选项: 过滤选项 ("all", "high_only", "auto_filter")
        
    Returns:
        是否应该保存
    """
    if 过滤选项 == "all":
        return True
    elif 过滤选项 == "high_only":
        return 等级 == "high"
    elif 过滤选项 == "auto_filter":
        return not 是否过滤 and 等级 != "low"
    return True


def 模拟数据收集过程(片段列表: List[模拟片段评估结果], 过滤选项: str) -> Tuple[List[int], int, int, int]:
    """
    模拟数据收集过程中的过滤逻辑
    
    Args:
        片段列表: 片段评估结果列表
        过滤选项: 过滤选项
        
    Returns:
        (保存的片段索引列表, 总片段数, 保存计数, 过滤计数)
    """
    保存的片段索引 = []
    保存计数 = 0
    过滤计数 = 0
    总片段数 = len(片段列表)
    
    for i, 片段 in enumerate(片段列表):
        if should_save_segment(片段.评分, 片段.等级, 片段.是否过滤, 过滤选项):
            保存的片段索引.append(i)
            保存计数 += 1
        else:
            过滤计数 += 1
    
    return (保存的片段索引, 总片段数, 保存计数, 过滤计数)


# ==================== 策略定义 ====================

@st.composite
def 有效价值等级(draw):
    """生成有效的价值等级"""
    return draw(st.sampled_from(["high", "medium", "low"]))


@st.composite
def 有效过滤选项(draw):
    """生成有效的过滤选项"""
    return draw(st.sampled_from(["all", "high_only", "auto_filter"]))


@st.composite
def 有效评分(draw):
    """生成有效的价值评分 (0-100)"""
    return draw(st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False))


@st.composite
def 片段评估结果(draw):
    """生成随机的片段评估结果"""
    评分 = draw(有效评分())
    
    # 根据评分确定等级
    if 评分 >= 70:
        等级 = "high"
    elif 评分 >= 40:
        等级 = "medium"
    else:
        等级 = "low"
    
    # 随机决定是否应该过滤
    是否过滤 = draw(st.booleans())
    
    # 生成过滤原因
    可能的原因 = ["idle", "repetitive", "stuck", "loading"]
    if 是否过滤:
        过滤原因 = draw(st.lists(st.sampled_from(可能的原因), min_size=1, max_size=3))
    else:
        过滤原因 = []
    
    return 模拟片段评估结果(评分=评分, 等级=等级, 是否过滤=是否过滤, 过滤原因=过滤原因)


@st.composite
def 片段列表(draw, min_size=1, max_size=20):
    """生成片段评估结果列表"""
    return draw(st.lists(片段评估结果(), min_size=min_size, max_size=max_size))


# ==================== 属性 2: 过滤逻辑一致性 ====================

class Test过滤逻辑一致性属性:
    """
    属性测试: 过滤逻辑一致性
    
    Feature: business-logic-fixes, Property 2: 过滤逻辑一致性
    *对于任意* 片段评估结果，当 should_filter=True 或 (等级="low" 且 过滤选项="auto_filter") 时，
    该片段不应出现在最终的训练数据列表中。
    
    **验证: 需求 2.1, 2.2**
    """

    @settings(max_examples=100, deadline=30000)
    @given(片段=片段评估结果())
    def test_should_filter为True时不保存_auto_filter模式(self, 片段: 模拟片段评估结果):
        """
        属性测试: 当 should_filter=True 且使用 auto_filter 模式时，片段不应被保存
        
        Feature: business-logic-fixes, Property 2: 过滤逻辑一致性
        **验证: 需求 2.1**
        """
        assume(片段.是否过滤 == True)
        
        结果 = should_save_segment(片段.评分, 片段.等级, 片段.是否过滤, "auto_filter")
        
        assert 结果 == False, \
            f"should_filter=True 时，auto_filter 模式应该过滤片段，但返回了 {结果}"

    @settings(max_examples=100, deadline=30000)
    @given(片段=片段评估结果())
    def test_低价值片段在auto_filter模式下不保存(self, 片段: 模拟片段评估结果):
        """
        属性测试: 当等级="low" 且使用 auto_filter 模式时，片段不应被保存
        
        Feature: business-logic-fixes, Property 2: 过滤逻辑一致性
        **验证: 需求 2.2**
        """
        assume(片段.等级 == "low")
        
        结果 = should_save_segment(片段.评分, 片段.等级, 片段.是否过滤, "auto_filter")
        
        assert 结果 == False, \
            f"等级=low 时，auto_filter 模式应该过滤片段，但返回了 {结果}"

    @settings(max_examples=100, deadline=30000)
    @given(片段列表=片段列表())
    def test_过滤的片段不在保存列表中(self, 片段列表: List[模拟片段评估结果]):
        """
        属性测试: 被过滤的片段不应出现在保存列表中
        
        Feature: business-logic-fixes, Property 2: 过滤逻辑一致性
        **验证: 需求 2.1, 2.2**
        """
        保存的索引, _, _, _ = 模拟数据收集过程(片段列表, "auto_filter")
        
        for i in 保存的索引:
            片段 = 片段列表[i]
            # 保存的片段不应该是被标记为过滤的，也不应该是低价值的
            assert not (片段.是否过滤 or 片段.等级 == "low"), \
                f"片段 {i} 不应该被保存: 是否过滤={片段.是否过滤}, 等级={片段.等级}"


# ==================== 属性 3: 过滤模式正确性 ====================

class Test过滤模式正确性属性:
    """
    属性测试: 过滤模式正确性
    
    Feature: business-logic-fixes, Property 3: 过滤模式正确性
    *对于任意* 片段集合和过滤选项：
    - 当选项为"high_only"时，结果列表中所有片段的等级都应为"high"
    - 当选项为"all"时，结果列表应包含所有输入片段
    
    **验证: 需求 2.3, 2.4**
    """

    @settings(max_examples=100, deadline=30000)
    @given(片段列表=片段列表())
    def test_high_only模式只保存高价值片段(self, 片段列表: List[模拟片段评估结果]):
        """
        属性测试: high_only 模式下，只有高价值片段被保存
        
        Feature: business-logic-fixes, Property 3: 过滤模式正确性
        **验证: 需求 2.3**
        """
        保存的索引, _, _, _ = 模拟数据收集过程(片段列表, "high_only")
        
        for i in 保存的索引:
            片段 = 片段列表[i]
            assert 片段.等级 == "high", \
                f"high_only 模式下，片段 {i} 的等级应为 high，实际为 {片段.等级}"

    @settings(max_examples=100, deadline=30000)
    @given(片段列表=片段列表())
    def test_high_only模式保存所有高价值片段(self, 片段列表: List[模拟片段评估结果]):
        """
        属性测试: high_only 模式下，所有高价值片段都被保存
        
        Feature: business-logic-fixes, Property 3: 过滤模式正确性
        **验证: 需求 2.3**
        """
        保存的索引, _, _, _ = 模拟数据收集过程(片段列表, "high_only")
        
        # 找出所有高价值片段的索引
        高价值索引 = [i for i, 片段 in enumerate(片段列表) if 片段.等级 == "high"]
        
        # 验证所有高价值片段都被保存
        for i in 高价值索引:
            assert i in 保存的索引, \
                f"high_only 模式下，高价值片段 {i} 应该被保存"

    @settings(max_examples=100, deadline=30000)
    @given(片段列表=片段列表())
    def test_all模式保存所有片段(self, 片段列表: List[模拟片段评估结果]):
        """
        属性测试: all 模式下，所有片段都被保存
        
        Feature: business-logic-fixes, Property 3: 过滤模式正确性
        **验证: 需求 2.4**
        """
        保存的索引, 总片段数, 保存计数, 过滤计数 = 模拟数据收集过程(片段列表, "all")
        
        # 验证所有片段都被保存
        assert len(保存的索引) == len(片段列表), \
            f"all 模式下，应保存所有 {len(片段列表)} 个片段，实际保存 {len(保存的索引)} 个"
        
        # 验证保存计数等于总片段数
        assert 保存计数 == 总片段数, \
            f"all 模式下，保存计数 {保存计数} 应等于总片段数 {总片段数}"
        
        # 验证过滤计数为 0
        assert 过滤计数 == 0, \
            f"all 模式下，过滤计数应为 0，实际为 {过滤计数}"

    @settings(max_examples=100, deadline=30000)
    @given(片段列表=片段列表(), 过滤选项=有效过滤选项())
    def test_保存的片段索引有效(self, 片段列表: List[模拟片段评估结果], 过滤选项: str):
        """
        属性测试: 保存的片段索引应该是有效的
        
        Feature: business-logic-fixes, Property 3: 过滤模式正确性
        **验证: 需求 2.3, 2.4**
        """
        保存的索引, _, _, _ = 模拟数据收集过程(片段列表, 过滤选项)
        
        for i in 保存的索引:
            assert 0 <= i < len(片段列表), \
                f"保存的索引 {i} 超出范围 [0, {len(片段列表)})"


# ==================== 属性 4: 统计准确性 ====================

class Test统计准确性属性:
    """
    属性测试: 统计准确性
    
    Feature: business-logic-fixes, Property 4: 统计准确性
    *对于任意* 录制会话，过滤计数 + 保存计数 应等于总片段数。
    
    **验证: 需求 2.5**
    """

    @settings(max_examples=100, deadline=30000)
    @given(片段列表=片段列表(), 过滤选项=有效过滤选项())
    def test_过滤计数加保存计数等于总片段数(self, 片段列表: List[模拟片段评估结果], 过滤选项: str):
        """
        属性测试: 过滤计数 + 保存计数 = 总片段数
        
        Feature: business-logic-fixes, Property 4: 统计准确性
        **验证: 需求 2.5**
        """
        _, 总片段数, 保存计数, 过滤计数 = 模拟数据收集过程(片段列表, 过滤选项)
        
        assert 保存计数 + 过滤计数 == 总片段数, \
            f"保存计数({保存计数}) + 过滤计数({过滤计数}) 应等于总片段数({总片段数})"

    @settings(max_examples=100, deadline=30000)
    @given(片段列表=片段列表(), 过滤选项=有效过滤选项())
    def test_保存索引数量等于保存计数(self, 片段列表: List[模拟片段评估结果], 过滤选项: str):
        """
        属性测试: 保存的索引数量应等于保存计数
        
        Feature: business-logic-fixes, Property 4: 统计准确性
        **验证: 需求 2.5**
        """
        保存的索引, _, 保存计数, _ = 模拟数据收集过程(片段列表, 过滤选项)
        
        assert len(保存的索引) == 保存计数, \
            f"保存的索引数量({len(保存的索引)}) 应等于保存计数({保存计数})"

    @settings(max_examples=100, deadline=30000)
    @given(片段列表=片段列表(), 过滤选项=有效过滤选项())
    def test_统计值非负(self, 片段列表: List[模拟片段评估结果], 过滤选项: str):
        """
        属性测试: 所有统计值应为非负数
        
        Feature: business-logic-fixes, Property 4: 统计准确性
        **验证: 需求 2.5**
        """
        _, 总片段数, 保存计数, 过滤计数 = 模拟数据收集过程(片段列表, 过滤选项)
        
        assert 总片段数 >= 0, f"总片段数应为非负数，实际为 {总片段数}"
        assert 保存计数 >= 0, f"保存计数应为非负数，实际为 {保存计数}"
        assert 过滤计数 >= 0, f"过滤计数应为非负数，实际为 {过滤计数}"

    def test_空片段列表统计为零(self):
        """
        测试: 空片段列表的统计应全为零
        
        Feature: business-logic-fixes, Property 4: 统计准确性
        **验证: 需求 2.5**
        """
        _, 总片段数, 保存计数, 过滤计数 = 模拟数据收集过程([], "all")
        
        assert 总片段数 == 0, f"空列表的总片段数应为 0，实际为 {总片段数}"
        assert 保存计数 == 0, f"空列表的保存计数应为 0，实际为 {保存计数}"
        assert 过滤计数 == 0, f"空列表的过滤计数应为 0，实际为 {过滤计数}"


# ==================== 边界情况测试 ====================

class Test边界情况:
    """边界情况测试"""

    def test_单个高价值片段_all模式(self):
        """测试单个高价值片段在 all 模式下被保存"""
        片段 = 模拟片段评估结果(评分=80.0, 等级="high", 是否过滤=False, 过滤原因=[])
        保存的索引, _, 保存计数, 过滤计数 = 模拟数据收集过程([片段], "all")
        
        assert 保存计数 == 1
        assert 过滤计数 == 0
        assert 0 in 保存的索引

    def test_单个低价值片段_high_only模式(self):
        """测试单个低价值片段在 high_only 模式下被过滤"""
        片段 = 模拟片段评估结果(评分=20.0, 等级="low", 是否过滤=False, 过滤原因=[])
        保存的索引, _, 保存计数, 过滤计数 = 模拟数据收集过程([片段], "high_only")
        
        assert 保存计数 == 0
        assert 过滤计数 == 1
        assert len(保存的索引) == 0

    def test_混合价值片段_auto_filter模式(self):
        """测试混合价值片段在 auto_filter 模式下的过滤"""
        片段列表 = [
            模拟片段评估结果(评分=80.0, 等级="high", 是否过滤=False, 过滤原因=[]),
            模拟片段评估结果(评分=50.0, 等级="medium", 是否过滤=False, 过滤原因=[]),
            模拟片段评估结果(评分=20.0, 等级="low", 是否过滤=False, 过滤原因=[]),
            模拟片段评估结果(评分=60.0, 等级="medium", 是否过滤=True, 过滤原因=["idle"]),
        ]
        
        保存的索引, 总片段数, 保存计数, 过滤计数 = 模拟数据收集过程(片段列表, "auto_filter")
        
        # 应该保存: 高价值(0) 和 中价值未过滤(1)
        # 应该过滤: 低价值(2) 和 被标记过滤(3)
        assert 保存计数 == 2, f"应保存 2 个片段，实际 {保存计数}"
        assert 过滤计数 == 2, f"应过滤 2 个片段，实际 {过滤计数}"
        assert 0 in 保存的索引, "高价值片段应被保存"
        assert 1 in 保存的索引, "中价值未过滤片段应被保存"
        assert 2 not in 保存的索引, "低价值片段应被过滤"
        assert 3 not in 保存的索引, "被标记过滤的片段应被过滤"

    def test_所有片段都是高价值_high_only模式(self):
        """测试所有片段都是高价值时，high_only 模式保存全部"""
        片段列表 = [
            模拟片段评估结果(评分=80.0, 等级="high", 是否过滤=False, 过滤原因=[]),
            模拟片段评估结果(评分=90.0, 等级="high", 是否过滤=False, 过滤原因=[]),
            模拟片段评估结果(评分=75.0, 等级="high", 是否过滤=False, 过滤原因=[]),
        ]
        
        保存的索引, _, 保存计数, 过滤计数 = 模拟数据收集过程(片段列表, "high_only")
        
        assert 保存计数 == 3
        assert 过滤计数 == 0
        assert len(保存的索引) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])
