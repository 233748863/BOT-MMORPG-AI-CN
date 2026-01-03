"""
属性测试：参数锁定有效性
Property 16: 对于任意被锁定的参数，自动调参过程中该参数值必须保持不变。

**Feature: smart-training-system, Property 16: 参数锁定有效性**
**验证: 需求 9.3**
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
default_param_names = list(get_default_parameter_spaces().keys())
param_name_strategy = st.sampled_from(default_param_names)


# 生成要锁定的参数子集
@st.composite
def locked_params_subset(draw):
    """生成要锁定的参数名称子集（至少锁定一个）"""
    params = default_param_names.copy()
    # 随机选择要锁定的参数数量（1到全部）
    num_to_lock = draw(st.integers(min_value=1, max_value=len(params)))
    # 随机选择要锁定的参数
    locked = draw(st.lists(
        st.sampled_from(params),
        min_size=num_to_lock,
        max_size=num_to_lock,
        unique=True
    ))
    return locked


class Test参数锁定有效性属性:
    """
    Property 16: 参数锁定有效性
    
    *对于任意* 被锁定的参数，自动调参过程中该参数值必须保持不变。
    **验证: 需求 9.3**
    """
    
    @given(
        param_name=param_name_strategy,
        metrics=st.lists(valid_performance_metric(), min_size=5, max_size=20),
        aggressiveness=aggressiveness_level
    )
    @settings(max_examples=100)
    def test_锁定参数在tune_parameter时保持不变(
        self, 
        param_name: str, 
        metrics: list, 
        aggressiveness: AggressivenessLevel
    ):
        """
        *对于任意* 被锁定的参数，调用 tune_parameter() 时该参数值必须保持不变。
        
        **Feature: smart-training-system, Property 16: 参数锁定有效性**
        **验证: 需求 9.3**
        """
        temp_dir = tempfile.mkdtemp()
        try:
            # 创建 AutoTuner
            tuner = AutoTuner(
                enabled=True,
                aggressiveness=aggressiveness,
                tuning_dir=temp_dir
            )
            
            # 收集性能指标
            for metric in metrics:
                tuner.collect_metric(metric)
            
            # 记录锁定前的参数值
            original_value = tuner.get_parameter(param_name).current_value
            
            # 锁定参数
            tuner.lock_parameter(param_name)
            
            # 尝试调整锁定的参数（应该抛出异常）
            with pytest.raises(ValueError):
                tuner.tune_parameter(param_name)
            
            # 验证参数值保持不变
            current_value = tuner.get_parameter(param_name).current_value
            assert current_value == original_value, \
                f"锁定参数 {param_name} 的值从 {original_value} 变为 {current_value}"
            
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    @given(
        locked_params=locked_params_subset(),
        metrics=st.lists(valid_performance_metric(), min_size=5, max_size=20),
        aggressiveness=aggressiveness_level,
        tune_cycles=st.integers(min_value=1, max_value=10)
    )
    @settings(max_examples=100)
    def test_锁定参数在auto_tune_cycle中保持不变(
        self, 
        locked_params: list, 
        metrics: list, 
        aggressiveness: AggressivenessLevel,
        tune_cycles: int
    ):
        """
        *对于任意* 被锁定的参数集合，多次自动调参循环后这些参数值必须保持不变。
        
        **Feature: smart-training-system, Property 16: 参数锁定有效性**
        **验证: 需求 9.3**
        """
        temp_dir = tempfile.mkdtemp()
        try:
            # 创建 AutoTuner
            tuner = AutoTuner(
                enabled=True,
                aggressiveness=aggressiveness,
                tuning_dir=temp_dir
            )
            
            # 收集性能指标
            for metric in metrics:
                tuner.collect_metric(metric)
            
            # 记录锁定前的参数值
            original_values = {}
            for param_name in locked_params:
                original_values[param_name] = tuner.get_parameter(param_name).current_value
            
            # 锁定参数
            for param_name in locked_params:
                tuner.lock_parameter(param_name)
            
            # 执行多次自动调参循环
            for _ in range(tune_cycles):
                tuner.auto_tune_cycle()
            
            # 验证所有锁定参数的值保持不变
            for param_name in locked_params:
                current_value = tuner.get_parameter(param_name).current_value
                assert current_value == original_values[param_name], \
                    f"锁定参数 {param_name} 的值从 {original_values[param_name]} 变为 {current_value}"
            
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    @given(
        param_name=param_name_strategy,
        adjustment_delta=st.floats(min_value=-100.0, max_value=100.0, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100)
    def test_锁定参数在ParameterSpace_adjust中保持不变(
        self, 
        param_name: str, 
        adjustment_delta: float
    ):
        """
        *对于任意* 被锁定的 ParameterSpace，调用 adjust() 时参数值必须保持不变。
        
        **Feature: smart-training-system, Property 16: 参数锁定有效性**
        **验证: 需求 9.3**
        """
        # 获取默认参数空间
        params = get_default_parameter_spaces()
        param = params[param_name]
        
        # 记录锁定前的值
        original_value = param.current_value
        
        # 锁定参数
        param.locked = True
        
        # 尝试调整
        result = param.adjust(adjustment_delta)
        
        # 验证值保持不变
        assert param.current_value == original_value, \
            f"锁定参数 {param_name} 的值从 {original_value} 变为 {param.current_value}"
        assert result == original_value, \
            f"adjust() 返回值 {result} 不等于原始值 {original_value}"
    
    @given(
        param_name=param_name_strategy,
        metrics=st.lists(valid_performance_metric(), min_size=5, max_size=20)
    )
    @settings(max_examples=100)
    def test_锁定参数在reset_to_defaults中保持不变(
        self, 
        param_name: str, 
        metrics: list
    ):
        """
        *对于任意* 被锁定的参数，调用 reset_to_defaults() 时该参数值必须保持不变。
        
        **Feature: smart-training-system, Property 16: 参数锁定有效性**
        **验证: 需求 9.3**
        """
        temp_dir = tempfile.mkdtemp()
        try:
            # 创建 AutoTuner
            tuner = AutoTuner(
                enabled=True,
                aggressiveness=AggressivenessLevel.BALANCED,
                tuning_dir=temp_dir
            )
            
            # 修改参数值（使其不等于默认值）
            param = tuner.get_parameter(param_name)
            new_value = param.min_value + (param.max_value - param.min_value) * 0.75
            tuner.set_parameter_value(param_name, new_value)
            
            # 记录锁定前的值
            original_value = tuner.get_parameter(param_name).current_value
            
            # 锁定参数
            tuner.lock_parameter(param_name)
            
            # 调用 reset_to_defaults
            tuner.reset_to_defaults()
            
            # 验证锁定参数的值保持不变
            current_value = tuner.get_parameter(param_name).current_value
            assert current_value == original_value, \
                f"锁定参数 {param_name} 的值从 {original_value} 变为 {current_value}"
            
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    @given(
        param_name=param_name_strategy,
        new_value=st.floats(min_value=0.0, max_value=2.0, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100)
    def test_锁定参数在set_parameter_value中保持不变(
        self, 
        param_name: str, 
        new_value: float
    ):
        """
        *对于任意* 被锁定的参数，调用 set_parameter_value() 时该参数值必须保持不变。
        
        **Feature: smart-training-system, Property 16: 参数锁定有效性**
        **验证: 需求 9.3**
        """
        temp_dir = tempfile.mkdtemp()
        try:
            # 创建 AutoTuner
            tuner = AutoTuner(
                enabled=True,
                aggressiveness=AggressivenessLevel.BALANCED,
                tuning_dir=temp_dir
            )
            
            # 记录锁定前的值
            original_value = tuner.get_parameter(param_name).current_value
            
            # 锁定参数
            tuner.lock_parameter(param_name)
            
            # 尝试设置新值
            result = tuner.set_parameter_value(param_name, new_value)
            
            # 验证设置失败
            assert result == False, \
                f"set_parameter_value() 应该返回 False，但返回了 {result}"
            
            # 验证参数值保持不变
            current_value = tuner.get_parameter(param_name).current_value
            assert current_value == original_value, \
                f"锁定参数 {param_name} 的值从 {original_value} 变为 {current_value}"
            
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


class Test参数锁定状态一致性:
    """测试参数锁定状态的一致性"""
    
    @given(
        param_name=param_name_strategy,
        lock_unlock_sequence=st.lists(st.booleans(), min_size=1, max_size=20)
    )
    @settings(max_examples=100)
    def test_锁定解锁序列后状态正确(
        self, 
        param_name: str, 
        lock_unlock_sequence: list
    ):
        """
        *对于任意* 锁定/解锁操作序列，最终的锁定状态应该与最后一次操作一致。
        
        **Feature: smart-training-system, Property 16: 参数锁定有效性**
        **验证: 需求 9.3**
        """
        temp_dir = tempfile.mkdtemp()
        try:
            tuner = AutoTuner(
                enabled=True,
                aggressiveness=AggressivenessLevel.BALANCED,
                tuning_dir=temp_dir
            )
            
            # 执行锁定/解锁序列
            for should_lock in lock_unlock_sequence:
                if should_lock:
                    tuner.lock_parameter(param_name)
                else:
                    tuner.unlock_parameter(param_name)
            
            # 验证最终状态与最后一次操作一致
            expected_locked = lock_unlock_sequence[-1]
            actual_locked = tuner.is_parameter_locked(param_name)
            
            assert actual_locked == expected_locked, \
                f"参数 {param_name} 的锁定状态应该是 {expected_locked}，但实际是 {actual_locked}"
            
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    @given(locked_params=locked_params_subset())
    @settings(max_examples=100)
    def test_get_locked_parameters返回正确列表(self, locked_params: list):
        """
        *对于任意* 被锁定的参数集合，get_locked_parameters() 应该返回正确的列表。
        
        **Feature: smart-training-system, Property 16: 参数锁定有效性**
        **验证: 需求 9.3**
        """
        temp_dir = tempfile.mkdtemp()
        try:
            tuner = AutoTuner(
                enabled=True,
                aggressiveness=AggressivenessLevel.BALANCED,
                tuning_dir=temp_dir
            )
            
            # 锁定参数
            for param_name in locked_params:
                tuner.lock_parameter(param_name)
            
            # 获取锁定参数列表
            actual_locked = set(tuner.get_locked_parameters())
            expected_locked = set(locked_params)
            
            assert actual_locked == expected_locked, \
                f"锁定参数列表不匹配: 期望 {expected_locked}，实际 {actual_locked}"
            
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--hypothesis-show-statistics'])
