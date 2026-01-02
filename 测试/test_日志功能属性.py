# -*- coding: utf-8 -*-
"""
日志功能属性测试模块

使用Hypothesis进行属性测试，验证日志显示功能。

**Property 5: 日志显示功能**
*对于任意* 添加的日志消息，应包含时间戳；
对于任意过滤条件，过滤结果应只包含符合条件的日志；
对于任意搜索关键词，搜索结果应包含该关键词

**Validates: Requirements 3.6, 7.1, 7.2, 7.3**
"""

import sys
import os
import tempfile

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from hypothesis import given, strategies as st, settings, assume

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

# 有效的日志级别
有效日志级别 = ["信息", "警告", "错误"]

# 生成非空字符串的策略
非空字符串策略 = st.text(
    alphabet=st.characters(
        whitelist_categories=('L', 'N', 'P', 'S'),
        whitelist_characters=' '
    ),
    min_size=1,
    max_size=100
).filter(lambda x: x.strip())


@pytest.fixture(scope="module")
def 应用实例():
    """创建QApplication实例（整个模块共享）"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def 日志查看器(应用实例):
    """创建日志查看器实例"""
    from 界面.组件.日志查看器 import LogViewer
    查看器 = LogViewer()
    yield 查看器
    查看器.close()


class Test日志功能属性测试:
    """
    日志功能属性测试类
    
    **Feature: modern-ui, Property 5: 日志显示功能**
    **Validates: Requirements 3.6, 7.1, 7.2, 7.3**
    """
    
    @given(
        级别=st.sampled_from(有效日志级别),
        消息=非空字符串策略
    )
    @settings(max_examples=100, deadline=None)
    def test_日志添加包含时间戳(self, 应用实例, 级别, 消息):
        """
        属性测试: 对于任意添加的日志消息，应包含时间戳
        
        **Feature: modern-ui, Property 5: 日志显示功能**
        **Validates: Requirements 7.1**
        """
        from 界面.组件.日志查看器 import LogViewer
        import re
        
        # 创建日志查看器
        查看器 = LogViewer()
        
        try:
            # 添加日志
            查看器.添加日志(级别, 消息)
            
            # 获取所有日志
            日志列表 = 查看器.获取所有日志()
            
            # 验证1: 日志列表不为空
            assert len(日志列表) == 1, "添加一条日志后，日志列表应有1条记录"
            
            # 验证2: 日志条目包含时间戳
            条目 = 日志列表[0]
            assert 条目.时间戳 is not None, "日志条目应包含时间戳"
            
            # 验证3: 时间戳格式正确 (HH:MM:SS)
            时间戳格式 = re.compile(r'^\d{2}:\d{2}:\d{2}$')
            assert 时间戳格式.match(条目.时间戳), \
                f"时间戳格式应为HH:MM:SS，实际为'{条目.时间戳}'"
            
            # 验证4: 格式化输出包含时间戳
            格式化文本 = 条目.格式化()
            assert 条目.时间戳 in 格式化文本, "格式化输出应包含时间戳"
        finally:
            查看器.close()
    
    @given(
        过滤级别=st.sampled_from(有效日志级别),
        日志数据=st.lists(
            st.tuples(
                st.sampled_from(有效日志级别),
                非空字符串策略
            ),
            min_size=1,
            max_size=20
        )
    )
    @settings(max_examples=100, deadline=None)
    def test_日志级别过滤(self, 应用实例, 过滤级别, 日志数据):
        """
        属性测试: 对于任意过滤条件，过滤结果应只包含符合条件的日志
        
        **Feature: modern-ui, Property 5: 日志显示功能**
        **Validates: Requirements 7.2**
        """
        from 界面.组件.日志查看器 import LogViewer
        
        # 创建日志查看器
        查看器 = LogViewer()
        
        try:
            # 添加多条日志
            for 级别, 消息 in 日志数据:
                查看器.添加日志(级别, 消息)
            
            # 执行过滤
            过滤结果 = 查看器.过滤日志(过滤级别)
            
            # 验证: 所有过滤结果的级别都应与过滤条件一致
            for 条目 in 过滤结果:
                assert 条目.级别 == 过滤级别, \
                    f"过滤结果中的日志级别应为'{过滤级别}'，实际为'{条目.级别}'"
            
            # 验证: 过滤结果数量应等于原始数据中该级别的数量
            预期数量 = sum(1 for 级别, _ in 日志数据 if 级别 == 过滤级别)
            assert len(过滤结果) == 预期数量, \
                f"过滤结果数量应为{预期数量}，实际为{len(过滤结果)}"
        finally:
            查看器.close()
    
    @given(
        日志数据=st.lists(
            st.tuples(
                st.sampled_from(有效日志级别),
                非空字符串策略
            ),
            min_size=1,
            max_size=20
        )
    )
    @settings(max_examples=100, deadline=None)
    def test_日志全部过滤(self, 应用实例, 日志数据):
        """
        属性测试: 过滤条件为"全部"时，应返回所有日志
        
        **Feature: modern-ui, Property 5: 日志显示功能**
        **Validates: Requirements 7.2**
        """
        from 界面.组件.日志查看器 import LogViewer
        
        # 创建日志查看器
        查看器 = LogViewer()
        
        try:
            # 添加多条日志
            for 级别, 消息 in 日志数据:
                查看器.添加日志(级别, 消息)
            
            # 执行"全部"过滤
            过滤结果 = 查看器.过滤日志("全部")
            
            # 验证: 过滤结果数量应等于添加的日志数量
            assert len(过滤结果) == len(日志数据), \
                f"'全部'过滤应返回所有日志，预期{len(日志数据)}条，实际{len(过滤结果)}条"
        finally:
            查看器.close()
    
    @given(
        关键词=st.text(min_size=1, max_size=20).filter(lambda x: x.strip()),
        日志数据=st.lists(
            st.tuples(
                st.sampled_from(有效日志级别),
                非空字符串策略
            ),
            min_size=1,
            max_size=20
        )
    )
    @settings(max_examples=100, deadline=None)
    def test_日志搜索功能(self, 应用实例, 关键词, 日志数据):
        """
        属性测试: 对于任意搜索关键词，搜索结果应包含该关键词
        
        **Feature: modern-ui, Property 5: 日志显示功能**
        **Validates: Requirements 7.3**
        """
        from 界面.组件.日志查看器 import LogViewer
        
        # 创建日志查看器
        查看器 = LogViewer()
        
        try:
            # 添加多条日志
            for 级别, 消息 in 日志数据:
                查看器.添加日志(级别, 消息)
            
            # 执行搜索
            搜索结果 = 查看器.搜索日志(关键词)
            
            # 验证: 所有搜索结果的消息都应包含关键词（不区分大小写）
            关键词小写 = 关键词.lower()
            for 条目 in 搜索结果:
                assert 关键词小写 in 条目.消息.lower(), \
                    f"搜索结果中的消息应包含关键词'{关键词}'，实际消息为'{条目.消息}'"
            
            # 验证: 搜索结果数量应等于原始数据中包含关键词的数量
            预期数量 = sum(1 for _, 消息 in 日志数据 if 关键词小写 in 消息.lower())
            assert len(搜索结果) == 预期数量, \
                f"搜索结果数量应为{预期数量}，实际为{len(搜索结果)}"
        finally:
            查看器.close()
    
    @given(
        日志数据=st.lists(
            st.tuples(
                st.sampled_from(有效日志级别),
                非空字符串策略
            ),
            min_size=1,
            max_size=20
        )
    )
    @settings(max_examples=100, deadline=None)
    def test_空关键词搜索返回全部(self, 应用实例, 日志数据):
        """
        属性测试: 空关键词搜索应返回所有日志
        
        **Feature: modern-ui, Property 5: 日志显示功能**
        **Validates: Requirements 7.3**
        """
        from 界面.组件.日志查看器 import LogViewer
        
        # 创建日志查看器
        查看器 = LogViewer()
        
        try:
            # 添加多条日志
            for 级别, 消息 in 日志数据:
                查看器.添加日志(级别, 消息)
            
            # 执行空关键词搜索
            搜索结果 = 查看器.搜索日志("")
            
            # 验证: 空关键词搜索应返回所有日志
            assert len(搜索结果) == len(日志数据), \
                f"空关键词搜索应返回所有日志，预期{len(日志数据)}条，实际{len(搜索结果)}条"
        finally:
            查看器.close()
    
    @given(
        日志数据=st.lists(
            st.tuples(
                st.sampled_from(有效日志级别),
                非空字符串策略
            ),
            min_size=1,
            max_size=10
        )
    )
    @settings(max_examples=100, deadline=None)
    def test_日志导出功能(self, 应用实例, 日志数据):
        """
        属性测试: 导出的日志文件应包含所有日志条目
        
        **Feature: modern-ui, Property 5: 日志显示功能**
        **Validates: Requirements 7.4**
        """
        from 界面.组件.日志查看器 import LogViewer
        
        # 创建日志查看器
        查看器 = LogViewer()
        
        try:
            # 添加多条日志
            for 级别, 消息 in 日志数据:
                查看器.添加日志(级别, 消息)
            
            # 创建临时文件
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                临时文件路径 = f.name
            
            try:
                # 导出日志
                导出结果 = 查看器.导出日志(临时文件路径)
                
                # 验证: 导出应成功
                assert 导出结果 is True, "日志导出应成功"
                
                # 读取导出文件
                with open(临时文件路径, 'r', encoding='utf-8') as f:
                    导出内容 = f.read()
                
                # 验证: 导出文件应包含所有日志消息
                日志列表 = 查看器.获取所有日志()
                for 条目 in 日志列表:
                    assert 条目.消息 in 导出内容, \
                        f"导出文件应包含消息'{条目.消息}'"
                    assert 条目.时间戳 in 导出内容, \
                        f"导出文件应包含时间戳'{条目.时间戳}'"
            finally:
                # 清理临时文件
                if os.path.exists(临时文件路径):
                    os.remove(临时文件路径)
        finally:
            查看器.close()
    
    def test_日志清空功能(self, 日志查看器):
        """
        测试: 清空日志后，日志列表应为空
        
        **Feature: modern-ui, Property 5: 日志显示功能**
        **Validates: Requirements 7.1**
        """
        # 添加一些日志
        日志查看器.添加日志("信息", "测试消息1")
        日志查看器.添加日志("警告", "测试消息2")
        日志查看器.添加日志("错误", "测试消息3")
        
        # 验证日志已添加
        assert 日志查看器.获取日志数量() == 3
        
        # 清空日志
        日志查看器.清空日志()
        
        # 验证日志已清空
        assert 日志查看器.获取日志数量() == 0
        assert len(日志查看器.获取所有日志()) == 0
    
    def test_日志级别颜色映射(self, 日志查看器):
        """
        测试: 不同日志级别应有对应的颜色
        
        **Feature: modern-ui, Property 5: 日志显示功能**
        **Validates: Requirements 3.6**
        """
        from 界面.组件.日志查看器 import LogViewer
        
        # 验证所有级别都有颜色映射
        for 级别 in 有效日志级别:
            assert 级别 in LogViewer.级别颜色, \
                f"日志级别'{级别}'应有对应的颜色映射"
            
            颜色 = LogViewer.级别颜色[级别]
            assert 颜色.startswith("#"), \
                f"颜色值应为十六进制格式，实际为'{颜色}'"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
