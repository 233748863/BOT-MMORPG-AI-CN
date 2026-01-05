"""
结果时效性属性测试

属性 3: 结果时效性
*对于任意* 获取的检测结果，时间戳应反映实际检测完成时间

验证: 需求 2.3

Feature: yolo-async-detection, Property 3: 结果时效性
"""

import time
import threading
import numpy as np
import pytest
from hypothesis import given, strategies as st, settings, assume
from typing import List, Tuple, Any

# 导入被测试的模块
from 核心.异步检测 import 异步检测器, 结果缓存


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
        self.最后检测时间 = 0.0
    
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
        self.最后检测时间 = time.time()
        return [{'id': self.检测次数, 'confidence': 0.9}]


# ==================== 策略定义 ====================

@st.composite
def 检测器配置(draw):
    """生成随机检测器配置"""
    队列大小 = draw(st.integers(min_value=1, max_value=5))
    检测间隔 = draw(st.integers(min_value=1, max_value=3))
    检测延迟 = draw(st.floats(min_value=0.01, max_value=0.1))
    return 队列大小, 检测间隔, 检测延迟


@st.composite
def 时间戳容差(draw):
    """生成时间戳容差参数"""
    容差 = draw(st.floats(min_value=0.01, max_value=0.1))
    return 容差


# ==================== 属性测试 ====================

class Test结果时效性属性:
    """
    属性测试: 结果时效性
    
    Feature: yolo-async-detection, Property 3: 结果时效性
    Validates: Requirements 2.3
    """
    
    @settings(max_examples=50, deadline=120000)
    @given(配置=检测器配置())
    def test_时间戳应反映检测完成时间(self, 配置: Tuple[int, int, float]):
        """
        属性测试: 时间戳应反映实际检测完成时间
        
        *对于任意* 获取的检测结果，时间戳应反映实际检测完成时间
        
        Feature: yolo-async-detection, Property 3: 结果时效性
        Validates: Requirements 2.3
        """
        队列大小, 检测间隔, 检测延迟 = 配置
        
        # 创建模拟检测器和异步检测器
        模拟器 = 模拟检测器(检测延迟=检测延迟)
        异步器 = 异步检测器(
            检测器=模拟器,
            队列大小=队列大小,
            检测间隔=1  # 每帧都检测
        )
        
        try:
            # 启动检测器
            启动成功 = 异步器.启动()
            assert 启动成功, "检测器应成功启动"
            
            # 提交帧并等待检测完成
            图像 = np.random.randint(0, 256, (64, 64, 3), dtype=np.uint8)
            异步器.提交帧(图像)
            
            # 等待检测完成
            time.sleep(检测延迟 * 3)
            
            # 获取结果和时间戳
            结果, 时间戳, 帧编号 = 异步器.获取结果带时间戳()
            
            # 如果有检测结果，验证时间戳
            if 时间戳 > 0 and 模拟器.最后检测时间 > 0:
                # 时间戳应接近检测完成时间（容差 100ms）
                时间差 = abs(时间戳 - 模拟器.最后检测时间)
                assert 时间差 < 0.1, \
                    f"时间戳差异 {时间差:.3f}s 应小于 0.1s"
            
        finally:
            异步器.停止(超时=1.0)
    
    @settings(max_examples=50, deadline=120000)
    @given(配置=检测器配置())
    def test_时间戳应单调递增(self, 配置: Tuple[int, int, float]):
        """
        属性测试: 连续检测的时间戳应单调递增
        
        *对于任意* 连续的检测结果，后一个时间戳应大于等于前一个
        
        Feature: yolo-async-detection, Property 3: 结果时效性
        Validates: Requirements 2.3
        """
        队列大小, 检测间隔, 检测延迟 = 配置
        
        模拟器 = 模拟检测器(检测延迟=检测延迟)
        异步器 = 异步检测器(
            检测器=模拟器,
            队列大小=队列大小,
            检测间隔=1
        )
        
        时间戳列表 = []
        
        try:
            异步器.启动()
            
            图像 = np.random.randint(0, 256, (64, 64, 3), dtype=np.uint8)
            
            # 提交多帧并收集时间戳
            for _ in range(3):
                异步器.提交帧(图像)
                time.sleep(检测延迟 * 2)
                
                _, 时间戳, _ = 异步器.获取结果带时间戳()
                if 时间戳 > 0:
                    时间戳列表.append(时间戳)
            
            # 验证时间戳单调递增
            for i in range(1, len(时间戳列表)):
                assert 时间戳列表[i] >= 时间戳列表[i-1], \
                    f"时间戳应单调递增: {时间戳列表[i-1]} -> {时间戳列表[i]}"
            
        finally:
            异步器.停止(超时=1.0)
    
    @settings(max_examples=50, deadline=120000)
    @given(配置=检测器配置())
    def test_缓存年龄应与时间戳一致(self, 配置: Tuple[int, int, float]):
        """
        属性测试: 缓存年龄应与时间戳一致
        
        *对于任意* 检测结果，缓存年龄应等于当前时间减去时间戳
        
        Feature: yolo-async-detection, Property 3: 结果时效性
        Validates: Requirements 2.3
        """
        队列大小, 检测间隔, 检测延迟 = 配置
        
        缓存 = 结果缓存()
        
        # 更新缓存
        测试结果 = [{'id': 1}]
        缓存.更新(测试结果, 帧编号=1)
        
        # 等待一段时间
        等待时间 = 0.1
        time.sleep(等待时间)
        
        # 获取时间戳和年龄
        _, 时间戳, _ = 缓存.获取()
        年龄 = 缓存.获取年龄()
        
        # 计算期望年龄
        当前时间 = time.time()
        期望年龄 = 当前时间 - 时间戳
        
        # 年龄应接近期望值（容差 50ms）
        年龄差 = abs(年龄 - 期望年龄)
        assert 年龄差 < 0.05, \
            f"年龄差异 {年龄差:.3f}s 应小于 0.05s"
        
        # 年龄应大于等于等待时间
        assert 年龄 >= 等待时间 - 0.01, \
            f"年龄 {年龄:.3f}s 应大于等待时间 {等待时间}s"


class Test结果时效性单元测试:
    """结果时效性单元测试"""
    
    def test_结果缓存时间戳更新(self):
        """测试结果缓存时间戳正确更新"""
        缓存 = 结果缓存()
        
        # 初始时间戳应为 0
        _, 初始时间戳, _ = 缓存.获取()
        assert 初始时间戳 == 0.0, "初始时间戳应为 0"
        
        # 更新后时间戳应为当前时间
        更新前时间 = time.time()
        缓存.更新([{'id': 1}], 帧编号=1)
        更新后时间 = time.time()
        
        _, 时间戳, _ = 缓存.获取()
        
        assert 更新前时间 <= 时间戳 <= 更新后时间, \
            f"时间戳 {时间戳} 应在 [{更新前时间}, {更新后时间}] 范围内"
    
    def test_异步检测时间戳准确性(self):
        """测试异步检测时间戳准确性"""
        模拟器 = 模拟检测器(检测延迟=0.05)
        异步器 = 异步检测器(
            检测器=模拟器,
            队列大小=3,
            检测间隔=1
        )
        
        try:
            异步器.启动()
            
            # 提交帧
            图像 = np.zeros((64, 64, 3), dtype=np.uint8)
            异步器.提交帧(图像)
            
            # 等待检测完成
            time.sleep(0.2)
            
            # 获取结果
            结果, 时间戳, 帧编号 = 异步器.获取结果带时间戳()
            
            # 验证时间戳
            if 时间戳 > 0:
                当前时间 = time.time()
                年龄 = 当前时间 - 时间戳
                
                # 年龄应小于等待时间
                assert 年龄 < 0.3, f"结果年龄 {年龄:.3f}s 应小于 0.3s"
            
        finally:
            异步器.停止(超时=1.0)
    
    def test_多次更新时间戳递增(self):
        """测试多次更新时间戳递增"""
        缓存 = 结果缓存()
        时间戳列表 = []
        
        for i in range(5):
            缓存.更新([{'id': i}], 帧编号=i)
            _, 时间戳, _ = 缓存.获取()
            时间戳列表.append(时间戳)
            time.sleep(0.01)
        
        # 验证时间戳递增
        for i in range(1, len(时间戳列表)):
            assert 时间戳列表[i] > 时间戳列表[i-1], \
                f"时间戳应递增: {时间戳列表[i-1]} -> {时间戳列表[i]}"
    
    def test_缓存有效性检查(self):
        """测试缓存有效性检查"""
        缓存 = 结果缓存()
        
        # 初始状态应无效（年龄为无穷大）
        assert not 缓存.是否有效(最大年龄=1.0), "初始状态应无效"
        
        # 更新后应有效
        缓存.更新([{'id': 1}], 帧编号=1)
        assert 缓存.是否有效(最大年龄=1.0), "更新后应有效"
        
        # 等待超过最大年龄后应无效
        time.sleep(0.15)
        assert not 缓存.是否有效(最大年龄=0.1), "超时后应无效"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
