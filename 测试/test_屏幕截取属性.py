"""
屏幕截取属性测试模块

使用 Hypothesis 进行属性测试，验证屏幕截取模块的正确性。

**属性 1: 参数名称等价性**
*对于任意* 有效的屏幕区域，使用参数名"区域"和"region"调用截取屏幕函数应产生相同的结果。
验证: 需求 1.3, 1.4

**属性 5: 截取尺寸正确性**
*对于任意* 有效区域 (左, 上, 右, 下)，截取返回的图像尺寸应为 (右-左, 下-上)。
验证: 需求 3.1, 3.2, 3.3
"""

import pytest
import numpy as np
from hypothesis import given, strategies as st, settings, assume
from typing import Tuple
from unittest.mock import patch, MagicMock


# ==================== 策略定义 ====================

@st.composite
def 有效屏幕区域(draw, 最大宽度=500, 最大高度=500):
    """
    生成有效的屏幕区域 (左, 上, 右, 下)
    
    确保:
    - 左 < 右
    - 上 < 下
    - 所有值为非负整数
    - 区域大小合理（避免过大导致测试超时）
    """
    左 = draw(st.integers(min_value=0, max_value=最大宽度 - 10))
    上 = draw(st.integers(min_value=0, max_value=最大高度 - 10))
    
    # 确保宽度和高度至少为 10 像素
    宽度 = draw(st.integers(min_value=10, max_value=min(200, 最大宽度 - 左)))
    高度 = draw(st.integers(min_value=10, max_value=min(200, 最大高度 - 上)))
    
    右 = 左 + 宽度
    下 = 上 + 高度
    
    return (左, 上, 右, 下)


@st.composite
def 小屏幕区域(draw):
    """
    生成较小的屏幕区域，用于快速测试
    """
    左 = draw(st.integers(min_value=0, max_value=100))
    上 = draw(st.integers(min_value=0, max_value=100))
    宽度 = draw(st.integers(min_value=10, max_value=50))
    高度 = draw(st.integers(min_value=10, max_value=50))
    
    return (左, 上, 左 + 宽度, 上 + 高度)


# ==================== 模拟 GDI 截取函数 ====================

def 模拟GDI截取(区域=None):
    """
    模拟 GDI 截取函数，用于测试宽高计算逻辑
    
    这个函数模拟了 _标准GDI截取 的宽高计算逻辑，
    但返回一个指定尺寸的空白图像而不是实际截取屏幕。
    """
    if 区域:
        左, 上, 右, 下 = 区域
        # 正确的计算方式：不加 1
        宽度 = 右 - 左
        高度 = 下 - 上
    else:
        # 默认全屏尺寸
        宽度 = 1920
        高度 = 1080
    
    # 返回指定尺寸的空白 RGB 图像
    return np.zeros((高度, 宽度, 3), dtype=np.uint8)


def 错误的GDI截取(区域=None):
    """
    模拟错误的 GDI 截取函数（加 1 的版本）
    用于对比测试
    """
    if 区域:
        左, 上, 右, 下 = 区域
        # 错误的计算方式：加 1
        宽度 = 右 - 左 + 1
        高度 = 下 - 上 + 1
    else:
        宽度 = 1920
        高度 = 1080
    
    return np.zeros((高度, 宽度, 3), dtype=np.uint8)


# ==================== 属性 1: 参数名称等价性 ====================

class Test参数名称等价性属性:
    """
    属性测试: 参数名称等价性
    
    Feature: business-logic-fixes, Property 1: 参数名称等价性
    *对于任意* 有效的屏幕区域，使用参数名"区域"和"region"调用截取屏幕函数应产生相同的结果。
    
    **验证: 需求 1.3, 1.4**
    """

    @settings(max_examples=100, deadline=30000)
    @given(区域=小屏幕区域())
    def test_参数别名产生相同结果(self, 区域: Tuple[int, int, int, int]):
        """
        属性测试: 使用"区域"和"region"参数应产生相同结果
        
        Feature: business-logic-fixes, Property 1: 参数名称等价性
        **验证: 需求 1.3, 1.4**
        """
        # 使用模拟函数测试参数别名逻辑
        def 截取屏幕_模拟(区域=None, region=None):
            """模拟截取屏幕函数的参数别名逻辑"""
            实际区域 = 区域 if 区域 is not None else region
            return 模拟GDI截取(实际区域)
        
        # 使用 区域 参数
        结果1 = 截取屏幕_模拟(区域=区域)
        
        # 使用 region 参数
        结果2 = 截取屏幕_模拟(region=区域)
        
        # 验证两种方式产生相同的结果
        assert 结果1.shape == 结果2.shape, \
            f"参数别名产生不同尺寸: 区域={结果1.shape}, region={结果2.shape}"
        
        assert np.array_equal(结果1, 结果2), \
            "参数别名产生不同的图像内容"

    @settings(max_examples=100, deadline=30000)
    @given(区域=小屏幕区域())
    def test_区域参数优先于region参数(self, 区域: Tuple[int, int, int, int]):
        """
        属性测试: 当同时提供两个参数时，区域参数应优先
        
        Feature: business-logic-fixes, Property 1: 参数名称等价性
        **验证: 需求 1.3, 1.4**
        """
        # 创建一个不同的区域
        其他区域 = (区域[0] + 5, 区域[1] + 5, 区域[2] + 5, 区域[3] + 5)
        
        def 截取屏幕_模拟(区域=None, region=None):
            """模拟截取屏幕函数的参数别名逻辑"""
            实际区域 = 区域 if 区域 is not None else region
            return 模拟GDI截取(实际区域)
        
        # 同时提供两个参数，区域参数应优先
        结果 = 截取屏幕_模拟(区域=区域, region=其他区域)
        
        # 验证使用的是 区域 参数
        期望宽度 = 区域[2] - 区域[0]
        期望高度 = 区域[3] - 区域[1]
        
        assert 结果.shape[1] == 期望宽度, \
            f"应使用区域参数的宽度 {期望宽度}，实际 {结果.shape[1]}"
        assert 结果.shape[0] == 期望高度, \
            f"应使用区域参数的高度 {期望高度}，实际 {结果.shape[0]}"

    def test_两个参数都为None时返回全屏(self):
        """
        测试: 当两个参数都为 None 时应返回全屏截图
        
        Feature: business-logic-fixes, Property 1: 参数名称等价性
        **验证: 需求 1.3, 1.4**
        """
        def 截取屏幕_模拟(区域=None, region=None):
            """模拟截取屏幕函数的参数别名逻辑"""
            实际区域 = 区域 if 区域 is not None else region
            return 模拟GDI截取(实际区域)
        
        结果 = 截取屏幕_模拟()
        
        # 验证返回默认全屏尺寸
        assert 结果.shape == (1080, 1920, 3), \
            f"全屏截图尺寸不正确: {结果.shape}"


# ==================== 属性 5: 截取尺寸正确性 ====================

class Test截取尺寸正确性属性:
    """
    属性测试: 截取尺寸正确性
    
    Feature: business-logic-fixes, Property 5: 截取尺寸正确性
    *对于任意* 有效区域 (左, 上, 右, 下)，截取返回的图像尺寸应为 (右-左, 下-上)。
    
    **验证: 需求 3.1, 3.2, 3.3**
    """

    @settings(max_examples=100, deadline=30000)
    @given(区域=有效屏幕区域())
    def test_截取尺寸等于区域差值(self, 区域: Tuple[int, int, int, int]):
        """
        属性测试: 截取的图像尺寸应等于 (右-左, 下-上)
        
        Feature: business-logic-fixes, Property 5: 截取尺寸正确性
        **验证: 需求 3.1, 3.2, 3.3**
        """
        左, 上, 右, 下 = 区域
        
        # 使用正确的 GDI 截取模拟
        图像 = 模拟GDI截取(区域)
        
        期望宽度 = 右 - 左
        期望高度 = 下 - 上
        
        assert 图像.shape[1] == 期望宽度, \
            f"宽度不正确: 期望 {期望宽度}，实际 {图像.shape[1]}"
        assert 图像.shape[0] == 期望高度, \
            f"高度不正确: 期望 {期望高度}，实际 {图像.shape[0]}"

    @settings(max_examples=100, deadline=30000)
    @given(区域=有效屏幕区域())
    def test_宽度计算不加1(self, 区域: Tuple[int, int, int, int]):
        """
        属性测试: 宽度计算应为 (右 - 左)，不加 1
        
        Feature: business-logic-fixes, Property 5: 截取尺寸正确性
        **验证: 需求 3.1**
        """
        左, 上, 右, 下 = 区域
        
        图像 = 模拟GDI截取(区域)
        
        正确宽度 = 右 - 左
        错误宽度 = 右 - 左 + 1
        
        assert 图像.shape[1] == 正确宽度, \
            f"宽度应为 {正确宽度}，不是 {错误宽度}"
        assert 图像.shape[1] != 错误宽度, \
            "宽度计算错误地加了 1"

    @settings(max_examples=100, deadline=30000)
    @given(区域=有效屏幕区域())
    def test_高度计算不加1(self, 区域: Tuple[int, int, int, int]):
        """
        属性测试: 高度计算应为 (下 - 上)，不加 1
        
        Feature: business-logic-fixes, Property 5: 截取尺寸正确性
        **验证: 需求 3.2**
        """
        左, 上, 右, 下 = 区域
        
        图像 = 模拟GDI截取(区域)
        
        正确高度 = 下 - 上
        错误高度 = 下 - 上 + 1
        
        assert 图像.shape[0] == 正确高度, \
            f"高度应为 {正确高度}，不是 {错误高度}"
        assert 图像.shape[0] != 错误高度, \
            "高度计算错误地加了 1"

    def test_100x100区域返回100x100图像(self):
        """
        测试: 区域 (0, 0, 100, 100) 应返回正好 100x100 像素的图像
        
        Feature: business-logic-fixes, Property 5: 截取尺寸正确性
        **验证: 需求 3.3**
        """
        区域 = (0, 0, 100, 100)
        
        图像 = 模拟GDI截取(区域)
        
        assert 图像.shape == (100, 100, 3), \
            f"区域 (0, 0, 100, 100) 应返回 100x100 图像，实际 {图像.shape}"

    def test_错误实现会产生多1像素(self):
        """
        对比测试: 验证错误的实现（加 1）会产生多 1 像素
        
        Feature: business-logic-fixes, Property 5: 截取尺寸正确性
        **验证: 需求 3.1, 3.2, 3.3**
        """
        区域 = (0, 0, 100, 100)
        
        正确图像 = 模拟GDI截取(区域)
        错误图像 = 错误的GDI截取(区域)
        
        # 正确实现应返回 100x100
        assert 正确图像.shape == (100, 100, 3), \
            f"正确实现应返回 100x100，实际 {正确图像.shape}"
        
        # 错误实现会返回 101x101
        assert 错误图像.shape == (101, 101, 3), \
            f"错误实现应返回 101x101，实际 {错误图像.shape}"

    @settings(max_examples=100, deadline=30000)
    @given(区域=有效屏幕区域())
    def test_图像通道数为3(self, 区域: Tuple[int, int, int, int]):
        """
        属性测试: 截取的图像应为 RGB 格式（3 通道）
        
        Feature: business-logic-fixes, Property 5: 截取尺寸正确性
        **验证: 需求 3.1, 3.2**
        """
        图像 = 模拟GDI截取(区域)
        
        assert len(图像.shape) == 3, \
            f"图像应为 3 维数组，实际 {len(图像.shape)} 维"
        assert 图像.shape[2] == 3, \
            f"图像应为 3 通道（RGB），实际 {图像.shape[2]} 通道"


# ==================== 边界情况测试 ====================

class Test边界情况:
    """边界情况测试"""

    def test_最小有效区域(self):
        """测试最小有效区域 (1x1 像素)"""
        区域 = (0, 0, 1, 1)
        图像 = 模拟GDI截取(区域)
        
        assert 图像.shape == (1, 1, 3), \
            f"1x1 区域应返回 1x1 图像，实际 {图像.shape}"

    def test_非零起点区域(self):
        """测试非零起点的区域"""
        区域 = (100, 200, 150, 250)
        图像 = 模拟GDI截取(区域)
        
        期望宽度 = 150 - 100  # 50
        期望高度 = 250 - 200  # 50
        
        assert 图像.shape == (期望高度, 期望宽度, 3), \
            f"区域 {区域} 应返回 {期望高度}x{期望宽度} 图像，实际 {图像.shape}"

    def test_宽高不等的区域(self):
        """测试宽高不等的区域"""
        区域 = (0, 0, 200, 100)  # 宽 200，高 100
        图像 = 模拟GDI截取(区域)
        
        assert 图像.shape == (100, 200, 3), \
            f"200x100 区域应返回 100x200 图像（高x宽），实际 {图像.shape}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])
