# -*- coding: utf-8 -*-
"""
属性测试：配置持久性
Property 3: 对于任意保存的窗口配置，重新加载后应与保存时一致

**Feature: auto-window-detection, Property 3: 配置持久性**
**验证: 需求 4.1**
"""

import sys
import os
import tempfile
import shutil

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from hypothesis import given, strategies as st, settings, assume
from typing import Tuple

from 核心.窗口检测 import 窗口配置管理器, 窗口信息


# ==================== 测试数据生成策略 ====================

# 有效的窗口标识策略（进程名或标题）
valid_identifier_strategy = st.text(
    min_size=1,
    max_size=50,
    alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-."
).filter(lambda x: x.strip() != "" and len(x.strip()) > 0)

# 有效的窗口标题策略
valid_title_strategy = st.text(
    min_size=1,
    max_size=100,
    alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_- 中文测试游戏"
).filter(lambda x: x.strip() != "")

# 有效的进程名策略
valid_process_name_strategy = st.text(
    min_size=1,
    max_size=50,
    alphabet="abcdefghijklmnopqrstuvwxyz0123456789_-."
).filter(lambda x: x.strip() != "" and len(x.strip()) > 0)

# 有效的位置策略
valid_position_strategy = st.tuples(
    st.integers(min_value=-1000, max_value=5000),  # x
    st.integers(min_value=-1000, max_value=3000)   # y
)

# 有效的大小策略
valid_size_strategy = st.tuples(
    st.integers(min_value=100, max_value=3840),   # width
    st.integers(min_value=100, max_value=2160)    # height
)

# 有效的别名策略
valid_alias_strategy = st.text(
    min_size=0,
    max_size=30,
    alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_- 中文"
)

# 有效的备注策略
valid_note_strategy = st.text(
    min_size=0,
    max_size=100,
    alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_- 中文测试备注。，！"
)


def create_window_info(
    句柄: int,
    标题: str,
    进程名: str,
    进程ID: int,
    位置: Tuple[int, int],
    大小: Tuple[int, int]
) -> 窗口信息:
    """创建窗口信息对象"""
    return 窗口信息(
        句柄=句柄,
        标题=标题,
        进程名=进程名,
        进程ID=进程ID,
        位置=位置,
        大小=大小,
        是否可见=True,
        是否最小化=False
    )


# ==================== 属性测试类 ====================

class Test配置持久性属性:
    """
    属性测试：配置持久性
    
    **Feature: auto-window-detection, Property 3: 配置持久性**
    **验证: 需求 4.1**
    """
    
    @pytest.fixture(autouse=True)
    def 初始化(self):
        """初始化测试环境"""
        # 创建临时目录
        self.临时目录 = tempfile.mkdtemp()
        self.配置路径 = os.path.join(self.临时目录, "窗口配置.json")
        yield
        # 清理临时目录
        shutil.rmtree(self.临时目录, ignore_errors=True)
    
    @settings(max_examples=100, deadline=None)
    @given(
        标识=valid_identifier_strategy,
        标题=valid_title_strategy,
        进程名=valid_process_name_strategy,
        位置=valid_position_strategy,
        大小=valid_size_strategy,
        别名=valid_alias_strategy,
        备注=valid_note_strategy
    )
    def test_保存后加载配置一致性(
        self,
        标识: str,
        标题: str,
        进程名: str,
        位置: Tuple[int, int],
        大小: Tuple[int, int],
        别名: str,
        备注: str
    ):
        """
        属性测试: 对于任意保存的窗口配置，重新加载后应与保存时一致
        
        **Feature: auto-window-detection, Property 3: 配置持久性**
        **验证: 需求 4.1**
        """
        # 创建配置管理器
        管理器 = 窗口配置管理器(self.配置路径)
        
        # 创建窗口信息
        窗口 = create_window_info(
            句柄=12345,
            标题=标题,
            进程名=进程名,
            进程ID=1000,
            位置=位置,
            大小=大小
        )
        
        # 保存配置
        保存结果 = 管理器.保存配置(标识, 窗口, 别名=别名, 备注=备注)
        assert 保存结果, f"保存配置应该成功，标识: {标识}"
        
        # 创建新的管理器实例（模拟重新加载）
        新管理器 = 窗口配置管理器(self.配置路径)
        
        # 加载配置
        加载的配置 = 新管理器.加载配置(标识)
        
        # 验证配置存在
        assert 加载的配置 is not None, f"应能加载保存的配置，标识: {标识}"
        
        # 验证关键字段一致性
        assert 加载的配置['标识值'] == 标识, \
            f"标识值应一致: 期望 {标识}, 实际 {加载的配置['标识值']}"
        
        assert 加载的配置['进程名'] == 进程名, \
            f"进程名应一致: 期望 {进程名}, 实际 {加载的配置['进程名']}"
        
        assert 加载的配置['标题'] == 标题, \
            f"标题应一致: 期望 {标题}, 实际 {加载的配置['标题']}"
        
        # 验证位置一致性
        期望位置 = [位置[0], 位置[1], 大小[0], 大小[1]]
        assert 加载的配置['上次位置'] == 期望位置, \
            f"位置应一致: 期望 {期望位置}, 实际 {加载的配置['上次位置']}"
        
        # 验证别名和备注一致性
        assert 加载的配置['别名'] == 别名, \
            f"别名应一致: 期望 {别名}, 实际 {加载的配置['别名']}"
        
        assert 加载的配置['备注'] == 备注, \
            f"备注应一致: 期望 {备注}, 实际 {加载的配置['备注']}"
    
    @settings(max_examples=100, deadline=None)
    @given(
        标识=valid_identifier_strategy,
        进程名=valid_process_name_strategy,
        位置=valid_position_strategy,
        大小=valid_size_strategy
    )
    def test_多次保存加载一致性(
        self,
        标识: str,
        进程名: str,
        位置: Tuple[int, int],
        大小: Tuple[int, int]
    ):
        """
        属性测试: 多次保存和加载后配置应保持一致
        
        **Feature: auto-window-detection, Property 3: 配置持久性**
        **验证: 需求 4.1**
        """
        管理器 = 窗口配置管理器(self.配置路径)
        
        窗口 = create_window_info(
            句柄=12345,
            标题="测试窗口",
            进程名=进程名,
            进程ID=1000,
            位置=位置,
            大小=大小
        )
        
        # 多次保存和加载
        for i in range(3):
            管理器.保存配置(标识, 窗口)
            
            # 创建新管理器加载
            新管理器 = 窗口配置管理器(self.配置路径)
            加载的配置 = 新管理器.加载配置(标识)
            
            assert 加载的配置 is not None, f"第 {i+1} 次加载应成功"
            assert 加载的配置['进程名'] == 进程名, \
                f"第 {i+1} 次加载后进程名应一致"
    
    @settings(max_examples=100, deadline=None)
    @given(
        标识列表=st.lists(
            valid_identifier_strategy,
            min_size=1,
            max_size=5,
            unique=True
        )
    )
    def test_多配置持久性(self, 标识列表):
        """
        属性测试: 多个配置保存后都应能正确加载
        
        **Feature: auto-window-detection, Property 3: 配置持久性**
        **验证: 需求 4.1**
        """
        管理器 = 窗口配置管理器(self.配置路径)
        
        # 保存多个配置
        for i, 标识 in enumerate(标识列表):
            窗口 = create_window_info(
                句柄=10000 + i,
                标题=f"窗口_{i}",
                进程名=f"process_{i}.exe",
                进程ID=1000 + i,
                位置=(100 * i, 100 * i),
                大小=(800 + i * 10, 600 + i * 10)
            )
            管理器.保存配置(标识, 窗口)
        
        # 创建新管理器验证所有配置
        新管理器 = 窗口配置管理器(self.配置路径)
        
        for i, 标识 in enumerate(标识列表):
            加载的配置 = 新管理器.加载配置(标识)
            assert 加载的配置 is not None, f"配置 {标识} 应能加载"
            assert 加载的配置['进程名'] == f"process_{i}.exe", \
                f"配置 {标识} 的进程名应正确"
    
    @settings(max_examples=100, deadline=None)
    @given(
        标识=valid_identifier_strategy,
        进程名=valid_process_name_strategy
    )
    def test_默认配置持久性(self, 标识: str, 进程名: str):
        """
        属性测试: 默认配置设置后应能正确持久化
        
        **Feature: auto-window-detection, Property 3: 配置持久性**
        **验证: 需求 4.1**
        """
        管理器 = 窗口配置管理器(self.配置路径)
        
        窗口 = create_window_info(
            句柄=12345,
            标题="测试窗口",
            进程名=进程名,
            进程ID=1000,
            位置=(100, 100),
            大小=(800, 600)
        )
        
        # 保存配置并设置为默认
        管理器.保存配置(标识, 窗口)
        管理器.设置默认(标识)
        
        # 创建新管理器验证默认配置
        新管理器 = 窗口配置管理器(self.配置路径)
        
        assert 新管理器.获取默认配置() == 标识, \
            f"默认配置应为 {标识}"
        
        # 不指定标识加载默认配置
        默认配置 = 新管理器.加载配置()
        assert 默认配置 is not None, "应能加载默认配置"
        assert 默认配置['标识值'] == 标识, "默认配置标识应正确"


# ==================== 单元测试 ====================

class Test配置持久性单元测试:
    """配置持久性的单元测试"""
    
    @pytest.fixture(autouse=True)
    def 初始化(self):
        """初始化测试环境"""
        self.临时目录 = tempfile.mkdtemp()
        self.配置路径 = os.path.join(self.临时目录, "窗口配置.json")
        yield
        shutil.rmtree(self.临时目录, ignore_errors=True)
    
    def test_空配置文件创建(self):
        """测试: 新建管理器应创建空配置"""
        管理器 = 窗口配置管理器(self.配置路径)
        assert 管理器.获取配置数量() == 0, "新建管理器应无配置"
    
    def test_配置文件自动创建(self):
        """测试: 保存配置时应自动创建配置文件"""
        管理器 = 窗口配置管理器(self.配置路径)
        
        窗口 = create_window_info(
            句柄=12345,
            标题="测试",
            进程名="test.exe",
            进程ID=1000,
            位置=(0, 0),
            大小=(800, 600)
        )
        
        管理器.保存配置("test.exe", 窗口)
        
        assert os.path.exists(self.配置路径), "配置文件应被创建"
    
    def test_损坏配置文件恢复(self):
        """测试: 损坏的配置文件应使用默认配置"""
        # 写入损坏的 JSON
        os.makedirs(os.path.dirname(self.配置路径), exist_ok=True)
        with open(self.配置路径, 'w', encoding='utf-8') as f:
            f.write("这不是有效的JSON{{{")
        
        # 创建管理器应该不会崩溃
        管理器 = 窗口配置管理器(self.配置路径)
        assert 管理器.获取配置数量() == 0, "损坏配置应使用默认空配置"
    
    def test_配置版本迁移(self):
        """测试: 旧版本配置应能正确迁移"""
        # 写入旧版本配置（无版本字段）
        import json
        旧配置 = {
            "默认": "test.exe",
            "配置列表": {
                "test.exe": {
                    "标识类型": "process",
                    "标识值": "test.exe",
                    "上次位置": [0, 0, 800, 600],
                    "进程名": "test.exe",
                    "标题": "测试",
                    "上次使用": "2026-01-01T00:00:00"
                }
            }
        }
        
        os.makedirs(os.path.dirname(self.配置路径), exist_ok=True)
        with open(self.配置路径, 'w', encoding='utf-8') as f:
            json.dump(旧配置, f, ensure_ascii=False)
        
        # 加载应成功并迁移
        管理器 = 窗口配置管理器(self.配置路径)
        assert 管理器.配置是否存在("test.exe"), "迁移后配置应存在"
        
        配置 = 管理器.加载配置("test.exe")
        assert 配置 is not None, "应能加载迁移后的配置"
        # 迁移后应添加新字段
        assert '别名' in 配置, "迁移后应有别名字段"
        assert '备注' in 配置, "迁移后应有备注字段"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])
