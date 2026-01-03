# -*- coding: utf-8 -*-
"""
属性测试：恢复训练连续性
Property 4: 对于任意检查点恢复，恢复后的 batch 应紧接中断时的 batch

**Feature: checkpoint-resume-training, Property 4: 恢复训练连续性**
**验证: 需求 2.5**
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
from typing import List, Tuple, Optional

# 直接导入检查点管理模块
import importlib.util
检查点管理路径 = os.path.join(项目根目录, '工具', '检查点管理.py')
spec = importlib.util.spec_from_file_location("检查点管理", 检查点管理路径)
检查点管理模块 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(检查点管理模块)

检查点管理器 = 检查点管理模块.检查点管理器
计算恢复起点 = 检查点管理模块.计算恢复起点
训练恢复器 = 检查点管理模块.训练恢复器
恢复训练状态 = 检查点管理模块.恢复训练状态


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

# epoch 策略
epoch_strategy = st.integers(min_value=0, max_value=100)

# batch 策略
batch_strategy = st.integers(min_value=0, max_value=1000)

# 每 epoch 批次数策略
batches_per_epoch_strategy = st.integers(min_value=10, max_value=500)

# loss 值策略
loss_strategy = st.floats(
    min_value=0.0, 
    max_value=10.0, 
    allow_nan=False, 
    allow_infinity=False
)


# ==================== 属性测试类 ====================

class Test恢复训练连续性属性:
    """
    属性测试：恢复训练连续性
    
    **Feature: checkpoint-resume-training, Property 4: 恢复训练连续性**
    **验证: 需求 2.5**
    """
    
    @settings(max_examples=100, deadline=None)
    @given(
        中断epoch=epoch_strategy,
        中断batch=batch_strategy
    )
    def test_恢复后batch紧接中断batch(
        self,
        中断epoch: int,
        中断batch: int
    ):
        """
        属性测试: 对于任意检查点恢复，恢复后的 batch 应紧接中断时的 batch
        
        不指定每 epoch 批次数时，恢复后的 batch 应为中断 batch + 1
        
        **Feature: checkpoint-resume-training, Property 4: 恢复训练连续性**
        **验证: 需求 2.5**
        """
        临时目录 = tempfile.mkdtemp()
        try:
            管理器 = 检查点管理器(临时目录, 最大检查点数=5)
            模型 = 模拟模型({'layer1': [1.0, 2.0]})
            
            # 保存检查点（模拟训练中断）
            管理器.保存检查点(
                模型=模型,
                优化器状态={'lr': 0.001, 'step': 中断epoch * 100 + 中断batch},
                当前epoch=中断epoch,
                当前batch=中断batch,
                loss值=0.5
            )
            
            # 加载检查点
            检查点数据 = 管理器.加载检查点()
            assert 检查点数据 is not None, "应能加载检查点"
            
            # 计算恢复起点（不指定每 epoch 批次数）
            恢复起点 = 计算恢复起点(检查点数据)
            
            # 验证恢复后的 batch 紧接中断时的 batch
            assert 恢复起点['中断epoch'] == 中断epoch, \
                f"中断 epoch 应正确记录: 期望 {中断epoch}, 实际 {恢复起点['中断epoch']}"
            assert 恢复起点['中断batch'] == 中断batch, \
                f"中断 batch 应正确记录: 期望 {中断batch}, 实际 {恢复起点['中断batch']}"
            
            # 不指定每 epoch 批次数时，起始 batch 应为中断 batch + 1
            期望起始batch = 中断batch + 1
            assert 恢复起点['起始batch'] == 期望起始batch, \
                f"起始 batch 应紧接中断 batch: 期望 {期望起始batch}, 实际 {恢复起点['起始batch']}"
            assert 恢复起点['起始epoch'] == 中断epoch, \
                f"起始 epoch 应与中断 epoch 相同: 期望 {中断epoch}, 实际 {恢复起点['起始epoch']}"
        finally:
            shutil.rmtree(临时目录, ignore_errors=True)
    
    @settings(max_examples=100, deadline=None)
    @given(
        中断epoch=epoch_strategy,
        中断batch=batch_strategy,
        每epoch批次数=batches_per_epoch_strategy
    )
    def test_恢复时考虑epoch边界(
        self,
        中断epoch: int,
        中断batch: int,
        每epoch批次数: int
    ):
        """
        属性测试: 恢复时如果下一个 batch 超过 epoch 边界，应进入下一个 epoch
        
        **Feature: checkpoint-resume-training, Property 4: 恢复训练连续性**
        **验证: 需求 2.5**
        """
        # 确保中断 batch 在有效范围内
        assume(中断batch < 每epoch批次数)
        
        临时目录 = tempfile.mkdtemp()
        try:
            管理器 = 检查点管理器(临时目录, 最大检查点数=5)
            模型 = 模拟模型({'layer1': [1.0]})
            
            # 保存检查点
            管理器.保存检查点(
                模型=模型,
                优化器状态={'lr': 0.001},
                当前epoch=中断epoch,
                当前batch=中断batch,
                loss值=0.5
            )
            
            # 加载检查点
            检查点数据 = 管理器.加载检查点()
            assert 检查点数据 is not None, "应能加载检查点"
            
            # 计算恢复起点（指定每 epoch 批次数）
            恢复起点 = 计算恢复起点(检查点数据, 每epoch批次数=每epoch批次数)
            
            # 计算期望的起始位置
            下一batch = 中断batch + 1
            if 下一batch >= 每epoch批次数:
                # 应进入下一个 epoch
                期望起始epoch = 中断epoch + 1
                期望起始batch = 0
                期望是否新epoch = True
            else:
                # 继续当前 epoch
                期望起始epoch = 中断epoch
                期望起始batch = 下一batch
                期望是否新epoch = False
            
            assert 恢复起点['起始epoch'] == 期望起始epoch, \
                f"起始 epoch 不正确: 期望 {期望起始epoch}, 实际 {恢复起点['起始epoch']}"
            assert 恢复起点['起始batch'] == 期望起始batch, \
                f"起始 batch 不正确: 期望 {期望起始batch}, 实际 {恢复起点['起始batch']}"
            assert 恢复起点['是否新epoch'] == 期望是否新epoch, \
                f"是否新 epoch 不正确: 期望 {期望是否新epoch}, 实际 {恢复起点['是否新epoch']}"
        finally:
            shutil.rmtree(临时目录, ignore_errors=True)
    
    @settings(max_examples=100, deadline=None)
    @given(
        中断epoch=epoch_strategy,
        每epoch批次数=batches_per_epoch_strategy
    )
    def test_epoch最后一个batch恢复到下一epoch(
        self,
        中断epoch: int,
        每epoch批次数: int
    ):
        """
        属性测试: 如果中断在 epoch 的最后一个 batch，恢复应从下一个 epoch 的第一个 batch 开始
        
        **Feature: checkpoint-resume-training, Property 4: 恢复训练连续性**
        **验证: 需求 2.5**
        """
        # 中断在 epoch 的最后一个 batch
        中断batch = 每epoch批次数 - 1
        
        临时目录 = tempfile.mkdtemp()
        try:
            管理器 = 检查点管理器(临时目录, 最大检查点数=5)
            模型 = 模拟模型({'layer1': [1.0]})
            
            # 保存检查点
            管理器.保存检查点(
                模型=模型,
                优化器状态={'lr': 0.001},
                当前epoch=中断epoch,
                当前batch=中断batch,
                loss值=0.5
            )
            
            # 加载检查点
            检查点数据 = 管理器.加载检查点()
            
            # 计算恢复起点
            恢复起点 = 计算恢复起点(检查点数据, 每epoch批次数=每epoch批次数)
            
            # 验证恢复到下一个 epoch 的第一个 batch
            assert 恢复起点['起始epoch'] == 中断epoch + 1, \
                f"应恢复到下一个 epoch: 期望 {中断epoch + 1}, 实际 {恢复起点['起始epoch']}"
            assert 恢复起点['起始batch'] == 0, \
                f"应从 batch 0 开始: 期望 0, 实际 {恢复起点['起始batch']}"
            assert 恢复起点['是否新epoch'] == True, \
                "应标记为新 epoch"
        finally:
            shutil.rmtree(临时目录, ignore_errors=True)
    
    @settings(max_examples=100, deadline=None)
    @given(
        中断epoch=epoch_strategy,
        中断batch=batch_strategy
    )
    def test_训练恢复器连续性(
        self,
        中断epoch: int,
        中断batch: int
    ):
        """
        属性测试: 使用训练恢复器恢复时，起始位置应紧接中断位置
        
        **Feature: checkpoint-resume-training, Property 4: 恢复训练连续性**
        **验证: 需求 2.5**
        """
        临时目录 = tempfile.mkdtemp()
        try:
            管理器 = 检查点管理器(临时目录, 最大检查点数=5)
            模型 = 模拟模型({'layer1': [1.0, 2.0, 3.0]})
            
            # 保存检查点
            管理器.保存检查点(
                模型=模型,
                优化器状态={'lr': 0.001, 'momentum': 0.9},
                当前epoch=中断epoch,
                当前batch=中断batch,
                loss值=0.5
            )
            
            # 使用训练恢复器恢复
            恢复器 = 训练恢复器(管理器)
            新模型 = 模拟模型()
            
            结果 = 恢复器.恢复(新模型)
            
            assert 结果 is not None, "恢复应成功"
            
            # 验证起始位置紧接中断位置
            assert 恢复器.起始epoch == 中断epoch, \
                f"起始 epoch 应与中断 epoch 相同: 期望 {中断epoch}, 实际 {恢复器.起始epoch}"
            assert 恢复器.起始batch == 中断batch + 1, \
                f"起始 batch 应紧接中断 batch: 期望 {中断batch + 1}, 实际 {恢复器.起始batch}"
        finally:
            shutil.rmtree(临时目录, ignore_errors=True)
    
    @settings(max_examples=50, deadline=None)
    @given(
        检查点序列=st.lists(
            st.tuples(epoch_strategy, batch_strategy),
            min_size=2,
            max_size=5,
            unique=True
        )
    )
    def test_多检查点恢复最新后连续性(
        self,
        检查点序列: List[Tuple[int, int]]
    ):
        """
        属性测试: 保存多个检查点后，恢复最新检查点时应从最新位置的下一个 batch 继续
        
        **Feature: checkpoint-resume-training, Property 4: 恢复训练连续性**
        **验证: 需求 2.5**
        """
        临时目录 = tempfile.mkdtemp()
        try:
            管理器 = 检查点管理器(临时目录, 最大检查点数=len(检查点序列) + 5)
            模型 = 模拟模型({'layer1': [1.0]})
            
            # 保存多个检查点
            for epoch, batch in 检查点序列:
                管理器.保存检查点(
                    模型=模型,
                    优化器状态={'lr': 0.001},
                    当前epoch=epoch,
                    当前batch=batch,
                    loss值=0.5
                )
            
            # 计算最新的检查点（按 epoch, batch 排序）
            最新检查点 = max(检查点序列, key=lambda x: (x[0], x[1]))
            期望中断epoch, 期望中断batch = 最新检查点
            
            # 加载最新检查点并计算恢复起点
            检查点数据 = 管理器.加载检查点()
            恢复起点 = 计算恢复起点(检查点数据)
            
            # 验证恢复起点紧接最新检查点
            assert 恢复起点['中断epoch'] == 期望中断epoch, \
                f"中断 epoch 应为最新: 期望 {期望中断epoch}, 实际 {恢复起点['中断epoch']}"
            assert 恢复起点['中断batch'] == 期望中断batch, \
                f"中断 batch 应为最新: 期望 {期望中断batch}, 实际 {恢复起点['中断batch']}"
            assert 恢复起点['起始batch'] == 期望中断batch + 1, \
                f"起始 batch 应紧接中断: 期望 {期望中断batch + 1}, 实际 {恢复起点['起始batch']}"
        finally:
            shutil.rmtree(临时目录, ignore_errors=True)


# ==================== 单元测试 ====================

class Test恢复训练连续性单元测试:
    """恢复训练连续性的单元测试"""
    
    @pytest.fixture(autouse=True)
    def 初始化(self):
        """初始化测试环境"""
        self.临时目录 = tempfile.mkdtemp()
        yield
        shutil.rmtree(self.临时目录, ignore_errors=True)
    
    def test_基本恢复连续性(self):
        """测试: 基本的恢复连续性"""
        管理器 = 检查点管理器(self.临时目录)
        模型 = 模拟模型({'w': [1.0, 2.0]})
        
        # 保存检查点（模拟在 epoch 5, batch 100 中断）
        管理器.保存检查点(
            模型=模型,
            优化器状态={'lr': 0.01},
            当前epoch=5,
            当前batch=100,
            loss值=0.25
        )
        
        # 加载并计算恢复起点
        检查点数据 = 管理器.加载检查点()
        恢复起点 = 计算恢复起点(检查点数据)
        
        assert 恢复起点['中断epoch'] == 5
        assert 恢复起点['中断batch'] == 100
        assert 恢复起点['起始epoch'] == 5
        assert 恢复起点['起始batch'] == 101  # 紧接中断的 batch
    
    def test_epoch边界恢复(self):
        """测试: 在 epoch 边界恢复"""
        管理器 = 检查点管理器(self.临时目录)
        模型 = 模拟模型({'w': [1.0]})
        
        # 保存检查点（模拟在 epoch 3 的最后一个 batch 中断）
        管理器.保存检查点(
            模型=模型,
            优化器状态={'lr': 0.01},
            当前epoch=3,
            当前batch=99,  # 假设每 epoch 100 个 batch
            loss值=0.25
        )
        
        检查点数据 = 管理器.加载检查点()
        恢复起点 = 计算恢复起点(检查点数据, 每epoch批次数=100)
        
        assert 恢复起点['中断epoch'] == 3
        assert 恢复起点['中断batch'] == 99
        assert 恢复起点['起始epoch'] == 4  # 进入下一个 epoch
        assert 恢复起点['起始batch'] == 0  # 从 batch 0 开始
        assert 恢复起点['是否新epoch'] == True
    
    def test_epoch中间恢复(self):
        """测试: 在 epoch 中间恢复"""
        管理器 = 检查点管理器(self.临时目录)
        模型 = 模拟模型({'w': [1.0]})
        
        管理器.保存检查点(
            模型=模型,
            优化器状态={'lr': 0.01},
            当前epoch=3,
            当前batch=50,
            loss值=0.25
        )
        
        检查点数据 = 管理器.加载检查点()
        恢复起点 = 计算恢复起点(检查点数据, 每epoch批次数=100)
        
        assert 恢复起点['起始epoch'] == 3  # 继续当前 epoch
        assert 恢复起点['起始batch'] == 51  # 紧接中断的 batch
        assert 恢复起点['是否新epoch'] == False
    
    def test_训练恢复器完整流程(self):
        """测试: 训练恢复器的完整恢复流程"""
        管理器 = 检查点管理器(self.临时目录)
        原始模型 = 模拟模型({'layer1': [1.0, 2.0, 3.0], 'layer2': [4.0, 5.0]})
        
        # 保存检查点
        管理器.保存检查点(
            模型=原始模型,
            优化器状态={'lr': 0.001, 'momentum': 0.9, 'step': 500},
            当前epoch=10,
            当前batch=250,
            loss值=0.15
        )
        
        # 使用训练恢复器恢复
        恢复器 = 训练恢复器(管理器)
        新模型 = 模拟模型()
        
        结果 = 恢复器.恢复(新模型)
        
        assert 结果 is not None, "恢复应成功"
        assert 恢复器.起始epoch == 10
        assert 恢复器.起始batch == 251  # 紧接中断的 batch
        
        # 验证优化器状态恢复
        优化器状态 = 恢复器.优化器状态
        assert 优化器状态['lr'] == 0.001
        assert 优化器状态['momentum'] == 0.9
    
    def test_空检查点数据处理(self):
        """测试: 空检查点数据应抛出异常"""
        with pytest.raises(ValueError, match="检查点数据为空"):
            计算恢复起点(None)
    
    def test_batch_0恢复(self):
        """测试: 从 batch 0 中断后恢复"""
        管理器 = 检查点管理器(self.临时目录)
        模型 = 模拟模型({'w': [1.0]})
        
        管理器.保存检查点(
            模型=模型,
            优化器状态={'lr': 0.01},
            当前epoch=0,
            当前batch=0,
            loss值=1.0
        )
        
        检查点数据 = 管理器.加载检查点()
        恢复起点 = 计算恢复起点(检查点数据)
        
        assert 恢复起点['起始epoch'] == 0
        assert 恢复起点['起始batch'] == 1  # 从 batch 1 继续


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])
