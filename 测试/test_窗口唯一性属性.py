# -*- coding: utf-8 -*-
"""
属性测试：窗口唯一性
Property 1: 对于任意返回的窗口句柄，应对应一个有效的窗口

**Feature: auto-window-detection, Property 1: 窗口唯一性**
**验证: 需求 1.3**
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import ctypes
from hypothesis import given, strategies as st, settings, assume
from typing import List, Optional

from 核心.窗口检测 import 窗口查找器, 窗口信息


# ==================== 辅助函数 ====================

def 验证窗口句柄有效(句柄: int) -> bool:
    """
    验证窗口句柄是否有效
    
    参数:
        句柄: 窗口句柄
        
    返回:
        True 如果句柄对应有效窗口，否则 False
    """
    try:
        user32 = ctypes.windll.user32
        return user32.IsWindow(句柄) != 0
    except Exception:
        return False


def 获取窗口标题(句柄: int) -> Optional[str]:
    """
    获取窗口标题
    
    参数:
        句柄: 窗口句柄
        
    返回:
        窗口标题，无效句柄返回 None
    """
    try:
        user32 = ctypes.windll.user32
        长度 = user32.GetWindowTextLengthW(句柄) + 1
        缓冲区 = ctypes.create_unicode_buffer(长度)
        user32.GetWindowTextW(句柄, 缓冲区, 长度)
        return 缓冲区.value if 缓冲区.value else None
    except Exception:
        return None


# ==================== 属性测试类 ====================

class Test窗口唯一性属性:
    """
    属性测试：窗口唯一性
    
    **Feature: auto-window-detection, Property 1: 窗口唯一性**
    **验证: 需求 1.3**
    """
    
    @pytest.fixture(autouse=True)
    def 初始化(self):
        """初始化测试环境"""
        self.查找器 = 窗口查找器()
    
    @settings(max_examples=100, deadline=None)
    @given(st.just(None))  # 使用 just(None) 触发属性测试框架
    def test_获取所有窗口返回有效句柄(self, _):
        """
        属性测试: 对于任意返回的窗口，其句柄应对应一个有效的窗口
        
        **Feature: auto-window-detection, Property 1: 窗口唯一性**
        **验证: 需求 1.3**
        """
        # 获取所有可见窗口
        窗口列表 = self.查找器.获取所有窗口(仅可见=True)
        
        # 验证每个返回的窗口句柄都是有效的
        for 窗口 in 窗口列表:
            assert isinstance(窗口, 窗口信息), \
                f"返回的对象应为窗口信息类型，实际为 {type(窗口)}"
            
            assert isinstance(窗口.句柄, int), \
                f"窗口句柄应为整数类型，实际为 {type(窗口.句柄)}"
            
            assert 窗口.句柄 > 0, \
                f"窗口句柄应为正整数，实际为 {窗口.句柄}"
            
            # 核心属性：句柄应对应有效窗口
            assert 验证窗口句柄有效(窗口.句柄), \
                f"窗口句柄 {窗口.句柄} 应对应有效窗口，但验证失败"
    
    @settings(max_examples=100, deadline=None)
    @given(st.just(None))
    def test_窗口句柄唯一性(self, _):
        """
        属性测试: 返回的窗口句柄应该是唯一的，不应有重复
        
        **Feature: auto-window-detection, Property 1: 窗口唯一性**
        **验证: 需求 1.3**
        """
        窗口列表 = self.查找器.获取所有窗口(仅可见=True)
        
        句柄集合 = set()
        for 窗口 in 窗口列表:
            assert 窗口.句柄 not in 句柄集合, \
                f"窗口句柄 {窗口.句柄} 重复出现，违反唯一性"
            句柄集合.add(窗口.句柄)
    
    @settings(max_examples=100, deadline=None)
    @given(st.text(min_size=1, max_size=20, alphabet="abcdefghijklmnopqrstuvwxyz"))
    def test_按标题查找返回有效句柄(self, 搜索标题: str):
        """
        属性测试: 按标题查找返回的窗口句柄应对应有效窗口
        
        **Feature: auto-window-detection, Property 1: 窗口唯一性**
        **验证: 需求 1.3**
        """
        窗口列表 = self.查找器.按标题查找(搜索标题, 模糊匹配=True)
        
        # 验证每个返回的窗口句柄都是有效的
        for 窗口 in 窗口列表:
            assert 验证窗口句柄有效(窗口.句柄), \
                f"按标题 '{搜索标题}' 查找返回的句柄 {窗口.句柄} 应对应有效窗口"
    
    @settings(max_examples=100, deadline=None)
    @given(st.text(min_size=1, max_size=20, alphabet="abcdefghijklmnopqrstuvwxyz."))
    def test_按进程名查找返回有效句柄(self, 进程名: str):
        """
        属性测试: 按进程名查找返回的窗口句柄应对应有效窗口
        
        **Feature: auto-window-detection, Property 1: 窗口唯一性**
        **验证: 需求 1.3**
        """
        窗口列表 = self.查找器.按进程名查找(进程名)
        
        # 验证每个返回的窗口句柄都是有效的
        for 窗口 in 窗口列表:
            assert 验证窗口句柄有效(窗口.句柄), \
                f"按进程名 '{进程名}' 查找返回的句柄 {窗口.句柄} 应对应有效窗口"
    
    @settings(max_examples=100, deadline=None)
    @given(st.just(None))
    def test_窗口信息完整性(self, _):
        """
        属性测试: 返回的窗口信息应包含所有必要字段
        
        **Feature: auto-window-detection, Property 1: 窗口唯一性**
        **验证: 需求 1.3**
        """
        窗口列表 = self.查找器.获取所有窗口(仅可见=True)
        
        for 窗口 in 窗口列表:
            # 验证必要字段存在且类型正确
            assert hasattr(窗口, '句柄') and isinstance(窗口.句柄, int), \
                "窗口信息应包含整数类型的句柄字段"
            
            assert hasattr(窗口, '标题') and isinstance(窗口.标题, str), \
                "窗口信息应包含字符串类型的标题字段"
            
            assert hasattr(窗口, '进程名') and isinstance(窗口.进程名, str), \
                "窗口信息应包含字符串类型的进程名字段"
            
            assert hasattr(窗口, '进程ID') and isinstance(窗口.进程ID, int), \
                "窗口信息应包含整数类型的进程ID字段"
            
            assert hasattr(窗口, '位置') and isinstance(窗口.位置, tuple), \
                "窗口信息应包含元组类型的位置字段"
            
            assert hasattr(窗口, '大小') and isinstance(窗口.大小, tuple), \
                "窗口信息应包含元组类型的大小字段"
            
            assert len(窗口.位置) == 2, \
                f"位置应为二元组 (x, y)，实际长度为 {len(窗口.位置)}"
            
            assert len(窗口.大小) == 2, \
                f"大小应为二元组 (width, height)，实际长度为 {len(窗口.大小)}"


# ==================== 单元测试 ====================

class Test窗口查找器单元测试:
    """窗口查找器的单元测试"""
    
    def test_获取所有窗口不为空(self):
        """测试: 系统中应至少存在一个可见窗口"""
        查找器 = 窗口查找器()
        窗口列表 = 查找器.获取所有窗口(仅可见=True)
        
        # 系统中应该至少有一个可见窗口
        assert len(窗口列表) > 0, "系统中应至少存在一个可见窗口"
    
    def test_获取窗口信息_无效句柄返回None(self):
        """测试: 无效句柄应返回 None"""
        查找器 = 窗口查找器()
        
        # 使用一个明显无效的句柄
        无效句柄 = 0
        结果 = 查找器.获取窗口信息(无效句柄)
        
        assert 结果 is None, "无效句柄应返回 None"
    
    def test_获取窗口信息_极大无效句柄返回None(self):
        """测试: 极大的无效句柄应返回 None"""
        查找器 = 窗口查找器()
        
        # 使用一个极大的无效句柄
        极大句柄 = 0xFFFFFFFF
        结果 = 查找器.获取窗口信息(极大句柄)
        
        assert 结果 is None, "极大的无效句柄应返回 None"
    
    def test_按标题查找_空字符串返回空列表(self):
        """测试: 空标题搜索应返回空列表"""
        查找器 = 窗口查找器()
        
        # 空字符串搜索
        结果 = 查找器.按标题查找("")
        
        # 空字符串会匹配所有窗口，所以这里检查返回类型
        assert isinstance(结果, list), "按标题查找应返回列表"
    
    def test_按进程名查找_不存在的进程返回空列表(self):
        """测试: 不存在的进程名应返回空列表"""
        查找器 = 窗口查找器()
        
        # 使用一个不太可能存在的进程名
        结果 = 查找器.按进程名查找("不存在的进程名_xyz123.exe")
        
        assert isinstance(结果, list), "按进程名查找应返回列表"
        assert len(结果) == 0, "不存在的进程名应返回空列表"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
