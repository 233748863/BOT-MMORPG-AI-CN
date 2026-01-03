"""
属性测试：性能数据持久化Round-Trip
Property 12: 对于任意 PerformanceMetric，存储后再读取必须得到等价的数据。

**Feature: smart-training-system, Property 12: 性能数据持久化Round-Trip**
**验证: 需求 7.4**
"""

import pytest
import tempfile
import shutil
from datetime import datetime
from hypothesis import given, strategies as st, settings

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


def metrics_list_strategy(min_size=1, max_size=10):
    """生成性能指标列表"""
    return st.lists(performance_metric_strategy(), min_size=min_size, max_size=max_size)


def create_temp_tuner(temp_dir):
    """创建带有指定目录的 AutoTuner 实例"""
    tuner = AutoTuner(
        enabled=True,
        aggressiveness=AggressivenessLevel.BALANCED,
        tuning_dir=temp_dir
    )
    return tuner


class TestPerformanceMetricPersistenceRoundTrip:
    """
    Property 12: 性能数据持久化Round-Trip
    验证: 需求 7.4
    
    对于任意 PerformanceMetric，存储后再读取必须得到等价的数据。
    """
    
    @given(metric=performance_metric_strategy())
    @settings(max_examples=100, deadline=None)
    def test_single_metric_round_trip(self, metric):
        """
        对于任意单个性能指标，存储后重新加载应得到等价的数据。
        Feature: smart-training-system, Property 12: 性能数据持久化Round-Trip
        """
        temp_dir = tempfile.mkdtemp()
        try:
            # 创建第一个 tuner 并收集指标
            tuner1 = create_temp_tuner(temp_dir)
            tuner1.collect_metric(metric)
            
            # 创建第二个 tuner，从同一目录加载数据
            tuner2 = create_temp_tuner(temp_dir)
            loaded_metrics = tuner2.get_metrics()
            
            # 验证加载的指标数量
            assert len(loaded_metrics) == 1
            
            # 验证加载的指标与原始指标等价
            loaded = loaded_metrics[0]
            assert loaded.action_success_rate == pytest.approx(metric.action_success_rate, abs=1e-9)
            assert loaded.state_accuracy == pytest.approx(metric.state_accuracy, abs=1e-9)
            assert loaded.stuck_count == metric.stuck_count
            assert loaded.task_efficiency == pytest.approx(metric.task_efficiency, abs=1e-9)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    @given(metrics=metrics_list_strategy(min_size=1, max_size=10))
    @settings(max_examples=100, deadline=None)
    def test_multiple_metrics_round_trip(self, metrics):
        """
        对于任意多个性能指标，存储后重新加载应得到等价的数据列表。
        Feature: smart-training-system, Property 12: 性能数据持久化Round-Trip
        """
        temp_dir = tempfile.mkdtemp()
        try:
            # 创建第一个 tuner 并收集所有指标
            tuner1 = create_temp_tuner(temp_dir)
            for metric in metrics:
                tuner1.collect_metric(metric)
            
            # 创建第二个 tuner，从同一目录加载数据
            tuner2 = create_temp_tuner(temp_dir)
            loaded_metrics = tuner2.get_metrics()
            
            # 验证加载的指标数量
            assert len(loaded_metrics) == len(metrics)
            
            # 验证每个加载的指标与原始指标等价
            for original, loaded in zip(metrics, loaded_metrics):
                assert loaded.action_success_rate == pytest.approx(original.action_success_rate, abs=1e-9)
                assert loaded.state_accuracy == pytest.approx(original.state_accuracy, abs=1e-9)
                assert loaded.stuck_count == original.stuck_count
                assert loaded.task_efficiency == pytest.approx(original.task_efficiency, abs=1e-9)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    @given(metric=performance_metric_strategy())
    @settings(max_examples=100, deadline=None)
    def test_metric_to_dict_from_dict_round_trip(self, metric):
        """
        对于任意性能指标，to_dict 后再 from_dict 应得到等价的对象。
        Feature: smart-training-system, Property 12: 性能数据持久化Round-Trip
        """
        # 序列化为字典
        data = metric.to_dict()
        
        # 从字典反序列化
        restored = PerformanceMetric.from_dict(data)
        
        # 验证等价性
        assert restored.action_success_rate == pytest.approx(metric.action_success_rate, abs=1e-9)
        assert restored.state_accuracy == pytest.approx(metric.state_accuracy, abs=1e-9)
        assert restored.stuck_count == metric.stuck_count
        assert restored.task_efficiency == pytest.approx(metric.task_efficiency, abs=1e-9)
    
    @given(metrics=metrics_list_strategy(min_size=1, max_size=5))
    @settings(max_examples=100, deadline=None)
    def test_persistence_preserves_order(self, metrics):
        """
        对于任意性能指标列表，持久化后加载应保持原始顺序。
        Feature: smart-training-system, Property 12: 性能数据持久化Round-Trip
        """
        temp_dir = tempfile.mkdtemp()
        try:
            # 创建第一个 tuner 并按顺序收集指标
            tuner1 = create_temp_tuner(temp_dir)
            for metric in metrics:
                tuner1.collect_metric(metric)
            
            # 创建第二个 tuner，从同一目录加载数据
            tuner2 = create_temp_tuner(temp_dir)
            loaded_metrics = tuner2.get_metrics()
            
            # 验证顺序保持一致（通过比较各指标的值）
            for i, (original, loaded) in enumerate(zip(metrics, loaded_metrics)):
                assert loaded.action_success_rate == pytest.approx(original.action_success_rate, abs=1e-9), \
                    f"第 {i} 个指标的 action_success_rate 不匹配"
                assert loaded.state_accuracy == pytest.approx(original.state_accuracy, abs=1e-9), \
                    f"第 {i} 个指标的 state_accuracy 不匹配"
                assert loaded.stuck_count == original.stuck_count, \
                    f"第 {i} 个指标的 stuck_count 不匹配"
                assert loaded.task_efficiency == pytest.approx(original.task_efficiency, abs=1e-9), \
                    f"第 {i} 个指标的 task_efficiency 不匹配"
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
