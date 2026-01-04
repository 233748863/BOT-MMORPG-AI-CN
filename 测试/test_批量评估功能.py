"""
批量评估功能测试
测试任务 4.1 和 4.2 的实现
"""

import numpy as np
import time
import os
import tempfile
import pytest


class 模拟模型:
    """模拟模型用于测试"""
    def __init__(self, 类别数=5):
        self.类别数 = 类别数
    
    def predict(self, x):
        time.sleep(0.001)  # 模拟推理延迟
        batch_size = x.shape[0]
        return np.random.rand(batch_size, self.类别数)


class Test测试数据加载器:
    """测试数据加载器测试类"""
    
    def test_初始化(self):
        """测试加载器初始化"""
        from 工具.模型评估 import 测试数据加载器
        
        loader = 测试数据加载器()
        assert loader.数据目录 == "数据/"
        assert '.npy' in loader.支持格式
        assert '.npz' in loader.支持格式
        assert '.json' in loader.支持格式
        assert '.pkl' in loader.支持格式
    
    def test_加载npy文件(self):
        """测试加载 .npy 格式文件"""
        from 工具.模型评估 import 测试数据加载器
        
        # 创建临时测试数据
        临时目录 = tempfile.mkdtemp()
        测试文件 = os.path.join(临时目录, '测试数据.npy')
        
        try:
            # 创建测试数据（模拟收集的数据格式）
            测试数据 = []
            for i in range(20):
                图像 = np.random.rand(50, 50, 3).astype(np.float32)
                动作 = [0] * 5
                动作[i % 5] = 1
                测试数据.append([图像, 动作])
            
            # 使用 allow_pickle 保存对象数组
            np.save(测试文件, np.array(测试数据, dtype=object))
            
            # 加载数据
            loader = 测试数据加载器()
            加载的数据 = loader.加载测试数据(测试文件)
            
            assert len(加载的数据) == 20
            assert all(isinstance(item, tuple) for item in 加载的数据)
            assert all(len(item) == 2 for item in 加载的数据)
            
            # 验证标签转换正确
            for i, (图像, 标签) in enumerate(加载的数据):
                assert isinstance(标签, int)
                assert 0 <= 标签 < 5
        finally:
            os.remove(测试文件)
            os.rmdir(临时目录)
    
    def test_获取数据统计(self):
        """测试获取数据统计信息"""
        from 工具.模型评估 import 测试数据加载器
        
        loader = 测试数据加载器()
        
        # 创建测试数据
        测试数据 = [(np.zeros((100, 100, 3)), i % 5) for i in range(100)]
        
        统计 = loader.获取数据统计(测试数据)
        
        assert 统计['总样本数'] == 100
        assert 统计['类别数'] == 5
        assert sum(统计['类别分布'].values()) == 100
        assert 统计['最大类别样本数'] == 20
        assert 统计['最小类别样本数'] == 20
    
    def test_空数据统计(self):
        """测试空数据的统计"""
        from 工具.模型评估 import 测试数据加载器
        
        loader = 测试数据加载器()
        统计 = loader.获取数据统计([])
        
        assert 统计['总样本数'] == 0
        assert 统计['类别分布'] == {}
    
    def test_最大样本数限制(self):
        """测试最大样本数限制"""
        from 工具.模型评估 import 测试数据加载器
        
        # 创建临时测试数据
        临时目录 = tempfile.mkdtemp()
        测试文件 = os.path.join(临时目录, '测试数据.npy')
        
        try:
            # 创建50个样本
            测试数据 = []
            for i in range(50):
                图像 = np.random.rand(50, 50, 3).astype(np.float32)
                动作 = [0] * 5
                动作[i % 5] = 1
                测试数据.append([图像, 动作])
            
            np.save(测试文件, np.array(测试数据, dtype=object))
            
            # 限制加载10个样本
            loader = 测试数据加载器()
            加载的数据 = loader.加载测试数据(测试文件, 最大样本数=10)
            
            assert len(加载的数据) == 10
        finally:
            os.remove(测试文件)
            os.rmdir(临时目录)


class Test批量评估器:
    """批量评估器测试类"""
    
    def test_初始化(self):
        """测试批量评估器初始化"""
        from 工具.模型评估 import 批量评估器
        
        动作定义 = {i: f'动作{i}' for i in range(5)}
        evaluator = 批量评估器(动作定义=动作定义)
        
        assert evaluator.动作定义 == 动作定义
        assert evaluator.数据加载器 is not None
        assert evaluator.评估器 is not None
    
    def test_设置模型(self):
        """测试设置模型"""
        from 工具.模型评估 import 批量评估器
        
        evaluator = 批量评估器()
        模型 = 模拟模型()
        
        evaluator.设置模型(模型)
        assert evaluator.模型 == 模型
    
    def test_批量评估(self):
        """测试批量评估功能"""
        from 工具.模型评估 import 批量评估器, 测试数据加载器
        
        # 创建临时测试数据
        临时目录 = tempfile.mkdtemp()
        测试文件 = os.path.join(临时目录, '测试数据.npy')
        
        try:
            # 创建测试数据
            测试数据 = []
            for i in range(30):
                图像 = np.random.rand(50, 50, 3).astype(np.float32)
                动作 = [0] * 5
                动作[i % 5] = 1
                测试数据.append([图像, 动作])
            
            np.save(测试文件, np.array(测试数据, dtype=object))
            
            # 创建评估器
            模型 = 模拟模型(类别数=5)
            动作定义 = {i: f'动作{i}' for i in range(5)}
            evaluator = 批量评估器(模型, 动作定义)
            
            # 执行批量评估
            结果 = evaluator.批量评估(测试文件, 测试比例=1.0, 显示进度=False)
            
            assert 结果.样本数量 == 30
            assert 结果.评估时间 > 0
            assert 0 <= 结果.总体准确率 <= 1
            assert len(结果.类别指标) == 5
        finally:
            os.remove(测试文件)
            os.rmdir(临时目录)
    
    def test_吞吐量计算(self):
        """测试吞吐量计算"""
        from 工具.模型评估 import 批量评估器
        
        # 创建临时测试数据
        临时目录 = tempfile.mkdtemp()
        测试文件 = os.path.join(临时目录, '测试数据.npy')
        
        try:
            # 创建测试数据
            测试数据 = []
            for i in range(20):
                图像 = np.random.rand(50, 50, 3).astype(np.float32)
                动作 = [0] * 5
                动作[i % 5] = 1
                测试数据.append([图像, 动作])
            
            np.save(测试文件, np.array(测试数据, dtype=object))
            
            # 创建评估器
            模型 = 模拟模型(类别数=5)
            动作定义 = {i: f'动作{i}' for i in range(5)}
            evaluator = 批量评估器(模型, 动作定义)
            
            # 执行批量评估
            结果 = evaluator.批量评估(测试文件, 测试比例=1.0, 显示进度=False)
            
            # 验证吞吐量
            吞吐量 = 结果.样本数量 / 结果.评估时间 if 结果.评估时间 > 0 else 0
            assert 吞吐量 > 0
            print(f"吞吐量: {吞吐量:.1f} 样本/秒")
        finally:
            os.remove(测试文件)
            os.rmdir(临时目录)


class Test便捷函数:
    """便捷函数测试类"""
    
    def test_快速评估(self):
        """测试快速评估函数"""
        from 工具.模型评估 import 快速评估
        
        模型 = 模拟模型(类别数=5)
        动作定义 = {i: f'动作{i}' for i in range(5)}
        
        # 创建测试数据
        测试数据 = [(np.random.rand(50, 50, 3).astype(np.float32), i % 5) for i in range(20)]
        
        结果 = 快速评估(模型, 测试数据, 动作定义)
        
        assert 结果.样本数量 == 20
        assert 0 <= 结果.总体准确率 <= 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
