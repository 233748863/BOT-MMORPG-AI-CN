"""
图像尺寸保持不变属性测试模块

使用 Hypothesis 进行属性测试，验证数据增强变换操作保持图像尺寸不变。

**属性 1: 图像尺寸保持不变**
*对于任意* 输入图像和任意变换操作，输出图像尺寸应与输入相同

验证: 需求 1.6
"""

import pytest
import numpy as np
from hypothesis import given, strategies as st, settings, assume
from typing import Tuple, List

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
    语义安全增强管道,
    创建语义安全增强器,
)


# ==================== 策略定义 ====================

@st.composite
def 随机BGR图像(draw, 最小宽度=10, 最大宽度=200, 最小高度=10, 最大高度=200):
    """
    生成随机 BGR 图像
    
    参数:
        最小宽度: 图像最小宽度
        最大宽度: 图像最大宽度
        最小高度: 图像最小高度
        最大高度: 图像最大高度
    """
    宽度 = draw(st.integers(min_value=最小宽度, max_value=最大宽度))
    高度 = draw(st.integers(min_value=最小高度, max_value=最大高度))
    
    # 使用随机种子生成图像
    种子 = draw(st.integers(min_value=0, max_value=2**31 - 1))
    rng = np.random.default_rng(种子)
    
    return rng.integers(0, 256, size=(高度, 宽度, 3), dtype=np.uint8)


@st.composite
def 随机灰度图像(draw, 最小宽度=10, 最大宽度=200, 最小高度=10, 最大高度=200):
    """生成随机灰度图像"""
    宽度 = draw(st.integers(min_value=最小宽度, max_value=最大宽度))
    高度 = draw(st.integers(min_value=最小高度, max_value=最大高度))
    
    种子 = draw(st.integers(min_value=0, max_value=2**31 - 1))
    rng = np.random.default_rng(种子)
    
    return rng.integers(0, 256, size=(高度, 宽度), dtype=np.uint8)


@st.composite
def 有效概率(draw):
    """生成有效的概率值 (0-1)"""
    return draw(st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False))


@st.composite
def 有效强度(draw):
    """生成有效的强度值 (0-1)"""
    return draw(st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False))


@st.composite
def 亮度调整变换(draw):
    """生成亮度调整变换实例"""
    概率 = draw(有效概率())
    强度 = draw(有效强度())
    范围最小 = draw(st.floats(min_value=-0.5, max_value=0.0))
    范围最大 = draw(st.floats(min_value=0.0, max_value=0.5))
    return 亮度调整(概率=1.0, 强度=强度, 范围=(范围最小, 范围最大))


@st.composite
def 对比度调整变换(draw):
    """生成对比度调整变换实例"""
    强度 = draw(有效强度())
    范围最小 = draw(st.floats(min_value=0.5, max_value=1.0))
    范围最大 = draw(st.floats(min_value=1.0, max_value=1.5))
    return 对比度调整(概率=1.0, 强度=强度, 范围=(范围最小, 范围最大))


@st.composite
def 高斯噪声变换(draw):
    """生成高斯噪声变换实例"""
    强度 = draw(有效强度())
    标准差 = draw(st.floats(min_value=0.01, max_value=0.1))
    return 高斯噪声(概率=1.0, 强度=强度, 标准差=标准差)


@st.composite
def 颜色抖动变换(draw):
    """生成颜色抖动变换实例"""
    强度 = draw(有效强度())
    色调范围 = draw(st.floats(min_value=0.01, max_value=0.2))
    饱和度范围 = draw(st.floats(min_value=0.01, max_value=0.3))
    return 颜色抖动(概率=1.0, 强度=强度, 色调范围=色调范围, 饱和度范围=饱和度范围)


@st.composite
def 高斯模糊变换(draw):
    """生成高斯模糊变换实例"""
    强度 = draw(有效强度())
    核最小 = draw(st.integers(min_value=3, max_value=5))
    核最大 = draw(st.integers(min_value=核最小, max_value=9))
    # 确保核大小为奇数
    if 核最小 % 2 == 0:
        核最小 += 1
    if 核最大 % 2 == 0:
        核最大 += 1
    return 高斯模糊(概率=1.0, 强度=强度, 核大小范围=(核最小, 核最大))


@st.composite
def 旋转变换(draw):
    """生成旋转变换实例"""
    强度 = draw(有效强度())
    角度最小 = draw(st.floats(min_value=-15.0, max_value=0.0))
    角度最大 = draw(st.floats(min_value=0.0, max_value=15.0))
    return 旋转(概率=1.0, 强度=强度, 角度范围=(角度最小, 角度最大))


@st.composite
def 缩放裁剪变换(draw):
    """生成缩放裁剪变换实例"""
    强度 = draw(有效强度())
    缩放最小 = draw(st.floats(min_value=0.8, max_value=1.0))
    缩放最大 = draw(st.floats(min_value=1.0, max_value=1.2))
    return 缩放裁剪(概率=1.0, 强度=强度, 缩放范围=(缩放最小, 缩放最大))


@st.composite
def 光照模拟变换(draw):
    """生成光照模拟变换实例"""
    强度 = draw(有效强度())
    强度最小 = draw(st.floats(min_value=0.5, max_value=1.0))
    强度最大 = draw(st.floats(min_value=1.0, max_value=1.5))
    return 光照模拟(概率=1.0, 强度=强度, 强度范围=(强度最小, 强度最大))


@st.composite
def UI遮挡模拟变换(draw):
    """生成UI遮挡模拟变换实例"""
    强度 = draw(有效强度())
    遮挡数量 = draw(st.integers(min_value=1, max_value=3))
    最大尺寸 = draw(st.floats(min_value=0.02, max_value=0.15))
    return UI遮挡模拟(概率=1.0, 强度=强度, 遮挡数量=遮挡数量, 最大尺寸=最大尺寸)


@st.composite
def 透视变换变换(draw):
    """生成透视变换实例"""
    强度 = draw(有效强度())
    最大偏移 = draw(st.floats(min_value=0.01, max_value=0.1))
    return 透视变换(概率=1.0, 强度=强度, 最大偏移=最大偏移)


@st.composite
def 任意变换(draw):
    """生成任意变换实例"""
    变换类型 = draw(st.sampled_from([
        '亮度调整', '对比度调整', '水平翻转', '垂直翻转',
        '高斯噪声', '颜色抖动', '高斯模糊', '旋转',
        '缩放裁剪', '光照模拟', 'UI遮挡模拟', '透视变换'
    ]))
    
    if 变换类型 == '亮度调整':
        return draw(亮度调整变换())
    elif 变换类型 == '对比度调整':
        return draw(对比度调整变换())
    elif 变换类型 == '水平翻转':
        return 水平翻转(概率=1.0)
    elif 变换类型 == '垂直翻转':
        return 垂直翻转(概率=1.0)
    elif 变换类型 == '高斯噪声':
        return draw(高斯噪声变换())
    elif 变换类型 == '颜色抖动':
        return draw(颜色抖动变换())
    elif 变换类型 == '高斯模糊':
        return draw(高斯模糊变换())
    elif 变换类型 == '旋转':
        return draw(旋转变换())
    elif 变换类型 == '缩放裁剪':
        return draw(缩放裁剪变换())
    elif 变换类型 == '光照模拟':
        return draw(光照模拟变换())
    elif 变换类型 == 'UI遮挡模拟':
        return draw(UI遮挡模拟变换())
    elif 变换类型 == '透视变换':
        return draw(透视变换变换())


# ==================== 属性 1: 图像尺寸保持不变 ====================

class Test图像尺寸保持不变属性:
    """
    属性测试: 图像尺寸保持不变
    
    Feature: training-data-augmentation, Property 1: 图像尺寸保持不变
    *对于任意* 输入图像和任意变换操作，输出图像尺寸应与输入相同
    
    **验证: 需求 1.6**
    """

    @settings(max_examples=100, deadline=10000)
    @given(图像=随机BGR图像(), 变换=任意变换())
    def test_任意变换保持图像尺寸(self, 图像: np.ndarray, 变换: 变换基类):
        """
        属性测试: 任意变换操作应保持图像尺寸不变
        
        Feature: training-data-augmentation, Property 1: 图像尺寸保持不变
        **验证: 需求 1.6**
        """
        原始尺寸 = 图像.shape
        
        # 应用变换
        结果图像 = 变换(图像)
        
        assert 结果图像.shape == 原始尺寸, \
            f"变换 {变换.名称} 改变了图像尺寸: {原始尺寸} -> {结果图像.shape}"

    @settings(max_examples=100, deadline=10000)
    @given(图像=随机BGR图像())
    def test_亮度调整保持图像尺寸(self, 图像: np.ndarray):
        """
        属性测试: 亮度调整应保持图像尺寸不变
        
        Feature: training-data-augmentation, Property 1: 图像尺寸保持不变
        **验证: 需求 1.6**
        """
        原始尺寸 = 图像.shape
        变换 = 亮度调整(概率=1.0)
        
        结果图像 = 变换(图像)
        
        assert 结果图像.shape == 原始尺寸, \
            f"亮度调整改变了图像尺寸: {原始尺寸} -> {结果图像.shape}"

    @settings(max_examples=100, deadline=10000)
    @given(图像=随机BGR图像())
    def test_对比度调整保持图像尺寸(self, 图像: np.ndarray):
        """
        属性测试: 对比度调整应保持图像尺寸不变
        
        Feature: training-data-augmentation, Property 1: 图像尺寸保持不变
        **验证: 需求 1.6**
        """
        原始尺寸 = 图像.shape
        变换 = 对比度调整(概率=1.0)
        
        结果图像 = 变换(图像)
        
        assert 结果图像.shape == 原始尺寸, \
            f"对比度调整改变了图像尺寸: {原始尺寸} -> {结果图像.shape}"

    @settings(max_examples=100, deadline=10000)
    @given(图像=随机BGR图像())
    def test_水平翻转保持图像尺寸(self, 图像: np.ndarray):
        """
        属性测试: 水平翻转应保持图像尺寸不变
        
        Feature: training-data-augmentation, Property 1: 图像尺寸保持不变
        **验证: 需求 1.6**
        """
        原始尺寸 = 图像.shape
        变换 = 水平翻转(概率=1.0)
        
        结果图像 = 变换(图像)
        
        assert 结果图像.shape == 原始尺寸, \
            f"水平翻转改变了图像尺寸: {原始尺寸} -> {结果图像.shape}"

    @settings(max_examples=100, deadline=10000)
    @given(图像=随机BGR图像())
    def test_高斯噪声保持图像尺寸(self, 图像: np.ndarray):
        """
        属性测试: 高斯噪声应保持图像尺寸不变
        
        Feature: training-data-augmentation, Property 1: 图像尺寸保持不变
        **验证: 需求 1.6**
        """
        原始尺寸 = 图像.shape
        变换 = 高斯噪声(概率=1.0)
        
        结果图像 = 变换(图像)
        
        assert 结果图像.shape == 原始尺寸, \
            f"高斯噪声改变了图像尺寸: {原始尺寸} -> {结果图像.shape}"

    @settings(max_examples=100, deadline=10000)
    @given(图像=随机BGR图像())
    def test_颜色抖动保持图像尺寸(self, 图像: np.ndarray):
        """
        属性测试: 颜色抖动应保持图像尺寸不变
        
        Feature: training-data-augmentation, Property 1: 图像尺寸保持不变
        **验证: 需求 1.6**
        """
        原始尺寸 = 图像.shape
        变换 = 颜色抖动(概率=1.0)
        
        结果图像 = 变换(图像)
        
        assert 结果图像.shape == 原始尺寸, \
            f"颜色抖动改变了图像尺寸: {原始尺寸} -> {结果图像.shape}"

    @settings(max_examples=100, deadline=10000)
    @given(图像=随机BGR图像())
    def test_旋转保持图像尺寸(self, 图像: np.ndarray):
        """
        属性测试: 旋转应保持图像尺寸不变
        
        Feature: training-data-augmentation, Property 1: 图像尺寸保持不变
        **验证: 需求 1.6**
        """
        原始尺寸 = 图像.shape
        变换 = 旋转(概率=1.0)
        
        结果图像 = 变换(图像)
        
        assert 结果图像.shape == 原始尺寸, \
            f"旋转改变了图像尺寸: {原始尺寸} -> {结果图像.shape}"

    @settings(max_examples=100, deadline=10000)
    @given(图像=随机BGR图像())
    def test_缩放裁剪保持图像尺寸(self, 图像: np.ndarray):
        """
        属性测试: 缩放裁剪应保持图像尺寸不变
        
        Feature: training-data-augmentation, Property 1: 图像尺寸保持不变
        **验证: 需求 1.6**
        """
        原始尺寸 = 图像.shape
        变换 = 缩放裁剪(概率=1.0)
        
        结果图像 = 变换(图像)
        
        assert 结果图像.shape == 原始尺寸, \
            f"缩放裁剪改变了图像尺寸: {原始尺寸} -> {结果图像.shape}"

    @settings(max_examples=100, deadline=10000)
    @given(图像=随机BGR图像())
    def test_透视变换保持图像尺寸(self, 图像: np.ndarray):
        """
        属性测试: 透视变换应保持图像尺寸不变
        
        Feature: training-data-augmentation, Property 1: 图像尺寸保持不变
        **验证: 需求 1.6**
        """
        原始尺寸 = 图像.shape
        变换 = 透视变换(概率=1.0)
        
        结果图像 = 变换(图像)
        
        assert 结果图像.shape == 原始尺寸, \
            f"透视变换改变了图像尺寸: {原始尺寸} -> {结果图像.shape}"

    @settings(max_examples=100, deadline=10000)
    @given(图像=随机BGR图像())
    def test_增强管道保持图像尺寸(self, 图像: np.ndarray):
        """
        属性测试: 增强管道应保持图像尺寸不变
        
        Feature: training-data-augmentation, Property 1: 图像尺寸保持不变
        **验证: 需求 1.6**
        """
        原始尺寸 = 图像.shape
        
        管道 = 增强管道()
        管道.添加变换(亮度调整(概率=1.0))
        管道.添加变换(对比度调整(概率=1.0))
        管道.添加变换(水平翻转(概率=1.0))
        
        结果图像 = 管道(图像)
        
        assert 结果图像.shape == 原始尺寸, \
            f"增强管道改变了图像尺寸: {原始尺寸} -> {结果图像.shape}"

    @settings(max_examples=100, deadline=10000)
    @given(图像=随机BGR图像())
    def test_数据增强器保持图像尺寸(self, 图像: np.ndarray):
        """
        属性测试: 数据增强器应保持图像尺寸不变
        
        Feature: training-data-augmentation, Property 1: 图像尺寸保持不变
        **验证: 需求 1.6**
        """
        原始尺寸 = 图像.shape
        
        增强器 = 数据增强器()
        结果图像 = 增强器.增强(图像)
        
        assert 结果图像.shape == 原始尺寸, \
            f"数据增强器改变了图像尺寸: {原始尺寸} -> {结果图像.shape}"

    @settings(max_examples=100, deadline=10000)
    @given(图像=随机BGR图像())
    def test_语义安全增强器保持图像尺寸(self, 图像: np.ndarray):
        """
        属性测试: 语义安全增强器应保持图像尺寸不变
        
        Feature: training-data-augmentation, Property 1: 图像尺寸保持不变
        **验证: 需求 1.6**
        """
        原始尺寸 = 图像.shape
        
        增强器 = 创建语义安全增强器()
        结果图像 = 增强器.增强(图像)
        
        assert 结果图像.shape == 原始尺寸, \
            f"语义安全增强器改变了图像尺寸: {原始尺寸} -> {结果图像.shape}"


# ==================== 灰度图像测试 ====================

class Test灰度图像尺寸保持:
    """灰度图像的尺寸保持测试"""

    @settings(max_examples=100, deadline=10000)
    @given(图像=随机灰度图像())
    def test_亮度调整灰度图像保持尺寸(self, 图像: np.ndarray):
        """
        属性测试: 亮度调整应保持灰度图像尺寸不变
        
        Feature: training-data-augmentation, Property 1: 图像尺寸保持不变
        **验证: 需求 1.6**
        """
        原始尺寸 = 图像.shape
        变换 = 亮度调整(概率=1.0)
        
        结果图像 = 变换(图像)
        
        assert 结果图像.shape == 原始尺寸, \
            f"亮度调整改变了灰度图像尺寸: {原始尺寸} -> {结果图像.shape}"

    @settings(max_examples=100, deadline=10000)
    @given(图像=随机灰度图像())
    def test_高斯噪声灰度图像保持尺寸(self, 图像: np.ndarray):
        """
        属性测试: 高斯噪声应保持灰度图像尺寸不变
        
        Feature: training-data-augmentation, Property 1: 图像尺寸保持不变
        **验证: 需求 1.6**
        """
        原始尺寸 = 图像.shape
        变换 = 高斯噪声(概率=1.0)
        
        结果图像 = 变换(图像)
        
        assert 结果图像.shape == 原始尺寸, \
            f"高斯噪声改变了灰度图像尺寸: {原始尺寸} -> {结果图像.shape}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])
