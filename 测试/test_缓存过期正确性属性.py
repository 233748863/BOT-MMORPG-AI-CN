"""
缓存过期正确性属性测试

属性 3: 缓存过期正确性
*对于任意* 超过过期时间的缓存，下次请求应触发新检测

验证: 需求 4.1, 4.2
"""

import time
import numpy as np
import pytest
from hypothesis import given, strategies as st, settings, assume
from dataclasses import dataclass
from typing import List

# 导入被测试的模块
from 核心.智能缓存 import 智能缓存, 缓存统计, 缓存条目
from 核心.缓存策略 import 缓存策略


# ==================== 策略定义 ====================

@st.composite
def 随机图像(draw, 最小尺寸=32, 最大尺寸=128):
    """生成随机图像"""
    宽度 = draw(st.integers(min_value=最小尺寸, max_value=最大尺寸))
    高度 = draw(st.integers(min_value=最小尺寸, max_value=最大尺寸))
    图像 = np.random.randint(0, 256, (高度, 宽度, 3), dtype=np.uint8)
    return 图像


@st.composite
def 有效过期时间(draw):
    """生成有效的过期时间（秒）"""
    # 使用较短的过期时间以便测试
    return draw(st.floats(min_value=0.01, max_value=0.5, allow_nan=False, allow_infinity=False))


@st.composite
def 有效相似度阈值(draw):
    """生成有效的相似度阈值"""
    return draw(st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False))


# ==================== 模拟检测器 ====================

class 模拟检测器:
    """模拟检测器，用于测试"""
    
    def __init__(self):
        self.检测次数 = 0
        self.最后检测图像 = None
    
    def 检测(self, 图像: np.ndarray, 使用缓存: bool = True) -> List:
        """模拟检测方法"""
        self.检测次数 += 1
        self.最后检测图像 = 图像
        # 返回空列表作为模拟检测结果
        return []
    
    def 重置(self):
        """重置计数器"""
        self.检测次数 = 0
        self.最后检测图像 = None


# ==================== 属性测试 ====================

class Test缓存过期正确性属性:
    """
    属性测试: 缓存过期正确性
    
    Feature: detection-cache-optimization, Property 3: 缓存过期正确性
    Validates: Requirements 4.1, 4.2
    """
    
    @settings(max_examples=100, deadline=10000)
    @given(过期时间=有效过期时间())
    def test_超过过期时间缓存失效(self, 过期时间: float):
        """
        属性测试: 超过过期时间的缓存应该失效
        
        *对于任意* 过期时间设置，当缓存年龄超过过期时间时，
        缓存应该被判定为过期
        
        Feature: detection-cache-optimization, Property 3: 缓存过期正确性
        Validates: Requirements 4.1, 4.2
        """
        # 创建智能缓存
        缓存 = 智能缓存(过期时间=过期时间)
        
        # 创建测试图像
        测试图像 = np.random.randint(0, 256, (64, 64, 3), dtype=np.uint8)
        
        # 存储缓存
        缓存.存储(测试图像, [])
        
        # 刚存储时不应过期
        assert not 缓存.是否过期(), "刚存储的缓存不应过期"
        
        # 等待超过过期时间
        time.sleep(过期时间 + 0.02)
        
        # 现在应该过期
        assert 缓存.是否过期(), f"超过过期时间 {过期时间}s 后缓存应该过期"
    
    @settings(max_examples=100, deadline=10000)
    @given(过期时间=有效过期时间())
    def test_过期缓存获取返回None(self, 过期时间: float):
        """
        属性测试: 过期的缓存获取应返回 None
        
        *对于任意* 过期时间设置，当缓存过期后，
        获取操作应返回 None 而不是缓存的结果
        
        Feature: detection-cache-optimization, Property 3: 缓存过期正确性
        Validates: Requirements 4.1, 4.2
        """
        # 创建智能缓存
        缓存 = 智能缓存(过期时间=过期时间)
        
        # 创建测试图像
        测试图像 = np.random.randint(0, 256, (64, 64, 3), dtype=np.uint8)
        
        # 存储缓存
        缓存.存储(测试图像, [])
        
        # 刚存储时应该能获取
        结果 = 缓存.获取(测试图像)
        assert 结果 is not None, "刚存储的缓存应该能获取"
        
        # 等待超过过期时间
        time.sleep(过期时间 + 0.02)
        
        # 过期后获取应返回 None
        结果 = 缓存.获取(测试图像)
        assert 结果 is None, f"过期后获取应返回 None"
    
    @settings(max_examples=100, deadline=10000)
    @given(过期时间=有效过期时间())
    def test_过期后触发新检测(self, 过期时间: float):
        """
        属性测试: 缓存过期后应触发新检测
        
        *对于任意* 过期时间设置，当缓存过期后，
        下次检测请求应触发新的检测而不是使用缓存
        
        Feature: detection-cache-optimization, Property 3: 缓存过期正确性
        Validates: Requirements 4.1, 4.2
        """
        # 创建模拟检测器
        检测器 = 模拟检测器()
        
        # 创建智能缓存
        缓存 = 智能缓存(检测器=检测器, 过期时间=过期时间)
        
        # 创建测试图像
        测试图像 = np.random.randint(0, 256, (64, 64, 3), dtype=np.uint8)
        
        # 第一次检测
        缓存.检测(测试图像)
        初始检测次数 = 检测器.检测次数
        assert 初始检测次数 == 1, "第一次应该执行检测"
        
        # 立即再次检测（应使用缓存）
        缓存.检测(测试图像)
        assert 检测器.检测次数 == 1, "缓存有效时不应触发新检测"
        
        # 等待超过过期时间
        time.sleep(过期时间 + 0.02)
        
        # 再次检测（应触发新检测）
        缓存.检测(测试图像)
        assert 检测器.检测次数 == 2, "缓存过期后应触发新检测"
    
    @settings(max_examples=100, deadline=10000)
    @given(过期时间=有效过期时间())
    def test_禁用时间过期后缓存不过期(self, 过期时间: float):
        """
        属性测试: 禁用时间过期后缓存不应过期
        
        *对于任意* 过期时间设置，当禁用时间过期后，
        即使超过过期时间，缓存也不应被判定为过期
        
        Feature: detection-cache-optimization, Property 3: 缓存过期正确性
        Validates: Requirements 4.3
        """
        # 创建智能缓存
        缓存 = 智能缓存(过期时间=过期时间)
        
        # 创建测试图像
        测试图像 = np.random.randint(0, 256, (64, 64, 3), dtype=np.uint8)
        
        # 存储缓存
        缓存.存储(测试图像, [])
        
        # 禁用时间过期
        缓存.禁用时间过期()
        
        # 等待超过过期时间
        time.sleep(过期时间 + 0.02)
        
        # 禁用后不应过期
        assert not 缓存.是否过期(), "禁用时间过期后缓存不应过期"
        
        # 获取应该成功
        结果 = 缓存.获取(测试图像)
        assert 结果 is not None, "禁用时间过期后应能获取缓存"


class Test缓存统计属性:
    """
    属性测试: 缓存统计功能
    
    Feature: detection-cache-optimization
    Validates: Requirements 2.4
    """
    
    @settings(max_examples=100, deadline=5000)
    @given(命中次数=st.integers(min_value=0, max_value=100),
           未命中次数=st.integers(min_value=0, max_value=100))
    def test_命中率计算正确(self, 命中次数: int, 未命中次数: int):
        """
        属性测试: 命中率计算应正确
        
        Feature: detection-cache-optimization
        Validates: Requirements 2.4
        """
        统计 = 缓存统计()
        
        # 记录命中
        for _ in range(命中次数):
            统计.记录命中()
        
        # 记录未命中
        for _ in range(未命中次数):
            统计.记录未命中()
        
        总数 = 命中次数 + 未命中次数
        
        if 总数 == 0:
            assert 统计.命中率 == 0.0, "无请求时命中率应为 0"
        else:
            期望命中率 = 命中次数 / 总数
            assert abs(统计.命中率 - 期望命中率) < 0.001, \
                f"命中率计算错误: 期望 {期望命中率}, 实际 {统计.命中率}"
    
    @settings(max_examples=100, deadline=5000)
    @given(过期次数=st.integers(min_value=0, max_value=50),
           区域次数=st.integers(min_value=0, max_value=50),
           相似度次数=st.integers(min_value=0, max_value=50))
    def test_失效原因统计正确(self, 过期次数: int, 区域次数: int, 相似度次数: int):
        """
        属性测试: 失效原因统计应正确
        
        Feature: detection-cache-optimization
        Validates: Requirements 2.4
        """
        统计 = 缓存统计()
        
        # 记录各种失效原因
        for _ in range(过期次数):
            统计.记录未命中("过期")
        
        for _ in range(区域次数):
            统计.记录未命中("区域变化")
        
        for _ in range(相似度次数):
            统计.记录未命中("相似度不足")
        
        assert 统计.过期失效数 == 过期次数, f"过期失效数错误: {统计.过期失效数}"
        assert 统计.区域失效数 == 区域次数, f"区域失效数错误: {统计.区域失效数}"
        assert 统计.相似度失效数 == 相似度次数, f"相似度失效数错误: {统计.相似度失效数}"
        assert 统计.缓存未命中数 == 过期次数 + 区域次数 + 相似度次数


class Test缓存条目属性:
    """
    属性测试: 缓存条目功能
    
    Feature: detection-cache-optimization
    """
    
    @settings(max_examples=100, deadline=5000)
    @given(等待时间=st.floats(min_value=0.01, max_value=0.2, allow_nan=False, allow_infinity=False))
    def test_缓存年龄计算正确(self, 等待时间: float):
        """
        属性测试: 缓存年龄应正确反映时间流逝
        
        Feature: detection-cache-optimization
        """
        图像 = np.zeros((64, 64, 3), dtype=np.uint8)
        条目 = 缓存条目(结果=[], 时间戳=time.time(), 参考帧=图像)
        
        # 等待一段时间
        time.sleep(等待时间)
        
        # 年龄应该接近等待时间
        年龄 = 条目.年龄
        assert 年龄 >= 等待时间, f"年龄 {年龄} 应该 >= 等待时间 {等待时间}"
        # 允许一些误差（最多 50ms）
        assert 年龄 < 等待时间 + 0.05, f"年龄 {年龄} 不应该远大于等待时间 {等待时间}"


class Test智能缓存单元测试:
    """智能缓存单元测试"""
    
    def test_初始化默认参数(self):
        """测试默认初始化"""
        缓存 = 智能缓存()
        assert 缓存.策略.全局阈值 == 0.95
        assert 缓存.策略.过期时间 == 0.5
    
    def test_初始化自定义参数(self):
        """测试自定义参数初始化"""
        缓存 = 智能缓存(相似度阈值=0.8, 过期时间=1.0)
        assert 缓存.策略.全局阈值 == 0.8
        assert 缓存.策略.过期时间 == 1.0
    
    def test_存储和获取(self):
        """测试存储和获取功能"""
        缓存 = 智能缓存()
        图像 = np.zeros((64, 64, 3), dtype=np.uint8)
        
        # 存储
        缓存.存储(图像, [])
        
        # 获取
        结果 = 缓存.获取(图像)
        assert 结果 is not None
        assert 结果 == []
    
    def test_清空缓存(self):
        """测试清空缓存"""
        缓存 = 智能缓存()
        图像 = np.zeros((64, 64, 3), dtype=np.uint8)
        
        缓存.存储(图像, [])
        assert 缓存.是否有缓存()
        
        缓存.清空()
        assert not 缓存.是否有缓存()
    
    def test_获取统计(self):
        """测试获取统计信息"""
        缓存 = 智能缓存()
        图像 = np.zeros((64, 64, 3), dtype=np.uint8)
        
        # 存储并获取
        缓存.存储(图像, [])
        缓存.获取(图像)
        
        统计 = 缓存.获取统计()
        assert "总请求数" in 统计
        assert "命中率" in 统计
        assert 统计["有缓存"] == True
    
    def test_设置相似度阈值(self):
        """测试设置相似度阈值"""
        缓存 = 智能缓存()
        
        缓存.设置相似度阈值(0.8)
        assert 缓存.策略.全局阈值 == 0.8
        
        # 无效值应被忽略
        缓存.设置相似度阈值(1.5)
        assert 缓存.策略.全局阈值 == 0.8
    
    def test_设置过期时间(self):
        """测试设置过期时间"""
        缓存 = 智能缓存()
        
        缓存.设置过期时间(1.0)
        assert 缓存.策略.过期时间 == 1.0
        
        # 负值应被忽略
        缓存.设置过期时间(-1.0)
        assert 缓存.策略.过期时间 == 1.0
    
    def test_启用禁用时间过期(self):
        """测试启用/禁用时间过期"""
        缓存 = 智能缓存()
        
        assert 缓存.策略.启用时间过期 == True
        
        缓存.禁用时间过期()
        assert 缓存.策略.启用时间过期 == False
        
        缓存.启用时间过期(True)
        assert 缓存.策略.启用时间过期 == True
    
    def test_获取过期信息(self):
        """测试获取过期信息"""
        缓存 = 智能缓存(过期时间=0.5)
        图像 = np.zeros((64, 64, 3), dtype=np.uint8)
        
        # 无缓存时
        信息 = 缓存.获取过期信息()
        assert 信息["有缓存"] == False
        
        # 有缓存时
        缓存.存储(图像, [])
        信息 = 缓存.获取过期信息()
        assert 信息["有缓存"] == True
        assert "缓存年龄" in 信息
        assert "剩余时间" in 信息
    
    def test_检查并处理过期(self):
        """测试检查并处理过期"""
        缓存 = 智能缓存(过期时间=0.05)
        图像 = np.zeros((64, 64, 3), dtype=np.uint8)
        
        缓存.存储(图像, [])
        
        # 刚存储时不应过期
        assert not 缓存.检查并处理过期()
        assert 缓存.是否有缓存()
        
        # 等待过期
        time.sleep(0.07)
        
        # 应该过期并清空
        assert 缓存.检查并处理过期()
        assert not 缓存.是否有缓存()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
