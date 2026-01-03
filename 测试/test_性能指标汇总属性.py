"""
属性测试：性能指标汇总正确性
Property 11: 对于任意时间窗口内的性能指标集合，汇总后的各项指标必须是该窗口内所有指标的正确聚合。

**Feature: smart-training-system, Property 11: 性能指标汇总正确性**
**验证: 需求 7.2**
"""

import pytest
import tempfile
import shutil
from datetime import datetime
from hypothesis import given, strategies as st, settings, assume

from 核心.自动调参 import (
    AutoTuner,
    PerformanceMetric,
    AggressivenessLevel
)


def valid_rate_strategy():
    """生成有效的比率值 (0.0 - 1.0)"""
    return st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)


def valid_stuck_count_strategy():
    """生成有效的卡住次数 (非负整数)"""
    return st.integers(min_value=0, max_value=100)


@st.composite
def performance_metric_strategy(draw):
    """生成有效的性能指标"""
    return PerformanceMetric(
        timestamp=datetime.now(),
        action_success_rate=draw(valid_rate_strategy()),
        state_accuracy=draw(valid_rate_strategy()),
        stuck_count=draw(valid_stuck_count_strategy()),
        task_efficiency=draw(valid_rate_strategy())
    )


def metrics_list_strategy(min_size=0, max_size=20):
    """生成性能指标列表"""
    return st.lists(performance_metric_strategy(), min_size=min_size, max_size=max_size)


def create_temp_tuner():
    """创建带有临时目录的 AutoTuner 实例"""
    temp_dir = tempfile.mkdtemp()
    tuner = AutoTuner(
        enabled=True,
        aggressiveness=AggressivenessLevel.BALANCED,
        tuning_dir=temp_dir
    )
    return tuner, temp_dir


def cleanup_temp_dir(temp_dir):
    """清理临时目录"""
    shutil.rmtree(temp_dir, ignore_errors=True)


class TestMetricsAggregation:
    """
    Property 11: 性能指标汇总正确性
    验证: 需求 7.2
    """
    
    @given(metrics=metrics_list_strategy(min_size=1, max_size=20))
    @settings(max_examples=100)
    def test_average_metrics_aggregation(self, metrics):
        """
        对于任意非空性能指标集合，汇总后的平均值指标必须等于所有指标的算术平均值。
        Feature: smart-training-system, Property 11
        """
        tuner, temp_dir = create_temp_tuner()
        try:
            for metric in metrics:
                tuner.collect_metric(metric)
            
            aggregated = tuner.get_aggregated_metrics(window_minutes=60)
            
            count = len(metrics)
            expected_action = sum(m.action_success_rate for m in metrics) / count
            expected_state = sum(m.state_accuracy for m in metrics) / count
            expected_task = sum(m.task_efficiency for m in metrics) / count
            
            assert abs(aggregated.action_success_rate - expected_action) < 1e-9
            assert abs(aggregated.state_accuracy - expected_state) < 1e-9
            assert abs(aggregated.task_efficiency - expected_task) < 1e-9
        finally:
            cleanup_temp_dir(temp_dir)
    
    @given(metrics=metrics_list_strategy(min_size=1, max_size=20))
    @settings(max_examples=100)
    def test_sum_metrics_aggregation(self, metrics):
        """
        对于任意非空性能指标集合，汇总后的 stuck_count 必须等于所有指标的累加值。
        Feature: smart-training-system, Property 11
        """
        tuner, temp_dir = create_temp_tuner()
        try:
            for metric in metrics:
                tuner.collect_metric(metric)
            
            aggregated = tuner.get_aggregated_metrics(window_minutes=60)
            expected_stuck = sum(m.stuck_count for m in metrics)
            
            assert aggregated.stuck_count == expected_stuck
        finally:
            cleanup_temp_dir(temp_dir)
    
    @given(st.just(None))
    @settings(max_examples=10)
    def test_empty_metrics_returns_default(self, _):
        """
        对于空的性能指标集合，汇总应返回默认值。
        Feature: smart-training-system, Property 11
        """
        tuner, temp_dir = create_temp_tuner()
        try:
            aggregated = tuner.get_aggregated_metrics(window_minutes=60)
            
            assert aggregated.action_success_rate == 0.0
            assert aggregated.state_accuracy == 0.0
            assert aggregated.stuck_count == 0
            assert aggregated.task_efficiency == 0.0
        finally:
            cleanup_temp_dir(temp_dir)
    
    @given(metrics=metrics_list_strategy(min_size=2, max_size=10))
    @settings(max_examples=100)
    def test_aggregated_metrics_in_valid_range(self, metrics):
        """
        对于任意性能指标集合，汇总后的比率指标必须在 [0.0, 1.0] 范围内。
        Feature: smart-training-system, Property 11
        """
        tuner, temp_dir = create_temp_tuner()
        try:
            for metric in metrics:
                tuner.collect_metric(metric)
            
            aggregated = tuner.get_aggregated_metrics(window_minutes=60)
            
            assert 0.0 <= aggregated.action_success_rate <= 1.0
            assert 0.0 <= aggregated.state_accuracy <= 1.0
            assert 0.0 <= aggregated.task_efficiency <= 1.0
            assert aggregated.stuck_count >= 0
        finally:
            cleanup_temp_dir(temp_dir)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
