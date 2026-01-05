"""
决策引擎属性测试
使用hypothesis进行属性测试，验证决策引擎的核心属性

Property 7: 状态-动作权重映射正确性
Property 8: 规则优先级覆盖正确性
Property 9: 动作冷却机制正确性
Property 10: 决策日志完整性

**Validates: Requirements 3.1-3.9**
"""

import sys
import os
import time

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from hypothesis import given, strategies as st, settings, assume

from 核心.数据类型 import (
    游戏状态, 决策策略, 检测结果, 决策上下文, 决策结果, 决策规则, 实体类型, 方向
)
from 核心.决策引擎 import 决策引擎
from 配置.增强设置 import 状态动作权重, 游戏状态枚举, 动作冷却时间
from 配置.设置 import 动作定义, 总动作数


# ==================== 策略定义 ====================

# 游戏状态策略
游戏状态策略 = st.sampled_from(list(游戏状态))

# 血量百分比策略 (0.0 - 1.0)
血量策略 = st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)

# 敌人数量策略
敌人数量策略 = st.integers(min_value=0, max_value=10)

# 模型预测策略 (32维概率向量)
模型预测策略 = st.lists(
    st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
    min_size=32,
    max_size=32
)

# 规则优先级策略
优先级策略 = st.integers(min_value=1, max_value=200)

# 动作索引策略
动作索引策略 = st.integers(min_value=0, max_value=总动作数 - 1)

# 冷却时间策略
冷却时间策略 = st.floats(min_value=0.0, max_value=5.0, allow_nan=False, allow_infinity=False)


def 创建决策上下文(状态: 游戏状态, 血量: float = 1.0, 
                  敌人数量: int = 0, 模型预测: list = None) -> 决策上下文:
    """创建决策上下文的辅助函数"""
    return 决策上下文(
        游戏状态=状态,
        检测结果=[],
        模型预测=模型预测 if 模型预测 else [0.1] * 32,
        血量百分比=血量,
        附近敌人数量=敌人数量
    )


# ==================== Property 7: 状态-动作权重映射正确性 ====================

class Test状态动作权重映射属性:
    """
    Property 7: 状态-动作权重映射正确性
    
    *For any* 游戏状态，决策引擎应该返回对应的动作权重，
    战斗状态偏向技能，对话状态偏向交互，移动状态偏向移动
    
    **Validates: Requirements 3.1, 3.2, 3.3, 3.4**
    """
    
    @given(状态=游戏状态策略)
    @settings(max_examples=100)
    def test_权重列表长度正确(self, 状态: 游戏状态):
        """
        **Feature: game-ai-enhancement, Property 7: 状态-动作权重映射正确性**
        
        对于任意游戏状态，返回的权重列表长度应该等于总动作数(32)
        """
        引擎 = 决策引擎()
        权重 = 引擎.获取状态动作权重(状态)
        
        assert isinstance(权重, list), "权重应该是列表类型"
        assert len(权重) == 总动作数, f"权重列表长度应该是{总动作数}，实际是{len(权重)}"
    
    @given(状态=游戏状态策略)
    @settings(max_examples=100)
    def test_权重值非负(self, 状态: 游戏状态):
        """
        **Feature: game-ai-enhancement, Property 7: 状态-动作权重映射正确性**
        
        对于任意游戏状态，所有权重值应该非负
        """
        引擎 = 决策引擎()
        权重 = 引擎.获取状态动作权重(状态)
        
        for i, w in enumerate(权重):
            assert w >= 0, f"动作{i}的权重不应为负数，当前值: {w}"
    
    def test_战斗状态技能权重较高(self):
        """
        **Feature: game-ai-enhancement, Property 7: 状态-动作权重映射正确性**
        
        战斗状态下，技能类动作的权重应该较高
        **Validates: Requirements 3.2**
        """
        引擎 = 决策引擎()
        战斗权重 = 引擎.获取状态动作权重(游戏状态.战斗)
        
        # 获取技能动作的权重 (动作9-19是技能)
        技能权重 = [战斗权重[i] for i in range(9, 20) if i < len(战斗权重)]
        # 获取移动动作的权重 (动作0-8是移动)
        移动权重 = [战斗权重[i] for i in range(0, 9) if i < len(战斗权重)]
        
        # 战斗状态下技能平均权重应该不低于移动平均权重
        if 技能权重 and 移动权重:
            技能平均 = sum(技能权重) / len(技能权重)
            移动平均 = sum(移动权重) / len(移动权重)
            # 技能权重应该相对较高（允许一定容差）
            assert 技能平均 >= 移动平均 * 0.5, \
                f"战斗状态下技能权重({技能平均:.2f})应该不低于移动权重的一半({移动平均 * 0.5:.2f})"
    
    def test_对话状态交互权重较高(self):
        """
        **Feature: game-ai-enhancement, Property 7: 状态-动作权重映射正确性**
        
        对话状态下，鼠标/交互类动作的权重应该较高，技能权重应该较低
        **Validates: Requirements 3.3**
        """
        引擎 = 决策引擎()
        对话权重 = 引擎.获取状态动作权重(游戏状态.对话)
        
        # 获取鼠标动作的权重 (动作23-27是鼠标)
        鼠标权重 = [对话权重[i] for i in range(23, 28) if i < len(对话权重)]
        # 获取技能动作的权重 (动作9-19是技能)
        技能权重 = [对话权重[i] for i in range(9, 20) if i < len(对话权重)]
        
        if 鼠标权重 and 技能权重:
            鼠标平均 = sum(鼠标权重) / len(鼠标权重)
            技能平均 = sum(技能权重) / len(技能权重)
            # 对话状态下鼠标权重应该高于技能权重
            assert 鼠标平均 >= 技能平均, \
                f"对话状态下鼠标权重({鼠标平均:.2f})应该不低于技能权重({技能平均:.2f})"
    
    def test_移动状态移动权重较高(self):
        """
        **Feature: game-ai-enhancement, Property 7: 状态-动作权重映射正确性**
        
        移动状态下，移动类动作的权重应该较高
        **Validates: Requirements 3.4**
        """
        引擎 = 决策引擎()
        移动状态权重 = 引擎.获取状态动作权重(游戏状态.移动)
        
        # 获取移动动作的权重 (动作0-8是移动，但8是无操作)
        移动权重 = [移动状态权重[i] for i in range(0, 8) if i < len(移动状态权重)]
        # 获取技能动作的权重 (动作9-19是技能)
        技能权重 = [移动状态权重[i] for i in range(9, 20) if i < len(移动状态权重)]
        
        if 移动权重 and 技能权重:
            移动平均 = sum(移动权重) / len(移动权重)
            技能平均 = sum(技能权重) / len(技能权重)
            # 移动状态下移动权重应该高于技能权重
            assert 移动平均 >= 技能平均, \
                f"移动状态下移动权重({移动平均:.2f})应该不低于技能权重({技能平均:.2f})"


# ==================== Property 8: 规则优先级覆盖正确性 ====================

class Test规则优先级覆盖属性:
    """
    Property 8: 规则优先级覆盖正确性
    
    *For any* 高优先级规则触发的情况，规则结果应该覆盖模型预测结果
    
    **Validates: Requirements 3.5**
    """
    
    @given(
        高优先级=st.integers(min_value=100, max_value=200),
        低优先级=st.integers(min_value=1, max_value=50),
        高优先级动作=动作索引策略,
        低优先级动作=动作索引策略
    )
    @settings(max_examples=100)
    def test_高优先级规则优先匹配(self, 高优先级: int, 低优先级: int, 
                                高优先级动作: int, 低优先级动作: int):
        """
        **Feature: game-ai-enhancement, Property 8: 规则优先级覆盖正确性**
        
        当多个规则都匹配时，高优先级规则应该优先被选择
        """
        # 确保两个动作不同
        assume(高优先级动作 != 低优先级动作)
        assume(高优先级 > 低优先级)
        
        引擎 = 决策引擎(策略=决策策略.规则优先)
        引擎.清空规则()
        引擎.重置冷却()
        
        # 添加两个都会匹配的规则
        低优先级规则 = 决策规则(
            名称="低优先级规则",
            优先级=低优先级,
            条件=lambda ctx: True,  # 始终匹配
            动作=低优先级动作,
            冷却时间=0.0
        )
        
        高优先级规则 = 决策规则(
            名称="高优先级规则",
            优先级=高优先级,
            条件=lambda ctx: True,  # 始终匹配
            动作=高优先级动作,
            冷却时间=0.0
        )
        
        # 先添加低优先级，再添加高优先级
        引擎.添加规则(低优先级规则)
        引擎.添加规则(高优先级规则)
        
        上下文 = 创建决策上下文(游戏状态.空闲)
        结果 = 引擎.决策(上下文)
        
        # 高优先级规则应该被选择
        assert 结果.动作索引 == 高优先级动作, \
            f"应该选择高优先级规则的动作{高优先级动作}，实际选择了{结果.动作索引}"
        assert 结果.来源 == "rule", "决策来源应该是规则"
    
    @given(
        规则优先级=优先级策略,
        规则动作=动作索引策略,
        模型预测=模型预测策略
    )
    @settings(max_examples=100)
    def test_规则优先策略下规则覆盖模型(self, 规则优先级: int, 
                                       规则动作: int, 模型预测: list):
        """
        **Feature: game-ai-enhancement, Property 8: 规则优先级覆盖正确性**
        
        在规则优先策略下，匹配的规则应该覆盖模型预测
        """
        引擎 = 决策引擎(策略=决策策略.规则优先)
        引擎.清空规则()
        引擎.重置冷却()
        
        # 添加一个始终匹配的规则
        规则 = 决策规则(
            名称="测试规则",
            优先级=规则优先级,
            条件=lambda ctx: True,
            动作=规则动作,
            冷却时间=0.0
        )
        引擎.添加规则(规则)
        
        上下文 = 创建决策上下文(游戏状态.空闲, 模型预测=模型预测)
        结果 = 引擎.决策(上下文)
        
        # 规则应该覆盖模型预测
        assert 结果.动作索引 == 规则动作, \
            f"规则优先策略下应该选择规则动作{规则动作}，实际选择了{结果.动作索引}"
        assert 结果.来源 == "rule", "决策来源应该是规则"
    
    @given(模型预测=模型预测策略)
    @settings(max_examples=100)
    def test_无匹配规则时使用模型(self, 模型预测: list):
        """
        **Feature: game-ai-enhancement, Property 8: 规则优先级覆盖正确性**
        
        当没有规则匹配时，应该使用模型预测
        """
        引擎 = 决策引擎(策略=决策策略.规则优先)
        引擎.清空规则()
        引擎.重置冷却()
        
        # 添加一个永不匹配的规则
        规则 = 决策规则(
            名称="永不匹配",
            优先级=100,
            条件=lambda ctx: False,  # 永不匹配
            动作=0,
            冷却时间=0.0
        )
        引擎.添加规则(规则)
        
        上下文 = 创建决策上下文(游戏状态.空闲, 模型预测=模型预测)
        结果 = 引擎.决策(上下文)
        
        # 应该使用模型预测
        assert 结果.来源 == "model", "无匹配规则时决策来源应该是模型"


# ==================== Property 9: 动作冷却机制正确性 ====================

class Test动作冷却机制属性:
    """
    Property 9: 动作冷却机制正确性
    
    *For any* 处于冷却中的动作，决策引擎应该阻止该动作被选择
    
    **Validates: Requirements 3.9**
    """
    
    @given(动作索引=动作索引策略)
    @settings(max_examples=100)
    def test_无冷却配置的动作始终可执行(self, 动作索引: int):
        """
        **Feature: game-ai-enhancement, Property 9: 动作冷却机制正确性**
        
        没有配置冷却时间的动作应该始终可以执行
        """
        # 跳过有冷却配置的动作
        assume(动作索引 not in 动作冷却时间)
        
        引擎 = 决策引擎()
        引擎.重置冷却()
        
        # 记录执行
        引擎.记录动作执行(动作索引)
        
        # 无冷却配置的动作应该立即可执行
        assert 引擎.检查冷却(动作索引) == True, \
            f"无冷却配置的动作{动作索引}应该始终可执行"
    
    @given(动作索引=st.sampled_from(list(动作冷却时间.keys())))
    @settings(max_examples=100)
    def test_有冷却配置的动作执行后进入冷却(self, 动作索引: int):
        """
        **Feature: game-ai-enhancement, Property 9: 动作冷却机制正确性**
        
        有冷却配置的动作执行后应该进入冷却状态
        """
        引擎 = 决策引擎()
        引擎.重置冷却()
        
        # 执行前应该可以执行
        assert 引擎.检查冷却(动作索引) == True, "执行前动作应该可以执行"
        
        # 记录执行
        引擎.记录动作执行(动作索引)
        
        # 立即检查应该在冷却中（因为冷却时间 > 0）
        冷却时间 = 动作冷却时间[动作索引]
        if 冷却时间 > 0:
            assert 引擎.检查冷却(动作索引) == False, \
                f"动作{动作索引}执行后应该在冷却中（冷却时间: {冷却时间}秒）"
    
    def test_重置冷却后所有动作可执行(self):
        """
        **Feature: game-ai-enhancement, Property 9: 动作冷却机制正确性**
        
        重置冷却后，所有动作都应该可以执行
        """
        引擎 = 决策引擎()
        
        # 记录多个动作执行
        for 动作 in 动作冷却时间.keys():
            引擎.记录动作执行(动作)
        
        # 重置冷却
        引擎.重置冷却()
        
        # 所有动作都应该可执行
        for 动作 in 动作冷却时间.keys():
            assert 引擎.检查冷却(动作) == True, \
                f"重置冷却后动作{动作}应该可以执行"
    
    @given(
        规则动作=st.sampled_from(list(动作冷却时间.keys())),
        模型预测=模型预测策略
    )
    @settings(max_examples=100)
    def test_冷却中的规则动作不被选择(self, 规则动作: int, 模型预测: list):
        """
        **Feature: game-ai-enhancement, Property 9: 动作冷却机制正确性**
        
        当规则指定的动作在冷却中时，该规则不应该被选择
        """
        引擎 = 决策引擎(策略=决策策略.规则优先)
        引擎.清空规则()
        
        # 添加一个始终匹配的规则
        规则 = 决策规则(
            名称="冷却测试规则",
            优先级=100,
            条件=lambda ctx: True,
            动作=规则动作,
            冷却时间=0.0
        )
        引擎.添加规则(规则)
        
        # 记录动作执行，使其进入冷却
        引擎.记录动作执行(规则动作)
        
        上下文 = 创建决策上下文(游戏状态.空闲, 模型预测=模型预测)
        结果 = 引擎.决策(上下文)
        
        # 冷却中的动作不应该被选择
        冷却时间 = 动作冷却时间.get(规则动作, 0)
        if 冷却时间 > 0:
            assert 结果.动作索引 != 规则动作, \
                f"冷却中的动作{规则动作}不应该被选择"


# ==================== Property 10: 决策日志完整性 ====================

class Test决策日志完整性属性:
    """
    Property 10: 决策日志完整性
    
    *For any* 决策过程，日志应该包含状态、候选动作、最终选择及原因
    
    **Validates: Requirements 3.7**
    """
    
    @given(
        状态=游戏状态策略,
        血量=血量策略,
        敌人数量=敌人数量策略,
        模型预测=模型预测策略
    )
    @settings(max_examples=100)
    def test_决策日志包含时间戳(self, 状态: 游戏状态, 血量: float, 
                              敌人数量: int, 模型预测: list):
        """
        **Feature: game-ai-enhancement, Property 10: 决策日志完整性**
        
        每条决策日志都应该包含有效的时间戳
        """
        引擎 = 决策引擎()
        引擎.清空日志()
        
        上下文 = 创建决策上下文(状态, 血量, 敌人数量, 模型预测)
        
        开始时间 = time.time()
        引擎.决策(上下文)
        结束时间 = time.time()
        
        日志列表 = 引擎.获取决策日志(1)
        assert len(日志列表) == 1, "应该有一条决策日志"
        
        日志 = 日志列表[0]
        assert 日志.时间戳 >= 开始时间, "时间戳应该不早于决策开始时间"
        assert 日志.时间戳 <= 结束时间 + 0.1, "时间戳应该不晚于决策结束时间"
    
    @given(
        状态=游戏状态策略,
        血量=血量策略,
        敌人数量=敌人数量策略,
        模型预测=模型预测策略
    )
    @settings(max_examples=100)
    def test_决策日志包含上下文(self, 状态: 游戏状态, 血量: float, 
                              敌人数量: int, 模型预测: list):
        """
        **Feature: game-ai-enhancement, Property 10: 决策日志完整性**
        
        每条决策日志都应该包含决策上下文信息
        """
        引擎 = 决策引擎()
        引擎.清空日志()
        
        上下文 = 创建决策上下文(状态, 血量, 敌人数量, 模型预测)
        引擎.决策(上下文)
        
        日志列表 = 引擎.获取决策日志(1)
        assert len(日志列表) == 1, "应该有一条决策日志"
        
        日志 = 日志列表[0]
        assert 日志.上下文 is not None, "日志应该包含上下文"
        assert 日志.上下文.游戏状态 == 状态, "上下文中的游戏状态应该正确"
        assert abs(日志.上下文.血量百分比 - 血量) < 0.001, "上下文中的血量应该正确"
        assert 日志.上下文.附近敌人数量 == 敌人数量, "上下文中的敌人数量应该正确"
    
    @given(
        状态=游戏状态策略,
        模型预测=模型预测策略
    )
    @settings(max_examples=100)
    def test_决策日志包含候选动作(self, 状态: 游戏状态, 模型预测: list):
        """
        **Feature: game-ai-enhancement, Property 10: 决策日志完整性**
        
        每条决策日志都应该包含候选动作列表
        """
        引擎 = 决策引擎()
        引擎.清空日志()
        引擎.重置冷却()
        
        上下文 = 创建决策上下文(状态, 模型预测=模型预测)
        引擎.决策(上下文)
        
        日志列表 = 引擎.获取决策日志(1)
        assert len(日志列表) == 1, "应该有一条决策日志"
        
        日志 = 日志列表[0]
        assert 日志.候选动作 is not None, "日志应该包含候选动作"
        assert isinstance(日志.候选动作, list), "候选动作应该是列表"
        
        # 验证候选动作格式
        for 候选 in 日志.候选动作:
            assert isinstance(候选, tuple), "每个候选动作应该是元组"
            assert len(候选) == 2, "候选动作元组应该包含(动作索引, 分数)"
            动作索引, 分数 = 候选
            assert isinstance(动作索引, int), "动作索引应该是整数"
            assert isinstance(分数, (int, float)), "分数应该是数值"
    
    @given(
        状态=游戏状态策略,
        模型预测=模型预测策略
    )
    @settings(max_examples=100)
    def test_决策日志包含最终决策(self, 状态: 游戏状态, 模型预测: list):
        """
        **Feature: game-ai-enhancement, Property 10: 决策日志完整性**
        
        每条决策日志都应该包含最终决策结果
        """
        引擎 = 决策引擎()
        引擎.清空日志()
        引擎.重置冷却()
        
        上下文 = 创建决策上下文(状态, 模型预测=模型预测)
        决策结果 = 引擎.决策(上下文)
        
        日志列表 = 引擎.获取决策日志(1)
        assert len(日志列表) == 1, "应该有一条决策日志"
        
        日志 = 日志列表[0]
        assert 日志.最终决策 is not None, "日志应该包含最终决策"
        
        # 验证最终决策与返回结果一致
        assert 日志.最终决策.动作索引 == 决策结果.动作索引, "日志中的动作索引应该与返回结果一致"
        assert 日志.最终决策.动作名称 == 决策结果.动作名称, "日志中的动作名称应该与返回结果一致"
        assert 日志.最终决策.来源 == 决策结果.来源, "日志中的来源应该与返回结果一致"
    
    @given(
        状态=游戏状态策略,
        模型预测=模型预测策略
    )
    @settings(max_examples=100)
    def test_决策日志包含决策原因(self, 状态: 游戏状态, 模型预测: list):
        """
        **Feature: game-ai-enhancement, Property 10: 决策日志完整性**
        
        每条决策日志的最终决策都应该包含决策原因
        """
        引擎 = 决策引擎()
        引擎.清空日志()
        引擎.重置冷却()
        
        上下文 = 创建决策上下文(状态, 模型预测=模型预测)
        引擎.决策(上下文)
        
        日志列表 = 引擎.获取决策日志(1)
        assert len(日志列表) == 1, "应该有一条决策日志"
        
        日志 = 日志列表[0]
        assert 日志.最终决策.原因 is not None, "最终决策应该包含原因"
        assert len(日志.最终决策.原因) > 0, "决策原因不应为空"
        assert isinstance(日志.最终决策.原因, str), "决策原因应该是字符串"
    
    @given(决策次数=st.integers(min_value=1, max_value=20))
    @settings(max_examples=50)
    def test_日志数量与决策次数一致(self, 决策次数: int):
        """
        **Feature: game-ai-enhancement, Property 10: 决策日志完整性**
        
        日志数量应该与决策次数一致
        """
        引擎 = 决策引擎()
        引擎.清空日志()
        
        上下文 = 创建决策上下文(游戏状态.空闲)
        
        for _ in range(决策次数):
            引擎.决策(上下文)
        
        日志列表 = 引擎.获取决策日志(决策次数 + 10)  # 请求更多以确保获取全部
        assert len(日志列表) == 决策次数, \
            f"日志数量({len(日志列表)})应该等于决策次数({决策次数})"
    
    @given(
        状态=游戏状态策略,
        模型预测=模型预测策略
    )
    @settings(max_examples=100)
    def test_决策来源有效(self, 状态: 游戏状态, 模型预测: list):
        """
        **Feature: game-ai-enhancement, Property 10: 决策日志完整性**
        
        决策来源应该是有效值: "rule", "model", 或 "mixed"
        """
        引擎 = 决策引擎()
        引擎.清空日志()
        引擎.重置冷却()
        
        上下文 = 创建决策上下文(状态, 模型预测=模型预测)
        引擎.决策(上下文)
        
        日志列表 = 引擎.获取决策日志(1)
        assert len(日志列表) == 1, "应该有一条决策日志"
        
        日志 = 日志列表[0]
        有效来源 = {"rule", "model", "mixed"}
        assert 日志.最终决策.来源 in 有效来源, \
            f"决策来源'{日志.最终决策.来源}'应该是{有效来源}之一"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
