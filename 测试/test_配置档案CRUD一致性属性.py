# -*- coding: utf-8 -*-
"""
属性测试：配置档案CRUD一致性
Property 6: 对于任意 GameProfile，创建后必须能通过 load_profile 加载到相同数据；
删除后 load_profile 必须失败或返回空。

**Feature: smart-training-system, Property 6: 配置档案CRUD一致性**
**验证: 需求 4.1, 4.2, 4.3, 4.6**
"""

import sys
import os
import tempfile
import shutil

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from hypothesis import given, strategies as st, settings, assume
from typing import Dict, Any

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

# 有效的UI区域策略
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

# 有效的检测参数策略
有效检测参数策略 = st.builds(
    DetectionParams,
    yolo_model_path=st.just("模型/预训练模型/yolo.pt"),
    confidence_threshold=st.floats(min_value=0.1, max_value=0.9, allow_nan=False, allow_infinity=False)
)

# 有效的决策规则策略
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


class Test配置档案CRUD一致性属性:
    """
    Property 6: 配置档案CRUD一致性
    
    *对于任意* GameProfile，创建后必须能通过 load_profile 加载到相同数据；
    删除后 load_profile 必须失败或返回空。
    
    **Feature: smart-training-system, Property 6: 配置档案CRUD一致性**
    **验证: 需求 4.1, 4.2, 4.3, 4.6**
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
    @settings(max_examples=100)
    def test_创建保存后加载应返回相同数据(
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
        *对于任意* 有效的 GameProfile，创建并保存后，
        通过 load_profile 加载必须得到相同的数据。
        
        **Feature: smart-training-system, Property 6: 配置档案CRUD一致性**
        **验证: 需求 4.1, 4.2, 4.6**
        """
        test_dir = tempfile.mkdtemp()
        profiles_dir = os.path.join(test_dir, 'profiles')
        
        try:
            # 创建配置管理器
            manager = ConfigManager(profiles_dir=profiles_dir, auto_load_last=False)
            
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
            save_result = manager.save_profile(profile)
            assert save_result, "保存档案应该成功"
            
            # 加载档案
            loaded_profile = manager.load_profile(name)
            
            # 验证关键字段相同
            assert loaded_profile.name == profile.name, \
                f"名称不匹配: 期望 {profile.name}, 实际 {loaded_profile.name}"
            assert loaded_profile.game_name == profile.game_name, \
                f"游戏名称不匹配: 期望 {profile.game_name}, 实际 {loaded_profile.game_name}"
            
            # 验证窗口配置
            assert loaded_profile.window_config.x == profile.window_config.x
            assert loaded_profile.window_config.y == profile.window_config.y
            assert loaded_profile.window_config.width == profile.window_config.width
            assert loaded_profile.window_config.height == profile.window_config.height
            
            # 验证按键映射
            assert loaded_profile.key_mapping.move_keys == profile.key_mapping.move_keys
            assert loaded_profile.key_mapping.skill_keys == profile.key_mapping.skill_keys
            assert loaded_profile.key_mapping.interact_key == profile.key_mapping.interact_key
            
            # 验证UI区域
            assert loaded_profile.ui_regions.health_bar == profile.ui_regions.health_bar
            assert loaded_profile.ui_regions.skill_bar == profile.ui_regions.skill_bar
            assert loaded_profile.ui_regions.dialog_area == profile.ui_regions.dialog_area
            assert loaded_profile.ui_regions.minimap == profile.ui_regions.minimap
            
            # 验证检测参数
            assert loaded_profile.detection_params.yolo_model_path == profile.detection_params.yolo_model_path
            assert abs(loaded_profile.detection_params.confidence_threshold - 
                      profile.detection_params.confidence_threshold) < 1e-6
            
            # 验证决策规则
            assert loaded_profile.decision_rules.state_priorities == profile.decision_rules.state_priorities
            # 浮点数比较需要容差
            for key in profile.decision_rules.action_weights:
                assert abs(loaded_profile.decision_rules.action_weights[key] - 
                          profile.decision_rules.action_weights[key]) < 1e-6
            
        finally:
            shutil.rmtree(test_dir, ignore_errors=True)
    
    @given(
        name=有效档案名称策略,
        game_name=有效游戏名称策略
    )
    @settings(max_examples=100)
    def test_删除后加载应失败(
        self,
        name: str,
        game_name: str
    ):
        """
        *对于任意* 已删除的 GameProfile，load_profile 必须抛出 FileNotFoundError。
        
        **Feature: smart-training-system, Property 6: 配置档案CRUD一致性**
        **验证: 需求 4.3, 4.6**
        """
        test_dir = tempfile.mkdtemp()
        profiles_dir = os.path.join(test_dir, 'profiles')
        
        try:
            # 创建配置管理器
            manager = ConfigManager(profiles_dir=profiles_dir, auto_load_last=False)
            
            # 创建并保存档案
            profile = manager.create_profile(name, game_name)
            manager.save_profile(profile)
            
            # 确认档案存在
            assert manager.profile_exists(name), "档案应该存在"
            
            # 删除档案
            delete_result = manager.delete_profile(name)
            assert delete_result, "删除档案应该成功"
            
            # 确认档案不存在
            assert not manager.profile_exists(name), "档案应该已被删除"
            
            # 尝试加载已删除的档案应该失败
            with pytest.raises(FileNotFoundError):
                manager.load_profile(name)
            
        finally:
            shutil.rmtree(test_dir, ignore_errors=True)
    
    @given(
        name=有效档案名称策略,
        game_name=有效游戏名称策略
    )
    @settings(max_examples=100)
    def test_列表应包含已创建的档案(
        self,
        name: str,
        game_name: str
    ):
        """
        *对于任意* 已创建并保存的 GameProfile，list_profiles 必须包含该档案名称。
        
        **Feature: smart-training-system, Property 6: 配置档案CRUD一致性**
        **验证: 需求 4.1, 4.2**
        """
        test_dir = tempfile.mkdtemp()
        profiles_dir = os.path.join(test_dir, 'profiles')
        
        try:
            manager = ConfigManager(profiles_dir=profiles_dir, auto_load_last=False)
            
            # 创建并保存档案
            profile = manager.create_profile(name, game_name)
            manager.save_profile(profile)
            
            # 获取档案列表
            profiles_list = manager.list_profiles()
            
            # 验证列表包含该档案
            assert name in profiles_list, \
                f"档案列表应包含 '{name}'，实际列表: {profiles_list}"
            
        finally:
            shutil.rmtree(test_dir, ignore_errors=True)
    
    @given(
        name=有效档案名称策略,
        game_name=有效游戏名称策略
    )
    @settings(max_examples=100)
    def test_删除后列表不应包含该档案(
        self,
        name: str,
        game_name: str
    ):
        """
        *对于任意* 已删除的 GameProfile，list_profiles 不应包含该档案名称。
        
        **Feature: smart-training-system, Property 6: 配置档案CRUD一致性**
        **验证: 需求 4.3**
        """
        test_dir = tempfile.mkdtemp()
        profiles_dir = os.path.join(test_dir, 'profiles')
        
        try:
            manager = ConfigManager(profiles_dir=profiles_dir, auto_load_last=False)
            
            # 创建并保存档案
            profile = manager.create_profile(name, game_name)
            manager.save_profile(profile)
            
            # 删除档案
            manager.delete_profile(name)
            
            # 获取档案列表
            profiles_list = manager.list_profiles()
            
            # 验证列表不包含该档案
            assert name not in profiles_list, \
                f"档案列表不应包含已删除的 '{name}'，实际列表: {profiles_list}"
            
        finally:
            shutil.rmtree(test_dir, ignore_errors=True)
    
    @given(
        name=有效档案名称策略,
        game_name=有效游戏名称策略,
        new_game_name=有效游戏名称策略
    )
    @settings(max_examples=100)
    def test_更新保存后加载应返回更新后的数据(
        self,
        name: str,
        game_name: str,
        new_game_name: str
    ):
        """
        *对于任意* GameProfile，更新并保存后，load_profile 必须返回更新后的数据。
        
        **Feature: smart-training-system, Property 6: 配置档案CRUD一致性**
        **验证: 需求 4.2, 4.6**
        """
        # 确保新旧游戏名称不同
        assume(game_name.strip() != new_game_name.strip())
        
        test_dir = tempfile.mkdtemp()
        profiles_dir = os.path.join(test_dir, 'profiles')
        
        try:
            manager = ConfigManager(profiles_dir=profiles_dir, auto_load_last=False)
            
            # 创建并保存初始档案
            profile = manager.create_profile(name, game_name)
            manager.save_profile(profile)
            
            # 加载档案
            loaded_profile = manager.load_profile(name)
            
            # 修改游戏名称
            loaded_profile.game_name = new_game_name
            
            # 保存更新后的档案
            manager.save_profile(loaded_profile)
            
            # 重新加载
            reloaded_profile = manager.load_profile(name)
            
            # 验证更新后的数据
            assert reloaded_profile.game_name == new_game_name, \
                f"游戏名称应为 '{new_game_name}'，实际为 '{reloaded_profile.game_name}'"
            
        finally:
            shutil.rmtree(test_dir, ignore_errors=True)


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--hypothesis-show-statistics'])
