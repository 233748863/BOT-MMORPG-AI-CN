"""
属性测试：价值评分范围约束
Property 1: 对于任意 RecordingSegment，其 value_score 必须在 0 到 100 之间（包含边界）。

**Feature: smart-training-system, Property 1: 价值评分范围约束**
**验证: 需求 1.6**
"""

import pytest
from hypothesis import given, strategies as st, settings, assume

from 核心.智能录制 import RecordingSegment, GameEvent, ValueEvaluator


class Test价值评分范围约束属性:
    """
    Property 1: 价值评分范围约束
    
    *对于任意* RecordingSegment，其 value_score 必须在 0 到 100 之间（包含边界）。
    **验证: 需求 1.6**
    """
    
    @given(score=st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False))
    @settings(max_examples=100)
    def test_有效评分范围内的值应被接受(self, score: float):
        """
        *对于任意* 0到100范围内的浮点数，设置为 value_score 后应该被正确存储。
        
        **Feature: smart-training-system, Property 1: 价值评分范围约束**
        **验证: 需求 1.6**
        """
        segment = RecordingSegment()
        segment.value_score = score
        
        # 验证评分被正确存储
        assert segment.value_score == score
        # 验证评分在有效范围内
        assert 0.0 <= segment.value_score <= 100.0
    
    @given(score=st.floats(max_value=-0.001, allow_nan=False, allow_infinity=False))
    @settings(max_examples=100)
    def test_负数评分应被拒绝(self, score: float):
        """
        *对于任意* 负数，设置为 value_score 时应该抛出 ValueError。
        
        **Feature: smart-training-system, Property 1: 价值评分范围约束**
        **验证: 需求 1.6**
        """
        segment = RecordingSegment()
        
        with pytest.raises(ValueError):
            segment.value_score = score
    
    @given(score=st.floats(min_value=100.001, allow_nan=False, allow_infinity=False))
    @settings(max_examples=100)
    def test_超过100的评分应被拒绝(self, score: float):
        """
        *对于任意* 大于100的数，设置为 value_score 时应该抛出 ValueError。
        
        **Feature: smart-training-system, Property 1: 价值评分范围约束**
        **验证: 需求 1.6**
        """
        # 过滤掉无穷大的值
        assume(score < float('inf'))
        
        segment = RecordingSegment()
        
        with pytest.raises(ValueError):
            segment.value_score = score
    
    @given(
        events=st.lists(
            st.sampled_from(['kill', 'quest_complete', 'combo', 'pickup', 'idle', 'repeat', 'stuck', 'loading', 'normal']),
            min_size=0,
            max_size=20
        ),
        confidences=st.lists(
            st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
            min_size=0,
            max_size=20
        )
    )
    @settings(max_examples=100)
    def test_评估后的评分始终在有效范围内(self, events: list, confidences: list):
        """
        *对于任意* 事件组合，经过 ValueEvaluator 评估后的 value_score 必须在 0-100 范围内。
        
        **Feature: smart-training-system, Property 1: 价值评分范围约束**
        **验证: 需求 1.6**
        """
        segment = RecordingSegment()
        evaluator = ValueEvaluator()
        
        # 创建事件列表（使用较短的列表长度）
        min_len = min(len(events), len(confidences))
        for i in range(min_len):
            event = GameEvent(
                event_type=events[i],
                timestamp=float(i),
                confidence=confidences[i]
            )
            segment.events.append(event)
        
        # 评估片段
        score = evaluator.evaluate_segment(segment)
        
        # 验证评分在有效范围内
        assert 0.0 <= score <= 100.0
        assert 0.0 <= segment.value_score <= 100.0
    
    @given(initial_score=st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False))
    @settings(max_examples=100)
    def test_初始化时的评分范围约束(self, initial_score: float):
        """
        *对于任意* 0到100范围内的初始评分，创建 RecordingSegment 时应该被正确设置。
        
        **Feature: smart-training-system, Property 1: 价值评分范围约束**
        **验证: 需求 1.6**
        """
        segment = RecordingSegment(_value_score=initial_score)
        
        # 验证评分在有效范围内
        assert 0.0 <= segment.value_score <= 100.0
        assert segment.value_score == initial_score


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--hypothesis-show-statistics'])
