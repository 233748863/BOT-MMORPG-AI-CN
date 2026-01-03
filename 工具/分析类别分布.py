#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
类别分布分析脚本

提供命令行接口，用于分析训练数据中的类别分布，
生成分析报告和可视化图表。

功能:
- 统计各类别样本数量
- 计算不平衡比率
- 识别欠代表类别
- 生成分析报告
- 生成可视化图表

使用示例:
    # 显示帮助信息
    python 工具/分析类别分布.py --help
    
    # 分析默认数据目录
    python 工具/分析类别分布.py
    
    # 分析指定数据目录
    python 工具/分析类别分布.py --数据路径 数据/训练数据
    
    # 生成可视化图表
    python 工具/分析类别分布.py --可视化
    
    # 保存可视化图表到文件
    python 工具/分析类别分布.py --可视化 --图表路径 分布图.png
    
    # 保存报告到 JSON 文件
    python 工具/分析类别分布.py --报告路径 报告.json
    
    # 计算类别权重
    python 工具/分析类别分布.py --计算权重 --策略 逆频率
    
    # 保存权重配置
    python 工具/分析类别分布.py --计算权重 --权重路径 配置/类别权重.json
"""

import os
import sys
import json
import argparse
from typing import Optional

# 添加项目根目录到路径
项目根目录 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, 项目根目录)

from 工具.类别权重 import (
    类别分析器,
    权重计算器,
    权重策略,
    分析报告
)


def 创建参数解析器() -> argparse.ArgumentParser:
    """创建命令行参数解析器"""
    解析器 = argparse.ArgumentParser(
        description='分析训练数据中的类别分布',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  %(prog)s                              # 分析默认数据目录
  %(prog)s --数据路径 数据/训练数据      # 分析指定目录
  %(prog)s --可视化                     # 生成可视化图表
  %(prog)s --可视化 --图表路径 分布.png  # 保存图表到文件
  %(prog)s --报告路径 报告.json          # 保存报告到 JSON
  %(prog)s --计算权重 --策略 逆频率      # 计算类别权重
        """
    )
    
    # 数据路径参数
    解析器.add_argument(
        '--数据路径', '-d',
        type=str,
        default=None,
        help='训练数据目录路径 (默认: 配置中的数据保存路径)'
    )
    
    # 可视化参数
    解析器.add_argument(
        '--可视化', '-v',
        action='store_true',
        help='生成类别分布可视化图表'
    )
    
    解析器.add_argument(
        '--图表路径', '-o',
        type=str,
        default=None,
        help='可视化图表保存路径 (不指定则显示图表)'
    )
    
    # 报告参数
    解析器.add_argument(
        '--报告路径', '-r',
        type=str,
        default=None,
        help='分析报告保存路径 (JSON 格式)'
    )
    
    # 权重计算参数
    解析器.add_argument(
        '--计算权重', '-w',
        action='store_true',
        help='计算类别权重'
    )
    
    解析器.add_argument(
        '--策略', '-s',
        type=str,
        choices=['逆频率', '平方根逆频率', '有效样本数',
                 'inverse_frequency', 'sqrt_inverse_frequency', 'effective_samples'],
        default='逆频率',
        help='权重计算策略 (默认: 逆频率)'
    )
    
    解析器.add_argument(
        '--权重路径',
        type=str,
        default=None,
        help='权重配置保存路径 (JSON 格式)'
    )
    
    # 欠代表阈值
    解析器.add_argument(
        '--阈值', '-t',
        type=float,
        default=0.05,
        help='欠代表类别阈值 (相对于最大类别的比例，默认: 0.05)'
    )
    
    # 静默模式
    解析器.add_argument(
        '--静默', '-q',
        action='store_true',
        help='静默模式，只输出必要信息'
    )
    
    return 解析器


def 获取权重策略(策略名称: str) -> 权重策略:
    """将策略名称转换为权重策略枚举"""
    策略映射 = {
        '逆频率': 权重策略.逆频率,
        '平方根逆频率': 权重策略.平方根逆频率,
        '有效样本数': 权重策略.有效样本数,
        'inverse_frequency': 权重策略.逆频率,
        'sqrt_inverse_frequency': 权重策略.平方根逆频率,
        'effective_samples': 权重策略.有效样本数,
    }
    return 策略映射.get(策略名称, 权重策略.逆频率)


def 打印分隔线(字符: str = '-', 长度: int = 60):
    """打印分隔线"""
    print(字符 * 长度)


def 打印报告(报告: 分析报告, 静默: bool = False):
    """打印分析报告"""
    if 静默:
        print(f"样本数: {报告.总样本数}, 类别数: {报告.类别数量}, 不平衡比率: {报告.不平衡比率:.2f}")
        return
    
    print("\n" + "=" * 60)
    print("📊 类别分布分析报告")
    print("=" * 60)
    
    print(f"\n📈 基本统计:")
    打印分隔线()
    print(f"  总样本数:     {报告.总样本数:,}")
    print(f"  类别数量:     {报告.类别数量}")
    print(f"  不平衡比率:   {报告.不平衡比率:.2f}")
    print(f"  最大类别:     {报告.最大类别}")
    print(f"  最小类别:     {报告.最小类别}")
    
    if 报告.欠代表类别:
        print(f"\n⚠️  欠代表类别 (少于最大值的 5%):")
        打印分隔线()
        for 类别 in 报告.欠代表类别:
            print(f"  • {类别}")
    
    if 报告.类别详情:
        print(f"\n📋 类别详情:")
        打印分隔线()
        print(f"  {'类别名称':<12} {'样本数':>8} {'占比':>8} {'状态':<10}")
        打印分隔线()
        for 详情 in 报告.类别详情:
            状态 = "⚠️ 欠代表" if 详情.是否欠代表 else "✓ 正常"
            print(f"  {详情.类别名称:<12} {详情.样本数量:>8,} {详情.占比*100:>7.1f}% {状态:<10}")
    
    print(f"\n💡 建议:")
    打印分隔线()
    for 建议 in 报告.建议:
        print(f"  • {建议}")
    
    print()


def 保存报告(报告: 分析报告, 路径: str):
    """保存报告到 JSON 文件"""
    报告字典 = 报告.to_dict()
    
    # 添加类别详情
    if 报告.类别详情:
        报告字典['类别详情'] = [
            {
                '类别名称': 详情.类别名称,
                '类别索引': 详情.类别索引,
                '样本数量': 详情.样本数量,
                '占比': round(详情.占比, 4),
                '是否欠代表': 详情.是否欠代表
            }
            for 详情 in 报告.类别详情
        ]
    
    # 确保目录存在
    目录 = os.path.dirname(路径)
    if 目录 and not os.path.exists(目录):
        os.makedirs(目录)
    
    with open(路径, 'w', encoding='utf-8') as f:
        json.dump(报告字典, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 报告已保存: {路径}")


def 主程序():
    """主程序入口"""
    解析器 = 创建参数解析器()
    参数 = 解析器.parse_args()
    
    # 创建分析器
    分析器 = 类别分析器(参数.数据路径)
    
    # 统计分布
    统计 = 分析器.统计分布()
    
    if not 统计:
        print("❌ 错误: 未找到训练数据")
        print(f"   数据路径: {分析器.数据路径}")
        print("   请确保数据目录存在且包含 .npy 文件")
        sys.exit(1)
    
    # 生成报告
    报告 = 分析器.生成报告()
    
    # 打印报告
    打印报告(报告, 参数.静默)
    
    # 保存报告
    if 参数.报告路径:
        保存报告(报告, 参数.报告路径)
    
    # 生成可视化
    if 参数.可视化:
        try:
            分析器.可视化(参数.图表路径)
            if 参数.图表路径:
                print(f"✅ 图表已保存: {参数.图表路径}")
        except Exception as e:
            print(f"⚠️  可视化失败: {e}")
            print("   请确保已安装 matplotlib: pip install matplotlib")
    
    # 计算权重
    if 参数.计算权重:
        策略 = 获取权重策略(参数.策略)
        计算器 = 权重计算器(统计, 策略)
        计算器.计算权重()
        
        if not 参数.静默:
            计算器.打印权重()
        
        if 参数.权重路径:
            计算器.保存权重(参数.权重路径)
            print(f"✅ 权重已保存: {参数.权重路径}")


if __name__ == "__main__":
    主程序()
