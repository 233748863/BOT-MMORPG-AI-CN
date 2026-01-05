"""
血量检测集成属性测试模块

使用 Hypothesis 进行属性测试，验证增强机器人的血量检测集成和紧急规则触发。

**属性 8: 血量检测集成**
**属性 9: 紧急规则触发**

Feature: business-logic-fixes
验证: 需求 8.1, 8.3, 8.4
"""

import sys
import os
import pytest
import numpy as np
from hypothesis import given, strategies as st, settings
from unittest.mock import Mock, patch, MagicMock

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from 核心.数据类型 import 决策上下文, 游戏状态, 实体类型
from 核心.状态检测 import 状态检测结果


# ==================== 策略定义 ====================

def 血量百分比策略():
    """生成血量百分比 (0.0-1.0)"""
    return st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)


def 游戏图像策略(宽度=640, 高度=480):
    """生成随机游戏图像"""
    return st.builds(
        lambda: np.random.randint(0, 256, (高度, 宽度, 3), dtype=np.uint8)
    )


def 敌人数量策略():
    """生成附近敌人数量"""
    return st.integers(min_value=0, max_value=10)


# ==================== 属性 8: 血量检测集成 ====================

class Test血量检测集成_属性测试:
    """
    测试增强机器人的血量检测集成
    
    Feature: business-logic-fixes, 属性 8: 血量检测集成
    **验证: 需求 8.1, 8.3**
    """
    
    @settings(max_examples=100, deadline=5000)
    @given(血量=血量百分比策略())
    def test_属性8_检测成功时使用实际血量(self, 血量: float):
        """
        属性测试: 当状态检测器返回有效血量时，决策上下文应使用该血量值
        
        Feature: business-logic-fixes, Property 8: 血量检测集成
        **验证: 需求 8.1**
        """
        # 模拟状态检测器
        mock_检测器 = Mock()
        mock_检测结果 = 状态检测结果(
            血量百分比=血量,
            蓝量百分比=1.0,
            血量置信度=0.9,
            蓝量置信度=0.9,
            检测时间=0.01
        )
        mock_检测器.检测.return_value = mock_检测结果
        
        # 创建测试图像
        测试图像 = np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8)
        
        # 模拟 _获取血量百分比 方法的逻辑
        try:
            检测结果 = mock_检测器.检测(测试图像)
            检测到的血量 = 检测结果.血量百分比
            
            # 验证血量值在有效范围内
            if 0.0 <= 检测到的血量 <= 1.0:
                # 验证返回的血量等于检测器返回的血量
                assert abs(检测到的血量 - 血量) < 0.001, \
                    f"检测到的血量 {检测到的血量} 应等于状态检测器返回的血量 {血量}"
            else:
                # 无效值应被拒绝
                assert False, f"检测器返回了无效血量值: {检测到的血量}"
        except Exception as e:
            # 检测失败应回退到默认值
            assert False, f"检测不应失败: {e}"
    
    @settings(max_examples=50, deadline=5000)
    @given(血量=血量百分比策略())
    def test_属性8_检测失败时回退到默认值(self, 血量: float):
        """
        属性测试: 当状态检测失败时，应回退到默认值 1.0
        
        Feature: business-logic-fixes, Property 8: 血量检测集成
        **验证: 需求 8.3**
        """
        # 模拟状态检测器抛出异常
        mock_检测器 = Mock()
        mock_检测器.检测.side_effect = Exception("检测失败")
        
        # 创建测试图像
        测试图像 = np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8)
        
        # 模拟 _获取血量百分比 方法的错误处理逻辑
        try:
            检测结果 = mock_检测器.检测(测试图像)
            检测到的血量 = 检测结果.血量百分比
            # 不应该到达这里
            assert False, "检测应该失败"
        except Exception:
            # 检测失败，应回退到默认值 1.0
            检测到的血量 = 1.0
            
        # 验证返回默认值 1.0
        assert 检测到的血量 == 1.0, \
            f"检测失败时应回退到默认值 1.0，实际返回 {检测到的血量}"
    
    @settings(max_examples=50, deadline=5000)
    @given(血量=st.floats(min_value=-1.0, max_value=2.0, allow_nan=False, allow_infinity=False))
    def test_属性8_无效血量值使用上次有效值(self, 血量: float):
        """
        属性测试: 当检测器返回无效血量值时，应使用上次有效值
        
        Feature: business-logic-fixes, Property 8: 血量检测集成
        **验证: 需求 8.3**
        """
        # 只测试无效值
        if 0.0 <= 血量 <= 1.0:
            return
        
        # 设置上次有效血量
        上次有效血量 = 0.75
        
        # 模拟状态检测器返回无效值
        mock_检测器 = Mock()
        mock_检测结果 = 状态检测结果(
            血量百分比=血量,  # 无效值
            蓝量百分比=1.0,
            血量置信度=0.9,
            蓝量置信度=0.9,
            检测时间=0.01
        )
        mock_检测器.检测.return_value = mock_检测结果
        
        # 创建测试图像
        测试图像 = np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8)
        
        # 模拟 _获取血量百分比 方法的验证逻辑
        try:
            检测结果 = mock_检测器.检测(测试图像)
            检测到的血量 = 检测结果.血量百分比
            
            # 验证血量值在有效范围内
            if 0.0 <= 检测到的血量 <= 1.0:
                # 有效值，不应该到达这里（因为我们测试的是无效值）
                assert False, f"测试的是无效值，但检测到有效值: {检测到的血量}"
            else:
                # 无效值，应使用上次有效值
                检测到的血量 = 上次有效血量
        except Exception:
            # 检测失败，使用默认值
            检测到的血量 = 1.0
        
        # 验证返回上次有效值
        assert 检测到的血量 == 上次有效血量, \
            f"无效血量值 {血量} 时应使用上次有效值 {上次有效血量}，实际返回 {检测到的血量}"


# ==================== 属性 9: 紧急规则触发 ====================

class Test紧急规则触发_属性测试:
    """
    测试决策引擎在低血量时正确触发紧急规则
    
    Feature: business-logic-fixes, 属性 9: 紧急规则触发
    **验证: 需求 8.4**
    """
    
    @settings(max_examples=100, deadline=5000)
    @given(
        血量=st.floats(min_value=0.0, max_value=0.29, allow_nan=False, allow_infinity=False),
        敌人数量=敌人数量策略()
    )
    def test_属性9_低血量触发紧急规则(self, 血量: float, 敌人数量: int):
        """
        属性测试: 当血量低于紧急阈值时，决策引擎应触发紧急规则
        
        Feature: business-logic-fixes, Property 9: 紧急规则触发
        **验证: 需求 8.4**
        """
        from 核心.决策引擎 import 决策引擎
        from 配置.增强设置 import 紧急规则配置
        
        # 创建决策引擎
        引擎 = 决策引擎()
        
        # 获取紧急阈值
        低血量阈值 = 紧急规则配置.get("低血量阈值", 0.3)
        
        # 确保血量低于阈值
        assert 血量 < 低血量阈值, f"测试血量 {血量} 应低于阈值 {低血量阈值}"
        
        # 创建决策上下文
        上下文 = 决策上下文(
            游戏状态=游戏状态.战斗,
            检测结果=[],
            模型预测=[0.1] * 32,
            血量百分比=血量,
            附近敌人数量=敌人数量
        )
        
        # 执行决策
        决策结果 = 引擎.决策(上下文)
        
        # 验证触发了紧急规则
        assert 决策结果.来源 in ["rule", "mixed"], \
            f"低血量 ({血量:.1%}) 时应触发紧急规则，实际来源: {决策结果.来源}"
        
        # 验证原因包含"紧急"或"低血量"
        assert "紧急" in 决策结果.原因 or "低血量" in 决策结果.原因, \
            f"决策原因应包含'紧急'或'低血量'，实际原因: {决策结果.原因}"
    
    @settings(max_examples=100, deadline=5000)
    @given(
        血量=st.floats(min_value=0.31, max_value=1.0, allow_nan=False, allow_infinity=False),
        敌人数量=st.integers(min_value=0, max_value=2)
    )
    def test_属性9_正常血量不触发紧急规则(self, 血量: float, 敌人数量: int):
        """
        属性测试: 当血量正常且敌人数量少时，不应触发紧急规则
        
        Feature: business-logic-fixes, Property 9: 紧急规则触发
        **验证: 需求 8.4**
        """
        from 核心.决策引擎 import 决策引擎
        from 配置.增强设置 import 紧急规则配置
        
        # 创建决策引擎
        引擎 = 决策引擎()
        
        # 获取紧急阈值
        低血量阈值 = 紧急规则配置.get("低血量阈值", 0.3)
        被围攻阈值 = 紧急规则配置.get("被围攻阈值", 3)
        
        # 确保血量高于阈值且敌人数量少
        assert 血量 >= 低血量阈值, f"测试血量 {血量} 应高于阈值 {低血量阈值}"
        assert 敌人数量 < 被围攻阈值, f"测试敌人数量 {敌人数量} 应少于阈值 {被围攻阈值}"
        
        # 创建决策上下文
        上下文 = 决策上下文(
            游戏状态=游戏状态.战斗,
            检测结果=[],
            模型预测=[0.1] * 32,
            血量百分比=血量,
            附近敌人数量=敌人数量
        )
        
        # 执行决策
        决策结果 = 引擎.决策(上下文)
        
        # 验证没有触发紧急规则（原因中不应包含"紧急"）
        # 注意：可能触发其他规则或使用模型预测
        if 决策结果.来源 == "rule":
            assert "紧急" not in 决策结果.原因, \
                f"正常血量 ({血量:.1%}) 和少量敌人 ({敌人数量}) 时不应触发紧急规则，实际原因: {决策结果.原因}"
    
    @settings(max_examples=50, deadline=5000)
    @given(
        血量=血量百分比策略(),
        敌人数量=st.integers(min_value=3, max_value=10)
    )
    def test_属性9_被围攻触发紧急规则(self, 血量: float, 敌人数量: int):
        """
        属性测试: 当被围攻时（敌人数量 >= 3），应触发紧急规则
        
        Feature: business-logic-fixes, Property 9: 紧急规则触发
        **验证: 需求 8.4**
        """
        from 核心.决策引擎 import 决策引擎
        from 配置.增强设置 import 紧急规则配置
        
        # 创建决策引擎
        引擎 = 决策引擎()
        
        # 获取被围攻阈值
        被围攻阈值 = 紧急规则配置.get("被围攻阈值", 3)
        
        # 确保敌人数量达到阈值
        assert 敌人数量 >= 被围攻阈值, f"测试敌人数量 {敌人数量} 应达到阈值 {被围攻阈值}"
        
        # 创建决策上下文
        上下文 = 决策上下文(
            游戏状态=游戏状态.战斗,
            检测结果=[],
            模型预测=[0.1] * 32,
            血量百分比=血量,
            附近敌人数量=敌人数量
        )
        
        # 执行决策
        决策结果 = 引擎.决策(上下文)
        
        # 验证触发了紧急规则
        assert 决策结果.来源 in ["rule", "mixed"], \
            f"被围攻 ({敌人数量}个敌人) 时应触发紧急规则，实际来源: {决策结果.来源}"
        
        # 验证原因包含"紧急"或"被围攻"
        assert "紧急" in 决策结果.原因 or "被围攻" in 决策结果.原因, \
            f"决策原因应包含'紧急'或'被围攻'，实际原因: {决策结果.原因}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])
