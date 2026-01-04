# -*- coding: utf-8 -*-
"""
属性测试：配置切换即时生效
Property 9: 对于任意配置切换操作，switch_profile 成功后 get_current_profile 必须返回新切换的档案。

**Feature: smart-training-system, Property 9: 配置切换即时生效**
**验证: 需求 6.2**
"""

import sys
import os
import tempfile
import shutil

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from hypothesis import given, strategies as st, settings, assume
from typing import List

from 核心.配置管理 import (
    ConfigManager,
    GameProfile,
    WindowConfig,
    KeyMapping,
    UIRegions,
    DetectionParams,
    DecisionRules
)


# ==================== 数据生成策略 ====================

# 有效的档案名称策略（避免特殊字符导致文件系统问题）
有效档案名称策略 = st.text(
    min_size=1,
    max_size=30,
    alphabet="abcdefghijklmnopqrstuvwxyz0123456789_-"
).filter(lambda x: x.strip() != "" and len(x.strip()) > 0)

# 有效的游戏名称策略
有效游戏名称策略 = st.text(
    min_size=1,
    max_size=30,
    alphabet="abcdefghijklmnopqrstuvwxyz0123456789_- "
).filter(lambda x: x.strip() != "")

# 有效的窗口配置策略
有效窗口配置策略 = st.builds(
    WindowConfig,
    x=st.integers(min_value=0, max_value=1000),
    y=st.integers(min_value=0, max_value=500),
    width=st.integers(min_value=640, max_value=3840),
    height=st.integers(min_value=480, max_value=2160)
)

# 有效的按键映射策略
有效按键映射策略 = st.builds(
    KeyMapping,
    move_keys=st.fixed_dictionaries({
        "W": st.just("up"),
        "S": st.just("down"),
        "A": st.just("left"),
        "D": st.just("right")
    }),
    skill_keys=st.fixed_dictionaries({
        "1": st.just("skill1"),
        "2": st.just("skill2"),
        "3": st.just("skill3"),
        "4": st.just("skill4")
    }),
    interact_key=st.sampled_from(["F", "E", "G", "R"])
)


def 生成有效区域():
    """生成有效的UI区域元组 (x, y, width, height)"""
    return st.tuples(
        st.integers(min_value=0, max_value=1000),
        st.integers(min_value=0, max_value=500),
        st.integers(min_value=10, max_value=500),
        st.integers(min_value=10, max_value=300)
    )


有效UI区域策略 = st.builds(
    UIRegions,
    health_bar=生成有效区域(),
    skill_bar=生成有效区域(),
    dialog_area=生成有效区域(),
    minimap=生成有效区域()
)

有效检测参数策略 = st.builds(
    DetectionParams,
    yolo_model_path=st.just("模型/预训练模型/yolo.pt"),
    confidence_threshold=st.floats(min_value=0.1, max_value=0.9, allow_nan=False, allow_infinity=False)
)

有效决策规则策略 = st.builds(
    DecisionRules,
    state_priorities=st.fixed_dictionaries({
        "combat": st.integers(min_value=1, max_value=10),
        "dialog": st.integers(min_value=1, max_value=10),
        "looting": st.integers(min_value=1, max_value=10),
        "moving": st.integers(min_value=1, max_value=10),
        "idle": st.integers(min_value=1, max_value=10)
    }),
    action_weights=st.fixed_dictionaries({
        "skill": st.floats(min_value=0.1, max_value=1.0, allow_nan=False, allow_infinity=False),
        "move": st.floats(min_value=0.1, max_value=1.0, allow_nan=False, allow_infinity=False),
        "interact": st.floats(min_value=0.1, max_value=1.0, allow_nan=False, allow_infinity=False),
        "wait": st.floats(min_value=0.1, max_value=1.0, allow_nan=False, allow_infinity=False)
    })
)


class Test配置切换即时生效属性:
    """
    Property 9: 配置切换即时生效
    
    *对于任意* 配置切换操作，switch_profile 成功后 get_current_profile 必须返回新切换的档案。
    
    **Feature: smart-training-system, Property 9: 配置切换即时生效**
    **验证: 需求 6.2**
    """
    
    @given(
        name=有效档案名称策略,
        game_name=有效游戏名称策略,
        window_config=有效窗口配置策略,
        key_mapping=有效按键映射策略,
        ui_regions=有效UI区域策略,
        detection_params=有效检测参数策略,
        decision_rules=有效决策规则策略
    )
    @settings(max_examples=100, deadline=None)
    def test_切换后get_current_profile返回新档案(
        self,
        name: str,
        game_name: str,
        window_config: WindowConfig,
        key_mapping: KeyMapping,
        ui_regions: UIRegions,
        detection_params: DetectionParams,
        decision_rules: DecisionRules
    ):
        """
        *对于任意* 有效的 GameProfile，switch_profile 成功后，
        get_current_profile 必须返回新切换的档案。
        
        **Feature: smart-training-system, Property 9: 配置切换即时生效**
        **验证: 需求 6.2**
        """
        test_dir = tempfile.mkdtemp()
        profiles_dir = os.path.join(test_dir, 'profiles')
        last_profile_file = os.path.join(test_dir, 'last_profile.txt')
        
        try:
            # 创建配置管理器
            manager = ConfigManager(
                profiles_dir=profiles_dir,
                last_profile_file=last_profile_file,
                auto_load_last=False
            )
            
            # 创建配置档案
            profile = GameProfile(
                name=name,
                game_name=game_name,
                window_config=window_config,
                key_mapping=key_mapping,
                ui_regions=ui_regions,
                detection_params=detection_params,
                decision_rules=decision_rules
            )
            
            # 保存档案
            manager.save_profile(profile)
            
            # 切换到该档案
            switch_result = manager.switch_profile(name)
            assert switch_result, "切换档案应该成功"
            
            # 获取当前档案
            current_profile = manager.get_current_profile()
            
            # 验证当前档案不为空
            assert current_profile is not None, "切换后当前档案不应为空"
            
            # 验证当前档案名称与切换的档案一致
            assert current_profile.name == name, \
                f"当前档案名称应为 '{name}'，实际为 '{current_profile.name}'"
            
            # 验证当前档案游戏名称一致
            assert current_profile.game_name == game_name, \
                f"当前档案游戏名称应为 '{game_name}'，实际为 '{current_profile.game_name}'"
            
            # 验证窗口配置一致
            assert current_profile.window_config.x == window_config.x
            assert current_profile.window_config.y == window_config.y
            assert current_profile.window_config.width == window_config.width
            assert current_profile.window_config.height == window_config.height
            
        finally:
            shutil.rmtree(test_dir, ignore_errors=True)
    
    @given(
        name1=有效档案名称策略,
        name2=有效档案名称策略,
        game_name1=有效游戏名称策略,
        game_name2=有效游戏名称策略
    )
    @settings(max_examples=100, deadline=None)
    def test_多次切换后get_current_profile返回最后切换的档案(
        self,
        name1: str,
        name2: str,
        game_name1: str,
        game_name2: str
    ):
        """
        *对于任意* 两个不同的 GameProfile，多次切换后，
        get_current_profile 必须返回最后切换的档案。
        
        **Feature: smart-training-system, Property 9: 配置切换即时生效**
        **验证: 需求 6.2**
        """
        # 确保两个档案名称不同
        assume(name1.strip() != name2.strip())
        
        test_dir = tempfile.mkdtemp()
        profiles_dir = os.path.join(test_dir, 'profiles')
        last_profile_file = os.path.join(test_dir, 'last_profile.txt')
        
        try:
            manager = ConfigManager(
                profiles_dir=profiles_dir,
                last_profile_file=last_profile_file,
                auto_load_last=False
            )
            
            # 创建并保存两个档案
            profile1 = GameProfile(name=name1, game_name=game_name1)
            profile2 = GameProfile(name=name2, game_name=game_name2)
            
            manager.save_profile(profile1)
            manager.save_profile(profile2)
            
            # 切换到第一个档案
            manager.switch_profile(name1)
            current = manager.get_current_profile()
            assert current is not None
            assert current.name == name1, \
                f"切换到 '{name1}' 后，当前档案应为 '{name1}'，实际为 '{current.name}'"
            
            # 切换到第二个档案
            manager.switch_profile(name2)
            current = manager.get_current_profile()
            assert current is not None
            assert current.name == name2, \
                f"切换到 '{name2}' 后，当前档案应为 '{name2}'，实际为 '{current.name}'"
            
            # 再次切换回第一个档案
            manager.switch_profile(name1)
            current = manager.get_current_profile()
            assert current is not None
            assert current.name == name1, \
                f"再次切换到 '{name1}' 后，当前档案应为 '{name1}'，实际为 '{current.name}'"
            
        finally:
            shutil.rmtree(test_dir, ignore_errors=True)
    
    @given(
        name=有效档案名称策略,
        game_name=有效游戏名称策略
    )
    @settings(max_examples=100, deadline=None)
    def test_切换不存在的档案应失败(
        self,
        name: str,
        game_name: str
    ):
        """
        *对于任意* 不存在的档案名称，switch_profile 应该抛出 FileNotFoundError，
        且 get_current_profile 应保持原状态。
        
        **Feature: smart-training-system, Property 9: 配置切换即时生效**
        **验证: 需求 6.2**
        """
        test_dir = tempfile.mkdtemp()
        profiles_dir = os.path.join(test_dir, 'profiles')
        last_profile_file = os.path.join(test_dir, 'last_profile.txt')
        
        try:
            manager = ConfigManager(
                profiles_dir=profiles_dir,
                last_profile_file=last_profile_file,
                auto_load_last=False
            )
            
            # 创建并保存一个档案
            profile = GameProfile(name=name, game_name=game_name)
            manager.save_profile(profile)
            
            # 切换到该档案
            manager.switch_profile(name)
            
            # 记录当前档案
            current_before = manager.get_current_profile()
            assert current_before is not None
            
            # 尝试切换到不存在的档案
            non_existent_name = f"{name}_nonexistent_xyz123"
            with pytest.raises(FileNotFoundError):
                manager.switch_profile(non_existent_name)
            
            # 验证当前档案保持不变
            current_after = manager.get_current_profile()
            assert current_after is not None
            assert current_after.name == current_before.name, \
                "切换失败后，当前档案应保持不变"
            
        finally:
            shutil.rmtree(test_dir, ignore_errors=True)


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--hypothesis-show-statistics'])
