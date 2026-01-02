# -*- coding: utf-8 -*-
"""
属性测试：配置档案完整性
Property 8: 对于任意 GameProfile，必须包含所有必要字段：
window_config、key_mapping、ui_regions、detection_params、decision_rules。

**Feature: smart-training-system, Property 8: 配置档案完整性**
**验证: 需求 5.1, 5.2, 5.3, 5.4, 5.5**
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from hypothesis import given, strategies as st, settings, assume
from typing import Dict, Any, Optional

from 核心.配置管理 import (
    GameProfile,
    WindowConfig,
    KeyMapping,
    UIRegions,
    DetectionParams,
    DecisionRules
)


# ==================== 数据生成策略 ====================

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
    skill_keys=st.dictionaries(
        keys=st.sampled_from(["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"]),
        values=st.text(min_size=1, max_size=20, alphabet="abcdefghijklmnopqrstuvwxyz_"),
        min_size=1,
        max_size=10
    ),
    interact_key=st.sampled_from(["F", "E", "G", "R", "Space"])
)

# 有效的UI区域策略（确保宽高为正数）
def 生成有效区域():
    """生成有效的UI区域元组 (x, y, width, height)"""
    return st.tuples(
        st.integers(min_value=0, max_value=1000),  # x
        st.integers(min_value=0, max_value=500),   # y
        st.integers(min_value=10, max_value=500),  # width > 0
        st.integers(min_value=10, max_value=300)   # height > 0
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
    yolo_model_path=st.text(min_size=1, max_size=100, alphabet="abcdefghijklmnopqrstuvwxyz0123456789_/.-"),
    confidence_threshold=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)
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
        "skill": st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
        "move": st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
        "interact": st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
        "wait": st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)
    })
)

# 有效的档案名称策略
有效档案名称策略 = st.text(
    min_size=1,
    max_size=50,
    alphabet="abcdefghijklmnopqrstuvwxyz0123456789_-中文测试游戏"
).filter(lambda x: x.strip() != "")

# 有效的游戏名称策略
有效游戏名称策略 = st.text(
    min_size=1,
    max_size=50,
    alphabet="abcdefghijklmnopqrstuvwxyz0123456789_- 中文测试游戏"
).filter(lambda x: x.strip() != "")


class Test配置档案完整性属性:
    """
    Property 8: 配置档案完整性
    
    *对于任意* GameProfile，必须包含所有必要字段：
    window_config、key_mapping、ui_regions、detection_params、decision_rules。
    
    **Feature: smart-training-system, Property 8: 配置档案完整性**
    **验证: 需求 5.1, 5.2, 5.3, 5.4, 5.5**
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
    def test_完整配置档案应包含所有必要字段(
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
        *对于任意* 有效的配置组件，创建的 GameProfile 必须包含所有必要字段。
        
        **Feature: smart-training-system, Property 8: 配置档案完整性**
        **验证: 需求 5.1, 5.2, 5.3, 5.4, 5.5**
        """
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
        
        # 验证所有必要字段都存在且不为 None
        assert profile.window_config is not None, "window_config 不应为 None"
        assert profile.key_mapping is not None, "key_mapping 不应为 None"
        assert profile.ui_regions is not None, "ui_regions 不应为 None"
        assert profile.detection_params is not None, "detection_params 不应为 None"
        assert profile.decision_rules is not None, "decision_rules 不应为 None"
        
        # 验证完整性检查方法返回 True
        is_complete, missing_fields = profile.validate_completeness()
        assert is_complete, f"配置档案应该完整，但缺少字段: {missing_fields}"
        assert len(missing_fields) == 0, f"不应有缺失字段，但发现: {missing_fields}"
    
    @given(
        name=有效档案名称策略,
        game_name=有效游戏名称策略
    )
    @settings(max_examples=100)
    def test_默认创建的配置档案应包含所有必要字段(
        self,
        name: str,
        game_name: str
    ):
        """
        *对于任意* 有效的档案名称和游戏名称，使用默认值创建的 GameProfile 
        必须包含所有必要字段。
        
        **Feature: smart-training-system, Property 8: 配置档案完整性**
        **验证: 需求 5.1, 5.2, 5.3, 5.4, 5.5**
        """
        # 使用默认值创建配置档案
        profile = GameProfile(name=name, game_name=game_name)
        
        # 验证所有必要字段都存在且不为 None
        assert profile.window_config is not None, "window_config 不应为 None"
        assert profile.key_mapping is not None, "key_mapping 不应为 None"
        assert profile.ui_regions is not None, "ui_regions 不应为 None"
        assert profile.detection_params is not None, "detection_params 不应为 None"
        assert profile.decision_rules is not None, "decision_rules 不应为 None"
        
        # 验证完整性检查方法返回 True
        is_complete, missing_fields = profile.validate_completeness()
        assert is_complete, f"默认配置档案应该完整，但缺少字段: {missing_fields}"
    
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
    def test_配置档案字段类型正确(
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
        *对于任意* 有效的配置组件，GameProfile 的各字段类型必须正确。
        
        **Feature: smart-training-system, Property 8: 配置档案完整性**
        **验证: 需求 5.1, 5.2, 5.3, 5.4, 5.5**
        """
        profile = GameProfile(
            name=name,
            game_name=game_name,
            window_config=window_config,
            key_mapping=key_mapping,
            ui_regions=ui_regions,
            detection_params=detection_params,
            decision_rules=decision_rules
        )
        
        # 验证字段类型
        assert isinstance(profile.window_config, WindowConfig), \
            f"window_config 应为 WindowConfig 类型，实际为 {type(profile.window_config)}"
        assert isinstance(profile.key_mapping, KeyMapping), \
            f"key_mapping 应为 KeyMapping 类型，实际为 {type(profile.key_mapping)}"
        assert isinstance(profile.ui_regions, UIRegions), \
            f"ui_regions 应为 UIRegions 类型，实际为 {type(profile.ui_regions)}"
        assert isinstance(profile.detection_params, DetectionParams), \
            f"detection_params 应为 DetectionParams 类型，实际为 {type(profile.detection_params)}"
        assert isinstance(profile.decision_rules, DecisionRules), \
            f"decision_rules 应为 DecisionRules 类型，实际为 {type(profile.decision_rules)}"
    
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
    def test_窗口配置包含必要属性(
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
        *对于任意* GameProfile，其 window_config 必须包含 x、y、width、height 属性。
        
        **Feature: smart-training-system, Property 8: 配置档案完整性**
        **验证: 需求 5.1**
        """
        profile = GameProfile(
            name=name,
            game_name=game_name,
            window_config=window_config,
            key_mapping=key_mapping,
            ui_regions=ui_regions,
            detection_params=detection_params,
            decision_rules=decision_rules
        )
        
        # 验证窗口配置包含必要属性
        assert hasattr(profile.window_config, 'x'), "window_config 应包含 x 属性"
        assert hasattr(profile.window_config, 'y'), "window_config 应包含 y 属性"
        assert hasattr(profile.window_config, 'width'), "window_config 应包含 width 属性"
        assert hasattr(profile.window_config, 'height'), "window_config 应包含 height 属性"
        
        # 验证窗口尺寸为正数
        assert profile.window_config.width > 0, "窗口宽度必须为正数"
        assert profile.window_config.height > 0, "窗口高度必须为正数"
    
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
    def test_按键映射包含必要属性(
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
        *对于任意* GameProfile，其 key_mapping 必须包含 move_keys、skill_keys、interact_key 属性。
        
        **Feature: smart-training-system, Property 8: 配置档案完整性**
        **验证: 需求 5.2**
        """
        profile = GameProfile(
            name=name,
            game_name=game_name,
            window_config=window_config,
            key_mapping=key_mapping,
            ui_regions=ui_regions,
            detection_params=detection_params,
            decision_rules=decision_rules
        )
        
        # 验证按键映射包含必要属性
        assert hasattr(profile.key_mapping, 'move_keys'), "key_mapping 应包含 move_keys 属性"
        assert hasattr(profile.key_mapping, 'skill_keys'), "key_mapping 应包含 skill_keys 属性"
        assert hasattr(profile.key_mapping, 'interact_key'), "key_mapping 应包含 interact_key 属性"
        
        # 验证属性类型
        assert isinstance(profile.key_mapping.move_keys, dict), "move_keys 应为字典类型"
        assert isinstance(profile.key_mapping.skill_keys, dict), "skill_keys 应为字典类型"
        assert isinstance(profile.key_mapping.interact_key, str), "interact_key 应为字符串类型"
    
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
    def test_UI区域包含必要属性(
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
        *对于任意* GameProfile，其 ui_regions 必须包含 health_bar、skill_bar、dialog_area、minimap 属性。
        
        **Feature: smart-training-system, Property 8: 配置档案完整性**
        **验证: 需求 5.3**
        """
        profile = GameProfile(
            name=name,
            game_name=game_name,
            window_config=window_config,
            key_mapping=key_mapping,
            ui_regions=ui_regions,
            detection_params=detection_params,
            decision_rules=decision_rules
        )
        
        # 验证UI区域包含必要属性
        assert hasattr(profile.ui_regions, 'health_bar'), "ui_regions 应包含 health_bar 属性"
        assert hasattr(profile.ui_regions, 'skill_bar'), "ui_regions 应包含 skill_bar 属性"
        assert hasattr(profile.ui_regions, 'dialog_area'), "ui_regions 应包含 dialog_area 属性"
        assert hasattr(profile.ui_regions, 'minimap'), "ui_regions 应包含 minimap 属性"
        
        # 验证每个区域都是4元组
        for region_name in ['health_bar', 'skill_bar', 'dialog_area', 'minimap']:
            region = getattr(profile.ui_regions, region_name)
            assert len(region) == 4, f"{region_name} 应为4元组 (x, y, w, h)"
            assert region[2] > 0, f"{region_name} 的宽度必须为正数"
            assert region[3] > 0, f"{region_name} 的高度必须为正数"
    
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
    def test_检测参数包含必要属性(
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
        *对于任意* GameProfile，其 detection_params 必须包含 yolo_model_path、confidence_threshold 属性。
        
        **Feature: smart-training-system, Property 8: 配置档案完整性**
        **验证: 需求 5.4**
        """
        profile = GameProfile(
            name=name,
            game_name=game_name,
            window_config=window_config,
            key_mapping=key_mapping,
            ui_regions=ui_regions,
            detection_params=detection_params,
            decision_rules=decision_rules
        )
        
        # 验证检测参数包含必要属性
        assert hasattr(profile.detection_params, 'yolo_model_path'), \
            "detection_params 应包含 yolo_model_path 属性"
        assert hasattr(profile.detection_params, 'confidence_threshold'), \
            "detection_params 应包含 confidence_threshold 属性"
        
        # 验证置信度阈值在有效范围内
        assert 0.0 <= profile.detection_params.confidence_threshold <= 1.0, \
            f"置信度阈值应在 0-1 范围内，实际为 {profile.detection_params.confidence_threshold}"
    
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
    def test_决策规则包含必要属性(
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
        *对于任意* GameProfile，其 decision_rules 必须包含 state_priorities、action_weights 属性。
        
        **Feature: smart-training-system, Property 8: 配置档案完整性**
        **验证: 需求 5.5**
        """
        profile = GameProfile(
            name=name,
            game_name=game_name,
            window_config=window_config,
            key_mapping=key_mapping,
            ui_regions=ui_regions,
            detection_params=detection_params,
            decision_rules=decision_rules
        )
        
        # 验证决策规则包含必要属性
        assert hasattr(profile.decision_rules, 'state_priorities'), \
            "decision_rules 应包含 state_priorities 属性"
        assert hasattr(profile.decision_rules, 'action_weights'), \
            "decision_rules 应包含 action_weights 属性"
        
        # 验证属性类型
        assert isinstance(profile.decision_rules.state_priorities, dict), \
            "state_priorities 应为字典类型"
        assert isinstance(profile.decision_rules.action_weights, dict), \
            "action_weights 应为字典类型"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--hypothesis-show-statistics'])
