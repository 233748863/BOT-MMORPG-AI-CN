# -*- coding: utf-8 -*-
"""
属性测试：检查点保存完整性
Property 1: 对于任意训练状态，保存后加载应得到等价的状态

**Feature: checkpoint-resume-training, Property 1: 检查点保存完整性**
**验证: 需求 1.2, 2.3, 3.1**
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
from typing import Dict, Any, List

# 直接导入检查点管理模块，避免工具包的导入问题
import importlib.util
检查点管理路径 = os.path.join(项目根目录, '工具', '检查点管理.py')
spec = importlib.util.spec_from_file_location("检查点管理", 检查点管理路径)
检查点管理模块 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(检查点管理模块)

检查点管理器 = 检查点管理模块.检查点管理器
训练状态 = 检查点管理模块.训练状态
检查点元数据 = 检查点管理模块.检查点元数据


# ==================== 测试数据生成策略 ====================

# 有效的 epoch 策略
valid_epoch_strategy = st.integers(min_value=0, max_value=1000)

# 有效的 batch 策略
valid_batch_strategy = st.integers(min_value=0, max_value=10000)

# 有效的 loss 值策略
valid_loss_strategy = st.floats(
    min_value=0.0,
    max_value=100.0,
    allow_nan=False,
    allow_infinity=False
)

# 简单的模型权重策略（模拟权重字典）
simple_weight_strategy = st.dictionaries(
    keys=st.text(
        min_size=1,
        max_size=20,
        alphabet="abcdefghijklmnopqrstuvwxyz_"
    ),
    values=st.lists(
        st.floats(min_value=-10.0, max_value=10.0, allow_nan=False, allow_infinity=False),
        min_size=1,
        max_size=10
    ),
    min_size=1,
    max_size=5
)

# 简单的优化器状态策略
simple_optimizer_state_strategy = st.fixed_dictionaries({
    'learning_rate': st.floats(min_value=1e-6, max_value=1.0, allow_nan=False, allow_infinity=False),
    'step': st.integers(min_value=0, max_value=100000),
    'momentum': st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)
})


# ==================== 模拟模型类 ====================

class 模拟模型:
    """用于测试的模拟模型类"""
    
    def __init__(self, 权重: Dict[str, Any] = None):
        self._权重 = 权重 or {}
    
    def get_weights(self):
        """获取模型权重"""
        return self._权重
    
    def set_weights(self, 权重):
        """设置模型权重"""
        self._权重 = 权重


# ==================== 属性测试类 ====================

class Test检查点完整性属性:
    """
    属性测试：检查点保存完整性
    
    **Feature: checkpoint-resume-training, Property 1: 检查点保存完整性**
    **验证: 需求 1.2, 2.3, 3.1**
    """
    
    @settings(max_examples=100, deadline=None)
    @given(
        当前epoch=valid_epoch_strategy,
        当前batch=valid_batch_strategy,
        loss值=valid_loss_strategy,
        优化器状态=simple_optimizer_state_strategy,
        模型权重=simple_weight_strategy
    )
    def test_检查点保存后加载一致性(
        self,
        当前epoch: int,
        当前batch: int,
        loss值: float,
        优化器状态: Dict[str, Any],
        模型权重: Dict[str, Any]
    ):
        """
        属性测试: 对于任意训练状态，保存后加载应得到等价的状态
        
        **Feature: checkpoint-resume-training, Property 1: 检查点保存完整性**
        **验证: 需求 1.2, 2.3, 3.1**
        """
        # 每次测试使用独立的临时目录
        临时目录 = tempfile.mkdtemp()
        try:
            # 创建检查点管理器
            管理器 = 检查点管理器(临时目录, 最大检查点数=5)
            
            # 创建模拟模型
            模型 = 模拟模型(模型权重)
            
            # 保存检查点
            检查点路径 = 管理器.保存检查点(
                模型=模型,
                优化器状态=优化器状态,
                当前epoch=当前epoch,
                当前batch=当前batch,
                loss值=loss值
            )
            
            # 验证检查点文件存在
            assert os.path.exists(检查点路径), f"检查点文件应存在: {检查点路径}"
            
            # 加载检查点
            加载的数据 = 管理器.加载检查点(检查点路径)
            
            # 验证加载成功
            assert 加载的数据 is not None, "应能成功加载检查点"
            
            # 验证训练进度一致性
            训练进度 = 加载的数据.get('训练进度', {})
            assert 训练进度.get('当前epoch') == 当前epoch, \
                f"epoch 应一致: 期望 {当前epoch}, 实际 {训练进度.get('当前epoch')}"
            assert 训练进度.get('当前batch') == 当前batch, \
                f"batch 应一致: 期望 {当前batch}, 实际 {训练进度.get('当前batch')}"
            
            # 验证 loss 值一致性
            指标 = 加载的数据.get('指标', {})
            assert abs(指标.get('loss', 0) - loss值) < 1e-6, \
                f"loss 应一致: 期望 {loss值}, 实际 {指标.get('loss')}"
            
            # 验证优化器状态一致性
            加载的优化器状态 = 加载的数据.get('优化器状态', {})
            for 键, 值 in 优化器状态.items():
                assert 键 in 加载的优化器状态, f"优化器状态应包含键: {键}"
                if isinstance(值, float):
                    assert abs(加载的优化器状态[键] - 值) < 1e-6, \
                        f"优化器状态 {键} 应一致: 期望 {值}, 实际 {加载的优化器状态[键]}"
                else:
                    assert 加载的优化器状态[键] == 值, \
                        f"优化器状态 {键} 应一致: 期望 {值}, 实际 {加载的优化器状态[键]}"
            
            # 验证模型权重一致性
            加载的权重 = 加载的数据.get('模型权重', {})
            assert 加载的权重.get('类型') == 'tflearn', "权重类型应为 tflearn"
            加载的权重数据 = 加载的权重.get('权重', {})
            for 键, 值 in 模型权重.items():
                assert 键 in 加载的权重数据, f"模型权重应包含键: {键}"
                # 比较列表中的浮点数
                for i, (期望值, 实际值) in enumerate(zip(值, 加载的权重数据[键])):
                    assert abs(期望值 - 实际值) < 1e-6, \
                        f"模型权重 {键}[{i}] 应一致: 期望 {期望值}, 实际 {实际值}"
        finally:
            # 清理临时目录
            shutil.rmtree(临时目录, ignore_errors=True)


    @settings(max_examples=100, deadline=None)
    @given(
        当前epoch=valid_epoch_strategy,
        当前batch=valid_batch_strategy,
        loss值=valid_loss_strategy
    )
    def test_默认加载最新检查点(
        self,
        当前epoch: int,
        当前batch: int,
        loss值: float
    ):
        """
        属性测试: 不指定路径时应加载最新的检查点
        
        **Feature: checkpoint-resume-training, Property 1: 检查点保存完整性**
        **验证: 需求 1.2, 2.3, 3.1**
        """
        # 每次测试使用独立的临时目录
        临时目录 = tempfile.mkdtemp()
        try:
            管理器 = 检查点管理器(临时目录, 最大检查点数=5)
            模型 = 模拟模型({'layer1': [1.0, 2.0, 3.0]})
            
            # 保存检查点
            管理器.保存检查点(
                模型=模型,
                优化器状态={'lr': 0.001},
                当前epoch=当前epoch,
                当前batch=当前batch,
                loss值=loss值
            )
            
            # 不指定路径加载（应加载最新）
            加载的数据 = 管理器.加载检查点()
            
            assert 加载的数据 is not None, "应能加载最新检查点"
            
            训练进度 = 加载的数据.get('训练进度', {})
            assert 训练进度.get('当前epoch') == 当前epoch, "应加载正确的 epoch"
            assert 训练进度.get('当前batch') == 当前batch, "应加载正确的 batch"
        finally:
            # 清理临时目录
            shutil.rmtree(临时目录, ignore_errors=True)
    
    @settings(max_examples=50, deadline=None)
    @given(
        epoch序列=st.lists(
            st.tuples(valid_epoch_strategy, valid_batch_strategy),
            min_size=2,
            max_size=5,
            unique=True
        )
    )
    def test_多检查点保存后加载最新(self, epoch序列):
        """
        属性测试: 保存多个检查点后，默认加载应返回训练进度最新的检查点
        
        注意: "最新"指的是训练进度最新的检查点（epoch/batch 最大的），
        而不是最后保存的检查点。这确保了即使乱序保存，也能正确恢复到最新进度。
        
        **Feature: checkpoint-resume-training, Property 1: 检查点保存完整性**
        **验证: 需求 1.2, 2.3, 3.1**
        """
        # 每次测试使用独立的临时目录
        临时目录 = tempfile.mkdtemp()
        try:
            管理器 = 检查点管理器(临时目录, 最大检查点数=10)
            模型 = 模拟模型({'layer1': [1.0]})
            
            # 保存多个检查点
            for epoch, batch in epoch序列:
                管理器.保存检查点(
                    模型=模型,
                    优化器状态={'lr': 0.001},
                    当前epoch=epoch,
                    当前batch=batch,
                    loss值=0.5
                )
            
            # 计算训练进度最新的检查点（epoch/batch 最大的）
            期望的最新 = max(epoch序列, key=lambda x: (x[0], x[1]))
            
            # 加载最新检查点（应该是训练进度最新的）
            加载的数据 = 管理器.加载检查点()
            
            assert 加载的数据 is not None, "应能加载检查点"
            
            训练进度 = 加载的数据.get('训练进度', {})
            assert 训练进度.get('当前epoch') == 期望的最新[0], \
                f"应加载训练进度最新的 epoch: 期望 {期望的最新[0]}, 实际 {训练进度.get('当前epoch')}"
            assert 训练进度.get('当前batch') == 期望的最新[1], \
                f"应加载训练进度最新的 batch: 期望 {期望的最新[1]}, 实际 {训练进度.get('当前batch')}"
        finally:
            # 清理临时目录
            shutil.rmtree(临时目录, ignore_errors=True)


# ==================== 单元测试 ====================

class Test检查点完整性单元测试:
    """检查点完整性的单元测试"""
    
    @pytest.fixture(autouse=True)
    def 初始化(self):
        """初始化测试环境"""
        self.临时目录 = tempfile.mkdtemp()
        yield
        shutil.rmtree(self.临时目录, ignore_errors=True)
    
    def test_空目录创建(self):
        """测试: 新建管理器应创建保存目录"""
        保存目录 = os.path.join(self.临时目录, "checkpoints")
        管理器 = 检查点管理器(保存目录)
        assert os.path.exists(保存目录), "保存目录应被创建"
    
    def test_基本保存加载(self):
        """测试: 基本的保存和加载功能"""
        管理器 = 检查点管理器(self.临时目录)
        模型 = 模拟模型({'w': [1.0, 2.0]})
        
        路径 = 管理器.保存检查点(
            模型=模型,
            优化器状态={'lr': 0.01},
            当前epoch=5,
            当前batch=100,
            loss值=0.25
        )
        
        assert os.path.exists(路径), "检查点文件应存在"
        
        数据 = 管理器.加载检查点(路径)
        assert 数据 is not None, "应能加载检查点"
        assert 数据['训练进度']['当前epoch'] == 5
        assert 数据['训练进度']['当前batch'] == 100
    
    def test_检查点列表(self):
        """测试: 列出检查点功能"""
        管理器 = 检查点管理器(self.临时目录)
        模型 = 模拟模型({'w': [1.0]})
        
        # 保存多个检查点
        for i in range(3):
            管理器.保存检查点(
                模型=模型,
                优化器状态={},
                当前epoch=i,
                当前batch=0,
                loss值=1.0 - i * 0.1
            )
        
        列表 = 管理器.列出检查点()
        assert len(列表) == 3, "应有3个检查点"
        
        # 验证按 epoch 倒序排列
        epochs = [项['epoch'] for 项 in 列表]
        assert epochs == sorted(epochs, reverse=True), "应按 epoch 倒序排列"
    
    def test_元数据保存(self):
        """测试: 元数据应正确保存"""
        管理器 = 检查点管理器(self.临时目录)
        模型 = 模拟模型({'w': [1.0]})
        
        管理器.保存检查点(
            模型=模型,
            优化器状态={},
            当前epoch=10,
            当前batch=500,
            loss值=0.123
        )
        
        列表 = 管理器.列出检查点()
        assert len(列表) == 1
        
        检查点 = 列表[0]
        assert 检查点['epoch'] == 10
        assert 检查点['batch'] == 500
        assert abs(检查点['loss'] - 0.123) < 1e-6
        assert '创建时间' in 检查点
        assert '文件大小' in 检查点
    
    def test_按epoch加载检查点(self):
        """测试: 按 epoch 编号加载特定检查点"""
        管理器 = 检查点管理器(self.临时目录, 最大检查点数=10)
        模型 = 模拟模型({'w': [1.0]})
        
        # 保存多个不同 epoch 的检查点
        for epoch in [1, 2, 3, 5, 8]:
            管理器.保存检查点(
                模型=模型,
                优化器状态={'lr': 0.001},
                当前epoch=epoch,
                当前batch=100,
                loss值=1.0 / epoch
            )
        
        # 按 epoch 加载
        数据 = 管理器.加载检查点(epoch=3)
        assert 数据 is not None, "应能按 epoch 加载检查点"
        assert 数据['训练进度']['当前epoch'] == 3, "应加载正确的 epoch"
        
        # 加载不存在的 epoch
        数据 = 管理器.加载检查点(epoch=99)
        assert 数据 is None, "不存在的 epoch 应返回 None"
    
    def test_按epoch加载同epoch多batch(self):
        """测试: 同一 epoch 有多个 batch 时，应加载最新的 batch"""
        管理器 = 检查点管理器(self.临时目录, 最大检查点数=10)
        模型 = 模拟模型({'w': [1.0]})
        
        # 保存同一 epoch 的多个 batch
        for batch in [100, 200, 300]:
            管理器.保存检查点(
                模型=模型,
                优化器状态={'lr': 0.001},
                当前epoch=5,
                当前batch=batch,
                loss值=0.5
            )
        
        # 按 epoch 加载，应返回最大 batch 的检查点
        数据 = 管理器.加载检查点(epoch=5)
        assert 数据 is not None, "应能按 epoch 加载检查点"
        assert 数据['训练进度']['当前epoch'] == 5
        assert 数据['训练进度']['当前batch'] == 300, "应加载最新的 batch"
    
    def test_按时间戳加载检查点(self):
        """测试: 按时间戳加载最接近的检查点"""
        import time
        from datetime import datetime
        
        管理器 = 检查点管理器(self.临时目录, 最大检查点数=10)
        模型 = 模拟模型({'w': [1.0]})
        
        # 保存第一个检查点
        管理器.保存检查点(
            模型=模型,
            优化器状态={'lr': 0.001},
            当前epoch=1,
            当前batch=0,
            loss值=1.0
        )
        
        # 记录中间时间
        time.sleep(0.1)
        中间时间 = datetime.now().isoformat()
        time.sleep(0.1)
        
        # 保存第二个检查点
        管理器.保存检查点(
            模型=模型,
            优化器状态={'lr': 0.001},
            当前epoch=2,
            当前batch=0,
            loss值=0.5
        )
        
        # 按中间时间加载，应返回最接近的检查点
        数据 = 管理器.加载检查点(时间戳=中间时间)
        assert 数据 is not None, "应能按时间戳加载检查点"
        # 由于时间接近，可能返回 epoch 1 或 2，只要能加载成功即可
        assert 数据['训练进度']['当前epoch'] in [1, 2]
    
    def test_无效时间戳格式(self):
        """测试: 无效的时间戳格式应返回 None"""
        管理器 = 检查点管理器(self.临时目录)
        模型 = 模拟模型({'w': [1.0]})
        
        管理器.保存检查点(
            模型=模型,
            优化器状态={},
            当前epoch=1,
            当前batch=0,
            loss值=1.0
        )
        
        # 使用无效的时间戳格式
        数据 = 管理器.加载检查点(时间戳="invalid-timestamp")
        assert 数据 is None, "无效时间戳应返回 None"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])
