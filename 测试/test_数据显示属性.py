# -*- coding: utf-8 -*-
"""
数据显示属性测试模块

使用Hypothesis进行属性测试，验证数据文件显示一致性。

**Property 9: 数据文件显示一致性**
*对于任意* 数据目录中的文件，Data_Manager应正确显示文件列表、
文件信息和统计数据

**Validates: Requirements 6.1, 6.2, 6.3**
"""

import sys
import os
import tempfile
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import numpy as np
from hypothesis import given, strategies as st, settings, assume, HealthCheck

# 检查PySide6是否可用
try:
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import Qt
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


def 创建测试数据文件(目录: str, 文件名: str, 样本数量: int, 动作分布: dict = None) -> str:
    """
    创建测试用的数据文件
    
    参数:
        目录: 保存目录
        文件名: 文件名（不含.npy后缀）
        样本数量: 样本数量
        动作分布: 动作分布字典 {动作索引: 数量}
    
    返回:
        文件路径（含.npy后缀）
    """
    # 确保文件名不重复添加.npy后缀
    if 文件名.endswith('.npy'):
        文件名 = 文件名[:-4]
    
    文件路径 = os.path.join(目录, 文件名)
    
    if 动作分布 is None:
        # 默认均匀分布
        动作分布 = {0: 样本数量}
    
    # 创建样本数据
    样本列表 = []
    for 动作索引, 数量 in 动作分布.items():
        for _ in range(数量):
            # 创建模拟样本: [图像数据, 动作标签]
            图像 = np.zeros((68, 120, 3), dtype=np.uint8)
            动作 = np.zeros(10)
            动作[动作索引 % 10] = 1
            样本列表.append([图像, 动作])
    
    # 保存为npy文件
    np.save(文件路径, np.array(样本列表, dtype=object))
    
    # np.save会自动添加.npy后缀
    return 文件路径 + ".npy"


class Test数据文件信息类测试:
    """
    数据文件信息类测试
    
    **Feature: modern-ui, Property 9: 数据文件显示一致性**
    **Validates: Requirements 6.2**
    """
    
    @given(样本数量=st.integers(min_value=1, max_value=100))
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_样本数量读取一致性(self, 应用实例, 样本数量):
        """
        属性测试: 对于任意样本数量的数据文件，读取的样本数量应与实际一致
        
        **Feature: modern-ui, Property 9: 数据文件显示一致性**
        **Validates: Requirements 6.2**
        """
        from 界面.页面.数据管理页 import 数据文件信息
        
        with tempfile.TemporaryDirectory() as 临时目录:
            # 创建测试文件
            文件路径 = 创建测试数据文件(临时目录, f"test_{样本数量}", 样本数量)
            
            # 读取文件信息
            文件信息 = 数据文件信息(文件路径)
            
            # 验证样本数量一致
            assert 文件信息.样本数量 == 样本数量, \
                f"样本数量应为{样本数量}，实际为{文件信息.样本数量}"
    
    @given(
        动作0数量=st.integers(min_value=0, max_value=50),
        动作1数量=st.integers(min_value=0, max_value=50),
        动作2数量=st.integers(min_value=0, max_value=50),
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_动作分布读取一致性(self, 应用实例, 动作0数量, 动作1数量, 动作2数量):
        """
        属性测试: 对于任意动作分布的数据文件，读取的动作分布应与实际一致
        
        **Feature: modern-ui, Property 9: 数据文件显示一致性**
        **Validates: Requirements 6.3**
        """
        # 确保至少有一个样本
        总数量 = 动作0数量 + 动作1数量 + 动作2数量
        assume(总数量 > 0)
        
        from 界面.页面.数据管理页 import 数据文件信息
        
        with tempfile.TemporaryDirectory() as 临时目录:
            # 创建测试文件
            动作分布 = {}
            if 动作0数量 > 0:
                动作分布[0] = 动作0数量
            if 动作1数量 > 0:
                动作分布[1] = 动作1数量
            if 动作2数量 > 0:
                动作分布[2] = 动作2数量
            
            文件路径 = 创建测试数据文件(
                临时目录, 
                f"test_dist_{动作0数量}_{动作1数量}_{动作2数量}", 
                总数量,
                动作分布
            )
            
            # 读取文件信息
            文件信息 = 数据文件信息(文件路径)
            
            # 验证动作分布一致
            for 动作索引, 期望数量 in 动作分布.items():
                实际数量 = 文件信息.动作分布.get(动作索引, 0)
                assert 实际数量 == 期望数量, \
                    f"动作{动作索引}数量应为{期望数量}，实际为{实际数量}"
    
    def test_文件大小读取正确(self, 应用实例):
        """
        测试: 文件大小读取应正确
        
        **Feature: modern-ui, Property 9: 数据文件显示一致性**
        **Validates: Requirements 6.2**
        """
        from 界面.页面.数据管理页 import 数据文件信息
        
        with tempfile.TemporaryDirectory() as 临时目录:
            # 创建测试文件
            文件路径 = 创建测试数据文件(临时目录, "test_size", 10)
            
            # 获取实际文件大小
            实际大小 = os.path.getsize(文件路径)
            
            # 读取文件信息
            文件信息 = 数据文件信息(文件路径)
            
            # 验证文件大小一致
            assert 文件信息.文件大小 == 实际大小, \
                f"文件大小应为{实际大小}，实际为{文件信息.文件大小}"
    
    def test_文件名读取正确(self, 应用实例):
        """
        测试: 文件名读取应正确
        
        **Feature: modern-ui, Property 9: 数据文件显示一致性**
        **Validates: Requirements 6.1**
        """
        from 界面.页面.数据管理页 import 数据文件信息
        
        with tempfile.TemporaryDirectory() as 临时目录:
            # 创建测试文件（不含.npy后缀）
            期望文件名 = "test_name_file.npy"
            文件路径 = 创建测试数据文件(临时目录, "test_name_file", 5)
            
            # 读取文件信息
            文件信息 = 数据文件信息(文件路径)
            
            # 验证文件名一致
            assert 文件信息.文件名 == 期望文件名, \
                f"文件名应为'{期望文件名}'，实际为'{文件信息.文件名}'"


class Test文件大小格式化测试:
    """
    文件大小格式化测试
    
    **Feature: modern-ui, Property 9: 数据文件显示一致性**
    **Validates: Requirements 6.2**
    """
    
    @given(字节数=st.integers(min_value=0, max_value=1023))
    @settings(max_examples=100, deadline=None)
    def test_字节格式化(self, 应用实例, 字节数):
        """
        属性测试: 小于1KB的文件应显示为字节
        
        **Feature: modern-ui, Property 9: 数据文件显示一致性**
        **Validates: Requirements 6.2**
        """
        from 界面.页面.数据管理页 import 数据文件信息
        
        # 创建一个临时文件信息对象
        文件信息 = 数据文件信息.__new__(数据文件信息)
        文件信息.文件大小 = 字节数
        
        格式化结果 = 文件信息.格式化大小()
        
        assert 格式化结果 == f"{字节数} B", \
            f"字节格式化应为'{字节数} B'，实际为'{格式化结果}'"
    
    @given(kb数=st.integers(min_value=1, max_value=1023))
    @settings(max_examples=100, deadline=None)
    def test_KB格式化(self, 应用实例, kb数):
        """
        属性测试: 1KB到1MB之间的文件应显示为KB
        
        **Feature: modern-ui, Property 9: 数据文件显示一致性**
        **Validates: Requirements 6.2**
        """
        from 界面.页面.数据管理页 import 数据文件信息
        
        字节数 = kb数 * 1024
        
        # 创建一个临时文件信息对象
        文件信息 = 数据文件信息.__new__(数据文件信息)
        文件信息.文件大小 = 字节数
        
        格式化结果 = 文件信息.格式化大小()
        
        期望结果 = f"{kb数:.1f} KB"
        assert 格式化结果 == 期望结果, \
            f"KB格式化应为'{期望结果}'，实际为'{格式化结果}'"
    
    @given(mb数=st.integers(min_value=1, max_value=1023))
    @settings(max_examples=100, deadline=None)
    def test_MB格式化(self, 应用实例, mb数):
        """
        属性测试: 1MB到1GB之间的文件应显示为MB
        
        **Feature: modern-ui, Property 9: 数据文件显示一致性**
        **Validates: Requirements 6.2**
        """
        from 界面.页面.数据管理页 import 数据文件信息
        
        字节数 = mb数 * 1024 * 1024
        
        # 创建一个临时文件信息对象
        文件信息 = 数据文件信息.__new__(数据文件信息)
        文件信息.文件大小 = 字节数
        
        格式化结果 = 文件信息.格式化大小()
        
        期望结果 = f"{mb数:.1f} MB"
        assert 格式化结果 == 期望结果, \
            f"MB格式化应为'{期望结果}'，实际为'{格式化结果}'"


class Test统计卡片测试:
    """
    统计卡片测试
    
    **Feature: modern-ui, Property 9: 数据文件显示一致性**
    **Validates: Requirements 6.3**
    """
    
    @given(
        文件数量=st.integers(min_value=1, max_value=10),
        每文件样本数=st.integers(min_value=1, max_value=100),
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_统计数据一致性(self, 应用实例, 文件数量, 每文件样本数):
        """
        属性测试: 对于任意数量的文件，统计卡片应正确显示文件数和总样本数
        
        **Feature: modern-ui, Property 9: 数据文件显示一致性**
        **Validates: Requirements 6.3**
        """
        from 界面.页面.数据管理页 import 统计卡片, 数据文件信息
        
        with tempfile.TemporaryDirectory() as 临时目录:
            # 创建测试文件
            文件信息列表 = []
            for i in range(文件数量):
                文件路径 = 创建测试数据文件(
                    临时目录, 
                    f"test_stat_{i}", 
                    每文件样本数
                )
                文件信息列表.append(数据文件信息(文件路径))
            
            # 创建统计卡片并更新
            卡片 = 统计卡片()
            卡片.更新统计(文件信息列表)
            
            try:
                # 验证文件数量
                显示文件数 = 卡片._文件数标签.text()
                assert 显示文件数 == str(文件数量), \
                    f"文件数应为{文件数量}，实际显示为{显示文件数}"
                
                # 验证总样本数
                期望总样本数 = 文件数量 * 每文件样本数
                显示样本数 = 卡片._样本数标签.text().replace(",", "")
                assert 显示样本数 == str(期望总样本数), \
                    f"总样本数应为{期望总样本数}，实际显示为{显示样本数}"
            finally:
                卡片.close()
    
    def test_空文件列表统计(self, 应用实例):
        """
        测试: 空文件列表时统计应显示0
        
        **Feature: modern-ui, Property 9: 数据文件显示一致性**
        **Validates: Requirements 6.3**
        """
        from 界面.页面.数据管理页 import 统计卡片
        
        卡片 = 统计卡片()
        卡片.更新统计([])
        
        try:
            assert 卡片._文件数标签.text() == "0", "空列表时文件数应为0"
            assert 卡片._样本数标签.text() == "0", "空列表时样本数应为0"
            assert 卡片._类别数标签.text() == "0", "空列表时类别数应为0"
        finally:
            卡片.close()


class Test文件表格显示测试:
    """
    文件表格显示测试
    
    **Feature: modern-ui, Property 9: 数据文件显示一致性**
    **Validates: Requirements 6.1, 6.2**
    """
    
    @given(文件数量=st.integers(min_value=1, max_value=5))
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_文件列表行数一致性(self, 应用实例, 文件数量):
        """
        属性测试: 对于任意数量的文件，表格行数应与文件数量一致
        
        **Feature: modern-ui, Property 9: 数据文件显示一致性**
        **Validates: Requirements 6.1**
        """
        from 界面.页面.数据管理页 import 数据管理页, 数据文件信息
        
        with tempfile.TemporaryDirectory() as 临时目录:
            # 创建测试文件
            文件信息列表 = []
            for i in range(文件数量):
                文件路径 = 创建测试数据文件(临时目录, f"test_row_{i}", 10)
                文件信息列表.append(数据文件信息(文件路径))
            
            # 创建数据管理页
            页面 = 数据管理页()
            
            try:
                # 模拟设置文件列表
                页面._文件列表 = 文件信息列表
                页面._更新文件表格()
                
                # 验证表格行数
                实际行数 = 页面._文件表格.rowCount()
                assert 实际行数 == 文件数量, \
                    f"表格行数应为{文件数量}，实际为{实际行数}"
            finally:
                页面.close()
    
    def test_文件信息显示正确(self, 应用实例):
        """
        测试: 文件信息在表格中应正确显示
        
        **Feature: modern-ui, Property 9: 数据文件显示一致性**
        **Validates: Requirements 6.1, 6.2**
        """
        from 界面.页面.数据管理页 import 数据管理页, 数据文件信息
        
        with tempfile.TemporaryDirectory() as 临时目录:
            # 创建测试文件（不含.npy后缀）
            文件名 = "test_display.npy"
            样本数 = 25
            文件路径 = 创建测试数据文件(临时目录, "test_display", 样本数)
            文件信息 = 数据文件信息(文件路径)
            
            # 创建数据管理页
            页面 = 数据管理页()
            
            try:
                # 设置文件列表
                页面._文件列表 = [文件信息]
                页面._更新文件表格()
                
                # 验证文件名显示
                显示文件名 = 页面._文件表格.item(0, 1).text()
                assert 显示文件名 == 文件名, \
                    f"文件名应为'{文件名}'，实际显示为'{显示文件名}'"
                
                # 验证样本数显示
                显示样本数 = 页面._文件表格.item(0, 4).text().replace(",", "")
                assert 显示样本数 == str(样本数), \
                    f"样本数应为'{样本数}'，实际显示为'{显示样本数}'"
            finally:
                页面.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
