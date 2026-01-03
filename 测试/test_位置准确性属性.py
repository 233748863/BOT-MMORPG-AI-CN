"""
位置准确性属性测试

属性 2: 位置准确性
*对于任意* 获取的窗口位置，应与实际窗口位置一致

验证: 需求 3.2
"""

import ctypes
import time
import threading
import pytest
from hypothesis import given, strategies as st, settings, assume

# 导入被测试的模块
from 核心.窗口检测 import (
    窗口查找器, 窗口跟踪器, 窗口信息, 窗口变化事件, 自动窗口检测器
)


class Test位置准确性属性:
    """
    属性测试: 位置准确性
    
    Feature: auto-window-detection, Property 2: 位置准确性
    Validates: Requirements 3.2
    """
    
    def setup_method(self):
        """测试前准备"""
        self.查找器 = 窗口查找器()
        self.user32 = ctypes.windll.user32
    
    def _获取实际窗口位置(self, 句柄: int) -> tuple:
        """使用 Windows API 直接获取窗口位置"""
        矩形 = ctypes.wintypes.RECT()
        self.user32.GetWindowRect(句柄, ctypes.byref(矩形))
        return (矩形.left, 矩形.top, 矩形.right - 矩形.left, 矩形.bottom - 矩形.top)
    
    @settings(max_examples=50, deadline=5000)
    @given(st.integers(min_value=0, max_value=10))
    def test_获取位置与实际位置一致(self, 窗口索引: int):
        """
        属性测试: 获取的窗口位置应与实际窗口位置一致
        
        Feature: auto-window-detection, Property 2: 位置准确性
        Validates: Requirements 3.2
        """
        # 获取所有窗口
        所有窗口 = self.查找器.获取所有窗口()
        assume(len(所有窗口) > 0)
        
        # 选择一个窗口
        索引 = 窗口索引 % len(所有窗口)
        窗口 = 所有窗口[索引]
        
        # 获取模块返回的位置
        模块位置 = 窗口.获取区域()
        
        # 使用 Windows API 直接获取位置
        实际位置 = self._获取实际窗口位置(窗口.句柄)
        
        # 验证位置一致（允许 1 像素误差）
        assert abs(模块位置[0] - 实际位置[0]) <= 1, f"X 坐标不一致: {模块位置[0]} vs {实际位置[0]}"
        assert abs(模块位置[1] - 实际位置[1]) <= 1, f"Y 坐标不一致: {模块位置[1]} vs {实际位置[1]}"
        assert abs(模块位置[2] - 实际位置[2]) <= 1, f"宽度不一致: {模块位置[2]} vs {实际位置[2]}"
        assert abs(模块位置[3] - 实际位置[3]) <= 1, f"高度不一致: {模块位置[3]} vs {实际位置[3]}"
    
    @settings(max_examples=30, deadline=5000)
    @given(st.integers(min_value=0, max_value=5))
    def test_跟踪器位置与查找器位置一致(self, 窗口索引: int):
        """
        属性测试: 跟踪器获取的位置应与查找器获取的位置一致
        
        Feature: auto-window-detection, Property 2: 位置准确性
        Validates: Requirements 3.2
        """
        # 获取所有窗口
        所有窗口 = self.查找器.获取所有窗口()
        assume(len(所有窗口) > 0)
        
        # 选择一个窗口
        索引 = 窗口索引 % len(所有窗口)
        窗口 = 所有窗口[索引]
        
        # 创建跟踪器
        跟踪器 = 窗口跟踪器(窗口.句柄)
        
        try:
            # 获取跟踪器位置
            跟踪器位置 = 跟踪器.获取当前位置()
            assume(跟踪器位置 is not None)
            
            # 获取查找器位置
            查找器信息 = self.查找器.获取窗口信息(窗口.句柄)
            assume(查找器信息 is not None)
            查找器位置 = 查找器信息.获取区域()
            
            # 验证位置一致
            assert 跟踪器位置 == 查找器位置, f"位置不一致: {跟踪器位置} vs {查找器位置}"
        finally:
            跟踪器.停止()


class Test跟踪器单元测试:
    """窗口跟踪器单元测试"""
    
    def setup_method(self):
        """测试前准备"""
        self.查找器 = 窗口查找器()
    
    def test_跟踪器初始化(self):
        """测试跟踪器初始化"""
        所有窗口 = self.查找器.获取所有窗口()
        assert len(所有窗口) > 0, "应该有可用窗口"
        
        窗口 = 所有窗口[0]
        跟踪器 = 窗口跟踪器(窗口.句柄)
        
        assert 跟踪器.句柄 == 窗口.句柄
        assert not 跟踪器.是否运行中
        assert 跟踪器.窗口是否存在()
    
    def test_跟踪器启动停止(self):
        """测试跟踪器启动和停止"""
        所有窗口 = self.查找器.获取所有窗口()
        assert len(所有窗口) > 0
        
        窗口 = 所有窗口[0]
        跟踪器 = 窗口跟踪器(窗口.句柄)
        
        # 启动跟踪
        跟踪器.启动()
        assert 跟踪器.是否运行中
        
        # 等待一小段时间
        time.sleep(0.1)
        
        # 停止跟踪
        跟踪器.停止()
        assert not 跟踪器.是否运行中
    
    def test_跟踪器获取当前位置(self):
        """测试跟踪器获取当前位置"""
        所有窗口 = self.查找器.获取所有窗口()
        assert len(所有窗口) > 0
        
        窗口 = 所有窗口[0]
        跟踪器 = 窗口跟踪器(窗口.句柄)
        
        位置 = 跟踪器.获取当前位置()
        assert 位置 is not None
        assert len(位置) == 4
        assert all(isinstance(v, int) for v in 位置)
    
    def test_跟踪器无效句柄(self):
        """测试跟踪器处理无效句柄"""
        跟踪器 = 窗口跟踪器(0)  # 无效句柄
        
        assert not 跟踪器.窗口是否存在()
        assert 跟踪器.获取当前位置() is None
    
    def test_跟踪器回调机制(self):
        """测试跟踪器回调机制"""
        所有窗口 = self.查找器.获取所有窗口()
        assert len(所有窗口) > 0
        
        窗口 = 所有窗口[0]
        回调计数 = {"位置": 0, "大小": 0, "关闭": 0}
        
        def 位置回调(事件):
            回调计数["位置"] += 1
        
        def 大小回调(事件):
            回调计数["大小"] += 1
        
        def 关闭回调(事件):
            回调计数["关闭"] += 1
        
        跟踪器 = 窗口跟踪器(
            窗口.句柄,
            位置变化回调=位置回调,
            大小变化回调=大小回调,
            窗口关闭回调=关闭回调
        )
        
        # 验证跟踪器创建成功
        assert 跟踪器.句柄 == 窗口.句柄
        
        # 启动并立即停止（不会触发回调，因为窗口没有移动）
        跟踪器.启动()
        time.sleep(0.2)
        跟踪器.停止()
        
        # 回调计数应该为 0（窗口没有移动）
        assert 回调计数["位置"] == 0
        assert 回调计数["大小"] == 0
    
    def test_跟踪器检查间隔设置(self):
        """测试跟踪器检查间隔设置"""
        所有窗口 = self.查找器.获取所有窗口()
        assert len(所有窗口) > 0
        
        窗口 = 所有窗口[0]
        跟踪器 = 窗口跟踪器(窗口.句柄)
        
        # 默认检查间隔
        assert 跟踪器.检查间隔 == 0.5
        
        # 设置新的检查间隔
        跟踪器.检查间隔 = 1.0
        assert 跟踪器.检查间隔 == 1.0
        
        # 设置无效值（应该被忽略）
        跟踪器.检查间隔 = -1.0
        assert 跟踪器.检查间隔 == 1.0  # 保持原值
    
    def test_变化历史记录(self):
        """测试变化历史记录功能"""
        所有窗口 = self.查找器.获取所有窗口()
        assert len(所有窗口) > 0
        
        窗口 = 所有窗口[0]
        跟踪器 = 窗口跟踪器(窗口.句柄)
        
        # 初始历史应该为空
        历史 = 跟踪器.获取变化历史()
        assert len(历史) == 0
        
        # 清除历史（即使为空也应该正常工作）
        跟踪器.清除历史()
        assert len(跟踪器.获取变化历史()) == 0


class Test自动窗口检测器集成测试:
    """自动窗口检测器集成测试"""
    
    def test_检测器创建(self):
        """测试检测器创建"""
        检测器 = 自动窗口检测器()
        assert 检测器.获取当前窗口() is None
        assert 检测器.获取截取区域() is None
        assert not 检测器.是否正在跟踪()
    
    def test_检测器自动检测(self):
        """测试检测器自动检测功能"""
        检测器 = 自动窗口检测器()
        
        # 尝试检测一个常见的窗口
        窗口 = 检测器.自动检测(标题="")
        # 可能找不到窗口，这是正常的
        
        # 如果找到了窗口，验证区域
        if 窗口:
            区域 = 检测器.获取截取区域()
            assert 区域 is not None
            assert len(区域) == 4
    
    def test_检测器跟踪功能(self):
        """测试检测器跟踪功能"""
        检测器 = 自动窗口检测器()
        查找器 = 窗口查找器()
        
        # 获取一个窗口
        所有窗口 = 查找器.获取所有窗口()
        if len(所有窗口) == 0:
            pytest.skip("没有可用窗口")
        
        # 手动设置当前窗口（模拟选择）
        检测器._当前窗口 = 所有窗口[0]
        检测器._截取区域 = 所有窗口[0].获取区域()
        
        # 启动跟踪
        检测器.启动跟踪()
        assert 检测器.是否正在跟踪()
        
        # 等待一小段时间
        time.sleep(0.2)
        
        # 停止跟踪
        检测器.停止跟踪()
        assert not 检测器.是否正在跟踪()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
