"""
异步检测优雅关闭属性测试

属性 2: 优雅关闭
*对于任意* 停止请求，检测线程应在 1 秒内完成关闭

验证: 需求 1.5

Feature: yolo-async-detection, Property 2: 优雅关闭
"""

import time
import threading
import numpy as np
import pytest
from hypothesis import given, strategies as st, settings, assume
from typing import List, Tuple, Any

# 导入被测试的模块
from 核心.异步检测 import 异步检测器, 检测队列, 结果缓存


# ==================== 模拟检测器 ====================

class 模拟检测器:
    """模拟 YOLO 检测器，用于测试"""
    
    def __init__(self, 检测延迟: float = 0.05):
        """
        初始化模拟检测器
        
        参数:
            检测延迟: 模拟检测延迟（秒）
        """
        self.检测延迟 = 检测延迟
        self.检测次数 = 0
    
    def 检测(self, 图像: np.ndarray) -> List[dict]:
        """
        模拟检测
        
        参数:
            图像: 输入图像
            
        返回:
            模拟检测结果
        """
        time.sleep(self.检测延迟)
        self.检测次数 += 1
        return [{'id': self.检测次数, 'confidence': 0.9}]


# ==================== 策略定义 ====================

@st.composite
def 检测器配置(draw):
    """生成随机检测器配置"""
    队列大小 = draw(st.integers(min_value=1, max_value=10))
    检测间隔 = draw(st.integers(min_value=1, max_value=5))
    检测延迟 = draw(st.floats(min_value=0.01, max_value=0.2))
    return 队列大小, 检测间隔, 检测延迟


@st.composite
def 停止超时参数(draw):
    """生成停止超时参数"""
    超时 = draw(st.floats(min_value=0.5, max_value=2.0))
    return 超时


# ==================== 属性测试 ====================

class Test优雅关闭属性:
    """
    属性测试: 优雅关闭
    
    Feature: yolo-async-detection, Property 2: 优雅关闭
    Validates: Requirements 1.5
    """
    
    @settings(max_examples=100, deadline=60000)
    @given(配置=检测器配置())
    def test_停止请求应在1秒内完成(self, 配置: Tuple[int, int, float]):
        """
        属性测试: 停止请求应在 1 秒内完成
        
        *对于任意* 停止请求，检测线程应在 1 秒内完成关闭
        
        Feature: yolo-async-detection, Property 2: 优雅关闭
        Validates: Requirements 1.5
        """
        队列大小, 检测间隔, 检测延迟 = 配置
        
        # 创建模拟检测器和异步检测器
        模拟器 = 模拟检测器(检测延迟=检测延迟)
        异步器 = 异步检测器(
            检测器=模拟器,
            队列大小=队列大小,
            检测间隔=检测间隔
        )
        
        try:
            # 启动检测器
            启动成功 = 异步器.启动()
            assert 启动成功, "检测器应成功启动"
            
            # 提交一些帧
            图像 = np.random.randint(0, 256, (64, 64, 3), dtype=np.uint8)
            for _ in range(5):
                异步器.提交帧(图像)
                time.sleep(0.01)
            
            # 记录停止开始时间
            停止开始时间 = time.time()
            
            # 发送停止请求
            停止成功 = 异步器.停止(超时=1.0)
            
            # 计算停止耗时
            停止耗时 = time.time() - 停止开始时间
            
            # 验证停止在 1 秒内完成
            assert 停止耗时 < 1.0, f"停止耗时 {停止耗时:.3f}s 应小于 1 秒"
            assert 停止成功, "停止应成功"
            assert not 异步器.是否运行中(), "停止后应不再运行"
            
        finally:
            # 确保清理
            if 异步器.是否运行中():
                异步器.停止(超时=2.0)
    
    @settings(max_examples=100, deadline=60000)
    @given(配置=检测器配置())
    def test_空闲状态下停止应立即完成(self, 配置: Tuple[int, int, float]):
        """
        属性测试: 空闲状态下停止应立即完成
        
        *对于任意* 空闲的检测器，停止应几乎立即完成
        
        Feature: yolo-async-detection, Property 2: 优雅关闭
        Validates: Requirements 1.5
        """
        队列大小, 检测间隔, 检测延迟 = 配置
        
        模拟器 = 模拟检测器(检测延迟=检测延迟)
        异步器 = 异步检测器(
            检测器=模拟器,
            队列大小=队列大小,
            检测间隔=检测间隔
        )
        
        try:
            # 启动检测器
            异步器.启动()
            
            # 等待一小段时间让线程进入等待状态
            time.sleep(0.1)
            
            # 记录停止开始时间
            停止开始时间 = time.time()
            
            # 发送停止请求
            停止成功 = 异步器.停止(超时=1.0)
            
            # 计算停止耗时
            停止耗时 = time.time() - 停止开始时间
            
            # 空闲状态下停止应很快（小于 0.6 秒，考虑队列超时 0.5 秒）
            assert 停止耗时 < 0.7, f"空闲状态停止耗时 {停止耗时:.3f}s 应小于 0.7 秒"
            assert 停止成功, "停止应成功"
            
        finally:
            if 异步器.是否运行中():
                异步器.停止(超时=2.0)
    
    @settings(max_examples=100, deadline=60000)
    @given(配置=检测器配置())
    def test_繁忙状态下停止应在1秒内完成(self, 配置: Tuple[int, int, float]):
        """
        属性测试: 繁忙状态下停止应在 1 秒内完成
        
        *对于任意* 正在处理任务的检测器，停止应在 1 秒内完成
        
        Feature: yolo-async-detection, Property 2: 优雅关闭
        Validates: Requirements 1.5
        """
        队列大小, 检测间隔, 检测延迟 = 配置
        
        模拟器 = 模拟检测器(检测延迟=检测延迟)
        异步器 = 异步检测器(
            检测器=模拟器,
            队列大小=队列大小,
            检测间隔=1  # 每帧都检测，增加繁忙程度
        )
        
        try:
            # 启动检测器
            异步器.启动()
            
            # 持续提交帧，保持繁忙状态
            图像 = np.random.randint(0, 256, (64, 64, 3), dtype=np.uint8)
            for _ in range(队列大小 * 2):
                异步器.提交帧(图像)
            
            # 记录停止开始时间
            停止开始时间 = time.time()
            
            # 发送停止请求
            停止成功 = 异步器.停止(超时=1.0)
            
            # 计算停止耗时
            停止耗时 = time.time() - 停止开始时间
            
            # 验证停止在 1 秒内完成
            assert 停止耗时 < 1.0, f"繁忙状态停止耗时 {停止耗时:.3f}s 应小于 1 秒"
            assert 停止成功, "停止应成功"
            
        finally:
            if 异步器.是否运行中():
                异步器.停止(超时=2.0)
    
    @settings(max_examples=100, deadline=60000)
    @given(配置=检测器配置())
    def test_重复停止应安全(self, 配置: Tuple[int, int, float]):
        """
        属性测试: 重复停止应安全
        
        *对于任意* 检测器，多次调用停止应安全且快速
        
        Feature: yolo-async-detection, Property 2: 优雅关闭
        Validates: Requirements 1.5
        """
        队列大小, 检测间隔, 检测延迟 = 配置
        
        模拟器 = 模拟检测器(检测延迟=检测延迟)
        异步器 = 异步检测器(
            检测器=模拟器,
            队列大小=队列大小,
            检测间隔=检测间隔
        )
        
        try:
            # 启动检测器
            异步器.启动()
            time.sleep(0.05)
            
            # 第一次停止
            停止开始时间 = time.time()
            停止成功1 = 异步器.停止(超时=1.0)
            停止耗时1 = time.time() - 停止开始时间
            
            # 第二次停止（应立即返回）
            停止开始时间 = time.time()
            停止成功2 = 异步器.停止(超时=1.0)
            停止耗时2 = time.time() - 停止开始时间
            
            # 第三次停止
            停止开始时间 = time.time()
            停止成功3 = 异步器.停止(超时=1.0)
            停止耗时3 = time.time() - 停止开始时间
            
            # 验证
            assert 停止成功1, "第一次停止应成功"
            assert 停止成功2, "第二次停止应成功"
            assert 停止成功3, "第三次停止应成功"
            
            # 重复停止应几乎立即返回
            assert 停止耗时2 < 0.1, f"重复停止耗时 {停止耗时2:.3f}s 应很短"
            assert 停止耗时3 < 0.1, f"重复停止耗时 {停止耗时3:.3f}s 应很短"
            
        finally:
            if 异步器.是否运行中():
                异步器.停止(超时=2.0)
    
    @settings(max_examples=100, deadline=60000)
    @given(配置=检测器配置())
    def test_未启动时停止应安全(self, 配置: Tuple[int, int, float]):
        """
        属性测试: 未启动时停止应安全
        
        *对于任意* 未启动的检测器，调用停止应安全且立即返回
        
        Feature: yolo-async-detection, Property 2: 优雅关闭
        Validates: Requirements 1.5
        """
        队列大小, 检测间隔, 检测延迟 = 配置
        
        模拟器 = 模拟检测器(检测延迟=检测延迟)
        异步器 = 异步检测器(
            检测器=模拟器,
            队列大小=队列大小,
            检测间隔=检测间隔
        )
        
        # 不启动，直接停止
        停止开始时间 = time.time()
        停止成功 = 异步器.停止(超时=1.0)
        停止耗时 = time.time() - 停止开始时间
        
        # 验证
        assert 停止成功, "未启动时停止应返回成功"
        assert 停止耗时 < 0.1, f"未启动时停止耗时 {停止耗时:.3f}s 应很短"


class Test优雅关闭单元测试:
    """优雅关闭单元测试"""
    
    def test_基本启动停止(self):
        """测试基本启动停止流程"""
        模拟器 = 模拟检测器(检测延迟=0.05)
        异步器 = 异步检测器(检测器=模拟器, 队列大小=3, 检测间隔=1)
        
        # 启动
        assert 异步器.启动() == True
        assert 异步器.是否运行中() == True
        
        # 停止
        停止开始 = time.time()
        assert 异步器.停止(超时=1.0) == True
        停止耗时 = time.time() - 停止开始
        
        assert 异步器.是否运行中() == False
        assert 停止耗时 < 1.0, f"停止耗时 {停止耗时:.3f}s 应小于 1 秒"
    
    def test_上下文管理器(self):
        """测试上下文管理器自动关闭"""
        模拟器 = 模拟检测器(检测延迟=0.05)
        
        停止开始 = None
        with 异步检测器(检测器=模拟器, 队列大小=3, 检测间隔=1) as 异步器:
            assert 异步器.是否运行中() == True
            
            # 提交一些帧
            图像 = np.zeros((64, 64, 3), dtype=np.uint8)
            for _ in range(3):
                异步器.提交帧(图像)
            
            停止开始 = time.time()
        
        # 退出上下文后应自动停止
        停止耗时 = time.time() - 停止开始
        assert 停止耗时 < 1.5, f"上下文退出耗时 {停止耗时:.3f}s 应小于 1.5 秒"
    
    def test_停止事件信号(self):
        """测试停止事件信号机制"""
        模拟器 = 模拟检测器(检测延迟=0.1)
        异步器 = 异步检测器(检测器=模拟器, 队列大小=3, 检测间隔=1)
        
        异步器.启动()
        
        # 验证停止事件初始状态
        assert not 异步器._停止事件.is_set()
        
        # 停止
        异步器.停止(超时=1.0)
        
        # 验证停止事件已设置
        assert 异步器._停止事件.is_set()
    
    def test_线程正确终止(self):
        """测试线程正确终止"""
        模拟器 = 模拟检测器(检测延迟=0.05)
        异步器 = 异步检测器(检测器=模拟器, 队列大小=3, 检测间隔=1)
        
        异步器.启动()
        
        # 获取线程引用
        线程 = 异步器._线程
        assert 线程 is not None
        assert 线程.is_alive()
        
        # 停止
        异步器.停止(超时=1.0)
        
        # 验证线程已终止
        assert not 线程.is_alive()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
