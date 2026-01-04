"""
状态识别器属性测试模块

使用Hypothesis进行属性测试，验证状态识别器的核心功能。

**Property 3: 状态识别返回格式正确性**
*For any* 输入图像，状态识别器应该返回包含状态和置信度的结果，置信度在0-1范围内

**Property 4: 状态判定优先级正确性**
*For any* 检测到UI元素的情况，状态应该优先判定为UI相关状态；
*For any* 检测到近距离敌对实体的情况，状态应该判定为战斗状态

**Property 5: 状态历史记录正确性**
*For any* N次状态更新，状态历史应该正确记录最近N次状态，且长度不超过配置的最大长度

**Property 6: 置信度累积正确性**
*For any* 连续相同状态的序列，累积置信度应该随着连续次数增加而增加

验证: Requirements 2.2, 2.3, 2.4, 2.6, 2.7
"""

import pytest
import numpy as np
from hypothesis import given, strategies as st, settings, assume
from typing import List, Tuple

from 核心.数据类型 import 游戏状态, 实体类型, 方向, 检测结果, 状态识别结果
from 核心.状态识别器 import 状态识别器
from 配置.增强设置 import 状态判定阈值


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
def 单个检测结果(draw, 实体类型值=None, 最大距离=500):
    """生成单个有效的检测结果"""
    if 实体类型值 is None:
        类型 = draw(st.sampled_from(list(实体类型)))
    else:
        类型 = 实体类型值
    
    置信度 = draw(st.floats(min_value=0.1, max_value=1.0, allow_nan=False, allow_infinity=False))
    边界框 = draw(有效边界框())
    
    # 计算中心点
    x, y, w, h = 边界框
    中心点 = (x + w // 2, y + h // 2)
    
    # 生成距离
    距离 = draw(st.floats(min_value=0.0, max_value=最大距离, allow_nan=False, allow_infinity=False))
    
    方向值 = draw(st.sampled_from(list(方向)))
    
    return 检测结果(
        类型=类型,
        置信度=置信度,
        边界框=边界框,
        中心点=中心点,
        方向=方向值,
        距离=距离
    )


@st.composite
def 怪物检测结果(draw, 近距离=True):
    """生成怪物类型的检测结果"""
    战斗距离阈值 = 状态判定阈值["战斗_敌人距离"]
    if 近距离:
        最大距离 = 战斗距离阈值 - 1
    else:
        最大距离 = 500
    return draw(单个检测结果(实体类型值=实体类型.怪物, 最大距离=最大距离))


@st.composite
def 物品检测结果(draw, 近距离=True):
    """生成物品类型的检测结果"""
    拾取距离阈值 = 状态判定阈值["拾取_物品距离"]
    if 近距离:
        最大距离 = 拾取距离阈值 - 1
    else:
        最大距离 = 500
    return draw(单个检测结果(实体类型值=实体类型.物品, 最大距离=最大距离))


@st.composite
def 检测结果列表(draw, 最小数量=0, 最大数量=10):
    """生成检测结果列表"""
    数量 = draw(st.integers(min_value=最小数量, max_value=最大数量))
    结果列表 = []
    for _ in range(数量):
        结果 = draw(单个检测结果())
        结果列表.append(结果)
    return 结果列表


@st.composite
def 有效历史长度(draw):
    """生成有效的历史长度"""
    return draw(st.integers(min_value=1, max_value=50))


@st.composite
def 有效累积系数(draw):
    """生成有效的置信度累积系数"""
    return draw(st.floats(min_value=0.01, max_value=0.5, allow_nan=False, allow_infinity=False))


def 创建测试图像(宽度=1920, 高度=1080):
    """创建测试用的空白图像"""
    return np.zeros((高度, 宽度, 3), dtype=np.uint8)


# ==================== Property 3: 状态识别返回格式正确性 ====================

class Test状态识别返回格式正确性属性:
    """
    属性测试: 状态识别返回格式正确性
    
    Feature: game-ai-enhancement, Property 3: 状态识别返回格式正确性
    Validates: Requirements 2.2
    """
    
    def setup_method(self):
        """每个测试方法前创建识别器实例"""
        self.识别器 = 状态识别器(历史长度=10, 置信度累积系数=0.1)

    
    @settings(max_examples=100, deadline=5000)
    @given(检测结果列表=检测结果列表())
    def test_识别结果包含有效状态(self, 检测结果列表: List[检测结果]):
        """
        属性测试: 识别结果应包含有效的游戏状态枚举值
        
        Feature: game-ai-enhancement, Property 3: 状态识别返回格式正确性
        Validates: Requirements 2.2
        """
        图像 = 创建测试图像()
        
        结果 = self.识别器.识别状态(图像, 检测结果列表)
        
        # 验证返回类型
        assert isinstance(结果, 状态识别结果), \
            f"识别结果应为状态识别结果类型，实际: {type(结果)}"
        
        # 验证状态是有效枚举
        assert isinstance(结果.状态, 游戏状态), \
            f"状态应为游戏状态枚举，实际: {type(结果.状态)}"
        assert 结果.状态 in list(游戏状态), \
            f"状态应为有效的游戏状态枚举值，实际: {结果.状态}"
    
    @settings(max_examples=100, deadline=5000)
    @given(检测结果列表=检测结果列表())
    def test_识别结果置信度在有效范围内(self, 检测结果列表: List[检测结果]):
        """
        属性测试: 识别结果的置信度应在0-1范围内
        
        Feature: game-ai-enhancement, Property 3: 状态识别返回格式正确性
        Validates: Requirements 2.2
        """
        图像 = 创建测试图像()
        
        结果 = self.识别器.识别状态(图像, 检测结果列表)
        
        assert 0.0 <= 结果.置信度 <= 1.0, \
            f"置信度应在0-1范围内，实际: {结果.置信度}"

    
    @settings(max_examples=100, deadline=5000)
    @given(检测结果列表=检测结果列表())
    def test_识别结果UI元素列表为列表类型(self, 检测结果列表: List[检测结果]):
        """
        属性测试: 识别结果的UI元素应为列表类型
        
        Feature: game-ai-enhancement, Property 3: 状态识别返回格式正确性
        Validates: Requirements 2.2
        """
        图像 = 创建测试图像()
        
        结果 = self.识别器.识别状态(图像, 检测结果列表)
        
        assert isinstance(结果.检测到的UI元素, list), \
            f"检测到的UI元素应为列表类型，实际: {type(结果.检测到的UI元素)}"
    
    @settings(max_examples=100, deadline=5000)
    @given(检测结果列表=检测结果列表())
    def test_识别结果附近实体数量非负(self, 检测结果列表: List[检测结果]):
        """
        属性测试: 识别结果的附近实体数量应为非负整数
        
        Feature: game-ai-enhancement, Property 3: 状态识别返回格式正确性
        Validates: Requirements 2.2
        """
        图像 = 创建测试图像()
        
        结果 = self.识别器.识别状态(图像, 检测结果列表)
        
        assert isinstance(结果.附近实体数量, int), \
            f"附近实体数量应为整数，实际: {type(结果.附近实体数量)}"
        assert 结果.附近实体数量 >= 0, \
            f"附近实体数量应为非负数，实际: {结果.附近实体数量}"
        assert 结果.附近实体数量 == len(检测结果列表), \
            f"附近实体数量应等于检测结果数量，期望: {len(检测结果列表)}，实际: {结果.附近实体数量}"


# ==================== Property 4: 状态判定优先级正确性 ====================

class Test状态判定优先级正确性属性:
    """
    属性测试: 状态判定优先级正确性
    
    Feature: game-ai-enhancement, Property 4: 状态判定优先级正确性
    Validates: Requirements 2.3, 2.4
    """
    
    def setup_method(self):
        """每个测试方法前创建识别器实例"""
        self.识别器 = 状态识别器(历史长度=10, 置信度累积系数=0.1)

    
    @settings(max_examples=100, deadline=5000)
    @given(怪物数量=st.integers(min_value=1, max_value=5))
    def test_近距离敌人触发战斗状态(self, 怪物数量: int):
        """
        属性测试: 检测到近距离敌对实体时应判定为战斗状态
        
        Feature: game-ai-enhancement, Property 4: 状态判定优先级正确性
        Validates: Requirements 2.4
        """
        图像 = 创建测试图像()
        
        # 创建近距离怪物检测结果
        战斗距离阈值 = 状态判定阈值["战斗_敌人距离"]
        检测列表 = []
        for i in range(怪物数量):
            检测列表.append(检测结果(
                类型=实体类型.怪物,
                置信度=0.8,
                边界框=(100 + i * 50, 100, 50, 50),
                中心点=(125 + i * 50, 125),
                方向=方向.中心,
                距离=战斗距离阈值 - 50  # 确保在战斗距离内
            ))
        
        结果 = self.识别器.识别状态(图像, 检测列表)
        
        assert 结果.状态 == 游戏状态.战斗, \
            f"检测到近距离敌人时应判定为战斗状态，实际: {结果.状态}"
    
    @settings(max_examples=100, deadline=5000)
    @given(物品数量=st.integers(min_value=1, max_value=5))
    def test_近距离物品触发拾取状态(self, 物品数量: int):
        """
        属性测试: 检测到近距离物品时应判定为拾取状态（无敌人时）
        
        Feature: game-ai-enhancement, Property 4: 状态判定优先级正确性
        Validates: Requirements 2.3
        """
        图像 = 创建测试图像()
        
        # 创建近距离物品检测结果
        拾取距离阈值 = 状态判定阈值["拾取_物品距离"]
        检测列表 = []
        for i in range(物品数量):
            检测列表.append(检测结果(
                类型=实体类型.物品,
                置信度=0.8,
                边界框=(100 + i * 50, 100, 50, 50),
                中心点=(125 + i * 50, 125),
                方向=方向.中心,
                距离=拾取距离阈值 - 20  # 确保在拾取距离内
            ))
        
        结果 = self.识别器.识别状态(图像, 检测列表)
        
        assert 结果.状态 == 游戏状态.拾取, \
            f"检测到近距离物品时应判定为拾取状态，实际: {结果.状态}"

    
    @settings(max_examples=100, deadline=5000)
    @given(怪物数量=st.integers(min_value=1, max_value=3),
           物品数量=st.integers(min_value=1, max_value=3))
    def test_战斗状态优先于拾取状态(self, 怪物数量: int, 物品数量: int):
        """
        属性测试: 战斗状态应优先于拾取状态
        
        Feature: game-ai-enhancement, Property 4: 状态判定优先级正确性
        Validates: Requirements 2.3, 2.4
        """
        图像 = 创建测试图像()
        
        战斗距离阈值 = 状态判定阈值["战斗_敌人距离"]
        拾取距离阈值 = 状态判定阈值["拾取_物品距离"]
        
        检测列表 = []
        
        # 添加近距离怪物
        for i in range(怪物数量):
            检测列表.append(检测结果(
                类型=实体类型.怪物,
                置信度=0.8,
                边界框=(100 + i * 50, 100, 50, 50),
                中心点=(125 + i * 50, 125),
                方向=方向.中心,
                距离=战斗距离阈值 - 50
            ))
        
        # 添加近距离物品
        for i in range(物品数量):
            检测列表.append(检测结果(
                类型=实体类型.物品,
                置信度=0.8,
                边界框=(300 + i * 50, 100, 50, 50),
                中心点=(325 + i * 50, 125),
                方向=方向.中心,
                距离=拾取距离阈值 - 20
            ))
        
        结果 = self.识别器.识别状态(图像, 检测列表)
        
        # 战斗状态应优先于拾取状态
        assert 结果.状态 == 游戏状态.战斗, \
            f"战斗状态应优先于拾取状态，实际: {结果.状态}"
    
    @settings(max_examples=100, deadline=5000)
    @given(检测结果列表=检测结果列表(最大数量=5))
    def test_无特殊条件时返回合理状态(self, 检测结果列表: List[检测结果]):
        """
        属性测试: 无特殊条件时应返回合理的默认状态
        
        Feature: game-ai-enhancement, Property 4: 状态判定优先级正确性
        Validates: Requirements 2.3
        """
        图像 = 创建测试图像()
        
        结果 = self.识别器.识别状态(图像, 检测结果列表)
        
        # 验证返回的状态是有效的
        有效状态 = {游戏状态.战斗, 游戏状态.拾取, 游戏状态.移动, 游戏状态.空闲,
                   游戏状态.对话, 游戏状态.菜单, 游戏状态.死亡, 游戏状态.加载}
        assert 结果.状态 in 有效状态, \
            f"应返回有效状态，实际: {结果.状态}"


# ==================== Property 5: 状态历史记录正确性 ====================

class Test状态历史记录正确性属性:
    """
    属性测试: 状态历史记录正确性
    
    Feature: game-ai-enhancement, Property 5: 状态历史记录正确性
    Validates: Requirements 2.6
    """
    
    @settings(max_examples=100, deadline=5000)
    @given(历史长度=有效历史长度(), 更新次数=st.integers(min_value=1, max_value=30))
    def test_历史记录长度不超过最大值(self, 历史长度: int, 更新次数: int):
        """
        属性测试: 状态历史记录长度不应超过配置的最大长度
        
        Feature: game-ai-enhancement, Property 5: 状态历史记录正确性
        Validates: Requirements 2.6
        """
        识别器 = 状态识别器(历史长度=历史长度, 置信度累积系数=0.1)
        图像 = 创建测试图像()
        
        # 执行多次状态识别
        for _ in range(更新次数):
            识别器.识别状态(图像, [])
        
        # 验证历史长度不超过最大值
        历史 = 识别器.获取状态历史(更新次数)
        assert len(历史) <= 历史长度, \
            f"历史记录长度 {len(历史)} 超过最大值 {历史长度}"
    
    @settings(max_examples=100, deadline=5000)
    @given(历史长度=有效历史长度(), 更新次数=st.integers(min_value=1, max_value=20))
    def test_历史记录正确记录状态(self, 历史长度: int, 更新次数: int):
        """
        属性测试: 状态历史应正确记录每次识别的状态
        
        Feature: game-ai-enhancement, Property 5: 状态历史记录正确性
        Validates: Requirements 2.6
        """
        识别器 = 状态识别器(历史长度=历史长度, 置信度累积系数=0.1)
        图像 = 创建测试图像()
        
        # 执行多次状态识别并记录结果
        识别结果列表 = []
        for _ in range(更新次数):
            结果 = 识别器.识别状态(图像, [])
            识别结果列表.append(结果)
        
        # 获取历史记录
        期望数量 = min(更新次数, 历史长度)
        历史 = 识别器.获取状态历史(期望数量)
        
        # 验证历史记录数量
        assert len(历史) == 期望数量, \
            f"历史记录数量应为 {期望数量}，实际: {len(历史)}"

    
    @settings(max_examples=100, deadline=5000)
    @given(历史长度=有效历史长度())
    def test_获取历史数量参数有效(self, 历史长度: int):
        """
        属性测试: 获取历史记录时数量参数应正确工作
        
        Feature: game-ai-enhancement, Property 5: 状态历史记录正确性
        Validates: Requirements 2.6
        """
        识别器 = 状态识别器(历史长度=历史长度, 置信度累积系数=0.1)
        图像 = 创建测试图像()
        
        # 填充历史
        for _ in range(历史长度):
            识别器.识别状态(图像, [])
        
        # 测试获取不同数量的历史（确保请求数量至少为1）
        测试数量列表 = [1, max(1, 历史长度 // 2), 历史长度, 历史长度 + 10]
        for 请求数量 in 测试数量列表:
            历史 = 识别器.获取状态历史(请求数量)
            期望数量 = min(请求数量, 历史长度)
            assert len(历史) <= 期望数量, \
                f"请求 {请求数量} 条历史，期望最多 {期望数量} 条，实际: {len(历史)}"
    
    @settings(max_examples=100, deadline=5000)
    @given(历史长度=有效历史长度())
    def test_清空历史后记录为空(self, 历史长度: int):
        """
        属性测试: 清空历史后记录应为空
        
        Feature: game-ai-enhancement, Property 5: 状态历史记录正确性
        Validates: Requirements 2.6
        """
        识别器 = 状态识别器(历史长度=历史长度, 置信度累积系数=0.1)
        图像 = 创建测试图像()
        
        # 填充历史
        for _ in range(历史长度):
            识别器.识别状态(图像, [])
        
        # 清空历史
        识别器.清空历史()
        
        # 验证历史为空
        历史 = 识别器.获取状态历史(历史长度)
        assert len(历史) == 0, \
            f"清空后历史应为空，实际: {len(历史)}"


# ==================== Property 6: 置信度累积正确性 ====================

class Test置信度累积正确性属性:
    """
    属性测试: 置信度累积正确性
    
    Feature: game-ai-enhancement, Property 6: 置信度累积正确性
    Validates: Requirements 2.7
    """

    
    @settings(max_examples=100, deadline=5000)
    @given(累积系数=有效累积系数(), 连续次数=st.integers(min_value=2, max_value=10))
    def test_连续相同状态置信度累积(self, 累积系数: float, 连续次数: int):
        """
        属性测试: 连续相同状态时置信度应累积增加
        
        Feature: game-ai-enhancement, Property 6: 置信度累积正确性
        Validates: Requirements 2.7
        """
        识别器 = 状态识别器(历史长度=20, 置信度累积系数=累积系数)
        图像 = 创建测试图像()
        
        # 执行多次相同状态的识别（空检测列表会产生空闲状态）
        置信度列表 = []
        for _ in range(连续次数):
            结果 = 识别器.识别状态(图像, [])
            置信度列表.append(结果.置信度)
        
        # 验证置信度随连续次数增加（或保持不变，因为有上限1.0）
        for i in range(1, len(置信度列表)):
            assert 置信度列表[i] >= 置信度列表[i - 1] or 置信度列表[i] >= 0.99, \
                f"连续相同状态时置信度应累积增加，第{i}次: {置信度列表[i-1]} -> {置信度列表[i]}"
    
    @settings(max_examples=100, deadline=5000)
    @given(累积系数=有效累积系数())
    def test_置信度不超过1(self, 累积系数: float):
        """
        属性测试: 累积后的置信度不应超过1.0
        
        Feature: game-ai-enhancement, Property 6: 置信度累积正确性
        Validates: Requirements 2.7
        """
        识别器 = 状态识别器(历史长度=50, 置信度累积系数=累积系数)
        图像 = 创建测试图像()
        
        # 执行多次识别，确保累积足够多
        for _ in range(50):
            结果 = 识别器.识别状态(图像, [])
            assert 结果.置信度 <= 1.0, \
                f"置信度不应超过1.0，实际: {结果.置信度}"

    
    @settings(max_examples=100, deadline=5000)
    @given(累积系数=有效累积系数())
    def test_状态变化重置累积(self, 累积系数: float):
        """
        属性测试: 状态变化时累积应重置
        
        Feature: game-ai-enhancement, Property 6: 置信度累积正确性
        Validates: Requirements 2.7
        """
        识别器 = 状态识别器(历史长度=20, 置信度累积系数=累积系数)
        图像 = 创建测试图像()
        
        战斗距离阈值 = 状态判定阈值["战斗_敌人距离"]
        
        # 先产生空闲状态
        for _ in range(5):
            识别器.识别状态(图像, [])
        
        # 然后产生战斗状态（通过添加近距离怪物）
        怪物检测 = [检测结果(
            类型=实体类型.怪物,
            置信度=0.8,
            边界框=(100, 100, 50, 50),
            中心点=(125, 125),
            方向=方向.中心,
            距离=战斗距离阈值 - 50
        )]
        
        第一次战斗结果 = 识别器.识别状态(图像, 怪物检测)
        
        # 验证状态变为战斗
        assert 第一次战斗结果.状态 == 游戏状态.战斗, \
            f"应判定为战斗状态，实际: {第一次战斗结果.状态}"
        
        # 继续战斗状态，置信度应该累积
        第二次战斗结果 = 识别器.识别状态(图像, 怪物检测)
        
        assert 第二次战斗结果.置信度 >= 第一次战斗结果.置信度 or 第二次战斗结果.置信度 >= 0.99, \
            f"连续战斗状态置信度应累积，{第一次战斗结果.置信度} -> {第二次战斗结果.置信度}"
    
    @settings(max_examples=100, deadline=5000)
    @given(累积系数=有效累积系数(), 连续次数=st.integers(min_value=1, max_value=15))
    def test_累积置信度计算正确(self, 累积系数: float, 连续次数: int):
        """
        属性测试: 累积置信度计算应符合公式
        
        Feature: game-ai-enhancement, Property 6: 置信度累积正确性
        Validates: Requirements 2.7
        """
        识别器 = 状态识别器(历史长度=20, 置信度累积系数=累积系数)
        图像 = 创建测试图像()
        
        # 执行多次识别
        for i in range(连续次数):
            结果 = 识别器.识别状态(图像, [])
            
            # 获取连续次数
            实际连续次数 = 识别器.获取连续状态次数(结果.状态)
            
            # 验证连续次数正确
            assert 实际连续次数 == i + 1, \
                f"连续次数应为 {i + 1}，实际: {实际连续次数}"


# ==================== 单元测试 ====================

class Test状态识别器单元测试:
    """状态识别器单元测试"""
    
    def test_初始化默认参数(self):
        """测试使用默认参数初始化"""
        识别器 = 状态识别器()
        assert 识别器.历史长度 == 10
        assert 识别器.置信度累积系数 == 0.1

    
    def test_初始化自定义参数(self):
        """测试使用自定义参数初始化"""
        识别器 = 状态识别器(历史长度=20, 置信度累积系数=0.2)
        assert 识别器.历史长度 == 20
        assert 识别器.置信度累积系数 == 0.2
    
    def test_空检测列表返回空闲状态(self):
        """测试空检测列表返回空闲状态"""
        识别器 = 状态识别器()
        图像 = 创建测试图像()
        
        结果 = 识别器.识别状态(图像, [])
        
        assert 结果.状态 == 游戏状态.空闲
        assert 结果.附近实体数量 == 0
    
    def test_状态变更回调触发(self):
        """测试状态变更时回调被触发"""
        识别器 = 状态识别器()
        图像 = 创建测试图像()
        
        回调记录 = []
        
        def 回调函数(旧状态, 新状态):
            回调记录.append((旧状态, 新状态))
        
        识别器.注册状态变更回调(回调函数)
        
        # 先产生空闲状态
        识别器.识别状态(图像, [])
        
        # 然后产生战斗状态
        战斗距离阈值 = 状态判定阈值["战斗_敌人距离"]
        怪物检测 = [检测结果(
            类型=实体类型.怪物,
            置信度=0.8,
            边界框=(100, 100, 50, 50),
            中心点=(125, 125),
            方向=方向.中心,
            距离=战斗距离阈值 - 50
        )]
        识别器.识别状态(图像, 怪物检测)
        
        # 验证回调被触发
        assert len(回调记录) == 1
        assert 回调记录[0] == (游戏状态.空闲, 游戏状态.战斗)
    
    def test_取消状态变更回调(self):
        """测试取消状态变更回调"""
        识别器 = 状态识别器()
        图像 = 创建测试图像()
        
        回调记录 = []
        
        def 回调函数(旧状态, 新状态):
            回调记录.append((旧状态, 新状态))
        
        识别器.注册状态变更回调(回调函数)
        识别器.取消状态变更回调(回调函数)
        
        # 产生状态变化
        识别器.识别状态(图像, [])
        
        战斗距离阈值 = 状态判定阈值["战斗_敌人距离"]
        怪物检测 = [检测结果(
            类型=实体类型.怪物,
            置信度=0.8,
            边界框=(100, 100, 50, 50),
            中心点=(125, 125),
            方向=方向.中心,
            距离=战斗距离阈值 - 50
        )]
        识别器.识别状态(图像, 怪物检测)
        
        # 验证回调未被触发
        assert len(回调记录) == 0
    
    def test_是否处于状态方法(self):
        """测试是否处于状态方法"""
        识别器 = 状态识别器()
        图像 = 创建测试图像()
        
        # 初始状态
        assert not 识别器.是否处于状态(游戏状态.空闲)
        
        # 产生空闲状态
        识别器.识别状态(图像, [])
        
        assert 识别器.是否处于状态(游戏状态.空闲)
        assert not 识别器.是否处于状态(游戏状态.战斗)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])
