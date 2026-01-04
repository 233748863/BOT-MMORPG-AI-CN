# -*- coding: utf-8 -*-
"""
类型一致性属性测试模块

使用Hypothesis进行属性测试，验证配置值类型与模式定义的一致性。

**属性 1: 类型一致性**
*对于任意* 保存的配置值，其类型应与模式定义一致

**验证: 需求 4.3**
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from hypothesis import given, strategies as st, settings, assume
from typing import Any, Dict

from 核心.配置验证 import 配置验证器, 默认配置模式, 验证错误


# ==================== 策略定义 ====================

# 整数类型策略
整数策略 = st.integers(min_value=-10000, max_value=10000)

# 浮点数类型策略
浮点数策略 = st.floats(min_value=-10000.0, max_value=10000.0, allow_nan=False, allow_infinity=False)

# 字符串类型策略
字符串策略 = st.text(min_size=0, max_size=100)

# 布尔类型策略
布尔策略 = st.booleans()

# 路径类型策略（字符串）
路径策略 = st.text(min_size=1, max_size=200).filter(lambda x: x.strip() != "")

# 选项类型策略
选项策略 = st.sampled_from(["DEBUG", "INFO", "WARNING", "ERROR"])

# 错误类型策略（用于测试类型不匹配）
# 注意: 在 Python 中，bool 是 int 的子类，所以 isinstance(True, int) 返回 True
# 因此我们不将 bool 作为"错误的整数类型"
错误整数类型策略 = st.one_of(
    st.text(min_size=1, max_size=10),
    st.floats(allow_nan=False, allow_infinity=False).filter(lambda x: x != int(x) if x == x else True),
    st.lists(st.integers(), max_size=3),
)

# 注意: bool 在 Python 中也是 int 的子类，所以 bool 值也能通过 float 验证
错误浮点数类型策略 = st.one_of(
    st.text(min_size=1, max_size=10),
    st.lists(st.integers(), max_size=3),
)

错误字符串类型策略 = st.one_of(
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.booleans(),
    st.lists(st.integers(), max_size=3),
)

错误布尔类型策略 = st.one_of(
    st.integers().filter(lambda x: x not in (0, 1)),
    st.text(min_size=1, max_size=10).filter(lambda x: x.lower() not in ("true", "false")),
    st.lists(st.integers(), max_size=3),
)


class Test类型一致性属性:
    """
    类型一致性属性测试类
    
    **Feature: config-gui, 属性 1: 类型一致性**
    **验证: 需求 4.3**
    """
    
    @given(值=整数策略)
    @settings(max_examples=100, deadline=None)
    def test_整数类型验证_有效值应通过(self, 值: int):
        """
        属性测试: 对于任意整数值，int类型验证应通过
        
        **Feature: config-gui, 属性 1: 类型一致性**
        **验证: 需求 4.3**
        """
        验证器 = 配置验证器(默认配置模式)
        
        # 验证整数类型
        结果 = 验证器.验证类型(值, "int")
        
        assert 结果 is True, f"整数值 {值} 应通过 int 类型验证"
    
    @given(值=浮点数策略)
    @settings(max_examples=100, deadline=None)
    def test_浮点数类型验证_有效值应通过(self, 值: float):
        """
        属性测试: 对于任意浮点数值，float类型验证应通过
        
        **Feature: config-gui, 属性 1: 类型一致性**
        **验证: 需求 4.3**
        """
        验证器 = 配置验证器(默认配置模式)
        
        # 验证浮点数类型
        结果 = 验证器.验证类型(值, "float")
        
        assert 结果 is True, f"浮点数值 {值} 应通过 float 类型验证"
    
    @given(值=整数策略)
    @settings(max_examples=100, deadline=None)
    def test_浮点数类型验证_整数也应通过(self, 值: int):
        """
        属性测试: 对于任意整数值，float类型验证也应通过（int是float的子集）
        
        **Feature: config-gui, 属性 1: 类型一致性**
        **验证: 需求 4.3**
        """
        验证器 = 配置验证器(默认配置模式)
        
        # 整数也应该通过浮点数验证
        结果 = 验证器.验证类型(值, "float")
        
        assert 结果 is True, f"整数值 {值} 应通过 float 类型验证"
    
    @given(值=字符串策略)
    @settings(max_examples=100, deadline=None)
    def test_字符串类型验证_有效值应通过(self, 值: str):
        """
        属性测试: 对于任意字符串值，str类型验证应通过
        
        **Feature: config-gui, 属性 1: 类型一致性**
        **验证: 需求 4.3**
        """
        验证器 = 配置验证器(默认配置模式)
        
        # 验证字符串类型
        结果 = 验证器.验证类型(值, "str")
        
        assert 结果 is True, f"字符串值 '{值}' 应通过 str 类型验证"
    
    @given(值=布尔策略)
    @settings(max_examples=100, deadline=None)
    def test_布尔类型验证_有效值应通过(self, 值: bool):
        """
        属性测试: 对于任意布尔值，bool类型验证应通过
        
        **Feature: config-gui, 属性 1: 类型一致性**
        **验证: 需求 4.3**
        """
        验证器 = 配置验证器(默认配置模式)
        
        # 验证布尔类型
        结果 = 验证器.验证类型(值, "bool")
        
        assert 结果 is True, f"布尔值 {值} 应通过 bool 类型验证"
    
    @given(值=路径策略)
    @settings(max_examples=100, deadline=None)
    def test_路径类型验证_有效值应通过(self, 值: str):
        """
        属性测试: 对于任意路径字符串，path类型验证应通过
        
        **Feature: config-gui, 属性 1: 类型一致性**
        **验证: 需求 4.3**
        """
        验证器 = 配置验证器(默认配置模式)
        
        # 验证路径类型
        结果 = 验证器.验证类型(值, "path")
        
        assert 结果 is True, f"路径值 '{值}' 应通过 path 类型验证"
    
    @given(值=选项策略)
    @settings(max_examples=100, deadline=None)
    def test_选项类型验证_有效值应通过(self, 值: str):
        """
        属性测试: 对于任意选项字符串，choice类型验证应通过
        
        **Feature: config-gui, 属性 1: 类型一致性**
        **验证: 需求 4.3**
        """
        验证器 = 配置验证器(默认配置模式)
        
        # 验证选项类型
        结果 = 验证器.验证类型(值, "choice")
        
        assert 结果 is True, f"选项值 '{值}' 应通过 choice 类型验证"
    
    @given(值=错误整数类型策略)
    @settings(max_examples=100, deadline=None)
    def test_整数类型验证_无效值应失败(self, 值: Any):
        """
        属性测试: 对于非整数值，int类型验证应失败
        
        **Feature: config-gui, 属性 1: 类型一致性**
        **验证: 需求 4.3**
        """
        验证器 = 配置验证器(默认配置模式)
        
        # 验证非整数类型应失败
        结果 = 验证器.验证类型(值, "int")
        
        assert 结果 is False, f"非整数值 {值} (类型: {type(值).__name__}) 不应通过 int 类型验证"
    
    @given(值=错误浮点数类型策略)
    @settings(max_examples=100, deadline=None)
    def test_浮点数类型验证_无效值应失败(self, 值: Any):
        """
        属性测试: 对于非数值类型，float类型验证应失败
        
        **Feature: config-gui, 属性 1: 类型一致性**
        **验证: 需求 4.3**
        """
        验证器 = 配置验证器(默认配置模式)
        
        # 验证非数值类型应失败
        结果 = 验证器.验证类型(值, "float")
        
        assert 结果 is False, f"非数值 {值} (类型: {type(值).__name__}) 不应通过 float 类型验证"
    
    @given(值=错误字符串类型策略)
    @settings(max_examples=100, deadline=None)
    def test_字符串类型验证_无效值应失败(self, 值: Any):
        """
        属性测试: 对于非字符串值，str类型验证应失败
        
        **Feature: config-gui, 属性 1: 类型一致性**
        **验证: 需求 4.3**
        """
        验证器 = 配置验证器(默认配置模式)
        
        # 验证非字符串类型应失败
        结果 = 验证器.验证类型(值, "str")
        
        assert 结果 is False, f"非字符串值 {值} (类型: {type(值).__name__}) 不应通过 str 类型验证"
    
    @given(值=错误布尔类型策略)
    @settings(max_examples=100, deadline=None)
    def test_布尔类型验证_无效值应失败(self, 值: Any):
        """
        属性测试: 对于非布尔值，bool类型验证应失败
        
        **Feature: config-gui, 属性 1: 类型一致性**
        **验证: 需求 4.3**
        """
        验证器 = 配置验证器(默认配置模式)
        
        # 验证非布尔类型应失败
        结果 = 验证器.验证类型(值, "bool")
        
        assert 结果 is False, f"非布尔值 {值} (类型: {type(值).__name__}) 不应通过 bool 类型验证"
    
    def test_None值应通过所有类型验证(self):
        """
        测试: None值应通过所有类型验证（None在必需验证中处理）
        
        **Feature: config-gui, 属性 1: 类型一致性**
        **验证: 需求 4.3**
        """
        验证器 = 配置验证器(默认配置模式)
        
        类型列表 = ["int", "float", "str", "bool", "path", "choice"]
        
        for 类型 in 类型列表:
            结果 = 验证器.验证类型(None, 类型)
            assert 结果 is True, f"None 值应通过 {类型} 类型验证"
    
    def test_未知类型应通过验证(self):
        """
        测试: 未知类型应默认通过验证
        
        **Feature: config-gui, 属性 1: 类型一致性**
        **验证: 需求 4.3**
        """
        验证器 = 配置验证器(默认配置模式)
        
        # 未知类型应默认通过
        结果 = 验证器.验证类型("任意值", "unknown_type")
        assert 结果 is True, "未知类型应默认通过验证"
        
        结果 = 验证器.验证类型(123, "custom")
        assert 结果 is True, "自定义类型应默认通过验证"


class Test类型一致性_验证值方法:
    """
    使用验证值方法测试类型一致性
    
    **Feature: config-gui, 属性 1: 类型一致性**
    **验证: 需求 4.3**
    """
    
    @given(值=整数策略)
    @settings(max_examples=100, deadline=None)
    def test_验证值_整数类型_有效值应通过(self, 值: int):
        """
        属性测试: 使用验证值方法验证整数类型
        
        **Feature: config-gui, 属性 1: 类型一致性**
        **验证: 需求 4.3**
        """
        验证器 = 配置验证器(默认配置模式)
        参数定义 = {"类型": "int"}
        
        有效, 错误 = 验证器.验证值("测试参数", 值, 参数定义)
        
        assert 有效 is True, f"整数值 {值} 应通过验证值方法"
        assert 错误 is None, f"有效值不应产生错误"
    
    @given(值=浮点数策略)
    @settings(max_examples=100, deadline=None)
    def test_验证值_浮点数类型_有效值应通过(self, 值: float):
        """
        属性测试: 使用验证值方法验证浮点数类型
        
        **Feature: config-gui, 属性 1: 类型一致性**
        **验证: 需求 4.3**
        """
        验证器 = 配置验证器(默认配置模式)
        参数定义 = {"类型": "float"}
        
        有效, 错误 = 验证器.验证值("测试参数", 值, 参数定义)
        
        assert 有效 is True, f"浮点数值 {值} 应通过验证值方法"
        assert 错误 is None, f"有效值不应产生错误"
    
    @given(值=布尔策略)
    @settings(max_examples=100, deadline=None)
    def test_验证值_布尔类型_有效值应通过(self, 值: bool):
        """
        属性测试: 使用验证值方法验证布尔类型
        
        **Feature: config-gui, 属性 1: 类型一致性**
        **验证: 需求 4.3**
        """
        验证器 = 配置验证器(默认配置模式)
        参数定义 = {"类型": "bool"}
        
        有效, 错误 = 验证器.验证值("测试参数", 值, 参数定义)
        
        assert 有效 is True, f"布尔值 {值} 应通过验证值方法"
        assert 错误 is None, f"有效值不应产生错误"
    
    @given(值=错误整数类型策略)
    @settings(max_examples=100, deadline=None)
    def test_验证值_整数类型_无效值应返回错误(self, 值: Any):
        """
        属性测试: 使用验证值方法验证非整数类型应返回错误
        
        **Feature: config-gui, 属性 1: 类型一致性**
        **验证: 需求 4.3**
        """
        验证器 = 配置验证器(默认配置模式)
        参数定义 = {"类型": "int"}
        
        有效, 错误 = 验证器.验证值("测试参数", 值, 参数定义)
        
        assert 有效 is False, f"非整数值 {值} 不应通过验证"
        assert 错误 is not None, f"无效值应产生错误"
        assert isinstance(错误, 验证错误), f"错误应为验证错误类型"
        assert 错误.错误类型 == "type", f"错误类型应为 'type'"
    
    @given(值=错误布尔类型策略)
    @settings(max_examples=100, deadline=None)
    def test_验证值_布尔类型_无效值应返回错误(self, 值: Any):
        """
        属性测试: 使用验证值方法验证非布尔类型应返回错误
        
        **Feature: config-gui, 属性 1: 类型一致性**
        **验证: 需求 4.3**
        """
        验证器 = 配置验证器(默认配置模式)
        参数定义 = {"类型": "bool"}
        
        有效, 错误 = 验证器.验证值("测试参数", 值, 参数定义)
        
        assert 有效 is False, f"非布尔值 {值} 不应通过验证"
        assert 错误 is not None, f"无效值应产生错误"
        assert isinstance(错误, 验证错误), f"错误应为验证错误类型"
        assert 错误.错误类型 == "type", f"错误类型应为 'type'"


class Test类型一致性_完整配置验证:
    """
    测试完整配置的类型一致性验证
    
    **Feature: config-gui, 属性 1: 类型一致性**
    **验证: 需求 4.3**
    """
    
    @given(
        窗口X=st.integers(min_value=0, max_value=1000),
        窗口Y=st.integers(min_value=0, max_value=1000),
        窗口宽度=st.integers(min_value=100, max_value=7680),
        窗口高度=st.integers(min_value=100, max_value=4320),
    )
    @settings(max_examples=100, deadline=None)
    def test_有效窗口设置配置应通过类型验证(self, 窗口X, 窗口Y, 窗口宽度, 窗口高度):
        """
        属性测试: 对于任意有效的窗口设置配置，类型验证应通过
        
        **Feature: config-gui, 属性 1: 类型一致性**
        **验证: 需求 4.3**
        """
        验证器 = 配置验证器(默认配置模式)
        
        配置 = {
            "窗口设置": {
                "窗口X": 窗口X,
                "窗口Y": 窗口Y,
                "窗口宽度": 窗口宽度,
                "窗口高度": 窗口高度,
            }
        }
        
        有效, 错误列表 = 验证器.验证配置(配置)
        
        # 过滤出类型错误
        类型错误 = [e for e in 错误列表 if e.错误类型 == "type"]
        
        assert len(类型错误) == 0, f"有效的窗口设置配置不应产生类型错误，但得到: {类型错误}"
    
    @given(
        置信度阈值=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
        批次大小=st.integers(min_value=1, max_value=256),
        学习率=st.floats(min_value=0.0001, max_value=0.1, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=100, deadline=None)
    def test_有效模型和训练设置应通过类型验证(self, 置信度阈值, 批次大小, 学习率):
        """
        属性测试: 对于任意有效的模型和训练设置，类型验证应通过
        
        **Feature: config-gui, 属性 1: 类型一致性**
        **验证: 需求 4.3**
        """
        验证器 = 配置验证器(默认配置模式)
        
        配置 = {
            "模型设置": {
                "模型路径": "模型/test.pth",
                "YOLO模型": "模型/yolo.pt",
                "置信度阈值": 置信度阈值,
            },
            "训练设置": {
                "批次大小": 批次大小,
                "学习率": 学习率,
                "训练轮次": 100,
            }
        }
        
        有效, 错误列表 = 验证器.验证配置(配置)
        
        # 过滤出类型错误
        类型错误 = [e for e in 错误列表 if e.错误类型 == "type"]
        
        assert len(类型错误) == 0, f"有效的模型和训练设置不应产生类型错误，但得到: {类型错误}"
    
    @given(
        启用YOLO=布尔策略,
        显示调试=布尔策略,
        日志级别=选项策略,
    )
    @settings(max_examples=100, deadline=None)
    def test_有效运行设置应通过类型验证(self, 启用YOLO, 显示调试, 日志级别):
        """
        属性测试: 对于任意有效的运行设置，类型验证应通过
        
        **Feature: config-gui, 属性 1: 类型一致性**
        **验证: 需求 4.3**
        """
        验证器 = 配置验证器(默认配置模式)
        
        配置 = {
            "运行设置": {
                "启用YOLO": 启用YOLO,
                "显示调试": 显示调试,
                "日志级别": 日志级别,
            }
        }
        
        有效, 错误列表 = 验证器.验证配置(配置)
        
        # 过滤出类型错误
        类型错误 = [e for e in 错误列表 if e.错误类型 == "type"]
        
        assert len(类型错误) == 0, f"有效的运行设置不应产生类型错误，但得到: {类型错误}"
    
    def test_错误类型配置应产生类型错误(self):
        """
        测试: 错误类型的配置值应产生类型错误
        
        **Feature: config-gui, 属性 1: 类型一致性**
        **验证: 需求 4.3**
        """
        验证器 = 配置验证器(默认配置模式)
        
        # 使用错误类型的配置
        配置 = {
            "窗口设置": {
                "窗口X": "不是整数",  # 应该是 int
                "窗口Y": 3.14,  # 应该是 int，但 float 不是 int
                "窗口宽度": True,  # 应该是 int
            },
            "运行设置": {
                "启用YOLO": "yes",  # 应该是 bool
                "显示调试": 1,  # 应该是 bool
            }
        }
        
        有效, 错误列表 = 验证器.验证配置(配置)
        
        # 应该有类型错误
        类型错误 = [e for e in 错误列表 if e.错误类型 == "type"]
        
        assert len(类型错误) > 0, f"错误类型的配置应产生类型错误"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])
