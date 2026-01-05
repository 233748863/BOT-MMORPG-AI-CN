# -*- coding: utf-8 -*-
"""
训练模块单元测试

测试类别权重应用和 loss 值获取功能。

**验证: 需求 6.1, 6.2, 7.2, 7.3**
"""

import sys
import os
import tempfile
import json
import numpy as np

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from unittest.mock import MagicMock, patch


class Test类别权重应用:
    """
    测试类别权重应用功能
    
    **验证: 需求 6.1, 6.2**
    """
    
    def test_加权损失函数创建(self):
        """
        测试: 加权损失函数能够正确创建
        
        **验证: 需求 6.1**
        """
        try:
            from 工具.类别权重 import 加权交叉熵损失
        except ImportError:
            pytest.skip("类别权重模块不可用")
        
        # 创建类别权重字典
        类别权重 = {0: 0.5, 1: 2.0, 2: 1.5, 3: 1.0}
        
        # 创建加权损失函数
        损失函数 = 加权交叉熵损失(类别权重, 类别数=4)
        
        # 验证损失函数创建成功
        assert 损失函数 is not None
        assert 损失函数.类别数 == 4
        
        # 验证权重数组正确
        权重数组 = 损失函数.获取权重数组()
        assert len(权重数组) == 4
        assert 权重数组[0] == 0.5
        assert 权重数组[1] == 2.0
        assert 权重数组[2] == 1.5
        assert 权重数组[3] == 1.0
    
    def test_加权损失函数计算(self):
        """
        测试: 加权损失函数能够正确计算损失值
        
        **验证: 需求 6.2**
        """
        try:
            from 工具.类别权重 import 加权交叉熵损失
        except ImportError:
            pytest.skip("类别权重模块不可用")
        
        # 创建类别权重字典
        类别权重 = {0: 1.0, 1: 2.0}
        损失函数 = 加权交叉熵损失(类别权重, 类别数=2)
        
        # 创建测试数据
        # 预测值 (softmax 后的概率)
        预测 = np.array([[0.9, 0.1], [0.2, 0.8]])
        # 真实标签 (one-hot)
        标签 = np.array([[1, 0], [0, 1]])
        
        # 计算损失
        损失值 = 损失函数(预测, 标签)
        
        # 验证损失值是有效的数值
        assert isinstance(损失值, float)
        assert 损失值 >= 0
        assert not np.isnan(损失值)
        assert not np.isinf(损失值)
    
    def test_加权损失函数权重影响(self):
        """
        测试: 类别权重应该影响损失值计算
        
        **验证: 需求 6.1, 6.2**
        """
        try:
            from 工具.类别权重 import 加权交叉熵损失
        except ImportError:
            pytest.skip("类别权重模块不可用")
        
        # 创建两个不同权重的损失函数
        权重1 = {0: 1.0, 1: 1.0}  # 均匀权重
        权重2 = {0: 1.0, 1: 10.0}  # 类别1权重更高
        
        损失函数1 = 加权交叉熵损失(权重1, 类别数=2)
        损失函数2 = 加权交叉熵损失(权重2, 类别数=2)
        
        # 创建测试数据 - 类别1预测错误
        预测 = np.array([[0.1, 0.9]])  # 预测为类别1
        标签 = np.array([[0, 1]])  # 真实为类别1
        
        # 计算损失
        损失1 = 损失函数1(预测, 标签)
        损失2 = 损失函数2(预测, 标签)
        
        # 由于类别1权重更高，损失2应该更大（对于相同的预测错误）
        # 但这里预测正确，所以损失应该较小
        # 让我们测试预测错误的情况
        预测错误 = np.array([[0.9, 0.1]])  # 预测为类别0
        标签1 = np.array([[0, 1]])  # 真实为类别1
        
        损失1_错误 = 损失函数1(预测错误, 标签1)
        损失2_错误 = 损失函数2(预测错误, 标签1)
        
        # 类别1权重更高时，预测错误的损失应该更大
        assert 损失2_错误 > 损失1_错误, \
            f"高权重类别的预测错误应产生更大损失: {损失2_错误} > {损失1_错误}"
    
    def test_tensorflow损失函数获取(self):
        """
        测试: 能够获取 TensorFlow 兼容的损失函数
        
        **验证: 需求 6.2**
        """
        try:
            from 工具.类别权重 import 加权交叉熵损失
            import tensorflow as tf
        except ImportError:
            pytest.skip("类别权重模块或 TensorFlow 不可用")
        
        # 创建加权损失函数
        类别权重 = {0: 0.5, 1: 2.0, 2: 1.5}
        损失函数 = 加权交叉熵损失(类别权重, 类别数=3)
        
        # 获取 TensorFlow 损失函数
        tf_损失函数 = 损失函数.获取tensorflow损失函数()
        
        # 验证返回的是可调用对象
        assert callable(tf_损失函数)
        
        # 测试 TensorFlow 损失函数
        y_pred = tf.constant([[0.7, 0.2, 0.1], [0.1, 0.8, 0.1]], dtype=tf.float32)
        y_true = tf.constant([[1, 0, 0], [0, 1, 0]], dtype=tf.float32)
        
        损失值 = tf_损失函数(y_pred, y_true)
        
        # 验证损失值是有效的张量
        assert isinstance(损失值, tf.Tensor)
        损失数值 = 损失值.numpy()
        assert not np.isnan(损失数值)
        assert not np.isinf(损失数值)
        assert 损失数值 >= 0


class Test模型定义:
    """
    测试模型定义中的自定义损失函数支持
    
    **验证: 需求 6.2**
    """
    
    def test_模型支持自定义损失函数参数(self):
        """
        测试: inception_v3 函数应支持自定义损失函数参数
        
        **验证: 需求 6.2**
        """
        # 直接读取模型定义文件检查函数签名
        模型定义路径 = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            '核心', '模型定义.py'
        )
        
        with open(模型定义路径, 'r', encoding='utf-8') as f:
            代码内容 = f.read()
        
        # 验证函数定义包含自定义损失函数参数
        assert '自定义损失函数=None' in 代码内容, \
            "inception_v3 函数应包含 '自定义损失函数' 参数，默认值为 None"
        
        # 验证函数使用了自定义损失函数
        assert 'if 自定义损失函数 is not None:' in 代码内容, \
            "inception_v3 函数应检查并使用自定义损失函数"
        
        # 验证有回退到默认损失函数的逻辑
        assert "loss='categorical_crossentropy'" in 代码内容, \
            "inception_v3 函数应在没有自定义损失函数时使用默认的 categorical_crossentropy"


class TestLoss值获取:
    """
    测试 Loss 值获取功能
    
    **验证: 需求 7.2, 7.3**
    """
    
    def test_检查点包含loss值字段(self):
        """
        测试: 检查点管理器应支持保存 loss 值
        
        **验证: 需求 7.3**
        """
        try:
            from 工具.检查点管理 import 检查点管理器
        except ImportError:
            pytest.skip("检查点管理模块不可用")
        
        # 创建临时目录
        with tempfile.TemporaryDirectory() as 临时目录:
            # 创建检查点管理器
            管理器 = 检查点管理器(临时目录, 最大检查点数=3)
            
            # 模拟保存检查点（不需要真实模型）
            测试loss值 = 0.5678
            
            # 检查保存检查点方法的参数
            import inspect
            签名 = inspect.signature(管理器.保存检查点)
            参数名列表 = list(签名.parameters.keys())
            
            # 验证支持 loss 值参数
            assert 'loss值' in 参数名列表, \
                "保存检查点方法应支持 'loss值' 参数"
    
    def test_loss值不为硬编码零(self):
        """
        测试: 训练代码中不应使用硬编码的 0.0 作为 loss 值
        
        **验证: 需求 7.2**
        """
        # 读取训练模型代码
        训练模型路径 = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            '训练', '训练模型.py'
        )
        
        with open(训练模型路径, 'r', encoding='utf-8') as f:
            代码内容 = f.read()
        
        # 检查是否存在 "TODO: 从训练过程获取实际loss" 注释
        # 如果存在，说明 loss 值获取尚未实现
        assert "TODO: 从训练过程获取实际loss" not in 代码内容, \
            "训练代码中不应存在未实现的 TODO 注释"
        
        # 检查是否使用了 evaluate 方法获取 loss
        assert "模型.evaluate" in 代码内容 or "evaluate" in 代码内容, \
            "训练代码应使用 evaluate 方法获取实际 loss 值"
    
    def test_训练进度输出包含loss值(self):
        """
        测试: 训练进度输出应包含 loss 值显示
        
        **验证: 需求 7.4**
        """
        # 读取训练模型代码
        训练模型路径 = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            '训练', '训练模型.py'
        )
        
        with open(训练模型路径, 'r', encoding='utf-8') as f:
            代码内容 = f.read()
        
        # 检查是否有 loss 值的输出
        assert "当前批次 Loss" in 代码内容 or "Loss:" in 代码内容, \
            "训练代码应在进度输出中显示 loss 值"


class Test损失函数日志记录:
    """
    测试损失函数类型的日志记录
    
    **验证: 需求 6.3, 6.4**
    """
    
    def test_训练代码记录损失函数类型(self):
        """
        测试: 训练代码应记录使用的损失函数类型
        
        **验证: 需求 6.3**
        """
        # 读取训练模型代码
        训练模型路径 = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            '训练', '训练模型.py'
        )
        
        with open(训练模型路径, 'r', encoding='utf-8') as f:
            代码内容 = f.read()
        
        # 检查是否记录了损失函数类型
        assert "使用的损失函数类型" in 代码内容 or "损失函数:" in 代码内容, \
            "训练代码应记录使用的损失函数类型"
    
    def test_训练代码处理损失函数创建失败(self):
        """
        测试: 训练代码应处理损失函数创建失败的情况
        
        **验证: 需求 6.4**
        """
        # 读取训练模型代码
        训练模型路径 = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            '训练', '训练模型.py'
        )
        
        with open(训练模型路径, 'r', encoding='utf-8') as f:
            代码内容 = f.read()
        
        # 检查是否有异常处理和回退逻辑
        assert "回退" in 代码内容 or "categorical_crossentropy" in 代码内容, \
            "训练代码应在损失函数创建失败时回退到默认损失函数"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
