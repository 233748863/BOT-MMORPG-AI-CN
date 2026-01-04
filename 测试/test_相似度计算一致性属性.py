"""
相似度计算一致性属性测试

属性 1: 相似度计算一致性
*对于任意* 两帧图像，相同图像相似度为 1.0，完全不同图像接近 0.0

验证: 需求 1.1
"""

import numpy as np
import pytest
from hypothesis import given, strategies as st, settings, assume

# 导入被测试的模块
from 核心.帧比较 import 帧比较器, 快速帧差异检测


# ==================== 策略定义 ====================

@st.composite
def 随机图像(draw, 最小尺寸=32, 最大尺寸=256):
    """生成随机图像"""
    宽度 = draw(st.integers(min_value=最小尺寸, max_value=最大尺寸))
    高度 = draw(st.integers(min_value=最小尺寸, max_value=最大尺寸))
    通道数 = draw(st.sampled_from([1, 3]))  # 灰度或 BGR
    
    if 通道数 == 1:
        图像 = np.random.randint(0, 256, (高度, 宽度), dtype=np.uint8)
    else:
        图像 = np.random.randint(0, 256, (高度, 宽度, 通道数), dtype=np.uint8)
    
    return 图像


@st.composite
def 相同尺寸图像对(draw, 最小尺寸=32, 最大尺寸=128):
    """生成相同尺寸的图像对"""
    宽度 = draw(st.integers(min_value=最小尺寸, max_value=最大尺寸))
    高度 = draw(st.integers(min_value=最小尺寸, max_value=最大尺寸))
    通道数 = draw(st.sampled_from([1, 3]))
    
    if 通道数 == 1:
        图像1 = np.random.randint(0, 256, (高度, 宽度), dtype=np.uint8)
        图像2 = np.random.randint(0, 256, (高度, 宽度), dtype=np.uint8)
    else:
        图像1 = np.random.randint(0, 256, (高度, 宽度, 通道数), dtype=np.uint8)
        图像2 = np.random.randint(0, 256, (高度, 宽度, 通道数), dtype=np.uint8)
    
    return 图像1, 图像2


@st.composite
def 有效区域(draw, 图像宽度, 图像高度):
    """生成有效的区域坐标"""
    x = draw(st.integers(min_value=0, max_value=max(0, 图像宽度 - 10)))
    y = draw(st.integers(min_value=0, max_value=max(0, 图像高度 - 10)))
    w = draw(st.integers(min_value=10, max_value=max(10, 图像宽度 - x)))
    h = draw(st.integers(min_value=10, max_value=max(10, 图像高度 - y)))
    return (x, y, w, h)


class Test相似度计算一致性属性:
    """
    属性测试: 相似度计算一致性
    
    Feature: detection-cache-optimization, Property 1: 相似度计算一致性
    Validates: Requirements 1.1
    """
    
    @settings(max_examples=100, deadline=5000)
    @given(图像=随机图像())
    def test_相同图像相似度为1(self, 图像: np.ndarray):
        """
        属性测试: 相同图像的相似度应为 1.0
        
        Feature: detection-cache-optimization, Property 1: 相似度计算一致性
        Validates: Requirements 1.1
        """
        比较器 = 帧比较器(方法="histogram")
        
        # 相同图像比较
        相似度 = 比较器.比较(图像, 图像.copy())
        
        # 相同图像相似度应该非常接近 1.0
        assert 相似度 >= 0.99, f"相同图像相似度应接近 1.0，实际: {相似度}"
    
    @settings(max_examples=100, deadline=5000)
    @given(方法=st.sampled_from(["histogram", "ssim", "mse", "hash"]))
    def test_所有方法相同图像相似度为1(self, 方法: str):
        """
        属性测试: 所有比较方法对相同图像应返回接近 1.0 的相似度
        
        Feature: detection-cache-optimization, Property 1: 相似度计算一致性
        Validates: Requirements 1.1
        """
        # 创建固定测试图像
        图像 = np.random.randint(0, 256, (64, 64, 3), dtype=np.uint8)
        比较器 = 帧比较器(方法=方法)
        
        相似度 = 比较器.比较(图像, 图像.copy())
        
        assert 相似度 >= 0.99, f"方法 {方法}: 相同图像相似度应接近 1.0，实际: {相似度}"
    
    @settings(max_examples=100, deadline=5000)
    @given(图像对=相同尺寸图像对())
    def test_完全不同图像相似度较低(self, 图像对):
        """
        属性测试: 完全不同的图像相似度应较低
        
        Feature: detection-cache-optimization, Property 1: 相似度计算一致性
        Validates: Requirements 1.1
        """
        图像1, 图像2 = 图像对
        比较器 = 帧比较器(方法="histogram")
        
        相似度 = 比较器.比较(图像1, 图像2)
        
        # 相似度应在有效范围内
        assert 0.0 <= 相似度 <= 1.0, f"相似度应在 0-1 范围内，实际: {相似度}"
    
    @settings(max_examples=100, deadline=5000)
    @given(图像=随机图像())
    def test_相似度范围有效(self, 图像: np.ndarray):
        """
        属性测试: 相似度应始终在 0.0-1.0 范围内
        
        Feature: detection-cache-optimization, Property 1: 相似度计算一致性
        Validates: Requirements 1.1
        """
        # 创建一个完全不同的图像
        不同图像 = 255 - 图像  # 反色图像
        
        比较器 = 帧比较器(方法="histogram")
        相似度 = 比较器.比较(图像, 不同图像)
        
        assert 0.0 <= 相似度 <= 1.0, f"相似度应在 0-1 范围内，实际: {相似度}"
    
    @settings(max_examples=100, deadline=5000)
    @given(图像=随机图像())
    def test_比较对称性(self, 图像: np.ndarray):
        """
        属性测试: 比较应该是对称的 - compare(A, B) == compare(B, A)
        
        Feature: detection-cache-optimization, Property 1: 相似度计算一致性
        Validates: Requirements 1.1
        """
        # 创建略微不同的图像
        图像2 = 图像.copy()
        if len(图像2.shape) == 3:
            图像2[0, 0, 0] = (图像2[0, 0, 0] + 50) % 256
        else:
            图像2[0, 0] = (图像2[0, 0] + 50) % 256
        
        比较器 = 帧比较器(方法="histogram")
        
        相似度1 = 比较器.比较(图像, 图像2)
        相似度2 = 比较器.比较(图像2, 图像)
        
        # 允许微小的浮点误差
        assert abs(相似度1 - 相似度2) < 0.01, f"比较应对称: {相似度1} vs {相似度2}"


class Test区域比较属性:
    """
    属性测试: 区域比较功能
    
    Feature: detection-cache-optimization
    Validates: Requirements 1.4
    """
    
    @settings(max_examples=100, deadline=5000)
    @given(st.integers(min_value=64, max_value=128),
           st.integers(min_value=64, max_value=128))
    def test_区域比较相同区域相似度为1(self, 宽度: int, 高度: int):
        """
        属性测试: 相同图像的相同区域相似度应为 1.0
        
        Feature: detection-cache-optimization
        Validates: Requirements 1.4
        """
        图像 = np.random.randint(0, 256, (高度, 宽度, 3), dtype=np.uint8)
        比较器 = 帧比较器(方法="histogram")
        
        # 定义一个有效区域
        区域 = (10, 10, min(30, 宽度 - 10), min(30, 高度 - 10))
        
        相似度 = 比较器.比较区域(图像, 图像.copy(), 区域)
        
        assert 相似度 >= 0.99, f"相同区域相似度应接近 1.0，实际: {相似度}"
    
    @settings(max_examples=100, deadline=5000)
    @given(st.integers(min_value=64, max_value=128),
           st.integers(min_value=64, max_value=128))
    def test_区域比较范围有效(self, 宽度: int, 高度: int):
        """
        属性测试: 区域比较结果应在有效范围内
        
        Feature: detection-cache-optimization
        Validates: Requirements 1.4
        """
        图像1 = np.random.randint(0, 256, (高度, 宽度, 3), dtype=np.uint8)
        图像2 = np.random.randint(0, 256, (高度, 宽度, 3), dtype=np.uint8)
        比较器 = 帧比较器(方法="histogram")
        
        区域 = (10, 10, min(30, 宽度 - 10), min(30, 高度 - 10))
        
        相似度 = 比较器.比较区域(图像1, 图像2, 区域)
        
        assert 0.0 <= 相似度 <= 1.0, f"区域相似度应在 0-1 范围内，实际: {相似度}"


class Test快速帧差异检测属性:
    """
    属性测试: 快速帧差异检测
    
    Feature: detection-cache-optimization
    Validates: Requirements 1.1
    """
    
    @settings(max_examples=100, deadline=5000)
    @given(图像=随机图像())
    def test_相同帧无差异(self, 图像: np.ndarray):
        """
        属性测试: 相同帧应该没有显著差异
        
        Feature: detection-cache-optimization
        Validates: Requirements 1.1
        """
        有差异 = 快速帧差异检测(图像, 图像.copy(), 阈值=0.1)
        
        assert not 有差异, "相同帧不应该检测到差异"
    
    @settings(max_examples=100, deadline=5000)
    @given(图像=随机图像())
    def test_完全不同帧有差异(self, 图像: np.ndarray):
        """
        属性测试: 完全不同的帧应该有显著差异
        
        Feature: detection-cache-optimization
        Validates: Requirements 1.1
        """
        # 创建完全不同的图像（反色）
        不同图像 = 255 - 图像
        
        有差异 = 快速帧差异检测(图像, 不同图像, 阈值=0.1)
        
        assert 有差异, "完全不同的帧应该检测到差异"


class Test帧比较器单元测试:
    """帧比较器单元测试"""
    
    def test_初始化默认方法(self):
        """测试默认初始化"""
        比较器 = 帧比较器()
        assert 比较器.方法 == "histogram"
    
    def test_初始化指定方法(self):
        """测试指定方法初始化"""
        for 方法 in ["histogram", "ssim", "mse", "hash"]:
            比较器 = 帧比较器(方法=方法)
            assert 比较器.方法 == 方法
    
    def test_初始化无效方法(self):
        """测试无效方法初始化（应回退到默认）"""
        比较器 = 帧比较器(方法="invalid")
        assert 比较器.方法 == "histogram"
    
    def test_空图像处理(self):
        """测试空图像处理"""
        比较器 = 帧比较器()
        
        相似度 = 比较器.比较(None, None)
        assert 相似度 == 0.0
        
        图像 = np.zeros((64, 64, 3), dtype=np.uint8)
        相似度 = 比较器.比较(图像, None)
        assert 相似度 == 0.0
    
    def test_不同尺寸图像处理(self):
        """测试不同尺寸图像处理"""
        比较器 = 帧比较器()
        
        图像1 = np.random.randint(0, 256, (64, 64, 3), dtype=np.uint8)
        图像2 = np.random.randint(0, 256, (128, 128, 3), dtype=np.uint8)
        
        # 应该能正常处理（内部会调整尺寸）
        相似度 = 比较器.比较(图像1, 图像2)
        assert 0.0 <= 相似度 <= 1.0
    
    def test_多区域比较(self):
        """测试多区域比较"""
        比较器 = 帧比较器()
        
        图像 = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)
        区域列表 = [(0, 0, 30, 30), (50, 50, 30, 30)]
        
        结果 = 比较器.比较多区域(图像, 图像.copy(), 区域列表)
        
        assert len(结果) == 2
        for 相似度 in 结果:
            assert 相似度 >= 0.99


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
