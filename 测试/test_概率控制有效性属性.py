"""
概率控制有效性属性测试模块

使用 Hypothesis 进行属性测试，验证数据增强变换的概率控制有效性。

**属性 2: 概率控制有效性**
*对于任意* 设置概率 p 的变换，大量样本上实际应用比例应接近 p

验证: 需求 3.2
"""

import pytest
import numpy as np
from hypothesis import given, strategies as st, settings, assume
from typing import Tuple, List, Type

from 工具.数据增强 import (
    变换基类,
    亮度调整,
    对比度调整,
    水平翻转,
    垂直翻转,
    高斯噪声,
    颜色抖动,
    高斯模糊,
    旋转,
    缩放裁剪,
    光照模拟,
    UI遮挡模拟,
    透视变换,
    增强管道,
    数据增强器,
)


# ==================== 策略定义 ====================

@st.composite
def 随机BGR图像(draw, 宽度=64, 高度=64):
    """
    生成固定尺寸的随机 BGR 图像（用于概率测试）
    
    使用固定尺寸以减少测试时间
    """
    种子 = draw(st.integers(min_value=0, max_value=2**31 - 1))
    rng = np.random.default_rng(种子)
    return rng.integers(0, 256, size=(高度, 宽度, 3), dtype=np.uint8)


@st.composite
def 有效概率(draw):
    """生成有效的概率值 (0.1-0.9)，避免极端值"""
    return draw(st.floats(min_value=0.1, max_value=0.9, allow_nan=False, allow_infinity=False))


# ==================== 辅助函数 ====================

def 检测变换是否应用(原始图像: np.ndarray, 变换后图像: np.ndarray, 容差: float = 1e-6) -> bool:
    """
    检测变换是否实际应用（图像是否发生变化）
    
    参数:
        原始图像: 原始图像
        变换后图像: 变换后的图像
        容差: 判断变化的容差
        
    返回:
        True 如果图像发生了变化，False 否则
    """
    return not np.allclose(原始图像, 变换后图像, atol=容差)


def 统计变换应用率(变换: 变换基类, 图像: np.ndarray, 样本数: int = 500) -> float:
    """
    统计变换在多次应用中的实际应用率
    
    参数:
        变换: 变换实例
        图像: 测试图像
        样本数: 测试样本数量
        
    返回:
        实际应用率 (0-1)
    """
    应用次数 = 0
    
    for _ in range(样本数):
        结果图像 = 变换(图像.copy())
        if 检测变换是否应用(图像, 结果图像):
            应用次数 += 1
    
    return 应用次数 / 样本数


# ==================== 属性 2: 概率控制有效性 ====================

class Test概率控制有效性属性:
    """
    属性测试: 概率控制有效性
    
    Feature: training-data-augmentation, Property 2: 概率控制有效性
    *对于任意* 设置概率 p 的变换，大量样本上实际应用比例应接近 p
    
    **验证: 需求 3.2**
    """

    # 允许的误差范围（由于随机性，实际应用率可能与设定概率有偏差）
    # 使用较宽松的容差以适应统计波动
    容差 = 0.15

    @settings(max_examples=20, deadline=60000)
    @given(概率=有效概率())
    def test_亮度调整概率控制(self, 概率: float):
        """
        属性测试: 亮度调整的概率控制应有效
        
        Feature: training-data-augmentation, Property 2: 概率控制有效性
        **验证: 需求 3.2**
        """
        # 创建测试图像
        图像 = np.random.randint(0, 256, size=(64, 64, 3), dtype=np.uint8)
        
        # 创建变换
        变换 = 亮度调整(概率=概率, 范围=(-0.3, 0.3))
        
        # 统计应用率
        实际应用率 = 统计变换应用率(变换, 图像, 样本数=300)
        
        assert abs(实际应用率 - 概率) <= self.容差, \
            f"亮度调整概率控制失效: 设定概率={概率:.2f}, 实际应用率={实际应用率:.2f}"

    @settings(max_examples=20, deadline=60000)
    @given(概率=有效概率())
    def test_对比度调整概率控制(self, 概率: float):
        """
        属性测试: 对比度调整的概率控制应有效
        
        Feature: training-data-augmentation, Property 2: 概率控制有效性
        **验证: 需求 3.2**
        """
        图像 = np.random.randint(0, 256, size=(64, 64, 3), dtype=np.uint8)
        变换 = 对比度调整(概率=概率, 范围=(0.5, 1.5))
        
        实际应用率 = 统计变换应用率(变换, 图像, 样本数=300)
        
        assert abs(实际应用率 - 概率) <= self.容差, \
            f"对比度调整概率控制失效: 设定概率={概率:.2f}, 实际应用率={实际应用率:.2f}"

    @settings(max_examples=20, deadline=60000)
    @given(概率=有效概率())
    def test_水平翻转概率控制(self, 概率: float):
        """
        属性测试: 水平翻转的概率控制应有效
        
        Feature: training-data-augmentation, Property 2: 概率控制有效性
        **验证: 需求 3.2**
        """
        图像 = np.random.randint(0, 256, size=(64, 64, 3), dtype=np.uint8)
        变换 = 水平翻转(概率=概率)
        
        实际应用率 = 统计变换应用率(变换, 图像, 样本数=300)
        
        assert abs(实际应用率 - 概率) <= self.容差, \
            f"水平翻转概率控制失效: 设定概率={概率:.2f}, 实际应用率={实际应用率:.2f}"

    @settings(max_examples=20, deadline=60000)
    @given(概率=有效概率())
    def test_高斯噪声概率控制(self, 概率: float):
        """
        属性测试: 高斯噪声的概率控制应有效
        
        Feature: training-data-augmentation, Property 2: 概率控制有效性
        **验证: 需求 3.2**
        """
        图像 = np.random.randint(0, 256, size=(64, 64, 3), dtype=np.uint8)
        变换 = 高斯噪声(概率=概率, 标准差=0.05)
        
        实际应用率 = 统计变换应用率(变换, 图像, 样本数=300)
        
        assert abs(实际应用率 - 概率) <= self.容差, \
            f"高斯噪声概率控制失效: 设定概率={概率:.2f}, 实际应用率={实际应用率:.2f}"

    @settings(max_examples=20, deadline=60000)
    @given(概率=有效概率())
    def test_颜色抖动概率控制(self, 概率: float):
        """
        属性测试: 颜色抖动的概率控制应有效
        
        Feature: training-data-augmentation, Property 2: 概率控制有效性
        **验证: 需求 3.2**
        """
        图像 = np.random.randint(0, 256, size=(64, 64, 3), dtype=np.uint8)
        变换 = 颜色抖动(概率=概率, 色调范围=0.2, 饱和度范围=0.3)
        
        实际应用率 = 统计变换应用率(变换, 图像, 样本数=300)
        
        assert abs(实际应用率 - 概率) <= self.容差, \
            f"颜色抖动概率控制失效: 设定概率={概率:.2f}, 实际应用率={实际应用率:.2f}"

    @settings(max_examples=20, deadline=60000)
    @given(概率=有效概率())
    def test_旋转概率控制(self, 概率: float):
        """
        属性测试: 旋转的概率控制应有效
        
        Feature: training-data-augmentation, Property 2: 概率控制有效性
        **验证: 需求 3.2**
        """
        图像 = np.random.randint(0, 256, size=(64, 64, 3), dtype=np.uint8)
        变换 = 旋转(概率=概率, 角度范围=(-15, 15))
        
        实际应用率 = 统计变换应用率(变换, 图像, 样本数=300)
        
        assert abs(实际应用率 - 概率) <= self.容差, \
            f"旋转概率控制失效: 设定概率={概率:.2f}, 实际应用率={实际应用率:.2f}"

    @settings(max_examples=20, deadline=60000)
    @given(概率=有效概率())
    def test_透视变换概率控制(self, 概率: float):
        """
        属性测试: 透视变换的概率控制应有效
        
        Feature: training-data-augmentation, Property 2: 概率控制有效性
        **验证: 需求 3.2**
        """
        图像 = np.random.randint(0, 256, size=(64, 64, 3), dtype=np.uint8)
        变换 = 透视变换(概率=概率, 最大偏移=0.1)
        
        实际应用率 = 统计变换应用率(变换, 图像, 样本数=300)
        
        assert abs(实际应用率 - 概率) <= self.容差, \
            f"透视变换概率控制失效: 设定概率={概率:.2f}, 实际应用率={实际应用率:.2f}"


# ==================== 边界条件测试 ====================

class Test概率边界条件:
    """概率边界条件测试"""

    def test_概率为零时不应用变换(self):
        """
        测试: 概率为 0 时变换不应被应用
        
        Feature: training-data-augmentation, Property 2: 概率控制有效性
        **验证: 需求 3.2**
        """
        图像 = np.random.randint(0, 256, size=(64, 64, 3), dtype=np.uint8)
        变换 = 亮度调整(概率=0.0, 范围=(-0.5, 0.5))
        
        实际应用率 = 统计变换应用率(变换, 图像, 样本数=100)
        
        assert 实际应用率 == 0.0, \
            f"概率为 0 时变换仍被应用: 实际应用率={实际应用率:.2f}"

    def test_概率为一时总是应用变换(self):
        """
        测试: 概率为 1 时变换应总是被应用
        
        Feature: training-data-augmentation, Property 2: 概率控制有效性
        **验证: 需求 3.2**
        
        注意: 使用水平翻转而非亮度调整，因为水平翻转总是会产生可检测的变化，
        而亮度调整在随机值接近0时可能产生极小的变化导致检测失败。
        """
        图像 = np.random.randint(0, 256, size=(64, 64, 3), dtype=np.uint8)
        # 使用水平翻转，因为它总是会产生可检测的变化（除非图像完全对称）
        变换 = 水平翻转(概率=1.0)
        
        实际应用率 = 统计变换应用率(变换, 图像, 样本数=100)
        
        assert 实际应用率 == 1.0, \
            f"概率为 1 时变换未总是被应用: 实际应用率={实际应用率:.2f}"

    def test_概率裁剪到有效范围(self):
        """
        测试: 超出范围的概率应被裁剪到有效范围
        
        Feature: training-data-augmentation, Property 2: 概率控制有效性
        **验证: 需求 3.2**
        """
        # 测试负概率被裁剪为 0
        变换负 = 亮度调整(概率=-0.5)
        assert 变换负.概率 == 0.0, f"负概率未被裁剪: {变换负.概率}"
        
        # 测试超过 1 的概率被裁剪为 1
        变换超 = 亮度调整(概率=1.5)
        assert 变换超.概率 == 1.0, f"超过 1 的概率未被裁剪: {变换超.概率}"


# ==================== 增强管道概率测试 ====================

class Test增强管道概率控制:
    """增强管道的概率控制测试"""

    @settings(max_examples=10, deadline=120000)
    @given(概率1=有效概率(), 概率2=有效概率())
    def test_管道中多个变换的独立概率控制(self, 概率1: float, 概率2: float):
        """
        属性测试: 管道中多个变换应独立控制概率
        
        Feature: training-data-augmentation, Property 2: 概率控制有效性
        **验证: 需求 3.2**
        """
        图像 = np.random.randint(0, 256, size=(64, 64, 3), dtype=np.uint8)
        
        # 创建管道
        管道 = 增强管道()
        管道.添加变换(亮度调整(概率=概率1, 范围=(-0.3, 0.3)))
        管道.添加变换(水平翻转(概率=概率2))
        
        # 统计应用率（通过检测图像变化）
        样本数 = 200
        变化次数 = 0
        
        for _ in range(样本数):
            结果图像 = 管道(图像.copy())
            if 检测变换是否应用(图像, 结果图像):
                变化次数 += 1
        
        实际变化率 = 变化次数 / 样本数
        
        # 至少一个变换被应用的理论概率
        # P(至少一个) = 1 - P(都不应用) = 1 - (1-p1)(1-p2)
        理论变化率 = 1 - (1 - 概率1) * (1 - 概率2)
        
        # 由于是组合概率，使用更宽松的容差
        容差 = 0.2
        assert abs(实际变化率 - 理论变化率) <= 容差, \
            f"管道概率控制失效: 理论变化率={理论变化率:.2f}, 实际变化率={实际变化率:.2f}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])
