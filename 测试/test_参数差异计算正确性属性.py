"""
属性测试：参数差异计算正确性
Property 18: 对于任意参数，get_parameter_diff 返回的差异值必须等于 current_value - default_value。

**Feature: smart-training-system, Property 18: 参数差异计算正确性**
**验证: 需求 9.6**
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


class Test参数差异计算正确性属性:
    """
    Property 18: 参数差异计算正确性
    
    *对于任意* 参数，get_parameter_diff 返回的差异值必须等于 current_value - default_value。
    **验证: 需求 9.6**
    """
    
    @given(
        param_name=param_name_strategy,
        value_ratio=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100)
    def test_单个参数差异计算正确(
        self, 
        param_name: str, 
        value_ratio: float
    ):
        """
        *对于任意* 单个参数，修改后 get_parameter_diff 返回的差异必须正确。
        
        **Feature: smart-training-system, Property 18: 参数差异计算正确性**
        **验证: 需求 9.6**
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
            
            # 获取实际的当前值（可能被限制在范围内）
            actual_current = tuner.get_parameter(param_name).current_value
            
            # 获取差异
            diff = tuner.get_parameter_diff()
            
            # 如果当前值与默认值不同，应该在差异字典中
            if actual_current != default_value:
                assert param_name in diff, \
                    f"参数 {param_name} 的值 {actual_current} 与默认值 {default_value} 不同，但未出现在差异字典中"
                
                current_in_diff, default_in_diff = diff[param_name]
                
                # 验证返回的当前值正确
                assert current_in_diff == pytest.approx(actual_current), \
                    f"差异字典中的当前值 {current_in_diff} 与实际当前值 {actual_current} 不匹配"
                
                # 验证返回的默认值正确
                assert default_in_diff == pytest.approx(default_value), \
                    f"差异字典中的默认值 {default_in_diff} 与实际默认值 {default_value} 不匹配"
            else:
                # 如果当前值等于默认值，不应该在差异字典中
                assert param_name not in diff, \
                    f"参数 {param_name} 的值等于默认值，但出现在差异字典中"
            
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    @given(modifications=param_value_modifications())
    @settings(max_examples=100)
    def test_多参数差异计算正确(self, modifications: dict):
        """
        *对于任意* 参数修改组合，get_parameter_diff 返回的所有差异必须正确。
        
        **Feature: smart-training-system, Property 18: 参数差异计算正确性**
        **验证: 需求 9.6**
        """
        temp_dir = tempfile.mkdtemp()
        try:
            # 创建 AutoTuner
            tuner = AutoTuner(
                enabled=True,
                aggressiveness=AggressivenessLevel.BALANCED,
                tuning_dir=temp_dir
            )
            
            # 记录所有参数的默认值
            default_values = {
                name: param.default_value 
                for name, param in tuner.get_all_parameters().items()
            }
            
            # 应用所有修改
            for param_name, new_value in modifications.items():
                tuner.set_parameter_value(param_name, new_value)
            
            # 获取差异
            diff = tuner.get_parameter_diff()
            
            # 验证每个参数
            for param_name, param in tuner.get_all_parameters().items():
                actual_current = param.current_value
                default_value = default_values[param_name]
                
                if actual_current != default_value:
                    # 应该在差异字典中
                    assert param_name in diff, \
                        f"参数 {param_name} 的值 {actual_current} 与默认值 {default_value} 不同，但未出现在差异字典中"
                    
                    current_in_diff, default_in_diff = diff[param_name]
                    
                    assert current_in_diff == pytest.approx(actual_current), \
                        f"参数 {param_name}: 差异字典中的当前值 {current_in_diff} 与实际当前值 {actual_current} 不匹配"
                    
                    assert default_in_diff == pytest.approx(default_value), \
                        f"参数 {param_name}: 差异字典中的默认值 {default_in_diff} 与实际默认值 {default_value} 不匹配"
                else:
                    # 不应该在差异字典中
                    assert param_name not in diff, \
                        f"参数 {param_name} 的值等于默认值，但出现在差异字典中"
            
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    @given(
        param_name=param_name_strategy,
        value_ratio=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100)
    def test_get_all_parameter_diff差值计算正确(
        self, 
        param_name: str, 
        value_ratio: float
    ):
        """
        *对于任意* 参数，get_all_parameter_diff 返回的差值必须等于 current_value - default_value。
        
        **Feature: smart-training-system, Property 18: 参数差异计算正确性**
        **验证: 需求 9.6**
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
            
            # 获取实际的当前值
            actual_current = tuner.get_parameter(param_name).current_value
            
            # 获取详细差异
            all_diff = tuner.get_all_parameter_diff()
            
            # 验证参数在差异字典中
            assert param_name in all_diff, \
                f"参数 {param_name} 未出现在 get_all_parameter_diff 结果中"
            
            current_in_diff, default_in_diff, diff_value = all_diff[param_name]
            
            # 验证当前值正确
            assert current_in_diff == pytest.approx(actual_current), \
                f"差异字典中的当前值 {current_in_diff} 与实际当前值 {actual_current} 不匹配"
            
            # 验证默认值正确
            assert default_in_diff == pytest.approx(default_value), \
                f"差异字典中的默认值 {default_in_diff} 与实际默认值 {default_value} 不匹配"
            
            # 验证差值计算正确：diff_value == current_value - default_value
            expected_diff = actual_current - default_value
            assert diff_value == pytest.approx(expected_diff), \
                f"差值 {diff_value} 不等于 current_value - default_value = {expected_diff}"
            
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


class TestParameterSpace差异计算:
    """测试 ParameterSpace 类的 get_diff 方法"""
    
    @given(
        value_ratio=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
        param_name=param_name_strategy
    )
    @settings(max_examples=100)
    def test_ParameterSpace_get_diff方法正确(
        self, 
        value_ratio: float,
        param_name: str
    ):
        """
        *对于任意* ParameterSpace 对象，get_diff() 返回值必须等于 current_value - default_value。
        
        **Feature: smart-training-system, Property 18: 参数差异计算正确性**
        **验证: 需求 9.6**
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
        
        # 获取差异
        diff = param.get_diff()
        
        # 验证差值计算正确
        expected_diff = new_value - default_value
        assert diff == pytest.approx(expected_diff), \
            f"get_diff() 返回 {diff}，但期望 current_value - default_value = {expected_diff}"
    
    @given(
        min_val=st.floats(min_value=0.0, max_value=10.0, allow_nan=False, allow_infinity=False),
        range_size=st.floats(min_value=0.1, max_value=10.0, allow_nan=False, allow_infinity=False),
        default_ratio=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
        current_ratio=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100)
    def test_任意ParameterSpace_get_diff正确(
        self, 
        min_val: float,
        range_size: float,
        default_ratio: float,
        current_ratio: float
    ):
        """
        *对于任意* 有效的 ParameterSpace 配置，get_diff() 返回值必须等于 current_value - default_value。
        
        **Feature: smart-training-system, Property 18: 参数差异计算正确性**
        **验证: 需求 9.6**
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
        
        # 获取差异
        diff = param.get_diff()
        
        # 验证差值计算正确
        expected_diff = current_value - default_value
        assert diff == pytest.approx(expected_diff), \
            f"get_diff() 返回 {diff}，但期望 current_value - default_value = {expected_diff}"


class Test差异计算边界情况:
    """测试差异计算的边界情况"""
    
    @given(param_name=param_name_strategy)
    @settings(max_examples=100)
    def test_未修改参数差异为零(self, param_name: str):
        """
        *对于任意* 未修改的参数，差异应该为零且不出现在 get_parameter_diff 结果中。
        
        **Feature: smart-training-system, Property 18: 参数差异计算正确性**
        **验证: 需求 9.6**
        """
        temp_dir = tempfile.mkdtemp()
        try:
            # 创建 AutoTuner
            tuner = AutoTuner(
                enabled=True,
                aggressiveness=AggressivenessLevel.BALANCED,
                tuning_dir=temp_dir
            )
            
            # 获取差异（未修改任何参数）
            diff = tuner.get_parameter_diff()
            
            # 未修改的参数不应该出现在差异字典中
            assert param_name not in diff, \
                f"未修改的参数 {param_name} 不应该出现在差异字典中"
            
            # 验证 get_all_parameter_diff 中差值为零
            all_diff = tuner.get_all_parameter_diff()
            current, default, diff_value = all_diff[param_name]
            
            assert diff_value == pytest.approx(0.0), \
                f"未修改参数 {param_name} 的差值应该为 0，但得到 {diff_value}"
            
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    @given(
        param_name=param_name_strategy,
        aggressiveness=aggressiveness_level
    )
    @settings(max_examples=100)
    def test_不同激进程度下差异计算一致(
        self, 
        param_name: str,
        aggressiveness: AggressivenessLevel
    ):
        """
        *对于任意* 激进程度设置，差异计算结果应该一致（与激进程度无关）。
        
        **Feature: smart-training-system, Property 18: 参数差异计算正确性**
        **验证: 需求 9.6**
        """
        temp_dir = tempfile.mkdtemp()
        try:
            # 创建 AutoTuner
            tuner = AutoTuner(
                enabled=True,
                aggressiveness=aggressiveness,
                tuning_dir=temp_dir
            )
            
            # 获取参数信息
            param = tuner.get_parameter(param_name)
            
            # 设置一个固定的新值
            new_value = (param.min_value + param.max_value) / 2
            tuner.set_parameter_value(param_name, new_value)
            
            # 获取实际当前值
            actual_current = tuner.get_parameter(param_name).current_value
            default_value = param.default_value
            
            # 获取详细差异
            all_diff = tuner.get_all_parameter_diff()
            current_in_diff, default_in_diff, diff_value = all_diff[param_name]
            
            # 验证差值计算正确（与激进程度无关）
            expected_diff = actual_current - default_value
            assert diff_value == pytest.approx(expected_diff), \
                f"在 {aggressiveness.value} 模式下，差值 {diff_value} 不等于期望值 {expected_diff}"
            
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--hypothesis-show-statistics'])
