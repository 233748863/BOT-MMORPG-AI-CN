"""
YOLO检测器属性测试模块

使用Hypothesis进行属性测试，验证YOLO检测器的后处理和方向计算功能。

**Property 1: 检测结果后处理正确性**
*For any* 检测结果列表和置信度阈值，经过后处理后的结果应该：
(1) 按置信度降序排列，(2) 所有结果的置信度都 >= 阈值

**Property 2: 方向计算正确性**
*For any* 实体中心点坐标和屏幕尺寸，计算出的方向应该正确反映实体相对于屏幕中心的位置

验证: Requirements 1.2, 1.3, 1.6
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from typing import List, Tuple

from 核心.数据类型 import 实体类型, 方向, 检测结果
from 核心.目标检测器 import YOLO检测器


# ==================== 策略定义 ====================

@st.composite
def 有效置信度(draw):
    """生成有效的置信度值 (0.0-1.0)"""
    return draw(st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False))


@st.composite
def 有效边界框(draw, 最大宽度=1920, 最大高度=1080):
    """生成有效的边界框 (x, y, width, height)"""
    x = draw(st.integers(min_value=0, max_value=最大宽度 - 10))
    y = draw(st.integers(min_value=0, max_value=最大高度 - 10))
    宽度 = draw(st.integers(min_value=10, max_value=min(200, 最大宽度 - x)))
    高度 = draw(st.integers(min_value=10, max_value=min(200, 最大高度 - y)))
    return (x, y, 宽度, 高度)


@st.composite
def 有效中心点(draw, 最大宽度=1920, 最大高度=1080):
    """生成有效的中心点坐标"""
    x = draw(st.integers(min_value=0, max_value=最大宽度))
    y = draw(st.integers(min_value=0, max_value=最大高度))
    return (x, y)


@st.composite
def 有效屏幕尺寸(draw):
    """生成有效的屏幕尺寸 (宽度, 高度)"""
    宽度 = draw(st.integers(min_value=640, max_value=3840))
    高度 = draw(st.integers(min_value=480, max_value=2160))
    return (宽度, 高度)


@st.composite
def 单个检测结果(draw, 最大宽度=1920, 最大高度=1080):
    """生成单个有效的检测结果"""
    类型 = draw(st.sampled_from(list(实体类型)))
    置信度 = draw(有效置信度())
    边界框 = draw(有效边界框(最大宽度, 最大高度))
    
    # 计算中心点
    x, y, w, h = 边界框
    中心点 = (x + w // 2, y + h // 2)
    
    # 计算方向和距离（使用屏幕中心）
    屏幕中心x = 最大宽度 // 2
    屏幕中心y = 最大高度 // 2
    dx = 中心点[0] - 屏幕中心x
    dy = 中心点[1] - 屏幕中心y
    距离 = (dx * dx + dy * dy) ** 0.5
    
    # 简单方向计算
    方向值 = 方向.中心
    
    return 检测结果(
        类型=类型,
        置信度=置信度,
        边界框=边界框,
        中心点=中心点,
        方向=方向值,
        距离=距离
    )


@st.composite
def 检测结果列表(draw, 最小数量=0, 最大数量=20):
    """生成检测结果列表"""
    数量 = draw(st.integers(min_value=最小数量, max_value=最大数量))
    结果列表 = []
    for _ in range(数量):
        结果 = draw(单个检测结果())
        结果列表.append(结果)
    return 结果列表


@st.composite
def 置信度阈值(draw):
    """生成置信度阈值"""
    return draw(st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False))


# ==================== Property 1: 检测结果后处理正确性 ====================

class Test检测结果后处理正确性属性:
    """
    属性测试: 检测结果后处理正确性
    
    Feature: game-ai-enhancement, Property 1: 检测结果后处理正确性
    Validates: Requirements 1.2, 1.3
    """
    
    @settings(max_examples=100, deadline=5000)
    @given(结果列表=检测结果列表(), 阈值=置信度阈值())
    def test_后处理结果按置信度降序排列(self, 结果列表: List[检测结果], 阈值: float):
        """
        属性测试: 后处理后的结果应按置信度降序排列
        
        Feature: game-ai-enhancement, Property 1: 检测结果后处理正确性
        Validates: Requirements 1.2
        """
        # 执行后处理
        处理后结果 = YOLO检测器.后处理(结果列表, 阈值)
        
        # 验证按置信度降序排列
        if len(处理后结果) > 1:
            for i in range(len(处理后结果) - 1):
                assert 处理后结果[i].置信度 >= 处理后结果[i + 1].置信度, \
                    f"结果未按置信度降序排列: {处理后结果[i].置信度} < {处理后结果[i + 1].置信度}"
    
    @settings(max_examples=100, deadline=5000)
    @given(结果列表=检测结果列表(), 阈值=置信度阈值())
    def test_后处理结果置信度都大于等于阈值(self, 结果列表: List[检测结果], 阈值: float):
        """
        属性测试: 后处理后的所有结果置信度都 >= 阈值
        
        Feature: game-ai-enhancement, Property 1: 检测结果后处理正确性
        Validates: Requirements 1.3
        """
        # 执行后处理
        处理后结果 = YOLO检测器.后处理(结果列表, 阈值)
        
        # 验证所有结果置信度 >= 阈值
        for 结果 in 处理后结果:
            assert 结果.置信度 >= 阈值, \
                f"结果置信度 {结果.置信度} 低于阈值 {阈值}"

    
    @settings(max_examples=100, deadline=5000)
    @given(结果列表=检测结果列表(), 阈值=置信度阈值())
    def test_后处理不增加结果数量(self, 结果列表: List[检测结果], 阈值: float):
        """
        属性测试: 后处理不应增加结果数量（只能过滤）
        
        Feature: game-ai-enhancement, Property 1: 检测结果后处理正确性
        Validates: Requirements 1.3
        """
        # 执行后处理
        处理后结果 = YOLO检测器.后处理(结果列表, 阈值)
        
        # 验证结果数量不增加
        assert len(处理后结果) <= len(结果列表), \
            f"后处理后结果数量 {len(处理后结果)} 超过原始数量 {len(结果列表)}"
    
    @settings(max_examples=100, deadline=5000)
    @given(结果列表=检测结果列表())
    def test_阈值为0时保留所有结果(self, 结果列表: List[检测结果]):
        """
        属性测试: 阈值为0时应保留所有结果
        
        Feature: game-ai-enhancement, Property 1: 检测结果后处理正确性
        Validates: Requirements 1.3
        """
        # 执行后处理，阈值为0
        处理后结果 = YOLO检测器.后处理(结果列表, 0.0)
        
        # 验证保留所有结果
        assert len(处理后结果) == len(结果列表), \
            f"阈值为0时应保留所有结果，期望 {len(结果列表)}，实际 {len(处理后结果)}"
    
    @settings(max_examples=100, deadline=5000)
    @given(结果列表=检测结果列表())
    def test_阈值为1时只保留置信度为1的结果(self, 结果列表: List[检测结果]):
        """
        属性测试: 阈值为1时只保留置信度为1的结果
        
        Feature: game-ai-enhancement, Property 1: 检测结果后处理正确性
        Validates: Requirements 1.3
        """
        # 执行后处理，阈值为1
        处理后结果 = YOLO检测器.后处理(结果列表, 1.0)
        
        # 验证只保留置信度为1的结果
        期望数量 = sum(1 for r in 结果列表 if r.置信度 >= 1.0)
        assert len(处理后结果) == 期望数量, \
            f"阈值为1时应只保留置信度为1的结果，期望 {期望数量}，实际 {len(处理后结果)}"


# ==================== Property 2: 方向计算正确性 ====================

class Test方向计算正确性属性:
    """
    属性测试: 方向计算正确性
    
    Feature: game-ai-enhancement, Property 2: 方向计算正确性
    Validates: Requirements 1.6
    """
    
    def setup_method(self):
        """每个测试方法前创建检测器实例"""
        # 创建检测器实例（不加载模型）
        self.检测器 = YOLO检测器(模型路径="不存在的模型.pt")
    
    @settings(max_examples=100, deadline=5000)
    @given(屏幕尺寸=有效屏幕尺寸())
    def test_屏幕中心点返回中心方向(self, 屏幕尺寸: Tuple[int, int]):
        """
        属性测试: 屏幕中心点应返回中心方向
        
        Feature: game-ai-enhancement, Property 2: 方向计算正确性
        Validates: Requirements 1.6
        """
        宽度, 高度 = 屏幕尺寸
        中心点 = (宽度 // 2, 高度 // 2)
        
        计算方向 = self.检测器.计算方向(中心点, 屏幕尺寸)
        
        assert 计算方向 == 方向.中心, \
            f"屏幕中心点应返回中心方向，实际: {计算方向}"
    
    @settings(max_examples=100, deadline=5000)
    @given(屏幕尺寸=有效屏幕尺寸())
    def test_左侧点返回左方向(self, 屏幕尺寸: Tuple[int, int]):
        """
        属性测试: 屏幕左侧点应返回包含"左"的方向
        
        Feature: game-ai-enhancement, Property 2: 方向计算正确性
        Validates: Requirements 1.6
        """
        宽度, 高度 = 屏幕尺寸
        # 左侧点（x远小于中心，y接近中心）
        中心点 = (宽度 // 10, 高度 // 2)
        
        计算方向 = self.检测器.计算方向(中心点, 屏幕尺寸)
        
        左方向集合 = {方向.左, 方向.左上, 方向.左下}
        assert 计算方向 in 左方向集合, \
            f"屏幕左侧点应返回左方向，实际: {计算方向}"

    
    @settings(max_examples=100, deadline=5000)
    @given(屏幕尺寸=有效屏幕尺寸())
    def test_右侧点返回右方向(self, 屏幕尺寸: Tuple[int, int]):
        """
        属性测试: 屏幕右侧点应返回包含"右"的方向
        
        Feature: game-ai-enhancement, Property 2: 方向计算正确性
        Validates: Requirements 1.6
        """
        宽度, 高度 = 屏幕尺寸
        # 右侧点（x远大于中心，y接近中心）
        中心点 = (宽度 * 9 // 10, 高度 // 2)
        
        计算方向 = self.检测器.计算方向(中心点, 屏幕尺寸)
        
        右方向集合 = {方向.右, 方向.右上, 方向.右下}
        assert 计算方向 in 右方向集合, \
            f"屏幕右侧点应返回右方向，实际: {计算方向}"
    
    @settings(max_examples=100, deadline=5000)
    @given(屏幕尺寸=有效屏幕尺寸())
    def test_上方点返回上方向(self, 屏幕尺寸: Tuple[int, int]):
        """
        属性测试: 屏幕上方点应返回包含"上"的方向
        
        Feature: game-ai-enhancement, Property 2: 方向计算正确性
        Validates: Requirements 1.6
        """
        宽度, 高度 = 屏幕尺寸
        # 上方点（y远小于中心，x接近中心）
        中心点 = (宽度 // 2, 高度 // 10)
        
        计算方向 = self.检测器.计算方向(中心点, 屏幕尺寸)
        
        上方向集合 = {方向.上, 方向.左上, 方向.右上}
        assert 计算方向 in 上方向集合, \
            f"屏幕上方点应返回上方向，实际: {计算方向}"
    
    @settings(max_examples=100, deadline=5000)
    @given(屏幕尺寸=有效屏幕尺寸())
    def test_下方点返回下方向(self, 屏幕尺寸: Tuple[int, int]):
        """
        属性测试: 屏幕下方点应返回包含"下"的方向
        
        Feature: game-ai-enhancement, Property 2: 方向计算正确性
        Validates: Requirements 1.6
        """
        宽度, 高度 = 屏幕尺寸
        # 下方点（y远大于中心，x接近中心）
        中心点 = (宽度 // 2, 高度 * 9 // 10)
        
        计算方向 = self.检测器.计算方向(中心点, 屏幕尺寸)
        
        下方向集合 = {方向.下, 方向.左下, 方向.右下}
        assert 计算方向 in 下方向集合, \
            f"屏幕下方点应返回下方向，实际: {计算方向}"

    
    @settings(max_examples=100, deadline=5000)
    @given(屏幕尺寸=有效屏幕尺寸())
    def test_左上角点返回左上方向(self, 屏幕尺寸: Tuple[int, int]):
        """
        属性测试: 屏幕左上角点应返回左上方向
        
        Feature: game-ai-enhancement, Property 2: 方向计算正确性
        Validates: Requirements 1.6
        """
        宽度, 高度 = 屏幕尺寸
        # 左上角点
        中心点 = (宽度 // 10, 高度 // 10)
        
        计算方向 = self.检测器.计算方向(中心点, 屏幕尺寸)
        
        assert 计算方向 == 方向.左上, \
            f"屏幕左上角点应返回左上方向，实际: {计算方向}"
    
    @settings(max_examples=100, deadline=5000)
    @given(屏幕尺寸=有效屏幕尺寸())
    def test_右上角点返回右上方向(self, 屏幕尺寸: Tuple[int, int]):
        """
        属性测试: 屏幕右上角点应返回右上方向
        
        Feature: game-ai-enhancement, Property 2: 方向计算正确性
        Validates: Requirements 1.6
        """
        宽度, 高度 = 屏幕尺寸
        # 右上角点
        中心点 = (宽度 * 9 // 10, 高度 // 10)
        
        计算方向 = self.检测器.计算方向(中心点, 屏幕尺寸)
        
        assert 计算方向 == 方向.右上, \
            f"屏幕右上角点应返回右上方向，实际: {计算方向}"
    
    @settings(max_examples=100, deadline=5000)
    @given(屏幕尺寸=有效屏幕尺寸())
    def test_左下角点返回左下方向(self, 屏幕尺寸: Tuple[int, int]):
        """
        属性测试: 屏幕左下角点应返回左下方向
        
        Feature: game-ai-enhancement, Property 2: 方向计算正确性
        Validates: Requirements 1.6
        """
        宽度, 高度 = 屏幕尺寸
        # 左下角点
        中心点 = (宽度 // 10, 高度 * 9 // 10)
        
        计算方向 = self.检测器.计算方向(中心点, 屏幕尺寸)
        
        assert 计算方向 == 方向.左下, \
            f"屏幕左下角点应返回左下方向，实际: {计算方向}"

    
    @settings(max_examples=100, deadline=5000)
    @given(屏幕尺寸=有效屏幕尺寸())
    def test_右下角点返回右下方向(self, 屏幕尺寸: Tuple[int, int]):
        """
        属性测试: 屏幕右下角点应返回右下方向
        
        Feature: game-ai-enhancement, Property 2: 方向计算正确性
        Validates: Requirements 1.6
        """
        宽度, 高度 = 屏幕尺寸
        # 右下角点
        中心点 = (宽度 * 9 // 10, 高度 * 9 // 10)
        
        计算方向 = self.检测器.计算方向(中心点, 屏幕尺寸)
        
        assert 计算方向 == 方向.右下, \
            f"屏幕右下角点应返回右下方向，实际: {计算方向}"
    
    @settings(max_examples=100, deadline=5000)
    @given(中心点=有效中心点(), 屏幕尺寸=有效屏幕尺寸())
    def test_方向计算返回有效方向枚举(self, 中心点: Tuple[int, int], 屏幕尺寸: Tuple[int, int]):
        """
        属性测试: 方向计算应始终返回有效的方向枚举值
        
        Feature: game-ai-enhancement, Property 2: 方向计算正确性
        Validates: Requirements 1.6
        """
        # 确保中心点在屏幕范围内
        宽度, 高度 = 屏幕尺寸
        x = min(中心点[0], 宽度 - 1)
        y = min(中心点[1], 高度 - 1)
        调整后中心点 = (x, y)
        
        计算方向 = self.检测器.计算方向(调整后中心点, 屏幕尺寸)
        
        # 验证返回值是有效的方向枚举
        assert isinstance(计算方向, 方向), \
            f"方向计算应返回方向枚举，实际类型: {type(计算方向)}"
        assert 计算方向 in list(方向), \
            f"方向计算应返回有效的方向枚举值，实际: {计算方向}"

    
    @settings(max_examples=100, deadline=5000)
    @given(屏幕尺寸=有效屏幕尺寸())
    def test_方向计算一致性(self, 屏幕尺寸: Tuple[int, int]):
        """
        属性测试: 相同输入应产生相同的方向输出
        
        Feature: game-ai-enhancement, Property 2: 方向计算正确性
        Validates: Requirements 1.6
        """
        宽度, 高度 = 屏幕尺寸
        中心点 = (宽度 // 3, 高度 // 3)
        
        方向1 = self.检测器.计算方向(中心点, 屏幕尺寸)
        方向2 = self.检测器.计算方向(中心点, 屏幕尺寸)
        
        assert 方向1 == 方向2, \
            f"相同输入应产生相同方向，但得到 {方向1} 和 {方向2}"


# ==================== 单元测试 ====================

class TestYOLO检测器单元测试:
    """YOLO检测器单元测试"""
    
    def test_后处理空列表(self):
        """测试后处理空列表"""
        结果 = YOLO检测器.后处理([], 0.5)
        assert 结果 == [], "空列表后处理应返回空列表"
    
    def test_后处理单个结果(self):
        """测试后处理单个结果"""
        单个结果 = 检测结果(
            类型=实体类型.怪物,
            置信度=0.8,
            边界框=(100, 100, 50, 50),
            中心点=(125, 125),
            方向=方向.中心,
            距离=0.0
        )
        
        # 阈值低于置信度，应保留
        结果 = YOLO检测器.后处理([单个结果], 0.5)
        assert len(结果) == 1
        
        # 阈值高于置信度，应过滤
        结果 = YOLO检测器.后处理([单个结果], 0.9)
        assert len(结果) == 0

    
    def test_后处理多个结果排序(self):
        """测试后处理多个结果的排序"""
        结果列表 = [
            检测结果(类型=实体类型.怪物, 置信度=0.5, 边界框=(0, 0, 10, 10),
                    中心点=(5, 5), 方向=方向.中心, 距离=0.0),
            检测结果(类型=实体类型.NPC, 置信度=0.9, 边界框=(20, 20, 10, 10),
                    中心点=(25, 25), 方向=方向.中心, 距离=0.0),
            检测结果(类型=实体类型.物品, 置信度=0.7, 边界框=(40, 40, 10, 10),
                    中心点=(45, 45), 方向=方向.中心, 距离=0.0),
        ]
        
        处理后 = YOLO检测器.后处理(结果列表, 0.0)
        
        # 验证按置信度降序排列
        assert 处理后[0].置信度 == 0.9
        assert 处理后[1].置信度 == 0.7
        assert 处理后[2].置信度 == 0.5
    
    def test_方向计算边界情况(self):
        """测试方向计算的边界情况"""
        检测器 = YOLO检测器(模型路径="不存在的模型.pt")
        屏幕尺寸 = (1920, 1080)
        
        # 测试边界点
        assert 检测器.计算方向((0, 0), 屏幕尺寸) == 方向.左上
        assert 检测器.计算方向((1919, 0), 屏幕尺寸) == 方向.右上
        assert 检测器.计算方向((0, 1079), 屏幕尺寸) == 方向.左下
        assert 检测器.计算方向((1919, 1079), 屏幕尺寸) == 方向.右下
    
    def test_检测器未加载模型状态(self):
        """测试检测器未加载模型时的状态"""
        检测器 = YOLO检测器(模型路径="不存在的模型.pt")
        
        assert not 检测器.是否已加载(), "不存在的模型路径应导致未加载状态"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])
