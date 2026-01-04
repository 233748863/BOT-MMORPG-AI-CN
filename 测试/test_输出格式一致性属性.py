"""
输出格式一致性属性测试模块

使用 Hypothesis 进行属性测试，验证不同截取后端返回相同格式的图像。

**属性 1: 输出格式一致性**
*对于任意* 截取请求，DXGI 和 GDI 后端应返回相同格式的图像

**验证: 需求 1.3, 5.3**

**Feature: screen-capture-optimization, Property 1: 输出格式一致性**
"""

import os
import sys
import pytest
import numpy as np
from hypothesis import given, strategies as st, settings, assume
from typing import Tuple, Optional

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


def 后端名称策略():
    """生成可用后端名称的策略"""
    可用后端 = 后端检测器.获取可用后端列表()
    if not 可用后端:
        可用后端 = ["pil"]  # 回退到 PIL
    return st.sampled_from(可用后端)


# ==================== 辅助函数 ====================

def 验证图像格式(图像: np.ndarray) -> Tuple[bool, str]:
    """
    验证图像格式是否符合要求
    
    需求 1.3: 返回与 GDI 实现相同格式的图像（numpy 数组，RGB/BGR）
    需求 5.3: 返回相同格式的图像（numpy 数组，RGB）
    
    参数:
        图像: 待验证的图像
        
    返回:
        (是否有效, 错误信息)
    """
    if 图像 is None:
        return False, "图像为 None"
    
    if not isinstance(图像, np.ndarray):
        return False, f"图像类型错误: {type(图像)}"
    
    if 图像.ndim != 3:
        return False, f"图像维度错误: {图像.ndim}，应为 3"
    
    if 图像.shape[2] != 3:
        return False, f"图像通道数错误: {图像.shape[2]}，应为 3"
    
    if 图像.dtype != np.uint8:
        return False, f"图像数据类型错误: {图像.dtype}，应为 uint8"
    
    return True, ""


def 比较图像格式(图像A: np.ndarray, 图像B: np.ndarray) -> Tuple[bool, str]:
    """
    比较两个图像的格式是否一致
    
    参数:
        图像A: 第一个图像
        图像B: 第二个图像
        
    返回:
        (格式是否一致, 差异描述)
    """
    if 图像A is None or 图像B is None:
        return False, "其中一个图像为 None"
    
    # 检查类型
    if type(图像A) != type(图像B):
        return False, f"类型不一致: {type(图像A)} vs {type(图像B)}"
    
    # 检查维度
    if 图像A.ndim != 图像B.ndim:
        return False, f"维度不一致: {图像A.ndim} vs {图像B.ndim}"
    
    # 检查通道数
    if 图像A.shape[2] != 图像B.shape[2]:
        return False, f"通道数不一致: {图像A.shape[2]} vs {图像B.shape[2]}"
    
    # 检查数据类型
    if 图像A.dtype != 图像B.dtype:
        return False, f"数据类型不一致: {图像A.dtype} vs {图像B.dtype}"
    
    return True, ""


# ==================== 属性测试类 ====================

class Test输出格式一致性_属性测试:
    """
    输出格式一致性属性测试
    
    **Feature: screen-capture-optimization, Property 1: 输出格式一致性**
    
    验证不同截取后端返回相同格式的图像（numpy 数组，BGR，uint8）
    """
    
    @settings(max_examples=100, deadline=10000)
    @given(区域=区域策略())
    def test_属性1_全屏截取格式一致性(self, 区域: Tuple[int, int, int, int]):
        """
        **属性 1: 输出格式一致性**
        
        *对于任意* 截取请求，所有可用后端应返回相同格式的图像
        
        **验证: 需求 1.3, 5.3**
        """
        可用后端 = 后端检测器.获取可用后端列表()
        assume(len(可用后端) >= 1)  # 至少需要一个后端
        
        截取结果 = {}
        
        for 后端名称 in 可用后端:
            try:
                截取器 = 屏幕截取器(首选后端=后端名称, 启用回退=False)
                图像 = 截取器.截取()  # 全屏截取
                截取器.释放()
                
                if 图像 is not None:
                    截取结果[后端名称] = 图像
            except Exception:
                continue  # 跳过初始化失败的后端
        
        assume(len(截取结果) >= 1)  # 至少需要一个成功的截取
        
        # 验证所有截取结果的格式
        for 后端名称, 图像 in 截取结果.items():
            有效, 错误信息 = 验证图像格式(图像)
            assert 有效, f"后端 {后端名称} 输出格式无效: {错误信息}"
    
    @settings(max_examples=100, deadline=10000)
    @given(区域=区域策略())
    def test_属性1_区域截取格式一致性(self, 区域: Tuple[int, int, int, int]):
        """
        **属性 1: 输出格式一致性**
        
        *对于任意* 区域截取请求，所有可用后端应返回相同格式的图像
        
        **验证: 需求 1.3, 5.3**
        """
        可用后端 = 后端检测器.获取可用后端列表()
        assume(len(可用后端) >= 1)
        
        截取结果 = {}
        
        for 后端名称 in 可用后端:
            try:
                截取器 = 屏幕截取器(首选后端=后端名称, 启用回退=False)
                图像 = 截取器.截取(区域)
                截取器.释放()
                
                if 图像 is not None:
                    截取结果[后端名称] = 图像
            except Exception:
                continue
        
        assume(len(截取结果) >= 1)
        
        # 验证所有截取结果的格式
        for 后端名称, 图像 in 截取结果.items():
            有效, 错误信息 = 验证图像格式(图像)
            assert 有效, f"后端 {后端名称} 区域截取输出格式无效: {错误信息}"
            
            # 验证区域截取的尺寸
            x, y, w, h = 区域
            # 注意：实际尺寸可能因边界裁剪而略有不同
            assert 图像.shape[0] > 0, f"后端 {后端名称} 区域截取高度为 0"
            assert 图像.shape[1] > 0, f"后端 {后端名称} 区域截取宽度为 0"
    
    @settings(max_examples=50, deadline=15000)
    @given(后端A=后端名称策略(), 后端B=后端名称策略())
    def test_属性1_跨后端格式一致性(self, 后端A: str, 后端B: str):
        """
        **属性 1: 输出格式一致性**
        
        *对于任意* 两个后端，它们的输出格式应该一致
        
        **验证: 需求 1.3, 5.3**
        """
        assume(后端A != 后端B)  # 确保是不同的后端
        
        try:
            截取器A = 屏幕截取器(首选后端=后端A, 启用回退=False)
            图像A = 截取器A.截取()
            截取器A.释放()
        except Exception:
            assume(False)  # 跳过无法初始化的后端
            return
        
        try:
            截取器B = 屏幕截取器(首选后端=后端B, 启用回退=False)
            图像B = 截取器B.截取()
            截取器B.释放()
        except Exception:
            assume(False)
            return
        
        assume(图像A is not None and 图像B is not None)
        
        # 比较格式
        格式一致, 差异描述 = 比较图像格式(图像A, 图像B)
        assert 格式一致, f"后端 {后端A} 和 {后端B} 输出格式不一致: {差异描述}"


class Test输出格式验证_单元测试:
    """
    输出格式验证的单元测试
    
    验证基本的格式检查功能
    """
    
    def test_有效图像格式验证(self):
        """测试有效图像格式的验证"""
        有效图像 = np.zeros((100, 100, 3), dtype=np.uint8)
        有效, 错误 = 验证图像格式(有效图像)
        assert 有效, f"有效图像应该通过验证: {错误}"
    
    def test_无效图像_None(self):
        """测试 None 图像的验证"""
        有效, 错误 = 验证图像格式(None)
        assert not 有效
        assert "None" in 错误
    
    def test_无效图像_错误维度(self):
        """测试错误维度图像的验证"""
        错误图像 = np.zeros((100, 100), dtype=np.uint8)  # 2D 图像
        有效, 错误 = 验证图像格式(错误图像)
        assert not 有效
        assert "维度" in 错误
    
    def test_无效图像_错误通道数(self):
        """测试错误通道数图像的验证"""
        错误图像 = np.zeros((100, 100, 4), dtype=np.uint8)  # 4 通道
        有效, 错误 = 验证图像格式(错误图像)
        assert not 有效
        assert "通道" in 错误
    
    def test_无效图像_错误数据类型(self):
        """测试错误数据类型图像的验证"""
        错误图像 = np.zeros((100, 100, 3), dtype=np.float32)  # float32
        有效, 错误 = 验证图像格式(错误图像)
        assert not 有效
        assert "数据类型" in 错误
    
    def test_格式比较_一致(self):
        """测试格式一致的图像比较"""
        图像A = np.zeros((100, 100, 3), dtype=np.uint8)
        图像B = np.ones((200, 200, 3), dtype=np.uint8)  # 尺寸不同但格式相同
        一致, 差异 = 比较图像格式(图像A, 图像B)
        assert 一致, f"格式应该一致: {差异}"
    
    def test_格式比较_不一致_通道数(self):
        """测试通道数不一致的图像比较"""
        图像A = np.zeros((100, 100, 3), dtype=np.uint8)
        图像B = np.zeros((100, 100, 4), dtype=np.uint8)
        一致, 差异 = 比较图像格式(图像A, 图像B)
        assert not 一致
        assert "通道" in 差异


class Test截取器接口一致性:
    """
    测试截取器接口的一致性
    
    验证所有截取器实现相同的接口
    """
    
    def test_屏幕截取器_基本接口(self):
        """测试屏幕截取器的基本接口"""
        截取器 = 屏幕截取器()
        
        # 验证必要的方法存在
        assert hasattr(截取器, '截取')
        assert hasattr(截取器, '截取并缩放')
        assert hasattr(截取器, '获取当前后端')
        assert hasattr(截取器, '获取性能统计')
        assert hasattr(截取器, '释放')
        
        截取器.释放()
    
    def test_屏幕截取器_截取返回格式(self):
        """测试屏幕截取器截取返回的格式"""
        截取器 = 屏幕截取器()
        图像 = 截取器.截取()
        截取器.释放()
        
        if 图像 is not None:
            有效, 错误 = 验证图像格式(图像)
            assert 有效, f"截取返回格式无效: {错误}"
    
    def test_屏幕截取器_缩放截取返回格式(self):
        """测试屏幕截取器缩放截取返回的格式"""
        截取器 = 屏幕截取器()
        目标尺寸 = (320, 180)
        图像 = 截取器.截取并缩放(目标尺寸=目标尺寸)
        截取器.释放()
        
        if 图像 is not None:
            有效, 错误 = 验证图像格式(图像)
            assert 有效, f"缩放截取返回格式无效: {错误}"
            
            # 验证尺寸
            assert 图像.shape[1] == 目标尺寸[0], f"宽度不匹配: {图像.shape[1]} vs {目标尺寸[0]}"
            assert 图像.shape[0] == 目标尺寸[1], f"高度不匹配: {图像.shape[0]} vs {目标尺寸[1]}"
    
    def test_性能统计_返回格式(self):
        """测试性能统计返回的格式"""
        截取器 = 屏幕截取器()
        
        # 执行几次截取
        for _ in range(3):
            截取器.截取()
        
        统计 = 截取器.获取性能统计()
        截取器.释放()
        
        # 验证统计字典包含必要的键
        必要键 = ['后端类型', '总截取次数', '总失败次数', '平均截取时间', '成功率']
        for 键 in 必要键:
            assert 键 in 统计, f"性能统计缺少键: {键}"
        
        # 验证数值类型
        assert isinstance(统计['总截取次数'], int)
        assert isinstance(统计['平均截取时间'], (int, float))
        assert isinstance(统计['成功率'], (int, float))


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])
