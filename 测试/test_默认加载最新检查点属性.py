# -*- coding: utf-8 -*-
"""
属性测试：默认加载最新检查点
Property 3: 对于任意多个检查点，默认加载应返回最新的检查点

**Feature: checkpoint-resume-training, Property 3: 默认加载最新**
**验证: 需求 2.2**
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

# epoch 策略
epoch_strategy = st.integers(min_value=0, max_value=100)

# batch 策略
batch_strategy = st.integers(min_value=0, max_value=1000)

# loss 值策略
loss_strategy = st.floats(
    min_value=0.0, 
    max_value=10.0, 
    allow_nan=False, 
    allow_infinity=False
)

# 检查点序列策略：生成唯一的 (epoch, batch) 组合列表
checkpoint_sequence_strategy = st.lists(
    st.tuples(epoch_strategy, batch_strategy),
    min_size=2,
    max_size=10,
    unique=True
)


# ==================== 属性测试类 ====================

class Test默认加载最新检查点属性:
    """
    属性测试：默认加载最新检查点
    
    **Feature: checkpoint-resume-training, Property 3: 默认加载最新**
    **验证: 需求 2.2**
    """
    
    @settings(max_examples=100, deadline=None)
    @given(
        检查点序列=checkpoint_sequence_strategy
    )
    def test_默认加载返回epoch和batch最大的检查点(
        self,
        检查点序列: List[Tuple[int, int]]
    ):
        """
        属性测试: 对于任意多个检查点，默认加载应返回 epoch 和 batch 最大的检查点
        
        "最新"的定义：按 (epoch, batch) 排序后最大的检查点
        
        **Feature: checkpoint-resume-training, Property 3: 默认加载最新**
        **验证: 需求 2.2**
        """
        临时目录 = tempfile.mkdtemp()
        try:
            # 使用足够大的最大检查点数，确保所有检查点都被保留
            管理器 = 检查点管理器(临时目录, 最大检查点数=len(检查点序列) + 5)
            模型 = 模拟模型({'layer1': [1.0, 2.0]})
            
            # 保存所有检查点
            for epoch, batch in 检查点序列:
                管理器.保存检查点(
                    模型=模型,
                    优化器状态={'lr': 0.001},
                    当前epoch=epoch,
                    当前batch=batch,
                    loss值=0.5
                )
            
            # 计算期望的最新检查点（按 epoch, batch 排序后最大的）
            期望的最新 = max(检查点序列, key=lambda x: (x[0], x[1]))
            
            # 默认加载（不指定路径）
            加载的数据 = 管理器.加载检查点()
            
            assert 加载的数据 is not None, "应能加载检查点"
            
            训练进度 = 加载的数据.get('训练进度', {})
            实际epoch = 训练进度.get('当前epoch')
            实际batch = 训练进度.get('当前batch')
            
            assert 实际epoch == 期望的最新[0], \
                f"默认加载应返回最新 epoch: 期望 {期望的最新[0]}, 实际 {实际epoch}"
            assert 实际batch == 期望的最新[1], \
                f"默认加载应返回最新 batch: 期望 {期望的最新[1]}, 实际 {实际batch}"
        finally:
            shutil.rmtree(临时目录, ignore_errors=True)
    
    @settings(max_examples=100, deadline=None)
    @given(
        epoch序列=st.lists(
            epoch_strategy,
            min_size=2,
            max_size=8,
            unique=True
        )
    )
    def test_不同epoch的检查点默认加载最大epoch(
        self,
        epoch序列: List[int]
    ):
        """
        属性测试: 对于不同 epoch 的检查点，默认加载应返回最大 epoch 的检查点
        
        **Feature: checkpoint-resume-training, Property 3: 默认加载最新**
        **验证: 需求 2.2**
        """
        临时目录 = tempfile.mkdtemp()
        try:
            管理器 = 检查点管理器(临时目录, 最大检查点数=len(epoch序列) + 5)
            模型 = 模拟模型({'w': [1.0]})
            
            # 按随机顺序保存不同 epoch 的检查点
            for epoch in epoch序列:
                管理器.保存检查点(
                    模型=模型,
                    优化器状态={'lr': 0.001},
                    当前epoch=epoch,
                    当前batch=0,
                    loss值=1.0 / (epoch + 1)
                )
            
            期望的最大epoch = max(epoch序列)
            
            # 默认加载
            加载的数据 = 管理器.加载检查点()
            
            assert 加载的数据 is not None, "应能加载检查点"
            
            实际epoch = 加载的数据['训练进度']['当前epoch']
            assert 实际epoch == 期望的最大epoch, \
                f"默认加载应返回最大 epoch: 期望 {期望的最大epoch}, 实际 {实际epoch}"
        finally:
            shutil.rmtree(临时目录, ignore_errors=True)
    
    @settings(max_examples=100, deadline=None)
    @given(
        batch序列=st.lists(
            batch_strategy,
            min_size=2,
            max_size=8,
            unique=True
        ),
        固定epoch=epoch_strategy
    )
    def test_同epoch不同batch的检查点默认加载最大batch(
        self,
        batch序列: List[int],
        固定epoch: int
    ):
        """
        属性测试: 对于同一 epoch 不同 batch 的检查点，默认加载应返回最大 batch 的检查点
        
        **Feature: checkpoint-resume-training, Property 3: 默认加载最新**
        **验证: 需求 2.2**
        """
        临时目录 = tempfile.mkdtemp()
        try:
            管理器 = 检查点管理器(临时目录, 最大检查点数=len(batch序列) + 5)
            模型 = 模拟模型({'w': [1.0]})
            
            # 保存同一 epoch 不同 batch 的检查点
            for batch in batch序列:
                管理器.保存检查点(
                    模型=模型,
                    优化器状态={'lr': 0.001},
                    当前epoch=固定epoch,
                    当前batch=batch,
                    loss值=0.5
                )
            
            期望的最大batch = max(batch序列)
            
            # 默认加载
            加载的数据 = 管理器.加载检查点()
            
            assert 加载的数据 is not None, "应能加载检查点"
            
            实际batch = 加载的数据['训练进度']['当前batch']
            assert 实际batch == 期望的最大batch, \
                f"默认加载应返回最大 batch: 期望 {期望的最大batch}, 实际 {实际batch}"
        finally:
            shutil.rmtree(临时目录, ignore_errors=True)
    
    @settings(max_examples=50, deadline=None)
    @given(
        检查点序列=checkpoint_sequence_strategy,
        最大检查点数=st.integers(min_value=2, max_value=5)
    )
    def test_数量限制后仍加载最新检查点(
        self,
        检查点序列: List[Tuple[int, int]],
        最大检查点数: int
    ):
        """
        属性测试: 即使旧检查点被删除，默认加载仍应返回保留的最新检查点
        
        **Feature: checkpoint-resume-training, Property 3: 默认加载最新**
        **验证: 需求 2.2**
        """
        # 确保检查点数量大于限制，以触发删除
        assume(len(检查点序列) > 最大检查点数)
        
        临时目录 = tempfile.mkdtemp()
        try:
            管理器 = 检查点管理器(临时目录, 最大检查点数=最大检查点数)
            模型 = 模拟模型({'w': [1.0]})
            
            # 保存所有检查点
            for epoch, batch in 检查点序列:
                管理器.保存检查点(
                    模型=模型,
                    优化器状态={'lr': 0.001},
                    当前epoch=epoch,
                    当前batch=batch,
                    loss值=0.5
                )
            
            # 获取保留的检查点列表
            保留的检查点 = 管理器.列出检查点()
            assert len(保留的检查点) <= 最大检查点数, "检查点数量应不超过限制"
            
            # 计算保留检查点中的最新（按 epoch, batch 排序）
            期望的最新 = max(
                [(项['epoch'], 项['batch']) for 项 in 保留的检查点],
                key=lambda x: (x[0], x[1])
            )
            
            # 默认加载
            加载的数据 = 管理器.加载检查点()
            
            assert 加载的数据 is not None, "应能加载检查点"
            
            训练进度 = 加载的数据.get('训练进度', {})
            实际 = (训练进度.get('当前epoch'), 训练进度.get('当前batch'))
            
            assert 实际 == 期望的最新, \
                f"默认加载应返回保留的最新检查点: 期望 {期望的最新}, 实际 {实际}"
        finally:
            shutil.rmtree(临时目录, ignore_errors=True)


# ==================== 单元测试 ====================

class Test默认加载最新检查点单元测试:
    """默认加载最新检查点的单元测试"""
    
    @pytest.fixture(autouse=True)
    def 初始化(self):
        """初始化测试环境"""
        self.临时目录 = tempfile.mkdtemp()
        yield
        shutil.rmtree(self.临时目录, ignore_errors=True)
    
    def test_单个检查点默认加载(self):
        """测试: 只有一个检查点时默认加载该检查点"""
        管理器 = 检查点管理器(self.临时目录)
        模型 = 模拟模型({'w': [1.0]})
        
        管理器.保存检查点(
            模型=模型,
            优化器状态={'lr': 0.001},
            当前epoch=5,
            当前batch=100,
            loss值=0.25
        )
        
        数据 = 管理器.加载检查点()
        
        assert 数据 is not None, "应能加载检查点"
        assert 数据['训练进度']['当前epoch'] == 5
        assert 数据['训练进度']['当前batch'] == 100
    
    def test_无检查点时默认加载返回None(self):
        """测试: 没有检查点时默认加载返回 None"""
        管理器 = 检查点管理器(self.临时目录)
        
        数据 = 管理器.加载检查点()
        
        assert 数据 is None, "没有检查点时应返回 None"
    
    def test_乱序保存后默认加载最新(self):
        """测试: 乱序保存检查点后，默认加载应返回 epoch/batch 最大的"""
        管理器 = 检查点管理器(self.临时目录, 最大检查点数=10)
        模型 = 模拟模型({'w': [1.0]})
        
        # 乱序保存检查点
        保存顺序 = [(3, 0), (1, 0), (5, 0), (2, 0), (4, 0)]
        for epoch, batch in 保存顺序:
            管理器.保存检查点(
                模型=模型,
                优化器状态={'lr': 0.001},
                当前epoch=epoch,
                当前batch=batch,
                loss值=0.5
            )
        
        数据 = 管理器.加载检查点()
        
        assert 数据 is not None, "应能加载检查点"
        assert 数据['训练进度']['当前epoch'] == 5, "应加载最大 epoch 的检查点"
    
    def test_同epoch不同batch乱序保存(self):
        """测试: 同一 epoch 不同 batch 乱序保存后，默认加载最大 batch"""
        管理器 = 检查点管理器(self.临时目录, 最大检查点数=10)
        模型 = 模拟模型({'w': [1.0]})
        
        # 同一 epoch 乱序保存不同 batch
        for batch in [300, 100, 500, 200, 400]:
            管理器.保存检查点(
                模型=模型,
                优化器状态={'lr': 0.001},
                当前epoch=10,
                当前batch=batch,
                loss值=0.5
            )
        
        数据 = 管理器.加载检查点()
        
        assert 数据 is not None, "应能加载检查点"
        assert 数据['训练进度']['当前epoch'] == 10
        assert 数据['训练进度']['当前batch'] == 500, "应加载最大 batch 的检查点"
    
    def test_最新链接文件更新(self):
        """测试: 保存检查点后最新链接文件应指向最新检查点"""
        管理器 = 检查点管理器(self.临时目录, 最大检查点数=10)
        模型 = 模拟模型({'w': [1.0]})
        
        # 保存多个检查点
        for epoch in [1, 2, 3]:
            管理器.保存检查点(
                模型=模型,
                优化器状态={'lr': 0.001},
                当前epoch=epoch,
                当前batch=0,
                loss值=0.5
            )
        
        # 检查最新链接文件
        链接路径 = os.path.join(self.临时目录, 检查点管理器.最新检查点链接名)
        assert os.path.exists(链接路径), "最新链接文件应存在"
        
        with open(链接路径, 'r', encoding='utf-8') as f:
            链接内容 = f.read().strip()
        
        # 链接应指向 epoch 3 的检查点
        assert 'epoch_003' in 链接内容, "最新链接应指向 epoch 3 的检查点"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])
