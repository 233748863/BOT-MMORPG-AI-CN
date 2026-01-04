# -*- coding: utf-8 -*-
"""
默认值完整性属性测试模块

使用Hypothesis进行属性测试，验证所有配置参数都存在有效的默认值。

**属性 2: 默认值完整性**
*对于任意* 配置参数，应存在有效的默认值

**验证: 需求 5.4**
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from hypothesis import given, strategies as st, settings, assume
from typing import Any, Dict, List, Tuple

from 核心.配置管理 import ConfigManager
from 核心.配置验证 import 配置验证器, 默认配置模式, 验证错误


class Test默认值完整性属性:
    """
    默认值完整性属性测试类
    
    **Feature: config-gui, 属性 2: 默认值完整性**
    **验证: 需求 5.4**
    """
    
    def test_所有参数都有默认值定义(self):
        """
        测试: 模式定义中的所有参数都应有默认值
        
        **Feature: config-gui, 属性 2: 默认值完整性**
        **验证: 需求 5.4**
        """
        管理器 = ConfigManager(auto_load_last=False)
        模式定义 = 管理器.模式定义
        
        缺失默认值的参数 = []
        
        for 分区名, 分区定义 in 模式定义.items():
            for 参数名, 参数定义 in 分区定义.items():
                if "默认值" not in 参数定义:
                    缺失默认值的参数.append(f"{分区名}.{参数名}")
        
        assert len(缺失默认值的参数) == 0, \
            f"以下参数缺少默认值定义: {缺失默认值的参数}"
    
    def test_获取默认值方法返回所有参数的默认值(self):
        """
        测试: 获取默认值方法应返回所有参数的默认值
        
        **Feature: config-gui, 属性 2: 默认值完整性**
        **验证: 需求 5.4**
        """
        管理器 = ConfigManager(auto_load_last=False)
        所有默认值 = 管理器.获取默认值()
        模式定义 = 管理器.模式定义
        
        # 验证每个分区都有默认值
        for 分区名 in 模式定义.keys():
            assert 分区名 in 所有默认值, f"分区 '{分区名}' 应在默认值中"
        
        # 验证每个参数都有默认值
        for 分区名, 分区定义 in 模式定义.items():
            for 参数名 in 分区定义.keys():
                assert 参数名 in 所有默认值[分区名], \
                    f"参数 '{分区名}.{参数名}' 应在默认值中"
    
    def test_默认值类型与模式定义一致(self):
        """
        测试: 默认值的类型应与模式定义中的类型一致
        
        **Feature: config-gui, 属性 2: 默认值完整性**
        **验证: 需求 5.4**
        """
        管理器 = ConfigManager(auto_load_last=False)
        验证器 = 配置验证器(管理器.模式定义)
        模式定义 = 管理器.模式定义
        
        类型不匹配的参数 = []
        
        for 分区名, 分区定义 in 模式定义.items():
            for 参数名, 参数定义 in 分区定义.items():
                默认值 = 参数定义.get("默认值")
                期望类型 = 参数定义.get("类型", "str")
                
                if 默认值 is not None:
                    if not 验证器.验证类型(默认值, 期望类型):
                        类型不匹配的参数.append(
                            f"{分区名}.{参数名}: 默认值 {默认值} 类型为 {type(默认值).__name__}, "
                            f"期望类型为 {期望类型}"
                        )
        
        assert len(类型不匹配的参数) == 0, \
            f"以下参数的默认值类型不匹配: {类型不匹配的参数}"
    
    def test_默认值在有效范围内(self):
        """
        测试: 数值类型的默认值应在定义的范围内
        
        **Feature: config-gui, 属性 2: 默认值完整性**
        **验证: 需求 5.4**
        """
        管理器 = ConfigManager(auto_load_last=False)
        验证器 = 配置验证器(管理器.模式定义)
        模式定义 = 管理器.模式定义
        
        范围无效的参数 = []
        
        for 分区名, 分区定义 in 模式定义.items():
            for 参数名, 参数定义 in 分区定义.items():
                默认值 = 参数定义.get("默认值")
                期望类型 = 参数定义.get("类型", "str")
                
                # 只检查数值类型
                if 期望类型 in ("int", "float") and 默认值 is not None:
                    最小值 = 参数定义.get("最小值")
                    最大值 = 参数定义.get("最大值")
                    
                    if not 验证器.验证范围(默认值, 最小值, 最大值):
                        范围无效的参数.append(
                            f"{分区名}.{参数名}: 默认值 {默认值} 不在范围 "
                            f"[{最小值}, {最大值}] 内"
                        )
        
        assert len(范围无效的参数) == 0, \
            f"以下参数的默认值不在有效范围内: {范围无效的参数}"
    
    def test_选项类型默认值在选项列表中(self):
        """
        测试: choice类型的默认值应在选项列表中
        
        **Feature: config-gui, 属性 2: 默认值完整性**
        **验证: 需求 5.4**
        """
        管理器 = ConfigManager(auto_load_last=False)
        模式定义 = 管理器.模式定义
        
        选项无效的参数 = []
        
        for 分区名, 分区定义 in 模式定义.items():
            for 参数名, 参数定义 in 分区定义.items():
                期望类型 = 参数定义.get("类型", "str")
                
                if 期望类型 == "choice":
                    默认值 = 参数定义.get("默认值")
                    选项列表 = 参数定义.get("选项", [])
                    
                    if 默认值 is not None and 默认值 not in 选项列表:
                        选项无效的参数.append(
                            f"{分区名}.{参数名}: 默认值 '{默认值}' 不在选项列表 {选项列表} 中"
                        )
        
        assert len(选项无效的参数) == 0, \
            f"以下参数的默认值不在选项列表中: {选项无效的参数}"
    
    def test_获取单个参数默认值(self):
        """
        测试: 获取默认值方法应能获取单个参数的默认值
        
        **Feature: config-gui, 属性 2: 默认值完整性**
        **验证: 需求 5.4**
        """
        管理器 = ConfigManager(auto_load_last=False)
        模式定义 = 管理器.模式定义
        
        for 分区名, 分区定义 in 模式定义.items():
            for 参数名, 参数定义 in 分区定义.items():
                期望默认值 = 参数定义.get("默认值")
                
                # 使用 "分区.参数" 格式获取
                实际默认值 = 管理器.获取默认值(f"{分区名}.{参数名}")
                
                assert 实际默认值 == 期望默认值, \
                    f"参数 '{分区名}.{参数名}' 的默认值应为 {期望默认值}, 实际为 {实际默认值}"
    
    def test_重置为默认值功能(self):
        """
        测试: 重置为默认值应返回所有参数的默认值
        
        **Feature: config-gui, 属性 2: 默认值完整性**
        **验证: 需求 5.4**
        """
        管理器 = ConfigManager(auto_load_last=False)
        
        # 重置所有分区
        重置后配置 = 管理器.重置为默认()
        所有默认值 = 管理器.获取默认值()
        
        assert 重置后配置 == 所有默认值, \
            "重置为默认值应返回与获取默认值相同的结果"
    
    def test_重置单个分区为默认值(self):
        """
        测试: 重置单个分区应只返回该分区的默认值
        
        **Feature: config-gui, 属性 2: 默认值完整性**
        **验证: 需求 5.4**
        """
        管理器 = ConfigManager(auto_load_last=False)
        模式定义 = 管理器.模式定义
        
        for 分区名 in 模式定义.keys():
            重置后配置 = 管理器.重置为默认(分区名)
            
            assert 分区名 in 重置后配置, f"重置结果应包含分区 '{分区名}'"
            assert len(重置后配置) == 1, f"重置单个分区应只返回一个分区"
            
            # 验证分区内的参数
            所有默认值 = 管理器.获取默认值()
            assert 重置后配置[分区名] == 所有默认值[分区名], \
                f"分区 '{分区名}' 的重置值应与默认值一致"


class Test默认值完整性_属性测试:
    """
    使用Hypothesis进行默认值完整性的属性测试
    
    **Feature: config-gui, 属性 2: 默认值完整性**
    **验证: 需求 5.4**
    """
    
    @given(分区索引=st.integers(min_value=0, max_value=100))
    @settings(max_examples=100, deadline=None)
    def test_任意分区都有完整的默认值(self, 分区索引: int):
        """
        属性测试: 对于任意分区，所有参数都应有有效的默认值
        
        **Feature: config-gui, 属性 2: 默认值完整性**
        **验证: 需求 5.4**
        """
        管理器 = ConfigManager(auto_load_last=False)
        分区列表 = 管理器.获取分区列表()
        
        # 使用模运算选择分区
        if len(分区列表) == 0:
            return  # 没有分区，跳过测试
        
        分区名 = 分区列表[分区索引 % len(分区列表)]
        分区参数 = 管理器.获取分区参数(分区名)
        
        for 参数名, 参数定义 in 分区参数.items():
            # 验证默认值存在
            assert "默认值" in 参数定义, \
                f"参数 '{分区名}.{参数名}' 应有默认值定义"
            
            # 验证默认值有效
            默认值 = 参数定义["默认值"]
            期望类型 = 参数定义.get("类型", "str")
            
            验证器 = 配置验证器(管理器.模式定义)
            有效, 错误 = 验证器.验证值(f"{分区名}.{参数名}", 默认值, 参数定义)
            
            assert 有效, \
                f"参数 '{分区名}.{参数名}' 的默认值 {默认值} 应该是有效的，错误: {错误}"
    
    @given(参数索引=st.integers(min_value=0, max_value=100))
    @settings(max_examples=100, deadline=None)
    def test_任意参数的默认值都是有效的(self, 参数索引: int):
        """
        属性测试: 对于任意参数，其默认值应该通过验证
        
        **Feature: config-gui, 属性 2: 默认值完整性**
        **验证: 需求 5.4**
        """
        管理器 = ConfigManager(auto_load_last=False)
        验证器 = 配置验证器(管理器.模式定义)
        模式定义 = 管理器.模式定义
        
        # 收集所有参数
        所有参数 = []
        for 分区名, 分区定义 in 模式定义.items():
            for 参数名, 参数定义 in 分区定义.items():
                所有参数.append((分区名, 参数名, 参数定义))
        
        if len(所有参数) == 0:
            return  # 没有参数，跳过测试
        
        # 使用模运算选择参数
        分区名, 参数名, 参数定义 = 所有参数[参数索引 % len(所有参数)]
        
        # 验证默认值存在
        assert "默认值" in 参数定义, \
            f"参数 '{分区名}.{参数名}' 应有默认值定义"
        
        默认值 = 参数定义["默认值"]
        
        # 验证默认值有效
        有效, 错误 = 验证器.验证值(f"{分区名}.{参数名}", 默认值, 参数定义)
        
        assert 有效, \
            f"参数 '{分区名}.{参数名}' 的默认值 {默认值} 应该是有效的，错误: {错误}"


class Test默认配置模式完整性:
    """
    测试默认配置模式的完整性
    
    **Feature: config-gui, 属性 2: 默认值完整性**
    **验证: 需求 5.4**
    """
    
    def test_默认配置模式所有参数都有默认值(self):
        """
        测试: 默认配置模式中的所有参数都应有默认值
        
        **Feature: config-gui, 属性 2: 默认值完整性**
        **验证: 需求 5.4**
        """
        缺失默认值的参数 = []
        
        for 分区名, 分区定义 in 默认配置模式.items():
            for 参数名, 参数定义 in 分区定义.items():
                if "默认值" not in 参数定义:
                    缺失默认值的参数.append(f"{分区名}.{参数名}")
        
        assert len(缺失默认值的参数) == 0, \
            f"默认配置模式中以下参数缺少默认值: {缺失默认值的参数}"
    
    def test_默认配置模式默认值验证通过(self):
        """
        测试: 使用默认配置模式的默认值应该通过验证
        
        **Feature: config-gui, 属性 2: 默认值完整性**
        **验证: 需求 5.4**
        """
        验证器 = 配置验证器(默认配置模式)
        
        # 构建使用默认值的配置
        默认配置 = {}
        for 分区名, 分区定义 in 默认配置模式.items():
            默认配置[分区名] = {}
            for 参数名, 参数定义 in 分区定义.items():
                默认配置[分区名][参数名] = 参数定义.get("默认值")
        
        # 验证配置
        有效, 错误列表 = 验证器.验证配置(默认配置)
        
        assert 有效, \
            f"使用默认值的配置应该通过验证，错误: {[str(e) for e in 错误列表]}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])
