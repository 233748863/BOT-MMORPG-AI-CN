"""
属性测试：统计计算一致性
Property 5: 对于任意录制会话的片段集合，high_value_count + medium_value_count + low_value_count 必须等于 total_segments。

**Feature: smart-training-system, Property 5: 统计计算一致性**
**验证: 需求 3.2**
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from typing import List

from 核心.智能录制 import (
    RecordingSegment, 
    RecordingStatistics, 
    StatisticsService,
    GameEvent
)


# ==================== 策略定义 ====================

def valid_value_score_strategy():
    """生成有效的价值评分 (0-100)"""
    return st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False)


def valid_timestamp_strategy():
    """生成有效的时间戳 (非负数)"""
    return st.floats(min_value=0.0, max_value=10000.0, allow_nan=False, allow_infinity=False)


def valid_action_strategy():
    """生成有效的动作ID"""
    return st.integers(min_value=0, max_value=100)


def recording_segment_strategy():
    """生成有效的录制片段，确保 value_score 和 value_level 一致"""
    @st.composite
    def _build_segment(draw):
        start_time = draw(valid_timestamp_strategy())
        end_time = draw(valid_timestamp_strategy())
        actions = draw(st.lists(valid_action_strategy(), min_size=0, max_size=20))
        value_score = draw(valid_value_score_strategy())
        
        # 创建片段并通过 setter 设置 value_score，确保 value_level 同步
        segment = RecordingSegment(
            start_time=start_time,
            end_time=end_time,
            actions=actions
        )
        segment.value_score = value_score
        return segment
    
    return _build_segment()


def segments_list_strategy(min_size: int = 0, max_size: int = 50):
    """生成录制片段列表"""
    return st.lists(recording_segment_strategy(), min_size=min_size, max_size=max_size)


class Test统计计算一致性属性:
    """
    Property 5: 统计计算一致性
    
    *对于任意* 录制会话的片段集合，high_value_count + medium_value_count + low_value_count 必须等于 total_segments。
    **验证: 需求 3.2**
    """
    
    @given(segments=segments_list_strategy(min_size=0, max_size=50))
    @settings(max_examples=100)
    def test_价值等级计数总和等于总片段数(self, segments: List[RecordingSegment]):
        """
        *对于任意* 录制片段集合，高/中/低价值片段计数之和必须等于总片段数。
        
        **Feature: smart-training-system, Property 5: 统计计算一致性**
        **验证: 需求 3.2**
        """
        # 创建统计服务并添加片段
        stats_service = StatisticsService()
        stats_service.add_segments(segments)
        
        # 获取统计数据
        stats = stats_service.get_statistics()
        
        # 验证属性：价值等级计数总和等于总片段数
        total_by_level = stats.high_value_count + stats.medium_value_count + stats.low_value_count
        
        assert total_by_level == stats.total_segments, (
            f"价值等级计数总和 ({total_by_level}) 不等于总片段数 ({stats.total_segments})"
        )
        
        # 额外验证：总片段数等于输入片段数
        assert stats.total_segments == len(segments), (
            f"统计的总片段数 ({stats.total_segments}) 不等于输入片段数 ({len(segments)})"
        )
    
    @given(segments=segments_list_strategy(min_size=1, max_size=50))
    @settings(max_examples=100)
    def test_非空片段集合的统计一致性(self, segments: List[RecordingSegment]):
        """
        *对于任意* 非空录制片段集合，统计数据必须保持一致性。
        
        **Feature: smart-training-system, Property 5: 统计计算一致性**
        **验证: 需求 3.2**
        """
        # 使用 RecordingStatistics 直接更新
        stats = RecordingStatistics()
        stats.update_from_segments(segments)
        
        # 验证属性：价值等级计数总和等于总片段数
        total_by_level = stats.high_value_count + stats.medium_value_count + stats.low_value_count
        
        assert total_by_level == stats.total_segments, (
            f"价值等级计数总和 ({total_by_level}) 不等于总片段数 ({stats.total_segments})"
        )
        
        # 验证各计数非负
        assert stats.high_value_count >= 0, "高价值片段计数不能为负"
        assert stats.medium_value_count >= 0, "中价值片段计数不能为负"
        assert stats.low_value_count >= 0, "低价值片段计数不能为负"
    
    @given(
        high_count=st.integers(min_value=0, max_value=20),
        medium_count=st.integers(min_value=0, max_value=20),
        low_count=st.integers(min_value=0, max_value=20)
    )
    @settings(max_examples=100)
    def test_指定价值等级分布的统计一致性(
        self, 
        high_count: int, 
        medium_count: int, 
        low_count: int
    ):
        """
        *对于任意* 指定的高/中/低价值片段数量，统计后的计数必须与输入一致。
        
        **Feature: smart-training-system, Property 5: 统计计算一致性**
        **验证: 需求 3.2**
        """
        segments = []
        
        # 创建高价值片段 (value_score >= 70)
        # 注意：需要通过 value_score setter 设置，以确保 value_level 同步更新
        for i in range(high_count):
            seg = RecordingSegment(
                start_time=float(i * 10),
                end_time=float((i + 1) * 10)
            )
            seg.value_score = 80.0  # 通过 setter 设置，自动更新 value_level 为 "high"
            segments.append(seg)
        
        # 创建中价值片段 (40 <= value_score < 70)
        for i in range(medium_count):
            seg = RecordingSegment(
                start_time=float((high_count + i) * 10),
                end_time=float((high_count + i + 1) * 10)
            )
            seg.value_score = 55.0  # 通过 setter 设置，自动更新 value_level 为 "medium"
            segments.append(seg)
        
        # 创建低价值片段 (value_score < 40)
        for i in range(low_count):
            seg = RecordingSegment(
                start_time=float((high_count + medium_count + i) * 10),
                end_time=float((high_count + medium_count + i + 1) * 10)
            )
            seg.value_score = 20.0  # 通过 setter 设置，自动更新 value_level 为 "low"
            segments.append(seg)
        
        # 统计
        stats = RecordingStatistics()
        stats.update_from_segments(segments)
        
        # 验证属性：价值等级计数总和等于总片段数
        total_by_level = stats.high_value_count + stats.medium_value_count + stats.low_value_count
        expected_total = high_count + medium_count + low_count
        
        assert total_by_level == stats.total_segments == expected_total, (
            f"统计不一致: 计数总和={total_by_level}, total_segments={stats.total_segments}, 预期={expected_total}"
        )
        
        # 验证各等级计数正确
        assert stats.high_value_count == high_count, (
            f"高价值计数不正确: 期望 {high_count}, 实际 {stats.high_value_count}"
        )
        assert stats.medium_value_count == medium_count, (
            f"中价值计数不正确: 期望 {medium_count}, 实际 {stats.medium_value_count}"
        )
        assert stats.low_value_count == low_count, (
            f"低价值计数不正确: 期望 {low_count}, 实际 {stats.low_value_count}"
        )
    
    @given(segments=segments_list_strategy(min_size=0, max_size=30))
    @settings(max_examples=100)
    def test_多次更新后的统计一致性(self, segments: List[RecordingSegment]):
        """
        *对于任意* 录制片段集合，多次调用 update_from_segments 后统计仍保持一致。
        
        **Feature: smart-training-system, Property 5: 统计计算一致性**
        **验证: 需求 3.2**
        """
        stats = RecordingStatistics()
        
        # 多次更新（应该是幂等的）
        stats.update_from_segments(segments)
        stats.update_from_segments(segments)
        stats.update_from_segments(segments)
        
        # 验证属性：价值等级计数总和等于总片段数
        total_by_level = stats.high_value_count + stats.medium_value_count + stats.low_value_count
        
        assert total_by_level == stats.total_segments, (
            f"多次更新后统计不一致: 计数总和={total_by_level}, total_segments={stats.total_segments}"
        )
        
        # 验证总片段数正确
        assert stats.total_segments == len(segments), (
            f"多次更新后总片段数不正确: 期望 {len(segments)}, 实际 {stats.total_segments}"
        )
    
    @given(segments=segments_list_strategy(min_size=0, max_size=30))
    @settings(max_examples=100)
    def test_通过服务接口的统计一致性(self, segments: List[RecordingSegment]):
        """
        *对于任意* 录制片段集合，通过 StatisticsService 接口获取的统计数据必须一致。
        
        **Feature: smart-training-system, Property 5: 统计计算一致性**
        **验证: 需求 3.2**
        """
        stats_service = StatisticsService()
        stats_service.add_segments(segments)
        
        # 通过 get_value_counts 接口获取
        value_counts = stats_service.get_value_counts()
        
        # 通过 get_statistics 接口获取
        stats = stats_service.get_statistics()
        
        # 验证两种接口返回的数据一致
        assert value_counts['high'] == stats.high_value_count
        assert value_counts['medium'] == stats.medium_value_count
        assert value_counts['low'] == stats.low_value_count
        assert value_counts['total'] == stats.total_segments
        
        # 验证属性：价值等级计数总和等于总片段数
        total_by_level = value_counts['high'] + value_counts['medium'] + value_counts['low']
        
        assert total_by_level == value_counts['total'], (
            f"通过服务接口获取的统计不一致: 计数总和={total_by_level}, total={value_counts['total']}"
        )


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--hypothesis-show-statistics'])
