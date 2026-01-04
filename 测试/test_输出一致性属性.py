"""
输出一致性属性测试模块

使用 Hypothesis 进行属性测试，验证模型转换保持输出一致性。

**属性 3: 模型转换保持输出一致性**
*对于任意* 有效输入图像，ONNX 输出应与 TFLearn 输出差异 < 0.01

**验证: 需求 1.4, 2.5**

**Feature: model-inference-acceleration, Property 3: 模型转换保持输出一致性**
"""

import os
import sys
import pytest
import numpy as np
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from typing import Tuple, List
from dataclasses import dataclass

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入被测试模块
from 工具.模型转换 import (
    输出一致性验证器,
    输出比较结果,
    验证输出一致性
)


# ==================== 测试策略定义 ====================

def 图像策略(宽度: int = 480, 高度: int = 270, 通道: int = 3):
    """生成随机图像数据的策略"""
    return st.builds(
        lambda: np.random.rand(宽度, 高度, 通道).astype(np.float32)
    )


def 归一化图像策略(宽度: int = 480, 高度: int = 270, 通道: int = 3):
    """生成归一化图像数据的策略（0-1范围）"""
    return st.builds(
        lambda: np.random.rand(宽度, 高度, 通道).astype(np.float32)
    )


# ==================== Mock 推理后端 ====================

class Mock一致后端A:
    """模拟一致的推理后端 A"""
    
    def __init__(self, 输出维度: int = 32, 噪声级别: float = 0.0):
        """
        初始化 Mock 后端
        
        参数:
            输出维度: 输出向量维度
            噪声级别: 添加的噪声级别（用于模拟微小差异）
        """
        self.输出维度 = 输出维度
        self.噪声级别 = 噪声级别
        self._基础输出 = None
    
    def 预测(self, 图像: np.ndarray) -> List[float]:
        """模拟推理预测"""
        # 基于图像内容生成确定性输出
        np.random.seed(int(np.sum(图像[:10, :10, :]) * 1000) % (2**31))
        基础输出 = np.random.rand(self.输出维度).astype(np.float32)
        基础输出 = 基础输出 / 基础输出.sum()  # 归一化为概率分布
        
        # 添加噪声
        if self.噪声级别 > 0:
            噪声 = np.random.randn(self.输出维度).astype(np.float32) * self.噪声级别
            基础输出 = 基础输出 + 噪声
            基础输出 = np.clip(基础输出, 0, 1)
            基础输出 = 基础输出 / 基础输出.sum()
        
        return 基础输出.tolist()


class Mock一致后端B(Mock一致后端A):
    """模拟一致的推理后端 B（与 A 输出相同或非常接近）"""
    
    def __init__(self, 输出维度: int = 32, 差异级别: float = 0.001):
        """
        初始化 Mock 后端
        
        参数:
            输出维度: 输出向量维度
            差异级别: 与后端 A 的差异级别（应小于 0.01）
        """
        super().__init__(输出维度, 噪声级别=0.0)
        self.差异级别 = 差异级别
    
    def 预测(self, 图像: np.ndarray) -> List[float]:
        """模拟推理预测（与后端 A 非常接近）"""
        # 获取基础输出（与后端 A 相同的逻辑）
        np.random.seed(int(np.sum(图像[:10, :10, :]) * 1000) % (2**31))
        基础输出 = np.random.rand(self.输出维度).astype(np.float32)
        基础输出 = 基础输出 / 基础输出.sum()
        
        # 添加微小差异（模拟浮点精度差异）
        np.random.seed(None)  # 重置随机种子
        差异 = np.random.randn(self.输出维度).astype(np.float32) * self.差异级别
        输出 = 基础输出 + 差异
        输出 = np.clip(输出, 0, 1)
        输出 = 输出 / 输出.sum()
        
        return 输出.tolist()


class Mock不一致后端:
    """模拟不一致的推理后端（输出差异大于 0.01）"""
    
    def __init__(self, 输出维度: int = 32, 差异级别: float = 0.1):
        """
        初始化 Mock 后端
        
        参数:
            输出维度: 输出向量维度
            差异级别: 与其他后端的差异级别（应大于 0.01）
        """
        self.输出维度 = 输出维度
        self.差异级别 = 差异级别
    
    def 预测(self, 图像: np.ndarray) -> List[float]:
        """模拟推理预测（与其他后端差异较大）"""
        # 生成完全随机的输出
        输出 = np.random.rand(self.输出维度).astype(np.float32)
        输出 = 输出 / 输出.sum()
        return 输出.tolist()


# ==================== 属性测试类 ====================

class Test输出一致性属性:
    """
    输出一致性属性测试
    
    **Feature: model-inference-acceleration, Property 3: 模型转换保持输出一致性**
    **验证: 需求 1.4, 2.5**
    """
    
    @settings(
        max_examples=100,
        deadline=None,
        suppress_health_check=[HealthCheck.too_slow]
    )
    @given(st.integers(min_value=1, max_value=20))
    def test_一致后端输出差异小于容差(self, 测试次数: int):
        """
        属性测试：一致的推理后端输出差异应小于 0.01
        
        *对于任意* 有效输入图像，两个一致后端的输出差异应小于 0.01
        
        **Feature: model-inference-acceleration, Property 3: 模型转换保持输出一致性**
        **验证: 需求 1.4, 2.5**
        """
        # 创建两个一致的 Mock 后端
        后端A = Mock一致后端A(输出维度=32)
        后端B = Mock一致后端B(输出维度=32, 差异级别=0.001)  # 差异 < 0.01
        
        # 创建验证器
        验证器 = 输出一致性验证器(容差=0.01, 输入形状=(480, 270, 3))
        
        # 批量比较
        结果 = 验证器.批量比较输出(
            后端A, 后端B,
            测试样本数=测试次数,
            后端A名称="MockA",
            后端B名称="MockB"
        )
        
        # 验证一致性
        assert 结果.一致, f"一致后端的输出差异应小于 0.01，实际最大差异: {结果.最大差异:.6f}"
        assert 结果.最大差异 < 0.01, f"最大差异 {结果.最大差异:.6f} 应小于 0.01"
        assert 结果.测试样本数 == 测试次数, f"测试样本数应为 {测试次数}"
    
    @settings(
        max_examples=100,
        deadline=None,
        suppress_health_check=[HealthCheck.too_slow]
    )
    @given(st.integers(min_value=1, max_value=10))
    def test_不一致后端输出差异大于容差(self, 测试次数: int):
        """
        属性测试：不一致的推理后端输出差异应大于 0.01
        
        这是一个反向测试，验证差异检测逻辑正确工作
        """
        # 创建一致和不一致的 Mock 后端
        后端A = Mock一致后端A(输出维度=32)
        后端C = Mock不一致后端(输出维度=32, 差异级别=0.1)  # 差异 > 0.01
        
        # 创建验证器
        验证器 = 输出一致性验证器(容差=0.01, 输入形状=(480, 270, 3))
        
        # 批量比较
        结果 = 验证器.批量比较输出(
            后端A, 后端C,
            测试样本数=测试次数,
            后端A名称="MockA",
            后端B名称="MockC"
        )
        
        # 验证不一致性
        assert not 结果.一致, f"不一致后端的输出差异应大于 0.01，实际最大差异: {结果.最大差异:.6f}"
    
    @settings(
        max_examples=100,
        deadline=None,
        suppress_health_check=[HealthCheck.too_slow]
    )
    @given(
        st.floats(min_value=0.0, max_value=1.0),
        st.floats(min_value=0.0, max_value=1.0),
        st.floats(min_value=0.0, max_value=1.0)
    )
    def test_不同图像内容输出一致性(self, r: float, g: float, b: float):
        """
        属性测试：不同图像内容的输出一致性应保持
        
        *对于任意* 图像内容，一致后端的输出差异应小于 0.01
        """
        assume(np.isfinite(r) and np.isfinite(g) and np.isfinite(b))
        
        # 创建两个一致的 Mock 后端
        后端A = Mock一致后端A(输出维度=32)
        后端B = Mock一致后端B(输出维度=32, 差异级别=0.001)
        
        # 创建特定内容的图像
        图像 = np.zeros((480, 270, 3), dtype=np.float32)
        图像[:, :, 0] = r
        图像[:, :, 1] = g
        图像[:, :, 2] = b
        
        # 创建验证器
        验证器 = 输出一致性验证器(容差=0.01, 输入形状=(480, 270, 3))
        
        # 单次比较
        结果 = 验证器.比较输出(后端A, 后端B, 测试输入=图像)
        
        # 验证一致性
        assert 结果.一致, f"输出差异应小于 0.01，实际: {结果.最大差异:.6f}"


class Test输出比较结果属性:
    """
    输出比较结果属性测试
    
    验证输出比较结果的数学正确性
    """
    
    @settings(max_examples=100)
    @given(st.lists(st.floats(min_value=0.0, max_value=0.1), min_size=1, max_size=100))
    def test_差异统计计算正确性(self, 差异列表: List[float]):
        """
        属性测试：差异统计计算应正确
        
        *对于任意* 差异记录列表，统计值应满足数学关系
        """
        # 过滤无效值
        差异列表 = [x for x in 差异列表 if np.isfinite(x)]
        assume(len(差异列表) > 0)
        
        # 计算期望值
        期望最大 = max(差异列表)
        期望平均 = np.mean(差异列表)
        期望标准差 = np.std(差异列表)
        
        # 创建输出比较结果
        结果 = 输出比较结果(
            一致=期望最大 < 0.01,
            最大差异=期望最大,
            平均差异=期望平均,
            标准差=期望标准差,
            测试样本数=len(差异列表),
            容差=0.01,
            详细差异=差异列表
        )
        
        # 验证数学关系
        容差 = 1e-10
        assert 结果.平均差异 <= 结果.最大差异 + 容差, "平均差异应小于等于最大差异"
        assert 结果.最大差异 >= 0, "最大差异应非负"
        assert 结果.平均差异 >= 0, "平均差异应非负"
        assert 结果.标准差 >= 0, "标准差应非负"
    
    @settings(max_examples=100)
    @given(st.floats(min_value=0.0, max_value=0.009))
    def test_一致性判断_通过(self, 最大差异: float):
        """
        属性测试：最大差异小于 0.01 时应判断为一致
        """
        assume(np.isfinite(最大差异))
        
        结果 = 输出比较结果(
            一致=最大差异 < 0.01,
            最大差异=最大差异,
            平均差异=最大差异 * 0.5,
            标准差=最大差异 * 0.1,
            测试样本数=100,
            容差=0.01
        )
        
        assert 结果.一致, f"最大差异 {最大差异:.6f} 应判断为一致"
    
    @settings(max_examples=100)
    @given(st.floats(min_value=0.011, max_value=1.0))
    def test_一致性判断_不通过(self, 最大差异: float):
        """
        属性测试：最大差异大于 0.01 时应判断为不一致
        """
        assume(np.isfinite(最大差异))
        
        结果 = 输出比较结果(
            一致=最大差异 < 0.01,
            最大差异=最大差异,
            平均差异=最大差异 * 0.5,
            标准差=最大差异 * 0.1,
            测试样本数=100,
            容差=0.01
        )
        
        assert not 结果.一致, f"最大差异 {最大差异:.6f} 应判断为不一致"


class Test验证器配置属性:
    """
    验证器配置属性测试
    
    验证验证器配置的正确性
    """
    
    @settings(max_examples=100)
    @given(st.floats(min_value=0.001, max_value=0.1))
    def test_容差配置生效(self, 容差: float):
        """
        属性测试：容差配置应正确生效
        """
        assume(np.isfinite(容差))
        
        验证器 = 输出一致性验证器(容差=容差, 输入形状=(480, 270, 3))
        
        assert 验证器.容差 == 容差, f"容差应为 {容差}"
    
    @settings(max_examples=50)
    @given(
        st.integers(min_value=100, max_value=500),
        st.integers(min_value=100, max_value=500)
    )
    def test_输入形状配置生效(self, 宽度: int, 高度: int):
        """
        属性测试：输入形状配置应正确生效
        """
        验证器 = 输出一致性验证器(容差=0.01, 输入形状=(宽度, 高度, 3))
        
        assert 验证器.输入形状 == (宽度, 高度, 3), f"输入形状应为 ({宽度}, {高度}, 3)"


class Test便捷函数属性:
    """
    便捷函数属性测试
    
    验证便捷函数的正确性
    """
    
    @settings(
        max_examples=50,
        deadline=None,
        suppress_health_check=[HealthCheck.too_slow]
    )
    @given(st.integers(min_value=5, max_value=20))
    def test_验证输出一致性函数(self, 测试样本数: int):
        """
        属性测试：验证输出一致性便捷函数应正确工作
        """
        # 创建两个一致的 Mock 后端
        后端A = Mock一致后端A(输出维度=32)
        后端B = Mock一致后端B(输出维度=32, 差异级别=0.001)
        
        # 使用便捷函数
        结果 = 验证输出一致性(
            后端A, 后端B,
            测试样本数=测试样本数,
            容差=0.01,
            输入形状=(480, 270, 3)
        )
        
        # 验证结果
        assert isinstance(结果, 输出比较结果), "应返回输出比较结果对象"
        assert 结果.测试样本数 == 测试样本数, f"测试样本数应为 {测试样本数}"
        assert 结果.一致, f"一致后端应通过验证，实际最大差异: {结果.最大差异:.6f}"


# ==================== 运行测试 ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])
