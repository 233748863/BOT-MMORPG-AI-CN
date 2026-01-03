# -*- coding: utf-8 -*-
"""
运行状态属性测试模块

使用Hypothesis进行属性测试，验证运行状态显示一致性。

**Property 6: 运行状态显示一致性**
*对于任意* 机器人运行过程中的状态更新，显示的动作名称、游戏状态、
帧率、运动量和增强模块状态应与实际运行状态一致

**Validates: Requirements 4.4, 4.5, 4.6, 4.7**
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from hypothesis import given, strategies as st, settings, assume

# 检查PySide6是否可用
try:
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import Qt
    PYSIDE6_AVAILABLE = True
except ImportError:
    PYSIDE6_AVAILABLE = False

# 如果PySide6不可用，跳过所有测试
pytestmark = pytest.mark.skipif(
    not PYSIDE6_AVAILABLE,
    reason="PySide6未安装，跳过GUI测试"
)


@pytest.fixture(scope="module")
def 应用实例():
    """创建QApplication实例（整个模块共享）"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def 运行页(应用实例):
    """创建运行页面实例"""
    from 界面.页面.运行页 import 运行页
    页面 = 运行页()
    yield 页面
    页面.close()


@pytest.fixture
def 状态监控组件(应用实例):
    """创建运行状态监控组件实例"""
    from 界面.页面.运行页 import 运行状态监控
    组件 = 运行状态监控()
    yield 组件
    组件.close()


@pytest.fixture
def 增强模块状态组件(应用实例):
    """创建增强模块状态组件实例"""
    from 界面.页面.运行页 import 增强模块状态
    组件 = 增强模块状态()
    yield 组件
    组件.close()


class Test运行状态属性测试:
    """
    运行状态属性测试类
    
    **Feature: modern-ui, Property 6: 运行状态显示一致性**
    **Validates: Requirements 4.4, 4.5, 4.6, 4.7**
    """

    @given(动作名称=st.text(min_size=0, max_size=50))
    @settings(max_examples=100, deadline=None)
    def test_当前动作显示一致性(self, 应用实例, 动作名称):
        """
        属性测试: 对于任意动作名称，更新后显示应与输入一致
        
        **Feature: modern-ui, Property 6: 运行状态显示一致性**
        **Validates: Requirements 4.4**
        """
        from 界面.页面.运行页 import 运行状态监控
        
        # 创建状态监控组件
        组件 = 运行状态监控()
        
        try:
            # 更新当前动作
            组件.更新当前动作(动作名称)
            
            # 验证显示的动作名称与输入一致
            显示文本 = 组件._当前动作标签.text()
            assert 显示文本 == 动作名称, \
                f"当前动作显示应为'{动作名称}'，实际为'{显示文本}'"
        finally:
            组件.close()
    
    @given(游戏状态=st.sampled_from(["战斗", "对话", "移动", "空闲", "死亡", "加载", "未知"]))
    @settings(max_examples=100, deadline=None)
    def test_游戏状态显示一致性(self, 应用实例, 游戏状态):
        """
        属性测试: 对于任意游戏状态，更新后显示应与输入一致
        
        **Feature: modern-ui, Property 6: 运行状态显示一致性**
        **Validates: Requirements 4.5**
        """
        from 界面.页面.运行页 import 运行状态监控
        
        # 创建状态监控组件
        组件 = 运行状态监控()
        
        try:
            # 更新游戏状态
            组件.更新游戏状态(游戏状态)
            
            # 验证显示的游戏状态与输入一致
            显示文本 = 组件._游戏状态标签.text()
            assert 显示文本 == 游戏状态, \
                f"游戏状态显示应为'{游戏状态}'，实际为'{显示文本}'"
        finally:
            组件.close()
    
    @given(帧率=st.floats(min_value=0.0, max_value=120.0, allow_nan=False, allow_infinity=False))
    @settings(max_examples=100, deadline=None)
    def test_帧率显示一致性(self, 应用实例, 帧率):
        """
        属性测试: 对于任意帧率值，更新后显示应与输入一致（保留1位小数）
        
        **Feature: modern-ui, Property 6: 运行状态显示一致性**
        **Validates: Requirements 4.6**
        """
        from 界面.页面.运行页 import 运行状态监控
        
        # 创建状态监控组件
        组件 = 运行状态监控()
        
        try:
            # 更新帧率
            组件.更新帧率(帧率)
            
            # 验证显示的帧率与输入一致（保留1位小数）
            期望文本 = f"{帧率:.1f} FPS"
            显示文本 = 组件._帧率标签.text()
            assert 显示文本 == 期望文本, \
                f"帧率显示应为'{期望文本}'，实际为'{显示文本}'"
        finally:
            组件.close()
    
    @given(运动量=st.floats(min_value=0.0, max_value=1000.0, allow_nan=False, allow_infinity=False))
    @settings(max_examples=100, deadline=None)
    def test_运动量显示一致性(self, 应用实例, 运动量):
        """
        属性测试: 对于任意运动量值，更新后显示应与输入一致（保留1位小数）
        
        **Feature: modern-ui, Property 6: 运行状态显示一致性**
        **Validates: Requirements 4.7**
        """
        from 界面.页面.运行页 import 运行状态监控
        
        # 创建状态监控组件
        组件 = 运行状态监控()
        
        try:
            # 更新运动量
            组件.更新运动量(运动量)
            
            # 验证显示的运动量与输入一致（保留1位小数）
            期望文本 = f"{运动量:.1f}"
            显示文本 = 组件._运动量标签.text()
            assert 显示文本 == 期望文本, \
                f"运动量显示应为'{期望文本}'，实际为'{显示文本}'"
        finally:
            组件.close()

    @given(动作来源=st.sampled_from(["model", "rule", "mixed", "fallback"]))
    @settings(max_examples=100, deadline=None)
    def test_动作来源显示一致性(self, 应用实例, 动作来源):
        """
        属性测试: 对于任意动作来源，更新后显示应正确映射
        
        **Feature: modern-ui, Property 6: 运行状态显示一致性**
        **Validates: Requirements 4.4**
        """
        from 界面.页面.运行页 import 运行状态监控
        
        # 创建状态监控组件
        组件 = 运行状态监控()
        
        # 来源映射
        来源映射 = {
            "model": "模型预测",
            "rule": "规则决策",
            "mixed": "混合决策",
            "fallback": "降级模式",
        }
        
        try:
            # 更新动作来源
            组件.更新动作来源(动作来源)
            
            # 验证显示的动作来源与映射一致
            期望文本 = 来源映射.get(动作来源, 动作来源)
            显示文本 = 组件._动作来源标签.text()
            assert 显示文本 == 期望文本, \
                f"动作来源显示应为'{期望文本}'，实际为'{显示文本}'"
        finally:
            组件.close()
    
    @given(
        YOLO可用=st.booleans(),
        状态识别可用=st.booleans(),
        决策引擎可用=st.booleans(),
        低性能=st.booleans()
    )
    @settings(max_examples=100, deadline=None)
    def test_增强模块状态显示一致性(self, 应用实例, YOLO可用, 状态识别可用, 决策引擎可用, 低性能):
        """
        属性测试: 对于任意增强模块状态组合，更新后显示应与输入一致
        
        **Feature: modern-ui, Property 6: 运行状态显示一致性**
        **Validates: Requirements 4.7**
        """
        from 界面.页面.运行页 import 增强模块状态
        
        # 创建增强模块状态组件
        组件 = 增强模块状态()
        
        try:
            # 构造状态数据
            状态数据 = {
                "YOLO": YOLO可用,
                "状态识别": 状态识别可用,
                "决策引擎": 决策引擎可用,
                "低性能": 低性能,
            }
            
            # 更新模块状态
            组件.更新模块状态(状态数据)
            
            # 验证YOLO状态显示
            if YOLO可用:
                assert "已加载" in 组件._YOLO状态.text(), \
                    f"YOLO状态应显示'已加载'，实际为'{组件._YOLO状态.text()}'"
            else:
                assert "不可用" in 组件._YOLO状态.text(), \
                    f"YOLO状态应显示'不可用'，实际为'{组件._YOLO状态.text()}'"
            
            # 验证状态识别状态显示
            if 状态识别可用:
                assert "已加载" in 组件._状态识别状态.text(), \
                    f"状态识别状态应显示'已加载'，实际为'{组件._状态识别状态.text()}'"
            else:
                assert "不可用" in 组件._状态识别状态.text(), \
                    f"状态识别状态应显示'不可用'，实际为'{组件._状态识别状态.text()}'"
            
            # 验证决策引擎状态显示
            if 决策引擎可用:
                assert "已加载" in 组件._决策引擎状态.text(), \
                    f"决策引擎状态应显示'已加载'，实际为'{组件._决策引擎状态.text()}'"
            else:
                assert "不可用" in 组件._决策引擎状态.text(), \
                    f"决策引擎状态应显示'不可用'，实际为'{组件._决策引擎状态.text()}'"
            
            # 验证性能模式显示
            if 低性能:
                assert "低性能" in 组件._性能模式标签.text(), \
                    f"性能模式应显示'低性能'，实际为'{组件._性能模式标签.text()}'"
            else:
                assert "正常" in 组件._性能模式标签.text(), \
                    f"性能模式应显示'正常'，实际为'{组件._性能模式标签.text()}'"
        finally:
            组件.close()

    @given(
        当前动作=st.text(min_size=0, max_size=30),
        动作来源=st.sampled_from(["model", "rule", "mixed", "fallback"]),
        游戏状态=st.sampled_from(["战斗", "对话", "移动", "空闲", "死亡", "加载", "未知"]),
        帧率=st.floats(min_value=0.0, max_value=120.0, allow_nan=False, allow_infinity=False),
        运动量=st.floats(min_value=0.0, max_value=1000.0, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100, deadline=None)
    def test_运行页面状态更新一致性(self, 应用实例, 当前动作, 动作来源, 游戏状态, 帧率, 运动量):
        """
        属性测试: 对于任意状态数据组合，通过运行页面更新后，各字段显示应一致
        
        **Feature: modern-ui, Property 6: 运行状态显示一致性**
        **Validates: Requirements 4.4, 4.5, 4.6, 4.7**
        """
        from 界面.页面.运行页 import 运行页
        
        # 来源映射
        来源映射 = {
            "model": "模型预测",
            "rule": "规则决策",
            "mixed": "混合决策",
            "fallback": "降级模式",
        }
        
        # 创建运行页面
        页面 = 运行页()
        
        try:
            # 构造状态数据
            状态数据 = {
                "当前动作": 当前动作,
                "动作来源": 动作来源,
                "游戏状态": 游戏状态,
                "帧率": 帧率,
                "运动量": 运动量,
            }
            
            # 更新状态
            页面.更新状态(状态数据)
            
            # 获取状态监控组件
            状态监控 = 页面.获取状态监控()
            
            # 验证当前动作显示
            assert 状态监控._当前动作标签.text() == 当前动作, \
                f"当前动作显示不一致: 期望'{当前动作}'，实际'{状态监控._当前动作标签.text()}'"
            
            # 验证动作来源显示
            期望来源 = 来源映射.get(动作来源, 动作来源)
            assert 状态监控._动作来源标签.text() == 期望来源, \
                f"动作来源显示不一致: 期望'{期望来源}'，实际'{状态监控._动作来源标签.text()}'"
            
            # 验证游戏状态显示
            assert 状态监控._游戏状态标签.text() == 游戏状态, \
                f"游戏状态显示不一致: 期望'{游戏状态}'，实际'{状态监控._游戏状态标签.text()}'"
            
            # 验证帧率显示
            期望帧率 = f"{帧率:.1f} FPS"
            assert 状态监控._帧率标签.text() == 期望帧率, \
                f"帧率显示不一致: 期望'{期望帧率}'，实际'{状态监控._帧率标签.text()}'"
            
            # 验证运动量显示
            期望运动量 = f"{运动量:.1f}"
            assert 状态监控._运动量标签.text() == 期望运动量, \
                f"运动量显示不一致: 期望'{期望运动量}'，实际'{状态监控._运动量标签.text()}'"
        finally:
            页面.close()
    
    @given(
        状态序列=st.lists(
            st.tuples(
                st.text(min_size=1, max_size=20),  # 当前动作
                st.sampled_from(["战斗", "对话", "移动", "空闲"]),  # 游戏状态
                st.floats(min_value=0.0, max_value=60.0, allow_nan=False, allow_infinity=False),  # 帧率
                st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False)  # 运动量
            ),
            min_size=2,
            max_size=20
        )
    )
    @settings(max_examples=100, deadline=None)
    def test_连续状态更新一致性(self, 应用实例, 状态序列):
        """
        属性测试: 对于任意状态更新序列，每次更新后显示应与最新状态一致
        
        **Feature: modern-ui, Property 6: 运行状态显示一致性**
        **Validates: Requirements 4.4, 4.5, 4.6, 4.7**
        """
        from 界面.页面.运行页 import 运行页
        
        # 创建运行页面
        页面 = 运行页()
        
        try:
            for 当前动作, 游戏状态, 帧率, 运动量 in 状态序列:
                # 更新状态 - 使用强制更新绕过节流器
                状态数据 = {
                    "当前动作": 当前动作,
                    "游戏状态": 游戏状态,
                    "帧率": 帧率,
                    "运动量": 运动量,
                }
                # 直接调用内部更新方法，绕过节流器
                页面._执行状态更新(状态数据)
                
                # 获取状态监控组件
                状态监控 = 页面.获取状态监控()
                
                # 验证每次更新后显示与最新状态一致
                assert 状态监控._当前动作标签.text() == 当前动作, \
                    f"连续更新后当前动作显示不一致"
                assert 状态监控._游戏状态标签.text() == 游戏状态, \
                    f"连续更新后游戏状态显示不一致"
                assert 状态监控._帧率标签.text() == f"{帧率:.1f} FPS", \
                    f"连续更新后帧率显示不一致"
                assert 状态监控._运动量标签.text() == f"{运动量:.1f}", \
                    f"连续更新后运动量显示不一致"
        finally:
            页面.close()

    def test_初始状态正确(self, 状态监控组件):
        """
        测试: 运行状态监控组件初始状态应正确
        
        **Feature: modern-ui, Property 6: 运行状态显示一致性**
        **Validates: Requirements 4.4, 4.5, 4.6, 4.7**
        """
        # 验证初始运行状态
        assert 状态监控组件._运行状态标签.text() == "已停止", \
            "初始运行状态显示应为'已停止'"
        
        # 验证初始当前动作
        assert 状态监控组件._当前动作标签.text() == "无", \
            "初始当前动作显示应为'无'"
        
        # 验证初始动作来源
        assert 状态监控组件._动作来源标签.text() == "-", \
            "初始动作来源显示应为'-'"
        
        # 验证初始游戏状态
        assert 状态监控组件._游戏状态标签.text() == "未知", \
            "初始游戏状态显示应为'未知'"
        
        # 验证初始帧率
        assert 状态监控组件._帧率标签.text() == "0 FPS", \
            "初始帧率显示应为'0 FPS'"
        
        # 验证初始运动量
        assert 状态监控组件._运动量标签.text() == "0", \
            "初始运动量显示应为'0'"
    
    def test_重置功能(self, 状态监控组件):
        """
        测试: 重置后状态监控组件应恢复初始状态
        
        **Feature: modern-ui, Property 6: 运行状态显示一致性**
        **Validates: Requirements 4.4, 4.5, 4.6, 4.7**
        """
        # 先设置一些值
        状态监控组件.更新运行状态("运行中")
        状态监控组件.更新当前动作("前进")
        状态监控组件.更新动作来源("model")
        状态监控组件.更新游戏状态("战斗")
        状态监控组件.更新帧率(30.5)
        状态监控组件.更新运动量(15.3)
        
        # 重置
        状态监控组件.重置()
        
        # 验证重置后的状态
        assert 状态监控组件._运行状态标签.text() == "已停止", \
            "重置后运行状态显示应为'已停止'"
        assert 状态监控组件._当前动作标签.text() == "无", \
            "重置后当前动作显示应为'无'"
        assert 状态监控组件._动作来源标签.text() == "-", \
            "重置后动作来源显示应为'-'"
        assert 状态监控组件._游戏状态标签.text() == "未知", \
            "重置后游戏状态显示应为'未知'"
        assert 状态监控组件._帧率标签.text() == "0 FPS" or 状态监控组件._帧率标签.text() == "0.0 FPS", \
            "重置后帧率显示应为'0 FPS'或'0.0 FPS'"
        assert 状态监控组件._运动量标签.text() == "0" or 状态监控组件._运动量标签.text() == "0.0", \
            "重置后运动量显示应为'0'或'0.0'"
    
    def test_增强模块初始状态正确(self, 增强模块状态组件):
        """
        测试: 增强模块状态组件初始状态应正确
        
        **Feature: modern-ui, Property 6: 运行状态显示一致性**
        **Validates: Requirements 4.7**
        """
        # 验证初始YOLO状态
        assert 增强模块状态组件._YOLO状态.text() == "未加载", \
            "初始YOLO状态显示应为'未加载'"
        
        # 验证初始状态识别状态
        assert 增强模块状态组件._状态识别状态.text() == "未加载", \
            "初始状态识别状态显示应为'未加载'"
        
        # 验证初始决策引擎状态
        assert 增强模块状态组件._决策引擎状态.text() == "未加载", \
            "初始决策引擎状态显示应为'未加载'"
        
        # 验证初始性能模式
        assert "正常" in 增强模块状态组件._性能模式标签.text(), \
            "初始性能模式显示应包含'正常'"
    
    def test_增强模块重置功能(self, 增强模块状态组件):
        """
        测试: 重置后增强模块状态组件应恢复初始状态
        
        **Feature: modern-ui, Property 6: 运行状态显示一致性**
        **Validates: Requirements 4.7**
        """
        # 先设置一些值
        增强模块状态组件.更新YOLO状态(True)
        增强模块状态组件.更新状态识别状态(True)
        增强模块状态组件.更新决策引擎状态(True)
        增强模块状态组件.更新性能模式(True)
        
        # 重置
        增强模块状态组件.重置()
        
        # 验证重置后的状态
        assert 增强模块状态组件._YOLO状态.text() == "未加载", \
            "重置后YOLO状态显示应为'未加载'"
        assert 增强模块状态组件._状态识别状态.text() == "未加载", \
            "重置后状态识别状态显示应为'未加载'"
        assert 增强模块状态组件._决策引擎状态.text() == "未加载", \
            "重置后决策引擎状态显示应为'未加载'"
        assert "正常" in 增强模块状态组件._性能模式标签.text(), \
            "重置后性能模式显示应包含'正常'"
    
    @given(运行状态=st.sampled_from(["运行中", "已暂停", "已停止", "倒计时", "准备中"]))
    @settings(max_examples=100, deadline=None)
    def test_运行状态显示一致性(self, 应用实例, 运行状态):
        """
        属性测试: 对于任意运行状态，更新后显示应与输入一致
        
        **Feature: modern-ui, Property 6: 运行状态显示一致性**
        **Validates: Requirements 4.4**
        """
        from 界面.页面.运行页 import 运行状态监控
        
        # 创建状态监控组件
        组件 = 运行状态监控()
        
        try:
            # 更新运行状态
            组件.更新运行状态(运行状态)
            
            # 验证显示的运行状态与输入一致
            显示文本 = 组件._运行状态标签.text()
            assert 显示文本 == 运行状态, \
                f"运行状态显示应为'{运行状态}'，实际为'{显示文本}'"
        finally:
            组件.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
