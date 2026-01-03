# -*- coding: utf-8 -*-
"""
属性测试：检查点数量限制
Property 2: 对于任意保存操作序列，检查点数量应不超过配置的最大值

**Feature: checkpoint-resume-training, Property 2: 检查点数量限制**
**验证: 需求 1.4**
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
from typing import List, Tuple

# 直接导入检查点管理模块
import importlib.util
检查点管理路径 = os.path.join(项目根目录, '工具', '检查点管理.py')
spec = importlib.util.spec_from_file_location("检查点管理", 检查点管理路径)
检查点管理模块 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(检查点管理模块)

检查点管理器 = 检查点管理模块.检查点管理器


# ==================== 模拟模型类 ====================

class 模拟模型:
    """用于测试的模拟模型类"""
    
    def __init__(self, 权重=None):
        self._权重 = 权重 or {}
    
    def get_weights(self):
        return self._权重
    
    def set_weights(self, 权重):
        self._权重 = 权重


# ==================== 测试数据生成策略 ====================

# 最大检查点数策略（1-10个）
max_checkpoint_strategy = st.integers(min_value=1, max_value=10)

# 保存操作数量策略（1-20次保存）
save_count_strategy = st.integers(min_value=1, max_value=20)

# epoch 和 batch 策略
epoch_strategy = st.integers(min_value=0, max_value=100)
batch_strategy = st.integers(min_value=0, max_value=1000)

# loss 值策略
loss_strategy = st.floats(min_value=0.0, max_value=10.0, allow_nan=False, allow_infinity=False)


# ==================== 属性测试类 ====================

class Test检查点数量限制属性:
    """
    属性测试：检查点数量限制
    
    **Feature: checkpoint-resume-training, Property 2: 检查点数量限制**
    **验证: 需求 1.4**
    """
    
    @settings(max_examples=100, deadline=None)
    @given(
        最大检查点数=max_checkpoint_strategy,
        保存次数=save_count_strategy
    )
    def test_检查点数量不超过最大值(
        self,
        最大检查点数: int,
        保存次数: int
    ):
        """
        属性测试: 对于任意保存操作序列，检查点数量应不超过配置的最大值
        
        **Feature: checkpoint-resume-training, Property 2: 检查点数量限制**
        **验证: 需求 1.4**
        """
        临时目录 = tempfile.mkdtemp()
        try:
            管理器 = 检查点管理器(临时目录, 最大检查点数=最大检查点数)
            模型 = 模拟模型({'layer1': [1.0, 2.0]})
            
            # 执行多次保存操作
            for i in range(保存次数):
                管理器.保存检查点(
                    模型=模型,
                    优化器状态={'lr': 0.001, 'step': i},
                    当前epoch=i,
                    当前batch=0,
                    loss值=1.0 - i * 0.01
                )
                
                # 每次保存后验证数量限制
                检查点列表 = 管理器.列出检查点()
                当前数量 = len(检查点列表)
                
                assert 当前数量 <= 最大检查点数, \
                    f"检查点数量 {当前数量} 超过最大值 {最大检查点数}（第 {i+1} 次保存后）"
            
            # 最终验证
            最终列表 = 管理器.列出检查点()
            assert len(最终列表) <= 最大检查点数, \
                f"最终检查点数量 {len(最终列表)} 超过最大值 {最大检查点数}"
        finally:
            shutil.rmtree(临时目录, ignore_errors=True)
    
    @settings(max_examples=100, deadline=None)
    @given(
        最大检查点数=max_checkpoint_strategy,
        保存序列=st.lists(
            st.tuples(epoch_strategy, batch_strategy, loss_strategy),
            min_size=1,
            max_size=15
        )
    )
    def test_任意保存序列数量限制(
        self,
        最大检查点数: int,
        保存序列: List[Tuple[int, int, float]]
    ):
        """
        属性测试: 对于任意 epoch/batch/loss 组合的保存序列，数量应不超过最大值
        
        **Feature: checkpoint-resume-training, Property 2: 检查点数量限制**
        **验证: 需求 1.4**
        """
        临时目录 = tempfile.mkdtemp()
        try:
            管理器 = 检查点管理器(临时目录, 最大检查点数=最大检查点数)
            模型 = 模拟模型({'w': [0.5]})
            
            # 按序列保存检查点
            for epoch, batch, loss in 保存序列:
                管理器.保存检查点(
                    模型=模型,
                    优化器状态={'lr': 0.001},
                    当前epoch=epoch,
                    当前batch=batch,
                    loss值=loss
                )
            
            # 验证最终数量
            检查点列表 = 管理器.列出检查点()
            assert len(检查点列表) <= 最大检查点数, \
                f"检查点数量 {len(检查点列表)} 超过最大值 {最大检查点数}"
        finally:
            shutil.rmtree(临时目录, ignore_errors=True)
    
    @settings(max_examples=50, deadline=None)
    @given(
        最大检查点数=max_checkpoint_strategy
    )
    def test_保留最新检查点(
        self,
        最大检查点数: int
    ):
        """
        属性测试: 删除旧检查点时应保留最新的检查点
        
        **Feature: checkpoint-resume-training, Property 2: 检查点数量限制**
        **验证: 需求 1.4**
        """
        临时目录 = tempfile.mkdtemp()
        try:
            管理器 = 检查点管理器(临时目录, 最大检查点数=最大检查点数)
            模型 = 模拟模型({'w': [1.0]})
            
            # 保存超过限制数量的检查点
            总保存数 = 最大检查点数 + 5
            for i in range(总保存数):
                管理器.保存检查点(
                    模型=模型,
                    优化器状态={'lr': 0.001},
                    当前epoch=i,
                    当前batch=0,
                    loss值=1.0
                )
            
            # 获取保留的检查点
            检查点列表 = 管理器.列出检查点()
            保留的epochs = [项['epoch'] for 项 in 检查点列表]
            
            # 验证保留的是最新的检查点
            期望的最新epochs = list(range(总保存数 - 最大检查点数, 总保存数))
            
            for epoch in 期望的最新epochs:
                assert epoch in 保留的epochs, \
                    f"最新的 epoch {epoch} 应该被保留，但实际保留的是 {保留的epochs}"
        finally:
            shutil.rmtree(临时目录, ignore_errors=True)


# ==================== 单元测试 ====================

class Test检查点数量限制单元测试:
    """检查点数量限制的单元测试"""
    
    @pytest.fixture(autouse=True)
    def 初始化(self):
        """初始化测试环境"""
        self.临时目录 = tempfile.mkdtemp()
        yield
        shutil.rmtree(self.临时目录, ignore_errors=True)
    
    def test_最大检查点数为1(self):
        """测试: 最大检查点数为1时只保留最新的"""
        管理器 = 检查点管理器(self.临时目录, 最大检查点数=1)
        模型 = 模拟模型({'w': [1.0]})
        
        for i in range(5):
            管理器.保存检查点(
                模型=模型,
                优化器状态={},
                当前epoch=i,
                当前batch=0,
                loss值=1.0
            )
        
        检查点列表 = 管理器.列出检查点()
        assert len(检查点列表) == 1, "应只保留1个检查点"
        assert 检查点列表[0]['epoch'] == 4, "应保留最新的 epoch 4"
    
    def test_删除旧检查点返回值(self):
        """测试: 删除旧检查点方法应返回删除的数量"""
        管理器 = 检查点管理器(self.临时目录, 最大检查点数=3)
        模型 = 模拟模型({'w': [1.0]})
        
        # 保存5个检查点
        for i in range(5):
            管理器.保存检查点(
                模型=模型,
                优化器状态={},
                当前epoch=i,
                当前batch=0,
                loss值=1.0
            )
        
        # 手动调用删除（虽然保存时已自动调用）
        删除数量 = 管理器.删除旧检查点()
        
        # 由于保存时已删除，此时应该没有需要删除的
        assert 删除数量 == 0, "已经在保存时删除过了"
        
        检查点列表 = 管理器.列出检查点()
        assert len(检查点列表) == 3, "应保留3个检查点"
    
    def test_边界情况_恰好等于最大值(self):
        """测试: 保存数量恰好等于最大值时不应删除"""
        最大数 = 5
        管理器 = 检查点管理器(self.临时目录, 最大检查点数=最大数)
        模型 = 模拟模型({'w': [1.0]})
        
        for i in range(最大数):
            管理器.保存检查点(
                模型=模型,
                优化器状态={},
                当前epoch=i,
                当前batch=0,
                loss值=1.0
            )
        
        检查点列表 = 管理器.列出检查点()
        assert len(检查点列表) == 最大数, f"应保留 {最大数} 个检查点"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])
