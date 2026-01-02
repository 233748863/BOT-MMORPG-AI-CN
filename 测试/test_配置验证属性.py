# -*- coding: utf-8 -*-
"""
配置验证属性测试模块

使用Hypothesis进行属性测试，验证配置验证逻辑。

**Property 7: 配置验证逻辑**
*对于任意* 配置项输入，验证函数应正确判断输入有效性；
对于无效输入，应阻止保存并显示错误提示

**Validates: Requirements 5.5, 5.7**
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck

# 检查PySide6是否可用
try:
    from PySide6.QtWidgets import QApplication
    PYSIDE6_AVAILABLE = True
except ImportError:
    PYSIDE6_AVAILABLE = False

# 如果PySide6不可用，跳过所有测试
pytestmark = pytest.mark.skipif(
    not PYSIDE6_AVAILABLE,
    reason="PySide6未安装，跳过GUI测试"
)


@pytest.fixture(scope="module")
def 应用实例():
    """创建QApplication实例（整个模块共享）"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def 配置页(应用实例):
    """创建配置页实例"""
    from 界面.页面.配置页 import 配置页
    页面 = 配置页()
    yield 页面
    页面.close()


# 定义有效配置值的策略
有效游戏窗口左边界 = st.integers(min_value=0, max_value=1000)
有效游戏窗口上边界 = st.integers(min_value=0, max_value=500)
有效游戏窗口右边界 = st.integers(min_value=1000, max_value=3840)
有效游戏窗口下边界 = st.integers(min_value=600, max_value=2160)
有效游戏宽度 = st.integers(min_value=640, max_value=3840)
有效游戏高度 = st.integers(min_value=480, max_value=2160)
有效模型输入宽度 = st.integers(min_value=120, max_value=960)
有效模型输入高度 = st.integers(min_value=68, max_value=540)
有效学习率 = st.floats(min_value=0.0001, max_value=0.01)
有效训练轮数 = st.integers(min_value=1, max_value=100)
有效每文件样本数 = st.integers(min_value=100, max_value=5000)
有效运动检测阈值 = st.integers(min_value=100, max_value=5000)
有效规则权重 = st.floats(min_value=0.0, max_value=1.0)
有效帧率阈值 = st.integers(min_value=5, max_value=60)
有效YOLO置信度 = st.floats(min_value=0.1, max_value=0.9)
有效YOLO检测间隔 = st.integers(min_value=1, max_value=10)
非空路径 = st.text(min_size=1, max_size=50).filter(lambda x: x.strip() != "")


class Test配置验证属性测试:
    """
    配置验证属性测试类
    
    **Feature: modern-ui, Property 7: 配置验证逻辑**
    **Validates: Requirements 5.5, 5.7**
    """
    
    @given(
        左边界=有效游戏窗口左边界,
        上边界=有效游戏窗口上边界,
        右边界=有效游戏窗口右边界,
        下边界=有效游戏窗口下边界,
    )
    @settings(max_examples=100, deadline=None)
    def test_有效游戏窗口边界应通过验证(self, 应用实例, 左边界, 上边界, 右边界, 下边界):
        """
        属性测试: 对于任意有效的游戏窗口边界配置，验证应通过
        
        **Feature: modern-ui, Property 7: 配置验证逻辑**
        **Validates: Requirements 5.5**
        """
        # 确保边界关系有效
        assume(左边界 < 右边界)
        assume(上边界 < 下边界)
        assume(右边界 - 左边界 >= 640)  # 最小宽度
        assume(下边界 - 上边界 >= 480)  # 最小高度
        
        from 界面.页面.配置页 import 配置页
        页面 = 配置页()
        
        try:
            # 设置配置值
            页面._配置控件["游戏窗口_左"].setValue(左边界)
            页面._配置控件["游戏窗口_上"].setValue(上边界)
            页面._配置控件["游戏窗口_右"].setValue(右边界)
            页面._配置控件["游戏窗口_下"].setValue(下边界)
            
            # 执行验证
            有效, 错误列表 = 页面._验证配置()
            
            # 验证: 有效配置应通过验证（不包含窗口边界相关错误）
            窗口相关错误 = [e for e in 错误列表 if "游戏窗口" in e]
            assert len(窗口相关错误) == 0, \
                f"有效的游戏窗口配置不应产生错误，但得到: {窗口相关错误}"
        finally:
            页面.close()
    
    @given(
        左边界=st.integers(min_value=1000, max_value=2000),
        右边界=st.integers(min_value=0, max_value=999),
    )
    @settings(max_examples=100, deadline=None)
    def test_无效游戏窗口边界_左大于右_应失败(self, 应用实例, 左边界, 右边界):
        """
        属性测试: 当左边界大于等于右边界时，验证应失败
        
        **Feature: modern-ui, Property 7: 配置验证逻辑**
        **Validates: Requirements 5.7**
        """
        assume(左边界 >= 右边界)
        
        from 界面.页面.配置页 import 配置页
        页面 = 配置页()
        
        try:
            # 设置无效配置
            页面._配置控件["游戏窗口_左"].setValue(左边界)
            页面._配置控件["游戏窗口_右"].setValue(右边界)
            
            # 执行验证
            有效, 错误列表 = 页面._验证配置()
            
            # 验证: 应包含左边界相关错误
            assert any("左边界必须小于右边界" in e for e in 错误列表), \
                f"左边界({左边界})>=右边界({右边界})时应报错，但错误列表为: {错误列表}"
        finally:
            页面.close()
    
    @given(
        上边界=st.integers(min_value=1000, max_value=2000),
        下边界=st.integers(min_value=0, max_value=999),
    )
    @settings(max_examples=100, deadline=None)
    def test_无效游戏窗口边界_上大于下_应失败(self, 应用实例, 上边界, 下边界):
        """
        属性测试: 当上边界大于等于下边界时，验证应失败
        
        **Feature: modern-ui, Property 7: 配置验证逻辑**
        **Validates: Requirements 5.7**
        """
        assume(上边界 >= 下边界)
        
        from 界面.页面.配置页 import 配置页
        页面 = 配置页()
        
        try:
            # 设置无效配置
            页面._配置控件["游戏窗口_上"].setValue(上边界)
            页面._配置控件["游戏窗口_下"].setValue(下边界)
            
            # 执行验证
            有效, 错误列表 = 页面._验证配置()
            
            # 验证: 应包含上边界相关错误
            assert any("上边界必须小于下边界" in e for e in 错误列表), \
                f"上边界({上边界})>=下边界({下边界})时应报错，但错误列表为: {错误列表}"
        finally:
            页面.close()
    
    @given(
        模型宽度=st.integers(min_value=500, max_value=960),
        游戏宽度=st.integers(min_value=640, max_value=960),
    )
    @settings(max_examples=100, deadline=None)
    def test_模型输入宽度大于游戏宽度_应失败(self, 应用实例, 模型宽度, 游戏宽度):
        """
        属性测试: 当模型输入宽度大于游戏宽度时，验证应失败
        
        **Feature: modern-ui, Property 7: 配置验证逻辑**
        **Validates: Requirements 5.7**
        """
        assume(模型宽度 > 游戏宽度)
        
        from 界面.页面.配置页 import 配置页
        页面 = 配置页()
        
        try:
            # 设置无效配置
            页面._配置控件["模型输入宽度"].setValue(模型宽度)
            页面._配置控件["游戏宽度"].setValue(游戏宽度)
            
            # 执行验证
            有效, 错误列表 = 页面._验证配置()
            
            # 验证: 应包含模型宽度相关错误
            assert any("模型输入宽度不能大于游戏宽度" in e for e in 错误列表), \
                f"模型宽度({模型宽度})>游戏宽度({游戏宽度})时应报错，但错误列表为: {错误列表}"
        finally:
            页面.close()
    
    @given(
        游戏高度=st.integers(min_value=480, max_value=539),
        高度差=st.integers(min_value=1, max_value=60),
    )
    @settings(max_examples=100, deadline=None)
    def test_模型输入高度大于游戏高度_应失败(self, 应用实例, 游戏高度, 高度差):
        """
        属性测试: 当模型输入高度大于游戏高度时，验证应失败
        
        **Feature: modern-ui, Property 7: 配置验证逻辑**
        **Validates: Requirements 5.7**
        
        注意: 游戏高度控件范围是480-2160，模型输入高度控件范围是68-540
        所以我们需要确保游戏高度在480-539之间，模型高度在481-540之间
        """
        模型高度 = min(游戏高度 + 高度差, 540)  # 确保模型高度不超过控件最大值540
        assume(模型高度 > 游戏高度)  # 确保模型高度确实大于游戏高度
        
        from 界面.页面.配置页 import 配置页
        页面 = 配置页()
        
        try:
            # 设置无效配置
            页面._配置控件["模型输入高度"].setValue(模型高度)
            页面._配置控件["游戏高度"].setValue(游戏高度)
            
            # 执行验证
            有效, 错误列表 = 页面._验证配置()
            
            # 验证: 应包含模型高度相关错误
            assert any("模型输入高度不能大于游戏高度" in e for e in 错误列表), \
                f"模型高度({模型高度})>游戏高度({游戏高度})时应报错，但错误列表为: {错误列表}"
        finally:
            页面.close()
    
    def test_空模型保存路径_应失败(self, 应用实例):
        """
        测试: 空的模型保存路径应验证失败
        
        **Feature: modern-ui, Property 7: 配置验证逻辑**
        **Validates: Requirements 5.7**
        """
        from 界面.页面.配置页 import 配置页
        页面 = 配置页()
        
        try:
            # 设置空路径
            页面._配置控件["模型保存路径"].setText("")
            
            # 执行验证
            有效, 错误列表 = 页面._验证配置()
            
            # 验证: 应包含路径相关错误
            assert any("模型保存路径不能为空" in e for e in 错误列表), \
                f"空模型保存路径应报错，但错误列表为: {错误列表}"
        finally:
            页面.close()
    
    def test_空数据保存路径_应失败(self, 应用实例):
        """
        测试: 空的数据保存路径应验证失败
        
        **Feature: modern-ui, Property 7: 配置验证逻辑**
        **Validates: Requirements 5.7**
        """
        from 界面.页面.配置页 import 配置页
        页面 = 配置页()
        
        try:
            # 设置空路径
            页面._配置控件["数据保存路径"].setText("")
            
            # 执行验证
            有效, 错误列表 = 页面._验证配置()
            
            # 验证: 应包含路径相关错误
            assert any("数据保存路径不能为空" in e for e in 错误列表), \
                f"空数据保存路径应报错，但错误列表为: {错误列表}"
        finally:
            页面.close()
    
    @given(
        模型宽度=有效模型输入宽度,
        模型高度=有效模型输入高度,
        游戏宽度=有效游戏宽度,
        游戏高度=有效游戏高度,
    )
    @settings(max_examples=100, deadline=None)
    def test_有效模型尺寸配置应通过验证(self, 应用实例, 模型宽度, 模型高度, 游戏宽度, 游戏高度):
        """
        属性测试: 对于任意有效的模型尺寸配置，验证应通过
        
        **Feature: modern-ui, Property 7: 配置验证逻辑**
        **Validates: Requirements 5.5**
        """
        # 确保模型尺寸不超过游戏尺寸
        assume(模型宽度 <= 游戏宽度)
        assume(模型高度 <= 游戏高度)
        
        from 界面.页面.配置页 import 配置页
        页面 = 配置页()
        
        try:
            # 设置配置值
            页面._配置控件["模型输入宽度"].setValue(模型宽度)
            页面._配置控件["模型输入高度"].setValue(模型高度)
            页面._配置控件["游戏宽度"].setValue(游戏宽度)
            页面._配置控件["游戏高度"].setValue(游戏高度)
            
            # 执行验证
            有效, 错误列表 = 页面._验证配置()
            
            # 验证: 不应包含模型尺寸相关错误
            模型相关错误 = [e for e in 错误列表 if "模型输入" in e]
            assert len(模型相关错误) == 0, \
                f"有效的模型尺寸配置不应产生错误，但得到: {模型相关错误}"
        finally:
            页面.close()
    
    @given(规则权重=有效规则权重)
    @settings(max_examples=100, deadline=None)
    def test_有效规则权重应通过验证(self, 应用实例, 规则权重):
        """
        属性测试: 对于任意有效的规则权重(0-1)，验证应通过
        
        **Feature: modern-ui, Property 7: 配置验证逻辑**
        **Validates: Requirements 5.5**
        """
        from 界面.页面.配置页 import 配置页
        页面 = 配置页()
        
        try:
            # 设置配置值 (滑块值为0-100)
            页面._配置控件["规则权重"].setValue(int(规则权重 * 100))
            
            # 执行验证
            有效, 错误列表 = 页面._验证配置()
            
            # 验证: 不应包含规则权重相关错误
            权重相关错误 = [e for e in 错误列表 if "规则权重" in e]
            assert len(权重相关错误) == 0, \
                f"有效的规则权重({规则权重})不应产生错误，但得到: {权重相关错误}"
        finally:
            页面.close()
    
    @given(
        左边界=st.integers(min_value=0, max_value=500),
        右边界=st.integers(min_value=501, max_value=1000),
    )
    @settings(max_examples=100, deadline=None)
    def test_窗口宽度小于640_应失败(self, 应用实例, 左边界, 右边界):
        """
        属性测试: 当窗口宽度小于640像素时，验证应失败
        
        **Feature: modern-ui, Property 7: 配置验证逻辑**
        **Validates: Requirements 5.7**
        """
        assume(左边界 < 右边界)
        assume(右边界 - 左边界 < 640)
        
        from 界面.页面.配置页 import 配置页
        页面 = 配置页()
        
        try:
            # 设置配置值
            页面._配置控件["游戏窗口_左"].setValue(左边界)
            页面._配置控件["游戏窗口_右"].setValue(右边界)
            
            # 执行验证
            有效, 错误列表 = 页面._验证配置()
            
            # 验证: 应包含宽度相关错误
            assert any("宽度不能小于640" in e for e in 错误列表), \
                f"窗口宽度({右边界 - 左边界})小于640时应报错，但错误列表为: {错误列表}"
        finally:
            页面.close()
    
    @given(
        上边界=st.integers(min_value=0, max_value=300),
        下边界=st.integers(min_value=301, max_value=700),
    )
    @settings(max_examples=100, deadline=None)
    def test_窗口高度小于480_应失败(self, 应用实例, 上边界, 下边界):
        """
        属性测试: 当窗口高度小于480像素时，验证应失败
        
        **Feature: modern-ui, Property 7: 配置验证逻辑**
        **Validates: Requirements 5.7**
        """
        assume(上边界 < 下边界)
        assume(下边界 - 上边界 < 480)
        
        from 界面.页面.配置页 import 配置页
        页面 = 配置页()
        
        try:
            # 设置配置值
            页面._配置控件["游戏窗口_上"].setValue(上边界)
            页面._配置控件["游戏窗口_下"].setValue(下边界)
            
            # 执行验证
            有效, 错误列表 = 页面._验证配置()
            
            # 验证: 应包含高度相关错误
            assert any("高度不能小于480" in e for e in 错误列表), \
                f"窗口高度({下边界 - 上边界})小于480时应报错，但错误列表为: {错误列表}"
        finally:
            页面.close()
    
    @given(路径=非空路径)
    @settings(max_examples=100, deadline=None)
    def test_非空路径应通过验证(self, 应用实例, 路径):
        """
        属性测试: 对于任意非空路径，路径验证应通过
        
        **Feature: modern-ui, Property 7: 配置验证逻辑**
        **Validates: Requirements 5.5**
        """
        from 界面.页面.配置页 import 配置页
        页面 = 配置页()
        
        try:
            # 设置非空路径
            页面._配置控件["模型保存路径"].setText(路径)
            页面._配置控件["数据保存路径"].setText(路径)
            
            # 执行验证
            有效, 错误列表 = 页面._验证配置()
            
            # 验证: 不应包含路径为空的错误
            路径相关错误 = [e for e in 错误列表 if "路径不能为空" in e]
            assert len(路径相关错误) == 0, \
                f"非空路径'{路径}'不应产生路径为空错误，但得到: {路径相关错误}"
        finally:
            页面.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
