"""
属性测试：重复操作检测正确性

Property 4: 重复操作检测正确性
*对于任意* 动作序列，如果相同动作连续出现超过10次，则 is_repetitive() 必须返回 True。

验证: 需求 2.2 - WHEN 检测到重复相同操作超过10次 THEN THE Smart_Recorder SHALL 标记为重复数据

Feature: smart-training-system, Property 4: 重复操作检测正确性
"""

import pytest
from hypothesis import given, strategies as st, settings, assume

from 核心.智能录制 import DataFilter


class Test重复操作检测属性:
    """
    Property 4: 重复操作检测正确性
    
    *对于任意* 动作序列，如果相同动作连续出现超过10次，则 is_repetitive() 必须返回 True。
    
    **验证: 需求 2.2**
    """
    
    @given(
        action=st.integers(min_value=0, max_value=100),
        repeat_count=st.integers(min_value=11, max_value=100)
    )
    @settings(max_examples=100)
    def test_连续重复超过10次必须检测为重复(self, action: int, repeat_count: int):
        """
        Property 4: 对于任意动作，如果连续出现超过10次，is_repetitive() 必须返回 True
        
        Feature: smart-training-system, Property 4: 重复操作检测正确性
        **验证: 需求 2.2**
        """
        data_filter = DataFilter()
        
        # 生成连续重复的动作序列
        actions = [action] * repeat_count
        
        # 验证：连续重复超过10次必须检测为重复
        result = data_filter.is_repetitive(actions)
        assert result == True, f"连续 {repeat_count} 次动作 {action} 应该被检测为重复"
    
    @given(
        action=st.integers(min_value=0, max_value=100),
        repeat_count=st.integers(min_value=1, max_value=10)
    )
    @settings(max_examples=100)
    def test_连续重复不超过10次不应检测为重复(self, action: int, repeat_count: int):
        """
        Property 4 边界条件: 对于任意动作，如果连续出现不超过10次，is_repetitive() 必须返回 False
        
        Feature: smart-training-system, Property 4: 重复操作检测正确性
        **验证: 需求 2.2**
        """
        data_filter = DataFilter()
        
        # 生成连续重复的动作序列（不超过10次）
        actions = [action] * repeat_count
        
        # 验证：连续重复不超过10次不应检测为重复
        result = data_filter.is_repetitive(actions)
        assert result == False, f"连续 {repeat_count} 次动作 {action} 不应该被检测为重复"
    
    @given(
        action=st.integers(min_value=0, max_value=100),
        repeat_count=st.integers(min_value=11, max_value=50),
        prefix_actions=st.lists(st.integers(min_value=0, max_value=100), min_size=0, max_size=20),
        suffix_actions=st.lists(st.integers(min_value=0, max_value=100), min_size=0, max_size=20)
    )
    @settings(max_examples=100)
    def test_序列中间有连续重复超过10次必须检测为重复(
        self, action: int, repeat_count: int, 
        prefix_actions: list, suffix_actions: list
    ):
        """
        Property 4: 对于任意动作序列，如果中间有连续重复超过10次，is_repetitive() 必须返回 True
        
        Feature: smart-training-system, Property 4: 重复操作检测正确性
        **验证: 需求 2.2**
        """
        data_filter = DataFilter()
        
        # 确保前缀和后缀不会与重复动作连续
        # 过滤掉与重复动作相同的前缀末尾和后缀开头
        if prefix_actions and prefix_actions[-1] == action:
            prefix_actions = prefix_actions[:-1]
        if suffix_actions and suffix_actions[0] == action:
            suffix_actions = suffix_actions[1:]
        
        # 构建动作序列：前缀 + 重复动作 + 后缀
        actions = prefix_actions + [action] * repeat_count + suffix_actions
        
        # 验证：序列中有连续重复超过10次必须检测为重复
        result = data_filter.is_repetitive(actions)
        assert result == True, f"序列中有连续 {repeat_count} 次动作 {action} 应该被检测为重复"
    
    @given(
        actions=st.lists(
            st.integers(min_value=0, max_value=100),
            min_size=1,
            max_size=100
        )
    )
    @settings(max_examples=100)
    def test_无连续重复超过10次不应检测为重复(self, actions: list):
        """
        Property 4 逆向验证: 对于任意动作序列，如果没有连续重复超过10次，is_repetitive() 必须返回 False
        
        Feature: smart-training-system, Property 4: 重复操作检测正确性
        **验证: 需求 2.2**
        """
        data_filter = DataFilter()
        
        # 检查生成的序列是否有连续重复超过10次
        max_consecutive = self._get_max_consecutive_count(actions)
        
        # 只测试没有连续重复超过10次的序列
        assume(max_consecutive <= 10)
        
        # 验证：没有连续重复超过10次不应检测为重复
        result = data_filter.is_repetitive(actions)
        assert result == False, f"最大连续重复 {max_consecutive} 次不应该被检测为重复"
    
    def _get_max_consecutive_count(self, actions: list) -> int:
        """计算动作序列中最大连续重复次数"""
        if not actions:
            return 0
        
        max_count = 1
        current_count = 1
        
        for i in range(1, len(actions)):
            if actions[i] == actions[i-1]:
                current_count += 1
                max_count = max(max_count, current_count)
            else:
                current_count = 1
        
        return max_count


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--hypothesis-show-statistics'])
