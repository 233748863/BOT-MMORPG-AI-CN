"""
属性测试：空闲检测正确性
Property 3: 对于任意动作序列，如果连续无操作时间超过5秒，则 is_idle() 必须返回 True。

**Feature: smart-training-system, Property 3: 空闲检测正确性**
**验证: 需求 2.1**
"""

import pytest
from hypothesis import given, strategies as st, settings, assume

from 核心.智能录制 import DataFilter


class Test空闲检测正确性属性:
    """
    Property 3: 空闲检测正确性
    
    *对于任意* 动作序列，如果连续无操作时间超过5秒，则 is_idle() 必须返回 True。
    **验证: 需求 2.1**
    """
    
    @given(
        num_idle_actions=st.integers(min_value=10, max_value=200),
        duration=st.floats(min_value=5.1, max_value=60.0, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100)
    def test_全部无操作且时长超过5秒应检测为空闲(self, num_idle_actions: int, duration: float):
        """
        *对于任意* 全部为无操作(0)的动作序列，且时长超过5秒，is_idle() 必须返回 True。
        
        **Feature: smart-training-system, Property 3: 空闲检测正确性**
        **验证: 需求 2.1**
        """
        data_filter = DataFilter()
        
        # 创建全部为无操作的动作序列
        idle_actions = [0] * num_idle_actions
        
        # 验证检测结果
        result = data_filter.is_idle(idle_actions, duration)
        assert result == True, f"全部无操作序列(长度{num_idle_actions})且时长{duration}秒应检测为空闲"
    
    @given(
        num_actions=st.integers(min_value=10, max_value=200),
        duration=st.floats(min_value=0.1, max_value=4.9, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100)
    def test_时长不足5秒不应检测为空闲(self, num_actions: int, duration: float):
        """
        *对于任意* 动作序列，如果时长不足5秒，is_idle() 必须返回 False。
        
        **Feature: smart-training-system, Property 3: 空闲检测正确性**
        **验证: 需求 2.1**
        """
        data_filter = DataFilter()
        
        # 即使全部是无操作，时长不足也不应检测为空闲
        idle_actions = [0] * num_actions
        
        result = data_filter.is_idle(idle_actions, duration)
        assert result == False, f"时长{duration}秒不足5秒，不应检测为空闲"
    
    @given(
        active_actions=st.lists(
            st.integers(min_value=1, max_value=100),
            min_size=10,
            max_size=200
        ),
        duration=st.floats(min_value=5.1, max_value=60.0, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100)
    def test_全部有操作不应检测为空闲(self, active_actions: list, duration: float):
        """
        *对于任意* 全部为有效操作(非0)的动作序列，is_idle() 必须返回 False。
        
        **Feature: smart-training-system, Property 3: 空闲检测正确性**
        **验证: 需求 2.1**
        """
        data_filter = DataFilter()
        
        # 确保所有动作都是有效操作（非0）
        assume(all(action != 0 for action in active_actions))
        
        result = data_filter.is_idle(active_actions, duration)
        assert result == False, f"全部有效操作的序列不应检测为空闲"
    
    @given(
        idle_count=st.integers(min_value=50, max_value=150),
        active_count=st.integers(min_value=1, max_value=10),
        duration=st.floats(min_value=6.0, max_value=60.0, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100)
    def test_连续无操作占主导时应检测为空闲(self, idle_count: int, active_count: int, duration: float):
        """
        *对于任意* 动作序列，如果连续无操作时间超过5秒，is_idle() 必须返回 True。
        
        **Feature: smart-training-system, Property 3: 空闲检测正确性**
        **验证: 需求 2.1**
        """
        data_filter = DataFilter()
        
        # 创建以连续无操作为主的序列
        # 先放少量有效操作，然后是大量连续无操作
        actions = [1] * active_count + [0] * idle_count
        
        # 计算连续无操作的估计时长
        total_actions = len(actions)
        time_per_action = duration / total_actions
        consecutive_idle_duration = idle_count * time_per_action
        
        # 只有当连续无操作时长超过5秒时才验证
        if consecutive_idle_duration >= 5.0:
            result = data_filter.is_idle(actions, duration)
            assert result == True, f"连续无操作时长{consecutive_idle_duration:.2f}秒超过5秒，应检测为空闲"
    
    @given(duration=st.floats(min_value=5.1, max_value=60.0, allow_nan=False, allow_infinity=False))
    @settings(max_examples=100)
    def test_空动作列表且时长超过5秒应检测为空闲(self, duration: float):
        """
        *对于任意* 空动作列表，如果时长超过5秒，is_idle() 必须返回 True。
        
        **Feature: smart-training-system, Property 3: 空闲检测正确性**
        **验证: 需求 2.1**
        """
        data_filter = DataFilter()
        
        # 空动作列表表示没有任何操作记录
        empty_actions = []
        
        result = data_filter.is_idle(empty_actions, duration)
        assert result == True, f"空动作列表且时长{duration}秒超过5秒，应检测为空闲"
    
    @given(
        idle_threshold=st.floats(min_value=1.0, max_value=10.0, allow_nan=False, allow_infinity=False),
        num_idle_actions=st.integers(min_value=20, max_value=100)
    )
    @settings(max_examples=100)
    def test_自定义阈值的空闲检测(self, idle_threshold: float, num_idle_actions: int):
        """
        *对于任意* 自定义空闲阈值，当连续无操作时间超过该阈值时，is_idle() 必须返回 True。
        
        **Feature: smart-training-system, Property 3: 空闲检测正确性**
        **验证: 需求 2.1**
        """
        data_filter = DataFilter(idle_threshold=idle_threshold)
        
        # 创建全部无操作的序列
        idle_actions = [0] * num_idle_actions
        
        # 设置时长刚好超过阈值
        duration = idle_threshold + 1.0
        
        result = data_filter.is_idle(idle_actions, duration)
        assert result == True, f"自定义阈值{idle_threshold}秒，时长{duration}秒应检测为空闲"
        
        # 设置时长刚好不足阈值
        duration_short = idle_threshold - 0.5
        if duration_short > 0:
            result_short = data_filter.is_idle(idle_actions, duration_short)
            assert result_short == False, f"自定义阈值{idle_threshold}秒，时长{duration_short}秒不应检测为空闲"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--hypothesis-show-statistics'])
