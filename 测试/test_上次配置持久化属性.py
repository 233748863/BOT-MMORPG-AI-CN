# -*- coding: utf-8 -*-
"""
属性测试：上次配置持久化
Property 10: 对于任意配置切换操作，切换后的档案名必须被持久化，重新初始化 ConfigManager 后必须自动加载该档案。

**Feature: smart-training-system, Property 10: 上次配置持久化**
**验证: 需求 6.4**
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


class Test上次配置持久化属性:
    """
    Property 10: 上次配置持久化
    
    *对于任意* 配置切换操作，切换后的档案名必须被持久化，
    重新初始化 ConfigManager 后必须自动加载该档案。
    
    **Feature: smart-training-system, Property 10: 上次配置持久化**
    **验证: 需求 6.4**
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
    def test_切换后重新初始化自动加载上次档案(
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
        *对于任意* 有效的 GameProfile，切换档案后重新初始化 ConfigManager，
        必须自动加载上次切换的档案。
        
        **Feature: smart-training-system, Property 10: 上次配置持久化**
        **验证: 需求 6.4**
        """
        test_dir = tempfile.mkdtemp()
        profiles_dir = os.path.join(test_dir, 'profiles')
        last_profile_file = os.path.join(test_dir, 'last_profile.txt')
        
        try:
            # 第一个配置管理器实例：创建并切换档案
            manager1 = ConfigManager(
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
            manager1.save_profile(profile)
            
            # 切换到该档案（这会持久化上次使用的档案名）
            switch_result = manager1.switch_profile(name)
            assert switch_result, "切换档案应该成功"
            
            # 验证上次档案文件已被写入
            assert os.path.exists(last_profile_file), "上次档案记录文件应该存在"
            
            # 第二个配置管理器实例：启用自动加载
            manager2 = ConfigManager(
                profiles_dir=profiles_dir,
                last_profile_file=last_profile_file,
                auto_load_last=True  # 启用自动加载
            )
            
            # 获取当前档案
            current_profile = manager2.get_current_profile()
            
            # 验证自动加载成功
            assert current_profile is not None, \
                "重新初始化后应自动加载上次使用的档案"
            
            # 验证加载的档案名称正确
            assert current_profile.name == name, \
                f"自动加载的档案名称应为 '{name}'，实际为 '{current_profile.name}'"
            
            # 验证加载的档案游戏名称正确
            assert current_profile.game_name == game_name, \
                f"自动加载的档案游戏名称应为 '{game_name}'，实际为 '{current_profile.game_name}'"
            
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
    @settings(max_examples=100)
    def test_多次切换后持久化最后一个档案(
        self,
        name1: str,
        name2: str,
        game_name1: str,
        game_name2: str
    ):
        """
        *对于任意* 两个不同的 GameProfile，多次切换后，
        重新初始化 ConfigManager 必须自动加载最后切换的档案。
        
        **Feature: smart-training-system, Property 10: 上次配置持久化**
        **验证: 需求 6.4**
        """
        # 确保两个档案名称不同
        assume(name1.strip() != name2.strip())
        
        test_dir = tempfile.mkdtemp()
        profiles_dir = os.path.join(test_dir, 'profiles')
        last_profile_file = os.path.join(test_dir, 'last_profile.txt')
        
        try:
            # 第一个配置管理器实例
            manager1 = ConfigManager(
                profiles_dir=profiles_dir,
                last_profile_file=last_profile_file,
                auto_load_last=False
            )
            
            # 创建并保存两个档案
            profile1 = GameProfile(name=name1, game_name=game_name1)
            profile2 = GameProfile(name=name2, game_name=game_name2)
            
            manager1.save_profile(profile1)
            manager1.save_profile(profile2)
            
            # 切换到第一个档案
            manager1.switch_profile(name1)
            
            # 切换到第二个档案（最后一次切换）
            manager1.switch_profile(name2)
            
            # 第二个配置管理器实例：启用自动加载
            manager2 = ConfigManager(
                profiles_dir=profiles_dir,
                last_profile_file=last_profile_file,
                auto_load_last=True
            )
            
            # 获取当前档案
            current_profile = manager2.get_current_profile()
            
            # 验证自动加载的是最后切换的档案
            assert current_profile is not None, \
                "重新初始化后应自动加载上次使用的档案"
            assert current_profile.name == name2, \
                f"应自动加载最后切换的档案 '{name2}'，实际为 '{current_profile.name}'"
            
        finally:
            shutil.rmtree(test_dir, ignore_errors=True)
    
    @given(
        name=有效档案名称策略,
        game_name=有效游戏名称策略
    )
    @settings(max_examples=100)
    def test_上次档案文件内容正确(
        self,
        name: str,
        game_name: str
    ):
        """
        *对于任意* 配置切换操作，上次档案记录文件的内容必须是切换的档案名称。
        
        **Feature: smart-training-system, Property 10: 上次配置持久化**
        **验证: 需求 6.4**
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
            
            # 创建并保存档案
            profile = GameProfile(name=name, game_name=game_name)
            manager.save_profile(profile)
            
            # 切换到该档案
            manager.switch_profile(name)
            
            # 读取上次档案记录文件
            assert os.path.exists(last_profile_file), "上次档案记录文件应该存在"
            
            with open(last_profile_file, 'r', encoding='utf-8') as f:
                saved_name = f.read().strip()
            
            # 验证文件内容是档案名称
            assert saved_name == name, \
                f"上次档案记录文件内容应为 '{name}'，实际为 '{saved_name}'"
            
        finally:
            shutil.rmtree(test_dir, ignore_errors=True)
    
    @given(
        name=有效档案名称策略,
        game_name=有效游戏名称策略
    )
    @settings(max_examples=100)
    def test_档案被删除后重新初始化不崩溃(
        self,
        name: str,
        game_name: str
    ):
        """
        *对于任意* 配置切换操作，如果上次使用的档案被删除，
        重新初始化 ConfigManager 不应崩溃，且当前档案应为 None。
        
        **Feature: smart-training-system, Property 10: 上次配置持久化**
        **验证: 需求 6.4**
        """
        test_dir = tempfile.mkdtemp()
        profiles_dir = os.path.join(test_dir, 'profiles')
        last_profile_file = os.path.join(test_dir, 'last_profile.txt')
        
        try:
            # 第一个配置管理器实例
            manager1 = ConfigManager(
                profiles_dir=profiles_dir,
                last_profile_file=last_profile_file,
                auto_load_last=False
            )
            
            # 创建并保存档案
            profile = GameProfile(name=name, game_name=game_name)
            manager1.save_profile(profile)
            
            # 切换到该档案
            manager1.switch_profile(name)
            
            # 删除档案文件
            manager1.delete_profile(name)
            
            # 第二个配置管理器实例：启用自动加载
            # 这不应该崩溃，即使上次使用的档案已被删除
            manager2 = ConfigManager(
                profiles_dir=profiles_dir,
                last_profile_file=last_profile_file,
                auto_load_last=True
            )
            
            # 当前档案应为 None（因为上次的档案已被删除）
            current_profile = manager2.get_current_profile()
            assert current_profile is None, \
                "上次档案被删除后，重新初始化时当前档案应为 None"
            
        finally:
            shutil.rmtree(test_dir, ignore_errors=True)


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--hypothesis-show-statistics'])
