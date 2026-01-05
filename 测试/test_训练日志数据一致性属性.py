# -*- coding: utf-8 -*-
"""
属性测试：训练日志数据一致性
Property 1: 对于任意保存的日志文件，重新加载后应与内存数据一致

**Feature: training-visualization, Property 1: 数据一致性**
**验证: 需求 1.5**
"""

import sys
import os
import tempfile
import shutil

# 添加项目根目录到路径
项目根目录 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, 项目根目录)

import pytest
from hypothesis import given, strategies as st, settings, assume
from typing import Dict, Any, List, Optional

from 训练.训练监控 import 指标记录器, 批次指标, 轮次指标


# ==================== 测试数据生成策略 ====================

# 有效的批次号策略
valid_batch_strategy = st.integers(min_value=0, max_value=10000)

# 有效的轮次号策略
valid_epoch_strategy = st.integers(min_value=1, max_value=1000)

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

# 有效的学习率策略
valid_learning_rate_strategy = st.floats(
    min_value=1e-8,
    max_value=1.0,
    allow_nan=False,
    allow_infinity=False
)

# 可选的准确率策略
optional_accuracy_strategy = st.one_of(st.none(), valid_accuracy_strategy)

# 可选的学习率策略
optional_learning_rate_strategy = st.one_of(st.none(), valid_learning_rate_strategy)

# 批次指标策略
batch_metrics_strategy = st.fixed_dictionaries({
    '批次': valid_batch_strategy,
    'loss': valid_loss_strategy
})

# 轮次指标策略
epoch_metrics_strategy = st.fixed_dictionaries({
    '轮次': valid_epoch_strategy,
    '训练loss': valid_loss_strategy,
    '验证loss': st.one_of(st.none(), valid_loss_strategy),
    '训练准确率': optional_accuracy_strategy,
    '验证准确率': optional_accuracy_strategy,
    '学习率': optional_learning_rate_strategy
})


# ==================== 属性测试类 ====================

class Test训练日志数据一致性属性:
    """
    属性测试：训练日志数据一致性
    
    **Feature: training-visualization, Property 1: 数据一致性**
    **验证: 需求 1.5**
    """
    
    @pytest.fixture(autouse=True)
    def 初始化(self):
        """初始化测试环境"""
        self.临时目录 = tempfile.mkdtemp()
        yield
        shutil.rmtree(self.临时目录, ignore_errors=True)
    
    @settings(max_examples=100, deadline=None)
    @given(
        批次列表=st.lists(batch_metrics_strategy, min_size=1, max_size=50),
        轮次列表=st.lists(epoch_metrics_strategy, min_size=1, max_size=10)
    )
    def test_保存后加载数据一致性(
        self,
        批次列表: List[Dict[str, Any]],
        轮次列表: List[Dict[str, Any]]
    ):
        """
        属性测试: 对于任意保存的日志文件，重新加载后应与内存数据一致
        
        **Feature: training-visualization, Property 1: 数据一致性**
        **验证: 需求 1.5**
        """
        # 创建记录器并添加数据
        记录器 = 指标记录器(self.临时目录)
        记录器.开始训练()
        
        # 记录批次数据
        for 批次数据 in 批次列表:
            记录器.记录批次(批次数据['批次'], 批次数据['loss'])
        
        # 记录轮次数据
        for 轮次数据 in 轮次列表:
            记录器.记录轮次(
                轮次=轮次数据['轮次'],
                训练loss=轮次数据['训练loss'],
                验证loss=轮次数据['验证loss'],
                训练准确率=轮次数据['训练准确率'],
                验证准确率=轮次数据['验证准确率'],
                学习率=轮次数据['学习率']
            )
        
        # 保存到文件
        文件路径 = os.path.join(self.临时目录, "test_log.json")
        记录器.保存(文件路径)
        
        # 创建新记录器并加载
        新记录器 = 指标记录器()
        加载成功 = 新记录器.加载(文件路径)
        
        # 验证加载成功
        assert 加载成功, "应能成功加载日志文件"
        
        # 验证批次数量一致
        原始批次历史 = 记录器.获取批次历史()
        加载批次历史 = 新记录器.获取批次历史()
        assert len(原始批次历史) == len(加载批次历史), \
            f"批次数量应一致: 原始 {len(原始批次历史)}, 加载 {len(加载批次历史)}"
        
        # 验证轮次数量一致
        原始轮次历史 = 记录器.获取轮次历史()
        加载轮次历史 = 新记录器.获取轮次历史()
        assert len(原始轮次历史) == len(加载轮次历史), \
            f"轮次数量应一致: 原始 {len(原始轮次历史)}, 加载 {len(加载轮次历史)}"
        
        # 验证批次数据一致
        for i, (原始, 加载) in enumerate(zip(原始批次历史, 加载批次历史)):
            assert 原始.批次 == 加载.批次, \
                f"批次 {i} 的批次号应一致: 原始 {原始.批次}, 加载 {加载.批次}"
            assert abs(原始.loss - 加载.loss) < 1e-6, \
                f"批次 {i} 的 loss 应一致: 原始 {原始.loss}, 加载 {加载.loss}"
        
        # 验证轮次数据一致
        for i, (原始, 加载) in enumerate(zip(原始轮次历史, 加载轮次历史)):
            assert 原始.轮次 == 加载.轮次, \
                f"轮次 {i} 的轮次号应一致: 原始 {原始.轮次}, 加载 {加载.轮次}"
            assert abs(原始.训练loss - 加载.训练loss) < 1e-6, \
                f"轮次 {i} 的训练loss应一致: 原始 {原始.训练loss}, 加载 {加载.训练loss}"
            
            # 验证可选字段
            if 原始.验证loss is not None:
                assert 加载.验证loss is not None, f"轮次 {i} 的验证loss应存在"
                assert abs(原始.验证loss - 加载.验证loss) < 1e-6, \
                    f"轮次 {i} 的验证loss应一致"
            
            if 原始.训练准确率 is not None:
                assert 加载.训练准确率 is not None, f"轮次 {i} 的训练准确率应存在"
                assert abs(原始.训练准确率 - 加载.训练准确率) < 1e-6, \
                    f"轮次 {i} 的训练准确率应一致"
            
            if 原始.验证准确率 is not None:
                assert 加载.验证准确率 is not None, f"轮次 {i} 的验证准确率应存在"
                assert abs(原始.验证准确率 - 加载.验证准确率) < 1e-6, \
                    f"轮次 {i} 的验证准确率应一致"
            
            if 原始.学习率 is not None:
                assert 加载.学习率 is not None, f"轮次 {i} 的学习率应存在"
                assert abs(原始.学习率 - 加载.学习率) < 1e-6, \
                    f"轮次 {i} 的学习率应一致"
    
    @settings(max_examples=100, deadline=None)
    @given(
        批次列表=st.lists(batch_metrics_strategy, min_size=1, max_size=50)
    )
    def test_loss历史获取一致性(self, 批次列表: List[Dict[str, Any]]):
        """
        属性测试: 获取历史方法应返回与记录一致的数据
        
        **Feature: training-visualization, Property 1: 数据一致性**
        **验证: 需求 1.5**
        """
        记录器 = 指标记录器(self.临时目录)
        
        # 记录批次数据
        期望的loss列表 = []
        for 批次数据 in 批次列表:
            记录器.记录批次(批次数据['批次'], 批次数据['loss'])
            期望的loss列表.append(批次数据['loss'])
        
        # 获取历史
        实际的loss列表 = 记录器.获取历史('loss')
        
        # 验证一致性
        assert len(期望的loss列表) == len(实际的loss列表), \
            f"loss 历史长度应一致: 期望 {len(期望的loss列表)}, 实际 {len(实际的loss列表)}"
        
        for i, (期望, 实际) in enumerate(zip(期望的loss列表, 实际的loss列表)):
            assert abs(期望 - 实际) < 1e-6, \
                f"loss[{i}] 应一致: 期望 {期望}, 实际 {实际}"
    
    @settings(max_examples=50, deadline=None)
    @given(
        轮次列表=st.lists(epoch_metrics_strategy, min_size=1, max_size=20)
    )
    def test_轮次指标历史获取一致性(self, 轮次列表: List[Dict[str, Any]]):
        """
        属性测试: 轮次指标的获取历史方法应返回与记录一致的数据
        
        **Feature: training-visualization, Property 1: 数据一致性**
        **验证: 需求 1.5**
        """
        记录器 = 指标记录器(self.临时目录)
        
        期望的训练loss = []
        期望的验证loss = []
        期望的训练准确率 = []
        期望的验证准确率 = []
        期望的学习率 = []
        
        # 记录轮次数据
        for 轮次数据 in 轮次列表:
            记录器.记录轮次(
                轮次=轮次数据['轮次'],
                训练loss=轮次数据['训练loss'],
                验证loss=轮次数据['验证loss'],
                训练准确率=轮次数据['训练准确率'],
                验证准确率=轮次数据['验证准确率'],
                学习率=轮次数据['学习率']
            )
            期望的训练loss.append(轮次数据['训练loss'])
            if 轮次数据['验证loss'] is not None:
                期望的验证loss.append(轮次数据['验证loss'])
            if 轮次数据['训练准确率'] is not None:
                期望的训练准确率.append(轮次数据['训练准确率'])
            if 轮次数据['验证准确率'] is not None:
                期望的验证准确率.append(轮次数据['验证准确率'])
            if 轮次数据['学习率'] is not None:
                期望的学习率.append(轮次数据['学习率'])
        
        # 验证训练loss
        实际的训练loss = 记录器.获取历史('训练loss')
        assert len(期望的训练loss) == len(实际的训练loss), "训练loss历史长度应一致"
        for i, (期望, 实际) in enumerate(zip(期望的训练loss, 实际的训练loss)):
            assert abs(期望 - 实际) < 1e-6, f"训练loss[{i}] 应一致"
        
        # 验证验证loss
        实际的验证loss = 记录器.获取历史('验证loss')
        assert len(期望的验证loss) == len(实际的验证loss), "验证loss历史长度应一致"
        for i, (期望, 实际) in enumerate(zip(期望的验证loss, 实际的验证loss)):
            assert abs(期望 - 实际) < 1e-6, f"验证loss[{i}] 应一致"
        
        # 验证训练准确率
        实际的训练准确率 = 记录器.获取历史('训练准确率')
        assert len(期望的训练准确率) == len(实际的训练准确率), "训练准确率历史长度应一致"
        
        # 验证验证准确率
        实际的验证准确率 = 记录器.获取历史('验证准确率')
        assert len(期望的验证准确率) == len(实际的验证准确率), "验证准确率历史长度应一致"
        
        # 验证学习率
        实际的学习率 = 记录器.获取历史('学习率')
        assert len(期望的学习率) == len(实际的学习率), "学习率历史长度应一致"


# ==================== 单元测试 ====================

class Test训练日志单元测试:
    """训练日志的单元测试"""
    
    @pytest.fixture(autouse=True)
    def 初始化(self):
        """初始化测试环境"""
        self.临时目录 = tempfile.mkdtemp()
        yield
        shutil.rmtree(self.临时目录, ignore_errors=True)
    
    def test_空记录器保存加载(self):
        """测试: 空记录器的保存和加载"""
        记录器 = 指标记录器(self.临时目录)
        文件路径 = os.path.join(self.临时目录, "empty.json")
        记录器.保存(文件路径)
        
        新记录器 = 指标记录器()
        成功 = 新记录器.加载(文件路径)
        
        assert 成功, "应能加载空日志"
        assert len(新记录器.获取批次历史()) == 0, "批次历史应为空"
        assert len(新记录器.获取轮次历史()) == 0, "轮次历史应为空"
    
    def test_加载不存在的文件(self):
        """测试: 加载不存在的文件应返回 False"""
        记录器 = 指标记录器()
        成功 = 记录器.加载("不存在的文件.json")
        assert not 成功, "加载不存在的文件应返回 False"
    
    def test_加载损坏的文件(self):
        """测试: 加载损坏的 JSON 文件应返回 False"""
        损坏文件 = os.path.join(self.临时目录, "corrupted.json")
        with open(损坏文件, 'w') as f:
            f.write("这不是有效的JSON{{{")
        
        记录器 = 指标记录器()
        成功 = 记录器.加载(损坏文件)
        assert not 成功, "加载损坏的文件应返回 False"
    
    def test_清空功能(self):
        """测试: 清空功能应清除所有历史"""
        记录器 = 指标记录器(self.临时目录)
        记录器.记录批次(1, 0.5)
        记录器.记录轮次(1, 0.4)
        
        assert len(记录器.获取批次历史()) == 1
        assert len(记录器.获取轮次历史()) == 1
        
        记录器.清空()
        
        assert len(记录器.获取批次历史()) == 0, "清空后批次历史应为空"
        assert len(记录器.获取轮次历史()) == 0, "清空后轮次历史应为空"
    
    def test_获取最新指标(self):
        """测试: 获取最新指标功能"""
        记录器 = 指标记录器(self.临时目录)
        
        # 空记录器
        assert 记录器.获取最新批次指标() is None
        assert 记录器.获取最新轮次指标() is None
        
        # 添加数据后
        记录器.记录批次(1, 0.8)
        记录器.记录批次(2, 0.6)
        记录器.记录轮次(1, 0.7)
        
        最新批次 = 记录器.获取最新批次指标()
        assert 最新批次 is not None
        assert 最新批次.批次 == 2
        assert abs(最新批次.loss - 0.6) < 1e-6
        
        最新轮次 = 记录器.获取最新轮次指标()
        assert 最新轮次 is not None
        assert 最新轮次.轮次 == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])
