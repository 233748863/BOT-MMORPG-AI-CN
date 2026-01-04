# -*- coding: utf-8 -*-
"""
属性测试：配置导入导出Round-Trip
Property 7: 对于任意有效的 GameProfile，export_profile 后再 import_profile 必须得到等价的配置数据。

**Feature: smart-training-system, Property 7: 配置导入导出Round-Trip**
**验证: 需求 4.4, 4.5**
"""

import sys
import os
import tempfile
import shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from hypothesis import given, strategies as st, settings

from 核心.配置管理 import (
    ConfigManager,
    GameProfile,
    WindowConfig,
    KeyMapping,
    UIRegions,
    DetectionParams,
    DecisionRules
)


# 有效的档案名称策略
valid_name_strategy = st.text(
    min_size=1,
    max_size=30,
    alphabet="abcdefghijklmnopqrstuvwxyz0123456789_-"
).filter(lambda x: x.strip() != "" and len(x.strip()) > 0)

# 有效的游戏名称策略
valid_game_name_strategy = st.text(
    min_size=1,
    max_size=30,
    alphabet="abcdefghijklmnopqrstuvwxyz0123456789_- "
).filter(lambda x: x.strip() != "")

# 有效的窗口配置策略
valid_window_config_strategy = st.builds(
    WindowConfig,
    x=st.integers(min_value=0, max_value=1000),
    y=st.integers(min_value=0, max_value=500),
    width=st.integers(min_value=640, max_value=3840),
    height=st.integers(min_value=480, max_value=2160)
)


# 有效的按键映射策略
valid_key_mapping_strategy = st.builds(
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


def valid_region_strategy():
    """生成有效的UI区域元组 (x, y, width, height)"""
    return st.tuples(
        st.integers(min_value=0, max_value=1000),
        st.integers(min_value=0, max_value=500),
        st.integers(min_value=10, max_value=500),
        st.integers(min_value=10, max_value=300)
    )


valid_ui_regions_strategy = st.builds(
    UIRegions,
    health_bar=valid_region_strategy(),
    skill_bar=valid_region_strategy(),
    dialog_area=valid_region_strategy(),
    minimap=valid_region_strategy()
)

valid_detection_params_strategy = st.builds(
    DetectionParams,
    yolo_model_path=st.just("模型/预训练模型/yolo.pt"),
    confidence_threshold=st.floats(min_value=0.1, max_value=0.9, allow_nan=False, allow_infinity=False)
)

valid_decision_rules_strategy = st.builds(
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



class TestConfigImportExportRoundTrip:
    """
    Property 7: 配置导入导出Round-Trip
    
    *对于任意* 有效的 GameProfile，export_profile 后再 import_profile 必须得到等价的配置数据。
    
    **Feature: smart-training-system, Property 7: 配置导入导出Round-Trip**
    **验证: 需求 4.4, 4.5**
    """
    
    @given(
        name=valid_name_strategy,
        game_name=valid_game_name_strategy,
        window_config=valid_window_config_strategy,
        key_mapping=valid_key_mapping_strategy,
        ui_regions=valid_ui_regions_strategy,
        detection_params=valid_detection_params_strategy,
        decision_rules=valid_decision_rules_strategy
    )
    @settings(max_examples=100, deadline=None)
    def test_export_then_import_returns_equivalent_data(
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
        *对于任意* 有效的 GameProfile，export_profile 后再 import_profile 
        必须得到等价的配置数据。
        
        **Feature: smart-training-system, Property 7: 配置导入导出Round-Trip**
        **验证: 需求 4.4, 4.5**
        """
        test_dir = tempfile.mkdtemp()
        profiles_dir = os.path.join(test_dir, 'profiles')
        export_dir = os.path.join(test_dir, 'exports')
        os.makedirs(export_dir, exist_ok=True)
        
        try:
            # 创建配置管理器
            manager = ConfigManager(profiles_dir=profiles_dir, auto_load_last=False)
            
            # 创建配置档案
            original_profile = GameProfile(
                name=name,
                game_name=game_name,
                window_config=window_config,
                key_mapping=key_mapping,
                ui_regions=ui_regions,
                detection_params=detection_params,
                decision_rules=decision_rules
            )
            
            # 保存档案
            manager.save_profile(original_profile)
            
            # 导出档案到文件
            export_path = os.path.join(export_dir, f"{name}_export.json")
            export_result = manager.export_profile(name, export_path)
            assert export_result, "导出档案应该成功"
            assert os.path.exists(export_path), "导出文件应该存在"
            
            # 从文件导入档案
            imported_profile = manager.import_profile(export_path)
            
            # 验证关键字段相同
            assert imported_profile.name == original_profile.name
            assert imported_profile.game_name == original_profile.game_name
            
            # 验证窗口配置
            assert imported_profile.window_config.x == original_profile.window_config.x
            assert imported_profile.window_config.y == original_profile.window_config.y
            assert imported_profile.window_config.width == original_profile.window_config.width
            assert imported_profile.window_config.height == original_profile.window_config.height
            
            # 验证按键映射
            assert imported_profile.key_mapping.move_keys == original_profile.key_mapping.move_keys
            assert imported_profile.key_mapping.skill_keys == original_profile.key_mapping.skill_keys
            assert imported_profile.key_mapping.interact_key == original_profile.key_mapping.interact_key
            
            # 验证UI区域
            assert imported_profile.ui_regions.health_bar == original_profile.ui_regions.health_bar
            assert imported_profile.ui_regions.skill_bar == original_profile.ui_regions.skill_bar
            assert imported_profile.ui_regions.dialog_area == original_profile.ui_regions.dialog_area
            assert imported_profile.ui_regions.minimap == original_profile.ui_regions.minimap
            
            # 验证检测参数
            assert imported_profile.detection_params.yolo_model_path == original_profile.detection_params.yolo_model_path
            assert abs(imported_profile.detection_params.confidence_threshold - 
                      original_profile.detection_params.confidence_threshold) < 1e-6
            
            # 验证决策规则
            assert imported_profile.decision_rules.state_priorities == original_profile.decision_rules.state_priorities
            for key in original_profile.decision_rules.action_weights:
                assert abs(imported_profile.decision_rules.action_weights[key] - 
                          original_profile.decision_rules.action_weights[key]) < 1e-6
            
        finally:
            shutil.rmtree(test_dir, ignore_errors=True)


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--hypothesis-show-statistics'])
