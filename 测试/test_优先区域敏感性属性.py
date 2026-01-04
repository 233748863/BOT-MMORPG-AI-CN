"""
优先区域敏感性属性测试

属性 2: 优先区域敏感性
*对于任意* 优先区域显著变化的帧，即使全局相似度高也应触发新检测

验证: 需求 3.2
"""

import pytest
from hypothesis import given, strategies as st, settings, assume

# 导入被测试的模块
from 核心.缓存策略 import 缓存策略, 优先区域


# ==================== 策略定义 ====================

@st.composite
def 有效相似度(draw):
    """生成有效的相似度值 (0.0-1.0)"""
    return draw(st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False))


@st.composite
def 高相似度(draw, 最小值=0.95):
    """生成高相似度值"""
    return draw(st.floats(min_value=最小值, max_value=1.0, allow_nan=False, allow_infinity=False))


@st.composite
def 低相似度(draw, 最大值=0.85):
    """生成低相似度值"""
    return draw(st.floats(min_value=0.0, max_value=最大值, allow_nan=False, allow_infinity=False))


@st.composite
def 有效区域坐标(draw):
    """生成有效的相对区域坐标"""
    x = draw(st.floats(min_value=0.0, max_value=0.7, allow_nan=False, allow_infinity=False))
    y = draw(st.floats(min_value=0.0, max_value=0.7, allow_nan=False, allow_infinity=False))
    w = draw(st.floats(min_value=0.1, max_value=min(0.3, 1.0 - x), allow_nan=False, allow_infinity=False))
    h = draw(st.floats(min_value=0.1, max_value=min(0.3, 1.0 - y), allow_nan=False, allow_infinity=False))
    return (x, y, w, h)


@st.composite
def 有效阈值(draw, 最小值=0.5, 最大值=0.99):
    """生成有效的阈值"""
    return draw(st.floats(min_value=最小值, max_value=最大值, allow_nan=False, allow_infinity=False))


@st.composite
def 缓存策略配置(draw):
    """生成有效的缓存策略配置"""
    全局阈值 = draw(st.floats(min_value=0.8, max_value=0.99, allow_nan=False, allow_infinity=False))
    过期时间 = draw(st.floats(min_value=0.1, max_value=2.0, allow_nan=False, allow_infinity=False))
    return 全局阈值, 过期时间


class Test优先区域敏感性属性:
    """
    属性测试: 优先区域敏感性
    
    Feature: detection-cache-optimization, Property 2: 优先区域敏感性
    Validates: Requirements 3.2
    """
    
    @settings(max_examples=100, deadline=5000)
    @given(
        全局相似度=高相似度(最小值=0.96),
        区域相似度=低相似度(最大值=0.85),
        区域阈值=有效阈值(最小值=0.88, 最大值=0.95)
    )
    def test_优先区域变化触发新检测(self, 全局相似度: float, 区域相似度: float, 区域阈值: float):
        """
        属性测试: 当优先区域显著变化时，即使全局相似度高也应触发新检测
        
        Feature: detection-cache-optimization, Property 2: 优先区域敏感性
        Validates: Requirements 3.2
        """
        # 确保区域相似度低于区域阈值
        assume(区域相似度 < 区域阈值)
        
        策略 = 缓存策略(全局阈值=0.95, 过期时间=1.0)
        策略.添加优先区域("测试区域", (0.3, 0.3, 0.4, 0.4), 区域阈值)
        
        # 全局相似度高，但优先区域相似度低
        应该使用缓存 = 策略.应该使用缓存(全局相似度, [区域相似度], 0.1)
        
        # 应该不使用缓存（触发新检测）
        assert not 应该使用缓存, \
            f"优先区域变化显著时应触发新检测: 全局={全局相似度:.3f}, 区域={区域相似度:.3f}, 阈值={区域阈值:.3f}"
    
    @settings(max_examples=100, deadline=5000)
    @given(
        全局相似度=高相似度(最小值=0.96),
        区域相似度=高相似度(最小值=0.92)
    )
    def test_优先区域稳定时使用缓存(self, 全局相似度: float, 区域相似度: float):
        """
        属性测试: 当全局和优先区域都稳定时应使用缓存
        
        Feature: detection-cache-optimization, Property 2: 优先区域敏感性
        Validates: Requirements 3.2
        """
        策略 = 缓存策略(全局阈值=0.95, 过期时间=1.0)
        策略.添加优先区域("测试区域", (0.3, 0.3, 0.4, 0.4), 0.9)
        
        # 确保区域相似度高于区域阈值
        assume(区域相似度 >= 0.9)
        
        应该使用缓存 = 策略.应该使用缓存(全局相似度, [区域相似度], 0.1)
        
        assert 应该使用缓存, \
            f"全局和区域都稳定时应使用缓存: 全局={全局相似度:.3f}, 区域={区域相似度:.3f}"
    
    @settings(max_examples=100, deadline=5000)
    @given(
        区域数量=st.integers(min_value=1, max_value=5),
        变化区域索引=st.integers(min_value=0, max_value=4)
    )
    def test_任一优先区域变化触发新检测(self, 区域数量: int, 变化区域索引: int):
        """
        属性测试: 任何一个优先区域变化都应触发新检测
        
        Feature: detection-cache-optimization, Property 2: 优先区域敏感性
        Validates: Requirements 3.2
        """
        assume(变化区域索引 < 区域数量)
        
        策略 = 缓存策略(全局阈值=0.95, 过期时间=1.0)
        
        # 添加多个优先区域
        for i in range(区域数量):
            x = 0.1 * i
            策略.添加优先区域(f"区域{i}", (x, 0.1, 0.1, 0.1), 0.9)
        
        # 创建区域相似度列表，只有一个区域变化
        区域相似度列表 = [0.95] * 区域数量  # 所有区域都稳定
        区域相似度列表[变化区域索引] = 0.8  # 一个区域变化
        
        应该使用缓存 = 策略.应该使用缓存(0.98, 区域相似度列表, 0.1)
        
        assert not 应该使用缓存, \
            f"任一优先区域变化应触发新检测: 变化区域索引={变化区域索引}"
    
    @settings(max_examples=100, deadline=5000)
    @given(区域阈值=有效阈值(最小值=0.7, 最大值=0.95))
    def test_区域阈值生效(self, 区域阈值: float):
        """
        属性测试: 不同区域可以有不同的阈值
        
        Feature: detection-cache-optimization, Property 2: 优先区域敏感性
        Validates: Requirements 3.3
        """
        策略 = 缓存策略(全局阈值=0.95, 过期时间=1.0)
        策略.添加优先区域("测试区域", (0.3, 0.3, 0.4, 0.4), 区域阈值)
        
        # 相似度刚好低于阈值
        低于阈值相似度 = 区域阈值 - 0.05
        应该使用缓存_低 = 策略.应该使用缓存(0.98, [低于阈值相似度], 0.1)
        
        # 相似度刚好高于阈值
        高于阈值相似度 = min(区域阈值 + 0.03, 1.0)
        应该使用缓存_高 = 策略.应该使用缓存(0.98, [高于阈值相似度], 0.1)
        
        assert not 应该使用缓存_低, f"低于阈值时不应使用缓存: {低于阈值相似度:.3f} < {区域阈值:.3f}"
        assert 应该使用缓存_高, f"高于阈值时应使用缓存: {高于阈值相似度:.3f} >= {区域阈值:.3f}"


class Test缓存策略基本属性:
    """
    缓存策略基本属性测试
    
    Feature: detection-cache-optimization
    Validates: Requirements 2.1, 2.2, 2.3
    """
    
    @settings(max_examples=100, deadline=5000)
    @given(
        全局阈值=有效阈值(最小值=0.8, 最大值=0.99),
        相似度=有效相似度()
    )
    def test_全局阈值判断正确(self, 全局阈值: float, 相似度: float):
        """
        属性测试: 全局相似度阈值判断正确
        
        Feature: detection-cache-optimization
        Validates: Requirements 2.1, 2.2
        """
        策略 = 缓存策略(全局阈值=全局阈值, 过期时间=10.0, 启用时间过期=False)
        
        应该使用缓存 = 策略.应该使用缓存(相似度, [], 0.0)
        
        if 相似度 >= 全局阈值:
            assert 应该使用缓存, f"相似度 {相似度:.3f} >= 阈值 {全局阈值:.3f} 时应使用缓存"
        else:
            assert not 应该使用缓存, f"相似度 {相似度:.3f} < 阈值 {全局阈值:.3f} 时不应使用缓存"
    
    @settings(max_examples=100, deadline=5000)
    @given(
        过期时间=st.floats(min_value=0.1, max_value=2.0, allow_nan=False, allow_infinity=False),
        缓存年龄=st.floats(min_value=0.0, max_value=3.0, allow_nan=False, allow_infinity=False)
    )
    def test_时间过期判断正确(self, 过期时间: float, 缓存年龄: float):
        """
        属性测试: 时间过期判断正确
        
        Feature: detection-cache-optimization
        Validates: Requirements 4.1, 4.2
        """
        策略 = 缓存策略(全局阈值=0.5, 过期时间=过期时间, 启用时间过期=True)
        
        应该使用缓存 = 策略.应该使用缓存(0.99, [], 缓存年龄)
        
        if 缓存年龄 > 过期时间:
            assert not 应该使用缓存, f"缓存年龄 {缓存年龄:.3f} > 过期时间 {过期时间:.3f} 时不应使用缓存"
        else:
            assert 应该使用缓存, f"缓存年龄 {缓存年龄:.3f} <= 过期时间 {过期时间:.3f} 时应使用缓存"
    
    @settings(max_examples=100, deadline=5000)
    @given(缓存年龄=st.floats(min_value=0.0, max_value=10.0, allow_nan=False, allow_infinity=False))
    def test_禁用时间过期(self, 缓存年龄: float):
        """
        属性测试: 禁用时间过期时不检查缓存年龄
        
        Feature: detection-cache-optimization
        Validates: Requirements 4.3
        """
        策略 = 缓存策略(全局阈值=0.5, 过期时间=0.1, 启用时间过期=False)
        
        # 即使缓存年龄很大，禁用时间过期后也应该使用缓存
        应该使用缓存 = 策略.应该使用缓存(0.99, [], 缓存年龄)
        
        assert 应该使用缓存, f"禁用时间过期时应忽略缓存年龄 {缓存年龄:.3f}"


class Test优先区域数据类属性:
    """
    优先区域数据类属性测试
    
    Feature: detection-cache-optimization
    Validates: Requirements 3.1
    """
    
    @settings(max_examples=100, deadline=5000)
    @given(
        区域=有效区域坐标(),
        图像宽度=st.integers(min_value=100, max_value=1920),
        图像高度=st.integers(min_value=100, max_value=1080)
    )
    def test_像素坐标转换正确(self, 区域: tuple, 图像宽度: int, 图像高度: int):
        """
        属性测试: 相对坐标到像素坐标转换正确
        
        Feature: detection-cache-optimization
        Validates: Requirements 3.1
        """
        优先 = 优先区域(名称="测试", 区域=区域, 阈值=0.9)
        
        像素坐标 = 优先.转换为像素坐标(图像宽度, 图像高度)
        px, py, pw, ph = 像素坐标
        
        # 验证像素坐标在有效范围内
        assert 0 <= px < 图像宽度, f"x坐标 {px} 超出范围 [0, {图像宽度})"
        assert 0 <= py < 图像高度, f"y坐标 {py} 超出范围 [0, {图像高度})"
        assert pw > 0, f"宽度 {pw} 必须为正"
        assert ph > 0, f"高度 {ph} 必须为正"
    
    @settings(max_examples=100, deadline=5000)
    @given(阈值=有效阈值())
    def test_优先区域阈值有效(self, 阈值: float):
        """
        属性测试: 优先区域阈值在有效范围内
        
        Feature: detection-cache-optimization
        Validates: Requirements 3.1
        """
        优先 = 优先区域(名称="测试", 区域=(0.1, 0.1, 0.3, 0.3), 阈值=阈值)
        
        assert 0.0 <= 优先.阈值 <= 1.0, f"阈值 {优先.阈值} 超出有效范围"


class Test缓存策略单元测试:
    """缓存策略单元测试"""
    
    def test_默认初始化(self):
        """测试默认初始化"""
        策略 = 缓存策略()
        
        assert 策略.全局阈值 == 0.95
        assert 策略.过期时间 == 0.5
        assert 策略.启用时间过期 == True
        assert 策略.比较方法 == "histogram"
        assert len(策略.优先区域列表) == 0
    
    def test_添加移除优先区域(self):
        """测试添加和移除优先区域"""
        策略 = 缓存策略()
        
        策略.添加优先区域("区域1", (0.1, 0.1, 0.2, 0.2), 0.9)
        assert len(策略.优先区域列表) == 1
        
        策略.添加优先区域("区域2", (0.5, 0.5, 0.2, 0.2), 0.85)
        assert len(策略.优先区域列表) == 2
        
        策略.移除优先区域("区域1")
        assert len(策略.优先区域列表) == 1
        assert 策略.优先区域列表[0].名称 == "区域2"
    
    def test_清空优先区域(self):
        """测试清空优先区域"""
        策略 = 缓存策略()
        策略.添加优先区域("区域1", (0.1, 0.1, 0.2, 0.2), 0.9)
        策略.添加优先区域("区域2", (0.5, 0.5, 0.2, 0.2), 0.85)
        
        策略.清空优先区域()
        assert len(策略.优先区域列表) == 0
    
    def test_获取失效原因(self):
        """测试获取失效原因"""
        策略 = 缓存策略(全局阈值=0.95, 过期时间=0.5)
        策略.添加优先区域("中心", (0.3, 0.3, 0.4, 0.4), 0.9)
        
        # 时间过期
        原因 = 策略.获取失效原因(0.98, [0.95], 0.6)
        assert "时间过期" in 原因
        
        # 全局相似度不足
        原因 = 策略.获取失效原因(0.90, [0.95], 0.1)
        assert "全局相似度不足" in 原因
        
        # 优先区域变化
        原因 = 策略.获取失效原因(0.98, [0.85], 0.1)
        assert "优先区域" in 原因
        
        # 无失效原因
        原因 = 策略.获取失效原因(0.98, [0.95], 0.1)
        assert 原因 == ""
    
    def test_序列化反序列化(self):
        """测试序列化和反序列化"""
        策略 = 缓存策略(全局阈值=0.9, 过期时间=1.0)
        策略.添加优先区域("测试", (0.2, 0.2, 0.3, 0.3), 0.85)
        
        字典 = 策略.to_dict()
        恢复策略 = 缓存策略.from_dict(字典)
        
        assert 恢复策略.全局阈值 == 策略.全局阈值
        assert 恢复策略.过期时间 == 策略.过期时间
        assert len(恢复策略.优先区域列表) == 1
        assert 恢复策略.优先区域列表[0].名称 == "测试"
    
    def test_无效参数自动修正(self):
        """测试无效参数自动修正"""
        # 无效全局阈值
        策略 = 缓存策略(全局阈值=1.5)
        assert 策略.全局阈值 == 0.95
        
        # 无效过期时间
        策略 = 缓存策略(过期时间=-1.0)
        assert 策略.过期时间 == 0.5
        
        # 无效比较方法
        策略 = 缓存策略(比较方法="invalid")
        assert 策略.比较方法 == "histogram"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
