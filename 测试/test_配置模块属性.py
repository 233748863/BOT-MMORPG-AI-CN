# -*- coding: utf-8 -*-
"""
配置模块属性测试

使用Hypothesis进行属性测试，验证配置模块的正确性。

**Property 6: 按键映射唯一性**
*对于任意* 动作定义集合，不应存在两个不同的动作索引映射到相同的按键。
**Validates: Requirements 4.1**

**Property 7: 模型输入尺寸同步**
*对于任意* 窗口区域更新，更新后的模型输入宽度应等于 游戏宽度 // 模型缩放比例，
模型输入高度应等于 游戏高度 // 模型缩放比例。
**Validates: Requirements 5.1, 5.2, 5.3**
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from hypothesis import given, strategies as st, settings, assume


class Test按键映射唯一性属性:
    """
    按键映射唯一性属性测试类
    
    **Feature: business-logic-fixes, Property 6: 按键映射唯一性**
    **Validates: Requirements 4.1**
    """
    
    def test_动作定义中无按键冲突(self):
        """
        测试: 动作定义中不应存在按键冲突
        
        **Feature: business-logic-fixes, Property 6: 按键映射唯一性**
        **Validates: Requirements 4.1**
        """
        from 配置.设置 import 动作定义, 检测按键冲突
        
        # 执行冲突检测
        冲突列表 = 检测按键冲突()
        
        # 验证: 不应存在按键冲突
        assert len(冲突列表) == 0, \
            f"动作定义中存在按键冲突: {冲突列表}"
    
    def test_技能F和交互按键不同(self):
        """
        测试: 技能F(索引18)和交互(索引21)应使用不同的按键
        
        **Feature: business-logic-fixes, Property 6: 按键映射唯一性**
        **Validates: Requirements 4.2, 4.3**
        """
        from 配置.设置 import 动作定义
        
        技能F按键 = 动作定义[18]["按键"]
        交互按键 = 动作定义[21]["按键"]
        
        # 验证: 两个动作的按键应不同
        assert 技能F按键 != 交互按键, \
            f"技能F(索引18)和交互(索引21)使用了相同的按键: {技能F按键}"
    
    def test_交互动作使用G键(self):
        """
        测试: 交互动作(索引21)应使用G键
        
        **Feature: business-logic-fixes, Property 6: 按键映射唯一性**
        **Validates: Requirements 4.3**
        """
        from 配置.设置 import 动作定义
        
        交互按键 = 动作定义[21]["按键"]
        
        # 验证: 交互动作应使用G键
        assert 交互按键 == "G", \
            f"交互动作(索引21)应使用G键，但实际使用: {交互按键}"
    
    @given(
        动作索引列表=st.lists(
            st.integers(min_value=0, max_value=31),
            min_size=2,
            max_size=10,
            unique=True
        )
    )
    @settings(max_examples=100, deadline=None)
    def test_任意动作子集无按键冲突(self, 动作索引列表):
        """
        属性测试: 对于任意动作索引子集，不应存在按键冲突
        
        **Feature: business-logic-fixes, Property 6: 按键映射唯一性**
        **Validates: Requirements 4.1**
        """
        from 配置.设置 import 动作定义
        
        # 收集选中动作的按键映射
        按键映射 = {}
        for 索引 in 动作索引列表:
            if 索引 not in 动作定义:
                continue
            
            动作信息 = 动作定义[索引]
            按键 = 动作信息.get("按键", "")
            
            # 跳过特殊按键
            if 按键 in ["无", "鼠标左", "鼠标右", "鼠标中"]:
                continue
            
            if 按键 not in 按键映射:
                按键映射[按键] = []
            按键映射[按键].append(索引)
        
        # 验证: 每个按键最多映射到一个动作
        for 按键, 索引列表 in 按键映射.items():
            assert len(索引列表) <= 1, \
                f"按键 '{按键}' 被多个动作使用: {索引列表}"


class Test模型输入尺寸同步属性:
    """
    模型输入尺寸同步属性测试类
    
    **Feature: business-logic-fixes, Property 7: 模型输入尺寸同步**
    **Validates: Requirements 5.1, 5.2, 5.3**
    """
    
    @given(
        x=st.integers(min_value=0, max_value=1000),
        y=st.integers(min_value=0, max_value=500),
        width=st.integers(min_value=640, max_value=3840),
        height=st.integers(min_value=480, max_value=2160)
    )
    @settings(max_examples=100, deadline=None)
    def test_更新窗口区域后模型尺寸同步(self, x, y, width, height):
        """
        属性测试: 对于任意有效窗口区域，更新后模型输入尺寸应正确同步
        
        **Feature: business-logic-fixes, Property 7: 模型输入尺寸同步**
        **Validates: Requirements 5.1, 5.2, 5.3**
        """
        import 配置.设置 as 设置模块
        
        # 保存原始值以便恢复
        原始窗口区域 = 设置模块.游戏窗口区域
        原始宽度 = 设置模块.游戏宽度
        原始高度 = 设置模块.游戏高度
        原始模型宽度 = 设置模块.模型输入宽度
        原始模型高度 = 设置模块.模型输入高度
        
        try:
            # 执行窗口区域更新
            新区域 = (x, y, width, height)
            设置模块.更新窗口区域(新区域)
            
            # 获取缩放比例
            缩放比例 = 设置模块.模型缩放比例
            
            # 验证: 模型输入宽度 = 游戏宽度 // 模型缩放比例
            期望模型宽度 = width // 缩放比例
            assert 设置模块.模型输入宽度 == 期望模型宽度, \
                f"模型输入宽度应为 {期望模型宽度}，但实际为 {设置模块.模型输入宽度}"
            
            # 验证: 模型输入高度 = 游戏高度 // 模型缩放比例
            期望模型高度 = height // 缩放比例
            assert 设置模块.模型输入高度 == 期望模型高度, \
                f"模型输入高度应为 {期望模型高度}，但实际为 {设置模块.模型输入高度}"
            
            # 验证: 游戏宽度和高度也正确更新
            assert 设置模块.游戏宽度 == width, \
                f"游戏宽度应为 {width}，但实际为 {设置模块.游戏宽度}"
            assert 设置模块.游戏高度 == height, \
                f"游戏高度应为 {height}，但实际为 {设置模块.游戏高度}"
            
        finally:
            # 恢复原始值
            设置模块.游戏窗口区域 = 原始窗口区域
            设置模块.游戏宽度 = 原始宽度
            设置模块.游戏高度 = 原始高度
            设置模块.模型输入宽度 = 原始模型宽度
            设置模块.模型输入高度 = 原始模型高度
    
    def test_窗口区域更新后游戏窗口区域格式正确(self):
        """
        测试: 更新窗口区域后，游戏窗口区域应为 (x, y, x+width, y+height) 格式
        
        **Feature: business-logic-fixes, Property 7: 模型输入尺寸同步**
        **Validates: Requirements 5.1**
        """
        import 配置.设置 as 设置模块
        
        # 保存原始值
        原始窗口区域 = 设置模块.游戏窗口区域
        原始宽度 = 设置模块.游戏宽度
        原始高度 = 设置模块.游戏高度
        原始模型宽度 = 设置模块.模型输入宽度
        原始模型高度 = 设置模块.模型输入高度
        
        try:
            # 测试数据
            x, y, width, height = 100, 50, 1280, 720
            新区域 = (x, y, width, height)
            
            # 执行更新
            设置模块.更新窗口区域(新区域)
            
            # 验证窗口区域格式
            期望区域 = (x, y, x + width, y + height)
            assert 设置模块.游戏窗口区域 == 期望区域, \
                f"游戏窗口区域应为 {期望区域}，但实际为 {设置模块.游戏窗口区域}"
            
        finally:
            # 恢复原始值
            设置模块.游戏窗口区域 = 原始窗口区域
            设置模块.游戏宽度 = 原始宽度
            设置模块.游戏高度 = 原始高度
            设置模块.模型输入宽度 = 原始模型宽度
            设置模块.模型输入高度 = 原始模型高度
    
    def test_无效窗口区域不更新配置(self):
        """
        测试: 无效的窗口区域（None或长度不为4）不应更新配置
        
        **Feature: business-logic-fixes, Property 7: 模型输入尺寸同步**
        **Validates: Requirements 5.1**
        """
        import 配置.设置 as 设置模块
        
        # 保存原始值
        原始窗口区域 = 设置模块.游戏窗口区域
        原始宽度 = 设置模块.游戏宽度
        原始高度 = 设置模块.游戏高度
        原始模型宽度 = 设置模块.模型输入宽度
        原始模型高度 = 设置模块.模型输入高度
        
        try:
            # 测试 None
            设置模块.更新窗口区域(None)
            assert 设置模块.游戏窗口区域 == 原始窗口区域, \
                "None 不应更新窗口区域"
            
            # 测试长度不为4的元组
            设置模块.更新窗口区域((100, 200, 300))
            assert 设置模块.游戏窗口区域 == 原始窗口区域, \
                "长度不为4的元组不应更新窗口区域"
            
            # 测试空元组
            设置模块.更新窗口区域(())
            assert 设置模块.游戏窗口区域 == 原始窗口区域, \
                "空元组不应更新窗口区域"
            
        finally:
            # 恢复原始值
            设置模块.游戏窗口区域 = 原始窗口区域
            设置模块.游戏宽度 = 原始宽度
            设置模块.游戏高度 = 原始高度
            设置模块.模型输入宽度 = 原始模型宽度
            设置模块.模型输入高度 = 原始模型高度
    
    @given(缩放比例=st.integers(min_value=1, max_value=8))
    @settings(max_examples=100, deadline=None)
    def test_不同缩放比例下模型尺寸计算正确(self, 缩放比例):
        """
        属性测试: 对于任意有效缩放比例，模型尺寸计算应正确
        
        **Feature: business-logic-fixes, Property 7: 模型输入尺寸同步**
        **Validates: Requirements 5.2, 5.3**
        """
        import 配置.设置 as 设置模块
        
        # 保存原始值
        原始缩放比例 = 设置模块.模型缩放比例
        原始窗口区域 = 设置模块.游戏窗口区域
        原始宽度 = 设置模块.游戏宽度
        原始高度 = 设置模块.游戏高度
        原始模型宽度 = 设置模块.模型输入宽度
        原始模型高度 = 设置模块.模型输入高度
        
        try:
            # 设置新的缩放比例
            设置模块.模型缩放比例 = 缩放比例
            
            # 测试数据
            width, height = 1920, 1080
            新区域 = (0, 0, width, height)
            
            # 执行更新
            设置模块.更新窗口区域(新区域)
            
            # 验证计算
            期望模型宽度 = width // 缩放比例
            期望模型高度 = height // 缩放比例
            
            assert 设置模块.模型输入宽度 == 期望模型宽度, \
                f"缩放比例{缩放比例}下，模型宽度应为{期望模型宽度}，实际为{设置模块.模型输入宽度}"
            assert 设置模块.模型输入高度 == 期望模型高度, \
                f"缩放比例{缩放比例}下，模型高度应为{期望模型高度}，实际为{设置模块.模型输入高度}"
            
        finally:
            # 恢复原始值
            设置模块.模型缩放比例 = 原始缩放比例
            设置模块.游戏窗口区域 = 原始窗口区域
            设置模块.游戏宽度 = 原始宽度
            设置模块.游戏高度 = 原始高度
            设置模块.模型输入宽度 = 原始模型宽度
            设置模块.模型输入高度 = 原始模型高度


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
