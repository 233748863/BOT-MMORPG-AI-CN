"""
属性测试：渐进式调整约束
Property 15: 对于任意参数调整，单次调整幅度不超过 aggressiveness 级别对应的步长倍数（保守=1x，平衡=2x，激进=3x）。

**Feature: smart-training-system, Property 15: 渐进式调整约束**
**验证: 需求 8.6, 9.2**
"""

import pytest
import tempfile
import shutil
from hypothesis import given, strategies as st, settings, assume

from 核心.自动调参 import (
    AutoTuner, PerformanceMetric, ParameterSpace, 
    AggressivenessLevel, get_default_parameter_spaces
)


# ==================== 策略定义 ====================

# 生成有效的性能指标
@st.composite
def valid_performance_metric(draw):
    """生成有效的 PerformanceMetric 对象"""
    return PerformanceMetric(
        action_success_rate=draw(st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)),
        state_accuracy=draw(st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)),
        stuck_count=draw(st.integers(min_value=0, max_value=100)),
        task_efficiency=draw(st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False))
    )


# 生成激进程度
aggressiveness_level = st.sampled_from([
    AggressivenessLevel.CONSERVATIVE,
    AggressivenessLevel.BALANCED,
    AggressivenessLevel.AGGRESSIVE
])


# 生成参数名称（从默认参数空间中选择）
default_param_names = st.sampled_from([
    'action_cooldown',
    'state_switch_threshold',
    'rule_priority_weight',
    'detection_confidence_threshold'
])


class Test渐进式调整约束属性:
    """
    Property 15: 渐进式调整约束
    
    *对于任意* 参数调整，单次调整幅度不超过 aggressiveness 级别对应的步长倍数（保守=1x，平衡=2x，激进=3x）。
    **验证: 需求 8.6, 9.2**
    """
    
    @given(
        aggressiveness=aggressiveness_level,
        param_name=default_param_names
    )
    @settings(max_examples=100)
    def test_单次调整幅度不超过步长倍数(
        self, 
        aggressiveness: AggressivenessLevel,
        param_name: str
    ):
        """
        *对于任意* 激进程度和参数，单次调整幅度必须不超过 step * multiplier。
        
        **Feature: smart-training-system, Property 15: 渐进式调整约束**
        **验证: 需求 8.6, 9.2**
        """
        temp_dir = tempfile.mkdtemp()
        try:
            # 创建 AutoTuner
            tuner = AutoTuner(
                enabled=True,
                aggressiveness=aggressiveness,
                tuning_dir=temp_dir
            )
            
            # 收集足够的性能指标（至少5个）
            for i in range(5):
                metric = PerformanceMetric(
                    action_success_rate=0.7,
                    state_accuracy=0.8,
                    stuck_count=1,
                    task_efficiency=0.6
                )
                tuner.collect_metric(metric)
            
            # 获取参数信息
            param = tuner.get_parameter(param_name)
            step = param.step
            multiplier = aggressiveness.get_step_multiplier()
            max_allowed_delta = step * multiplier
            
            # 执行调参
            record = tuner.tune_parameter(param_name)
            
            # 计算实际调整幅度
            actual_delta = abs(record.new_value - record.old_value)
            
            # 验证调整幅度不超过允许的最大值
            # 允许小的浮点误差 (1e-9)
            assert actual_delta <= max_allowed_delta + 1e-9, \
                f"参数 {param_name} 的调整幅度 {actual_delta} 超过了允许的最大值 {max_allowed_delta} " \
                f"(激进程度: {aggressiveness.value}, 步长: {step}, 倍数: {multiplier})"
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    @given(
        aggressiveness=aggressiveness_level,
        metrics=st.lists(valid_performance_metric(), min_size=5, max_size=20)
    )
    @settings(max_examples=100)
    def test_不同性能指标下调整幅度约束(
        self, 
        aggressiveness: AggressivenessLevel,
        metrics: list
    ):
        """
        *对于任意* 激进程度和性能指标序列，所有参数的调整幅度都必须符合渐进式约束。
        
        **Feature: smart-training-system, Property 15: 渐进式调整约束**
        **验证: 需求 8.6, 9.2**
        """
        temp_dir = tempfile.mkdtemp()
        try:
            tuner = AutoTuner(
                enabled=True,
                aggressiveness=aggressiveness,
                tuning_dir=temp_dir
            )
            
            # 收集性能指标
            for metric in metrics:
                tuner.collect_metric(metric)
            
            multiplier = aggressiveness.get_step_multiplier()
            
            # 对每个未锁定的参数进行调整测试
            for param_name in tuner.get_unlocked_parameters():
                param = tuner.get_parameter(param_name)
                step = param.step
                max_allowed_delta = step * multiplier
                
                # 执行调参
                record = tuner.tune_parameter(param_name)
                
                # 计算实际调整幅度
                actual_delta = abs(record.new_value - record.old_value)
                
                # 验证调整幅度
                assert actual_delta <= max_allowed_delta + 1e-9, \
                    f"参数 {param_name} 的调整幅度 {actual_delta} 超过了允许的最大值 {max_allowed_delta}"
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    @given(
        aggressiveness=aggressiveness_level,
        tune_count=st.integers(min_value=1, max_value=10)
    )
    @settings(max_examples=100)
    def test_多次调参每次都符合渐进式约束(
        self, 
        aggressiveness: AggressivenessLevel,
        tune_count: int
    ):
        """
        *对于任意* 激进程度和调参次数，每次调参的幅度都必须符合渐进式约束。
        
        **Feature: smart-training-system, Property 15: 渐进式调整约束**
        **验证: 需求 8.6, 9.2**
        """
        temp_dir = tempfile.mkdtemp()
        try:
            tuner = AutoTuner(
                enabled=True,
                aggressiveness=aggressiveness,
                tuning_dir=temp_dir
            )
            
            # 收集足够的性能指标
            for i in range(10):
                metric = PerformanceMetric(
                    action_success_rate=0.5 + i * 0.05,
                    state_accuracy=0.7,
                    stuck_count=i % 3,
                    task_efficiency=0.6
                )
                tuner.collect_metric(metric)
            
            multiplier = aggressiveness.get_step_multiplier()
            unlocked_params = tuner.get_unlocked_parameters()
            
            # 执行多次调参
            for i in range(tune_count):
                if not unlocked_params:
                    break
                
                param_name = unlocked_params[i % len(unlocked_params)]
                param = tuner.get_parameter(param_name)
                step = param.step
                max_allowed_delta = step * multiplier
                
                # 执行调参
                record = tuner.tune_parameter(param_name)
                
                # 计算实际调整幅度
                actual_delta = abs(record.new_value - record.old_value)
                
                # 验证调整幅度
                assert actual_delta <= max_allowed_delta + 1e-9, \
                    f"第 {i+1} 次调参: 参数 {param_name} 的调整幅度 {actual_delta} " \
                    f"超过了允许的最大值 {max_allowed_delta}"
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


class Test激进程度步长倍数:
    """测试激进程度与步长倍数的对应关系"""
    
    def test_保守模式步长倍数为1(self):
        """保守模式的步长倍数应该是1"""
        assert AggressivenessLevel.CONSERVATIVE.get_step_multiplier() == 1
    
    def test_平衡模式步长倍数为2(self):
        """平衡模式的步长倍数应该是2"""
        assert AggressivenessLevel.BALANCED.get_step_multiplier() == 2
    
    def test_激进模式步长倍数为3(self):
        """激进模式的步长倍数应该是3"""
        assert AggressivenessLevel.AGGRESSIVE.get_step_multiplier() == 3
    
    @given(aggressiveness=aggressiveness_level)
    @settings(max_examples=100)
    def test_步长倍数在有效范围内(self, aggressiveness: AggressivenessLevel):
        """
        *对于任意* 激进程度，步长倍数必须在 [1, 3] 范围内。
        
        **Feature: smart-training-system, Property 15: 渐进式调整约束**
        **验证: 需求 9.2**
        """
        multiplier = aggressiveness.get_step_multiplier()
        assert 1 <= multiplier <= 3, \
            f"激进程度 {aggressiveness.value} 的步长倍数 {multiplier} 不在有效范围 [1, 3] 内"


class Test边界情况:
    """测试渐进式调整的边界情况"""
    
    @given(aggressiveness=aggressiveness_level)
    @settings(max_examples=100)
    def test_参数接近边界时调整幅度受限(self, aggressiveness: AggressivenessLevel):
        """
        *对于任意* 激进程度，当参数接近边界时，实际调整幅度可能小于最大允许幅度，但不会超过。
        
        **Feature: smart-training-system, Property 15: 渐进式调整约束**
        **验证: 需求 8.6, 9.2**
        """
        temp_dir = tempfile.mkdtemp()
        try:
            tuner = AutoTuner(
                enabled=True,
                aggressiveness=aggressiveness,
                tuning_dir=temp_dir
            )
            
            # 收集性能指标
            for i in range(5):
                tuner.collect_metric(PerformanceMetric(
                    action_success_rate=0.8,
                    state_accuracy=0.8,
                    stuck_count=1,
                    task_efficiency=0.7
                ))
            
            multiplier = aggressiveness.get_step_multiplier()
            
            # 将参数设置到接近最大值
            param_name = 'action_cooldown'
            param = tuner.get_parameter(param_name)
            
            # 设置到接近最大值（只留一个步长的空间）
            near_max_value = param.max_value - param.step * 0.5
            tuner.set_parameter_value(param_name, near_max_value)
            
            step = param.step
            max_allowed_delta = step * multiplier
            
            # 执行调参
            record = tuner.tune_parameter(param_name)
            
            # 计算实际调整幅度
            actual_delta = abs(record.new_value - record.old_value)
            
            # 验证调整幅度不超过允许的最大值
            assert actual_delta <= max_allowed_delta + 1e-9, \
                f"接近边界时，参数 {param_name} 的调整幅度 {actual_delta} " \
                f"超过了允许的最大值 {max_allowed_delta}"
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    @given(aggressiveness=aggressiveness_level)
    @settings(max_examples=100)
    def test_参数在边界时调整幅度为零或反向(self, aggressiveness: AggressivenessLevel):
        """
        *对于任意* 激进程度，当参数已在边界时，调整幅度仍然符合渐进式约束。
        
        **Feature: smart-training-system, Property 15: 渐进式调整约束**
        **验证: 需求 8.6, 9.2**
        """
        temp_dir = tempfile.mkdtemp()
        try:
            tuner = AutoTuner(
                enabled=True,
                aggressiveness=aggressiveness,
                tuning_dir=temp_dir
            )
            
            # 收集性能指标
            for i in range(5):
                tuner.collect_metric(PerformanceMetric(
                    action_success_rate=0.8,
                    state_accuracy=0.8,
                    stuck_count=1,
                    task_efficiency=0.7
                ))
            
            multiplier = aggressiveness.get_step_multiplier()
            
            # 将参数设置到最大值
            param_name = 'action_cooldown'
            param = tuner.get_parameter(param_name)
            tuner.set_parameter_value(param_name, param.max_value)
            
            step = param.step
            max_allowed_delta = step * multiplier
            
            # 执行调参
            record = tuner.tune_parameter(param_name)
            
            # 计算实际调整幅度
            actual_delta = abs(record.new_value - record.old_value)
            
            # 验证调整幅度不超过允许的最大值
            assert actual_delta <= max_allowed_delta + 1e-9, \
                f"在边界时，参数 {param_name} 的调整幅度 {actual_delta} " \
                f"超过了允许的最大值 {max_allowed_delta}"
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--hypothesis-show-statistics'])
