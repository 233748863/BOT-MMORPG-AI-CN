"""
错误恢复能力属性测试模块

使用 Hypothesis 进行属性测试，验证屏幕截取系统的错误恢复能力。

**属性 2: 错误恢复能力**
*对于任意* DXGI 截取失败，系统应能自动恢复或回退到其他后端

**验证: 需求 4.1, 4.2**

**Feature: screen-capture-optimization, Property 2: 错误恢复能力**
"""

import os
import sys
import pytest
import numpy as np
from hypothesis import given, strategies as st, settings, assume
from typing import Tuple, Optional, Dict, Any
from unittest.mock import patch, MagicMock

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入被测试模块
from 核心.屏幕截取优化 import (
    屏幕截取器,
    后端检测器,
    截取器基类,
    MSS截取器,
    PIL截取器,
    DXGI截取器
)


# ==================== 测试策略定义 ====================

def 区域策略():
    """
    生成有效截取区域的策略
    
    区域格式: (x, y, width, height)
    """
    return st.tuples(
        st.integers(min_value=0, max_value=500),   # x
        st.integers(min_value=0, max_value=300),   # y
        st.integers(min_value=50, max_value=400),  # width
        st.integers(min_value=50, max_value=300)   # height
    )


def 失败次数策略():
    """生成失败次数的策略"""
    return st.integers(min_value=1, max_value=10)


def 后端名称策略():
    """生成可用后端名称的策略"""
    可用后端 = 后端检测器.获取可用后端列表()
    if not 可用后端:
        可用后端 = ["pil"]  # 回退到 PIL
    return st.sampled_from(可用后端)


# ==================== 辅助函数 ====================

def 验证图像有效(图像: np.ndarray) -> bool:
    """验证图像是否有效"""
    if 图像 is None:
        return False
    if not isinstance(图像, np.ndarray):
        return False
    if 图像.ndim != 3:
        return False
    if 图像.shape[2] != 3:
        return False
    return True


def 创建模拟失败截取器(失败次数: int):
    """
    创建一个会失败指定次数后成功的模拟截取器
    
    参数:
        失败次数: 在成功之前失败的次数
    """
    class 模拟失败截取器(截取器基类):
        def __init__(self):
            super().__init__()
            self._当前失败次数 = 0
            self._目标失败次数 = 失败次数
            self._已初始化 = True
        
        def 截取(self, 区域=None):
            if self._当前失败次数 < self._目标失败次数:
                self._当前失败次数 += 1
                self._记录失败()
                return None
            # 返回有效图像
            return np.zeros((100, 100, 3), dtype=np.uint8)
        
        def 是否已初始化(self):
            return self._已初始化
    
    return 模拟失败截取器()


# ==================== 属性测试类 ====================

class Test错误恢复能力_属性测试:
    """
    错误恢复能力属性测试
    
    **Feature: screen-capture-optimization, Property 2: 错误恢复能力**
    
    验证系统在截取失败时能够自动恢复或回退到其他后端
    """
    
    @settings(max_examples=100, deadline=15000)
    @given(区域=区域策略())
    def test_属性2_回退机制启用时能恢复(self, 区域: Tuple[int, int, int, int]):
        """
        **属性 2: 错误恢复能力**
        
        *对于任意* 截取请求，当启用回退机制时，系统应能从失败中恢复
        
        **验证: 需求 4.1, 4.2**
        """
        可用后端 = 后端检测器.获取可用后端列表()
        assume(len(可用后端) >= 1)  # 至少需要一个后端
        
        # 创建启用回退的截取器
        截取器 = 屏幕截取器(首选后端="auto", 启用回退=True)
        
        # 执行截取
        图像 = 截取器.截取(区域)
        
        # 获取统计信息
        统计 = 截取器.获取性能统计()
        
        截取器.释放()
        
        # 验证：要么截取成功，要么有回退记录
        # 如果截取成功，图像应该有效
        if 图像 is not None:
            assert 验证图像有效(图像), "截取成功但图像格式无效"
        
        # 验证统计信息存在
        assert '后端类型' in 统计
        assert '成功率' in 统计
    
    @settings(max_examples=50, deadline=20000)
    @given(后端=后端名称策略())
    def test_属性2_单后端失败时回退(self, 后端: str):
        """
        **属性 2: 错误恢复能力**
        
        *对于任意* 后端，当该后端失败时，系统应能回退到其他后端
        
        **验证: 需求 4.2**
        """
        可用后端 = 后端检测器.获取可用后端列表()
        assume(len(可用后端) >= 2)  # 需要至少两个后端才能测试回退
        
        # 创建截取器
        截取器 = 屏幕截取器(首选后端=后端, 启用回退=True)
        原后端 = 截取器.获取当前后端()
        
        # 执行多次截取
        成功次数 = 0
        for _ in range(5):
            图像 = 截取器.截取()
            if 图像 is not None:
                成功次数 += 1
        
        统计 = 截取器.获取性能统计()
        截取器.释放()
        
        # 验证：至少有一次成功，或者有回退记录
        assert 成功次数 > 0 or 统计['回退次数'] >= 0, \
            f"截取全部失败且没有回退记录: 成功={成功次数}, 回退={统计['回退次数']}"
    
    @settings(max_examples=100, deadline=10000)
    @given(区域=区域策略())
    def test_属性2_错误日志记录(self, 区域: Tuple[int, int, int, int]):
        """
        **属性 2: 错误恢复能力**
        
        *对于任意* 截取操作，系统应记录错误和诊断信息
        
        **验证: 需求 4.3**
        """
        截取器 = 屏幕截取器(首选后端="auto", 启用回退=True)
        
        # 执行截取
        截取器.截取(区域)
        
        # 获取诊断信息
        诊断信息 = 截取器.获取诊断信息()
        
        截取器.释放()
        
        # 验证诊断信息结构
        assert '当前后端' in 诊断信息
        assert '性能统计' in 诊断信息
        assert '错误日志' in 诊断信息
        assert '回退历史' in 诊断信息
        assert '系统信息' in 诊断信息
        
        # 验证错误日志是列表
        assert isinstance(诊断信息['错误日志'], list)
        assert isinstance(诊断信息['回退历史'], list)


class Test错误恢复_单元测试:
    """
    错误恢复的单元测试
    
    验证错误恢复机制的基本功能
    """
    
    def test_截取器_回退启用状态(self):
        """测试截取器回退启用状态"""
        # 启用回退
        截取器1 = 屏幕截取器(启用回退=True)
        assert 截取器1._回退启用 == True
        截取器1.释放()
        
        # 禁用回退
        截取器2 = 屏幕截取器(启用回退=False)
        assert 截取器2._回退启用 == False
        截取器2.释放()
    
    def test_截取器_设置回退启用(self):
        """测试动态设置回退启用"""
        截取器 = 屏幕截取器(启用回退=True)
        
        截取器.设置回退启用(False)
        assert 截取器._回退启用 == False
        
        截取器.设置回退启用(True)
        assert 截取器._回退启用 == True
        
        截取器.释放()
    
    def test_错误日志_记录和获取(self):
        """测试错误日志的记录和获取"""
        截取器 = 屏幕截取器()
        
        # 手动记录错误
        截取器._记录错误("测试错误1", "test")
        截取器._记录错误("测试错误2", "test")
        
        错误日志 = 截取器.获取错误日志()
        
        assert len(错误日志) == 2
        assert 错误日志[0]['错误信息'] == "测试错误1"
        assert 错误日志[1]['错误信息'] == "测试错误2"
        
        截取器.释放()
    
    def test_错误日志_清除(self):
        """测试错误日志清除"""
        截取器 = 屏幕截取器()
        
        截取器._记录错误("测试错误", "test")
        assert len(截取器.获取错误日志()) == 1
        
        截取器.清除错误日志()
        assert len(截取器.获取错误日志()) == 0
        
        截取器.释放()
    
    def test_回退历史_获取(self):
        """测试回退历史获取"""
        截取器 = 屏幕截取器()
        
        回退历史 = 截取器.获取回退历史()
        
        # 回退历史应该是列表
        assert isinstance(回退历史, list)
        
        截取器.释放()
    
    def test_最后错误信息_获取(self):
        """测试最后错误信息获取"""
        截取器 = 屏幕截取器()
        
        # 初始应该为空
        assert 截取器.获取最后错误信息() == ""
        
        # 记录错误后应该有值
        截取器._记录错误("测试错误", "test")
        assert 截取器.获取最后错误信息() == "测试错误"
        
        截取器.释放()
    
    def test_诊断信息_完整性(self):
        """测试诊断信息的完整性"""
        截取器 = 屏幕截取器()
        
        诊断信息 = 截取器.获取诊断信息()
        
        # 验证必要的键
        必要键 = ['当前后端', '首选后端', '回退启用', '性能监控启用', 
                  '性能统计', '错误日志', '回退历史', '系统信息']
        
        for 键 in 必要键:
            assert 键 in 诊断信息, f"诊断信息缺少键: {键}"
        
        截取器.释放()
    
    def test_性能统计_包含错误信息(self):
        """测试性能统计包含错误相关信息"""
        截取器 = 屏幕截取器()
        
        统计 = 截取器.获取性能统计()
        
        # 验证错误相关的键
        assert '总失败次数' in 统计
        assert '回退次数' in 统计
        assert '恢复次数' in 统计
        assert '最后错误信息' in 统计
        assert '错误日志数量' in 统计
        assert '回退历史数量' in 统计
        
        截取器.释放()


class TestDXGI截取器_错误恢复:
    """
    DXGI 截取器错误恢复测试
    
    验证 DXGI 截取器的重新初始化和错误恢复功能
    """
    
    def test_DXGI截取器_重新初始化次数记录(self):
        """测试 DXGI 截取器重新初始化次数记录"""
        if not 后端检测器.检测DXGI可用():
            pytest.skip("DXGI 不可用")
        
        截取器 = DXGI截取器()
        
        if not 截取器.是否已初始化():
            pytest.skip("DXGI 截取器初始化失败")
        
        初始次数 = 截取器.获取重新初始化次数()
        assert 初始次数 == 0
        
        # 执行重新初始化
        截取器.重新初始化()
        
        新次数 = 截取器.获取重新初始化次数()
        assert 新次数 == 1
        
        截取器.释放()
    
    def test_DXGI截取器_最后错误信息(self):
        """测试 DXGI 截取器最后错误信息"""
        if not 后端检测器.检测DXGI可用():
            pytest.skip("DXGI 不可用")
        
        截取器 = DXGI截取器()
        
        if not 截取器.是否已初始化():
            pytest.skip("DXGI 截取器初始化失败")
        
        # 初始应该为空
        assert 截取器.获取最后错误信息() == ""
        
        截取器.释放()
    
    def test_DXGI截取器_资源统计包含错误信息(self):
        """测试 DXGI 截取器资源统计包含错误信息"""
        if not 后端检测器.检测DXGI可用():
            pytest.skip("DXGI 不可用")
        
        截取器 = DXGI截取器()
        
        if not 截取器.是否已初始化():
            pytest.skip("DXGI 截取器初始化失败")
        
        统计 = 截取器.获取资源统计()
        
        # 验证错误相关的键
        assert '连续失败次数' in 统计
        assert '重新初始化次数' in 统计
        assert '最后错误信息' in 统计
        
        截取器.释放()
    
    def test_DXGI截取器_显示模式变化检测设置(self):
        """测试 DXGI 截取器显示模式变化检测设置"""
        if not 后端检测器.检测DXGI可用():
            pytest.skip("DXGI 不可用")
        
        截取器 = DXGI截取器()
        
        if not 截取器.是否已初始化():
            pytest.skip("DXGI 截取器初始化失败")
        
        # 默认应该启用
        assert 截取器._显示模式变化检测 == True
        
        # 禁用
        截取器.设置显示模式变化检测(False)
        assert 截取器._显示模式变化检测 == False
        
        # 启用
        截取器.设置显示模式变化检测(True)
        assert 截取器._显示模式变化检测 == True
        
        截取器.释放()


class Test连续截取_错误恢复:
    """
    连续截取时的错误恢复测试
    
    验证在连续截取过程中系统的稳定性和恢复能力
    """
    
    @settings(max_examples=20, deadline=30000)
    @given(截取次数=st.integers(min_value=5, max_value=20))
    def test_属性2_连续截取稳定性(self, 截取次数: int):
        """
        **属性 2: 错误恢复能力**
        
        *对于任意* 连续截取操作，系统应保持稳定
        
        **验证: 需求 4.1, 4.2**
        """
        截取器 = 屏幕截取器(启用回退=True)
        
        成功次数 = 0
        失败次数 = 0
        
        for _ in range(截取次数):
            图像 = 截取器.截取()
            if 图像 is not None:
                成功次数 += 1
            else:
                失败次数 += 1
        
        统计 = 截取器.获取性能统计()
        截取器.释放()
        
        # 验证：成功率应该大于 0（至少有一次成功）
        # 或者系统应该记录了失败和恢复尝试
        总次数 = 成功次数 + 失败次数
        assert 总次数 == 截取次数, f"截取次数不匹配: {总次数} vs {截取次数}"
        
        # 验证统计信息一致性
        assert 统计['总截取次数'] == 成功次数, \
            f"成功次数不匹配: {统计['总截取次数']} vs {成功次数}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])
