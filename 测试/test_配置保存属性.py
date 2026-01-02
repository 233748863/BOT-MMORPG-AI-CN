# -*- coding: utf-8 -*-
"""
配置保存属性测试模块

使用Hypothesis进行属性测试，验证配置保存一致性。

**Property 8: 配置保存一致性**
*对于任意* 有效的配置修改，保存后配置文件内容应与用户输入一致

**Validates: Requirements 5.6**
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


# 定义有效配置值的策略
# 游戏窗口配置 - 确保边界关系有效
有效游戏窗口左边界 = st.integers(min_value=0, max_value=500)
有效游戏窗口上边界 = st.integers(min_value=0, max_value=300)
有效游戏窗口右边界 = st.integers(min_value=1200, max_value=1920)
有效游戏窗口下边界 = st.integers(min_value=800, max_value=1200)
有效游戏宽度 = st.integers(min_value=800, max_value=1920)
有效游戏高度 = st.integers(min_value=600, max_value=1080)

# 模型配置
有效模型输入宽度 = st.integers(min_value=120, max_value=480)
有效模型输入高度 = st.integers(min_value=68, max_value=270)

# 训练配置
有效学习率 = st.floats(min_value=0.0001, max_value=0.01, allow_nan=False, allow_infinity=False)
有效训练轮数 = st.integers(min_value=1, max_value=100)
有效每文件样本数 = st.integers(min_value=100, max_value=5000)
有效运动检测阈值 = st.integers(min_value=100, max_value=5000)

# 增强模块配置
有效YOLO置信度 = st.integers(min_value=10, max_value=90)  # 滑块值 10-90
有效YOLO检测间隔 = st.integers(min_value=1, max_value=10)
有效规则权重 = st.integers(min_value=0, max_value=100)  # 滑块值 0-100
有效帧率阈值 = st.integers(min_value=5, max_value=60)
有效决策策略 = st.integers(min_value=0, max_value=2)  # 0=规则优先, 1=模型优先, 2=混合加权

# 布尔值
布尔值 = st.booleans()

# 非空路径
非空路径 = st.text(
    alphabet=st.characters(whitelist_categories=('L', 'N'), whitelist_characters='/_-'),
    min_size=3,
    max_size=30
).filter(lambda x: x.strip() != "" and not x.startswith('/'))


class Test配置保存属性测试:
    """
    配置保存属性测试类
    
    **Feature: modern-ui, Property 8: 配置保存一致性**
    **Validates: Requirements 5.6**
    """
    
    @given(
        左边界=有效游戏窗口左边界,
        上边界=有效游戏窗口上边界,
        右边界=有效游戏窗口右边界,
        下边界=有效游戏窗口下边界,
    )
    @settings(max_examples=100, deadline=None)
    def test_游戏窗口配置保存一致性(self, 应用实例, 左边界, 上边界, 右边界, 下边界):
        """
        属性测试: 对于任意有效的游戏窗口配置，保存后重新加载应与原始输入一致
        
        **Feature: modern-ui, Property 8: 配置保存一致性**
        **Validates: Requirements 5.6**
        """
        # 确保边界关系有效
        assume(左边界 < 右边界)
        assume(上边界 < 下边界)
        assume(右边界 - 左边界 >= 640)
        assume(下边界 - 上边界 >= 480)
        
        from 界面.页面.配置页 import 配置页
        页面 = 配置页()
        
        try:
            # 设置配置值
            页面._配置控件["游戏窗口_左"].setValue(左边界)
            页面._配置控件["游戏窗口_上"].setValue(上边界)
            页面._配置控件["游戏窗口_右"].setValue(右边界)
            页面._配置控件["游戏窗口_下"].setValue(下边界)
            
            # 获取当前配置
            原始配置 = 页面._获取当前配置()
            
            # 生成设置文件内容
            设置内容 = 页面._生成设置文件内容(原始配置)
            
            # 验证生成的内容包含正确的值
            assert f"游戏窗口区域 = ({左边界}, {上边界}, {右边界}, {下边界})" in 设置内容, \
                f"生成的设置文件应包含正确的游戏窗口区域"
            
        finally:
            页面.close()
    
    @given(
        模型宽度=有效模型输入宽度,
        模型高度=有效模型输入高度,
        游戏宽度=有效游戏宽度,
        游戏高度=有效游戏高度,
    )
    @settings(max_examples=100, deadline=None)
    def test_模型尺寸配置保存一致性(self, 应用实例, 模型宽度, 模型高度, 游戏宽度, 游戏高度):
        """
        属性测试: 对于任意有效的模型尺寸配置，保存后应与原始输入一致
        
        **Feature: modern-ui, Property 8: 配置保存一致性**
        **Validates: Requirements 5.6**
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
            
            # 获取当前配置
            原始配置 = 页面._获取当前配置()
            
            # 生成设置文件内容
            设置内容 = 页面._生成设置文件内容(原始配置)
            
            # 验证生成的内容包含正确的值
            assert f"模型输入宽度 = {模型宽度}" in 设置内容, \
                f"生成的设置文件应包含正确的模型输入宽度"
            assert f"模型输入高度 = {模型高度}" in 设置内容, \
                f"生成的设置文件应包含正确的模型输入高度"
            assert f"游戏宽度 = {游戏宽度}" in 设置内容, \
                f"生成的设置文件应包含正确的游戏宽度"
            assert f"游戏高度 = {游戏高度}" in 设置内容, \
                f"生成的设置文件应包含正确的游戏高度"
            
        finally:
            页面.close()
    
    @given(
        训练轮数=有效训练轮数,
        每文件样本数=有效每文件样本数,
        运动检测阈值=有效运动检测阈值,
    )
    @settings(max_examples=100, deadline=None)
    def test_训练配置保存一致性(self, 应用实例, 训练轮数, 每文件样本数, 运动检测阈值):
        """
        属性测试: 对于任意有效的训练配置，保存后应与原始输入一致
        
        **Feature: modern-ui, Property 8: 配置保存一致性**
        **Validates: Requirements 5.6**
        """
        from 界面.页面.配置页 import 配置页
        页面 = 配置页()
        
        try:
            # 设置配置值
            页面._配置控件["训练轮数"].setValue(训练轮数)
            页面._配置控件["每文件样本数"].setValue(每文件样本数)
            页面._配置控件["运动检测阈值"].setValue(运动检测阈值)
            
            # 获取当前配置
            原始配置 = 页面._获取当前配置()
            
            # 生成设置文件内容
            设置内容 = 页面._生成设置文件内容(原始配置)
            
            # 验证生成的内容包含正确的值
            assert f"训练轮数 = {训练轮数}" in 设置内容, \
                f"生成的设置文件应包含正确的训练轮数"
            assert f"每文件样本数 = {每文件样本数}" in 设置内容, \
                f"生成的设置文件应包含正确的每文件样本数"
            assert f"运动检测阈值 = {运动检测阈值}" in 设置内容, \
                f"生成的设置文件应包含正确的运动检测阈值"
            
        finally:
            页面.close()
    
    @given(
        YOLO启用=布尔值,
        YOLO置信度=有效YOLO置信度,
        YOLO检测间隔=有效YOLO检测间隔,
    )
    @settings(max_examples=100, deadline=None)
    def test_YOLO配置保存一致性(self, 应用实例, YOLO启用, YOLO置信度, YOLO检测间隔):
        """
        属性测试: 对于任意有效的YOLO配置，保存后应与原始输入一致
        
        **Feature: modern-ui, Property 8: 配置保存一致性**
        **Validates: Requirements 5.6**
        """
        from 界面.页面.配置页 import 配置页
        页面 = 配置页()
        
        try:
            # 设置配置值
            页面._配置控件["YOLO启用"].setChecked(YOLO启用)
            页面._配置控件["YOLO置信度"].setValue(YOLO置信度)
            页面._配置控件["YOLO检测间隔"].setValue(YOLO检测间隔)
            
            # 获取当前配置
            原始配置 = 页面._获取当前配置()
            
            # 生成增强设置文件内容
            增强设置内容 = 页面._生成增强设置文件内容(原始配置)
            
            # 验证生成的内容包含正确的值
            期望置信度 = YOLO置信度 / 100  # 滑块值转换为实际值
            assert f'"置信度阈值": {期望置信度}' in 增强设置内容, \
                f"生成的增强设置文件应包含正确的YOLO置信度阈值"
            assert f'"检测间隔": {YOLO检测间隔}' in 增强设置内容, \
                f"生成的增强设置文件应包含正确的YOLO检测间隔"
            assert f'"启用": {YOLO启用}' in 增强设置内容, \
                f"生成的增强设置文件应包含正确的YOLO启用状态"
            
        finally:
            页面.close()
    
    @given(
        决策引擎启用=布尔值,
        决策策略=有效决策策略,
        规则权重=有效规则权重,
    )
    @settings(max_examples=100, deadline=None)
    def test_决策引擎配置保存一致性(self, 应用实例, 决策引擎启用, 决策策略, 规则权重):
        """
        属性测试: 对于任意有效的决策引擎配置，保存后应与原始输入一致
        
        **Feature: modern-ui, Property 8: 配置保存一致性**
        **Validates: Requirements 5.6**
        """
        from 界面.页面.配置页 import 配置页
        页面 = 配置页()
        
        try:
            # 设置配置值
            页面._配置控件["决策引擎启用"].setChecked(决策引擎启用)
            页面._配置控件["决策策略"].setCurrentIndex(决策策略)
            页面._配置控件["规则权重"].setValue(规则权重)
            
            # 获取当前配置
            原始配置 = 页面._获取当前配置()
            
            # 生成增强设置文件内容
            增强设置内容 = 页面._生成增强设置文件内容(原始配置)
            
            # 验证生成的内容包含正确的值
            期望规则权重 = 规则权重 / 100  # 滑块值转换为实际值
            策略名称列表 = ["规则优先", "模型优先", "混合加权"]
            期望策略 = 策略名称列表[决策策略]
            
            assert f'"规则权重": {期望规则权重}' in 增强设置内容, \
                f"生成的增强设置文件应包含正确的规则权重"
            assert f"决策策略枚举.{期望策略}" in 增强设置内容, \
                f"生成的增强设置文件应包含正确的决策策略"
            assert f'"启用": {决策引擎启用}' in 增强设置内容, \
                f"生成的增强设置文件应包含正确的决策引擎启用状态"
            
        finally:
            页面.close()
    
    @given(
        自动降级=布尔值,
        帧率阈值=有效帧率阈值,
    )
    @settings(max_examples=100, deadline=None)
    def test_性能配置保存一致性(self, 应用实例, 自动降级, 帧率阈值):
        """
        属性测试: 对于任意有效的性能配置，保存后应与原始输入一致
        
        **Feature: modern-ui, Property 8: 配置保存一致性**
        **Validates: Requirements 5.6**
        """
        from 界面.页面.配置页 import 配置页
        页面 = 配置页()
        
        try:
            # 设置配置值
            页面._配置控件["自动降级"].setChecked(自动降级)
            页面._配置控件["帧率阈值"].setValue(帧率阈值)
            
            # 获取当前配置
            原始配置 = 页面._获取当前配置()
            
            # 生成增强设置文件内容
            增强设置内容 = 页面._生成增强设置文件内容(原始配置)
            
            # 验证生成的内容包含正确的值
            assert f'"帧率阈值": {帧率阈值}' in 增强设置内容, \
                f"生成的增强设置文件应包含正确的帧率阈值"
            assert f'"自动降级": {自动降级}' in 增强设置内容, \
                f"生成的增强设置文件应包含正确的自动降级状态"
            
        finally:
            页面.close()
    
    @given(路径=非空路径)
    @settings(max_examples=100, deadline=None)
    def test_路径配置保存一致性(self, 应用实例, 路径):
        """
        属性测试: 对于任意有效的路径配置，保存后应与原始输入一致
        
        **Feature: modern-ui, Property 8: 配置保存一致性**
        **Validates: Requirements 5.6**
        """
        from 界面.页面.配置页 import 配置页
        页面 = 配置页()
        
        try:
            # 设置配置值
            页面._配置控件["模型保存路径"].setText(路径)
            页面._配置控件["数据保存路径"].setText(路径)
            
            # 获取当前配置
            原始配置 = 页面._获取当前配置()
            
            # 生成设置文件内容
            设置内容 = 页面._生成设置文件内容(原始配置)
            
            # 验证生成的内容包含正确的值
            assert f'模型保存路径 = "{路径}"' in 设置内容, \
                f"生成的设置文件应包含正确的模型保存路径"
            assert f'数据保存路径 = "{路径}"' in 设置内容, \
                f"生成的设置文件应包含正确的数据保存路径"
            
        finally:
            页面.close()
    
    @given(状态识别启用=布尔值)
    @settings(max_examples=100, deadline=None)
    def test_状态识别配置保存一致性(self, 应用实例, 状态识别启用):
        """
        属性测试: 对于任意有效的状态识别配置，保存后应与原始输入一致
        
        **Feature: modern-ui, Property 8: 配置保存一致性**
        **Validates: Requirements 5.6**
        """
        from 界面.页面.配置页 import 配置页
        页面 = 配置页()
        
        try:
            # 设置配置值
            页面._配置控件["状态识别启用"].setChecked(状态识别启用)
            
            # 获取当前配置
            原始配置 = 页面._获取当前配置()
            
            # 生成增强设置文件内容
            增强设置内容 = 页面._生成增强设置文件内容(原始配置)
            
            # 验证生成的内容包含正确的值
            # 状态识别配置在增强设置文件中
            assert f'"启用": {状态识别启用}' in 增强设置内容, \
                f"生成的增强设置文件应包含正确的状态识别启用状态"
            
        finally:
            页面.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
