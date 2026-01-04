"""
报告完整性属性测试
使用hypothesis进行属性测试，验证报告包含所有必需内容

Property 3: 报告完整性
*对于任意* 评估结果，报告应包含所有指标和混淆矩阵

**Validates: Requirements 3.2**
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import numpy as np
from hypothesis import given, strategies as st, settings, assume

from 工具.模型评估 import 模型评估器, 评估结果, 类别指标, 报告生成器


# ==================== 策略定义 ====================

# 类别数量策略 (2-8个类别)
类别数量策略 = st.integers(min_value=2, max_value=8)


def 生成评估结果(类别数: int) -> 评估结果:
    """生成随机评估结果"""
    混淆矩阵 = np.random.randint(1, 50, size=(类别数, 类别数))
    
    动作定义 = {i: f"动作{i}" for i in range(类别数)}
    评估器 = 模型评估器(动作定义=动作定义)
    
    结果 = 评估器.计算指标(混淆矩阵)
    结果.评估时间 = np.random.uniform(0.1, 10.0)
    结果.样本数量 = int(np.sum(混淆矩阵))
    
    return 结果, 动作定义


# ==================== Property 3: 报告完整性 ====================

class Test报告完整性属性:
    """
    Property 3: 报告完整性
    
    *对于任意* 评估结果，生成的报告应包含所有指标和混淆矩阵
    
    **Validates: Requirements 3.2**
    """
    
    @given(类别数=类别数量策略)
    @settings(max_examples=100)
    def test_文本报告包含总体准确率(self, 类别数: int):
        """
        **Feature: model-evaluation-tools, Property 3: 报告完整性**
        
        文本报告应包含总体准确率
        **Validates: Requirements 3.2**
        """
        结果, 动作定义 = 生成评估结果(类别数)
        生成器 = 报告生成器(结果, 动作定义)
        
        报告 = 生成器.生成文本报告()
        
        assert "总体准确率" in 报告, "文本报告应包含总体准确率"
        assert f"{结果.总体准确率:.4f}" in 报告, "文本报告应包含准确率数值"
    
    @given(类别数=类别数量策略)
    @settings(max_examples=100)
    def test_文本报告包含样本数量(self, 类别数: int):
        """
        **Feature: model-evaluation-tools, Property 3: 报告完整性**
        
        文本报告应包含样本数量
        **Validates: Requirements 3.2**
        """
        结果, 动作定义 = 生成评估结果(类别数)
        生成器 = 报告生成器(结果, 动作定义)
        
        报告 = 生成器.生成文本报告()
        
        assert "样本数量" in 报告, "文本报告应包含样本数量"
        assert str(结果.样本数量) in 报告, "文本报告应包含样本数量数值"
    
    @given(类别数=类别数量策略)
    @settings(max_examples=100)
    def test_文本报告包含所有类别指标(self, 类别数: int):
        """
        **Feature: model-evaluation-tools, Property 3: 报告完整性**
        
        文本报告应包含所有类别的指标
        **Validates: Requirements 3.2**
        """
        结果, 动作定义 = 生成评估结果(类别数)
        生成器 = 报告生成器(结果, 动作定义)
        
        报告 = 生成器.生成文本报告()
        
        for 类别名 in 结果.类别指标.keys():
            assert 类别名 in 报告, f"文本报告应包含类别 {类别名}"
    
    @given(类别数=类别数量策略)
    @settings(max_examples=100)
    def test_文本报告包含混淆矩阵(self, 类别数: int):
        """
        **Feature: model-evaluation-tools, Property 3: 报告完整性**
        
        文本报告应包含混淆矩阵
        **Validates: Requirements 3.2**
        """
        结果, 动作定义 = 生成评估结果(类别数)
        生成器 = 报告生成器(结果, 动作定义)
        
        报告 = 生成器.生成文本报告(包含混淆矩阵=True)
        
        assert "混淆矩阵" in 报告, "文本报告应包含混淆矩阵标题"
    
    @given(类别数=类别数量策略)
    @settings(max_examples=100)
    def test_文本报告包含分析摘要(self, 类别数: int):
        """
        **Feature: model-evaluation-tools, Property 3: 报告完整性**
        
        文本报告应包含分析摘要
        **Validates: Requirements 3.2**
        """
        结果, 动作定义 = 生成评估结果(类别数)
        生成器 = 报告生成器(结果, 动作定义)
        
        报告 = 生成器.生成文本报告()
        
        assert "分析摘要" in 报告, "文本报告应包含分析摘要"
    
    @given(类别数=类别数量策略)
    @settings(max_examples=100)
    def test_文本报告包含改进建议(self, 类别数: int):
        """
        **Feature: model-evaluation-tools, Property 3: 报告完整性**
        
        文本报告应包含改进建议
        **Validates: Requirements 3.4**
        """
        结果, 动作定义 = 生成评估结果(类别数)
        生成器 = 报告生成器(结果, 动作定义)
        
        报告 = 生成器.生成文本报告(包含建议=True)
        
        assert "改进建议" in 报告, "文本报告应包含改进建议"
    
    @given(类别数=类别数量策略)
    @settings(max_examples=100)
    def test_Markdown报告包含总体指标(self, 类别数: int):
        """
        **Feature: model-evaluation-tools, Property 3: 报告完整性**
        
        Markdown 报告应包含总体指标
        **Validates: Requirements 3.2, 3.3**
        """
        结果, 动作定义 = 生成评估结果(类别数)
        生成器 = 报告生成器(结果, 动作定义)
        
        报告 = 生成器.生成Markdown报告()
        
        assert "# 模型评估报告" in 报告, "Markdown 报告应包含标题"
        assert "## 总体指标" in 报告, "Markdown 报告应包含总体指标章节"
        assert "总体准确率" in 报告, "Markdown 报告应包含总体准确率"
    
    @given(类别数=类别数量策略)
    @settings(max_examples=100)
    def test_Markdown报告包含平均指标表格(self, 类别数: int):
        """
        **Feature: model-evaluation-tools, Property 3: 报告完整性**
        
        Markdown 报告应包含平均指标表格
        **Validates: Requirements 3.2, 3.3**
        """
        结果, 动作定义 = 生成评估结果(类别数)
        生成器 = 报告生成器(结果, 动作定义)
        
        报告 = 生成器.生成Markdown报告()
        
        assert "## 平均指标" in 报告, "Markdown 报告应包含平均指标章节"
        assert "| 指标类型 |" in 报告, "Markdown 报告应包含平均指标表格"
        assert "宏平均" in 报告 or "加权平均" in 报告, "Markdown 报告应包含平均指标数据"
    
    @given(类别数=类别数量策略)
    @settings(max_examples=100)
    def test_Markdown报告包含类别指标表格(self, 类别数: int):
        """
        **Feature: model-evaluation-tools, Property 3: 报告完整性**
        
        Markdown 报告应包含类别指标表格
        **Validates: Requirements 3.2, 3.3**
        """
        结果, 动作定义 = 生成评估结果(类别数)
        生成器 = 报告生成器(结果, 动作定义)
        
        报告 = 生成器.生成Markdown报告()
        
        assert "## 各类别指标" in 报告, "Markdown 报告应包含类别指标章节"
        assert "| 类别 |" in 报告, "Markdown 报告应包含类别指标表格"
        
        for 类别名 in 结果.类别指标.keys():
            assert 类别名 in 报告, f"Markdown 报告应包含类别 {类别名}"
    
    @given(类别数=类别数量策略)
    @settings(max_examples=100)
    def test_Markdown报告包含混淆矩阵(self, 类别数: int):
        """
        **Feature: model-evaluation-tools, Property 3: 报告完整性**
        
        Markdown 报告应包含混淆矩阵
        **Validates: Requirements 3.2, 3.3**
        """
        结果, 动作定义 = 生成评估结果(类别数)
        生成器 = 报告生成器(结果, 动作定义)
        
        报告 = 生成器.生成Markdown报告(包含混淆矩阵=True)
        
        assert "## 混淆矩阵" in 报告, "Markdown 报告应包含混淆矩阵章节"
        assert "| 真实\\预测 |" in 报告, "Markdown 报告应包含混淆矩阵表格"
    
    @given(类别数=类别数量策略)
    @settings(max_examples=100)
    def test_HTML报告包含所有必需元素(self, 类别数: int):
        """
        **Feature: model-evaluation-tools, Property 3: 报告完整性**
        
        HTML 报告应包含所有必需元素
        **Validates: Requirements 3.2, 3.3**
        """
        结果, 动作定义 = 生成评估结果(类别数)
        生成器 = 报告生成器(结果, 动作定义)
        
        报告 = 生成器.生成HTML报告()
        
        # 检查 HTML 结构
        assert "<!DOCTYPE html>" in 报告, "HTML 报告应包含 DOCTYPE"
        assert "<html" in 报告, "HTML 报告应包含 html 标签"
        assert "<head>" in 报告, "HTML 报告应包含 head 标签"
        assert "<body>" in 报告, "HTML 报告应包含 body 标签"
        
        # 检查内容
        assert "模型评估报告" in 报告, "HTML 报告应包含标题"
        assert "总体指标" in 报告, "HTML 报告应包含总体指标"
        assert "平均指标" in 报告, "HTML 报告应包含平均指标"
        assert "各类别指标" in 报告, "HTML 报告应包含类别指标"
    
    @given(类别数=类别数量策略)
    @settings(max_examples=100)
    def test_HTML报告包含混淆矩阵(self, 类别数: int):
        """
        **Feature: model-evaluation-tools, Property 3: 报告完整性**
        
        HTML 报告应包含混淆矩阵
        **Validates: Requirements 3.2, 3.3**
        """
        结果, 动作定义 = 生成评估结果(类别数)
        生成器 = 报告生成器(结果, 动作定义)
        
        报告 = 生成器.生成HTML报告(包含混淆矩阵=True)
        
        assert "混淆矩阵" in 报告, "HTML 报告应包含混淆矩阵"
        assert "confusion-matrix" in 报告, "HTML 报告应包含混淆矩阵样式类"
    
    @given(类别数=类别数量策略)
    @settings(max_examples=100)
    def test_HTML报告包含改进建议(self, 类别数: int):
        """
        **Feature: model-evaluation-tools, Property 3: 报告完整性**
        
        HTML 报告应包含改进建议
        **Validates: Requirements 3.3, 3.4**
        """
        结果, 动作定义 = 生成评估结果(类别数)
        生成器 = 报告生成器(结果, 动作定义)
        
        报告 = 生成器.生成HTML报告(包含建议=True)
        
        assert "改进建议" in 报告, "HTML 报告应包含改进建议"
    
    @given(类别数=类别数量策略)
    @settings(max_examples=100)
    def test_JSON报告包含所有字段(self, 类别数: int):
        """
        **Feature: model-evaluation-tools, Property 3: 报告完整性**
        
        JSON 报告应包含所有必需字段
        **Validates: Requirements 3.2**
        """
        结果, 动作定义 = 生成评估结果(类别数)
        生成器 = 报告生成器(结果, 动作定义)
        
        报告 = 生成器.生成JSON报告()
        
        assert '总体准确率' in 报告, "JSON 报告应包含总体准确率"
        assert '类别指标' in 报告, "JSON 报告应包含类别指标"
        assert '宏平均' in 报告, "JSON 报告应包含宏平均"
        assert '加权平均' in 报告, "JSON 报告应包含加权平均"
        assert '评估时间' in 报告, "JSON 报告应包含评估时间"
        assert '样本数量' in 报告, "JSON 报告应包含样本数量"
        assert '分析摘要' in 报告, "JSON 报告应包含分析摘要"
        assert '改进建议' in 报告, "JSON 报告应包含改进建议"
    
    @given(类别数=类别数量策略)
    @settings(max_examples=100)
    def test_改进建议非空(self, 类别数: int):
        """
        **Feature: model-evaluation-tools, Property 3: 报告完整性**
        
        改进建议列表应非空
        **Validates: Requirements 3.4**
        """
        结果, 动作定义 = 生成评估结果(类别数)
        生成器 = 报告生成器(结果, 动作定义)
        
        建议 = 生成器.生成改进建议()
        
        assert len(建议) > 0, "改进建议列表应非空"
        assert all(isinstance(s, str) for s in 建议), "改进建议应为字符串列表"
    
    @given(类别数=类别数量策略)
    @settings(max_examples=100)
    def test_弱势类别分析结果完整(self, 类别数: int):
        """
        **Feature: model-evaluation-tools, Property 3: 报告完整性**
        
        弱势类别分析结果应包含所有必需字段
        **Validates: Requirements 3.4**
        """
        结果, 动作定义 = 生成评估结果(类别数)
        生成器 = 报告生成器(结果, 动作定义)
        
        分析 = 生成器.分析弱势类别()
        
        assert '弱势类别列表' in 分析, "分析结果应包含弱势类别列表"
        assert '总弱势类别数' in 分析, "分析结果应包含总弱势类别数"
        assert '平均F1分数' in 分析, "分析结果应包含平均F1分数"
        assert '建议优先处理' in 分析, "分析结果应包含建议优先处理"
        
        # 验证数据一致性
        assert 分析['总弱势类别数'] == len(分析['弱势类别列表']), \
            "总弱势类别数应等于弱势类别列表长度"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
