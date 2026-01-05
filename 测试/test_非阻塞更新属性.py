# -*- coding: utf-8 -*-
"""
属性测试：非阻塞更新
Property 2: 对于任意图表更新操作，不应阻塞训练主循环超过 100ms

**Feature: training-visualization, Property 2: 非阻塞更新**
**验证: 需求 2.5**
"""

import sys
import os
import time
import tempfile
import shutil

# 添加项目根目录到路径
项目根目录 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, 项目根目录)

import pytest
from hypothesis import given, strategies as st, settings, assume
from typing import Dict, Any, List, Optional
from unittest.mock import MagicMock, patch

from 训练.训练监控 import 指标记录器, 实时图表


# ==================== 测试数据生成策略 ====================

# 有效的批次号策略
valid_batch_strategy = st.integers(min_value=0, max_value=10000)

# 有效的 loss 值策略（避免 NaN 和无穷大）
valid_loss_strategy = st.floats(
    min_value=0.0,
    max_value=100.0,
    allow_nan=False,
    allow_infinity=False
)

# 有效的准确率策略（0-1 之间）
valid_accuracy_strategy = st.floats(
    min_value=0.0,
    max_value=1.0,
    allow_nan=False,
    allow_infinity=False
)

# 批次指标策略
batch_metrics_strategy = st.fixed_dictionaries({
    '批次': valid_batch_strategy,
    'loss': valid_loss_strategy
})

# 更新间隔策略
update_interval_strategy = st.integers(min_value=1, max_value=100)


# ==================== Mock 类 ====================

class MockFigure:
    """模拟 matplotlib Figure"""
    def __init__(self):
        self.number = 1
        self.canvas = MockCanvas()
    
class MockCanvas:
    """模拟 matplotlib Canvas"""
    def __init__(self):
        self.manager = MockManager()
    
    def draw(self):
        pass
    
    def draw_idle(self):
        pass
    
    def flush_events(self):
        pass

class MockManager:
    """模拟 matplotlib Manager"""
    def set_window_title(self, title):
        pass

class MockAxes:
    """模拟 matplotlib Axes"""
    def __init__(self):
        self._lines = []
    
    def set_title(self, title, **kwargs):
        pass
    
    def set_xlabel(self, label, **kwargs):
        pass
    
    def set_ylabel(self, label, **kwargs):
        pass
    
    def grid(self, *args, **kwargs):
        pass
    
    def plot(self, *args, **kwargs):
        line = MockLine()
        self._lines.append(line)
        return (line,)
    
    def legend(self, **kwargs):
        pass
    
    def relim(self):
        pass
    
    def autoscale_view(self):
        pass

class MockLine:
    """模拟 matplotlib Line2D"""
    def __init__(self):
        self._xdata = []
        self._ydata = []
    
    def set_data(self, x, y):
        self._xdata = x
        self._ydata = y


# ==================== 属性测试类 ====================

class Test非阻塞更新属性:
    """
    属性测试：非阻塞更新
    
    **Feature: training-visualization, Property 2: 非阻塞更新**
    **验证: 需求 2.5**
    """
    
    @pytest.fixture(autouse=True)
    def 初始化(self):
        """初始化测试环境"""
        self.临时目录 = tempfile.mkdtemp()
        yield
        shutil.rmtree(self.临时目录, ignore_errors=True)
    
    def _创建模拟图表(self, 更新间隔: int = 10) -> 实时图表:
        """创建一个使用模拟对象的图表实例"""
        图表 = 实时图表(更新间隔=更新间隔)
        
        # 模拟 matplotlib
        图表._plt = MagicMock()
        图表._plt.ion = MagicMock()
        图表._plt.subplots = MagicMock(return_value=(MockFigure(), [[MockAxes()]]))
        图表._plt.tight_layout = MagicMock()
        图表._plt.fignum_exists = MagicMock(return_value=True)
        图表._plt.close = MagicMock()
        
        return 图表
    
    @settings(max_examples=100, deadline=None)
    @given(
        批次列表=st.lists(batch_metrics_strategy, min_size=10, max_size=100),
        更新间隔=update_interval_strategy
    )
    def test_更新操作延迟不超过100ms(
        self,
        批次列表: List[Dict[str, Any]],
        更新间隔: int
    ):
        """
        属性测试: 对于任意图表更新操作，不应阻塞训练主循环超过 100ms
        
        **Feature: training-visualization, Property 2: 非阻塞更新**
        **验证: 需求 2.5**
        """
        # 创建记录器和模拟图表
        记录器 = 指标记录器(self.临时目录)
        图表 = self._创建模拟图表(更新间隔)
        
        # 配置并启动图表
        图表.添加子图("loss", ["批次loss"], 标题="Loss", y轴标签="Loss")
        
        # 手动设置图表为已启动状态
        图表._已启动 = True
        图表._fig = MockFigure()
        图表._axes = {"loss": MockAxes()}
        图表._lines = {"loss": {"批次loss": MockLine()}}
        
        # 记录批次数据并测量更新时间
        最大延迟 = 0.0
        
        for 批次数据 in 批次列表:
            记录器.记录批次(批次数据['批次'], 批次数据['loss'])
            
            # 测量更新时间
            开始时间 = time.perf_counter()
            图表.更新(记录器)
            结束时间 = time.perf_counter()
            
            延迟 = (结束时间 - 开始时间) * 1000  # 转换为毫秒
            最大延迟 = max(最大延迟, 延迟)
        
        # 验证: 最大延迟不应超过 100ms
        assert 最大延迟 < 100, \
            f"更新操作延迟 {最大延迟:.2f}ms 超过了 100ms 限制"
    
    @settings(max_examples=50, deadline=None)
    @given(
        批次数量=st.integers(min_value=100, max_value=500),
        更新间隔=update_interval_strategy
    )
    def test_高频更新不阻塞(
        self,
        批次数量: int,
        更新间隔: int
    ):
        """
        属性测试: 高频更新场景下，图表更新不应阻塞训练
        
        **Feature: training-visualization, Property 2: 非阻塞更新**
        **验证: 需求 2.5**
        """
        # 创建记录器和模拟图表
        记录器 = 指标记录器(self.临时目录)
        图表 = self._创建模拟图表(更新间隔)
        
        # 配置并启动图表
        图表.添加子图("loss", ["批次loss"], 标题="Loss", y轴标签="Loss")
        
        # 手动设置图表为已启动状态
        图表._已启动 = True
        图表._fig = MockFigure()
        图表._axes = {"loss": MockAxes()}
        图表._lines = {"loss": {"批次loss": MockLine()}}
        
        # 模拟高频训练循环
        总更新时间 = 0.0
        更新次数 = 0
        
        for i in range(批次数量):
            # 模拟训练一个批次
            loss = 1.0 / (i + 1)  # 模拟递减的 loss
            记录器.记录批次(i, loss)
            
            # 测量更新时间
            开始时间 = time.perf_counter()
            更新成功 = 图表.更新(记录器)
            结束时间 = time.perf_counter()
            
            if 更新成功:
                延迟 = (结束时间 - 开始时间) * 1000
                总更新时间 += 延迟
                更新次数 += 1
                
                # 每次更新都不应超过 100ms
                assert 延迟 < 100, \
                    f"批次 {i} 的更新延迟 {延迟:.2f}ms 超过了 100ms 限制"
        
        # 验证平均更新时间
        if 更新次数 > 0:
            平均延迟 = 总更新时间 / 更新次数
            assert 平均延迟 < 50, \
                f"平均更新延迟 {平均延迟:.2f}ms 过高"
    
    @settings(max_examples=50, deadline=None)
    @given(
        更新间隔=update_interval_strategy
    )
    def test_更新间隔控制(
        self,
        更新间隔: int
    ):
        """
        属性测试: 图表应按配置的间隔更新，减少不必要的更新
        
        **Feature: training-visualization, Property 2: 非阻塞更新**
        **验证: 需求 2.4, 2.5**
        """
        # 创建记录器和模拟图表
        记录器 = 指标记录器(self.临时目录)
        图表 = self._创建模拟图表(更新间隔)
        
        # 配置并启动图表
        图表.添加子图("loss", ["批次loss"], 标题="Loss", y轴标签="Loss")
        
        # 手动设置图表为已启动状态
        图表._已启动 = True
        图表._fig = MockFigure()
        图表._axes = {"loss": MockAxes()}
        图表._lines = {"loss": {"批次loss": MockLine()}}
        
        # 记录批次并统计实际更新次数
        实际更新次数 = 0
        总批次数 = 更新间隔 * 5  # 测试 5 个更新周期
        
        for i in range(总批次数):
            记录器.记录批次(i, 0.5)
            
            上次更新批次 = 图表._上次更新批次
            图表.更新(记录器)
            
            if 图表._上次更新批次 != 上次更新批次:
                实际更新次数 += 1
        
        # 验证: 更新次数应该接近 总批次数 / 更新间隔
        期望更新次数 = 总批次数 // 更新间隔
        
        # 允许一定误差（首次更新可能在第一个间隔内）
        assert 实际更新次数 >= 期望更新次数 - 1, \
            f"更新次数 {实际更新次数} 低于期望 {期望更新次数 - 1}"
        assert 实际更新次数 <= 期望更新次数 + 1, \
            f"更新次数 {实际更新次数} 高于期望 {期望更新次数 + 1}"


# ==================== 单元测试 ====================

class Test实时图表单元测试:
    """实时图表的单元测试"""
    
    def test_默认配置(self):
        """测试: 默认配置应正确初始化"""
        图表 = 实时图表()
        
        assert 图表.更新间隔 == 10, "默认更新间隔应为 10"
        assert not 图表.是否已启动(), "初始状态应为未启动"
        assert len(图表.获取子图配置()) == 0, "初始应无子图配置"
    
    def test_自定义更新间隔(self):
        """测试: 自定义更新间隔"""
        图表 = 实时图表(更新间隔=20)
        
        assert 图表.获取更新间隔() == 20
        
        图表.设置更新间隔(30)
        assert 图表.获取更新间隔() == 30
        
        # 测试最小值限制
        图表.设置更新间隔(0)
        assert 图表.获取更新间隔() == 1, "更新间隔最小应为 1"
    
    def test_添加子图(self):
        """测试: 添加子图配置"""
        图表 = 实时图表()
        
        图表.添加子图("loss", ["训练loss", "验证loss"], 标题="Loss 曲线", y轴标签="Loss")
        图表.添加子图("accuracy", ["训练准确率"], 标题="准确率", y轴标签="准确率")
        
        配置 = 图表.获取子图配置()
        
        assert len(配置) == 2, "应有 2 个子图"
        assert "loss" in 配置
        assert "accuracy" in 配置
        assert 配置["loss"]["指标列表"] == ["训练loss", "验证loss"]
        assert 配置["loss"]["标题"] == "Loss 曲线"
    
    def test_配置标准训练图表(self):
        """测试: 标准训练图表配置"""
        图表 = 实时图表()
        图表.配置标准训练图表()
        
        配置 = 图表.获取子图配置()
        
        assert len(配置) == 3, "标准配置应有 3 个子图"
        assert "loss" in 配置
        assert "accuracy" in 配置
        assert "learning_rate" in 配置
    
    def test_配置简单图表(self):
        """测试: 简单图表配置"""
        图表 = 实时图表()
        图表.配置简单图表()
        
        配置 = 图表.获取子图配置()
        
        assert len(配置) == 1, "简单配置应有 1 个子图"
        assert "loss" in 配置
    
    def test_配置双指标图表(self):
        """测试: 双指标图表配置"""
        图表 = 实时图表()
        图表.配置双指标图表()
        
        配置 = 图表.获取子图配置()
        
        assert len(配置) == 2, "双指标配置应有 2 个子图"
        assert "loss" in 配置
        assert "accuracy" in 配置
    
    def test_清除子图配置(self):
        """测试: 清除子图配置"""
        图表 = 实时图表()
        图表.配置标准训练图表()
        
        assert len(图表.获取子图配置()) == 3
        
        图表.清除子图配置()
        
        assert len(图表.获取子图配置()) == 0, "清除后应无子图配置"
    
    def test_未启动时更新返回False(self):
        """测试: 未启动时更新应返回 False"""
        图表 = 实时图表()
        记录器 = 指标记录器()
        记录器.记录批次(1, 0.5)
        
        结果 = 图表.更新(记录器)
        
        assert not 结果, "未启动时更新应返回 False"
    
    def test_历史数据管理(self):
        """测试: 历史数据管理功能"""
        图表 = 实时图表()
        
        # 初始应为空
        assert len(图表.获取已叠加历史()) == 0
        
        # 清除历史
        结果 = 图表.清除历史叠加()
        assert 结果, "清除历史应返回 True"
    
    def test_repr(self):
        """测试: __repr__ 方法"""
        图表 = 实时图表(更新间隔=15)
        
        表示 = repr(图表)
        
        assert "未启动" in 表示
        assert "15" in 表示


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])
