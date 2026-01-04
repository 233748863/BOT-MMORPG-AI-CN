"""
检测值范围属性测试模块

使用 Hypothesis 进行属性测试，验证血量/蓝量检测结果的值范围。

**属性 1: 检测值范围**
*对于任意* 检测结果，百分比应在 [0.0, 1.0] 范围内

验证: 需求 2.5, 3.3
"""

import pytest
import numpy as np
from hypothesis import given, strategies as st, settings, assume
from typing import Tuple

from 核心.状态检测 import (
    状态条分析器,
    血量检测器,
    蓝量检测器,
    状态检测器,
    平滑器,
    状态检测结果
)


# ==================== 策略定义 ====================

@st.composite
def 有效图像尺寸(draw, 最小宽度=10, 最大宽度=500, 最小高度=5, 最大高度=100):
    """生成有效的图像尺寸"""
    宽度 = draw(st.integers(min_value=最小宽度, max_value=最大宽度))
    高度 = draw(st.integers(min_value=最小高度, max_value=最大高度))
    return (宽度, 高度)


@st.composite
def 随机BGR图像(draw, 宽度=None, 高度=None):
    """
    生成随机 BGR 图像
    
    参数:
        宽度: 图像宽度，None 则随机生成
        高度: 图像高度，None 则随机生成
    """
    if 宽度 is None:
        宽度 = draw(st.integers(min_value=10, max_value=100))
    if 高度 is None:
        高度 = draw(st.integers(min_value=5, max_value=50))
    
    # 使用随机种子生成图像
    种子 = draw(st.integers(min_value=0, max_value=2**31 - 1))
    rng = np.random.default_rng(种子)
    
    return rng.integers(0, 256, size=(高度, 宽度, 3), dtype=np.uint8)


@st.composite
def 纯色图像(draw, 宽度=None, 高度=None):
    """生成纯色图像"""
    if 宽度 is None:
        宽度 = draw(st.integers(min_value=10, max_value=100))
    if 高度 is None:
        高度 = draw(st.integers(min_value=5, max_value=50))
    
    B = draw(st.integers(min_value=0, max_value=255))
    G = draw(st.integers(min_value=0, max_value=255))
    R = draw(st.integers(min_value=0, max_value=255))
    
    图像 = np.full((高度, 宽度, 3), [B, G, R], dtype=np.uint8)
    return 图像


@st.composite
def 渐变图像(draw, 宽度=None, 高度=None):
    """生成水平渐变图像（模拟状态条）"""
    if 宽度 is None:
        宽度 = draw(st.integers(min_value=20, max_value=100))
    if 高度 is None:
        高度 = draw(st.integers(min_value=5, max_value=30))
    
    # 填充比例
    填充比例 = draw(st.floats(min_value=0.0, max_value=1.0))
    填充宽度 = int(宽度 * 填充比例)
    
    # 填充颜色（红色系）
    填充色 = [0, 0, 255]  # BGR 红色
    空白色 = [50, 50, 50]  # 灰色
    
    图像 = np.full((高度, 宽度, 3), 空白色, dtype=np.uint8)
    if 填充宽度 > 0:
        图像[:, :填充宽度] = 填充色
    
    return 图像


@st.composite
def 有效区域(draw, 图像宽度, 图像高度):
    """生成有效的检测区域"""
    x = draw(st.integers(min_value=0, max_value=max(0, 图像宽度 - 10)))
    y = draw(st.integers(min_value=0, max_value=max(0, 图像高度 - 5)))
    w = draw(st.integers(min_value=5, max_value=min(100, 图像宽度 - x)))
    h = draw(st.integers(min_value=3, max_value=min(30, 图像高度 - y)))
    return (x, y, w, h)


@st.composite
def 有效颜色配置(draw):
    """生成有效的颜色配置"""
    H_min = draw(st.integers(min_value=0, max_value=170))
    H_max = draw(st.integers(min_value=H_min, max_value=180))
    S_min = draw(st.integers(min_value=0, max_value=200))
    S_max = draw(st.integers(min_value=S_min, max_value=255))
    V_min = draw(st.integers(min_value=0, max_value=200))
    V_max = draw(st.integers(min_value=V_min, max_value=255))
    
    return {
        "填充色": {
            "H_min": H_min, "H_max": H_max,
            "S_min": S_min, "S_max": S_max,
            "V_min": V_min, "V_max": V_max
        }
    }


@st.composite
def 有效平滑值(draw):
    """生成有效的平滑输入值"""
    return draw(st.floats(min_value=-10.0, max_value=10.0, allow_nan=False, allow_infinity=False))


# ==================== 属性 1: 检测值范围 ====================

class Test检测值范围属性:
    """
    属性测试: 检测值范围
    
    Feature: health-mana-detection, Property 1: 检测值范围
    *对于任意* 检测结果，百分比应在 [0.0, 1.0] 范围内
    
    **验证: 需求 2.5, 3.3**
    """

    @settings(max_examples=100, deadline=10000)
    @given(图像=随机BGR图像())
    def test_状态条分析器返回值范围(self, 图像: np.ndarray):
        """
        属性测试: 状态条分析器返回的百分比和置信度应在 [0.0, 1.0] 范围内
        
        Feature: health-mana-detection, Property 1: 检测值范围
        **验证: 需求 2.5**
        """
        分析器 = 状态条分析器()
        
        百分比, 置信度 = 分析器.分析(图像)
        
        assert 0.0 <= 百分比 <= 1.0, \
            f"百分比应在 [0.0, 1.0] 范围内，实际: {百分比}"
        assert 0.0 <= 置信度 <= 1.0, \
            f"置信度应在 [0.0, 1.0] 范围内，实际: {置信度}"

    @settings(max_examples=100, deadline=10000)
    @given(图像=纯色图像())
    def test_纯色图像检测值范围(self, 图像: np.ndarray):
        """
        属性测试: 纯色图像的检测结果应在有效范围内
        
        Feature: health-mana-detection, Property 1: 检测值范围
        **验证: 需求 2.5**
        """
        分析器 = 状态条分析器()
        
        百分比, 置信度 = 分析器.分析(图像)
        
        assert 0.0 <= 百分比 <= 1.0, \
            f"纯色图像百分比应在 [0.0, 1.0] 范围内，实际: {百分比}"
        assert 0.0 <= 置信度 <= 1.0, \
            f"纯色图像置信度应在 [0.0, 1.0] 范围内，实际: {置信度}"

    @settings(max_examples=100, deadline=10000)
    @given(图像=渐变图像())
    def test_渐变图像检测值范围(self, 图像: np.ndarray):
        """
        属性测试: 渐变图像（模拟状态条）的检测结果应在有效范围内
        
        Feature: health-mana-detection, Property 1: 检测值范围
        **验证: 需求 2.5**
        """
        # 使用红色检测配置
        颜色配置 = {
            "填充色": {
                "H_min": 0, "H_max": 10,
                "S_min": 100, "S_max": 255,
                "V_min": 100, "V_max": 255
            }
        }
        分析器 = 状态条分析器(颜色配置)
        
        百分比, 置信度 = 分析器.分析(图像)
        
        assert 0.0 <= 百分比 <= 1.0, \
            f"渐变图像百分比应在 [0.0, 1.0] 范围内，实际: {百分比}"
        assert 0.0 <= 置信度 <= 1.0, \
            f"渐变图像置信度应在 [0.0, 1.0] 范围内，实际: {置信度}"

    @settings(max_examples=100, deadline=10000)
    @given(颜色配置=有效颜色配置(), 图像=随机BGR图像())
    def test_自定义颜色配置检测值范围(self, 颜色配置: dict, 图像: np.ndarray):
        """
        属性测试: 使用任意有效颜色配置的检测结果应在有效范围内
        
        Feature: health-mana-detection, Property 1: 检测值范围
        **验证: 需求 2.5**
        """
        分析器 = 状态条分析器(颜色配置)
        
        百分比, 置信度 = 分析器.分析(图像)
        
        assert 0.0 <= 百分比 <= 1.0, \
            f"自定义配置百分比应在 [0.0, 1.0] 范围内，实际: {百分比}"
        assert 0.0 <= 置信度 <= 1.0, \
            f"自定义配置置信度应在 [0.0, 1.0] 范围内，实际: {置信度}"

    @settings(max_examples=100, deadline=10000)
    @given(图像=随机BGR图像(宽度=200, 高度=100))
    def test_血量检测器返回值范围(self, 图像: np.ndarray):
        """
        属性测试: 血量检测器返回的百分比应在 [0.0, 1.0] 范围内
        
        Feature: health-mana-detection, Property 1: 检测值范围
        **验证: 需求 2.5**
        """
        检测器 = 血量检测器()
        检测器.设置区域((10, 10, 100, 20))
        
        血量 = 检测器.检测(图像)
        置信度 = 检测器.获取置信度()
        
        assert 0.0 <= 血量 <= 1.0, \
            f"血量百分比应在 [0.0, 1.0] 范围内，实际: {血量}"
        assert 0.0 <= 置信度 <= 1.0, \
            f"血量置信度应在 [0.0, 1.0] 范围内，实际: {置信度}"

    @settings(max_examples=100, deadline=10000)
    @given(图像=随机BGR图像(宽度=200, 高度=100))
    def test_蓝量检测器返回值范围(self, 图像: np.ndarray):
        """
        属性测试: 蓝量检测器返回的百分比应在 [0.0, 1.0] 范围内
        
        Feature: health-mana-detection, Property 1: 检测值范围
        **验证: 需求 3.3**
        """
        检测器 = 蓝量检测器()
        检测器.设置区域((10, 10, 100, 15))
        
        蓝量 = 检测器.检测(图像)
        置信度 = 检测器.获取置信度()
        
        assert 0.0 <= 蓝量 <= 1.0, \
            f"蓝量百分比应在 [0.0, 1.0] 范围内，实际: {蓝量}"
        assert 0.0 <= 置信度 <= 1.0, \
            f"蓝量置信度应在 [0.0, 1.0] 范围内，实际: {置信度}"

    @settings(max_examples=100, deadline=10000)
    @given(图像=随机BGR图像(宽度=300, 高度=150))
    def test_状态检测器返回值范围(self, 图像: np.ndarray):
        """
        属性测试: 状态检测器返回的所有百分比和置信度应在 [0.0, 1.0] 范围内
        
        Feature: health-mana-detection, Property 1: 检测值范围
        **验证: 需求 2.5, 3.3**
        """
        配置 = {
            "血条": {"区域": (10, 10, 100, 20)},
            "蓝条": {"区域": (10, 40, 100, 15)}
        }
        检测器 = 状态检测器(配置)
        
        结果 = 检测器.检测(图像)
        
        assert isinstance(结果, 状态检测结果), \
            f"返回类型应为状态检测结果，实际: {type(结果)}"
        
        assert 0.0 <= 结果.血量百分比 <= 1.0, \
            f"血量百分比应在 [0.0, 1.0] 范围内，实际: {结果.血量百分比}"
        assert 0.0 <= 结果.蓝量百分比 <= 1.0, \
            f"蓝量百分比应在 [0.0, 1.0] 范围内，实际: {结果.蓝量百分比}"
        assert 0.0 <= 结果.血量置信度 <= 1.0, \
            f"血量置信度应在 [0.0, 1.0] 范围内，实际: {结果.血量置信度}"
        assert 0.0 <= 结果.蓝量置信度 <= 1.0, \
            f"蓝量置信度应在 [0.0, 1.0] 范围内，实际: {结果.蓝量置信度}"

    @settings(max_examples=100, deadline=10000)
    @given(值=有效平滑值())
    def test_平滑器返回值范围(self, 值: float):
        """
        属性测试: 平滑器返回的值应在 [0.0, 1.0] 范围内
        
        Feature: health-mana-detection, Property 1: 检测值范围
        **验证: 需求 2.5**
        """
        平滑器实例 = 平滑器()
        
        平滑值 = 平滑器实例.平滑(值)
        
        assert 0.0 <= 平滑值 <= 1.0, \
            f"平滑后的值应在 [0.0, 1.0] 范围内，输入: {值}，输出: {平滑值}"

    @settings(max_examples=100, deadline=10000)
    @given(值序列=st.lists(有效平滑值(), min_size=1, max_size=20))
    def test_连续平滑返回值范围(self, 值序列: list):
        """
        属性测试: 连续平滑处理后的所有值应在 [0.0, 1.0] 范围内
        
        Feature: health-mana-detection, Property 1: 检测值范围
        **验证: 需求 2.5**
        """
        平滑器实例 = 平滑器()
        
        for i, 值 in enumerate(值序列):
            平滑值 = 平滑器实例.平滑(值)
            assert 0.0 <= 平滑值 <= 1.0, \
                f"第 {i+1} 次平滑后的值应在 [0.0, 1.0] 范围内，输入: {值}，输出: {平滑值}"


# ==================== 边界情况测试 ====================

class Test检测值范围边界情况:
    """边界情况测试"""

    def test_空图像返回默认值(self):
        """测试空图像返回默认值且在有效范围内"""
        分析器 = 状态条分析器()
        
        # 空图像
        空图像 = np.array([], dtype=np.uint8).reshape(0, 0, 3)
        百分比, 置信度 = 分析器.分析(空图像)
        
        assert 0.0 <= 百分比 <= 1.0
        assert 0.0 <= 置信度 <= 1.0

    def test_None图像返回默认值(self):
        """测试 None 图像返回默认值且在有效范围内"""
        分析器 = 状态条分析器()
        
        百分比, 置信度 = 分析器.分析(None)
        
        assert 0.0 <= 百分比 <= 1.0
        assert 0.0 <= 置信度 <= 1.0

    def test_灰度图像返回值范围(self):
        """测试灰度图像返回值在有效范围内"""
        分析器 = 状态条分析器()
        
        # 灰度图像
        灰度图像 = np.random.randint(0, 256, (20, 100), dtype=np.uint8)
        百分比, 置信度 = 分析器.分析(灰度图像)
        
        assert 0.0 <= 百分比 <= 1.0
        assert 0.0 <= 置信度 <= 1.0

    def test_未配置区域血量检测器返回满血(self):
        """测试未配置区域时血量检测器返回 1.0"""
        检测器 = 血量检测器()
        图像 = np.random.randint(0, 256, (100, 200, 3), dtype=np.uint8)
        
        血量 = 检测器.检测(图像)
        
        assert 血量 == 1.0, f"未配置区域时应返回 1.0，实际: {血量}"

    def test_未配置区域蓝量检测器返回满蓝(self):
        """测试未配置区域时蓝量检测器返回 1.0（需求 3.4）"""
        检测器 = 蓝量检测器()
        图像 = np.random.randint(0, 256, (100, 200, 3), dtype=np.uint8)
        
        蓝量 = 检测器.检测(图像)
        
        assert 蓝量 == 1.0, f"未配置区域时应返回 1.0，实际: {蓝量}"

    def test_极小图像返回值范围(self):
        """测试极小图像返回值在有效范围内"""
        分析器 = 状态条分析器()
        
        # 1x1 图像
        极小图像 = np.array([[[128, 128, 128]]], dtype=np.uint8)
        百分比, 置信度 = 分析器.分析(极小图像)
        
        assert 0.0 <= 百分比 <= 1.0
        assert 0.0 <= 置信度 <= 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])
