"""
属性测试：参数调整范围约束
Property 13: 对于任意参数调整操作，调整后的参数值必须在 ParameterSpace 定义的 [min_value, max_value] 范围内。

**Feature: smart-training-system, Property 13: 参数调整范围约束**
**验证: 需求 8.1, 8.3**
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

# 生成有效的参数空间
@st.composite
def valid_parameter_space(draw):
    """生成有效的 ParameterSpace 对象"""
    # 使用简单的字母数字字符串作为参数名
    name = draw(st.text(
        min_size=1, 
        max_size=20, 
        alphabet='abcdefghijklmnopqrstuvwxyz_0123456789'
    ))
    assume(name.strip())  # 确保名称非空
    assume(not name[0].isdigit())  # 确保不以数字开头
    
    # 生成有效的范围
    min_val = draw(st.floats(min_value=-100.0, max_value=100.0, allow_nan=False, allow_infinity=False))
    max_val = draw(st.floats(min_value=min_val + 0.01, max_value=200.0, allow_nan=False, allow_infinity=False))
    
    # 生成有效的步长
    step = draw(st.floats(min_value=0.001, max_value=(max_val - min_val) / 2, allow_nan=False, allow_infinity=False))
    
    # 生成在范围内的当前值和默认值
    current_val = draw(st.floats(min_value=min_val, max_value=max_val, allow_nan=False, allow_infinity=False))
    default_val = draw(st.floats(min_value=min_val, max_value=max_val, allow_nan=False, allow_infinity=False))
    
    return ParameterSpace(
        name=name,
        min_value=min_val,
        max_value=max_val,
        step=step,
        current_value=current_val,
        default_value=default_val,
        locked=False
    )


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


# 生成调整量（可正可负）
adjustment_delta = st.floats(min_value=-1000.0, max_value=1000.0, allow_nan=False, allow_infinity=False)


# 生成激进程度
aggressiveness_level = st.sampled_from([
    AggressivenessLevel.CONSERVATIVE,
    AggressivenessLevel.BALANCED,
    AggressivenessLevel.AGGRESSIVE
])


class Test参数调整范围约束属性:
    """
    Property 13: 参数调整范围约束
    
    *对于任意* 参数调整操作，调整后的参数值必须在 ParameterSpace 定义的 [min_value, max_value] 范围内。
    **验证: 需求 8.1, 8.3**
    """
    
    @given(param=valid_parameter_space(), delta=adjustment_delta)
    @settings(max_examples=100)
    def test_参数空间调整后值在范围内(self, param: ParameterSpace, delta: float):
        """
        *对于任意* ParameterSpace 和任意调整量，调用 adjust() 后的值必须在 [min_value, max_value] 范围内。
        
        **Feature: smart-training-system, Property 13: 参数调整范围约束**
        **验证: 需求 8.1, 8.3**
        """
        # 记录调整前的范围
        min_val = param.min_value
        max_val = param.max_value
        
        # 执行调整
        new_value = param.adjust(delta)
        
        # 验证调整后的值在范围内
        assert min_val <= new_value <= max_val, \
            f"调整后的值 {new_value} 不在范围 [{min_val}, {max_val}] 内"
        assert min_val <= param.current_value <= max_val, \
            f"参数当前值 {param.current_value} 不在范围 [{min_val}, {max_val}] 内"
    
    @given(
        param=valid_parameter_space(),
        deltas=st.lists(adjustment_delta, min_size=1, max_size=50)
    )
    @settings(max_examples=100)
    def test_多次连续调整后值仍在范围内(self, param: ParameterSpace, deltas: list):
        """
        *对于任意* ParameterSpace 和任意调整量序列，多次调用 adjust() 后的值必须始终在 [min_value, max_value] 范围内。
        
        **Feature: smart-training-system, Property 13: 参数调整范围约束**
        **验证: 需求 8.1, 8.3**
        """
        min_val = param.min_value
        max_val = param.max_value
        
        # 执行多次调整
        for delta in deltas:
            new_value = param.adjust(delta)
            
            # 每次调整后都验证范围
            assert min_val <= new_value <= max_val, \
                f"调整后的值 {new_value} 不在范围 [{min_val}, {max_val}] 内"
            assert min_val <= param.current_value <= max_val, \
                f"参数当前值 {param.current_value} 不在范围 [{min_val}, {max_val}] 内"
    
    @given(aggressiveness=aggressiveness_level)
    @settings(max_examples=100)
    def test_AutoTuner调参后值在范围内(self, aggressiveness: AggressivenessLevel):
        """
        *对于任意* 激进程度设置，AutoTuner.tune_parameter() 调整后的参数值必须在定义的范围内。
        
        **Feature: smart-training-system, Property 13: 参数调整范围约束**
        **验证: 需求 8.1, 8.3**
        """
        # 创建临时目录
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
            
            # 对每个未锁定的参数进行调整测试
            for param_name in tuner.get_unlocked_parameters():
                param = tuner.get_parameter(param_name)
                min_val = param.min_value
                max_val = param.max_value
                
                # 执行调参
                record = tuner.tune_parameter(param_name)
                
                # 验证调整后的值在范围内
                new_value = tuner.get_parameter(param_name).current_value
                assert min_val <= new_value <= max_val, \
                    f"参数 {param_name} 调整后的值 {new_value} 不在范围 [{min_val}, {max_val}] 内"
                assert min_val <= record.new_value <= max_val, \
                    f"记录中的新值 {record.new_value} 不在范围 [{min_val}, {max_val}] 内"
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    @given(
        metrics=st.lists(valid_performance_metric(), min_size=5, max_size=20),
        aggressiveness=aggressiveness_level,
        tune_count=st.integers(min_value=1, max_value=10)
    )
    @settings(max_examples=100)
    def test_多次调参后所有参数值在范围内(
        self, 
        metrics: list, 
        aggressiveness: AggressivenessLevel,
        tune_count: int
    ):
        """
        *对于任意* 性能指标序列和调参次数，多次调参后所有参数值必须在各自的范围内。
        
        **Feature: smart-training-system, Property 13: 参数调整范围约束**
        **验证: 需求 8.1, 8.3**
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
            
            # 执行多次调参
            unlocked_params = tuner.get_unlocked_parameters()
            for i in range(tune_count):
                if not unlocked_params:
                    break
                    
                # 选择一个参数进行调整
                param_name = unlocked_params[i % len(unlocked_params)]
                
                try:
                    tuner.tune_parameter(param_name)
                except ValueError:
                    # 参数可能被锁定，跳过
                    continue
            
            # 验证所有参数都在范围内
            for param_name, param in tuner.get_all_parameters().items():
                assert param.min_value <= param.current_value <= param.max_value, \
                    f"参数 {param_name} 的值 {param.current_value} 不在范围 [{param.min_value}, {param.max_value}] 内"
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    @given(
        param=valid_parameter_space(),
        extreme_delta=st.sampled_from([float('inf'), float('-inf'), 1e308, -1e308, 1e100, -1e100])
    )
    @settings(max_examples=100)
    def test_极端调整量后值仍在范围内(self, param: ParameterSpace, extreme_delta: float):
        """
        *对于任意* ParameterSpace 和极端调整量，调整后的值必须仍在 [min_value, max_value] 范围内。
        
        **Feature: smart-training-system, Property 13: 参数调整范围约束**
        **验证: 需求 8.1, 8.3**
        """
        # 跳过无穷大的情况（Python 浮点数运算可能产生 nan）
        assume(not (extreme_delta == float('inf') or extreme_delta == float('-inf')))
        
        min_val = param.min_value
        max_val = param.max_value
        
        # 执行调整
        new_value = param.adjust(extreme_delta)
        
        # 验证调整后的值在范围内
        assert min_val <= new_value <= max_val, \
            f"极端调整后的值 {new_value} 不在范围 [{min_val}, {max_val}] 内"


class Test默认参数空间范围约束:
    """测试默认参数空间的范围约束"""
    
    @given(delta=adjustment_delta)
    @settings(max_examples=100)
    def test_默认参数调整后在范围内(self, delta: float):
        """
        *对于任意* 调整量，默认参数空间中的所有参数调整后必须在各自的范围内。
        
        **Feature: smart-training-system, Property 13: 参数调整范围约束**
        **验证: 需求 8.1, 8.3**
        """
        params = get_default_parameter_spaces()
        
        for name, param in params.items():
            min_val = param.min_value
            max_val = param.max_value
            
            # 执行调整
            new_value = param.adjust(delta)
            
            # 验证范围
            assert min_val <= new_value <= max_val, \
                f"默认参数 {name} 调整后的值 {new_value} 不在范围 [{min_val}, {max_val}] 内"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--hypothesis-show-statistics'])
