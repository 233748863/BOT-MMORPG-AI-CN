"""
属性测试：参数保留/回滚决策正确性
Property 14: 对于任意参数调整，如果调整后性能提升（is_performance_degraded 返回 False），则参数保留；
如果性能下降，则参数回滚到调整前的值。

**Feature: smart-training-system, Property 14: 参数保留/回滚决策正确性**
**验证: 需求 8.4, 8.5**
"""

import pytest
import tempfile
import shutil
from datetime import datetime
from hypothesis import given, strategies as st, settings, assume

from 核心.自动调参 import (
    AutoTuner,
    PerformanceMetric,
    TuningRecord,
    AggressivenessLevel
)


# ==================== 策略定义 ====================

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


@st.composite
def performance_pair_improved_strategy(draw):
    """生成性能提升的指标对 (before, after)，确保 after 的综合分数 >= before"""
    before = draw(performance_metric_strategy())
    
    # 生成一个性能更好或相等的 after 指标
    # 通过提高各项指标或减少卡住次数来实现
    after_action_rate = draw(st.floats(
        min_value=before.action_success_rate, 
        max_value=1.0, 
        allow_nan=False, 
        allow_infinity=False
    ))
    after_state_accuracy = draw(st.floats(
        min_value=before.state_accuracy, 
        max_value=1.0, 
        allow_nan=False, 
        allow_infinity=False
    ))
    after_stuck_count = draw(st.integers(
        min_value=0, 
        max_value=before.stuck_count
    ))
    after_task_efficiency = draw(st.floats(
        min_value=before.task_efficiency, 
        max_value=1.0, 
        allow_nan=False, 
        allow_infinity=False
    ))
    
    after = PerformanceMetric(
        timestamp=datetime.now(),
        action_success_rate=after_action_rate,
        state_accuracy=after_state_accuracy,
        stuck_count=after_stuck_count,
        task_efficiency=after_task_efficiency
    )
    
    return before, after


@st.composite
def performance_pair_degraded_strategy(draw):
    """生成性能下降的指标对 (before, after)，确保汇总后 after 的综合分数 < before
    
    注意：stuck_count 在汇总时是累加的，所以需要使用较小的值以避免惩罚过大
    """
    # 先生成一个较好的 before 指标
    # 使用较小的 stuck_count 以避免累加后惩罚过大
    before = PerformanceMetric(
        timestamp=datetime.now(),
        action_success_rate=draw(st.floats(min_value=0.7, max_value=1.0, allow_nan=False, allow_infinity=False)),
        state_accuracy=draw(st.floats(min_value=0.7, max_value=1.0, allow_nan=False, allow_infinity=False)),
        stuck_count=0,  # 使用0以避免累加后惩罚过大
        task_efficiency=draw(st.floats(min_value=0.7, max_value=1.0, allow_nan=False, allow_infinity=False))
    )
    
    # 生成一个性能更差的 after 指标
    # 降低各项指标，增加 stuck_count
    after_action_rate = draw(st.floats(
        min_value=0.0, 
        max_value=0.4, 
        allow_nan=False, 
        allow_infinity=False
    ))
    after_state_accuracy = draw(st.floats(
        min_value=0.0, 
        max_value=0.4, 
        allow_nan=False, 
        allow_infinity=False
    ))
    # 使用较小的 stuck_count，因为会被累加（5个指标累加后最多5）
    after_stuck_count = draw(st.integers(min_value=1, max_value=1))
    after_task_efficiency = draw(st.floats(
        min_value=0.0, 
        max_value=0.4, 
        allow_nan=False, 
        allow_infinity=False
    ))
    
    after = PerformanceMetric(
        timestamp=datetime.now(),
        action_success_rate=after_action_rate,
        state_accuracy=after_state_accuracy,
        stuck_count=after_stuck_count,
        task_efficiency=after_task_efficiency
    )
    
    # 模拟汇总后的分数（5个指标汇总）
    # before: stuck_count 累加 = 0*5 = 0
    # after: stuck_count 累加 = 1*5 = 5
    aggregated_before = PerformanceMetric(
        timestamp=datetime.now(),
        action_success_rate=before.action_success_rate,
        state_accuracy=before.state_accuracy,
        stuck_count=before.stuck_count * 5,  # 模拟5个指标累加
        task_efficiency=before.task_efficiency
    )
    aggregated_after = PerformanceMetric(
        timestamp=datetime.now(),
        action_success_rate=after.action_success_rate,
        state_accuracy=after.state_accuracy,
        stuck_count=after.stuck_count * 5,  # 模拟5个指标累加
        task_efficiency=after.task_efficiency
    )
    
    # 确保汇总后 after 的分数确实低于 before
    assume(aggregated_after.get_overall_score() < aggregated_before.get_overall_score())
    
    return before, after


aggressiveness_level = st.sampled_from([
    AggressivenessLevel.CONSERVATIVE,
    AggressivenessLevel.BALANCED,
    AggressivenessLevel.AGGRESSIVE
])


def create_temp_tuner(temp_dir, aggressiveness=AggressivenessLevel.BALANCED):
    """创建带有指定目录的 AutoTuner 实例"""
    tuner = AutoTuner(
        enabled=True,
        aggressiveness=aggressiveness,
        tuning_dir=temp_dir
    )
    return tuner


class Test参数保留回滚决策属性:
    """
    Property 14: 参数保留/回滚决策正确性
    
    *对于任意* 参数调整，如果调整后性能提升（is_performance_degraded 返回 False），则参数保留；
    如果性能下降，则参数回滚到调整前的值。
    **验证: 需求 8.4, 8.5**
    """
    
    @given(
        before=performance_metric_strategy(),
        after=performance_metric_strategy()
    )
    @settings(max_examples=100, deadline=None)
    def test_is_performance_degraded_一致性(self, before: PerformanceMetric, after: PerformanceMetric):
        """
        *对于任意* 两个性能指标，is_performance_degraded 的返回值应与综合分数比较一致。
        
        **Feature: smart-training-system, Property 14: 参数保留/回滚决策正确性**
        **验证: 需求 8.4, 8.5**
        """
        temp_dir = tempfile.mkdtemp()
        try:
            tuner = create_temp_tuner(temp_dir)
            
            # 计算综合分数
            before_score = before.get_overall_score()
            after_score = after.get_overall_score()
            
            # 调用 is_performance_degraded
            is_degraded = tuner.is_performance_degraded(after, before)
            
            # 验证一致性：性能下降当且仅当 after_score < before_score
            expected_degraded = after_score < before_score
            assert is_degraded == expected_degraded, \
                f"is_performance_degraded 返回 {is_degraded}，但期望 {expected_degraded}。" \
                f"before_score={before_score}, after_score={after_score}"
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    @given(pair=performance_pair_improved_strategy())
    @settings(max_examples=100, deadline=None)
    def test_性能提升时参数保留(self, pair):
        """
        *对于任意* 性能提升的情况，evaluate_and_rollback_if_needed 应返回 True（保留参数）。
        
        **Feature: smart-training-system, Property 14: 参数保留/回滚决策正确性**
        **验证: 需求 8.4**
        """
        before, after = pair
        temp_dir = tempfile.mkdtemp()
        try:
            tuner = create_temp_tuner(temp_dir)
            
            # 收集足够的性能指标
            for _ in range(5):
                tuner.collect_metric(before)
            
            # 获取一个未锁定的参数
            unlocked_params = tuner.get_unlocked_parameters()
            assume(len(unlocked_params) > 0)
            param_name = unlocked_params[0]
            
            # 执行参数调整
            record = tuner.tune_parameter(param_name)
            old_value = record.old_value
            new_value = record.new_value
            
            # 清空指标，收集"调整后"的性能指标（模拟性能提升）
            tuner.clear_metrics()
            for _ in range(5):
                tuner.collect_metric(after)
            
            # 评估并决定是否回滚
            should_keep = tuner.evaluate_and_rollback_if_needed(record)
            
            # 验证：性能提升时应保留参数
            # 注意：如果 after 的分数 >= before 的分数，则不应回滚
            if after.get_overall_score() >= before.get_overall_score():
                assert should_keep is True, \
                    f"性能提升时应保留参数，但返回了 {should_keep}"
                # 验证参数值保持为调整后的值
                current_value = tuner.get_parameter(param_name).current_value
                assert current_value == new_value, \
                    f"参数应保持为调整后的值 {new_value}，但当前值为 {current_value}"
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    @given(pair=performance_pair_degraded_strategy())
    @settings(max_examples=100, deadline=None)
    def test_性能下降时参数回滚(self, pair):
        """
        *对于任意* 性能下降的情况，evaluate_and_rollback_if_needed 应返回 False（回滚参数）。
        
        **Feature: smart-training-system, Property 14: 参数保留/回滚决策正确性**
        **验证: 需求 8.5**
        """
        before, after = pair
        temp_dir = tempfile.mkdtemp()
        try:
            tuner = create_temp_tuner(temp_dir)
            
            # 收集足够的性能指标（调整前）
            for _ in range(5):
                tuner.collect_metric(before)
            
            # 获取一个未锁定的参数
            unlocked_params = tuner.get_unlocked_parameters()
            assume(len(unlocked_params) > 0)
            param_name = unlocked_params[0]
            
            # 记录调整前的值
            old_value = tuner.get_parameter(param_name).current_value
            
            # 执行参数调整
            record = tuner.tune_parameter(param_name)
            
            # 清空指标，收集"调整后"的性能指标（模拟性能下降）
            tuner.clear_metrics()
            for _ in range(5):
                tuner.collect_metric(after)
            
            # 评估并决定是否回滚
            should_keep = tuner.evaluate_and_rollback_if_needed(record)
            
            # 验证：性能下降时应回滚参数
            assert should_keep is False, \
                f"性能下降时应回滚参数，但返回了 {should_keep}"
            
            # 验证参数值已回滚到调整前的值
            current_value = tuner.get_parameter(param_name).current_value
            assert current_value == old_value, \
                f"参数应回滚到调整前的值 {old_value}，但当前值为 {current_value}"
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    @given(
        aggressiveness=aggressiveness_level,
        pair=performance_pair_degraded_strategy()
    )
    @settings(max_examples=100, deadline=None)
    def test_不同激进程度下回滚决策一致(self, aggressiveness, pair):
        """
        *对于任意* 激进程度设置，性能下降时都应该回滚参数。
        
        **Feature: smart-training-system, Property 14: 参数保留/回滚决策正确性**
        **验证: 需求 8.4, 8.5**
        """
        before, after = pair
        temp_dir = tempfile.mkdtemp()
        try:
            tuner = create_temp_tuner(temp_dir, aggressiveness)
            
            # 收集足够的性能指标
            for _ in range(5):
                tuner.collect_metric(before)
            
            # 获取一个未锁定的参数
            unlocked_params = tuner.get_unlocked_parameters()
            assume(len(unlocked_params) > 0)
            param_name = unlocked_params[0]
            
            # 记录调整前的值
            old_value = tuner.get_parameter(param_name).current_value
            
            # 执行参数调整
            record = tuner.tune_parameter(param_name)
            
            # 清空指标，收集"调整后"的性能指标
            tuner.clear_metrics()
            for _ in range(5):
                tuner.collect_metric(after)
            
            # 评估并决定是否回滚
            should_keep = tuner.evaluate_and_rollback_if_needed(record)
            
            # 验证：性能下降时应回滚
            assert should_keep is False, \
                f"激进程度 {aggressiveness} 下，性能下降时应回滚参数"
            
            # 验证参数值已回滚
            current_value = tuner.get_parameter(param_name).current_value
            assert current_value == old_value, \
                f"参数应回滚到 {old_value}，但当前值为 {current_value}"
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    @given(metric=performance_metric_strategy())
    @settings(max_examples=100, deadline=None)
    def test_rollback_方法正确恢复参数值(self, metric: PerformanceMetric):
        """
        *对于任意* 调参记录，rollback 方法应正确恢复参数到调整前的值。
        
        **Feature: smart-training-system, Property 14: 参数保留/回滚决策正确性**
        **验证: 需求 8.5**
        """
        temp_dir = tempfile.mkdtemp()
        try:
            tuner = create_temp_tuner(temp_dir)
            
            # 收集足够的性能指标
            for _ in range(5):
                tuner.collect_metric(metric)
            
            # 获取一个未锁定的参数
            unlocked_params = tuner.get_unlocked_parameters()
            assume(len(unlocked_params) > 0)
            param_name = unlocked_params[0]
            
            # 记录调整前的值
            old_value = tuner.get_parameter(param_name).current_value
            
            # 执行参数调整
            record = tuner.tune_parameter(param_name)
            new_value = record.new_value
            
            # 验证参数已被调整
            assert tuner.get_parameter(param_name).current_value == new_value
            
            # 执行回滚
            success = tuner.rollback(record)
            
            # 验证回滚成功
            assert success is True, "回滚应该成功"
            
            # 验证参数值已恢复
            current_value = tuner.get_parameter(param_name).current_value
            assert current_value == old_value, \
                f"回滚后参数应为 {old_value}，但当前值为 {current_value}"
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


class Test性能分数计算一致性:
    """测试性能分数计算的一致性，作为保留/回滚决策的基础"""
    
    @given(metric=performance_metric_strategy())
    @settings(max_examples=100, deadline=None)
    def test_综合分数在有效范围内(self, metric: PerformanceMetric):
        """
        *对于任意* 性能指标，综合分数应在 [0.0, 1.0] 范围内。
        
        **Feature: smart-training-system, Property 14: 参数保留/回滚决策正确性**
        **验证: 需求 8.4, 8.5**
        """
        score = metric.get_overall_score()
        assert 0.0 <= score <= 1.0, \
            f"综合分数 {score} 不在 [0.0, 1.0] 范围内"
    
    @given(
        metric1=performance_metric_strategy(),
        metric2=performance_metric_strategy()
    )
    @settings(max_examples=100, deadline=None)
    def test_相同指标产生相同分数(self, metric1: PerformanceMetric, metric2: PerformanceMetric):
        """
        *对于任意* 两个具有相同属性值的性能指标，应产生相同的综合分数。
        
        **Feature: smart-training-system, Property 14: 参数保留/回滚决策正确性**
        **验证: 需求 8.4, 8.5**
        """
        # 创建一个与 metric1 属性相同的新指标
        same_metric = PerformanceMetric(
            timestamp=datetime.now(),
            action_success_rate=metric1.action_success_rate,
            state_accuracy=metric1.state_accuracy,
            stuck_count=metric1.stuck_count,
            task_efficiency=metric1.task_efficiency
        )
        
        score1 = metric1.get_overall_score()
        score_same = same_metric.get_overall_score()
        
        assert score1 == pytest.approx(score_same, abs=1e-9), \
            f"相同属性的指标应产生相同分数，但得到 {score1} 和 {score_same}"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--hypothesis-show-statistics'])
