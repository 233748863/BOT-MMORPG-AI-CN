"""
自动调参模块功能验证测试
用于检查点14：确保自动调参模块测试通过
"""

import pytest
import tempfile
import shutil
import os
from datetime import datetime, timedelta

from 核心.自动调参 import (
    AutoTuner, PerformanceMetric, ParameterSpace, TuningRecord,
    AggressivenessLevel, get_default_parameter_spaces
)


class Test性能指标数据类:
    """测试 PerformanceMetric 数据类"""
    
    def test_创建有效指标(self):
        """有效参数应该成功创建指标"""
        metric = PerformanceMetric(
            action_success_rate=0.8,
            state_accuracy=0.9,
            stuck_count=2,
            task_efficiency=0.7
        )
        assert metric.action_success_rate == 0.8
        assert metric.state_accuracy == 0.9
        assert metric.stuck_count == 2
        assert metric.task_efficiency == 0.7
    
    def test_拒绝无效成功率(self):
        """超出范围的成功率应该被拒绝"""
        with pytest.raises(ValueError):
            PerformanceMetric(action_success_rate=1.5)
        with pytest.raises(ValueError):
            PerformanceMetric(action_success_rate=-0.1)
    
    def test_拒绝负数卡住次数(self):
        """负数卡住次数应该被拒绝"""
        with pytest.raises(ValueError):
            PerformanceMetric(stuck_count=-1)
    
    def test_综合分数计算(self):
        """综合分数应该在0-1范围内"""
        metric = PerformanceMetric(
            action_success_rate=0.8,
            state_accuracy=0.9,
            stuck_count=0,
            task_efficiency=0.7
        )
        score = metric.get_overall_score()
        assert 0.0 <= score <= 1.0
    
    def test_序列化反序列化(self):
        """序列化后反序列化应该得到等价对象"""
        metric = PerformanceMetric(
            action_success_rate=0.8,
            state_accuracy=0.9,
            stuck_count=2,
            task_efficiency=0.7
        )
        data = metric.to_dict()
        restored = PerformanceMetric.from_dict(data)
        assert restored.action_success_rate == metric.action_success_rate
        assert restored.state_accuracy == metric.state_accuracy
        assert restored.stuck_count == metric.stuck_count
        assert restored.task_efficiency == metric.task_efficiency


class Test参数空间数据类:
    """测试 ParameterSpace 数据类"""
    
    def test_创建有效参数空间(self):
        """有效参数应该成功创建参数空间"""
        param = ParameterSpace(
            name='test_param',
            min_value=0.0,
            max_value=1.0,
            step=0.1,
            current_value=0.5,
            default_value=0.5
        )
        assert param.name == 'test_param'
        assert param.current_value == 0.5
    
    def test_拒绝空名称(self):
        """空名称应该被拒绝"""
        with pytest.raises(ValueError):
            ParameterSpace(
                name='',
                min_value=0.0,
                max_value=1.0,
                step=0.1,
                current_value=0.5,
                default_value=0.5
            )
    
    def test_拒绝无效范围(self):
        """最小值大于最大值应该被拒绝"""
        with pytest.raises(ValueError):
            ParameterSpace(
                name='test',
                min_value=1.0,
                max_value=0.0,
                step=0.1,
                current_value=0.5,
                default_value=0.5
            )
    
    def test_参数调整在范围内(self):
        """参数调整后应该保持在范围内"""
        param = ParameterSpace(
            name='test',
            min_value=0.0,
            max_value=1.0,
            step=0.1,
            current_value=0.5,
            default_value=0.5
        )
        # 向上调整
        param.adjust(0.3)
        assert param.current_value == 0.8
        # 超出上限
        param.adjust(0.5)
        assert param.current_value == 1.0
        # 向下调整
        param.adjust(-1.5)
        assert param.current_value == 0.0
    
    def test_锁定参数不可调整(self):
        """锁定的参数不应该被调整"""
        param = ParameterSpace(
            name='test',
            min_value=0.0,
            max_value=1.0,
            step=0.1,
            current_value=0.5,
            default_value=0.5,
            locked=True
        )
        param.adjust(0.3)
        assert param.current_value == 0.5  # 保持不变
    
    def test_重置为默认值(self):
        """重置应该恢复默认值"""
        param = ParameterSpace(
            name='test',
            min_value=0.0,
            max_value=1.0,
            step=0.1,
            current_value=0.8,
            default_value=0.5
        )
        param.reset()
        assert param.current_value == 0.5
    
    def test_差异计算(self):
        """差异计算应该正确"""
        param = ParameterSpace(
            name='test',
            min_value=0.0,
            max_value=1.0,
            step=0.1,
            current_value=0.8,
            default_value=0.5
        )
        assert param.get_diff() == pytest.approx(0.3)


class Test调参记录数据类:
    """测试 TuningRecord 数据类"""
    
    def test_创建有效记录(self):
        """有效参数应该成功创建记录"""
        record = TuningRecord(
            parameter_name='test_param',
            old_value=0.5,
            new_value=0.6,
            reason='测试调整'
        )
        assert record.parameter_name == 'test_param'
        assert record.old_value == 0.5
        assert record.new_value == 0.6
    
    def test_拒绝空参数名(self):
        """空参数名应该被拒绝"""
        with pytest.raises(ValueError):
            TuningRecord(
                parameter_name='',
                old_value=0.5,
                new_value=0.6
            )
    
    def test_调整幅度计算(self):
        """调整幅度应该正确计算"""
        record = TuningRecord(
            parameter_name='test',
            old_value=0.5,
            new_value=0.8
        )
        assert record.adjustment_delta == pytest.approx(0.3)


class Test自动调参器:
    """测试 AutoTuner 类"""
    
    @pytest.fixture
    def temp_dir(self):
        """创建临时目录"""
        test_dir = tempfile.mkdtemp()
        yield test_dir
        shutil.rmtree(test_dir, ignore_errors=True)
    
    @pytest.fixture
    def tuner(self, temp_dir):
        """创建测试用的AutoTuner"""
        return AutoTuner(
            enabled=True,
            aggressiveness=AggressivenessLevel.BALANCED,
            tuning_dir=temp_dir
        )
    
    def test_初始化(self, tuner):
        """AutoTuner应该正确初始化"""
        assert tuner.enabled == True
        assert tuner.aggressiveness == AggressivenessLevel.BALANCED
        assert len(tuner.get_all_parameters()) > 0
    
    def test_指标收集(self, tuner):
        """应该能收集性能指标"""
        metric = PerformanceMetric(
            action_success_rate=0.8,
            state_accuracy=0.9,
            stuck_count=1,
            task_efficiency=0.7
        )
        tuner.collect_metric(metric)
        assert tuner.get_metrics_count() == 1
    
    def test_指标汇总(self, tuner):
        """应该正确汇总指标"""
        for i in range(5):
            metric = PerformanceMetric(
                action_success_rate=0.6 + i * 0.1,
                state_accuracy=0.8,
                stuck_count=1,
                task_efficiency=0.7
            )
            tuner.collect_metric(metric)
        
        aggregated = tuner.get_aggregated_metrics(window_minutes=60)
        # 平均值应该是 (0.6 + 0.7 + 0.8 + 0.9 + 1.0) / 5 = 0.8
        assert aggregated.action_success_rate == pytest.approx(0.8)
        # stuck_count 是累加值
        assert aggregated.stuck_count == 5
    
    def test_参数锁定(self, tuner):
        """应该能锁定和解锁参数"""
        tuner.lock_parameter('action_cooldown')
        assert tuner.is_parameter_locked('action_cooldown') == True
        
        tuner.unlock_parameter('action_cooldown')
        assert tuner.is_parameter_locked('action_cooldown') == False
    
    def test_锁定参数不被调整(self, tuner):
        """锁定的参数不应该被调整"""
        # 先收集足够的指标
        for i in range(5):
            tuner.collect_metric(PerformanceMetric(
                action_success_rate=0.8,
                state_accuracy=0.8,
                stuck_count=1,
                task_efficiency=0.7
            ))
        
        tuner.lock_parameter('action_cooldown')
        original_value = tuner.get_parameter('action_cooldown').current_value
        
        with pytest.raises(ValueError):
            tuner.tune_parameter('action_cooldown')
        
        # 值应该保持不变
        assert tuner.get_parameter('action_cooldown').current_value == original_value
    
    def test_参数调整在范围内(self, tuner):
        """参数调整后应该在定义的范围内"""
        # 先收集足够的指标
        for i in range(5):
            tuner.collect_metric(PerformanceMetric(
                action_success_rate=0.8,
                state_accuracy=0.8,
                stuck_count=1,
                task_efficiency=0.7
            ))
        
        param = tuner.get_parameter('action_cooldown')
        min_val = param.min_value
        max_val = param.max_value
        
        record = tuner.tune_parameter('action_cooldown')
        
        new_value = tuner.get_parameter('action_cooldown').current_value
        assert min_val <= new_value <= max_val
    
    def test_渐进式调整(self, tuner):
        """调整幅度应该符合激进程度设置"""
        # 先收集足够的指标
        for i in range(5):
            tuner.collect_metric(PerformanceMetric(
                action_success_rate=0.8,
                state_accuracy=0.8,
                stuck_count=1,
                task_efficiency=0.7
            ))
        
        param = tuner.get_parameter('action_cooldown')
        step = param.step
        multiplier = tuner.aggressiveness.get_step_multiplier()
        max_delta = step * multiplier
        
        old_value = param.current_value
        record = tuner.tune_parameter('action_cooldown')
        
        actual_delta = abs(record.new_value - record.old_value)
        assert actual_delta <= max_delta + 0.001  # 允许浮点误差
    
    def test_重置为默认值(self, tuner):
        """重置应该恢复所有参数的默认值"""
        # 修改一些参数
        tuner.set_parameter_value('action_cooldown', 1.0)
        tuner.set_parameter_value('state_switch_threshold', 0.8)
        
        tuner.reset_to_defaults()
        
        for name, param in tuner.get_all_parameters().items():
            if not param.locked:
                assert param.current_value == param.default_value
    
    def test_参数差异计算(self, tuner):
        """参数差异应该正确计算"""
        tuner.set_parameter_value('action_cooldown', 0.7)
        
        diff = tuner.get_parameter_diff()
        
        assert 'action_cooldown' in diff
        current, default = diff['action_cooldown']
        assert current == 0.7
        assert default == 0.5
    
    def test_性能下降判断(self, tuner):
        """应该正确判断性能是否下降"""
        baseline = PerformanceMetric(
            action_success_rate=0.8,
            state_accuracy=0.8,
            stuck_count=1,
            task_efficiency=0.7
        )
        
        better = PerformanceMetric(
            action_success_rate=0.9,
            state_accuracy=0.9,
            stuck_count=0,
            task_efficiency=0.8
        )
        
        worse = PerformanceMetric(
            action_success_rate=0.5,
            state_accuracy=0.5,
            stuck_count=5,
            task_efficiency=0.3
        )
        
        assert tuner.is_performance_degraded(better, baseline) == False
        assert tuner.is_performance_degraded(worse, baseline) == True
    
    def test_回滚功能(self, tuner):
        """回滚应该恢复参数到调整前的值"""
        # 先收集足够的指标
        for i in range(5):
            tuner.collect_metric(PerformanceMetric(
                action_success_rate=0.8,
                state_accuracy=0.8,
                stuck_count=1,
                task_efficiency=0.7
            ))
        
        original_value = tuner.get_parameter('action_cooldown').current_value
        record = tuner.tune_parameter('action_cooldown')
        
        # 确认值已改变
        assert tuner.get_parameter('action_cooldown').current_value != original_value or record.new_value == record.old_value
        
        # 回滚
        tuner.rollback(record)
        
        # 确认值已恢复
        assert tuner.get_parameter('action_cooldown').current_value == original_value


class Test激进程度:
    """测试激进程度枚举"""
    
    def test_保守模式步长倍数(self):
        """保守模式应该是1倍步长"""
        assert AggressivenessLevel.CONSERVATIVE.get_step_multiplier() == 1
    
    def test_平衡模式步长倍数(self):
        """平衡模式应该是2倍步长"""
        assert AggressivenessLevel.BALANCED.get_step_multiplier() == 2
    
    def test_激进模式步长倍数(self):
        """激进模式应该是3倍步长"""
        assert AggressivenessLevel.AGGRESSIVE.get_step_multiplier() == 3


class Test默认参数空间:
    """测试默认参数空间"""
    
    def test_包含必要参数(self):
        """默认参数空间应该包含所有必要参数"""
        params = get_default_parameter_spaces()
        
        required_params = [
            'action_cooldown',
            'state_switch_threshold',
            'rule_priority_weight',
            'detection_confidence_threshold'
        ]
        
        for param_name in required_params:
            assert param_name in params
    
    def test_参数范围有效(self):
        """所有参数的范围应该有效"""
        params = get_default_parameter_spaces()
        
        for name, param in params.items():
            assert param.min_value <= param.max_value
            assert param.min_value <= param.current_value <= param.max_value
            assert param.min_value <= param.default_value <= param.max_value
            assert param.step > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
