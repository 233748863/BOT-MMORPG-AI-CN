"""
属性测试：事件类型与价值等级映射一致性
Property 2: 对于任意 GameEvent，如果事件类型为击杀(kill)、任务完成(quest_complete)或技能连招(combo)，
则对应片段的 value_level 必须为 "high"；如果事件类型为拾取(pickup)，则 value_level 必须为 "medium"。

**Feature: smart-training-system, Property 2: 事件类型与价值等级映射一致性**
**验证: 需求 1.2, 1.3, 1.4, 1.5**
"""

import pytest
from hypothesis import given, strategies as st, settings, assume

from 核心.智能录制 import RecordingSegment, GameEvent, ValueEvaluator, 事件类型


# 定义高价值事件类型
HIGH_VALUE_EVENT_TYPES = [
    事件类型.击杀.value,        # 'kill'
    事件类型.任务完成.value,    # 'quest_complete'
    事件类型.技能连招.value,    # 'combo'
]

# 定义中等价值事件类型
MEDIUM_VALUE_EVENT_TYPES = [
    事件类型.拾取.value,        # 'pickup'
]


class Test事件类型与价值等级映射属性:
    """
    Property 2: 事件类型与价值等级映射一致性
    
    *对于任意* GameEvent，如果事件类型为击杀(kill)、任务完成(quest_complete)或技能连招(combo)，
    则 classify_event 返回的 value_level 必须为 "high"；
    如果事件类型为拾取(pickup)，则 value_level 必须为 "medium"。
    
    **验证: 需求 1.2, 1.3, 1.4, 1.5**
    """
    
    @given(
        event_type=st.sampled_from(HIGH_VALUE_EVENT_TYPES),
        timestamp=st.floats(min_value=0.0, max_value=10000.0, allow_nan=False, allow_infinity=False),
        confidence=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100)
    def test_高价值事件类型映射为high等级(self, event_type: str, timestamp: float, confidence: float):
        """
        *对于任意* 高价值事件类型（击杀、任务完成、技能连招），
        classify_event 返回的价值等级必须为 "high"。
        
        **Feature: smart-training-system, Property 2: 事件类型与价值等级映射一致性**
        **验证: 需求 1.2, 1.3, 1.5**
        """
        evaluator = ValueEvaluator()
        event = GameEvent(
            event_type=event_type,
            timestamp=timestamp,
            confidence=confidence
        )
        
        value_level, score_delta = evaluator.classify_event(event)
        
        # 验证价值等级为 "high"
        assert value_level == "high", \
            f"事件类型 '{event_type}' 应该映射为 'high'，但实际为 '{value_level}'"
    
    @given(
        event_type=st.sampled_from(MEDIUM_VALUE_EVENT_TYPES),
        timestamp=st.floats(min_value=0.0, max_value=10000.0, allow_nan=False, allow_infinity=False),
        confidence=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100)
    def test_中等价值事件类型映射为medium等级(self, event_type: str, timestamp: float, confidence: float):
        """
        *对于任意* 中等价值事件类型（拾取），
        classify_event 返回的价值等级必须为 "medium"。
        
        **Feature: smart-training-system, Property 2: 事件类型与价值等级映射一致性**
        **验证: 需求 1.4**
        """
        evaluator = ValueEvaluator()
        event = GameEvent(
            event_type=event_type,
            timestamp=timestamp,
            confidence=confidence
        )
        
        value_level, score_delta = evaluator.classify_event(event)
        
        # 验证价值等级为 "medium"
        assert value_level == "medium", \
            f"事件类型 '{event_type}' 应该映射为 'medium'，但实际为 '{value_level}'"
    
    @given(
        event_type=st.sampled_from(HIGH_VALUE_EVENT_TYPES),
        timestamp=st.floats(min_value=0.0, max_value=10000.0, allow_nan=False, allow_infinity=False),
        confidence=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100)
    def test_高价值事件分数增量为正(self, event_type: str, timestamp: float, confidence: float):
        """
        *对于任意* 高价值事件类型，classify_event 返回的分数增量应该为正数（或零，当置信度为0时）。
        
        **Feature: smart-training-system, Property 2: 事件类型与价值等级映射一致性**
        **验证: 需求 1.2, 1.3, 1.5**
        """
        evaluator = ValueEvaluator()
        event = GameEvent(
            event_type=event_type,
            timestamp=timestamp,
            confidence=confidence
        )
        
        value_level, score_delta = evaluator.classify_event(event)
        
        # 验证分数增量为非负数
        assert score_delta >= 0, \
            f"高价值事件 '{event_type}' 的分数增量应该 >= 0，但实际为 {score_delta}"
    
    @given(
        event_type=st.sampled_from(MEDIUM_VALUE_EVENT_TYPES),
        timestamp=st.floats(min_value=0.0, max_value=10000.0, allow_nan=False, allow_infinity=False),
        confidence=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100)
    def test_中等价值事件分数增量为非负(self, event_type: str, timestamp: float, confidence: float):
        """
        *对于任意* 中等价值事件类型，classify_event 返回的分数增量应该为非负数。
        
        **Feature: smart-training-system, Property 2: 事件类型与价值等级映射一致性**
        **验证: 需求 1.4**
        """
        evaluator = ValueEvaluator()
        event = GameEvent(
            event_type=event_type,
            timestamp=timestamp,
            confidence=confidence
        )
        
        value_level, score_delta = evaluator.classify_event(event)
        
        # 验证分数增量为非负数
        assert score_delta >= 0, \
            f"中等价值事件 '{event_type}' 的分数增量应该 >= 0，但实际为 {score_delta}"
    
    @given(
        high_event_type=st.sampled_from(HIGH_VALUE_EVENT_TYPES),
        timestamp=st.floats(min_value=0.0, max_value=10000.0, allow_nan=False, allow_infinity=False),
        confidence=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100)
    def test_高价值事件的主导价值等级为high(self, high_event_type: str, timestamp: float, confidence: float):
        """
        *对于任意* 包含高价值事件（击杀、任务完成、技能连招）的片段，
        get_dominant_value_level 返回的主导价值等级应该为 "high"。
        
        这验证了事件类型到价值等级的映射关系，而不是最终分数计算。
        
        **Feature: smart-training-system, Property 2: 事件类型与价值等级映射一致性**
        **验证: 需求 1.2, 1.3, 1.5**
        """
        evaluator = ValueEvaluator()
        segment = RecordingSegment()
        
        # 添加高价值事件
        event = GameEvent(
            event_type=high_event_type,
            timestamp=timestamp,
            confidence=confidence
        )
        segment.events.append(event)
        
        # 获取主导价值等级
        dominant_level = evaluator.get_dominant_value_level(segment)
        
        # 验证主导价值等级为 "high"
        assert dominant_level == "high", \
            f"包含 '{high_event_type}' 事件的片段主导价值等级应该为 'high'，但实际为 '{dominant_level}'"
    
    @given(
        medium_event_type=st.sampled_from(MEDIUM_VALUE_EVENT_TYPES),
        timestamp=st.floats(min_value=0.0, max_value=10000.0, allow_nan=False, allow_infinity=False),
        confidence=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100)
    def test_仅包含中等价值事件的片段主导价值等级为medium(self, medium_event_type: str, timestamp: float, confidence: float):
        """
        *对于任意* 仅包含中等价值事件（拾取）的片段，
        get_dominant_value_level 返回的主导价值等级应该为 "medium"。
        
        这验证了事件类型到价值等级的映射关系，而不是最终分数计算。
        
        **Feature: smart-training-system, Property 2: 事件类型与价值等级映射一致性**
        **验证: 需求 1.4**
        """
        evaluator = ValueEvaluator()
        segment = RecordingSegment()
        
        # 添加中等价值事件
        event = GameEvent(
            event_type=medium_event_type,
            timestamp=timestamp,
            confidence=confidence
        )
        segment.events.append(event)
        
        # 获取主导价值等级
        dominant_level = evaluator.get_dominant_value_level(segment)
        
        # 验证主导价值等级为 "medium"
        assert dominant_level == "medium", \
            f"仅包含 '{medium_event_type}' 事件的片段主导价值等级应该为 'medium'，但实际为 '{dominant_level}'"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--hypothesis-show-statistics'])
