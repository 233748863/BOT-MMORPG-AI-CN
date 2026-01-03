"""
属性测试：默认值恢复正确性
Property 17: 对于任意参数，调用 reset_to_defaults 后，该参数的 current_value 必须等于 default_value。

**Feature: smart-training-system, Property 17: 默认值恢复正确性**
**验证: 需求 9.5**
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


# 生成参数值修改映射
@st.composite
def param_value_modifications(draw):
    """生成参数值修改映射（参数名 -> 新值比例）"""
    params = get_default_parameter_spaces()
    modifications = {}
    for name, param in params.items():
        # 随机决定是否修改此参数
        if draw(st.booleans()):
            # 生成一个在有效范围内的新值比例 (0.0 到 1.0)
            ratio = draw(st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False))
            # 计算实际值
            new_value = param.min_value + (param.max_value - param.min_value) * ratio
            modifications[name] = new_value
    return modifications


class Test默认值恢复正确性属性:
    """
    Property 17: 默认值恢复正确性
    
    *对于任意* 参数，调用 reset_to_defaults 后，该参数的 current_value 必须等于 default_value。
    **验证: 需求 9.5**
    """
    
    @given(
        param_name=param_name_strategy,
        value_ratio=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100)
    def test_单个参数重置后等于默认值(
        self, 
        param_name: str, 
        value_ratio: float
    ):
        """
        *对于任意* 单个参数，修改后调用 reset_to_defaults，其 current_value 必须等于 default_value。
        
        **Feature: smart-training-system, Property 17: 默认值恢复正确性**
        **验证: 需求 9.5**
        """
        temp_dir = tempfile.mkdtemp()
        try:
            # 创建 AutoTuner
            tuner = AutoTuner(
                enabled=True,
                aggressiveness=AggressivenessLevel.BALANCED,
                tuning_dir=temp_dir
            )
            
            # 获取参数信息
            param = tuner.get_parameter(param_name)
            default_value = param.default_value
            
            # 计算新值（在有效范围内）
            new_value = param.min_value + (param.max_value - param.min_value) * value_ratio
            
            # 修改参数值
            tuner.set_parameter_value(param_name, new_value)
            
            # 调用 reset_to_defaults
            tuner.reset_to_defaults()
            
            # 验证参数值等于默认值
            current_value = tuner.get_parameter(param_name).current_value
            assert current_value == default_value, \
                f"参数 {param_name} 重置后的值 {current_value} 不等于默认值 {default_value}"
            
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    @given(modifications=param_value_modifications())
    @settings(max_examples=100)
    def test_所有参数重置后等于默认值(self, modifications: dict):
        """
        *对于任意* 参数修改组合，调用 reset_to_defaults 后，所有参数的 current_value 必须等于 default_value。
        
        **Feature: smart-training-system, Property 17: 默认值恢复正确性**
        **验证: 需求 9.5**
        """
        temp_dir = tempfile.mkdtemp()
        try:
            # 创建 AutoTuner
            tuner = AutoTuner(
                enabled=True,
                aggressiveness=AggressivenessLevel.BALANCED,
                tuning_dir=temp_dir
            )
            
            # 应用所有修改
            for param_name, new_value in modifications.items():
                tuner.set_parameter_value(param_name, new_value)
            
            # 调用 reset_to_defaults
            tuner.reset_to_defaults()
            
            # 验证所有参数值等于默认值
            for param_name, param in tuner.get_all_parameters().items():
                assert param.current_value == param.default_value, \
                    f"参数 {param_name} 重置后的值 {param.current_value} 不等于默认值 {param.default_value}"
            
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    @given(
        param_name=param_name_strategy,
        value_ratio=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100)
    def test_单个参数使用reset_parameter_to_default重置(
        self, 
        param_name: str, 
        value_ratio: float
    ):
        """
        *对于任意* 单个参数，调用 reset_parameter_to_default 后，其 current_value 必须等于 default_value。
        
        **Feature: smart-training-system, Property 17: 默认值恢复正确性**
        **验证: 需求 9.5**
        """
        temp_dir = tempfile.mkdtemp()
        try:
            # 创建 AutoTuner
            tuner = AutoTuner(
                enabled=True,
                aggressiveness=AggressivenessLevel.BALANCED,
                tuning_dir=temp_dir
            )
            
            # 获取参数信息
            param = tuner.get_parameter(param_name)
            default_value = param.default_value
            
            # 计算新值（在有效范围内）
            new_value = param.min_value + (param.max_value - param.min_value) * value_ratio
            
            # 修改参数值
            tuner.set_parameter_value(param_name, new_value)
            
            # 调用 reset_parameter_to_default
            result = tuner.reset_parameter_to_default(param_name)
            
            # 验证重置成功
            assert result == True, f"reset_parameter_to_default 应该返回 True"
            
            # 验证参数值等于默认值
            current_value = tuner.get_parameter(param_name).current_value
            assert current_value == default_value, \
                f"参数 {param_name} 重置后的值 {current_value} 不等于默认值 {default_value}"
            
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    @given(
        param_name=param_name_strategy,
        tune_cycles=st.integers(min_value=1, max_value=5),
        metrics=st.lists(valid_performance_metric(), min_size=5, max_size=10)
    )
    @settings(max_examples=100)
    def test_调参后重置恢复默认值(
        self, 
        param_name: str, 
        tune_cycles: int,
        metrics: list
    ):
        """
        *对于任意* 参数，经过多次自动调参后调用 reset_to_defaults，其 current_value 必须等于 default_value。
        
        **Feature: smart-training-system, Property 17: 默认值恢复正确性**
        **验证: 需求 9.5**
        """
        temp_dir = tempfile.mkdtemp()
        try:
            # 创建 AutoTuner
            tuner = AutoTuner(
                enabled=True,
                aggressiveness=AggressivenessLevel.BALANCED,
                tuning_dir=temp_dir
            )
            
            # 收集性能指标
            for metric in metrics:
                tuner.collect_metric(metric)
            
            # 记录默认值
            default_values = {
                name: param.default_value 
                for name, param in tuner.get_all_parameters().items()
            }
            
            # 执行多次自动调参循环
            for _ in range(tune_cycles):
                tuner.auto_tune_cycle()
            
            # 调用 reset_to_defaults
            tuner.reset_to_defaults()
            
            # 验证所有参数值等于默认值
            for param_name, param in tuner.get_all_parameters().items():
                assert param.current_value == default_values[param_name], \
                    f"参数 {param_name} 重置后的值 {param.current_value} 不等于默认值 {default_values[param_name]}"
            
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


class TestParameterSpace默认值恢复:
    """测试 ParameterSpace 类的默认值恢复功能"""
    
    @given(
        value_ratio=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
        param_name=param_name_strategy
    )
    @settings(max_examples=100)
    def test_ParameterSpace_reset方法恢复默认值(
        self, 
        value_ratio: float,
        param_name: str
    ):
        """
        *对于任意* ParameterSpace 对象，调用 reset() 后 current_value 必须等于 default_value。
        
        **Feature: smart-training-system, Property 17: 默认值恢复正确性**
        **验证: 需求 9.5**
        """
        # 获取默认参数空间
        params = get_default_parameter_spaces()
        param = params[param_name]
        
        # 记录默认值
        default_value = param.default_value
        
        # 计算新值（在有效范围内）
        new_value = param.min_value + (param.max_value - param.min_value) * value_ratio
        
        # 修改参数值
        param.current_value = new_value
        
        # 调用 reset
        param.reset()
        
        # 验证参数值等于默认值
        assert param.current_value == default_value, \
            f"参数 {param_name} 重置后的值 {param.current_value} 不等于默认值 {default_value}"
    
    @given(
        min_val=st.floats(min_value=0.0, max_value=10.0, allow_nan=False, allow_infinity=False),
        range_size=st.floats(min_value=0.1, max_value=10.0, allow_nan=False, allow_infinity=False),
        default_ratio=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
        current_ratio=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100)
    def test_任意ParameterSpace_reset恢复默认值(
        self, 
        min_val: float,
        range_size: float,
        default_ratio: float,
        current_ratio: float
    ):
        """
        *对于任意* 有效的 ParameterSpace 配置，调用 reset() 后 current_value 必须等于 default_value。
        
        **Feature: smart-training-system, Property 17: 默认值恢复正确性**
        **验证: 需求 9.5**
        """
        max_val = min_val + range_size
        default_value = min_val + range_size * default_ratio
        current_value = min_val + range_size * current_ratio
        
        # 创建 ParameterSpace
        param = ParameterSpace(
            name="test_param",
            min_value=min_val,
            max_value=max_val,
            step=0.1,
            current_value=current_value,
            default_value=default_value
        )
        
        # 调用 reset
        param.reset()
        
        # 验证参数值等于默认值
        assert param.current_value == default_value, \
            f"重置后的值 {param.current_value} 不等于默认值 {default_value}"


class Test锁定参数不被重置:
    """测试锁定参数在重置时保持不变（与 Property 16 相关但属于 Property 17 的边界情况）"""
    
    @given(
        param_name=param_name_strategy,
        value_ratio=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100)
    def test_锁定参数在reset_to_defaults时保持不变(
        self, 
        param_name: str, 
        value_ratio: float
    ):
        """
        *对于任意* 被锁定的参数，调用 reset_to_defaults 时该参数值必须保持不变（不恢复默认值）。
        
        **Feature: smart-training-system, Property 17: 默认值恢复正确性**
        **验证: 需求 9.5**
        """
        temp_dir = tempfile.mkdtemp()
        try:
            # 创建 AutoTuner
            tuner = AutoTuner(
                enabled=True,
                aggressiveness=AggressivenessLevel.BALANCED,
                tuning_dir=temp_dir
            )
            
            # 获取参数信息
            param = tuner.get_parameter(param_name)
            
            # 计算新值（在有效范围内，且不等于默认值）
            new_value = param.min_value + (param.max_value - param.min_value) * value_ratio
            
            # 修改参数值
            tuner.set_parameter_value(param_name, new_value)
            
            # 记录修改后的值
            modified_value = tuner.get_parameter(param_name).current_value
            
            # 锁定参数
            tuner.lock_parameter(param_name)
            
            # 调用 reset_to_defaults
            tuner.reset_to_defaults()
            
            # 验证锁定参数的值保持不变
            current_value = tuner.get_parameter(param_name).current_value
            assert current_value == modified_value, \
                f"锁定参数 {param_name} 的值从 {modified_value} 变为 {current_value}"
            
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    @given(
        param_name=param_name_strategy,
        value_ratio=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100)
    def test_锁定参数在reset_parameter_to_default时返回False(
        self, 
        param_name: str, 
        value_ratio: float
    ):
        """
        *对于任意* 被锁定的参数，调用 reset_parameter_to_default 应该返回 False 且值保持不变。
        
        **Feature: smart-training-system, Property 17: 默认值恢复正确性**
        **验证: 需求 9.5**
        """
        temp_dir = tempfile.mkdtemp()
        try:
            # 创建 AutoTuner
            tuner = AutoTuner(
                enabled=True,
                aggressiveness=AggressivenessLevel.BALANCED,
                tuning_dir=temp_dir
            )
            
            # 获取参数信息
            param = tuner.get_parameter(param_name)
            
            # 计算新值（在有效范围内）
            new_value = param.min_value + (param.max_value - param.min_value) * value_ratio
            
            # 修改参数值
            tuner.set_parameter_value(param_name, new_value)
            
            # 记录修改后的值
            modified_value = tuner.get_parameter(param_name).current_value
            
            # 锁定参数
            tuner.lock_parameter(param_name)
            
            # 调用 reset_parameter_to_default
            result = tuner.reset_parameter_to_default(param_name)
            
            # 验证返回 False
            assert result == False, f"reset_parameter_to_default 应该返回 False，但返回了 {result}"
            
            # 验证锁定参数的值保持不变
            current_value = tuner.get_parameter(param_name).current_value
            assert current_value == modified_value, \
                f"锁定参数 {param_name} 的值从 {modified_value} 变为 {current_value}"
            
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    @given(
        value_ratio=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
        param_name=param_name_strategy
    )
    @settings(max_examples=100)
    def test_锁定的ParameterSpace_reset不改变值(
        self, 
        value_ratio: float,
        param_name: str
    ):
        """
        *对于任意* 被锁定的 ParameterSpace，调用 reset() 时 current_value 必须保持不变。
        
        **Feature: smart-training-system, Property 17: 默认值恢复正确性**
        **验证: 需求 9.5**
        """
        # 获取默认参数空间
        params = get_default_parameter_spaces()
        param = params[param_name]
        
        # 计算新值（在有效范围内）
        new_value = param.min_value + (param.max_value - param.min_value) * value_ratio
        
        # 修改参数值
        param.current_value = new_value
        
        # 记录修改后的值
        modified_value = param.current_value
        
        # 锁定参数
        param.locked = True
        
        # 调用 reset
        param.reset()
        
        # 验证参数值保持不变
        assert param.current_value == modified_value, \
            f"锁定参数 {param_name} 的值从 {modified_value} 变为 {param.current_value}"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--hypothesis-show-statistics'])
